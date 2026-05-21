#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证模块 - 四层验证引擎

第一层：格式验证 (Format Validation)
第二层：完整性验证 (Completeness Validation)
第三层：有效性验证 (Validity Validation)
第四层：业务规则验证 (Business Rule Validation)
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Tuple


class ValidationError:
    """验证错误类"""
    
    def __init__(self, sheet, row, field, value, error_type, description, suggestion=""):
        self.sheet = sheet
        self.row = row
        self.field = field
        self.value = value
        self.error_type = error_type
        self.description = description
        self.suggestion = suggestion
    
    def __str__(self):
        return (f"[{self.sheet}] 行{self.row} - {self.field}: "
                f"{self.description} (当前值: {self.value})")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'sheet': self.sheet,
            'row': self.row,
            'field': self.field,
            'value': str(self.value),
            'error_type': self.error_type,
            'description': self.description,
            'suggestion': self.suggestion
        }


class DataValidator:
    """数据验证器 - 四层验证引擎"""
    
    # 枚举值定义
    ENUM_VALUES = {
        'Issuing Entity': ['GS1', 'HIBCC', 'ICCBBA'],
        'Risk Class': ['Class I', 'Class IIa', 'Class IIb', 'Class III', 
                      'Class A', 'Class B', 'Class C', 'Class D'],
        'Applicable Legislation': ['MDR', 'IVDR', 'MDD', 'AIMDD', 'IVDD'],
        'Device Type': ['Regular Device', 'System', 'Procedure Pack'],
        'Device Status': ['On the EU market', 'No longer placed on the EU market', 
                         'Not intended for the EU market'],
        'Country Code': ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
                        'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                        'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'IS', 'LI', 'NO'],
        'Language': ['bg', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fi', 'fr',
                    'hr', 'hu', 'it', 'lt', 'lv', 'mt', 'nl', 'pl', 'pt', 'ro',
                    'sk', 'sl', 'sv'],
        'CMR Type': ['1A', '1B']
    }
    
    # EU/EEA国家代码前缀
    EU_COUNTRY_CODES = ['AT', 'BE', 'BG', 'HR', 'CY', 'CZ', 'DK', 'EE', 'FI', 'FR',
                        'DE', 'GR', 'HU', 'IE', 'IT', 'LV', 'LT', 'LU', 'MT', 'NL',
                        'PL', 'PT', 'RO', 'SK', 'SI', 'ES', 'SE', 'IS', 'LI', 'NO']
    
    def __init__(self, data: Dict[str, List[Dict]]):
        self.data = data
        self.errors = []
        self.warnings = []
    
    def validate_all(self) -> Tuple[List[ValidationError], List[ValidationError]]:
        """执行所有验证"""
        print("\n  开始四层数据验证...")
        
        # 第一层：格式验证
        print("    [1/4] 格式验证...")
        self.validate_formats()
        
        # 第二层：完整性验证
        print("    [2/4] 完整性验证...")
        self.validate_completeness()
        
        # 第三层：有效性验证
        print("    [3/4] 有效性验证...")
        self.validate_validity()
        
        # 第四层：业务规则验证
        print("    [4/4] 业务规则验证...")
        self.validate_business_rules()
        
        print(f"\n  ✓ 验证完成：发现 {len(self.errors)} 个错误，{len(self.warnings)} 个警告")
        
        return self.errors, self.warnings
    
    # ========== 第一层：格式验证 ==========
    
    def validate_formats(self):
        """格式验证"""
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
        date_fields = ['Start Date', 'End Date', 'PI Expiration Date', 'PI Manufacturing Date']
        
        for field in date_fields:
            value = row.get(field, '')
            if value and value != '':
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
            'Trade Name Applicable', 'Placed on Market'
        ]
        
        for field in boolean_fields:
            value = row.get(field, '')
            if value and value != '':
                if str(value).upper() not in ['TRUE', 'FALSE']:
                    self.errors.append(ValidationError(
                        sheet, row.get('_row_number', '?'), field, value,
                        'FORMAT_ERROR',
                        '布尔值格式不正确',
                        '请输入TRUE或FALSE（必须大写）'
                    ))
    
    def _validate_udi_code_format(self, row: Dict, sheet: str):
        """验证UDI代码格式"""
        if sheet == 'Basic UDI-DI':
            code_field = 'Basic UDI-DI Code'
        else:
            code_field = 'UDI-DI Code'
        
        value = row.get(code_field, '')
        if value:
            # UDI代码应为8-50位的字母数字组合
            if not re.match(r'^[A-Za-z0-9]{8,50}$', str(value)):
                self.errors.append(ValidationError(
                    sheet, row.get('_row_number', '?'), code_field, value,
                    'FORMAT_ERROR',
                    'UDI代码格式不正确',
                    'UDI代码应为8-50位的字母数字组合'
                ))
    
    def _validate_url_format(self, row: Dict, sheet: str):
        """验证URL格式"""
        url_fields = ['eIFU URL', 'Public Website']
        
        for field in url_fields:
            value = row.get(field, '')
            if value and value != '':
                if not (str(value).startswith('http://') or str(value).startswith('https://')):
                    self.errors.append(ValidationError(
                        sheet, row.get('_row_number', '?'), field, value,
                        'FORMAT_ERROR',
                        'URL格式不正确',
                        'URL必须以http://或https://开头'
                    ))
    
    def _validate_email_format(self, row: Dict, sheet: str):
        """验证邮箱格式"""
        email_fields = ['Public Email']
        
        for field in email_fields:
            value = row.get(field, '')
            if value and value != '':
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, str(value)):
                    self.errors.append(ValidationError(
                        sheet, row.get('_row_number', '?'), field, value,
                        'FORMAT_ERROR',
                        '邮箱格式不正确',
                        '请输入有效的邮箱地址，例如：contact@example.com'
                    ))
    
    # ========== 第二层：完整性验证 ==========
    
    def validate_completeness(self):
        """完整性验证"""
        # 验证Basic UDI-DI必填字段
        basic_udi_required = [
            'Basic UDI-DI Code', 'Issuing Entity', 'Manufacturer SRN',
            'Risk Class', 'Applicable Legislation', 'Device Type',
            'EMDN Code', 'Is it a Kit', 'Reagent', 
            'Presence of Medicinal Substance'
        ]
        
        for row in self.data.get('Basic UDI-DI', []):
            for field in basic_udi_required:
                if not row.get(field) or row.get(field) == '':
                    self.errors.append(ValidationError(
                        'Basic UDI-DI', row.get('_row_number', '?'), field, '',
                        'MISSING_REQUIRED',
                        '必填字段缺失',
                        f'请填写{field}字段'
                    ))
            
            # Device Name/Model二选一验证
            if not row.get('Device Name/Model') and not row.get('Device Model'):
                self.errors.append(ValidationError(
                    'Basic UDI-DI', row.get('_row_number', '?'), 
                    'Device Name/Model', '',
                    'MISSING_REQUIRED',
                    'Device Name/Model和Device Model必须至少填写一个',
                    '请填写设备名称或型号'
                ))
        
        # 验证UDI-DI必填字段
        udi_di_required = [
            'Parent Basic UDI-DI', 'UDI-DI Code', 'UDI-DI Issuing Entity',
            'Device Status', 'Single Use Device', 'Device Labelled as Sterile',
            'Containing Latex', 'Trade Name Applicable',
            'PI Lot/Batch Number', 'PI Expiration Date', 'Nomenclature Code'
        ]
        
        for row in self.data.get('UDI-DI', []):
            for field in udi_di_required:
                if not row.get(field) or row.get(field) == '':
                    self.errors.append(ValidationError(
                        'UDI-DI', row.get('_row_number', '?'), field, '',
                        'MISSING_REQUIRED',
                        '必填字段缺失',
                        f'请填写{field}字段'
                    ))
            
            # Trade Name条件必填验证
            if row.get('Trade Name Applicable', '').upper() == 'TRUE':
                if not row.get('Trade Name'):
                    self.errors.append(ValidationError(
                        'UDI-DI', row.get('_row_number', '?'), 'Trade Name', '',
                        'CONDITIONAL_REQUIRED',
                        '当Trade Name Applicable为TRUE时，Trade Name为必填',
                        '请填写Trade Name字段'
                    ))
        
        # 验证Market Information必填字段
        for row in self.data.get('Market Information', []):
            required = ['UDI-DI Code', 'Country Code', 'Placed on Market']
            for field in required:
                if not row.get(field) or row.get(field) == '':
                    self.errors.append(ValidationError(
                        'Market Information', row.get('_row_number', '?'), field, '',
                        'MISSING_REQUIRED',
                        '必填字段缺失',
                        f'请填写{field}字段'
                    ))
    
    # ========== 第三层：有效性验证 ==========
    
    def validate_validity(self):
        """有效性验证"""
        # 验证枚举值
        for row in self.data.get('Basic UDI-DI', []):
            self._validate_enum_value(row, 'Basic UDI-DI', 'Issuing Entity')
            self._validate_enum_value(row, 'Basic UDI-DI', 'Risk Class')
            self._validate_enum_value(row, 'Basic UDI-DI', 'Applicable Legislation')
            self._validate_enum_value(row, 'Basic UDI-DI', 'Device Type')
        
        for row in self.data.get('UDI-DI', []):
            self._validate_enum_value(row, 'UDI-DI', 'UDI-DI Issuing Entity', 'Issuing Entity')
            self._validate_enum_value(row, 'UDI-DI', 'Device Status')
        
        for row in self.data.get('Market Information', []):
            self._validate_enum_value(row, 'Market Information', 'Country Code')
        
        # 验证关联关系
        self._validate_relationships()
    
    def _validate_enum_value(self, row: Dict, sheet: str, field: str, enum_key: str = None):
        """验证枚举值"""
        if enum_key is None:
            enum_key = field
        
        value = row.get(field, '')
        if value and value != '':
            valid_values = self.ENUM_VALUES.get(enum_key, [])
            if valid_values and value not in valid_values:
                self.errors.append(ValidationError(
                    sheet, row.get('_row_number', '?'), field, value,
                    'INVALID_ENUM',
                    '枚举值无效',
                    f'有效值为：{", ".join(valid_values)}'
                ))
    
    def _validate_relationships(self):
        """验证关联关系"""
        # 收集所有Basic UDI-DI代码
        basic_udi_codes = set()
        for row in self.data.get('Basic UDI-DI', []):
            code = row.get('Basic UDI-DI Code', '')
            if code:
                basic_udi_codes.add(code)
        
        # 验证UDI-DI的Parent Basic UDI-DI是否存在
        for row in self.data.get('UDI-DI', []):
            parent_code = row.get('Parent Basic UDI-DI', '')
            if parent_code and parent_code not in basic_udi_codes:
                self.errors.append(ValidationError(
                    'UDI-DI', row.get('_row_number', '?'), 'Parent Basic UDI-DI', parent_code,
                    'INVALID_REFERENCE',
                    '引用的Basic UDI-DI不存在',
                    f'请确保Basic UDI-DI工作表中存在代码为{parent_code}的记录'
                ))
        
        # 收集所有UDI-DI代码
        udi_di_codes = set()
        for row in self.data.get('UDI-DI', []):
            code = row.get('UDI-DI Code', '')
            if code:
                udi_di_codes.add(code)
        
        # 验证Market Information的UDI-DI Code是否存在
        for row in self.data.get('Market Information', []):
            udi_code = row.get('UDI-DI Code', '')
            if udi_code and udi_code not in udi_di_codes:
                self.warnings.append(ValidationError(
                    'Market Information', row.get('_row_number', '?'), 'UDI-DI Code', udi_code,
                    'INVALID_REFERENCE',
                    '引用的UDI-DI不存在',
                    f'请确保UDI-DI工作表中存在代码为{udi_code}的记录'
                ))
    
    # ========== 第四层：业务规则验证 ==========
    
    def validate_business_rules(self):
        """业务规则验证"""
        # RULE-00018: 非欧盟制造商必须有授权代表
        for row in self.data.get('Basic UDI-DI', []):
            manufacturer_srn = row.get('Manufacturer SRN', '')
            if manufacturer_srn:
                # 提取国家代码（SRN前两位）
                country_code = manufacturer_srn[:2].upper()
                
                # 如果不是EU/EEA国家
                if country_code not in self.EU_COUNTRY_CODES:
                    auth_rep = row.get('Authorised Representative SRN', '')
                    if not auth_rep or auth_rep == '':
                        self.errors.append(ValidationError(
                            'Basic UDI-DI', row.get('_row_number', '?'),
                            'Authorised Representative SRN', '',
                            'BUSINESS_RULE',
                            f'非欧盟制造商（{country_code}）必须填写授权代表SRN（RULE-00018）',
                            '请填写一个在EUDAMED注册的欧盟授权代表的SRN'
                        ))
        
        # RULE: IIb类植入物特殊验证
        for row in self.data.get('Basic UDI-DI', []):
            risk_class = row.get('Risk Class', '')
            implantable = row.get('Implantable', '').upper()
            
            if risk_class == 'Class IIb' and implantable == 'TRUE':
                special_field = row.get('Is Suture/Staple/Filling/Brace (IIb Implant)', '')
                if not special_field or special_field == '':
                    self.warnings.append(ValidationError(
                        'Basic UDI-DI', row.get('_row_number', '?'),
                        'Is Suture/Staple/Filling/Brace (IIb Implant)', '',
                        'BUSINESS_RULE',
                        'Class IIb植入物需要声明是否为缝合线、钉、牙填充物或牙套',
                        '请填写该字段（TRUE或FALSE）'
                    ))
        
        # 验证风险等级与法规的匹配
        for row in self.data.get('Basic UDI-DI', []):
            legislation = row.get('Applicable Legislation', '')
            risk_class = row.get('Risk Class', '')
            
            if legislation in ['MDR', 'MDD', 'AIMDD']:
                # MDR设备应使用Class I/IIa/IIb/III
                if risk_class not in ['Class I', 'Class IIa', 'Class IIb', 'Class III']:
                    if risk_class:  # 只有当有值时才报错
                        self.errors.append(ValidationError(
                            'Basic UDI-DI', row.get('_row_number', '?'),
                            'Risk Class', risk_class,
                            'BUSINESS_RULE',
                            f'{legislation}设备的风险等级应为Class I/IIa/IIb/III之一',
                            '请选择正确的风险等级'
                        ))
            
            elif legislation in ['IVDR', 'IVDD']:
                # IVDR设备应使用Class A/B/C/D
                if risk_class not in ['Class A', 'Class B', 'Class C', 'Class D']:
                    if risk_class:  # 只有当有值时才报错
                        self.errors.append(ValidationError(
                            'Basic UDI-DI', row.get('_row_number', '?'),
                            'Risk Class', risk_class,
                            'BUSINESS_RULE',
                            f'{legislation}设备的风险等级应为Class A/B/C/D之一',
                            '请选择正确的风险等级'
                        ))
