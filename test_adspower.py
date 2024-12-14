# -*- coding: utf-8 -*-
import os
import sys
import logging
from shopify_register.core.browser.adspower import AdsPowerController
from shopify_register.core.excel.excel_handler import ExcelHandler

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_adspower():
    """
    测试AdsPower的基本功能
    """
    try:
        # 初始化Excel处理器
        excel_path = os.path.join('data', 'stores.xlsx')
        if not os.path.exists(excel_path):
            logger.error(f"Excel文件不存在: {excel_path}")
            return
            
        excel_handler = ExcelHandler(excel_path)
        
        # 获取待处理的商店数据
        store = excel_handler.get_next_store()
        if not store:
            logger.info("没有待处理的数据")
            return
            
        # 初始化AdsPower
        adspower = AdsPowerController()
        
        # 获取最近100个浏览器环境
        browser_list = adspower.get_browser_list()  # 使用默认的page_size=100
        if not browser_list:
            logger.error("获取浏览器列表失败")
            return
            
        # 查找匹配的环境ID
        browser_id = None
        target_name = store['adspower_name']
        
        for browser in browser_list:
            if browser.get('name') == target_name:
                browser_id = browser.get('user_id')
                break
                
        if not browser_id:
            logger.error(f"未找到匹配的环境ID，环境名称: {target_name}")
            return
            
        # 检查浏览器状态
        if adspower.check_browser_status(browser_id):
            logger.info(f"浏览器 {browser_id} 已在运行，尝试关闭")
            adspower.stop_browser_by_id(browser_id)
            
        # 测试打开浏览器
        logger.info(f"正在测试打开浏览器: {target_name} (ID: {browser_id})")
        browser_data = adspower.start_browser_by_id(browser_id)
        
        if browser_data:
            logger.info("浏览器打开成功")
            logger.info(f"浏览器数据: {browser_data}")
            
            # 等待几秒后关闭浏览器
            import time
            time.sleep(5)
            
            # 测试关闭浏览器
            logger.info("正在测试关闭浏览器")
            adspower.close_browser()  # 使用close_browser来确保完全关闭
            logger.info("浏览器关闭成功")
        else:
            logger.error("打开浏览器失败")
            
    except Exception as e:
        logger.error(f"测试过程中出错: {str(e)}")

if __name__ == "__main__":
    test_adspower() 