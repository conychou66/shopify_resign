# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict
import time
from .human_like_actions import HumanLikeActions
from selenium.common.exceptions import NoSuchElementException
from .twofa_live import TwoFaLive

class Shopify2FA:
    """处理Shopify双重认证设置的类"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.human = HumanLikeActions(driver)

    def enable_2fa(self) -> bool:
        """开启双重认证"""
        try:
            # 等待页面加载
            self.human.random_sleep(2, 3)
            
            # 点击Turn on按钮
            turn_on_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Turn on')]"))
            )
            self.human.move_to_element_randomly(turn_on_button)
            self.human.random_sleep()
            turn_on_button.click()
            
            return True
            
        except Exception as e:
            print(f"开启双重认证失败: {str(e)}")
            return False

    def relogin_with_google(self, email: str) -> bool:
        """
        使用Google账户重新登录
        
        Args:
            email: Google邮箱地址
        """
        try:
            # 等待页面加载到登录界面
            self.human.random_sleep(2, 3)
            
            # 点击Google登录按钮
            google_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'google-login')]"))
            )
            self.human.move_to_element_randomly(google_button)
            self.human.random_sleep()
            google_button.click()
            
            # 处理Google账户选择
            try:
                account_element = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, f"//div[contains(text(), '{email}')]"))
                )
                self.human.move_to_element_randomly(account_element)
                self.human.random_sleep()
                account_element.click()
            except:
                print("未找到Google账户选择界面，可能已自动选择")
                pass
            
            # 等待Google登录完成
            self.human.random_sleep(3, 5)
            
            # 循环处理登录后可能出现的多个验证码
            max_attempts = 5  # 最大验证码处理次数
            for attempt in range(max_attempts):
                try:
                    # 检查是否已回到2FA设置页面
                    try:
                        self.wait.until(
                            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Two-step authentication')]"))
                        )
                        print("成功回到2FA设置页面")
                        return True
                    except:
                        pass
                    
                    # 检查是否存在验证码
                    try:
                        self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
                        print(f"处理第 {attempt + 1} 个验证码...")
                        
                        if not self.handle_recaptcha():
                            print(f"第 {attempt + 1} 个验证码处理失败")
                            return False
                        
                        self.human.random_sleep(2, 3)
                    except NoSuchElementException:
                        print("等待页面加载或下一个验证码...")
                        self.human.random_sleep(1, 2)
                
                except Exception as e:
                    print(f"处理验证码时出错: {str(e)}")
                    self.human.random_sleep(1, 2)
                    continue
            
            print(f"超过最大验证码处理次数({max_attempts}次)")
            return False
            
        except Exception as e:
            print(f"Google重新登录失败: {str(e)}")
            return False

    def save_2fa_code(self) -> str:
        """
        获取并保存2FA设置代码
        
        Returns:
            str: 2FA设置代码，失败返回空字符串
        """
        try:
            # 点击"Can't scan the QR Code?"链接
            cant_scan_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Can't scan the QR Code?')]"))
            )
            self.human.move_to_element_randomly(cant_scan_link)
            self.human.random_sleep()
            cant_scan_link.click()
            
            # 等待2FA代码出现
            code_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Enter this code into your authenticator app:')]/following-sibling::div"))
            )
            
            # 获取2FA代码
            setup_code = code_element.text.strip()
            print(f"获取到2FA设置代码: {setup_code}")
            return setup_code
            
        except Exception as e:
            print(f"获取2FA设置代码失败: {str(e)}")
            return ""

    def submit_2fa_verification(self, setup_code: str) -> bool:
        """
        提交2FA验证并完成设置
        
        Args:
            setup_code: 2FA设置代码
        """
        try:
            # 获取验证码
            verification_code = TwoFaLive.get_verification_code(setup_code)
            if not verification_code:
                return False
            
            # 输入验证码
            verification_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[contains(@placeholder, '000000')]"))
            )
            self.human.move_to_element_randomly(verification_input)
            self.human.random_sleep()
            verification_input.send_keys(verification_code)
            
            # 点击Turn on按钮
            turn_on_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Turn on')]"))
            )
            self.human.move_to_element_randomly(turn_on_button)
            self.human.random_sleep()
            turn_on_button.click()
            
            # 循环处理可能出现的多个验证码
            max_attempts = 5  # 最大验证码处理次数
            for attempt in range(max_attempts):
                try:
                    # 检查是否已到达下一步页面
                    try:
                        self.wait.until(
                            EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Download recovery codes')]"))
                        )
                        print("成功进入恢复码页面")
                        return True
                    except:
                        pass
                    
                    # 检查是否存在验证码
                    try:
                        self.driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
                        print(f"处理第 {attempt + 1} 个验证码...")
                        
                        if not self.handle_recaptcha():
                            print(f"第 {attempt + 1} 个验证码处理失败")
                            return False
                        
                        self.human.random_sleep(2, 3)
                    except NoSuchElementException:
                        print("等待页面加载或下一个验证码...")
                        self.human.random_sleep(1, 2)
                
                except Exception as e:
                    print(f"处理验证码时出错: {str(e)}")
                    self.human.random_sleep(1, 2)
                    continue
            
            print(f"超过最大验证码处理次数({max_attempts}次)")
            return False
            
        except Exception as e:
            print(f"提交2FA验证失败: {str(e)}")
            return False

    def setup_2fa(self) -> tuple[bool, str]:
        """
        设置双重认证
        
        Returns:
            tuple[bool, str]: (是否成功, 2FA设置代码)
        """
        try:
            # 开启2FA
            if not self.enable_2fa():
                return False, ""
                
            # 等待重定向到登录页面
            self.human.random_sleep(3, 5)
            
            # 重新使用Google账户登录
            if not self.relogin_with_google():
                return False, ""
                
            # 获取并保存2FA设置代码
            setup_code = self.save_2fa_code()
            if not setup_code:
                return False, ""
                
            # 提交2FA验证
            if not self.submit_2fa_verification(setup_code):
                return False, setup_code
            
            # 完成2FA设置
            if not self.complete_2fa_setup():
                return False, setup_code
            
            return True, setup_code
            
        except Exception as e:
            print(f"设置双重认证失败: {str(e)}")
            return False, ""

    def verify_2fa_status(self) -> bool:
        """验证2FA是否设置成功"""
        try:
            # 检查2FA状态
            status_element = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Two-step authentication is on')]"))
            )
            return True
            
        except Exception as e:
            print(f"验证2FA状态失败: {str(e)}")
            return False 

    def complete_2fa_setup(self) -> bool:
        """完成2FA设置流程"""
        try:
            # 点击Continue按钮
            continue_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]"))
            )
            self.human.move_to_element_randomly(continue_button)
            self.human.random_sleep()
            continue_button.click()
            
            # 等待页面加载
            self.human.random_sleep(2, 3)
            
            # 等待10秒后结束任务
            print("2FA设置成功，10秒后结束任务...")
            self.human.random_sleep(8, 10)  # 使用8-10秒的随机等待时间
            return True
            
        except Exception as e:
            print(f"完成2FA设置失败: {str(e)}")
            return False