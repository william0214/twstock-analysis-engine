#!/usr/bin/env python3
"""
爬取最新台股數據腳本
使用StockDataCrawler獲取最新的股票數據並保存
"""

import json
import os
import pandas as pd
from datetime import datetime
import logging
from stock_data_crawler import StockDataCrawler
from config import STOCK_DATA_DIR, MARKET_SUMMARY_DIR, DATA_DIR

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def save_data_to_files(data: dict, base_filename: str = "latest_stock_data"):
    """
    將數據保存到多個文件
    
    Args:
        data: 股票數據字典
        base_filename: 基礎文件名
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    try:
        # 保存完整數據為JSON
        json_filename = f"latest_stock_data_{timestamp}.json"
        json_filepath = os.path.join(STOCK_DATA_DIR, json_filename)
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"完整數據已保存到: {json_filepath}")
        
        # 保存漲停股票數據為CSV
        limit_up_filename = None
        if data.get('small_cap_limit_up'):
            limit_up_df = pd.DataFrame(data['small_cap_limit_up'])
            limit_up_filename = f"limit_up_stocks_{timestamp}.csv"
            limit_up_filepath = os.path.join(DATA_DIR, limit_up_filename)
            limit_up_df.to_csv(limit_up_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"小型股漲停數據已保存到: {limit_up_filepath}")
        
        # 保存強勢股票數據為CSV
        strong_filename = None
        if data.get('small_cap_strong'):
            strong_df = pd.DataFrame(data['small_cap_strong'])
            strong_filename = f"strong_stocks_{timestamp}.csv"
            strong_filepath = os.path.join(DATA_DIR, strong_filename)
            strong_df.to_csv(strong_filepath, index=False, encoding='utf-8-sig')
            logger.info(f"小型股強勢數據已保存到: {strong_filepath}")
        
        # 保存統計摘要
        summary = {
            'timestamp': data['timestamp'],
            'total_stocks': data['total_stocks'],
            'statistics': data['statistics'],
            'top_limit_up_stocks': data['small_cap_limit_up'][:10] if data.get('small_cap_limit_up') else [],
            'top_strong_stocks': data['small_cap_strong'][:10] if data.get('small_cap_strong') else []
        }
        
        summary_filename = f"market_summary_{timestamp}.json"
        summary_filepath = os.path.join(MARKET_SUMMARY_DIR, summary_filename)
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        logger.info(f"市場摘要已保存到: {summary_filepath}")
        
        return {
            'json_file': json_filepath,
            'limit_up_file': limit_up_filepath if limit_up_filename else None,
            'strong_file': strong_filepath if strong_filename else None,
            'summary_file': summary_filepath
        }
        
    except Exception as e:
        logger.error(f"保存數據時發生錯誤: {e}")
        return None

def analyze_market_trends(data: dict) -> dict:
    """
    分析市場趨勢
    
    Args:
        data: 股票數據字典
        
    Returns:
        dict: 市場趨勢分析結果
    """
    try:
        all_stocks = pd.DataFrame(data.get('all_stocks', []))
        
        if all_stocks.empty:
            return {}
        
        # 計算市場統計
        total_stocks = len(all_stocks)
        rising_stocks = len(all_stocks[all_stocks['ChangePercent'] > 0])
        falling_stocks = len(all_stocks[all_stocks['ChangePercent'] < 0])
        flat_stocks = len(all_stocks[all_stocks['ChangePercent'] == 0])
        
        # 計算平均漲跌幅
        avg_change = all_stocks['ChangePercent'].mean()
        
        # 計算成交量統計
        total_volume = all_stocks['TradeVolume'].sum()
        avg_volume = all_stocks['TradeVolume'].mean()
        
        # 找出成交量最大的股票
        top_volume_stocks = all_stocks.nlargest(5, 'TradeVolume')[['Code', 'Name', 'TradeVolume', 'ChangePercent']].to_dict('records')
        
        # 找出漲幅最大的股票
        top_gainers = all_stocks.nlargest(5, 'ChangePercent')[['Code', 'Name', 'ChangePercent', 'TradeVolume']].to_dict('records')
        
        # 找出跌幅最大的股票
        top_losers = all_stocks.nsmallest(5, 'ChangePercent')[['Code', 'Name', 'ChangePercent', 'TradeVolume']].to_dict('records')
        
        analysis = {
            'market_sentiment': {
                'total_stocks': total_stocks,
                'rising_stocks': rising_stocks,
                'falling_stocks': falling_stocks,
                'flat_stocks': flat_stocks,
                'rising_ratio': round(rising_stocks / total_stocks * 100, 2),
                'falling_ratio': round(falling_stocks / total_stocks * 100, 2)
            },
            'price_movement': {
                'average_change_percent': round(avg_change, 2),
                'market_direction': 'up' if avg_change > 0 else 'down' if avg_change < 0 else 'flat'
            },
            'volume_analysis': {
                'total_volume': int(total_volume),
                'average_volume': int(avg_volume)
            },
            'top_performers': {
                'top_volume_stocks': top_volume_stocks,
                'top_gainers': top_gainers,
                'top_losers': top_losers
            }
        }
        
        logger.info("市場趨勢分析完成")
        return analysis
        
    except Exception as e:
        logger.error(f"分析市場趨勢時發生錯誤: {e}")
        return {}

def main():
    """主函數"""
    logger.info("開始爬取最新台股數據...")
    
    # 初始化爬蟲
    crawler = StockDataCrawler()
    
    # 獲取綜合數據
    logger.info("正在獲取綜合股票數據...")
    data = crawler.get_comprehensive_data()
    
    if not data:
        logger.error("無法獲取股票數據")
        return False
    
    # 分析市場趨勢
    logger.info("正在分析市場趨勢...")
    market_analysis = analyze_market_trends(data)
    data['market_analysis'] = market_analysis
    
    # 保存數據到文件
    logger.info("正在保存數據到文件...")
    saved_files = save_data_to_files(data)
    
    if saved_files:
        logger.info("數據爬取和保存完成")
        
        # 顯示摘要信息
        print("\n=== 台股數據爬取摘要 ===")
        print(f"爬取時間: {data['timestamp']}")
        print(f"總股票數: {data['total_stocks']}")
        print(f"漲停股票數: {data['statistics']['limit_up_count']}")
        print(f"強勢股票數: {data['statistics']['strong_stocks_count']}")
        print(f"小型股漲停數: {data['statistics']['small_cap_limit_up_count']}")
        print(f"小型股強勢數: {data['statistics']['small_cap_strong_count']}")
        
        if market_analysis:
            print(f"\n=== 市場情緒分析 ===")
            sentiment = market_analysis.get('market_sentiment', {})
            print(f"上漲股票: {sentiment.get('rising_stocks', 0)} ({sentiment.get('rising_ratio', 0)}%)")
            print(f"下跌股票: {sentiment.get('falling_stocks', 0)} ({sentiment.get('falling_ratio', 0)}%)")
            print(f"平盤股票: {sentiment.get('flat_stocks', 0)}")
            
            price_movement = market_analysis.get('price_movement', {})
            print(f"平均漲跌幅: {price_movement.get('average_change_percent', 0)}%")
            print(f"市場方向: {price_movement.get('market_direction', 'unknown')}")
        
        print(f"\n=== 保存的文件 ===")
        for key, filename in saved_files.items():
            if filename:
                print(f"{key}: {filename}")
        
        return True
    else:
        logger.error("數據保存失敗")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ 數據爬取任務完成")
    else:
        print("\n❌ 數據爬取任務失敗")

