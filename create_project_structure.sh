#!/bin/bash

# 创建主目录结构
mkdir -p shopify_register/{core/{browser,excel,utils,ui},modules,config,logs,reports,data}

# 创建核心模块文件
touch shopify_register/core/browser/{__init__,adspower,google_login,human_like_actions,shopify_register,shopify_payments,shopify_2fa,twofa_live}.py
touch shopify_register/core/excel/{__init__,excel_handler}.py
touch shopify_register/core/utils/{__init__,logger}.py
touch shopify_register/core/ui/{__init__,main_window}.py

# 创建配置文件
touch config/config.yaml

# 创建主程序文件
touch main.py

# 创建依赖文件
touch requirements.txt

# 创建README
touch README.md 