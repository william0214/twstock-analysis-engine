#!/usr/bin/env python3
"""
API數據更新器
整合所有分析結果，生成latest_analysis.json文件供網站API使用
"""

import json
import os
import glob
from datetime import datetime
import logging
from typing import Dict, List
from config import STOCK_DATA_DIR, TECHNICAL_ANALYSIS_DIR, STATISTICS_DIR, MARKET_ANALYSIS_DIR

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIDataUpdater:
    """API數據更新器"""
    
    def __init__(self):
        """初始化更新器"""
        self.stock_data = self.load_latest_stock_data()
        self.technical_data = self.load_latest_technical_data()
        self.statistics_data = self.load_latest_statistics_data()
        self.report_data = self.load_latest_report_data()
        # 確保 stock_data 中有 small_cap 欄位，否則根據 MarketValue 計算
        self._ensure_small_cap_fields()

    def _ensure_small_cap_fields(self, market_cap_threshold: float = 10000000000):
        try:
            if not self.stock_data:
                return
            if self.stock_data.get('small_cap_limit_up') and self.stock_data.get('small_cap_strong'):
                return

            limit_up = self.stock_data.get('limit_up_stocks', [])
            strong = self.stock_data.get('strong_stocks', [])

            def filter_small(items):
                res = []
                for s in items:
                    mv = s.get('MarketValue')
                    if mv is None:
                        tv = s.get('TradeVolume') or 0
                        cp = s.get('ClosingPrice') or 0
                        try:
                            mv = float(tv) * float(cp)
                        except Exception:
                            mv = 0
                    try:
                        if float(mv) <= market_cap_threshold:
                            res.append(s)
                    except Exception:
                        continue
                return res

            self.stock_data['small_cap_limit_up'] = filter_small(limit_up)
            self.stock_data['small_cap_strong'] = filter_small(strong)
            logger.info(f"API updater 自動產生 small_cap fields: {len(self.stock_data['small_cap_limit_up'])} 漲停 / {len(self.stock_data['small_cap_strong'])} 強勢")
        except Exception as e:
            logger.error(f"API updater 確保 small_cap 欄位時發生錯誤: {e}")
        
    def load_latest_stock_data(self) -> Dict:
        """載入最新股票數據"""
        try:
            data_files = glob.glob(os.path.join(STOCK_DATA_DIR, "latest_stock_data_*.json"))
            if not data_files:
                logger.error("找不到股票數據文件")
                return {}
            
            latest_file = max(data_files)
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"載入股票數據: {latest_file}")
            return data
        except Exception as e:
            logger.error(f"載入股票數據失敗: {e}")
            return {}
    
    def load_latest_technical_data(self) -> Dict:
        """載入最新技術分析數據"""
        try:
            technical_files = glob.glob(os.path.join(TECHNICAL_ANALYSIS_DIR, "technical_analysis_report_*.json"))
            if not technical_files:
                logger.warning("找不到技術分析報告文件")
                return {}
            
            latest_file = max(technical_files)
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"載入技術分析數據: {latest_file}")
            return data
        except Exception as e:
            logger.error(f"載入技術分析數據失敗: {e}")
            return {}
    
    def load_latest_statistics_data(self) -> Dict:
        """載入最新統計數據"""
        try:
            stats_files = glob.glob(os.path.join(STATISTICS_DIR, "statistics_report_*.json"))
            if not stats_files:
                logger.warning("找不到統計報告文件")
                return {}
            
            latest_file = max(stats_files)
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"載入統計數據: {latest_file}")
            return data
        except Exception as e:
            logger.error(f"載入統計數據失敗: {e}")
            return {}
    
    def load_latest_report_data(self) -> str:
        """載入最新市場分析報告"""
        try:
            report_files = glob.glob(os.path.join(MARKET_ANALYSIS_DIR, "market_analysis_report_*.md"))
            if not report_files:
                logger.warning("找不到市場分析報告文件")
                return ""
            
            latest_file = max(report_files)
            with open(latest_file, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"載入市場分析報告: {latest_file}")
            return content
        except Exception as e:
            logger.error(f"載入市場分析報告失敗: {e}")
            return ""
    
    def create_api_data(self) -> Dict:
        """創建API數據結構"""
        logger.info("開始創建API數據結構...")
        
        api_data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "data_date": datetime.now().strftime("%Y-%m-%d"),
                "analysis_time": datetime.now().strftime("%H:%M:%S"),
                "version": "1.0",
                "source": "台股小型股漲停潛力分析系統"
            },
            "market_overview": self.create_market_overview(),
            "limit_up_stocks": self.create_limit_up_stocks_data(),
            "strong_stocks": self.create_strong_stocks_data(),
            "recommendations": self.create_recommendations_data(),
            "statistics": self.create_statistics_summary(),
            "technical_analysis": self.create_technical_summary(),
            "market_report": self.report_data,
            "charts": self.get_chart_files()
        }
        
        logger.info("API數據結構創建完成")
        return api_data
    
    def create_market_overview(self) -> Dict:
        """創建市場概覽"""
        try:
            overview = {}
            
            if self.stock_data.get('statistics'):
                stats = self.stock_data['statistics']
                # 優先使用 all_stocks 長度計算 total_stocks，若無則使用 statistics 或 0
                total_stocks = len(self.stock_data.get('all_stocks', [])) or stats.get('total_stocks', 0)
                overview.update({
                    "total_stocks": total_stocks,
                    "limit_up_count": stats.get('limit_up_count', 0),
                    "strong_stocks_count": stats.get('strong_stocks_count', 0),
                    "small_cap_limit_up_count": stats.get('small_cap_limit_up_count', 0),
                    "small_cap_strong_count": stats.get('small_cap_strong_count', 0)
                })
            
            if self.stock_data.get('market_analysis', {}).get('market_sentiment'):
                sentiment = self.stock_data['market_analysis']['market_sentiment']
                overview.update({
                    "market_sentiment": {
                        "rising_ratio": sentiment.get('rising_ratio', 0),
                        "falling_ratio": sentiment.get('falling_ratio', 0),
                        "flat_ratio": sentiment.get('flat_ratio', 0),
                        "direction": "up" if sentiment.get('rising_ratio', 0) > sentiment.get('falling_ratio', 0) else "down"
                    }
                })
            
            if self.statistics_data.get('summary', {}).get('market_summary'):
                market_summary = self.statistics_data['summary']['market_summary']
                overview.update({
                    "trading_volume": {
                        "total_volume_billion": market_summary.get('total_volume_billion', 0),
                        "total_value_billion": market_summary.get('total_value_billion', 0),
                        "avg_change_percent": market_summary.get('avg_change', 0)
                    }
                })
            
            return overview
            
        except Exception as e:
            logger.error(f"創建市場概覽時發生錯誤: {e}")
            return {}
    
    def create_limit_up_stocks_data(self) -> List[Dict]:
        """創建漲停股票數據"""
        try:
            limit_up_data = []
            
            if self.stock_data.get('small_cap_limit_up'):
                for stock in self.stock_data['small_cap_limit_up']:
                    # 尋找對應的技術分析數據
                    technical_info = self.find_technical_analysis(stock['Code'])
                    
                    stock_data = {
                        "code": stock['Code'],
                        "name": stock['Name'],
                        "closing_price": stock['ClosingPrice'],
                        "change_percent": stock['ChangePercent'],
                        "volume": stock['TradeVolume'],
                        "value": stock['TradeValue'],
                        "market_value": stock['MarketValue'],
                        "transactions": stock.get('Transaction', 0)
                    }
                    
                    # 添加技術分析結果
                    if technical_info:
                        stock_data.update({
                            "technical_score": technical_info['rating']['technical_score'],
                            "chip_score": technical_info['rating']['chip_score'],
                            "total_score": technical_info['rating']['total_score'],
                            "rating": technical_info['rating']['rating'],
                            "recommendation": technical_info['rating']['recommendation'],
                            "risk_level": technical_info['rating']['risk_level'],
                            "key_strengths": technical_info['rating'].get('key_strengths', []),
                            "key_risks": technical_info['rating'].get('key_risks', [])
                        })
                    
                    limit_up_data.append(stock_data)
            
            # 按評分排序
            limit_up_data.sort(key=lambda x: x.get('total_score', 0), reverse=True)
            
            return limit_up_data
            
        except Exception as e:
            logger.error(f"創建漲停股票數據時發生錯誤: {e}")
            return []
    
    def create_strong_stocks_data(self) -> List[Dict]:
        """創建強勢股票數據"""
        try:
            strong_data = []
            
            if self.stock_data.get('small_cap_strong'):
                for stock in self.stock_data['small_cap_strong'][:20]:  # 取前20名
                    # 尋找對應的技術分析數據
                    technical_info = self.find_technical_analysis(stock['Code'])
                    
                    stock_data = {
                        "code": stock['Code'],
                        "name": stock['Name'],
                        "closing_price": stock['ClosingPrice'],
                        "change_percent": stock['ChangePercent'],
                        "volume": stock['TradeVolume'],
                        "value": stock['TradeValue'],
                        "market_value": stock['MarketValue'],
                        "score": stock.get('Score', 0),
                        "transactions": stock.get('Transaction', 0)
                    }
                    
                    # 添加技術分析結果
                    if technical_info:
                        stock_data.update({
                            "technical_score": technical_info['rating']['technical_score'],
                            "chip_score": technical_info['rating']['chip_score'],
                            "total_score": technical_info['rating']['total_score'],
                            "rating": technical_info['rating']['rating'],
                            "recommendation": technical_info['rating']['recommendation'],
                            "risk_level": technical_info['rating']['risk_level'],
                            "key_strengths": technical_info['rating'].get('key_strengths', []),
                            "key_risks": technical_info['rating'].get('key_risks', [])
                        })
                    
                    strong_data.append(stock_data)
            
            # 按評分排序
            strong_data.sort(key=lambda x: x.get('total_score', 0), reverse=True)
            
            return strong_data
            
        except Exception as e:
            logger.error(f"創建強勢股票數據時發生錯誤: {e}")
            return []
    
    def create_recommendations_data(self) -> List[Dict]:
        """創建推薦股票數據"""
        try:
            if self.statistics_data.get('final_recommendations'):
                recommendations = self.statistics_data['final_recommendations']
                
                # 簡化推薦數據結構
                simplified_recommendations = []
                for rec in recommendations:
                    simplified_rec = {
                        "rank": rec['rank'],
                        "code": rec['code'],
                        "name": rec['name'],
                        "closing_price": rec['closing_price'],
                        "change_percent": rec['change_percent'],
                        "volume": rec['volume'],
                        "market_value": rec['market_value'],
                        "total_score": rec['total_score'],
                        "rating": rec['rating'],
                        "recommendation": rec['recommendation'],
                        "risk_level": rec['risk_level'],
                        "potential_assessment": rec['potential_assessment'],
                        "recommendation_score": rec['recommendation_score'],
                        "key_strengths": rec['key_strengths'],
                        "key_risks": rec['key_risks'],
                        "momentum_score": rec['momentum_score'],
                        "liquidity_score": rec['liquidity_score']
                    }
                    simplified_recommendations.append(simplified_rec)
                
                return simplified_recommendations
            
            return []
            
        except Exception as e:
            logger.error(f"創建推薦股票數據時發生錯誤: {e}")
            return []
    
    def create_statistics_summary(self) -> Dict:
        """創建統計摘要"""
        try:
            summary = {}
            
            if self.statistics_data.get('summary'):
                stats_summary = self.statistics_data['summary']
                
                # 市場統計
                if stats_summary.get('market_summary'):
                    summary['market'] = stats_summary['market_summary']
                
                # 推薦統計
                if stats_summary.get('recommendation_summary'):
                    summary['recommendations'] = stats_summary['recommendation_summary']
                
                # 績效統計
                if stats_summary.get('performance_summary'):
                    summary['performance'] = stats_summary['performance_summary']
            
            # 添加技術分析統計
            if self.technical_data.get('summary_statistics'):
                tech_stats = self.technical_data['summary_statistics']
                summary['technical'] = {
                    "rating_distribution": tech_stats.get('rating_distribution', {}),
                    "risk_distribution": tech_stats.get('risk_distribution', {}),
                    "limit_up_summary": tech_stats.get('limit_up_summary', {}),
                    "strong_stocks_summary": tech_stats.get('strong_stocks_summary', {})
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"創建統計摘要時發生錯誤: {e}")
            return {}
    
    def create_technical_summary(self) -> Dict:
        """創建技術分析摘要"""
        try:
            technical_summary = {
                "analysis_timestamp": self.technical_data.get('timestamp', ''),
                "total_analyzed": 0,
                "avg_scores": {},
                "rating_distribution": {},
                "risk_distribution": {}
            }
            
            if self.technical_data.get('summary_statistics'):
                stats = self.technical_data['summary_statistics']
                
                # 評級分布
                if stats.get('rating_distribution'):
                    technical_summary['rating_distribution'] = stats['rating_distribution']
                    technical_summary['total_analyzed'] = sum(stats['rating_distribution'].values())
                
                # 風險分布
                if stats.get('risk_distribution'):
                    technical_summary['risk_distribution'] = stats['risk_distribution']
                
                # 平均分數
                if stats.get('limit_up_summary'):
                    technical_summary['avg_scores']['limit_up'] = stats['limit_up_summary'].get('avg_score', 0)
                
                if stats.get('strong_stocks_summary'):
                    technical_summary['avg_scores']['strong_stocks'] = stats['strong_stocks_summary'].get('avg_score', 0)
            
            return technical_summary
            
        except Exception as e:
            logger.error(f"創建技術分析摘要時發生錯誤: {e}")
            return {}
    
    def find_technical_analysis(self, stock_code: str) -> Dict:
        """尋找股票的技術分析數據"""
        try:
            # 在漲停股票分析中尋找
            if self.technical_data.get('limit_up_analysis'):
                for analysis in self.technical_data['limit_up_analysis']:
                    if analysis['stock_info']['Code'] == stock_code:
                        return analysis
            
            # 在強勢股票分析中尋找
            if self.technical_data.get('strong_stocks_analysis'):
                for analysis in self.technical_data['strong_stocks_analysis']:
                    if analysis['stock_info']['Code'] == stock_code:
                        return analysis
            
            return {}
            
        except Exception as e:
            logger.error(f"尋找技術分析數據時發生錯誤: {e}")
            return {}
    
    def get_chart_files(self) -> List[str]:
        """獲取圖表文件列表"""
        try:
            chart_files = []
            
            # 收集所有PNG圖表文件
            png_files = glob.glob("*.png")
            for file in png_files:
                if any(keyword in file for keyword in ['analysis', 'comparison', 'overview', 'statistics', 'recommendation']):
                    chart_files.append(file)
            
            return chart_files
            
        except Exception as e:
            logger.error(f"獲取圖表文件時發生錯誤: {e}")
            return []
    
    def save_api_data(self, filename: str = "latest_analysis.json") -> bool:
        """保存API數據到文件"""
        try:
            api_data = self.create_api_data()
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(api_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"API數據已保存到: {filename}")
            
            # 顯示數據摘要
            self.display_data_summary(api_data)
            
            return True
            
        except Exception as e:
            logger.error(f"保存API數據時發生錯誤: {e}")
            return False
    
    def display_data_summary(self, api_data: Dict):
        """顯示數據摘要"""
        try:
            print("\n=== API數據摘要 ===")
            
            # 元數據
            metadata = api_data.get('metadata', {})
            print(f"最後更新: {metadata.get('last_updated', 'N/A')}")
            print(f"數據日期: {metadata.get('data_date', 'N/A')}")
            
            # 市場概覽
            overview = api_data.get('market_overview', {})
            print(f"\n市場概覽:")
            print(f"  總股票數: {overview.get('total_stocks', 0)}")
            print(f"  漲停股票: {overview.get('limit_up_count', 0)}")
            print(f"  小型股漲停: {overview.get('small_cap_limit_up_count', 0)}")
            print(f"  小型股強勢: {overview.get('small_cap_strong_count', 0)}")
            
            # 推薦數據
            recommendations = api_data.get('recommendations', [])
            print(f"\n推薦股票: {len(recommendations)} 檔")
            if recommendations:
                top_3 = recommendations[:3]
                for i, rec in enumerate(top_3, 1):
                    print(f"  {i}. {rec['name']} ({rec['code']}) - 評級: {rec['rating']} ({rec['total_score']:.1f}分)")
            
            # 圖表文件
            charts = api_data.get('charts', [])
            print(f"\n圖表文件: {len(charts)} 個")
            for chart in charts:
                print(f"  - {chart}")
            
        except Exception as e:
            logger.error(f"顯示數據摘要時發生錯誤: {e}")

def main():
    """主函數"""
    logger.info("開始更新API數據...")
    
    # 創建API數據更新器
    updater = APIDataUpdater()
    
    # 保存API數據
    success = updater.save_api_data("latest_analysis.json")
    
    if success:
        print("\n=== API數據更新完成 ===")
        print("文件: latest_analysis.json")
        print("網站API現在可以讀取最新的分析數據")
    else:
        print("\n=== API數據更新失敗 ===")
        print("請檢查錯誤日誌")
    
    return success

if __name__ == "__main__":
    main()

