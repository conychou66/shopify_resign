# -*- coding: utf-8 -*-
import random
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

class HumanLikeActions:
    """模拟人类操作的辅助类"""
    
    def __init__(self, driver):
        self.driver = driver
        self.action = ActionChains(driver)
        
    def random_sleep(self, min_seconds: float = 0.5, max_seconds: float = 2.0) -> None:
        """随机等待一段时间"""
        time.sleep(random.uniform(min_seconds, max_seconds))
        
    def human_like_type(self, element, text: str) -> None:
        """模拟人类输入文字"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # 随机打字间隔
            
    def move_to_element_randomly(self, element) -> None:
        """随机移动到元素位置"""
        # 获取元素位置
        location = element.location
        size = element.size
        
        # 计算元素中心点
        target_x = location['x'] + size['width'] / 2
        target_y = location['y'] + size['height'] / 2
        
        # 生成随机的中间点
        points = [(random.randint(0, self.driver.get_window_size()['width']),
                  random.randint(0, self.driver.get_window_size()['height']))
                 for _ in range(random.randint(2, 4))]
        
        # 移动鼠标
        self.action.move_by_offset(points[0][0], points[0][1])
        for point in points[1:]:
            self.action.move_by_offset(point[0], point[1])
            time.sleep(random.uniform(0.1, 0.3))
        
        # 最后移动到目标元素
        self.action.move_to_element(element)
        self.action.perform()
        
    def random_scroll(self) -> None:
        """随机滚动页面"""
        scroll_amount = random.randint(100, 300)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        self.random_sleep(0.5, 1.0)
        
    def add_random_mouse_movement(self) -> None:
        """添加随机鼠标移动"""
        for _ in range(random.randint(2, 5)):
            x = random.randint(-100, 100)
            y = random.randint(-100, 100)
            self.action.move_by_offset(x, y)
            self.random_sleep(0.1, 0.3)
        self.action.perform() 