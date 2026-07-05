#!/usr/bin/env python3
"""
台股漲停和強勢股票深度分析
分析漲停股票和強勢股票的特徵、行業分布、風險評估等
"""

import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import logging
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

from config import STOCK_DATA_DIR, TECHNICAL_ANALYSIS_DIR

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StockAnalyzer:
    """股票分析器"""
    
    def __init__(self, data_file: str):
        """
        初始化分析器
        
        Args:
            data_file: 股票數據JSON文件路徑
        """
        self.data_file = data_file
        self.data = self.load_data()
        
    def load_data(self) -> Dict:
        """載入股票數據"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"成功載入數據文件: {self.data_file}")
            return data
        except Exception as e:
            logger.error(f"載入數據文件失敗: {e}")
            return {}
    
    def analyze_limit_up_stocks(self) -> Dict:
        """
        分析漲停股票特徵
        
        Returns:
            Dict: 漲停股票分析結果
        """
        if not self.data.get('small_cap_limit_up'):
            return {}
        
        try:
            df = pd.DataFrame(self.data['small_cap_limit_up'])
            
            analysis = {
                'basic_stats': {
                    'total_count': len(df),
                    'avg_change_percent': df['ChangePercent'].mean(),
                    'avg_volume': df['TradeVolume'].mean(),
                    'avg_market_value': df['MarketValue'].mean(),
                    'total_trade_value': df['TradeValue'].sum()
                },
                'volume_analysis': {
                    'high_volume_stocks': len(df[df['TradeVolume'] > df['TradeVolume'].median()]),
                    'low_volume_stocks': len(df[df['TradeVolume'] <= df['TradeVolume'].median()]),
                    'volume_distribution': {
                        'min': df['TradeVolume'].min(),
                        'max': df['TradeVolume'].max(),
                        'median': df['TradeVolume'].median(),
                        'q1': df['TradeVolume'].quantile(0.25),
                        'q3': df['TradeVolume'].quantile(0.75)
                    }
                },
                'price_analysis': {
                    'price_range': {
                        'min_price': df['ClosingPrice'].min(),
                        'max_price': df['ClosingPrice'].max(),
                        'avg_price': df['ClosingPrice'].mean(),
                        'median_price': df['ClosingPrice'].median()
                    },
                    'high_price_stocks': len(df[df['ClosingPrice'] > 100]),
                    'mid_price_stocks': len(df[(df['ClosingPrice'] >= 50) & (df['ClosingPrice'] <= 100)]),
                    'low_price_stocks': len(df[df['ClosingPrice'] < 50])
                },
                'market_value_analysis': {
                    'avg_market_value': df['MarketValue'].mean(),
                    'median_market_value': df['MarketValue'].median(),
                    'small_cap_threshold': 5000000000,  # 50億
                    'micro_cap_count': len(df[df['MarketValue'] < 1000000000]),  # 10億以下
                    'small_cap_count': len(df[(df['MarketValue'] >= 1000000000) & (df['MarketValue'] < 5000000000)])
                },
                'top_performers': df.nlargest(5, 'ChangePercent')[['Code', 'Name', 'ChangePercent', 'TradeVolume', 'MarketValue']].to_dict('records'),
                'high_volume_performers': df.nlargest(5, 'TradeVolume')[['Code', 'Name', 'ChangePercent', 'TradeVolume', 'MarketValue']].to_dict('records')
            }
            
            logger.info("漲停股票分析完成")
            return analysis
            
        except Exception as e:
            logger.error(f"分析漲停股票時發生錯誤: {e}")
            return {}
    
    def analyze_strong_stocks(self) -> Dict:
        """
        分析強勢股票特徵
        
        Returns:
            Dict: 強勢股票分析結果
        """
        if not self.data.get('small_cap_strong'):
            return {}
        
        try:
            df = pd.DataFrame(self.data['small_cap_strong'])
            
            analysis = {
                'basic_stats': {
                    'total_count': len(df),
                    'avg_change_percent': df['ChangePercent'].mean(),
                    'avg_volume': df['TradeVolume'].mean(),
                    'avg_score': df['Score'].mean() if 'Score' in df.columns else 0,
                    'avg_market_value': df['MarketValue'].mean()
                },
                'change_distribution': {
                    'strong_growth': len(df[df['ChangePercent'] >= 7]),  # 強勢成長
                    'moderate_growth': len(df[(df['ChangePercent'] >= 5) & (df['ChangePercent'] < 7)]),  # 中等成長
                    'mild_growth': len(df[(df['ChangePercent'] >= 3) & (df['ChangePercent'] < 5)])  # 溫和成長
                },
                'volume_characteristics': {
                    'high_volume_threshold': df['TradeVolume'].quantile(0.75),
                    'high_volume_count': len(df[df['TradeVolume'] > df['TradeVolume'].quantile(0.75)]),
                    'active_trading_stocks': len(df[df['Transaction'] > df['Transaction'].median()])
                },
                'momentum_analysis': {
                    'high_momentum': len(df[(df['ChangePercent'] >= 6) & (df['TradeVolume'] > df['TradeVolume'].median())]),
                    'price_momentum': len(df[df['ChangePercent'] >= 5]),
                    'volume_momentum': len(df[df['TradeVolume'] > df['TradeVolume'].quantile(0.8)])
                },
                'top_by_score': df.nlargest(10, 'Score')[['Code', 'Name', 'ChangePercent', 'TradeVolume', 'Score']].to_dict('records') if 'Score' in df.columns else [],
                'top_by_change': df.nlargest(10, 'ChangePercent')[['Code', 'Name', 'ChangePercent', 'TradeVolume', 'MarketValue']].to_dict('records')
            }
            
            logger.info("強勢股票分析完成")
            return analysis
            
        except Exception as e:
            logger.error(f"分析強勢股票時發生錯誤: {e}")
            return {}
    
    def compare_limit_up_vs_strong(self) -> Dict:
        """
        比較漲停股票與強勢股票的差異
        
        Returns:
            Dict: 比較分析結果
        """
        try:
            limit_up_df = pd.DataFrame(self.data.get('small_cap_limit_up', []))
            strong_df = pd.DataFrame(self.data.get('small_cap_strong', []))
            
            if limit_up_df.empty or strong_df.empty:
                return {}
            
            comparison = {
                'count_comparison': {
                    'limit_up_count': len(limit_up_df),
                    'strong_count': len(strong_df),
                    'overlap_count': len(set(limit_up_df['Code']) & set(strong_df['Code']))
                },
                'average_metrics': {
                    'limit_up': {
                        'avg_change': limit_up_df['ChangePercent'].mean(),
                        'avg_volume': limit_up_df['TradeVolume'].mean(),
                        'avg_price': limit_up_df['ClosingPrice'].mean(),
                        'avg_market_value': limit_up_df['MarketValue'].mean()
                    },
                    'strong': {
                        'avg_change': strong_df['ChangePercent'].mean(),
                        'avg_volume': strong_df['TradeVolume'].mean(),
                        'avg_price': strong_df['ClosingPrice'].mean(),
                        'avg_market_value': strong_df['MarketValue'].mean()
                    }
                },
                'volume_comparison': {
                    'limit_up_high_volume': len(limit_up_df[limit_up_df['TradeVolume'] > 5000000]),
                    'strong_high_volume': len(strong_df[strong_df['TradeVolume'] > 5000000]),
                    'limit_up_median_volume': limit_up_df['TradeVolume'].median(),
                    'strong_median_volume': strong_df['TradeVolume'].median()
                },
                'overlapping_stocks': []
            }
            
            # 找出重疊的股票
            overlap_codes = set(limit_up_df['Code']) & set(strong_df['Code'])
            if overlap_codes:
                overlap_stocks = limit_up_df[limit_up_df['Code'].isin(overlap_codes)][['Code', 'Name', 'ChangePercent', 'TradeVolume']].to_dict('records')
                comparison['overlapping_stocks'] = overlap_stocks
            
            logger.info("漲停vs強勢股票比較分析完成")
            return comparison
            
        except Exception as e:
            logger.error(f"比較分析時發生錯誤: {e}")
            return {}
    
    def identify_potential_stocks(self) -> Dict:
        """
        識別具有潛力的股票
        
        Returns:
            Dict: 潛力股票分析結果
        """
        try:
            all_stocks_df = pd.DataFrame(self.data.get('all_stocks', []))
            
            if all_stocks_df.empty:
                return {}
            
            # 篩選條件
            potential_criteria = {
                'volume_active': all_stocks_df['TradeVolume'] > all_stocks_df['TradeVolume'].quantile(0.7),
                'price_momentum': (all_stocks_df['ChangePercent'] >= 2) & (all_stocks_df['ChangePercent'] < 9.5),
                'small_cap': all_stocks_df['MarketValue'] <= 10000000000,  # 100億以下
                'high_transactions': all_stocks_df['Transaction'] > all_stocks_df['Transaction'].median()
            }
            
            # 組合篩選
            potential_stocks = all_stocks_df[
                potential_criteria['volume_active'] & 
                potential_criteria['price_momentum'] & 
                potential_criteria['small_cap']
            ].copy()
            
            # 計算潛力評分
            if not potential_stocks.empty:
                potential_stocks['PotentialScore'] = (
                    potential_stocks['ChangePercent'] * 0.3 +
                    (potential_stocks['TradeVolume'] / 1000000) * 0.3 +
                    (potential_stocks['Transaction'] / 1000) * 0.2 +
                    (10000000000 / potential_stocks['MarketValue']) * 0.2  # 市值越小分數越高
                )
                
                potential_stocks = potential_stocks.sort_values('PotentialScore', ascending=False)
            
            analysis = {
                'total_potential_stocks': len(potential_stocks),
                'selection_criteria': {
                    'volume_threshold': f"成交量 > {all_stocks_df['TradeVolume'].quantile(0.7):.0f}",
                    'change_range': "漲幅 2% - 9.5%",
                    'market_cap_limit': "市值 < 100億",
                    'transaction_threshold': f"成交筆數 > {all_stocks_df['Transaction'].median():.0f}"
                },
                'top_potential_stocks': potential_stocks.head(20)[['Code', 'Name', 'ChangePercent', 'TradeVolume', 'MarketValue', 'PotentialScore']].to_dict('records') if not potential_stocks.empty else [],
                'statistics': {
                    'avg_change': potential_stocks['ChangePercent'].mean() if not potential_stocks.empty else 0,
                    'avg_volume': potential_stocks['TradeVolume'].mean() if not potential_stocks.empty else 0,
                    'avg_market_value': potential_stocks['MarketValue'].mean() if not potential_stocks.empty else 0,
                    'avg_score': potential_stocks['PotentialScore'].mean() if not potential_stocks.empty else 0
                }
            }
            
            logger.info(f"識別出 {len(potential_stocks)} 檔潛力股票")
            return analysis
            
        except Exception as e:
            logger.error(f"識別潛力股票時發生錯誤: {e}")
            return {}
    
    def create_visualizations(self) -> List[str]:
        """
        創建數據可視化圖表
        
        Returns:
            List[str]: 生成的圖表文件路徑列表
        """
        chart_files = []
        
        try:
            # 1. 漲停股票分布圖
            if self.data.get('small_cap_limit_up'):
                limit_up_df = pd.DataFrame(self.data['small_cap_limit_up'])
                
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
                fig.suptitle('小型股漲停股票分析', fontsize=16, fontweight='bold')
                
                # 漲幅分布
                ax1.hist(limit_up_df['ChangePercent'], bins=10, alpha=0.7, color='red', edgecolor='black')
                ax1.set_title('漲幅分布')
                ax1.set_xlabel('漲幅 (%)')
                ax1.set_ylabel('股票數量')
                
                # 成交量分布
                ax2.hist(limit_up_df['TradeVolume']/1000000, bins=10, alpha=0.7, color='blue', edgecolor='black')
                ax2.set_title('成交量分布')
                ax2.set_xlabel('成交量 (百萬股)')
                ax2.set_ylabel('股票數量')
                
                # 股價分布
                ax3.hist(limit_up_df['ClosingPrice'], bins=10, alpha=0.7, color='green', edgecolor='black')
                ax3.set_title('收盤價分布')
                ax3.set_xlabel('收盤價 (元)')
                ax3.set_ylabel('股票數量')
                
                # 市值分布
                ax4.hist(limit_up_df['MarketValue']/1000000000, bins=10, alpha=0.7, color='orange', edgecolor='black')
                ax4.set_title('市值分布')
                ax4.set_xlabel('市值 (十億元)')
                ax4.set_ylabel('股票數量')
                
                plt.tight_layout()
                chart_file = 'limit_up_analysis.png'
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)
                logger.info(f"漲停股票分析圖表已保存: {chart_file}")
            
            # 2. 強勢股票vs漲停股票比較
            if self.data.get('small_cap_strong') and self.data.get('small_cap_limit_up'):
                strong_df = pd.DataFrame(self.data['small_cap_strong'])
                limit_up_df = pd.DataFrame(self.data['small_cap_limit_up'])
                
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                fig.suptitle('強勢股票 vs 漲停股票比較', fontsize=16, fontweight='bold')
                
                # 漲幅比較
                ax1.boxplot([strong_df['ChangePercent'], limit_up_df['ChangePercent']], 
                           labels=['強勢股票', '漲停股票'])
                ax1.set_title('漲幅比較')
                ax1.set_ylabel('漲幅 (%)')
                
                # 成交量比較
                ax2.boxplot([strong_df['TradeVolume']/1000000, limit_up_df['TradeVolume']/1000000], 
                           labels=['強勢股票', '漲停股票'])
                ax2.set_title('成交量比較')
                ax2.set_ylabel('成交量 (百萬股)')
                
                plt.tight_layout()
                chart_file = 'strong_vs_limit_up_comparison.png'
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)
                logger.info(f"比較分析圖表已保存: {chart_file}")
            
            # 3. 市場整體分析
            if self.data.get('market_analysis'):
                market_data = self.data['market_analysis']
                sentiment = market_data.get('market_sentiment', {})
                
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                fig.suptitle('市場整體分析', fontsize=16, fontweight='bold')
                
                # 市場情緒餅圖
                labels = ['上漲', '下跌', '平盤']
                sizes = [sentiment.get('rising_stocks', 0), 
                        sentiment.get('falling_stocks', 0), 
                        sentiment.get('flat_stocks', 0)]
                colors = ['green', 'red', 'gray']
                
                ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                ax1.set_title('市場情緒分布')
                
                # 成交量前10股票
                if self.data.get('all_stocks'):
                    all_stocks_df = pd.DataFrame(self.data['all_stocks'])
                    top_volume = all_stocks_df.nlargest(10, 'TradeVolume')
                    
                    ax2.barh(range(len(top_volume)), top_volume['TradeVolume']/1000000)
                    ax2.set_yticks(range(len(top_volume)))
                    ax2.set_yticklabels([f"{row['Name']}({row['Code']})" for _, row in top_volume.iterrows()])
                    ax2.set_xlabel('成交量 (百萬股)')
                    ax2.set_title('成交量前10名股票')
                
                plt.tight_layout()
                chart_file = 'market_overview.png'
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)
                logger.info(f"市場概覽圖表已保存: {chart_file}")
            
            return chart_files
            
        except Exception as e:
            logger.error(f"創建可視化圖表時發生錯誤: {e}")
            return chart_files
    
    def generate_comprehensive_analysis(self) -> Dict:
        """
        生成綜合分析報告
        
        Returns:
            Dict: 綜合分析結果
        """
        logger.info("開始生成綜合分析報告...")
        
        analysis_result = {
            'timestamp': datetime.now().isoformat(),
            'data_source': self.data_file,
            'limit_up_analysis': self.analyze_limit_up_stocks(),
            'strong_stocks_analysis': self.analyze_strong_stocks(),
            'comparison_analysis': self.compare_limit_up_vs_strong(),
            'potential_stocks_analysis': self.identify_potential_stocks(),
            'market_summary': self.data.get('market_analysis', {}),
            'visualization_files': self.create_visualizations()
        }
        
        logger.info("綜合分析報告生成完成")
        return analysis_result

def main():
    """主函數"""
    import sys
    import glob
    
    # 優先使用命令行傳入的數據文件，否則在 STOCK_DATA_DIR 中尋找
    data_file = None
    if len(sys.argv) > 1:
        # 命令行傳入的數據文件路徑
        data_file = sys.argv[1]
        if os.path.exists(data_file):
            logger.info(f"使用命令行參數指定的數據文件: {data_file}")
        else:
            logger.warning(f"命令行指定的文件不存在: {data_file}，將在 STOCK_DATA_DIR 尋找")
            data_file = None
    
    # 若無命令行參數或文件不存在，在 STOCK_DATA_DIR 尋找
    if not data_file:
        data_files = glob.glob(os.path.join(STOCK_DATA_DIR, "latest_stock_data_*.json"))
        
        if not data_files:
            logger.error("找不到股票數據文件")
            return
        
        data_file = max(data_files)
    
    logger.info(f"使用數據文件: {data_file}")
    
    # 創建分析器
    analyzer = StockAnalyzer(data_file)
    
    # 生成綜合分析
    analysis = analyzer.generate_comprehensive_analysis()
    
    # 保存分析結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    analysis_file = f"stock_analysis_report_{timestamp}.json"
    analysis_filepath = os.path.join(TECHNICAL_ANALYSIS_DIR, analysis_file)
    
    with open(analysis_filepath, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, ensure_ascii=False, indent=2)
    
    logger.info(f"分析報告已保存: {analysis_filepath}")
    
    # 顯示摘要
    print("\n=== 股票分析報告摘要 ===")
    
    if analysis.get('limit_up_analysis'):
        limit_stats = analysis['limit_up_analysis'].get('basic_stats', {})
        print(f"漲停股票數量: {limit_stats.get('total_count', 0)}")
        print(f"平均漲幅: {limit_stats.get('avg_change_percent', 0):.2f}%")
        print(f"平均成交量: {limit_stats.get('avg_volume', 0):,.0f}")
    
    if analysis.get('strong_stocks_analysis'):
        strong_stats = analysis['strong_stocks_analysis'].get('basic_stats', {})
        print(f"強勢股票數量: {strong_stats.get('total_count', 0)}")
        print(f"平均漲幅: {strong_stats.get('avg_change_percent', 0):.2f}%")
    
    if analysis.get('potential_stocks_analysis'):
        potential_stats = analysis['potential_stocks_analysis']
        print(f"潛力股票數量: {potential_stats.get('total_potential_stocks', 0)}")
    
    if analysis.get('visualization_files'):
        print(f"\n生成的圖表文件:")
        for chart_file in analysis['visualization_files']:
            print(f"- {chart_file}")
    
    print(f"\n完整分析報告: {analysis_filepath}")

if __name__ == "__main__":
    main()

