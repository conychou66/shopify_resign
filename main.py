#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import logging

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# 导入所需模块
from shopify_register.core.excel.excel_handler import ExcelHandler
from shopify_register.core.browser.adspower_manager import AdsPowerManager
from shopify_register.core.browser.google_login import GoogleLoginHandler
from shopify_register.core.browser.shopify_register import ShopifyRegister
from shopify_register.core.browser.shopify_payments import ShopifyPayments
from shopify_register.core.browser.shopify_2fa import Shopify2FA
from shopify_register.core.utils.logger import setup_logger

# 设置日志
logger = logging.getLogger(__name__)
setup_logger()

def main():
    try:
        logger.info("开始执行自动化流程...")
        
        # 1. 读取Excel数据
        excel_handler = ExcelHandler("data/stores.xlsx")
        store = excel_handler.get_next_store()
        if not store:
            logger.error("没有找到需要处理的商店数据")
            return False    
            
        logger.info(f"开始处理商店: {store.get('business_name', 'Unknown')}")
        
        # 2. 初始化AdsPower
        adspower = AdsPowerManager()
        
        # 3. 启动浏览器（如果已经在运行则重用）
        browser_info = adspower.start_browser(store['adspower_name'])
        if not browser_info:
            logger.error("启动浏览器失败")
            return False
            
        driver = adspower.create_driver(browser_info)
        if not driver:
            logger.error("创建WebDriver失败")
            return False
        
        try:
            # 4. Gmail登录
            gmail_login = GoogleLoginHandler(driver, adspower_id=browser_info["user_id"])
            
            # 开始登录流程
            logger.info("开始Gmail登录流程...")
            if not gmail_login.login(store):
                logger.error("Gmail登录失败")
                return False
                
            logger.info("Gmail登录成功，重新连接浏览器...")
            
            # Gmail登录成功后重新连接浏览器
            driver = adspower.reconnect_browser(browser_info)
            if not driver:
                logger.error("重新连接浏览器失败")
                return False
            
            # 验证浏览器连接
            try:
                driver.current_url
                logger.info("浏览器重连成功")
            except Exception as e:
                logger.error(f"浏览器连接验证失败: {str(e)}")
                return False
            
            # 5. Shopify注册 - 使用重新连接的driver实例
            logger.info("开始Shopify注册流程...")
            shopify = ShopifyRegister(driver=driver)
            if not shopify.process_store(store, excel_handler):
                logger.error("Shopify注册失败")
                return False
            logger.info("Shopify注册成功")
            
            # 6. Payments设置
            payments = ShopifyPayments(driver)
            if not payments.setup(store):
                logger.error("Payments设置失败")
                return False
            logger.info("Payments设置成功")
                
            # 7. 2FA设置
            twofa = Shopify2FA(driver)
            if not twofa.setup():
                logger.error("2FA设置失败")
                return False
            logger.info("2FA设置成功")
                
            logger.info(f"商店 {store['business_name']} 处理完成")
            return True
            
        finally:
            # 不在这里关闭浏览器，让AdsPower管理浏览器生命周期
            pass
            
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        return False

if __name__ == "__main__":
    main()  