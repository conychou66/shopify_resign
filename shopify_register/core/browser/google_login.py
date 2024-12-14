# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
import logging
import requests
from typing import Dict
import pyperclip

class GoogleLoginHandler:
    def __init__(self, driver: webdriver.Chrome, adspower_id: str = None):
        self.driver = driver
        self.adspower_id = adspower_id
        self.api_base = "http://local.adspower.net:50325"
        self.wait = WebDriverWait(driver, 100)
        self.quick_wait = WebDriverWait(driver, 2)
        self.logger = logging.getLogger(__name__)
        self.actions = ActionChains(driver)

    def check_adspower_cookies(self) -> bool:
        """
        通过AdsPower API检查Google登录状态
        """
        if not self.adspower_id:
            return False

        try:
            # 调用AdsPower API获取Cookie
            url = f"{self.api_base}/api/v1/browser/cookies"
            params = {
                "user_id": self.adspower_id,
                "domain": ".google.com"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get("code") != 0:
                self.logger.error(f"获取Cookie失败: {data.get('msg')}")
                return False
                
            # 检查关键Cookie
            cookies = data.get("data", [])
            required_cookies = {'SID', 'HSID', 'SSID'}
            found_cookies = {
                cookie['name'] for cookie in cookies 
                if cookie['name'] in required_cookies
            }
            
            if found_cookies == required_cookies:
                self.logger.info("通过AdsPower API检测到Google登录成功")
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"检查AdsPower Cookie失败: {str(e)}")
            return False

    def check_login_success(self, quick_check: bool = True) -> bool:
        """检查Google登录状态，优先使用API和Cookie方法"""
        try:
            # 方法1: 通过AdsPower API检查
            if self.adspower_id:
                if self.check_adspower_cookies():
                    self.logger.info("通过AdsPower API检测到登录成功")
                    return True

            # 方法2: 直接检查Cookie
            if self.verify_google_cookies():
                self.logger.info("通过Cookie检测到登录成功")
                return True

            # 只有在快速检查模式关闭时才进行页面元素检查
            if not quick_check:
                # 方法3: 页面元素检查
                try:
                    if self.quick_wait.until(EC.presence_of_element_located((By.ID, "profileIdentifier"))):
                        self.logger.info("通过页面元素检测到登录成功")
                        return True
                except:
                    pass

                # 方法4: URL检查
                try:
                    current_url = self.driver.current_url
                    if any(domain in current_url for domain in [
                        "myaccount.google.com",
                        "accounts.google.com/SignOutOptions",
                        "accounts.google.com/o/oauth2"
                    ]):
                        self.logger.info("通过URL检测到登录成功")
                        return True
                except:
                    pass

            return False
        except Exception as e:
            self.logger.error(f"检查登录状态时出错: {str(e)}")
            return False

    def check_next_step(self, max_time=15):
        """快速检测下一步的可能元素"""
        try:
            # 1. 检查当前页面的URL和标题
            current_url = self.driver.current_url
            page_title = self.driver.title

            # 检查是否在验证页面
            if "signoutoptions" in current_url.lower() or "challenge" in current_url.lower():
                # 2. 检查辅助邮箱确认页面的特征
                try:
                    # 检查页面特征组合
                    verify_indicators = [
                        # 标题文本
                        "//h1[contains(text(), 'Verify')]",
                        # 验证说明文本
                        "//div[contains(text(), 'To help keep your account safe')]",
                        # 选择提示文本
                        "//div[contains(text(), 'Choose how you want to sign in')]",
                        # 辅助邮箱选项
                        "//div[contains(@class, 'l5PPKe')]",
                        # 父容器
                        "//div[contains(@class, 'Z1r7P')]"
                    ]

                    # 计算匹配的指标数量
                    matches = 0
                    for indicator in verify_indicators:
                        try:
                            if self.quick_wait.until(EC.presence_of_element_located((By.XPATH, indicator))):
                                matches += 1
                        except:
                            continue

                    # 如果匹配了足够多的特征，就认为是验证页面
                    if matches >= 2:
                        # 进一步检查是否存在辅助邮箱选项
                        recovery_selectors = [
                            "//div[contains(@class, 'l5PPKe') and contains(text(), 'Confirm your recovery email')]",
                            "//div[contains(@class, 'Z1r7P')]//div[contains(text(), 'Confirm your recovery email')]",
                            "//div[contains(text(), 'Confirm your recovery email')]"
                        ]

                        for selector in recovery_selectors:
                            try:
                                element = self.quick_wait.until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                                if element.is_displayed():
                                    self.logger.info(f"检测到辅助邮箱确认选项: {selector}")
                                    return "verify_email"
                            except:
                                continue

                except Exception as e:
                    self.logger.debug(f"检查验证页面时出错: {str(e)}")

            # 3. 检查辅助邮箱输入框页面
            try:
                recovery_input_indicators = [
                    "//input[@name='recoveryEmail']",
                    "//div[contains(text(), 'Confirm the recovery email')]",
                    "//div[contains(text(), 'recovery email address')]"
                ]
                
                matches = 0
                for indicator in recovery_input_indicators:
                    try:
                        if self.quick_wait.until(EC.presence_of_element_located((By.XPATH, indicator))):
                            matches += 1
                    except:
                        continue

                if matches >= 1:
                    return "verify_email_input"
            except:
                pass

            # 4. 检查"Simplify your sign-in"页面
            try:
                simplify_indicators = [
                    "//div[contains(text(), 'Simplify your sign-in')]",
                    "//button[contains(text(), 'Not now')]",
                    "//div[contains(text(), 'passkeys')]"
                ]
                
                matches = 0
                for indicator in simplify_indicators:
                    try:
                        if self.quick_wait.until(EC.presence_of_element_located((By.XPATH, indicator))):
                            matches += 1
                    except:
                        continue

                if matches >= 2:
                    return "simplify_signin"
            except:
                pass

            # 5. 检查Recovery information页面
            try:
                recovery_info_indicators = [
                    "//h1[contains(text(), 'Recovery information')]",
                    "//button[contains(text(), 'Cancel')]",
                    "//div[contains(text(), 'Keep your account secure')]"
                ]
                
                matches = 0
                for indicator in recovery_info_indicators:
                    try:
                        if self.quick_wait.until(EC.presence_of_element_located((By.XPATH, indicator))):
                            matches += 1
                    except:
                        continue

                if matches >= 2:
                    return "recovery_info"
            except:
                pass

            # 6. 最后检查是否登录成功
            if self.check_login_success(quick_check=True):
                return "success"

            return None

        except Exception as e:
            self.logger.error(f"检查页面状态时出错: {str(e)}")
            return None

    def paste_text_and_enter(self, element, text: str):
        """使用复制粘贴方式输入文本并回车"""
        try:
            pyperclip.copy(text)
            element.clear()
            self.actions.click(element).perform()
            time.sleep(0.5)
            self.actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
            time.sleep(0.5)
            element.send_keys(Keys.ENTER)
            time.sleep(2)
        except Exception as e:
            self.logger.error(f"粘贴文本失败: {str(e)}")
            raise

    def check_login_success_multiple(self, check_times=3, interval=1.0) -> bool:
        """
        多次检查Google登录状态
        Args:
            check_times: 检查次数
            interval: 每次检查间隔(秒)
        """
        # 首先尝试API和Cookie检查（快速检查）
        success_count = 0
        for i in range(check_times):
            if self.check_login_success(quick_check=True):
                success_count += 1
                self.logger.info(f"第{i+1}次快速检测登录成功")
            else:
                self.logger.info(f"第{i+1}次快速检测未成功")
            if i < check_times - 1:
                time.sleep(interval)

        if success_count >= 2:
            return True

        # 如果快速检查失败，进行完整检查
        self.logger.info("快速检查未确认登录状态，进行完整检查...")
        success_count = 0
        for i in range(check_times):
            if self.check_login_success(quick_check=False):
                success_count += 1
                self.logger.info(f"第{i+1}次完整检测登录成功")
            else:
                self.logger.info(f"第{i+1}次完整检测未成功")
            if i < check_times - 1:
                time.sleep(interval)

        return success_count >= 2

    def login(self, store_data: Dict) -> bool:
        """执行Google账号登录"""
        try:
            email = store_data.get('email')
            password = store_data.get('password')
            recovery_email = store_data.get('recovery_email')
            
            if not all([email, password, recovery_email]):
                self.logger.error("登录信息不完整")
                return False

            # 打开Google登录页面
            self.driver.get('https://accounts.google.com')
            time.sleep(2)

            # 输入邮箱
            email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "identifier")))
            self.logger.info("正在输入邮箱...")
            self.paste_text_and_enter(email_input, email)

            # 等待密码输入页面
            self.logger.info("等待密码输入页面...")
            try:
                password_input = self.wait.until(
                    EC.element_to_be_clickable((By.NAME, "Passwd"))
                )
            except Exception as e:
                self.logger.error(f"未找到密码输入框: {str(e)}")
                return False

            # 输入密码
            self.logger.info("正在输入密码...")
            # 增加等待时间，确保密码页面完全加载
            time.sleep(3)
            
            try:
                # 确保密码框可见并可交互
                self.driver.execute_script("arguments[0].scrollIntoView(true);", password_input)
                time.sleep(1)
                
                # 尝试多种方式点击密码框
                click_success = False
                click_methods = [
                    lambda: password_input.click(),  # 直接点击
                    lambda: self.actions.move_to_element(password_input).click().perform(),  # Actions链点击
                    lambda: self.driver.execute_script("arguments[0].click();", password_input)  # JavaScript点击
                ]
                
                for click_method in click_methods:
                    try:
                        click_method()
                        time.sleep(1)
                        if password_input.is_enabled() and password_input == self.driver.switch_to.active_element:
                            click_success = True
                            break
                    except:
                        continue
                
                if not click_success:
                    self.logger.error("无法使密码输入框获得焦点")
                    return False
                
                # 清除并输入密码
                password_input.clear()
                time.sleep(0.5)
                password_input.send_keys(password)
                time.sleep(1)
                
                # 使用回车键提交
                password_input.send_keys(Keys.ENTER)
                time.sleep(3)  # 等待提交后的响应

                # 输入密码后处理各种可能的页面
                if not self.handle_after_password(store_data):
                    return False

                return True

            except Exception as e:
                self.logger.error(f"密码输入失败: {str(e)}")
                return False

        except Exception as e:
            self.logger.error(f"Google登录失败: {str(e)}")
            return False
        finally:
            if not self.driver.find_elements(By.ID, "profileIdentifier"):
                try:
                    self.driver.quit()
                except:
                    pass

    def get_google_cookies(self) -> dict:
        """
        获取Google登录相关的Cookie
        """
        try:
            cookies = self.driver.get_cookies()
            google_cookies = {}
            for cookie in cookies:
                if cookie['name'] in ['SID', 'HSID', 'SSID']:
                    google_cookies[cookie['name']] = cookie['value']
            return google_cookies
        except Exception as e:
            self.logger.error(f"获取Cookie失败: {str(e)}")
            return {}

    def verify_google_cookies(self) -> bool:
        """
        验证Google登录Cookie是否有效
        """
        try:
            cookies = self.get_google_cookies()
            required_cookies = {'SID', 'HSID', 'SSID'}
            return set(cookies.keys()) == required_cookies
        except Exception as e:
            self.logger.error(f"验证Cookie失败: {str(e)}")
            return False

    def check_browser_alive(self) -> bool:
        """检查浏览器连接是否仍然有效"""
        try:
            # 尝试执行一个简单的命令
            self.driver.current_url
            return True
        except:
            return False

    def save_session(self):
        """保存Google登录会话"""
        try:
            # 保存Cookies
            cookies = self.driver.get_cookies()
            self.logger.info(f"保存了 {len(cookies)} 个Cookies")
            return cookies
        except Exception as e:
            self.logger.error(f"保存会话失败: {str(e)}")
            return None

    def handle_after_password(self, store_data: Dict) -> bool:
        """处理输入密码后的页面"""
        retry_count = 3  # 最多检测3次
        for retry in range(retry_count):
            self.logger.info(f"开始第{retry + 1}次页面状态检测...")
            next_step = self.check_next_step()

            if next_step == "verify_email":
                self.logger.info("检测到'Verify it's you'页面，点击'Confirm your recovery email'...")
                try:
                    # 点击"Confirm your recovery email"
                    confirm_button = self.wait.until(
                        EC.element_to_be_clickable((
                            By.XPATH, 
                            "//div[contains(@class, 'l5PPKe') and contains(text(), 'Confirm your recovery email')]"
                        ))
                    )
                    confirm_button.click()
                    time.sleep(2)

                    # 直接等待并处理辅助邮箱输入框
                    self.logger.info("等待辅助邮箱输入框...")
                    try:
                        # 使用更精确的选择器定位输入框
                        recovery_input = self.wait.until(
                            EC.presence_of_element_located((
                                By.XPATH,
                                "//input[@type='email' and @name='knowledgePreregisteredEmailResponse' and contains(@class, 'whsOnd')]"
                            ))
                        )
                        
                        # 确保输入框可见和可交互
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", recovery_input)
                        time.sleep(1)
                        
                        # 清除并输入辅助邮箱
                        recovery_input.clear()
                        recovery_input.send_keys(store_data['recovery_email'])
                        self.logger.info(f"已输入辅助邮箱: {store_data['recovery_email']}")
                        time.sleep(1)
                        
                        # 提交
                        recovery_input.send_keys(Keys.ENTER)
                        self.logger.info("已提交辅助邮箱")
                        time.sleep(3)  # 增加等待时间
                        
                        # 提交辅助邮箱后立即检查登录状态
                        self.logger.info("检查登录状态...")
                        if self.check_login_success(quick_check=True):
                            self.logger.info("检测到已成功登录")
                            return True
                        
                        # 再次确认登录状态
                        time.sleep(2)
                        if self.check_login_success_multiple(check_times=2, interval=1.0):
                            self.logger.info("多次检测确认已成功登录")
                            return True
                        
                        self.logger.warning("提交辅助邮箱后未检测到登录成功")
                        
                    except Exception as e:
                        self.logger.error(f"输入辅助邮箱失败: {str(e)}")
                        return False

                except Exception as e:
                    self.logger.error(f"点击'Confirm your recovery email'失败: {str(e)}")
                    return False

            elif next_step == "success":
                self.logger.info("检测到已成功登录")
                return True

            elif next_step == "simplify_signin":
                self.logger.info("检测到'Simplify your sign-in'页面，点击'Not now'...")
                try:
                    not_now_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not now')]"))
                    )
                    not_now_button.click()
                    time.sleep(2)
                except Exception as e:
                    self.logger.error(f"点击'Not now'按钮失败: {str(e)}")
                    continue

            elif next_step == "recovery_info":
                self.logger.info("检测到Recovery information页面，点击'Cancel'...")
                try:
                    cancel_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Cancel')]"))
                    )
                    cancel_button.click()
                    time.sleep(2)
                except Exception as e:
                    self.logger.error(f"点击'Cancel'按钮失败: {str(e)}")
                    continue

            if retry < retry_count - 1:
                self.logger.info("等待1秒后进行下一次检测...")
                time.sleep(1)

        self.logger.error("所有检测尝试都失败")
        return False