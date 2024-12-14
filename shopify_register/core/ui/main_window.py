# -*- coding: utf-8 -*-
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QFileDialog, QSpinBox, QTextEdit, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
from shopify_register.core.browser.adspower_manager import AdsPowerManager
from shopify_register.core.browser.shopify_register import ShopifyRegister
from shopify_register.core.excel.excel_handler import ExcelHandler

class ProcessTimeout(Exception):
    """流程超时异常"""
    pass

class RegisterThread(QThread):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(str)
    
    def __init__(self, excel_path):
        super().__init__()
        self.excel_path = excel_path
        self.excel_handler = ExcelHandler(excel_path)
        self.adspower = AdsPowerManager()
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        try:
            # 获取待处理的商店数据
            store = self.excel_handler.get_next_store()
            if not store:
                self.progress.emit("没有找到需要处理的商店")
                self.finished.emit(False, "没有待处理的数据")
                return
            
            # 使用AdsPower管理器
            adspower = AdsPowerManager()
            
            # 启动浏览器
            browser_info = adspower.start_browser(store['adspower_name'])
            if not browser_info:
                self.progress.emit("启动浏览器失败")
                self.finished.emit(False, "启动浏览器失败")
                return
            
            # 创建WebDriver实例
            driver = adspower.create_driver(browser_info)
            if not driver:
                self.progress.emit("创建WebDriver失败")
                self.finished.emit(False, "创建WebDriver失败")
                return
            
            # 创建ShopifyRegister实例，传入driver
            register = ShopifyRegister(driver=driver)
            
            # 执行注册流程
            result = register.process_store(store, self.excel_handler)
            
            if result:
                self.progress.emit(f"商店 {store['business_name']} 注册成功")
                self.finished.emit(True, "注册成功")
            else:
                self.progress.emit(f"商店 {store['business_name']} 注册失败")
                self.finished.emit(False, "注册失败")
                
        except Exception as e:
            error_msg = f"处理商店时出错: {str(e)}"
            self.progress.emit(error_msg)
            self.finished.emit(False, error_msg)
        finally:
            # 确保关闭浏览器
            if 'driver' in locals():
                try:
                    driver.quit()
                except:
                    pass

    def log_message(self, message: str):
        """
        统一的日志处理方法
        """
        self.progress.emit(message)
        self.logger.info(message)

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # 设置窗口
        self.setWindowTitle('Shopify 注册工具')
        self.setMinimumSize(800, 600)
        
        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel('未选择文件')
        self.select_file_btn = QPushButton('选择Excel文件')
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.select_file_btn)
        layout.addLayout(file_layout)
        
        # 控制区域
        control_layout = QHBoxLayout()
        self.start_btn = QPushButton('开始注册')
        self.start_btn.clicked.connect(self.start_registration)
        self.start_btn.setEnabled(False)
        self.thread_count = QSpinBox()
        self.thread_count.setRange(1, 10)
        self.thread_count.setValue(1)
        control_layout.addWidget(QLabel('线程数:'))
        control_layout.addWidget(self.thread_count)
        control_layout.addWidget(self.start_btn)
        layout.addLayout(control_layout)
        
        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 初始化工作线程
        self.worker = None
        
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.file_label.setText(file_path)
            self.start_btn.setEnabled(True)
            
    def log_message(self, message):
        self.log_text.append(message)
        logging.info(message)
        
    def start_registration(self):
        if not self.file_label.text() or self.file_label.text() == '未选择文件':
            self.log_message("请先选择Excel文件")
            return
            
        try:
            self.start_btn.setEnabled(False)
            self.select_file_btn.setEnabled(False)
            self.log_text.clear()
            
            # 创建并启动工作线程
            self.worker = RegisterThread(self.file_label.text())
            self.worker.progress.connect(self.log_message)
            self.worker.finished.connect(self.registration_finished)
            self.worker.start()
            
        except Exception as e:
            self.log_message(f"启动任务失败: {str(e)}")
            self.start_btn.setEnabled(True)
            self.select_file_btn.setEnabled(True)
        
    def registration_finished(self, success, message):
        self.start_btn.setEnabled(True)
        self.select_file_btn.setEnabled(True)
        if success:
            self.log_message(message)
        else:
            QMessageBox.critical(self, "错误", message) 