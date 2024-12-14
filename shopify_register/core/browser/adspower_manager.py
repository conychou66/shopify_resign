# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import logging
import requests
from typing import Optional, Dict, List

class AdsPowerManager:
    """AdsPower浏览器管理器"""
    
    def __init__(self):
        self.api_base = "http://local.adspower.net:50325"
        self.logger = logging.getLogger(__name__)
        self.current_browser_info = None  # 保存当前浏览器信息

    def get_browser_list(self) -> List[Dict]:
        """获取浏览器环境列表"""
        try:
            url = f"{self.api_base}/api/v1/user/list"
            params = {
                "page_size": 100,
                "page": 1,
                "sort_by": "created_at",
                "sort_type": "desc"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get("code") != 0:
                self.logger.error(f"获取浏览器列表失败: {data.get('msg')}")
                return []
                
            return data.get("data", {}).get("list", [])
            
        except Exception as e:
            self.logger.error(f"获取浏览器列表时出错: {str(e)}")
            return []

    def find_browser_id(self, browser_name: str) -> Optional[str]:
        """根据浏览器名称查找ID"""
        browser_list = self.get_browser_list()
        for browser in browser_list:
            if browser.get('name') == browser_name:
                return browser.get('user_id')
        return None

    def create_driver(self, browser_info: Dict) -> Optional[webdriver.Chrome]:
        """创建或重用WebDriver实例"""
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", browser_info["selenium_address"])
            service = Service(executable_path=browser_info["webdriver"])
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            self.logger.info("成功创建WebDriver实例")
            return driver
            
        except Exception as e:
            self.logger.error(f"创建WebDriver失败: {str(e)}")
            return None

    def start_browser(self, browser_name: str) -> Optional[Dict]:
        """启动指定名称的浏览器"""
        try:
            # 查找浏览器ID
            browser_id = self.find_browser_id(browser_name)
            if not browser_id:
                self.logger.error(f"未找到浏览器环境: {browser_name}")
                return None

            # 检查浏览器是否已经在运行
            if self.current_browser_info:
                if self.current_browser_info.get("user_id") == browser_id:
                    self.logger.info("浏览器已在运行中")
                    return self.current_browser_info
                else:
                    # 停止当前浏览器
                    self.stop_browser(self.current_browser_info["user_id"])

            # 启动浏览器
            self.logger.info(f"正在启动浏览器: {browser_name} (ID: {browser_id})")
            url = f"{self.api_base}/api/v1/browser/start"
            response = requests.get(url, params={"user_id": browser_id})
            data = response.json()
            
            if data.get("code") != 0:
                self.logger.error(f"启动浏览器失败: {data.get('msg')}")
                return None
                
            browser_info = {
                "selenium_address": data["data"]["ws"]["selenium"],
                "webdriver": data["data"]["webdriver"],
                "user_id": browser_id,
                "debug_port": data["data"].get("debug_port", ""),
                "puppeteer_ws": data["data"]["ws"].get("puppeteer", "")
            }
            
            self.current_browser_info = browser_info  # 保存浏览器信息
            return browser_info
            
        except Exception as e:
            self.logger.error(f"启动浏览器时出错: {str(e)}")
            return None

    def stop_browser(self, browser_id: str) -> bool:
        """停止指定ID的浏览器"""
        try:
            url = f"{self.api_base}/api/v1/browser/stop"
            response = requests.get(url, params={"user_id": browser_id})
            data = response.json()
            
            if data.get("code") != 0:
                if "not open" not in str(data.get("msg", "")).lower():
                    self.logger.error(f"停止浏览器失败: {data.get('msg')}")
                    return False
                    
            if self.current_browser_info and self.current_browser_info["user_id"] == browser_id:
                self.current_browser_info = None  # 清除当前浏览器信息
                
            return True
            
        except Exception as e:
            self.logger.error(f"停止浏览器时出错: {str(e)}")
            return False

    def reconnect_browser(self, browser_info: Dict) -> Optional[webdriver.Chrome]:
        """重新连接到已启动的浏览器"""
        try:
            self.logger.info("尝试重新连接到浏览器...")
            
            # 确保浏览器仍在运行
            if not self.current_browser_info or self.current_browser_info["user_id"] != browser_info["user_id"]:
                self.logger.error("浏览器状态异常，尝试重新启动...")
                browser_info = self.start_browser(browser_info["user_id"])
                if not browser_info:
                    return None
            
            # 创建新的WebDriver实例
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_experimental_option("debuggerAddress", browser_info["selenium_address"])
            service = Service(executable_path=browser_info["webdriver"])
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # 验证连接
            try:
                driver.current_url
                self.logger.info("成功重新连接到浏览器")
                return driver
            except Exception as e:
                self.logger.error(f"浏览器连接验证失败: {str(e)}")
                return None
            
        except Exception as e:
            self.logger.error(f"重新连接浏览器失败: {str(e)}")
            return None 