# -*- coding: utf-8 -*-
import pandas as pd
import os
import logging
from typing import Optional, Dict

class ExcelHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.logger = logging.getLogger(__name__)
        self.df = self.read_excel()

    def read_excel(self):
        """
        读取Excel文件中的数据
        """
        try:
            # 读取Excel文件，确保所有列名匹配
            required_columns = [
                'adspower_name', 'email', 'password', 'recovery_email',
                'business_name', 'first_name', 'last_name', 'birthday',
                'ssn', 'phone', 'address', 'city', 'state', 'zip_code',
                'ein', 'business_phone', 'business_address', 'business_city',
                'business_state', 'business_zip', '2fa_code', 'status', 'notes'
            ]
            
            df = pd.read_excel(self.file_path)
            
            # 验证所有必需的列是否存在
            missing_columns = set(required_columns) - set(df.columns)
            if missing_columns:
                raise ValueError(f"Excel文件缺少以下列: {missing_columns}")
            
            return df
        except Exception as e:
            self.logger.error(f"读取Excel文件失败: {str(e)}")
            raise

    def get_next_store(self) -> Optional[Dict]:
        """
        获取下一个待处理的商店数据
        
        Returns:
            包含商店数据的字典，如果没有更多数据则返回None
        """
        try:
            # 查找状态为空或failed的行
            pending_stores = self.df[
                (self.df['status'].isna()) | 
                (self.df['status'] == 'failed')
            ]
            
            if pending_stores.empty:
                self.logger.info("没有待处理的商店")
                return None
                
            # 获取第一个待处理的商店
            store = pending_stores.iloc[0].to_dict()
            return store
            
        except Exception as e:
            self.logger.error(f"获取商店数据时出错: {str(e)}")
            return None

    def update_store_status(self, store_name: str, status: str, notes: str = '') -> bool:
        """
        更新商店状态
        
        Args:
            store_name: 商店名称
            status: 新状态 ('success' 或 'failed')
            notes: 备注信息
        """
        try:
            # 查找匹配的行
            mask = self.df['business_name'] == store_name
            if not mask.any():
                self.logger.error(f"未找到商店: {store_name}")
                return False
                
            # 更新状态和备注
            self.df.loc[mask, 'status'] = status
            if notes:
                self.df.loc[mask, 'notes'] = notes
            
            # 保存更改
            self.df.to_excel(self.file_path, index=False)
            self.logger.info(f"已更新商店 {store_name} 的状态为: {status}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新商店状态时出错: {str(e)}")
            return False

    def update_status(self, df, index, status, notes=''):
        """
        更新Excel中某一行的状态和备注
        """
        try:
            df.at[index, 'status'] = status
            if notes:
                df.at[index, 'notes'] = notes
            df.to_excel(self.file_path, index=False)
            self.logger.info(f"更新状态成功: {status}")
        except Exception as e:
            self.logger.error(f"更新状态失败: {str(e)}")
            raise

    def get_all_data(self):
        """
        获取所有数据
        """
        try:
            return pd.read_excel(self.file_path)
        except Exception as e:
            self.logger.error(f"获取数据失败: {str(e)}")
            raise 