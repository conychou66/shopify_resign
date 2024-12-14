# -*- coding: utf-8 -*-
import logging
import os
from datetime import datetime
from shopify_register.core.excel.excel_handler import ExcelHandler
from shopify_register.core.browser import AdsPowerController  # 使用正确的类名
from shopify_register.core.browser import ShopifyRegister
import unittest

# 配置日志
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

log_file = os.path.join(log_dir, f"shopify_register_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TestShopifyRegister(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """在所有测试开始前执行一次"""
        cls.adspower = AdsPowerController()  # 使用正确的类名
        # 获取可用的浏览器配置
        cls.browser_profiles = cls.adspower.get_browser_profiles()
        if not cls.browser_profiles:
            logger.error("没有找到可用的AdsPower浏览器配置")
            raise Exception("没有找到可用的AdsPower浏览器配置")
        
        # 使用第一个可用的配置
        cls.test_profile = cls.browser_profiles[0]
        logger.info(f"使用浏览器配置: {cls.test_profile}")

    def setUp(self):
        """每个测试用例开始前执行"""
        try:
            # 启动浏览器
            browser_info = self.adspower.start_browser(self.test_profile)
            if not browser_info:
                raise Exception(f"无法启动浏览器配置: {self.test_profile}")
            
            self.driver = self.adspower.create_driver(browser_info)
            if not self.driver:
                raise Exception("无法创建WebDriver实例")
                
            self.shopify_register = ShopifyRegister(self.driver)
            logger.info("测试环境初始化成功")
            
        except Exception as e:
            logger.error(f"测试环境初始化失败: {str(e)}")
            raise

    def test_shopify_register_flow(self):
        """测试Shopify注册流程的主要功能"""
        try:
            # 测试数据
            test_data = {
                "email": "test@example.com",
                "password": "TestPassword123!",
                "business_name": "Test Store",
                "adspower_name": self.test_profile
            }
            
            logger.info(f"开始测试注册流程，使用配置: {test_data}")
            
            # 执行注册流程
            result = self.shopify_register.process_store(test_data, None)
            
            # 验证注册结果
            self.assertTrue(result, "Shopify注册流程应该成功完成")
            logger.info("注册流程测试成功")
            
        except Exception as e:
            logger.error(f"测试过程中出现错误: {str(e)}")
            raise

    def tearDown(self):
        """每个测试用例结束后执行"""
        try:
            if hasattr(self, 'driver') and self.driver:
                self.driver.quit()
                logger.info("测试环境清理完成")
        except Exception as e:
            logger.error(f"清理测试环境时出错: {str(e)}")

def main():
    logger.info("开始Shopify注册测试...")
    
    try:
        unittest.main()
    except Exception as e:
        logger.error(f"测试异常: {str(e)}")
    
    logger.info("测试结束")

if __name__ == "__main__":
    main() 