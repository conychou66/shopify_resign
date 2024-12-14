# -*- coding: utf-8 -*-
import os
import pathlib

def create_project_structure():
    # 项目根目录
    root_dir = "shopify_register"
    
    # 创建主目录结构
    directories = [
        "config",
        "core/browser",
        "core/data",
        "core/thread",
        "core/utils",
        "modules/registration",
        "modules/result",
        "modules/ui/components",
        "logs",
        "reports"
    ]
    
    # 需要创建的Python文件
    python_files = [
        # 核心模块的__init__.py文件
        "core/__init__.py",
        "core/browser/__init__.py",
        "core/data/__init__.py",
        "core/thread/__init__.py",
        "core/utils/__init__.py",
        "modules/__init__.py",
        "modules/registration/__init__.py",
        "modules/result/__init__.py",
        "modules/ui/__init__.py",
        "modules/ui/components/__init__.py",
        
        # 核心模块文件
        "core/browser/adspower.py",
        "core/browser/page_actions.py",
        "core/data/excel_reader.py",
        "core/data/data_validator.py",
        "core/thread/thread_pool.py",
        "core/thread/task_queue.py",
        "core/utils/logger.py",
        "core/utils/config.py",
        
        # 业务模块文件
        "modules/registration/form_filler.py",
        "modules/registration/process.py",
        "modules/result/exporter.py",
        "modules/result/reporter.py",
        "modules/ui/main_window.py",
        "modules/ui/components/widgets.py",
        
        # 主程序文件
        "main.py"
    ]
    
    # 其他文件
    other_files = [
        "config/config.yaml",
        "requirements.txt",
        "logs/.gitkeep",
        "reports/.gitkeep"
    ]
    
    try:
        # 创建项目根目录
        os.makedirs(root_dir, exist_ok=True)
        print(f"创建项目根目录: {root_dir}")
        
        # 创建目录结构
        for directory in directories:
            path = os.path.join(root_dir, directory)
            os.makedirs(path, exist_ok=True)
            print(f"创建目录: {path}")
        
        # 创建Python文件
        for file in python_files:
            path = os.path.join(root_dir, file)
            # 使用 'utf-8' 编码创建文件
            with open(path, 'w', encoding='utf-8') as f:
                f.write('# -*- coding: utf-8 -*-\n')
            print(f"创建Python文件: {path}")
        
        # 创建其他文件
        for file in other_files:
            path = os.path.join(root_dir, file)
            # 使用 'utf-8' 编码创建文件
            with open(path, 'w', encoding='utf-8') as f:
                pass
            print(f"创建文件: {path}")
            
        print("\n项目结构创建完成！")
        
    except Exception as e:
        print(f"创建项目结构时出错: {str(e)}")

if __name__ == "__main__":
    create_project_structure() 