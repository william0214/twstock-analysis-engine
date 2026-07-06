#!/usr/bin/env python3
"""
台股數據爬取系統
StockDataCrawler類用於爬取台灣證券交易所的股票數據
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import logging
from typing import Dict, List, Optional, Tuple
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockDataCrawler:
    """台股數據爬取器"""
    
    def __init__(self):
        self.base_url = "https://openapi.twse.com.tw/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        })
        
    def get_daily_stock_data(self) -> Optional[List[Dict]]:
        """
        獲取上市個股日成交資訊
        
        Returns:
            List[Dict]: 股票數據列表，每個字典包含股票的交易信息
        """
        try:
            url = f"{self.base_url}/exchangeReport/STOCK_DAY_ALL"
            logger.info(f"正在獲取股票日成交資訊: {url}")
            
            response = self.session.get(url, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"成功獲取 {len(data)} 筆股票數據")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"獲取股票數據時發生網路錯誤: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析JSON數據時發生錯誤: {e}")
            return None
        except Exception as e:
            logger.error(f"獲取股票數據時發生未知錯誤: {e}")
            return None
    
    def get_market_index_data(self) -> Optional[Dict]:
        """
        獲取大盤指數資訊
        
        Returns:
            Dict: 大盤指數數據
        """
        try:
            url = f"{self.base_url}/exchangeReport/MI_INDEX"
            logger.info(f"正在獲取大盤指數資訊: {url}")
            
            response = self.session.get(url, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            logger.info("成功獲取大盤指數數據")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"獲取大盤指數數據時發生網路錯誤: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析大盤指數JSON數據時發生錯誤: {e}")
            return None
        except Exception as e:
            logger.error(f"獲取大盤指數數據時發生未知錯誤: {e}")
            return None
    
    def get_pe_ratio_data(self) -> Optional[List[Dict]]:
        """
        獲取上市個股本益比資訊
        
        Returns:
            List[Dict]: 本益比數據列表
        """
        try:
            url = f"{self.base_url}/exchangeReport/BWIBBU_ALL"
            logger.info(f"正在獲取本益比資訊: {url}")
            
            response = self.session.get(url, timeout=30, verify=False)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"成功獲取 {len(data)} 筆本益比數據")
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"獲取本益比數據時發生網路錯誤: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"解析本益比JSON數據時發生錯誤: {e}")
            return None
        except Exception as e:
            logger.error(f"獲取本益比數據時發生未知錯誤: {e}")
            return None
    
    def process_stock_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        """
        處理原始股票數據，轉換為DataFrame格式
        
        Args:
            raw_data: 原始股票數據列表
            
        Returns:
            pd.DataFrame: 處理後的股票數據
        """
        if not raw_data:
            return pd.DataFrame()
        
        try:
            # 轉換為DataFrame
            df = pd.DataFrame(raw_data)
            
            # 數據清理和類型轉換
            numeric_columns = ['TradeVolume', 'TradeValue', 'OpeningPrice', 
                             'HighestPrice', 'LowestPrice', 'ClosingPrice', 'Transaction']
            
            for col in numeric_columns:
                if col in df.columns:
                    # 移除逗號並轉換為數值
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '', regex=False), errors='coerce')
            
            # 處理漲跌幅
            if 'Change' in df.columns and 'ClosingPrice' in df.columns:
                df['Change'] = pd.to_numeric(df['Change'].astype(str).str.replace(',', '', regex=False), errors='coerce')
                # 使用安全的除法，避免除以零或無窮值
                denom = df['ClosingPrice'] - df['Change']
                with np.errstate(divide='ignore', invalid='ignore'):
                    cp = (df['Change'] / denom) * 100
                # 將 inf 或 NaN 轉為 0，並四捨五入到小數點 2 位
                cp = cp.replace([np.inf, -np.inf], np.nan).fillna(0).round(2)
                df['ChangePercent'] = cp
            
            # 計算市值（假設以千股為單位）
            if 'TradeVolume' in df.columns and 'ClosingPrice' in df.columns:
                # MarketValue = TradeVolume * ClosingPrice (單位依據原始資料，必要時可調整除以千或百萬)
                df['MarketValue'] = df['TradeVolume'] * df['ClosingPrice']
            
            # 添加日期
            df['Date'] = datetime.now().strftime('%Y-%m-%d')
            
            logger.info(f"成功處理 {len(df)} 筆股票數據")
            return df
            
        except Exception as e:
            logger.error(f"處理股票數據時發生錯誤: {e}")
            return pd.DataFrame()
    
    def identify_limit_up_stocks(self, df: pd.DataFrame, limit_up_threshold: float = 9.5) -> pd.DataFrame:
        """
        識別漲停股票
        
        Args:
            df: 股票數據DataFrame
            limit_up_threshold: 漲停閾值（預設9.5%）
            
        Returns:
            pd.DataFrame: 漲停股票數據
        """
        if df.empty or 'ChangePercent' not in df.columns:
            return pd.DataFrame()
        
        try:
            # 篩選漲幅超過閾值的股票
            limit_up_stocks = df[df['ChangePercent'] >= limit_up_threshold].copy()
            
            # 按漲幅排序
            limit_up_stocks = limit_up_stocks.sort_values('ChangePercent', ascending=False)
            
            logger.info(f"識別出 {len(limit_up_stocks)} 檔漲停股票")
            return limit_up_stocks
            
        except Exception as e:
            logger.error(f"識別漲停股票時發生錯誤: {e}")
            return pd.DataFrame()
    
    def identify_strong_stocks(self, df: pd.DataFrame, 
                             volume_threshold: float = 1000000,
                             change_threshold: float = 3.0) -> pd.DataFrame:
        """
        識別強勢股票
        
        Args:
            df: 股票數據DataFrame
            volume_threshold: 成交量閾值
            change_threshold: 漲幅閾值
            
        Returns:
            pd.DataFrame: 強勢股票數據
        """
        if df.empty:
            return pd.DataFrame()
        
        try:
            # 篩選條件：成交量大且漲幅超過閾值
            strong_stocks = df[
                (df['TradeVolume'] >= volume_threshold) & 
                (df['ChangePercent'] >= change_threshold)
            ].copy()
            
            # 按成交量和漲幅綜合排序
            strong_stocks['Score'] = (strong_stocks['ChangePercent'] * 0.6 + 
                                    (strong_stocks['TradeVolume'] / 1000000) * 0.4)
            strong_stocks = strong_stocks.sort_values('Score', ascending=False)
            
            logger.info(f"識別出 {len(strong_stocks)} 檔強勢股票")
            return strong_stocks
            
        except Exception as e:
            logger.error(f"識別強勢股票時發生錯誤: {e}")
            return pd.DataFrame()
    
    def filter_small_cap_stocks(self, df: pd.DataFrame,
                               volume_threshold: float = 1000000) -> pd.DataFrame:
        """
        篩選具備流動性的股票（成交量門檻，非市值）

        原本用「成交金額（TradeVolume×ClosingPrice）≤ 100億」當市值代理排除股票，
        但這只是當日成交金額，不是公司市值（TWSE 現有的 3 個資料端點都沒有真正的
        股本/發行股數可算市值），用它篩選會誤判：低價高量股會被誤標成「小型股」，
        高價但當日量縮的股票反而被排除，跟實際公司規模無關。既然選股邏輯本來就
        只重視流動性、不在乎公司規模，改為只保留成交量下限（與 identify_strong_stocks
        的門檻一致），不再假裝在篩市值。

        Args:
            df: 股票數據DataFrame
            volume_threshold: 成交量門檻（預設100萬股）

        Returns:
            pd.DataFrame: 具備流動性的股票數據
        """
        if df.empty:
            return df

        try:
            if 'TradeVolume' not in df.columns:
                logger.warning('無 TradeVolume 欄位，跳過流動性篩選')
                return df

            df['TradeVolume'] = pd.to_numeric(df['TradeVolume'], errors='coerce').fillna(0)

            liquid_stocks = df[df['TradeVolume'] >= volume_threshold].copy()
            logger.info(f"篩選出 {len(liquid_stocks)} 檔流動性達標股票 (成交量門檻={volume_threshold})")
            return liquid_stocks

        except Exception as e:
            logger.error(f"篩選流動性股票時發生錯誤: {e}")
            return df
    
    def get_comprehensive_data(self) -> Dict:
        """
        獲取綜合股票數據
        
        Returns:
            Dict: 包含所有分析數據的字典
        """
        logger.info("開始獲取綜合股票數據...")
        
        # 獲取原始數據
        raw_stock_data = self.get_daily_stock_data()
        if not raw_stock_data:
            logger.error("無法獲取股票數據")
            return {}
        
        # 處理數據
        df = self.process_stock_data(raw_stock_data)
        if df.empty:
            logger.error("數據處理失敗")
            return {}
        
        # 分析數據
        limit_up_stocks = self.identify_limit_up_stocks(df)
        strong_stocks = self.identify_strong_stocks(df)
    
        small_cap_limit_up = self.filter_small_cap_stocks(limit_up_stocks)
        small_cap_strong = self.filter_small_cap_stocks(strong_stocks)
        
        # 獲取大盤數據
        market_data = self.get_market_index_data()
        
        # 獲取本益比數據
        pe_data = self.get_pe_ratio_data()
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'total_stocks': len(df),
            'all_stocks': df.to_dict('records'),
            'limit_up_stocks': limit_up_stocks.to_dict('records'),
            'strong_stocks': strong_stocks.to_dict('records'),
            'small_cap_limit_up': small_cap_limit_up.to_dict('records'),
            'small_cap_strong': small_cap_strong.to_dict('records'),
            'market_index': market_data,
            'pe_ratio_data': pe_data,
            'statistics': {
                'limit_up_count': len(limit_up_stocks),
                'strong_stocks_count': len(strong_stocks),
                'small_cap_limit_up_count': len(small_cap_limit_up),
                'small_cap_strong_count': len(small_cap_strong)
            }
        }
        
        logger.info("綜合數據獲取完成")
        return result

def main():
    """主函數，用於測試StockDataCrawler"""
    crawler = StockDataCrawler()
    
    # 測試獲取數據
    logger.info("開始測試股票數據爬取...")
    
    # 獲取綜合數據
    data = crawler.get_comprehensive_data()
    
    if data:
        # 正確顯示總檔案數與各類統計數字
        total = data.get('total_stocks') or len(data.get('all_stocks', []))
        print(f"總股票數: {total}")
        print(f"漲停股票數: {data['statistics'].get('limit_up_count')}")
        print(f"強勢股票數: {data['statistics'].get('strong_stocks_count')}")
        print(f"小型股漲停數: {data['statistics'].get('small_cap_limit_up_count')}")
        print(f"小型股強勢數: {data['statistics'].get('small_cap_strong_count')}")
        
        # 顯示前5檔小型股漲停股票
        if data['small_cap_limit_up']:
            print("\n前5檔小型股漲停股票:")
            for i, stock in enumerate(data['small_cap_limit_up'][:5]):
                print(f"{i+1}. {stock['Name']} ({stock['Code']}) - 漲幅: {stock.get('ChangePercent', 0):.2f}%")
    else:
        print("數據獲取失敗")

if __name__ == "__main__":
    main()

