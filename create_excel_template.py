# -*- coding: utf-8 -*-
import pandas as pd
import os

def create_template():
    """创建Excel模板文件"""
    # 定义列名和示例数据
    data = {
        'adspower_name': ['test001'],  # AdsPower浏览器环境名称
        'email': ['example@gmail.com'],  # Gmail账号
        'password': ['password123'],  # Gmail密码
        'recovery_email': ['recovery@example.com'],  # Gmail恢复邮箱
        'business_name': ['Handle Financial, Inc.'],  # 公司名称
        'first_name': ['John'],  # 名
        'last_name': ['Doe'],  # 姓
        'birthday': ['1964-05-01'],  # 生日
        'ssn': ['123456789'],  # 社会安全号
        'phone': ['1234567890'],  # 电话号码
        'address': ['123 Main St'],  # 地址
        'city': ['Santa Clara'],  # 城市
        'state': ['California'],  # 州
        'zip_code': ['95054'],  # 邮编
        'ein': ['12-3456789'],  # 雇主识别号
        'business_phone': ['1234567890'],  # 公司电话
        'business_address': ['123 Business St'],  # 公司地址
        'business_city': ['Santa Clara'],  # 公司所在城市
        'business_state': ['California'],  # 公司所在州
        'business_zip': ['95054'],  # 公司邮编
        '2fa_code': [''],  # 二次验证码
        'status': [''],  # 处理状态
        'notes': ['']  # 备注
    }
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 确保data目录存在
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # 保存模板
    template_path = os.path.join('data', 'shopify_register_template.xlsx')
    df.to_excel(template_path, index=False)
    print(f"模板文件已创建: {template_path}")

if __name__ == "__main__":
    create_template() 