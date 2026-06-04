#!/usr/bin/env python3
"""Create Outlook draft replies for EUDAMED/XML support emails.

This helper is intentionally semi-automatic: it can inspect matching Outlook
messages and attachments, but it never sends mail. Use --dry-run first to write
draft text files under local_beta_data/outlook_draft_assistant/.

Microsoft Outlook for Mac AppleScript support varies by Outlook version. If the
local Outlook build does not expose messages/attachments through AppleScript,
use --source-dir with exported .eml/.xml files or paste the generated response
manually.
"""

from __future__ import annotations

import argparse
import dataclasses
import email
from email import policy
import html
import json
import shutil
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "local_beta_data" / "outlook_draft_assistant"
DEFAULT_FEEDBACK_DIR = ROOT / "Feedback case"
KEYWORDS = ("eudamed", "xml")


@dataclasses.dataclass
class AttachmentInfo:
    name: str
    path: Path
    analysis: list[str]


@dataclasses.dataclass
class MailItem:
    message_id: str
    subject: str
    sender_name: str
    sender_email: str
    body: str
    attachments: list[AttachmentInfo]
    case_dir: Path | None = None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Find EUDAMED/XML mails and prepare Outlook reply drafts."
    )
    parser.add_argument("--limit", type=int, default=10, help="maximum messages to inspect")
    parser.add_argument("--days", type=int, default=14, help="lookback window for Outlook mode")
    parser.add_argument(
        "--feedback-dir",
        type=Path,
        default=DEFAULT_FEEDBACK_DIR,
        help="folder where matched email attachments are stored as numbered feedback cases",
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="analyze exported .eml/.xml files from a folder instead of Outlook",
    )
    parser.add_argument(
        "--create-drafts",
        action="store_true",
        help="create Outlook draft replies. Without this, draft text files are written only.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="force local draft text output only; this is the default unless --create-drafts is set.",
    )
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    args.feedback_dir.mkdir(parents=True, exist_ok=True)
    if args.source_dir:
        items = list(load_from_source_dir(args.source_dir, args.limit, args.feedback_dir))
    else:
        items = fetch_outlook_messages(limit=args.limit, days=args.days, feedback_dir=args.feedback_dir)

    matched = [item for item in items if is_relevant(item)]
    if args.limit:
        matched = matched[: args.limit]

    if not matched:
        print("No matching EUDAMED/XML messages found.")
        return 0

    manifest = []
    for item in matched:
        subject, body = build_reply(item)
        draft_path = write_draft_file(item, subject, body)
        created = False
        if args.create_drafts and not args.dry_run and item.sender_email:
            create_outlook_draft(item, subject, body)
            created = True
        manifest.append(
            {
                "message_id": item.message_id,
                "subject": item.subject,
                "sender": item.sender_email,
                "case_dir": str(item.case_dir) if item.case_dir else "",
                "draft_file": str(draft_path),
                "outlook_draft_created": created,
            }
        )

    manifest_path = OUT_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Prepared {len(manifest)} draft(s). Manifest: {manifest_path}")
    return 0


def is_relevant(item: MailItem) -> bool:
    haystack = " ".join(
        [
            item.subject,
            item.body,
            " ".join(att.name for att in item.attachments),
        ]
    ).lower()
    return any(keyword in haystack for keyword in KEYWORDS)


def fetch_outlook_messages(limit: int, days: int, feedback_dir: Path) -> list[MailItem]:
    record_sep = chr(30)
    field_sep = chr(31)
    attachment_sep = chr(29)
    next_case = next_feedback_case_number(feedback_dir)
    script = f"""
    set recordSep to ASCII character 30
    set fieldSep to ASCII character 31
    set attachmentSep to ASCII character 29
    set outputText to ""
    tell application "Microsoft Outlook"
        set cutoffDate to (current date) - ({days} * days)
        set inboxMessages to messages of inbox
        set hitCount to 0
        set nextCaseNumber to {next_case}
        repeat with msg in inboxMessages
            if hitCount is greater than or equal to {limit} then exit repeat
            try
                if time received of msg is less than cutoffDate then
                    -- keep scanning because Outlook ordering differs by version
                end if
                set msgSubject to subject of msg as text
                set msgContent to plain text content of msg as text
                set msgSenderName to ""
                set msgSenderEmail to ""
                try
                    set msgSenderName to name of sender of msg as text
                    set msgSenderEmail to address of email address of sender of msg as text
                end try
                set msgId to id of msg as text
                set haystack to (msgSubject & " " & msgContent)
                repeat with att in attachments of msg
                    try
                        set haystack to haystack & " " & (name of att as text)
                    end try
                end repeat
                if (haystack contains "EUDAMED") or (haystack contains "eudamed") or (haystack contains "XML") or (haystack contains "xml") then
                    set caseFolder to "{feedback_dir.as_posix()}/" & nextCaseNumber & "# feedback"
                    do shell script "mkdir -p " & quoted form of caseFolder
                    set savedAttachments to {{}}
                    set attachmentIndex to 1
                    repeat with att in attachments of msg
                        try
                            set attName to name of att as text
                            set safeName to my sanitizeFileName(attName)
                            set prefixText to my zeroPad(attachmentIndex)
                            set destPosix to caseFolder & "/" & prefixText & "_" & safeName
                            save att in POSIX file destPosix
                            set end of savedAttachments to destPosix
                            set attachmentIndex to attachmentIndex + 1
                        end try
                    end repeat
                    set metadataPath to caseFolder & "/email_context.txt"
                    set metadataText to "Subject: " & msgSubject & linefeed & "From: " & msgSenderName & " <" & msgSenderEmail & ">" & linefeed & linefeed & msgContent
                    do shell script "printf %s " & quoted form of metadataText & " > " & quoted form of metadataPath
                    set attachmentText to my joinList(savedAttachments, attachmentSep)
                    set outputText to outputText & my cleanField(msgId) & fieldSep & my cleanField(msgSubject) & fieldSep & my cleanField(msgSenderName) & fieldSep & my cleanField(msgSenderEmail) & fieldSep & my cleanField(msgContent) & fieldSep & attachmentText & fieldSep & caseFolder & recordSep
                    set hitCount to hitCount + 1
                    set nextCaseNumber to nextCaseNumber + 1
                end if
            end try
        end repeat
    end tell
    return outputText

    on sanitizeFileName(fileName)
        set invalidChars to {{":", "/", "\\\\", "*", "?", quote, "<", ">", "|"}}
        set cleanName to fileName
        repeat with c in invalidChars
            set AppleScript's text item delimiters to c
            set parts to text items of cleanName
            set AppleScript's text item delimiters to "_"
            set cleanName to parts as text
        end repeat
        set AppleScript's text item delimiters to ""
        return cleanName
    end sanitizeFileName

    on cleanField(valueText)
        set cleanText to valueText as text
        repeat with delimiterChar in {{ASCII character 30, ASCII character 31, ASCII character 29}}
            set AppleScript's text item delimiters to delimiterChar
            set parts to text items of cleanText
            set AppleScript's text item delimiters to " "
            set cleanText to parts as text
        end repeat
        set AppleScript's text item delimiters to ""
        return cleanText
    end cleanField

    on joinList(valueList, delimiterText)
        set AppleScript's text item delimiters to delimiterText
        set joinedText to valueList as text
        set AppleScript's text item delimiters to ""
        return joinedText
    end joinList

    on zeroPad(numberValue)
        if numberValue is less than 10 then
            return "0" & numberValue
        end if
        return numberValue as text
    end zeroPad
    """
    output = run_osascript(script)
    if not output.strip():
        return []
    items = []
    for record in output.split(record_sep):
        if not record.strip():
            continue
        fields = record.split(field_sep)
        if len(fields) < 6:
            continue
        attachment_paths = [Path(p) for p in fields[5].split(attachment_sep) if p]
        items.append(
            MailItem(
                message_id=fields[0],
                subject=fields[1],
                sender_name=fields[2],
                sender_email=fields[3],
                body=fields[4],
                attachments=[analyze_attachment(path) for path in attachment_paths if path.exists()],
                case_dir=Path(fields[6]) if len(fields) > 6 and fields[6] else None,
            )
        )
    return items


def load_from_source_dir(source_dir: Path, limit: int, feedback_dir: Path) -> Iterable[MailItem]:
    if not source_dir.exists():
        raise FileNotFoundError(source_dir)
    eml_files = newest_files(source_dir.glob("*.eml"), limit)
    if eml_files:
        for path in eml_files:
            yield parse_eml(path, feedback_dir)
        return
    xml_files = newest_files(source_dir.glob("*.xml"), limit)
    if xml_files:
        case_dir = create_feedback_case_dir(feedback_dir)
        attachments = []
        for idx, path in enumerate(xml_files, start=1):
            dest = copy_to_case(path, case_dir, idx)
            attachments.append(analyze_attachment(dest))
        yield MailItem(
            message_id="source-dir",
            subject="EUDAMED response XML analysis",
            sender_name="",
            sender_email="",
            body="",
            attachments=attachments,
            case_dir=case_dir,
        )


def parse_eml(path: Path, feedback_dir: Path) -> MailItem:
    msg = email.message_from_bytes(path.read_bytes(), policy=policy.default)
    body_parts = []
    attachments = []
    case_dir = create_feedback_case_dir(feedback_dir)
    attachment_index = 1
    for part in msg.walk():
        disposition = part.get_content_disposition()
        if disposition == "attachment":
            filename = part.get_filename() or "attachment.bin"
            dest = case_dir / f"{attachment_index:02d}_{safe_filename(filename)}"
            dest.write_bytes(part.get_payload(decode=True) or b"")
            attachments.append(analyze_attachment(dest))
            attachment_index += 1
        elif part.get_content_type() == "text/plain" and not disposition:
            body_parts.append(part.get_content())
        elif part.get_content_type() == "text/html" and not body_parts and not disposition:
            body_parts.append(strip_html(part.get_content()))
    sender_name, sender_email = parse_address(msg.get("from", ""))
    write_email_context(case_dir, msg.get("subject", path.stem), sender_name, sender_email, "\n".join(body_parts))
    return MailItem(
        message_id=msg.get("message-id", path.stem),
        subject=msg.get("subject", path.stem),
        sender_name=sender_name,
        sender_email=sender_email,
        body="\n".join(body_parts),
        attachments=attachments,
        case_dir=case_dir,
    )


def analyze_attachment(path: Path) -> AttachmentInfo:
    analysis = []
    suffix = path.suffix.lower()
    if suffix == ".xml":
        analysis.extend(analyze_xml(path))
    elif suffix in {".xlsx", ".xlsm", ".xls"}:
        analysis.append(
            "附件是 Excel 模板/源数据。建议先导入 EUDAMED 工具重新预检，重点看必填项、枚举值、版本号和 service 选择。"
        )
    elif suffix == ".zip":
        analysis.append(
            "附件是 ZIP 包。请确认按 manifest 顺序上传；含依赖的 UDI_DI.POST 必须等对应 DEVICE.POST 成功后再上传。"
        )
    else:
        analysis.append("附件未自动解析；需要人工确认其内容是否为 EUDAMED response 或源数据。")
    return AttachmentInfo(name=path.name, path=path, analysis=analysis)


def analyze_xml(path: Path) -> list[str]:
    content = path.read_bytes()
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        return [f"XML 解析失败：{exc}。可能是文件损坏、不是 XML，或导出时内容不完整。"]

    texts = " ".join(t.strip() for t in root.itertext() if t and t.strip())
    findings = []
    service = normalize_space(first_text(root, {"serviceID", "serviceId"}))
    operation = normalize_space(first_text(root, {"serviceOperation", "operation", "operationType"}))
    response = normalize_space(first_text(root, {"responseCode", "status", "processStatus"}))
    code = normalize_space(first_text(root, {"operationErrorCode", "errorCode", "code", "ruleCode"}))
    detail = normalize_space(first_text(root, {"operationDetail", "operationErrorDetail", "detail", "message", "description"}))

    if response:
        findings.append(f"EUDAMED 返回状态：{response}。")
    if service or operation:
        findings.append(f"XML/回执显示 service：{format_service(service, operation)}。")
    if code or detail:
        findings.append(f"错误码/详情：{summarize_detail(code, detail)}")

    lower = texts.lower()
    if "does not match selected" in lower and "service" in lower:
        findings.append(
            "可能原因：EUDAMED 上传页面选择的 service 与 XML 内部 service 不一致。请按导出文件名/manifest 选择相同 service，例如 UDI_DI.POST 不能用 UDI_DI.PATCH 上传。"
        )
    if "fixed value of '3.0.30'" in lower:
        findings.append(
            "可能原因：XML 仍使用旧 XSD/message version，例如 3.0.28；当前官方 production XSD 要求 3.0.30。请使用新版工具重新导出。"
        )
    if "marketinfo:country" in lower and "facet-valid with respect to enumeration" in lower:
        findings.append(
            "可能原因：市场国家代码不是 EUDAMED 允许枚举。常见问题是希腊应填 EUDAMED 枚举 `EL`，不是 ISO 习惯写法 `GR`。"
        )
    if "specialdevice" in lower:
        findings.append(
            "可能原因：Special Device Type 填入了非官方枚举值，常见误填是把产品名称/型号填到该字段。普通器械应留空；只有软件、眼镜/隐形眼镜、骨科、定制等特殊类别才选择官方枚举。"
        )
    if "current version" in lower or "version" in lower and "patch" in lower:
        findings.append(
            "可能原因：PATCH 服务需要填写 EUDAMED 当前版本号。请在网页端查看对应 Basic UDI 或 UDI-DI 的当前 version 后填入模板再导出。"
        )
    if "already exists" in lower:
        findings.append(
            "可能原因：要创建的 Basic UDI-DI 或 UDI-DI 已存在；已有 Basic 下追加 UDI-DI 应使用 UDI_DI.POST，维护已有记录应使用 PATCH。"
        )
    if "xsd" in lower or "cvc-" in lower:
        findings.append(
            "这是 XML schema 校验错误，通常发生在字段值、枚举、日期/数字格式或 service 选择不符合官方 XSD 时；还未进入完整业务审核。"
        )

    return findings or ["XML 已读取，但未识别出明确 EUDAMED 错误；建议人工查看 responseCode、operationErrorCode 和 operationDetail。"]


def newest_files(paths: Iterable[Path], limit: int) -> list[Path]:
    files = sorted(paths, key=lambda path: path.stat().st_mtime, reverse=True)
    return files[:limit] if limit else files


def next_feedback_case_number(feedback_dir: Path) -> int:
    max_number = 0
    if feedback_dir.exists():
        for path in feedback_dir.iterdir():
            if not path.is_dir():
                continue
            match = re.match(r"^(\d+)#\s*feedback$", path.name, re.IGNORECASE)
            if match:
                max_number = max(max_number, int(match.group(1)))
    return max_number + 1


def create_feedback_case_dir(feedback_dir: Path) -> Path:
    feedback_dir.mkdir(parents=True, exist_ok=True)
    number = next_feedback_case_number(feedback_dir)
    case_dir = feedback_dir / f"{number}# feedback"
    while case_dir.exists():
        number += 1
        case_dir = feedback_dir / f"{number}# feedback"
    case_dir.mkdir(parents=True)
    return case_dir


def copy_to_case(path: Path, case_dir: Path, index: int) -> Path:
    dest = case_dir / f"{index:02d}_{safe_filename(path.name)}"
    shutil.copy2(path, dest)
    return dest


def write_email_context(case_dir: Path, subject: str, sender_name: str, sender_email: str, body: str) -> None:
    content = f"Subject: {subject}\nFrom: {sender_name} <{sender_email}>\n\n{body}"
    (case_dir / "email_context.txt").write_text(content, encoding="utf-8")


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def format_service(service: str, operation: str) -> str:
    if service and operation:
        return f"{service}.{operation}"
    return service or operation or "未识别"


def summarize_detail(code: str, detail: str) -> str:
    text = f"{code} {detail}".strip()
    if len(text) <= 900:
        return text
    snippets = []
    for needle in (
        "Provided XML service",
        "fixed value of '3.0.30'",
        "marketinfo:country",
        "basicudi:specialDevice",
        "already exists",
    ):
        idx = text.find(needle)
        if idx >= 0:
            snippets.append(text[max(0, idx - 160): idx + 360])
    if snippets:
        return " ... ".join(normalize_space(item) for item in snippets)[:1200]
    return text[:900] + " ..."


def build_reply(item: MailItem) -> tuple[str, str]:
    subject = item.subject if item.subject.lower().startswith("re:") else f"Re: {item.subject}"
    attachment_notes = []
    for att in item.attachments:
        attachment_notes.append(f"- {att.name}")
        for line in att.analysis:
            attachment_notes.append(f"  {line}")

    if not attachment_notes:
        attachment_notes.append("- 邮件中未发现可自动解析的附件；以下判断基于邮件正文关键词，需要补充 response XML 或源 Excel 后确认。")

    likely_tool_updates = infer_tool_updates(item)
    body = f"""您好，

我看了这封邮件里和 EUDAMED/XML 相关的内容，初步判断如下：

为什么发生上传错误 / 可能出错的地方：
{chr(10).join(attachment_notes)}

建议处理：
1. 先确认 EUDAMED bulk upload 页面选择的 service 与 XML 文件一致，例如 DEVICE.POST、UDI_DI.POST、UDI_DI.PATCH、MARKET_INFO.PATCH 等不能混用。
2. 如果 response XML 提到枚举值无效，请回到模板中检查对应字段，不要把产品名称、型号或自由文本填入官方枚举字段。
3. 如果是 PATCH 类服务，请确认模板中填写了 EUDAMED 网页显示的当前 version。
4. 如果是 ZIP 分片包，请按 manifest 顺序上传；依赖 DEVICE.POST 的 UDI_DI.POST 需要等前一步成功后再传。

工具待更新 / 可改进点：
{likely_tool_updates}

我建议先把 EUDAMED 返回的 response XML 和本次上传的源 XML/Excel 一起发我，我可以继续定位到具体字段和记录。

此邮件为草稿，请发送前再人工确认。
"""
    return subject, body


def infer_tool_updates(item: MailItem) -> str:
    notes = []
    haystack = (item.body + "\n" + "\n".join(" ".join(att.analysis) for att in item.attachments)).lower()
    if "does not match selected" in haystack:
        notes.append("- 在导出结果旁增加更醒目的 EUDAMED 页面 service 选择提示。")
    if "special device type" in haystack or "specialdevice" in haystack:
        notes.append("- 在导入预检中拦截 Special Device Type 非枚举值，并提示普通器械应留空。")
    if "version" in haystack and "patch" in haystack:
        notes.append("- 在 PATCH 导出前增强当前 version 缺失/格式错误提示。")
    if not notes:
        notes.append("- 根据该邮件暂未判断出必须更新工具；需要结合 response XML 的 operationDetail 再确认。")
    return "\n".join(notes)


def write_draft_file(item: MailItem, subject: str, body: str) -> Path:
    filename = safe_filename(f"{subject[:80]}.txt") or "draft.txt"
    path = OUT_DIR / filename
    path.write_text(f"To: {item.sender_email}\nSubject: {subject}\n\n{body}", encoding="utf-8")
    return path


def create_outlook_draft(item: MailItem, subject: str, body: str) -> None:
    if not item.sender_email:
        raise ValueError("Cannot create Outlook draft without sender email.")
    script = f"""
    tell application "Microsoft Outlook"
        set newMessage to make new outgoing message with properties {{subject:{as_applescript_string(subject)}, plain text content:{as_applescript_string(body)}}}
        make new recipient at newMessage with properties {{email address:{{address:{as_applescript_string(item.sender_email)}, name:{as_applescript_string(item.sender_name or item.sender_email)}}}}}
        save newMessage
    end tell
    """
    run_osascript(script)


def run_osascript(script: str) -> str:
    proc = subprocess.run(
        ["osascript", "-e", script],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "osascript failed")
    return proc.stdout


def first_text(node: ET.Element, names: set[str]) -> str:
    for child in node.iter():
        if local_name(child.tag) in names:
            text = "".join(child.itertext()).strip()
            if text:
                return text
    return ""


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse_address(value: str) -> tuple[str, str]:
    parsed = email.utils.parseaddr(value)
    return parsed[0], parsed[1]


def strip_html(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\\1>", " ", value)
    value = re.sub(r"(?s)<br\\s*/?>", "\n", value)
    value = re.sub(r"(?s)</p>", "\n", value)
    value = re.sub(r"(?s)<.*?>", " ", value)
    return html.unescape(re.sub(r"[ \\t]+", " ", value)).strip()


def safe_filename(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|]+", "_", value)
    value = re.sub(r"\\s+", " ", value).strip()
    return value[:120]


def as_applescript_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)
