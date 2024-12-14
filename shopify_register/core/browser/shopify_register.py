# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from typing import Dict
import time
import logging
import requests
from .human_like_actions import HumanLikeActions
from .shopify_payments import ShopifyPayments
from .shopify_2fa import Shopify2FA
from .twofa_live import TwoFaLive

class ShopifyRegister:
    def __init__(self, driver=None):
        """
        初始化ShopifyRegister
        Args:
            driver: WebDriver实例
        """
        if not driver:
            raise ValueError("必须提供WebDriver实例")
            
        self.driver = driver
        self.wait = WebDriverWait(driver, 100)  # 所有关键步骤100秒超时
        self.quick_wait = WebDriverWait(driver, 2)  # 快速检测2秒超时
        self.logger = logging.getLogger(__name__)
        self.actions = ActionChains(driver)
        self._init_components()

    def check_browser_alive(self) -> bool:
        """
        检查浏览器是否还活着
        """
        try:
            # 尝试执行一个简单的命令
            self.driver.current_url
            return True
        except:
            return False

    def ensure_browser_active(self) -> bool:
        """
        确保浏览器处于活动状态，如果不是则尝试重新连接
        """
        if self.check_browser_alive():
            return True

        try:
            if self.adspower_id:
                # 尝试重新连接AdsPower浏览器
                self.logger.info("尝试重新连接AdsPower浏览器...")
                api_url = f"http://local.adspower.net:50325/api/v1/browser/start"
                response = requests.get(api_url, params={"user_id": self.adspower_id})
                data = response.json()
                
                if data.get("code") == 0:
                    debugger_address = data["data"]["ws"]["selenium"]
                    chrome_driver_path = data["data"]["webdriver"]
                    
                    # 重新创建WebDriver实例
                    chrome_options = webdriver.ChromeOptions()
                    chrome_options.add_experimental_option("debuggerAddress", debugger_address)
                    service = Service(executable_path=chrome_driver_path)
                    
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    self.wait = WebDriverWait(self.driver, 100)
                    self._init_components()  # 重新初始化组件
                    
                    self.logger.info("成功重新连接到浏览器")
                    return True
                else:
                    self.logger.error(f"重新连接失败: {data.get('msg')}")
                    return False
            else:
                self.logger.error("浏览器已断开连接且无法重新连接")
                return False
                
        except Exception as e:
            self.logger.error(f"重新连接浏览器时出错: {str(e)}")
            return False

    def start_register(self, store_data: Dict) -> bool:
        """
        开始Shopify注册流程
        """
        try:
            # 确保浏览器处于活动状态
            if not self.ensure_browser_active():
                return False

            self.logger.info("开始Shopify注册...")
            
            # 打开Shopify注册页面
            self.driver.get('https://www.shopify.com/signup')
            time.sleep(3)

            # 检查页面是否加载成功
            try:
                self.wait.until(
                    EC.presence_of_element_located((By.ID, "account_email"))
                )
            except TimeoutException:
                self.logger.error("Shopify注册页面加载失败")
                return False

            # ... 后续注册流程 ...

        except Exception as e:
            self.logger.error(f"开始Shopify注册时出错: {str(e)}")
            return False

    def process_store(self, store_data: Dict, excel_handler) -> bool:
        """处理商店注册流程"""
        try:
            # 确保浏览器处于活动状态
            if not self.check_browser_alive():
                self.logger.error("浏览器连接已断开")
                return False

            # 开始Shopify注册流程
            self.logger.info("开始Shopify注册流程...")
            # 在当前标签页打开注册页面
            self.driver.get('https://www.shopify.com/free-trial')
            self.logger.info(f"已打开Shopify注册页面: {self.driver.current_url}")
            time.sleep(3)

            # 首页点击Start free trial按钮
            try:
                start_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[text()='Start free trial']"))
                )
                self.logger.info("找到'Start free trial'按钮")
                # 使用JavaScript点击按钮，确保在当前页面跳转
                self.driver.execute_script("arguments[0].click();", start_button)
                self.logger.info("已点击'Start free trial'按钮")
                time.sleep(2)
            except Exception as e:
                self.logger.error(f"点击Start free trial按钮失败: {str(e)}")
                return False

            # 等待CF验证完成
            self.logger.info("等待Cloudflare验证...")
            if not self.wait_for_cf_check(timeout=100):
                self.logger.error("Cloudflare验证超时")
                return False
            self.logger.info("Cloudflare验证完成")
            # 等待并点击Sign up with email按钮
            retry_interval = 0.2  # 每0.2秒检查一次
            max_wait_time = 30  # 最多等待30秒
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                try:
                    # 使用更精确的选择器定位按钮
                    selectors = [
                        # 方式1: 使用class和内容组合
                        "//div[contains(@class, 'account-picker__item-content') and contains(@class, 'account-picker__action') and contains(@class, 'content') and contains(text(), 'Sign up with email')]",
                        # 方式2: 使用父子元素关系
                        "//div[contains(@class, 'account-picker__item-content')]//div[contains(text(), 'Sign up with email')]",
                        # 方式3: 使用文本内容
                        "//*[normalize-space()='Sign up with email']",
                        # 方式4: 备用选择器
                        "//div[contains(@class, 'content') and contains(text(), 'Sign up with email')]"
                    ]

                    for selector in selectors:
                        try:
                            email_signup_button = self.quick_wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if email_signup_button.is_displayed() and email_signup_button.is_enabled():
                                self.logger.info(f"找到'Sign up with email'按钮 (使用选择器: {selector})")
                                # 尝试使用JavaScript点击按钮
                                self.driver.execute_script("arguments[0].click();", email_signup_button)
                                self.logger.info("已点击'Sign up with email'按钮")
                                time.sleep(2)
                                break
                        except:
                            continue
                    else:
                        # 如果当前循环没有找到按钮，继续外层循环
                        time.sleep(retry_interval)
                        continue
                    
                    # 如果成功点击了按钮，跳出外层循环
                    break

                except Exception as e:
                    self.logger.debug(f"当前尝试查找按钮失败: {str(e)}")
                    time.sleep(retry_interval)
            else:
                self.logger.error("未找到'Sign up with email'按钮，已尝试所有可能的定位方式")
                return False
            # 填写注册表单
            try:
                # 等待邮箱和密码输入框
                self.logger.info("等待注册表单加载...")
                email_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, "account_email"))
                )
                password_input = self.wait.until(
                    EC.presence_of_element_located((By.ID, "account_password"))
                )

                # 输入邮箱
                self.logger.info("准备输入邮箱...")
                email_input.clear()
                email_input.send_keys(store_data['email'])
                self.logger.info(f"已输入邮箱: {store_data['email']}")
                time.sleep(1)

                # 输入密码
                self.logger.info("准备输入密码...")
                password_input.clear()
                password_input.send_keys(store_data['password'])
                self.logger.info("密码已输入")
                time.sleep(1)

                # 检查是否存在hCaptcha
                try:
                    # 使用quick_wait快速检查是否存在hCaptcha iframe
                    hcaptcha_frames = self.driver.find_elements(By.XPATH, "//iframe[contains(@src, 'hcaptcha.com')]")
                    if len(hcaptcha_frames) > 0 and hcaptcha_frames[0].is_displayed():
                        self.logger.info("检测到hCaptcha，等待验证完成...")
                        # 等待验证完成
                        start_time = time.time()
                        while time.time() - start_time < 60:  # 最多等待60秒
                            if self.check_hcaptcha_success():
                                self.logger.info("检测到hCaptcha验证成功标志")
                                break
                            time.sleep(0.2)  # 加快检测频率
                        else:
                            self.logger.info("验证等待超时，尝试提交...")
                    else:
                        self.logger.info("页面上没有hCaptcha验证")
                except:
                    self.logger.info("页面上没有hCaptcha验证")

                # 尝试提交表单
                max_attempts = 5  # 最多尝试5次
                for attempt in range(max_attempts):
                    self.logger.info(f"第{attempt + 1}次尝试提交表单...")
                    try:
                        password_input.send_keys(Keys.ENTER)
                        self.logger.info("使用回车键提交表单")
                    except:
                        try:
                            create_button = self.wait.until(
                                EC.presence_of_element_located((
                                    By.XPATH, 
                                    "//button[@type='submit' and contains(@class, 'ui-button--primary')]"
                                ))
                            )
                            create_button.click()
                            self.logger.info("已点击提交按钮")
                        except:
                            self.logger.warning("提交失败")

                    # 检查是否进入下一步
                    time.sleep(3)
                    if self.check_next_step():
                        self.logger.info("已成功进入下一步")
                        break
                    
                    self.logger.info("未检测到页面变化，等待2秒后重试...")
                    time.sleep(2)
                else:
                    self.logger.error(f"尝试{max_attempts}次后仍未能进入下一步")
                    return False

            except Exception as e:
                self.logger.error(f"填写注册表单失败: {str(e)}")
                return False

            # 等待并处理后续步骤
            while True:
                next_step = self.check_next_step()
                if not next_step:
                    self.logger.error("等待下一步超时")
                    return False

                if next_step == "dashboard":
                    self.logger.info("已成功进入Shopify仪表盘")
                    # 记录成功状态
                    if excel_handler:
                        try:
                            excel_handler.update_store_status(
                                store_data.get('business_name', ''), 
                                'success',
                                f"Store URL: {self.driver.current_url}"
                            )
                        except Exception as e:
                            self.logger.error(f"更新Excel状态失败: {str(e)}")
                    return True

                elif next_step == "skip_setup":
                    self.logger.info("点击'I don't want help setting up'...")
                    try:
                        skip_link = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'I don't want help setting up')]"))
                        )
                        skip_link.click()
                        time.sleep(2)
                    except Exception as e:
                        self.logger.error(f"点击跳过设置链接失败: {str(e)}")
                        return False

                elif next_step == "skip_plan":
                    self.logger.info("点击'Skip, I'll decide later'...")
                    try:
                        skip_link = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Skip, I'll decide later')]"))
                        )
                        skip_link.click()
                        time.sleep(2)
                    except Exception as e:
                        self.logger.error(f"点击跳过计划选择链接失败: {str(e)}")
                        return False

                elif next_step == "setup_page":
                    self.logger.info("检测到设置页面，点击跳过设置...")
                    try:
                        skip_button = self.wait.until(
                            EC.element_to_be_clickable((
                                By.XPATH,
                                "//button[contains(@class, 'gui-TmOq5') and contains(text(), 'I don't want help setting up')]"
                            ))
                        )
                        skip_button.click()
                        self.logger.info("已点击跳过设置按钮")
                        time.sleep(2)
                        continue
                    except Exception as e:
                        self.logger.error(f"点击跳过设置按钮失败: {str(e)}")
                        return False

                time.sleep(1)

            return True

        except Exception as e:
            self.logger.error(f"处理商店时出错: {str(e)}")
            if excel_handler:
                try:
                    excel_handler.update_store_status(
                        store_data.get('business_name', ''), 
                        'failed',
                        f"Error: {str(e)}"
                    )
                except:
                    pass
            return False

    def _init_components(self):
        """初始化组件"""
        if not self.driver:
            return
        self.human = HumanLikeActions(self.driver)
        self.shopify_payments = ShopifyPayments(self.driver)
        self.shopify_2fa = Shopify2FA(self.driver)
        self.twofa_live = TwoFaLive(self.driver)

    def close(self):
        """关闭浏览器"""
        if self.adspower:
            self.adspower.close_browser()
        self.driver = None
        self._init_components()

    def check_next_step(self, max_time=100):
        """快速检测下一步的可能元素"""
        start_time = time.time()
        while time.time() - start_time < max_time:
            try:
                # 检查是否已经在Shopify仪表盘
                if "admin.shopify.com/store" in self.driver.current_url:
                    # 双重确认 - 检查典型的仪表盘元素
                    try:
                        # 检查左侧菜单栏
                        self.quick_wait.until(
                            EC.presence_of_element_located((By.XPATH, "//span[contains(text(), 'Home')]"))
                        )
                        return "dashboard"
                    except:
                        pass
            except:
                pass

            try:
                # 检查Start free trial按钮
                if self.quick_wait.until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Start free trial')]"))
                ):
                    return "start_trial"
            except:
                pass

            try:
                # 检查Sign up with email按钮
                if self.quick_wait.until(
                    EC.presence_of_element_located((By.XPATH, "//button[contains(text(), 'Sign up with email')]"))
                ):
                    return "email_signup"
            except:
                pass

            # 检查设置页面
            try:
                if "admin.shopify.com/signup/" in self.driver.current_url:
                    # 检查"Let's get started"页面和跳过按钮
                    title = self.quick_wait.until(
                        EC.presence_of_element_located((
                            By.XPATH, "//h1[contains(text(), 'Let's get started')]"
                        ))
                    )
                    skip_button = self.quick_wait.until(
                        EC.presence_of_element_located((
                            By.XPATH, "//button[contains(@class, 'gui-TmOq5') and contains(text(), 'I don't want help setting up')]"
                        ))
                    )
                    if title.is_displayed() and skip_button.is_displayed():
                        return "setup_page"
            except:
                pass

            try:
                # 检查"I don't want help setting up"链接
                if self.quick_wait.until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'I don't want help setting up')]"))
                ):
                    return "skip_setup"
            except:
                pass

            try:
                # 检查"Skip, I'll decide later"链接
                if self.quick_wait.until(
                    EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Skip, I'll decide later')]"))
                ):
                    return "skip_plan"
            except:
                pass

            time.sleep(0.5)

        self.logger.error(f"等待下一步超时（{max_time}秒）")
        return None

    def register_shopify(self) -> bool:
        """注册Shopify商店"""
        try:
            # 打开Shopify注册页面
            self.driver.get('https://www.shopify.com/signup')
            time.sleep(3)

            while True:
                next_step = self.check_next_step()
                if not next_step:
                    return False

                if next_step == "dashboard":
                    self.logger.info("成功进入Shopify仪表盘")
                    return True

                elif next_step == "captcha":
                    self.logger.info("处理验证码...")
                    if not self.handle_recaptcha():
                        return False

                elif next_step == "skip_setup":
                    self.logger.info("跳过设置步骤...")
                    if not self.skip_all_steps():
                        return False

                # 每个步骤后检查是否已登录成功
                try:
                    if "myshopify.com/admin" in self.driver.current_url:
                        self.logger.info("检测到已进入Shopify仪表盘")
                        return True
                except:
                    pass

                time.sleep(1)  # 避免过于频繁的检查

        except Exception as e:
            self.logger.error(f"Shopify注册失败: {str(e)}")
            return False

    def handle_recaptcha(self) -> bool:
        """处理验证码"""
        try:
            # 首先检查页面是否真的存在验证码iframe
            try:
                # 使用更精确的选择器来检测验证码
                recaptcha_present = False
                recaptcha_selectors = [
                    "//iframe[contains(@src, 'recaptcha/api2/anchor')]",
                    "//iframe[contains(@src, 'recaptcha/api2/bframe')]",
                    "//div[@class='g-recaptcha']",
                    "//div[contains(@class, 'recaptcha')]"
                ]
                
                for selector in recaptcha_selectors:
                    try:
                        if self.quick_wait.until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        ):
                            recaptcha_present = True
                            self.logger.info(f"检测到验证码元素: {selector}")
                            break
                    except:
                        continue
                
                if not recaptcha_present:
                    self.logger.info("页面上没有检测到验证码")
                    return True
                    
                # 如果存在验证码，等待其处理完成
                self.logger.info("等待验证码处理...")
                start_time = time.time()
                while time.time() - start_time < 100:  # 最多等待100秒
                    try:
                        # 再次检查验证码是否还存在
                        recaptcha_still_present = False
                        for selector in recaptcha_selectors:
                            try:
                                if self.quick_wait.until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                ):
                                    recaptcha_still_present = True
                                    break
                            except:
                                continue
                        
                        if not recaptcha_still_present:
                            self.logger.info("验证码已处理完成")
                            return True
                        
                        time.sleep(2)
                    except:
                        self.logger.info("验证码已处理完成")
                        return True

                self.logger.error("验证码处理超时")
                return False
                
            except Exception as e:
                self.logger.debug(f"检查验证码时出错: {str(e)}")
                return True  # 如果检查过程出错，假定没有验证码

        except Exception as e:
            self.logger.error(f"验证码处理出错: {str(e)}")
            return False

    def skip_all_steps(self) -> bool:
        """跳过所有设置步骤"""
        try:
            while True:
                try:
                    skip_button = self.quick_wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Skip')]"))
                    )
                    skip_button.click()
                    time.sleep(1)
                except TimeoutException:
                    break

            return True

        except Exception as e:
            self.logger.error(f"跳过设置步骤时出错: {str(e)}")
            return False

    def wait_for_cf_check(self, timeout=100):
        """等待Cloudflare验证完成并处理注册页面"""
        self.logger.info("等待Cloudflare验证...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 检查当前URL是否已经变成了注册页面
                current_url = self.driver.current_url
                if "accounts.shopify.com/signup" in current_url:
                    self.logger.info("Cloudflare验证通过，已进入注册页面")
                    time.sleep(3)  # 等待页面完全加载
                    return True
                    
                # 检查是否仍在CF验证页面
                try:
                    if "challenges.cloudflare.com" in current_url:
                        self.logger.debug("仍在Cloudflare验证中...")
                        time.sleep(2)
                        continue
                except:
                    pass

                # 检查是否有CF验证iframe
                try:
                    cf_frame = self.quick_wait.until(
                        EC.presence_of_element_located((By.ID, "cf-challenge-iframe"))
                    )
                    if cf_frame.is_displayed():
                        self.logger.debug("检测到Cloudflare验证iframe...")
                        time.sleep(2)
                        continue
                except:
                    pass

                time.sleep(1)
            except Exception as e:
                self.logger.debug(f"等待过程中出错: {str(e)}")
                time.sleep(1)
        
        self.logger.error("Cloudflare验证或页面加载超时")
        return False

    def click_element_with_retry(self, element, element_name: str, success_condition, max_retries=3) -> bool:
        """
        通用的元素点击重试方法
        Args:
            element: 要点击的元素
            element_name: 元素名称（用于日志）
            success_condition: 点击成功的判断条件（函数）
            max_retries: 最大重试次数
        """
        click_methods = [
            # 方法1: 常规点击
            lambda: element.click(),
            # 方法2: Actions链点击
            lambda: self.actions.move_to_element(element).click().perform(),
            # 方法3: JavaScript点击
            lambda: self.driver.execute_script("arguments[0].click();", element)
        ]
        
        for i, click_method in enumerate(click_methods, 1):
            try:
                self.logger.info(f"尝试第{i}种方式点击{element_name}...")
                click_method()
                time.sleep(2)
                
                if success_condition():
                    self.logger.info(f"第{i}次尝试点击{element_name}成功")
                    return True
            except Exception as e:
                self.logger.warning(f"第{i}种点击方式失败: {str(e)}")
                continue
        
        self.logger.error(f"有点击{element_name}方式都失败")
        return False

    def wait_for_page_load(self, url_pattern: str, timeout: int, page_name: str) -> bool:
        """
        通用的页面加载等待方法
        Args:
            url_pattern: URL匹配模式
            timeout: 超时时间
            page_name: 页面名称（用于日志）
        """
        self.logger.info(f"等待{page_name}加载...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if url_pattern in self.driver.current_url:
                    self.logger.info(f"{page_name}加载完成")
                    time.sleep(3)  # 等待页面完全加载
                    return True
            except:
                pass
            time.sleep(1)
        
        self.logger.error(f"{page_name}加载超时")
        return False

    def wait_for_recaptcha(self, timeout=100) -> bool:
        """等待谷歌验证完成"""
        self.logger.info("检查是否需要处理谷歌验证...")
        start_time = time.time()
        
        try:
            # 检查是否存在验证码iframe
            recaptcha_present = False
            try:
                recaptcha = self.quick_wait.until(
                    EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'recaptcha')]"))
                )
                recaptcha_present = True
                self.logger.info("检测到谷歌验证，等待插件处理...")
            except:
                self.logger.info("未检测到谷歌验证，继续注册流程")
                return True
            
            if recaptcha_present:
                while time.time() - start_time < timeout:
                    try:
                        # 检查验证码是否还在
                        self.quick_wait.until(
                            EC.presence_of_element_located((By.XPATH, "//iframe[contains(@src, 'recaptcha')]"))
                        )
                        time.sleep(2)
                    except:
                        self.logger.info("谷歌验证已完成")
                        return True
                        
                self.logger.error("谷歌验证等待超时")
                return False
                
        except Exception as e:
            self.logger.error(f"处理谷歌验证时出错: {str(e)}")
            return False

    def fill_signup_form(self, store_data: Dict) -> bool:
        """填写注册表单"""
        try:
            # 输入邮箱
            self.logger.info("正在输入邮箱...")
            email_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "account_email"))
            )
            email_input.clear()
            self.actions.move_to_element(email_input).click().perform()
            time.sleep(0.5)
            email_input.send_keys(store_data['email'])
            time.sleep(1)
            
            # 输入密码
            self.logger.info("正在输入密码...")
            password_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "account_password"))
            )
            password_input.clear()
            self.actions.move_to_element(password_input).click().perform()
            time.sleep(0.5)
            password_input.send_keys(store_data['password'])
            time.sleep(1)
            
            # 等待谷歌验证完成
            if not self.wait_for_recaptcha(timeout=100):
                return False
            
            # 点击创建账号按钮
            self.logger.info("点击创建账号按钮...")
            create_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Create your account')]"))
            )
            create_button.click()
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"填写注册表单失败: {str(e)}")
            return False

    def check_signup_page_elements(self) -> str:
        """
        检查注册页面的元素状态
        Returns:
            str: 检测到的元素类型
        """
        try:
            # 检查"Sign up with email"按钮
            try:
                email_button = self.quick_wait.until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//button[contains(@class, 'ui-button') and contains(., 'Sign up with email')]"
                    ))
                )
                if email_button.is_displayed() and email_button.is_enabled():
                    self.logger.debug("检测到'Sign up with email'按钮可点击")
                    return "email_signup"
            except:
                pass

            # 检查页面标题
            try:
                title = self.quick_wait.until(
                    EC.presence_of_element_located((
                        By.XPATH, 
                        "//h1[contains(text(), 'Start your free trial')]"
                    ))
                )
                if title.is_displayed():
                    self.logger.debug("检测到注册页面标题")
            except:
                self.logger.debug("未检测到注册页面标题")

            # 检查其他登录选项
            try:
                login_options = self.quick_wait.until(
                    EC.presence_of_all_elements_located((
                        By.XPATH,
                        "//button[contains(@class, 'ui-button') and contains(., 'Sign up with')]"
                    ))
                )
                if login_options:
                    self.logger.debug(f"检测到 {len(login_options)} 个登录选项按钮")
            except:
                self.logger.debug("未检测到登录选项按钮")

            return None

        except Exception as e:
            self.logger.error(f"检查注册页面元素时出错: {str(e)}")
            return None

    def check_plugin_status(self):
        """检查插件处理状态"""
        try:
            # 检查验证完成的标志
            success_indicators = [
                # 方式1: 检查div元素
                "//div[@id='mymessage' and @class='fankui']",
                # 方式2: 检查完整的元素
                "//div[@id='mymessage' and @class='fankui' and @style='position: fixed; top: 0px; left: 0px; z-index: 99999999; display: block;']",
                # 方式3: 检查文本内容
                "//div[contains(text(), 'Automatic recognition completed')]",
                # 方式4: 检查html结构
                "//html[@data-id='hcaptcha-frame']//div[@id='mymessage']"
            ]
            
            for indicator in success_indicators:
                try:
                    element = self.quick_wait.until(EC.presence_of_element_located((By.XPATH, indicator)))
                    if element.is_displayed():
                        return True
                except:
                    continue
            return False
        except:
            return False

    def check_hcaptcha_frame(self):
        """检查hCaptcha验证码框是否存在"""
        try:
            frames = self.driver.find_elements(By.XPATH, "//iframe[contains(@src, 'hcaptcha.com/captcha')]")
            return len(frames) > 0
        except:
            return False

    def check_hcaptcha_success(self):
        """检查hCaptcha是否验证成功"""
        try:
            # 通过图片地址检查验证成功标志
            success_img = self.quick_wait.until(
                EC.presence_of_element_located((
                    By.XPATH, 
                    "//img[contains(@src, 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAABmJLR0QA')]"
                ))
            )
            if success_img.is_displayed():
                return True
            return False
        except:
            return False