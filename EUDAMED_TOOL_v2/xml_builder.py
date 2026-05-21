#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML构建模块 - 生成符合EUDAMED规范的XML文件
"""

import xml.etree.ElementTree as ET
from xml.dom import minidom

# EUDAMED命名空间
NAMESPACE = "http://ec.europa.eu/fpis/eudamed/v3"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"

# 映射表
ISSUING_ENTITY_MAP = {
    "GS1": "9999",
    "HIBCC": "9998",
    "ICCBBA": "9997"
}

RISK_CLASS_MAP = {
    "Class I": "CLASS_I",
    "Class IIa": "CLASS_IIA",
    "Class IIb": "CLASS_IIB",
    "Class III": "CLASS_III",
    "Class A": "CLASS_A",
    "Class B": "CLASS_B",
    "Class C": "CLASS_C",
    "Class D": "CLASS_D"
}

DEVICE_TYPE_MAP = {
    "Regular Device": "REGULAR_DEVICE",
    "System": "SYSTEM",
    "Procedure Pack": "PROCEDURE_PACK"
}

DEVICE_STATUS_MAP = {
    "On the EU market": "ON_THE_MARKET",
    "No longer placed on the EU market": "NO_LONGER_PLACED_ON_THE_MARKET",
    "Not intended for the EU market": "NOT_INTENDED_FOR_EU_MARKET"
}


class XMLBuilder:
    """XML构建器

    此构建器根据传入的数据以及服务类型构建EUDAMED兼容的XML。新增的``schema_version``和
    ``service_type``参数允许调用者指定要使用的XSD版本号和上传服务类型。当``service_type``
    为``UDI_DI/POST``（即仅上传UDI‑DI）时，根元素将切换为``udiDis``，并且不会包含
    ``basicUdi``节点。在默认的``DEVICE/POST``模式下，其行为与先前版本一致。
    """

    def __init__(self, data, schema_version: str = "3.0.25", service_type: str = "DEVICE/POST"):
        #: 输入的数据字典，包含各工作表解析的结果
        self.data = data
        #: XML根节点对象
        self.root = None
        #: XSD版本号，可通过命令行指定
        self.schema_version = schema_version
        #: 服务类型，决定生成的XML结构
        self.service_type = (service_type or "DEVICE/POST").upper()
    
    def build(self):
        """构建完整的XML结构。

        根据 ``service_type`` 的取值生成不同的XML结构：

        * 当 ``service_type`` 为 ``UDI_DI/POST`` 时，仅构建 ``udiDi`` 对象的集合，根节点命名为
          ``udiDis``，适用于向已有的Basic UDI‑DI中新增UDI‑DI的场景（Service 2）。
        * 其他情况（默认 ``DEVICE/POST``）下，根节点为 ``devices``，每个 ``device`` 对应一条
          Basic UDI‑DI，并包含其关联的 ``udiDis`` 列表。
        """
        # Service 2：仅上传UDI-DI
        if self.service_type == "UDI_DI/POST":
            # 创建根元素 <udiDis>
            self.root = ET.Element(f"{{{NAMESPACE}}}udiDis")
            # 设置schemaLocation和version
            self.root.set(f"{{{XSI_NAMESPACE}}}schemaLocation", f"{NAMESPACE} eudamed-v3.xsd")
            self.root.set("version", self.schema_version)
            # 构建所有UDI-DI元素
            udi_di_list = self.data.get('UDI-DI', []) or []
            for udi_di_data in udi_di_list:
                # Parent Basic UDI-DI必须存在，防止创建无引用的UDI-DI
                parent_code = udi_di_data.get("Parent Basic UDI-DI", "")
                if parent_code:
                    udi_di_elem = self._build_udi_di(udi_di_data)
                    self.root.append(udi_di_elem)
            return self.root

        # 默认：Service 1，上传Basic UDI-DI及其UDI-DI
        # 创建根元素 <devices>
        self.root = ET.Element(f"{{{NAMESPACE}}}devices")
        # 设置schemaLocation和version
        self.root.set(f"{{{XSI_NAMESPACE}}}schemaLocation", f"{NAMESPACE} eudamed-v3.xsd")
        self.root.set("version", self.schema_version)
        
        # 为每个Basic UDI-DI创建设备元素
        basic_udis = self.data.get('Basic UDI-DI', []) or []
        for basic_udi_data in basic_udis:
            device_elem = self._build_device(basic_udi_data)
            self.root.append(device_elem)
        
        return self.root
    
    def _build_device(self, basic_udi_data):
        """构建单个设备元素"""
        device = self._create_element("device")
        
        # 添加Basic UDI-DI
        basic_udi = self._build_basic_udi(basic_udi_data)
        device.append(basic_udi)
        
        # 添加关联的UDI-DI列表
        basic_code = basic_udi_data.get('Basic UDI-DI Code', '')
        udi_dis = self._build_udi_dis(basic_code)
        if len(udi_dis) > 0:
            device.append(udi_dis)
        
        return device
    
    def _build_basic_udi(self, data):
        """构建Basic UDI-DI元素"""
        basic_udi = self._create_element("basicUdi")
        
        # DI标识
        di_id = self._create_sub_element(basic_udi, "diIdentifier")
        self._create_sub_element(di_id, "diCode", data.get("Basic UDI-DI Code", ""))
        issuing_entity = data.get("Issuing Entity", "GS1")
        self._create_sub_element(di_id, "issuingEntityCode", 
                                ISSUING_ENTITY_MAP.get(issuing_entity, "9999"))
        
        # 制造商SRN
        self._create_sub_element(basic_udi, "manufacturerSrn", 
                                data.get("Manufacturer SRN", ""))
        
        # 风险等级
        risk_class = data.get("Risk Class", "Class I")
        self._create_sub_element(basic_udi, "riskClass", 
                                RISK_CLASS_MAP.get(risk_class, "CLASS_I"))
        
        # 适用法规
        legislation = data.get("Applicable Legislation", "MDR")
        self._create_sub_element(basic_udi, "applicableLegislation", legislation)
        
        # 设备类型
        device_type = data.get("Device Type", "Regular Device")
        self._create_sub_element(basic_udi, "deviceType", 
                                DEVICE_TYPE_MAP.get(device_type, "REGULAR_DEVICE"))
        
        # 设备名称
        device_name = data.get("Device Name/Model", "") or data.get("Device Model", "")
        if device_name:
            names = self._create_sub_element(basic_udi, "names")
            name_elem = self._create_sub_element(names, "name")
            self._create_sub_element(name_elem, "name", device_name)
            self._create_sub_element(name_elem, "language", "en")
        
        # EMDN代码
        emdn_code = data.get("EMDN Code", "")
        if emdn_code:
            emdn = self._create_sub_element(basic_udi, "emdn")
            self._create_sub_element(emdn, "code", emdn_code)
        
        # 授权代表（如果有）
        auth_rep = data.get("Authorised Representative SRN", "")
        if auth_rep:
            self._create_sub_element(basic_udi, "authorisedRepresentativeSrn", auth_rep)
        
        # MDR适用属性
        mdr_props = self._create_sub_element(basic_udi, "mdrApplicableProperties")
        
        self._add_boolean_element(mdr_props, "activeDevice", 
                                 data.get("Active Device", "FALSE"))
        self._add_boolean_element(mdr_props, "measuringFunction", 
                                 data.get("Measuring Function", "FALSE"))
        self._add_boolean_element(mdr_props, "administerMedicine", 
                                 data.get("Administer Medicine", "FALSE"))
        self._add_boolean_element(mdr_props, "implantable", 
                                 data.get("Implantable", "FALSE"))
        self._add_boolean_element(mdr_props, "reusable", 
                                 data.get("Reusable Surgical Instrument", "FALSE"))
        self._add_boolean_element(mdr_props, "presenceOfHumanTissues", 
                                 data.get("Presence of Human Tissues", "FALSE"))
        self._add_boolean_element(mdr_props, "presenceOfAnimalTissues", 
                                 data.get("Presence of Animal Tissues", "FALSE"))
        self._add_boolean_element(mdr_props, "medicinalProduct", 
                                 data.get("Medicinal Product Device", "FALSE"))
        
        # IVDR适用属性（如果是IVDR设备）
        if legislation == "IVDR":
            ivdr_props = self._create_sub_element(basic_udi, "ivdrApplicableProperties")
            
            self._add_boolean_element(ivdr_props, "companionDiagnostics", 
                                     data.get("Companion Diagnostic (IVDR)", "FALSE"))
            self._add_boolean_element(ivdr_props, "nearPatientTesting", 
                                     data.get("Near Patient Testing (IVDR)", "FALSE"))
            self._add_boolean_element(ivdr_props, "selfTesting", 
                                     data.get("Self-Testing (IVDR)", "FALSE"))
            self._add_boolean_element(ivdr_props, "professionalTesting", 
                                     data.get("Professional Testing (IVDR)", "FALSE"))
            self._add_boolean_element(ivdr_props, "instrument", 
                                     data.get("Instrument (IVDR)", "FALSE"))
            self._add_boolean_element(ivdr_props, "kit", 
                                     data.get("Kit (IVDR)", "FALSE"))
            self._add_boolean_element(ivdr_props, "reagent", 
                                     data.get("Reagent", "FALSE"))
        
        return basic_udi
    
    def _build_udi_dis(self, parent_basic_code):
        """构建UDI-DI列表元素"""
        udi_dis = self._create_element("udiDis")
        
        # 查找所有关联的UDI-DI
        udi_di_list = self.data.get('UDI-DI', [])
        
        for udi_di_data in udi_di_list:
            if udi_di_data.get("Parent Basic UDI-DI", "") == parent_basic_code:
                udi_di = self._build_udi_di(udi_di_data)
                udi_dis.append(udi_di)
        
        return udi_dis
    
    def _build_udi_di(self, data):
        """构建UDI-DI元素"""
        udi_di = self._create_element("udiDi")
        
        # DI标识
        di_id = self._create_sub_element(udi_di, "diIdentifier")
        self._create_sub_element(di_id, "diCode", data.get("UDI-DI Code", ""))
        issuing_entity = data.get("UDI-DI Issuing Entity", "GS1")
        self._create_sub_element(di_id, "issuingEntityCode", 
                                ISSUING_ENTITY_MAP.get(issuing_entity, "9999"))
        
        # 设备状态
        status = data.get("Device Status", "On the EU market")
        self._create_sub_element(udi_di, "status", 
                                DEVICE_STATUS_MAP.get(status, "ON_THE_MARKET"))
        
        # 每销售单位数量
        qty = data.get("Quantity of Device", "1")
        if qty:
            self._create_sub_element(udi_di, "quantityOfDevice", str(qty))
        
        # 布尔属性
        self._add_boolean_element(udi_di, "singleUse", 
                                 data.get("Single Use Device", "TRUE"))
        self._add_boolean_element(udi_di, "sterile", 
                                 data.get("Device Labelled as Sterile", "FALSE"))
        self._add_boolean_element(udi_di, "sterilisationNeeded", 
                                 data.get("Needs Sterilisation Before Use", "FALSE"))
        self._add_boolean_element(udi_di, "containingLatex", 
                                 data.get("Containing Latex", "FALSE"))
        
        # 商品名
        trade_applicable = data.get("Trade Name Applicable", "TRUE").upper() == "TRUE"
        if trade_applicable:
            trade_name = data.get("Trade Name", "")
            if trade_name:
                trade_names = self._create_sub_element(udi_di, "tradeNames")
                tn_elem = self._create_sub_element(trade_names, "tradeName")
                self._create_sub_element(tn_elem, "tradeName", trade_name)
                self._create_sub_element(tn_elem, "language", "en")
        
        # 生产标识符
        pi = self._create_sub_element(udi_di, "productionIdentifiers")
        self._add_boolean_element(pi, "lotNumber", 
                                 data.get("PI Lot/Batch Number", "TRUE"))
        self._add_boolean_element(pi, "expirationDate", 
                                 data.get("PI Expiration Date", "TRUE"))
        self._add_boolean_element(pi, "manufacturingDate", 
                                 data.get("PI Manufacturing Date", "FALSE"))
        self._add_boolean_element(pi, "serialNumber", 
                                 data.get("PI Serial Number", "FALSE"))
        
        return udi_di
    
    def _create_element(self, tag):
        """创建带命名空间的元素"""
        return ET.Element(f"{{{NAMESPACE}}}{tag}")
    
    def _create_sub_element(self, parent, tag, text=None):
        """创建子元素"""
        elem = ET.SubElement(parent, f"{{{NAMESPACE}}}{tag}")
        if text is not None and text != '':
            elem.text = str(text)
        return elem
    
    def _add_boolean_element(self, parent, tag, value):
        """添加布尔元素"""
        bool_val = str(value).upper() == "TRUE"
        self._create_sub_element(parent, tag, "true" if bool_val else "false")
    
    def to_string(self, pretty=True):
        """转换为字符串"""
        if pretty:
            rough_string = ET.tostring(self.root, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ", encoding='UTF-8')
        else:
            return ET.tostring(self.root, encoding='UTF-8')
    
    def save(self, filepath):
        """保存到文件"""
        xml_bytes = self.to_string(pretty=True)
        with open(filepath, 'wb') as f:
            f.write(xml_bytes)
