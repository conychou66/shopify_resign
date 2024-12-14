# -*- coding: utf-8 -*-
import sys
from PyQt6.QtWidgets import QApplication
from shopify_register.core.ui.main_window import MainWindow
from shopify_register.core.utils.logger import setup_logger

def main():
    # 设置日志
    setup_logger()
    
    # 创建应用
    app = QApplication(sys.argv)
    
    # 创建并显示主窗口
    window = MainWindow()
    window.show()
    
    # 运行应用
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 