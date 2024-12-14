# -*- coding: utf-8 -*-
import requests
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

class AdsPowerController:
    def __init__(self):
        self.api_base = "http://local.adspower.net:50325"
        self.driver = None
        self.current_user_id = None
        self.logger = logging.getLogger(__name__)
        
    def get_browser_list(self):
        """获取最近100条浏览器列表"""
        try:
            list_url = f"{self.api_base}/api/v1/user/list"
            params = {
                "page_size": 100,
                "page": 1,
                "sort_by": "created_at",
                "sort_type": "desc"
            }
            
            response = requests.get(list_url, params=params)
            data = response.json()
            
            if data.get("code") != 0:
                self.logger.error(f"获取浏览器列表失败: {data.get('msg')}")
                return None
                
            return data.get("data", {}).get("list", [])
            
        except Exception as e:
            self.logger.error(f"获取浏览器列表时出错: {str(e)}")
            return None

    def start_browser_by_id(self, user_id):
        """使用指定的user_id启动浏览器"""
        try:
            # 调用启动API
            open_url = f"{self.api_base}/api/v1/browser/start"
            params = {
                "user_id": user_id,
                "open_tabs": 1
            }
            
            self.logger.info(f"正在启动浏览器，user_id: {user_id}")
            response = requests.get(open_url, params=params)
            data = response.json()
            
            if data.get("code") != 0:
                self.logger.error(f"启动 AdsPower 失败: {data.get('msg')}")
                return None
            
            # 获取浏览器信息
            debugger_address = data["data"]["ws"]["selenium"]
            chrome_driver_path = data["data"]["webdriver"]
            
            # 设置 Chrome 选项
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", debugger_address)
            
            # 创建 Service 对象
            service = Service(executable_path=chrome_driver_path)
            
            # 创建浏览器实例
            self.driver = webdriver.Chrome(
                service=service,
                options=chrome_options
            )
            
            # 保存当前使用的user_id
            self.current_user_id = user_id
            
            # 返回完整的浏览器信息
            browser_info = {
                "selenium_address": debugger_address,
                "webdriver": chrome_driver_path,
                "user_id": user_id,
                "debug_port": data["data"].get("debug_port", ""),
                "puppeteer_ws": data["data"]["ws"].get("puppeteer", "")
            }
            
            self.logger.info(f"浏览器启动成功，信息: {json.dumps(browser_info, indent=2)}")
            return browser_info
            
        except Exception as e:
            self.logger.error(f"启动浏览器时出错: {str(e)}")
            return None

    def stop_browser_by_id(self, user_id):
        """停止指定ID的浏览器"""
        try:
            # 调用关闭API
            close_url = f"{self.api_base}/api/v1/browser/stop"
            params = {"user_id": user_id}
            
            response = requests.get(close_url, params=params)
            data = response.json()
            
            if data.get("code") != 0:
                # 如果错误是因为浏览器已经关闭，则认为是成功的
                if "not open" in str(data.get("msg", "")).lower():
                    return True
                self.logger.error(f"停止浏览器失败: {data.get('msg')}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"停止浏览器时出错: {str(e)}")
            return False

    def close_browser(self):
        """关闭当前打开的浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                
                if self.current_user_id:
                    self.stop_browser_by_id(self.current_user_id)
                
                self.current_user_id = None
                self.driver = None
                
        except Exception as e:
            self.logger.error(f"关闭浏览器时出错: {str(e)}")

    def check_browser_status(self, user_id):
        """检查浏览器状态"""
        try:
            # 调用状态检查API
            status_url = f"{self.api_base}/api/v1/browser/active"
            params = {"user_id": user_id}
            
            response = requests.get(status_url, params=params)
            data = response.json()
            
            if data.get("code") != 0:
                self.logger.error(f"检查浏览器状态失败: {data.get('msg')}")
                return False
            
            # 检查浏览器是否处于活动状态
            is_active = data.get("data", {}).get("status") == "Active"
            self.logger.info(f"浏览器 {user_id} 状态: {'运行中' if is_active else '未运行'}")
            
            return is_active
            
        except Exception as e:
            self.logger.error(f"检查浏览器状态时出错: {str(e)}")
            return False

# 为了保持向后兼容
AdsPower = AdsPowerController
