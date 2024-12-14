# -*- coding: utf-8 -*-
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict
import time
from .human_like_actions import HumanLikeActions

class ShopifyPayments:
    """处理Shopify Payments激活的类"""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.human = HumanLikeActions(driver)

    def navigate_to_payments(self) -> bool:
        """导航到支付设置页面"""
        try:
            # 获取当前商店的admin URL
            current_url = self.driver.current_url
            
            # 检查是否在Shopify后台
            if not "admin.shopify.com/store/" in current_url:
                print("当前不在Shopify管理后台")
                return False
            
            # 从URL中提取店铺专属URL
            # 例如：从 admin.shopify.com/store/mystore/xxx 提取 mystore
            store_name = current_url.split('/store/')[1].split('/')[0]
            
            # 构造payments页面URL
            payments_url = f"https://admin.shopify.com/store/{store_name}/settings/payments"
            self.driver.get(payments_url)
            self.human.random_sleep(2, 3)
            return True
            
        except Exception as e:
            print(f"导航到支付页面失败: {str(e)}")
            return False

    def activate_shopify_payments(self) -> bool:
        """激活Shopify Payments"""
        try:
            # 点击"Activate Shopify Payments"按钮
            activate_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Activate Shopify Payments')]"))
            )
            self.human.move_to_element_randomly(activate_button)
            self.human.random_sleep()
            activate_button.click()
            return True
            
        except Exception as e:
            print(f"激活Shopify Payments失败: {str(e)}")
            return False 

    def submit_business_details(self) -> bool:
        """点击Submit details按钮并开始设置商业信息"""
        try:
            # 等待页面加载
            self.human.random_sleep(2, 3)
            
            # 点击"Submit details"按钮
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit details')]"))
            )
            self.human.move_to_element_randomly(submit_button)
            self.human.random_sleep()
            submit_button.click()
            
            # 等待Complete account setup页面加载
            self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Set up Shopify Payments')]"))
            )
            
            # 检查是否成功进入setup页面
            if not "profile-assessment/interview" in self.driver.current_url:
                print("未能进入商家信息设置页面")
                return False
            
            # 选择商业类型
            if not self.select_business_type():
                return False
            
            return True
            
        except Exception as e:
            print(f"提交商家信息失败: {str(e)}")
            return False

    def select_business_type(self) -> bool:
        """选择商业类型为Sole proprietorship并进入下一步"""
        try:
            # 等待页面加载
            self.human.random_sleep(2, 3)
            
            # 选择"A registered business"选项
            registered_business = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='radio']/following-sibling::span[contains(text(), 'A registered business')]"))
            )
            self.human.move_to_element_randomly(registered_business)
            self.human.random_sleep()
            registered_business.click()
            
            # 等待下拉框可点击
            business_type_dropdown = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Select business type')]"))
            )
            self.human.move_to_element_randomly(business_type_dropdown)
            self.human.random_sleep()
            business_type_dropdown.click()
            
            # 选择"Sole proprietorship"选项
            sole_proprietorship = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Sole proprietorship']"))
            )
            self.human.move_to_element_randomly(sole_proprietorship)
            self.human.random_sleep()
            sole_proprietorship.click()
            
            # 点击Next按钮进入下一步
            if not self.click_next_step():
                return False
            
            return True
            
        except Exception as e:
            print(f"选择商业类型失败: {str(e)}")
            return False

    def click_next_step(self) -> bool:
        """点击Next按钮进入下一步"""
        try:
            # 等待Next按钮可点击
            next_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]"))
            )
            self.human.move_to_element_randomly(next_button)
            self.human.random_sleep()
            next_button.click()
            
            # 等待新页面加载
            self.human.random_sleep(2, 3)
            return True
            
        except Exception as e:
            print(f"点击Next按钮失败: {str(e)}")
            return False

    def fill_business_details(self, business_data: Dict[str, str]) -> bool:
        """
        填写商业资料
        
        Args:
            business_data: 包含商业信息的字典，需要包含以下字段：
                - business_name: 商业名称（例如：Tuthill Architecture, P.a.）
                - ein: EIN号码（9位数字）
                - phone: 电话号码（格式：(xxx) xxx-xxxx）
                - address: 完整地址
        """
        try:
            # 等待页面加载
            self.human.random_sleep(2, 3)
            
            # 填写注册商业名称
            business_name_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Registered business name']"))
            )
            self.human.move_to_element_randomly(business_name_input)
            self.human.random_sleep()
            business_name_input.clear()
            business_name_input.send_keys(business_data["business_name"])
            
            # 填写EIN号码
            ein_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Employer Identification Number (EIN)']"))
            )
            self.human.move_to_element_randomly(ein_input)
            self.human.random_sleep()
            ein_input.clear()
            ein_input.send_keys(business_data["ein"])
            
            # 填写电话号码
            phone_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Phone number']"))
            )
            self.human.move_to_element_randomly(phone_input)
            self.human.random_sleep()
            phone_input.clear()
            phone_input.send_keys(business_data["phone"])
            
            # 填写地址
            address_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Address']"))
            )
            self.human.move_to_element_randomly(address_input)
            self.human.random_sleep()
            address_input.clear()
            address_input.send_keys(business_data["address"])
            
            # 等待地址建议出现并选择
            try:
                address_suggestion = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//ul[@role='listbox']/li[1]"))
                )
                self.human.move_to_element_randomly(address_suggestion)
                self.human.random_sleep()
                address_suggestion.click()
            except:
                print("没有找到地址建议，继续使用手动输入的地址")
            
            # 点击Next进入下一步
            return self.click_next_step()
            
        except Exception as e:
            print(f"填写商业资料失败: {str(e)}")
            return False

    def fill_business_type_and_description(self, business_name: str) -> bool:
        """
        填写商业类型和服务描述（使用固定信息）
        
        Args:
            business_name: 商业名称，用于服务描述
        """
        try:
            # 等待页面加载
            self.human.random_sleep(2, 3)
            
            # 选择Retail类别
            category_dropdown = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Category')]"))
            )
            self.human.move_to_element_randomly(category_dropdown)
            self.human.random_sleep()
            category_dropdown.click()
            
            retail_option = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Retail']"))
            )
            self.human.move_to_element_randomly(retail_option)
            self.human.random_sleep()
            retail_option.click()
            
            # 选择Pets子类别
            subcategory_dropdown = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(@aria-label, 'Sub-category')]"))
            )
            self.human.move_to_element_randomly(subcategory_dropdown)
            self.human.random_sleep()
            subcategory_dropdown.click()
            
            pets_option = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[text()='Pets']"))
            )
            self.human.move_to_element_randomly(pets_option)
            self.human.random_sleep()
            pets_option.click()
            
            # 填写服务描述
            description = f"We at {business_name} are a customer experience focused company, all of our customers come from Facebook Ads, and when we receive an order we send it to our partners for fast shipping."
            
            description_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//textarea[contains(@placeholder, 'products or services')]"))
            )
            self.human.move_to_element_randomly(description_input)
            self.human.random_sleep()
            description_input.clear()
            description_input.send_keys(description)
            
            # 点击Next进入下一步
            return self.click_next_step()
            
        except Exception as e:
            print(f"填写商业类型和描述失败: {str(e)}")
            return False

    def fill_account_representative(self, business_data: Dict[str, str]) -> bool:
        """
        填写法人代表信息
        
        Args:
            business_data: 包含法人信息的字典，需要包含以下字段：
                - first_name: 名字
                - last_name: 姓氏
                - birth_month: 出生月
                - birth_day: 出生日
                - birth_year: 出生年
                - ssn: 社会安全号码
                - email: 邮箱地址
                - phone: 电话号码
                - address: 地址
        """
        try:
            # 等待页面加载
            self.human.random_sleep(2, 3)
            
            # 填写名字
            first_name_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='First name']"))
            )
            self.human.move_to_element_randomly(first_name_input)
            self.human.random_sleep()
            first_name_input.clear()
            first_name_input.send_keys(business_data["first_name"])
            
            # 填写姓氏
            last_name_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Last name']"))
            )
            self.human.move_to_element_randomly(last_name_input)
            self.human.random_sleep()
            last_name_input.clear()
            last_name_input.send_keys(business_data["last_name"])
            
            # 填写出生日期
            month_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='MM']"))
            )
            self.human.move_to_element_randomly(month_input)
            self.human.random_sleep()
            month_input.send_keys(business_data["birth_month"])
            
            day_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='DD']"))
            )
            self.human.move_to_element_randomly(day_input)
            self.human.random_sleep()
            day_input.send_keys(business_data["birth_day"])
            
            year_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@placeholder='YYYY']"))
            )
            self.human.move_to_element_randomly(year_input)
            self.human.random_sleep()
            year_input.send_keys(business_data["birth_year"])
            
            # 填写SSN
            ssn_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Social Security number (SSN)']"))
            )
            self.human.move_to_element_randomly(ssn_input)
            self.human.random_sleep()
            ssn_input.clear()
            ssn_input.send_keys(business_data["ssn"])
            
            # 填写邮箱
            email_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@type='email']"))
            )
            self.human.move_to_element_randomly(email_input)
            self.human.random_sleep()
            email_input.clear()
            email_input.send_keys(business_data["email"])
            
            # 填写地址
            address_input = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Address']"))
            )
            self.human.move_to_element_randomly(address_input)
            self.human.random_sleep()
            address_input.clear()
            address_input.send_keys(business_data["address"])
            
            # 等待地址建议出现并选择
            try:
                address_suggestion = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//ul[@role='listbox']/li[1]"))
                )
                self.human.move_to_element_randomly(address_suggestion)
                self.human.random_sleep()
                address_suggestion.click()
            except:
                print("没有找到地址建议，继续使用手动输入的地址")
            
            # 点击Next进入下一步
            return self.click_next_step()
            
        except Exception as e:
            print(f"填写法人代表信息失败: {str(e)}")
            return False

    def submit_for_verification(self) -> bool:
        """
        提交验证信息
        检查所有信息都已准备就绪（显示Ready状态）后提交验证
        """
        try:
            # 等待页面加载
            self.human.random_sleep(2, 3)
            
            # 检查所有信息是否都已准备就绪
            ready_statuses = self.wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//span[text()='Ready']"))
            )
            
            # 确保有3个Ready状态（商业信息、账户代表信息、条款确认）
            if len(ready_statuses) != 3:
                print(f"不是所有信息都已准备就绪，当前Ready状态数量: {len(ready_statuses)}")
                return False
            
            # 点击"Submit for verification"按钮
            submit_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit for verification')]"))
            )
            self.human.move_to_element_randomly(submit_button)
            self.human.random_sleep()
            submit_button.click()
            
            # 等待提交完成
            self.human.random_sleep(3, 5)
            
            # 检查是否成功提交
            try:
                success_message = self.wait.until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'submitted') or contains(text(), 'verification')]"))
                )
                print("验证信息提交成功")
                return True
            except:
                print("未检测到提交成功信息")
                return False
            
        except Exception as e:
            print(f"提交验证信息失败: {str(e)}")
            return False