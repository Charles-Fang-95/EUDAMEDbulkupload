#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报告日志模块 - 生成详细的处理报告
"""

from datetime import datetime
import json


class ReportLogger:
    """报告生成器"""
    
    def __init__(self, input_file, output_file):
        self.input_file = input_file
        self.output_file = output_file
        self.start_time = datetime.now()
        self.end_time = None
        self.stats = {
            'basic_udi_count': 0,
            'udi_di_count': 0,
            'market_info_count': 0,
            'error_count': 0,
            'warning_count': 0
        }
        self.errors = []
        self.warnings = []
    
    def set_stats(self, data, errors, warnings):
        """设置统计信息"""
        self.stats['basic_udi_count'] = len(data.get('Basic UDI-DI', []))
        self.stats['udi_di_count'] = len(data.get('UDI-DI', []))
        self.stats['market_info_count'] = len(data.get('Market Information', []))
        self.stats['error_count'] = len(errors)
        self.stats['warning_count'] = len(warnings)
        self.errors = errors
        self.warnings = warnings
    
    def finish(self):
        """标记处理完成"""
        self.end_time = datetime.now()
    
    def generate_console_report(self):
        """生成控制台报告"""
        print("\n" + "="*70)
        print("处理报告")
        print("="*70)
        
        # 基本信息
        print(f"\n输入文件: {self.input_file}")
        print(f"输出文件: {self.output_file}")
        print(f"处理时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            print(f"耗时: {duration:.2f}秒")
        
        # 数据统计
        print(f"\n数据统计:")
        print(f"  Basic UDI-DI记录: {self.stats['basic_udi_count']}")
        print(f"  UDI-DI记录: {self.stats['udi_di_count']}")
        print(f"  市场信息记录: {self.stats['market_info_count']}")
        
        # 验证结果
        print(f"\n验证结果:")
        print(f"  错误: {self.stats['error_count']}")
        print(f"  警告: {self.stats['warning_count']}")
        
        # 显示错误详情
        if self.errors:
            print(f"\n错误详情（前10条）:")
            for i, error in enumerate(self.errors[:10], 1):
                print(f"  {i}. {error}")
            if len(self.errors) > 10:
                print(f"  ... 还有 {len(self.errors) - 10} 个错误")
        
        # 显示警告详情
        if self.warnings:
            print(f"\n警告详情（前5条）:")
            for i, warning in enumerate(self.warnings[:5], 1):
                print(f"  {i}. {warning}")
            if len(self.warnings) > 5:
                print(f"  ... 还有 {len(self.warnings) - 5} 个警告")
        
        print("\n" + "="*70)
    
    def generate_html_report(self, filepath):
        """生成HTML格式报告"""
        duration = 0
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EUDAMED转换报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .info-item {{
            padding: 15px;
            background-color: #ecf0f1;
            border-radius: 5px;
        }}
        .info-label {{
            font-weight: bold;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .info-value {{
            font-size: 1.2em;
            color: #2c3e50;
            margin-top: 5px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            color: white;
        }}
        .stat-card.success {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .stat-card.warning {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .stat-card.error {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin: 10px 0;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        .error-list, .warning-list {{
            margin: 20px 0;
        }}
        .error-item, .warning-item {{
            padding: 15px;
            margin: 10px 0;
            border-radius: 5px;
            border-left: 4px solid;
        }}
        .error-item {{
            background-color: #fff5f5;
            border-left-color: #e74c3c;
        }}
        .warning-item {{
            background-color: #fffbf0;
            border-left-color: #f39c12;
        }}
        .error-header, .warning-header {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .error-description, .warning-description {{
            color: #666;
            font-size: 0.95em;
        }}
        .success-badge {{
            display: inline-block;
            padding: 5px 15px;
            background-color: #27ae60;
            color: white;
            border-radius: 20px;
            font-size: 0.9em;
        }}
        .error-badge {{
            display: inline-block;
            padding: 5px 15px;
            background-color: #e74c3c;
            color: white;
            border-radius: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏥 EUDAMED批量注册转换报告</h1>
        
        <h2>📋 基本信息</h2>
        <div class="info-grid">
            <div class="info-item">
                <div class="info-label">输入文件</div>
                <div class="info-value">{self.input_file}</div>
            </div>
            <div class="info-item">
                <div class="info-label">输出文件</div>
                <div class="info-value">{self.output_file}</div>
            </div>
            <div class="info-item">
                <div class="info-label">处理时间</div>
                <div class="info-value">{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
            <div class="info-item">
                <div class="info-label">处理耗时</div>
                <div class="info-value">{duration:.2f}秒</div>
            </div>
        </div>
        
        <h2>📊 数据统计</h2>
        <div class="stats-grid">
            <div class="stat-card success">
                <div class="stat-label">Basic UDI-DI</div>
                <div class="stat-number">{self.stats['basic_udi_count']}</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">UDI-DI</div>
                <div class="stat-number">{self.stats['udi_di_count']}</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">市场信息</div>
                <div class="stat-number">{self.stats['market_info_count']}</div>
            </div>
        </div>
        
        <h2>✅ 验证结果</h2>
        <div class="stats-grid">
            <div class="stat-card {'success' if self.stats['error_count'] == 0 else 'error'}">
                <div class="stat-label">错误</div>
                <div class="stat-number">{self.stats['error_count']}</div>
            </div>
            <div class="stat-card {'success' if self.stats['warning_count'] == 0 else 'warning'}">
                <div class="stat-label">警告</div>
                <div class="stat-number">{self.stats['warning_count']}</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">状态</div>
                <div class="stat-number">{'✓' if self.stats['error_count'] == 0 else '✗'}</div>
            </div>
        </div>
"""
        
        # 添加错误详情
        if self.errors:
            html += """
        <h2>❌ 错误详情</h2>
        <div class="error-list">
"""
            for error in self.errors:
                error_dict = error.to_dict()
                html += f"""
            <div class="error-item">
                <div class="error-header">
                    [{error_dict['sheet']}] 行{error_dict['row']} - {error_dict['field']}
                </div>
                <div class="error-description">
                    {error_dict['message']}<br>
                    <strong>当前值:</strong> {error_dict['value']}<br>
                    <strong>建议:</strong> {error_dict['suggestion']}
                </div>
            </div>
"""
            html += """
        </div>
"""
        
        # 添加警告详情
        if self.warnings:
            html += """
        <h2>⚠️ 警告详情</h2>
        <div class="warning-list">
"""
            for warning in self.warnings:
                warning_dict = warning.to_dict()
                html += f"""
            <div class="warning-item">
                <div class="warning-header">
                    [{warning_dict['sheet']}] 行{warning_dict['row']} - {warning_dict['field']}
                </div>
                <div class="warning-description">
                    {warning_dict['message']}<br>
                    <strong>当前值:</strong> {warning_dict['value']}<br>
                    <strong>建议:</strong> {warning_dict['suggestion']}
                </div>
            </div>
"""
            html += """
        </div>
"""
        
        html += """
    </div>
</body>
</html>
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"  ✓ HTML报告已生成: {filepath}")
    
    def generate_json_report(self, filepath):
        """生成JSON格式报告"""
        duration = 0
        if self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
        
        report = {
            'input_file': self.input_file,
            'output_file': self.output_file,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_seconds': duration,
            'statistics': self.stats,
            'errors': [e.to_dict() for e in self.errors],
            'warnings': [w.to_dict() for w in self.warnings]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"  ✓ JSON报告已生成: {filepath}")
