#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EUDAMED数据验证器 v2.2 - BUG修复版
修复内容：
1. PI Expiration Date从日期字段改为布尔字段
2. 布尔值False判断逻辑修复
3. 字段名映射已在读取器中处理
4. Device Status枚举值保持正确
5. Parent Basic UDI-DI智能验证（支持两种Service类型）
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple

class ValidationError:
    """验证错误"""
    
    def __init__(self, sheet: str, row: int, field: str, value: any, 
                 error_type: str, message: str, suggestion: str = ''):
        self.sheet = sheet
        self.row = row
        self.field = field
        self.value = value
        self.error_type = error_type
        self.message = message
        self.suggestion = suggestion
    
    def __str__(self):
        return f"[{self.sheet}] 行{self.row} - {self.field}: {self.message} (当前值: {self.value})"
    
    def to_dict(self):
        return {
            'sheet': self.sheet,
            'row': self.row,
            'field': self.field,
            'value': str(self.value),
            'error_type': self.error_type,
            'message': self.message,
            'suggestion': self.suggestion
        }

class DataValidator:
    """数据验证器 - 四层验证引擎"""
    
    # 枚举值定义
    ENUM_VALUES = {
        'Issuing Entity': ['GS1', 'HIBCC', 'ICCBBA', 'IFA', 'EUDAMED'],
        'Risk Class': ['Class I', 'Class IIa', 'Class IIb', 'Class III',
                      'Class A', 'Class B', 'Class C', 'Class D',
                      'AIMDD', 'IVD Annex II List A', 'IVD Annex II List B',
                      'IVD Self Testing', 'IVD General'],
        'Applicable Legislation': ['MDR', 'IVDR', 'MDD', 'AIMDD', 'IVDD'],
        'Device Type': ['Regular Device', 'System', 'Procedure Pack'],
        'Device Status': ['On the EU market', 'No longer placed on the EU market',
                         'Not intended for the EU market'],
        'Country Code': ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
                        'DE', 'EL', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                        'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'IS', 'LI', 'NO',
                        'TR', 'XI'],
        'Language': ['bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr',
                    'ga', 'hr', 'hu', 'is', 'it', 'lt', 'lv', 'mt', 'nl', 'no',
                    'pl', 'pt', 'ro', 'sk', 'sl', 'sv', 'tr'],
        'CMR Type': ['1A', '1B']
    }
    
    # EU/EEA国家代码前缀
    EU_COUNTRY_CODES = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
                        'DE', 'EL', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                        'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'IS', 'LI', 'NO']
    
    def __init__(self, data: Dict[str, List[Dict]]):
        self.data = data
        self.errors = []
        self.warnings = []
        self.basic_by_code = {
            str(row.get('Basic UDI-DI Code') or '').strip(): row
            for row in self.data.get('Basic UDI-DI', [])
            if str(row.get('Basic UDI-DI Code') or '').strip()
        }

    def _udi_legislation(self, row: Dict) -> str:
        """Return the Applicable Legislation for a UDI-DI row via its parent Basic."""
        parent_code = str(row.get('Parent Basic UDI-DI') or '').strip()
        basic = self.basic_by_code.get(parent_code, {})
        return str(basic.get('Applicable Legislation') or row.get('Applicable Legislation') or '').strip().upper()

    def _requires_latex_field(self, row: Dict) -> bool:
        """Containing Latex is required only for MDR/MDD/AIMDD profiles, not IVDR/IVDD."""
        return self._udi_legislation(row) in {'MDR', 'MDD', 'AIMDD'}
    
    def validate_all(self) -> Tuple[List[ValidationError], List[ValidationError]]:
        """执行所有验证"""
        print("  开始四层数据验证...")
        
        # 第一层：格式验证
        print("    [1/4] 格式验证...")
        self._layer1_format_validation()
        
        # 第二层：完整性验证
        print("    [2/4] 完整性验证...")
        self._layer2_completeness_validation()
        
        # 第三层：有效性验证
        print("    [3/4] 有效性验证...")
        self._layer3_validity_validation()
        
        # 第四层：业务规则验证
        print("    [4/4] 业务规则验证...")
        self._layer4_business_rules_validation()
        
        print(f"  ✓ 验证完成：发现 {len(self.errors)} 个错误，{len(self.warnings)} 个警告")
        
        return self.errors, self.warnings
    
    def _layer1_format_validation(self):
        """第一层：格式验证"""
        # 验证Basic UDI-DI
        for row in self.data.get('Basic UDI-DI', []):
            self._validate_date_format(row, 'Basic UDI-DI')
            self._validate_boolean_format(row, 'Basic UDI-DI')
            self._validate_udi_code_format(row, 'Basic UDI-DI')
        
        # 验证UDI-DI
        for row in self.data.get('UDI-DI', []):
            self._validate_date_format(row, 'UDI-DI')
            self._validate_boolean_format(row, 'UDI-DI')
            self._validate_udi_code_format(row, 'UDI-DI')
            self._validate_url_format(row, 'UDI-DI')
            self._validate_email_format(row, 'UDI-DI')
        
        # 验证Market Information
        for row in self.data.get('Market Information', []):
            self._validate_date_format(row, 'Market Information')
    
    def _validate_date_format(self, row: Dict, sheet: str):
        """验证日期格式（YYYY-MM-DD）"""
        # PI 字段在当前模板中是“是否包含该生产标识”的布尔开关，不是实际日期值
        date_fields = ['Start Date', 'End Date']
        
        for field in date_fields:
            value = row.get(field, '')
            # BUG FIX 2: 使用is not None判断
            if value is not None and value != '':
                if not self._is_valid_date(value):
                    self.errors.append(ValidationError(
                        sheet, row.get('_row_number', '?'), field, value,
                        'FORMAT_ERROR',
                        '日期格式不正确',
                        '请使用YYYY-MM-DD格式，例如：2026-12-31'
                    ))
    
    def _is_valid_date(self, date_str: str) -> bool:
        """检查日期格式是否有效"""
        if not isinstance(date_str, str):
            return False
        
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False
        
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def _validate_boolean_format(self, row: Dict, sheet: str):
        """验证布尔值格式（TRUE/FALSE）"""
        boolean_fields = [
            'Active Device', 'Measuring Function', 'Administer Medicine',
            'Implantable', 'Reusable Surgical Instrument', 'Presence of Human Tissues',
            'Presence of Animal Tissues', 'Medicinal Product Device',
            'Companion Diagnostic (IVDR)', 'Near Patient Testing (IVDR)',
            'Self-Testing (IVDR)', 'Professional Testing (IVDR)',
            'Instrument (IVDR)', 'Kit (IVDR)', 'Microbial Origin (IVDR)',
            'Is it a Kit', 'Reagent', 'Presence of Medicinal Substance',
            'Single Use Device', 'Device Labelled as Sterile',
            'Needs Sterilisation Before Use', 'Containing Latex',
            'Reprocessed Single Use Device', 'New Device (IVDR)',
            'Trade Name Applicable', 'Placed on Market',
            # BUG FIX 1: 添加PI字段（这些是布尔字段，不是日期字段）
            'PI Lot/Batch Number', 'PI Expiration Date', 'PI Manufacturing Date',
            'PI Serial Number', 'PI Software Identification'
        ]
        
        for field in boolean_fields:
            value = row.get(field, '')
            # BUG FIX 2: 使用is not None判断，避免False被当作空值
            if value is not None and value != '':
                # 处理布尔类型（Excel可能存储为bool）
                if isinstance(value, bool):
                    continue  # 布尔类型直接通过
                # 处理字符串类型
                if str(value).upper() not in ['TRUE', 'FALSE']:
                    self.errors.append(ValidationError(
                        sheet, row.get('_row_number', '?'), field, value,
                        'FORMAT_ERROR',
                        '布尔值格式不正确',
                        '请输入TRUE或FALSE（必须大写）'
                    ))
    
    def _validate_udi_code_format(self, row: Dict, sheet: str):
        """验证UDI代码格式"""
        udi_fields = ['Basic UDI-DI Code', 'UDI-DI Code', 'Secondary UDI-DI Code',
                     'Unit of Use DI Code', 'DM DI Code']
        
        for field in udi_fields:
            value = row.get(field, '')
            if value is not None and value != '':
                if not self._is_valid_udi_code(value):
                    self.errors.append(ValidationError(
                        sheet, row.get('_row_number', '?'), field, value,
                        'FORMAT_ERROR',
                        'UDI代码格式不正确',
                        'UDI代码应为8-50位字母数字字符'
                    ))
    
    def _is_valid_udi_code(self, code: str) -> bool:
        """检查UDI代码格式"""
        if not isinstance(code, str):
            return False
        # UDI代码：8-50位字母数字字符
        pattern = r'^[A-Za-z0-9]{8,50}$'
        return bool(re.match(pattern, code))
    
    def _validate_url_format(self, row: Dict, sheet: str):
        """验证URL格式"""
        url_fields = ['Additional Information URL', 'eIFU URL', 'Public Website']
        
        for field in url_fields:
            value = row.get(field, '')
            if value is not None and value != '':
                if not self._is_valid_url(value):
                    self.errors.append(ValidationError(
                        sheet, row.get('_row_number', '?'), field, value,
                        'FORMAT_ERROR',
                        'URL格式不正确',
                        '请输入有效的URL，例如：https://example.com'
                    ))
    
    def _is_valid_url(self, url: str) -> bool:
        """检查URL格式"""
        if not isinstance(url, str):
            return False
        pattern = r'^https?://[^\s]+$'
        return bool(re.match(pattern, url))
    
    def _validate_email_format(self, row: Dict, sheet: str):
        """验证邮箱格式"""
        email_fields = ['Public Email']
        
        for field in email_fields:
            value = row.get(field, '')
            if value is not None and value != '':
                if not self._is_valid_email(value):
                    self.errors.append(ValidationError(
                        sheet, row.get('_row_number', '?'), field, value,
                        'FORMAT_ERROR',
                        '邮箱格式不正确',
                        '请输入有效的邮箱地址'
                    ))
    
    def _is_valid_email(self, email: str) -> bool:
        """检查邮箱格式"""
        if not isinstance(email, str):
            return False
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def _layer2_completeness_validation(self):
        """第二层：完整性验证"""
        # 验证Basic UDI-DI必填字段
        basic_udi_required = [
            'Basic UDI-DI Code', 'Issuing Entity', 'Manufacturer SRN',
            'Risk Class', 'Applicable Legislation', 'Device Type',
            'Device Name/Model', 'EMDN Code'
        ]
        
        for row in self.data.get('Basic UDI-DI', []):
            for field in basic_udi_required:
                value = row.get(field, '')
                # BUG FIX 2: 使用is not None判断
                if value is None or value == '':
                    self.errors.append(ValidationError(
                        'Basic UDI-DI', row.get('_row_number', '?'), field, value,
                        'REQUIRED_FIELD_MISSING',
                        '必填字段缺失',
                        '请填写此字段'
                    ))
        
        # 验证UDI-DI必填字段
        udi_di_required = [
            'Parent Basic UDI-DI', 'UDI-DI Code', 'UDI-DI Issuing Entity',
            'Device Status', 'Single Use Device', 'Device Labelled as Sterile',
            'Trade Name Applicable',
            'Nomenclature Code'
        ]
        
        for row in self.data.get('UDI-DI', []):
            for field in udi_di_required:
                value = row.get(field, '')
                # BUG FIX 2: 使用is not None判断，避免False被当作空值
                if value is None or value == '':
                    self.errors.append(ValidationError(
                        'UDI-DI', row.get('_row_number', '?'), field, value,
                        'REQUIRED_FIELD_MISSING',
                        '必填字段缺失',
                        '请填写此字段'
                    ))

            if self._requires_latex_field(row):
                value = row.get('Containing Latex', '')
                if value is None or value == '':
                    self.errors.append(ValidationError(
                        'UDI-DI', row.get('_row_number', '?'), 'Containing Latex', value,
                        'REQUIRED_FIELD_MISSING',
                        '必填字段缺失',
                        'MDR/MDD/AIMDD 设备需要填写 Containing Latex；IVDR/IVDD 不需要。'
                    ))
            
            # 条件必填：Trade Name Applicable为TRUE时，Trade Name为必填
            trade_name_applicable = row.get('Trade Name Applicable', '')
            if trade_name_applicable and str(trade_name_applicable).upper() == 'TRUE':
                trade_name = row.get('Trade Name', '')
                if not trade_name or trade_name == '':
                    self.errors.append(ValidationError(
                        'UDI-DI', row.get('_row_number', '?'), 'Trade Name', trade_name,
                        'CONDITIONAL_REQUIRED_MISSING',
                        '当Trade Name Applicable为TRUE时，Trade Name为必填',
                        '请填写Trade Name或将Trade Name Applicable改为FALSE'
                    ))
    
    def _layer3_validity_validation(self):
        """第三层：有效性验证"""
        # 验证Basic UDI-DI枚举值
        for row in self.data.get('Basic UDI-DI', []):
            self._validate_enum_value(row, 'Basic UDI-DI', 'Issuing Entity')
            self._validate_enum_value(row, 'Basic UDI-DI', 'Risk Class')
            self._validate_enum_value(row, 'Basic UDI-DI', 'Applicable Legislation')
            self._validate_enum_value(row, 'Basic UDI-DI', 'Device Type')
        
        # 验证UDI-DI枚举值
        for row in self.data.get('UDI-DI', []):
            self._validate_enum_value(row, 'UDI-DI', 'UDI-DI Issuing Entity', 'Issuing Entity')
            self._validate_enum_value(row, 'UDI-DI', 'Device Status')
        
        # BUG FIX 5: 智能验证Parent Basic UDI-DI引用
        self._validate_parent_basic_udi_di_references()
        
        # 验证UDI-DI Code引用（Market Information等）
        self._validate_udi_di_code_references()
    
    def _validate_enum_value(self, row: Dict, sheet: str, field: str, enum_key: str = None):
        """验证枚举值"""
        if enum_key is None:
            enum_key = field
        
        value = row.get(field, '')
        if value is not None and value != '':
            valid_values = self.ENUM_VALUES.get(enum_key, [])
            if valid_values and value not in valid_values:
                self.errors.append(ValidationError(
                    sheet, row.get('_row_number', '?'), field, value,
                    'INVALID_ENUM_VALUE',
                    '枚举值无效',
                    f'有效值：{", ".join(valid_values)}'
                ))
    
    def _validate_parent_basic_udi_di_references(self):
        """验证UDI-DI的Parent Basic UDI-DI引用"""
        # BUG FIX 5: 智能检测Service类型
        basic_udi_data = self.data.get('Basic UDI-DI', [])
        udi_di_data = self.data.get('UDI-DI', [])
        
        if len(basic_udi_data) > 0:
            # Service 1: Upload of Basic UDI and UDI-DI
            # 验证Parent Basic UDI-DI必须在Basic UDI-DI工作表中存在
            basic_udi_codes = [row.get('Basic UDI-DI Code', '') for row in basic_udi_data]
            
            for row in udi_di_data:
                parent_code = row.get('Parent Basic UDI-DI', '')
                if parent_code and parent_code not in basic_udi_codes:
                    self.errors.append(ValidationError(
                        'UDI-DI', row.get('_row_number', '?'), 'Parent Basic UDI-DI', parent_code,
                        'REFERENCE_ERROR',
                        '引用的Basic UDI-DI不存在',
                        f'请在Basic UDI-DI工作表中添加代码为 {parent_code} 的记录'
                    ))
        else:
            # Service 2: Upload of UDI-DI for existing basic udi-di
            # Basic UDI-DI已在EUDAMED系统中，只发出警告
            for row in udi_di_data:
                parent_code = row.get('Parent Basic UDI-DI', '')
                if parent_code:
                    self.warnings.append(ValidationError(
                        'UDI-DI', row.get('_row_number', '?'), 'Parent Basic UDI-DI', parent_code,
                        'REFERENCE_WARNING',
                        '引用的Basic UDI-DI未在Excel中提供，假设在EUDAMED系统中已存在',
                        '如果该Basic UDI-DI不存在于系统中，上传将失败'
                    ))
    
    def _validate_udi_di_code_references(self):
        """验证UDI-DI Code引用"""
        udi_di_codes = [row.get('UDI-DI Code', '') for row in self.data.get('UDI-DI', [])]
        
        # 验证Market Information中的UDI-DI Code引用
        for row in self.data.get('Market Information', []):
            udi_di_code = row.get('UDI-DI Code', '')
            if udi_di_code and udi_di_code not in udi_di_codes:
                self.warnings.append(ValidationError(
                    'Market Information', row.get('_row_number', '?'), 'UDI-DI Code', udi_di_code,
                    'REFERENCE_WARNING',
                    '引用的UDI-DI不存在',
                    f'请在UDI-DI工作表中添加代码为 {udi_di_code} 的记录'
                ))
    
    def _layer4_business_rules_validation(self):
        """第四层：业务规则验证"""
        # BR-UDID-018: 非欧盟制造商必须有授权代表
        for row in self.data.get('Basic UDI-DI', []):
            manufacturer_srn = row.get('Manufacturer SRN', '')
            if manufacturer_srn and not self._is_eu_manufacturer(manufacturer_srn):
                ar_srn = row.get('Authorised Representative SRN', '')
                if not ar_srn or ar_srn == '':
                    self.errors.append(ValidationError(
                        'Basic UDI-DI', row.get('_row_number', '?'), 'Authorised Representative SRN', ar_srn,
                        'BUSINESS_RULE_VIOLATION',
                        '非欧盟制造商必须有授权代表（BR-UDID-018）',
                        '请填写Authorised Representative SRN'
                    ))
    
    def _is_eu_manufacturer(self, srn: str) -> bool:
        """检查是否为欧盟制造商"""
        if not srn or len(srn) < 2:
            return False
        country_code = srn[:2].upper()
        return country_code in self.EU_COUNTRY_CODES
