#!/usr/bin/env python3
"""
統計數據和推薦評分計算器
計算各種統計指標，生成最終的推薦評分和排序
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Dict, List, Tuple
import glob
import matplotlib.pyplot as plt
import seaborn as sns
from config import STOCK_DATA_DIR, TECHNICAL_ANALYSIS_DIR, STATISTICS_DIR

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StatisticsCalculator:
    """統計數據和推薦評分計算器"""
    
    def __init__(self):
        """初始化計算器"""
        self.stock_data = self.load_latest_stock_data()
        self.technical_data = self.load_latest_technical_data()
        
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
    
    def calculate_market_statistics(self) -> Dict:
        """計算市場統計數據"""
        try:
            stats = {}
            
            if self.stock_data.get('all_stocks'):
                all_stocks_df = pd.DataFrame(self.stock_data['all_stocks'])
                
                # 基本統計
                stats['basic_statistics'] = {
                    'total_stocks': len(all_stocks_df),
                    'trading_stocks': len(all_stocks_df[all_stocks_df['TradeVolume'] > 0]),
                    'avg_change_percent': all_stocks_df['ChangePercent'].mean(),
                    'median_change_percent': all_stocks_df['ChangePercent'].median(),
                    'std_change_percent': all_stocks_df['ChangePercent'].std(),
                    'total_volume': all_stocks_df['TradeVolume'].sum(),
                    'total_value': all_stocks_df['TradeValue'].sum(),
                    'avg_volume': all_stocks_df['TradeVolume'].mean(),
                    'median_volume': all_stocks_df['TradeVolume'].median()
                }
                
                # 漲跌分布
                stats['change_distribution'] = {
                    'limit_up_count': len(all_stocks_df[all_stocks_df['ChangePercent'] >= 9.5]),
                    'strong_up_count': len(all_stocks_df[(all_stocks_df['ChangePercent'] >= 5) & (all_stocks_df['ChangePercent'] < 9.5)]),
                    'moderate_up_count': len(all_stocks_df[(all_stocks_df['ChangePercent'] >= 2) & (all_stocks_df['ChangePercent'] < 5)]),
                    'mild_up_count': len(all_stocks_df[(all_stocks_df['ChangePercent'] > 0) & (all_stocks_df['ChangePercent'] < 2)]),
                    'flat_count': len(all_stocks_df[all_stocks_df['ChangePercent'] == 0]),
                    'mild_down_count': len(all_stocks_df[(all_stocks_df['ChangePercent'] < 0) & (all_stocks_df['ChangePercent'] > -2)]),
                    'moderate_down_count': len(all_stocks_df[(all_stocks_df['ChangePercent'] <= -2) & (all_stocks_df['ChangePercent'] > -5)]),
                    'strong_down_count': len(all_stocks_df[(all_stocks_df['ChangePercent'] <= -5) & (all_stocks_df['ChangePercent'] > -9.5)]),
                    'limit_down_count': len(all_stocks_df[all_stocks_df['ChangePercent'] <= -9.5])
                }
                
                # 成交量分布
                volume_quantiles = all_stocks_df['TradeVolume'].quantile([0.25, 0.5, 0.75, 0.9, 0.95])
                stats['volume_distribution'] = {
                    'q25': volume_quantiles[0.25],
                    'q50': volume_quantiles[0.5],
                    'q75': volume_quantiles[0.75],
                    'q90': volume_quantiles[0.9],
                    'q95': volume_quantiles[0.95],
                    'high_volume_count': len(all_stocks_df[all_stocks_df['TradeVolume'] > volume_quantiles[0.9]]),
                    'low_volume_count': len(all_stocks_df[all_stocks_df['TradeVolume'] < volume_quantiles[0.25]])
                }
                
                # 價格分布
                price_ranges = {
                    'under_10': len(all_stocks_df[all_stocks_df['ClosingPrice'] < 10]),
                    'range_10_50': len(all_stocks_df[(all_stocks_df['ClosingPrice'] >= 10) & (all_stocks_df['ClosingPrice'] < 50)]),
                    'range_50_100': len(all_stocks_df[(all_stocks_df['ClosingPrice'] >= 50) & (all_stocks_df['ClosingPrice'] < 100)]),
                    'range_100_500': len(all_stocks_df[(all_stocks_df['ClosingPrice'] >= 100) & (all_stocks_df['ClosingPrice'] < 500)]),
                    'over_500': len(all_stocks_df[all_stocks_df['ClosingPrice'] >= 500])
                }
                stats['price_distribution'] = price_ranges
                
                # 市值分布（簡化計算）
                market_cap_ranges = {
                    'micro_cap': len(all_stocks_df[all_stocks_df['MarketValue'] < 1000000000]),  # 10億以下
                    'small_cap': len(all_stocks_df[(all_stocks_df['MarketValue'] >= 1000000000) & (all_stocks_df['MarketValue'] < 10000000000)]),  # 10-100億
                    'mid_cap': len(all_stocks_df[(all_stocks_df['MarketValue'] >= 10000000000) & (all_stocks_df['MarketValue'] < 50000000000)]),  # 100-500億
                    'large_cap': len(all_stocks_df[all_stocks_df['MarketValue'] >= 50000000000])  # 500億以上
                }
                stats['market_cap_distribution'] = market_cap_ranges
                
            logger.info("市場統計數據計算完成")
            return stats
            
        except Exception as e:
            logger.error(f"計算市場統計數據時發生錯誤: {e}")
            return {}
    
    def calculate_performance_metrics(self) -> Dict:
        """計算績效指標"""
        try:
            metrics = {}
            
            # 漲停股票績效
            if self.stock_data.get('small_cap_limit_up'):
                limit_up_df = pd.DataFrame(self.stock_data['small_cap_limit_up'])
                
                metrics['limit_up_performance'] = {
                    'count': len(limit_up_df),
                    'avg_change': limit_up_df['ChangePercent'].mean(),
                    'avg_volume': limit_up_df['TradeVolume'].mean(),
                    'avg_value': limit_up_df['TradeValue'].mean(),
                    'total_value': limit_up_df['TradeValue'].sum(),
                    'avg_market_cap': limit_up_df['MarketValue'].mean(),
                    'volume_efficiency': (limit_up_df['TradeValue'].sum() / limit_up_df['TradeVolume'].sum()) if limit_up_df['TradeVolume'].sum() > 0 else 0
                }
            
            # 強勢股票績效
            if self.stock_data.get('small_cap_strong'):
                strong_df = pd.DataFrame(self.stock_data['small_cap_strong'])
                
                metrics['strong_stocks_performance'] = {
                    'count': len(strong_df),
                    'avg_change': strong_df['ChangePercent'].mean(),
                    'avg_volume': strong_df['TradeVolume'].mean(),
                    'avg_value': strong_df['TradeValue'].mean(),
                    'total_value': strong_df['TradeValue'].sum(),
                    'avg_score': strong_df['Score'].mean() if 'Score' in strong_df.columns else 0,
                    'avg_market_cap': strong_df['MarketValue'].mean()
                }
            
            # 技術分析績效
            if self.technical_data.get('summary_statistics'):
                tech_stats = self.technical_data['summary_statistics']
                
                metrics['technical_performance'] = {
                    'limit_up_avg_score': tech_stats.get('limit_up_summary', {}).get('avg_score', 0),
                    'strong_avg_score': tech_stats.get('strong_stocks_summary', {}).get('avg_score', 0),
                    'high_grade_ratio': self.calculate_high_grade_ratio(tech_stats.get('rating_distribution', {})),
                    'low_risk_ratio': self.calculate_low_risk_ratio(tech_stats.get('risk_distribution', {}))
                }
            
            logger.info("績效指標計算完成")
            return metrics
            
        except Exception as e:
            logger.error(f"計算績效指標時發生錯誤: {e}")
            return {}
    
    def calculate_high_grade_ratio(self, rating_dist: Dict) -> float:
        """計算高評級比例"""
        try:
            total = sum(rating_dist.values())
            if total == 0:
                return 0
            
            high_grade_count = rating_dist.get('A+', 0) + rating_dist.get('A', 0)
            return (high_grade_count / total) * 100
        except:
            return 0
    
    def calculate_low_risk_ratio(self, risk_dist: Dict) -> float:
        """計算低風險比例"""
        try:
            total = sum(risk_dist.values())
            if total == 0:
                return 0
            
            low_risk_count = risk_dist.get('低風險', 0)
            return (low_risk_count / total) * 100
        except:
            return 0
    
    def generate_final_recommendations(self, top_n: int = 20) -> List[Dict]:
        """生成最終推薦股票列表"""
        try:
            all_analyzed_stocks = []
            
            # 收集所有分析過的股票
            if self.technical_data.get('limit_up_analysis'):
                all_analyzed_stocks.extend(self.technical_data['limit_up_analysis'])
            
            if self.technical_data.get('strong_stocks_analysis'):
                all_analyzed_stocks.extend(self.technical_data['strong_stocks_analysis'])
            
            # 去重並按評分排序
            seen_codes = set()
            unique_stocks = []
            
            for stock in all_analyzed_stocks:
                code = stock['stock_info']['Code']
                if code not in seen_codes:
                    seen_codes.add(code)
                    unique_stocks.append(stock)
            
            # 按總評分排序
            sorted_stocks = sorted(unique_stocks, key=lambda x: x['rating']['total_score'], reverse=True)
            
            # 過濾出 A 級以上的股票（A+ 和 A）
            high_grade_stocks = [
                stock for stock in sorted_stocks 
                if stock['rating']['rating'] in ['A+', 'A']
            ]
            
            # 如果沒有 A 級以上的股票，返回空列表
            if not high_grade_stocks:
                logger.warning("⚠️ 本次分析沒有 A 級以上的推薦股票")
                return []
            
            # 計算額外的推薦指標
            recommendations = []
            for i, stock in enumerate(high_grade_stocks[:top_n]):
                stock_info = stock['stock_info']
                rating = stock['rating']
                technical = stock['technical_indicators']
                chip = stock['chip_analysis']
                
                # 計算綜合推薦分數
                recommendation_score = self.calculate_recommendation_score(stock)
                
                # 計算潛力評估
                potential_assessment = self.assess_potential(stock)
                
                recommendation = {
                    'rank': i + 1,
                    'code': stock_info['Code'],
                    'name': stock_info['Name'],
                    'closing_price': stock_info['ClosingPrice'],
                    'change_percent': stock_info['ChangePercent'],
                    'volume': stock_info['TradeVolume'],
                    'market_value': stock_info['MarketValue'],
                    'technical_score': rating['technical_score'],
                    'chip_score': rating['chip_score'],
                    'total_score': rating['total_score'],
                    'rating': rating['rating'],
                    'recommendation': rating['recommendation'],
                    'risk_level': rating['risk_level'],
                    'recommendation_score': recommendation_score,
                    'potential_assessment': potential_assessment,
                    'key_strengths': rating.get('key_strengths', []),
                    'key_risks': rating.get('key_risks', []),
                    'momentum_score': technical.get('momentum_score', 0),
                    'liquidity_score': technical.get('liquidity_score', 0),
                    'investor_sentiment': chip.get('investor_behavior', {}).get('sentiment', ''),
                    'activity_level': chip.get('market_participation', {}).get('activity_level', '')
                }
                
                recommendations.append(recommendation)
            
            logger.info(f"生成 {len(recommendations)} 檔推薦股票")
            return recommendations
            
        except Exception as e:
            logger.error(f"生成最終推薦時發生錯誤: {e}")
            return []
    
    def calculate_recommendation_score(self, stock: Dict) -> float:
        """計算推薦分數"""
        try:
            stock_info = stock['stock_info']
            rating = stock['rating']
            technical = stock['technical_indicators']
            
            # 基礎分數（技術評分）
            base_score = rating['total_score']
            
            # 動能加分
            momentum_bonus = min(technical.get('momentum_score', 0) / 10 * 5, 5)
            
            # 流動性加分
            liquidity_bonus = min(technical.get('liquidity_score', 0) / 100 * 3, 3)
            
            # 漲幅適中加分（避免過度追高）
            change_percent = stock_info['ChangePercent']
            if 3 <= change_percent <= 7:
                change_bonus = 2
            elif 7 < change_percent <= 9.5:
                change_bonus = 1
            else:
                change_bonus = 0
            
            # 風險調整
            risk_level = rating['risk_level']
            if risk_level == '低風險':
                risk_adjustment = 1.1
            elif risk_level == '中風險':
                risk_adjustment = 1.0
            else:
                risk_adjustment = 0.9
            
            # 計算最終推薦分數
            final_score = (base_score + momentum_bonus + liquidity_bonus + change_bonus) * risk_adjustment
            
            return min(100, max(0, final_score))
            
        except Exception as e:
            logger.error(f"計算推薦分數時發生錯誤: {e}")
            return 0
    
    def assess_potential(self, stock: Dict) -> str:
        """評估股票潛力"""
        try:
            stock_info = stock['stock_info']
            rating = stock['rating']
            technical = stock['technical_indicators']
            
            # 評估因子
            score = rating['total_score']
            momentum = technical.get('momentum_score', 0)
            change_percent = stock_info['ChangePercent']
            volume = stock_info['TradeVolume']
            
            # 潛力評估邏輯
            if score >= 80 and momentum >= 8 and change_percent >= 5:
                return "極高潛力"
            elif score >= 70 and momentum >= 6 and change_percent >= 3:
                return "高潛力"
            elif score >= 60 and momentum >= 4:
                return "中等潛力"
            elif score >= 50:
                return "一般潛力"
            else:
                return "潛力有限"
                
        except Exception as e:
            logger.error(f"評估股票潛力時發生錯誤: {e}")
            return "未知"
    
    def create_statistics_visualization(self) -> List[str]:
        """創建統計數據可視化"""
        chart_files = []
        
        try:
            # 1. 市場統計概覽
            market_stats = self.calculate_market_statistics()
            
            if market_stats.get('change_distribution'):
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
                fig.suptitle('市場統計概覽', fontsize=16, fontweight='bold')
                
                # 漲跌分布
                change_dist = market_stats['change_distribution']
                categories = ['漲停', '強漲', '溫漲', '微漲', '平盤', '微跌', '溫跌', '強跌', '跌停']
                values = [
                    change_dist['limit_up_count'],
                    change_dist['strong_up_count'],
                    change_dist['moderate_up_count'],
                    change_dist['mild_up_count'],
                    change_dist['flat_count'],
                    change_dist['mild_down_count'],
                    change_dist['moderate_down_count'],
                    change_dist['strong_down_count'],
                    change_dist['limit_down_count']
                ]
                
                colors = ['red', 'orange', 'lightcoral', 'pink', 'gray', 'lightblue', 'blue', 'darkblue', 'darkred']
                ax1.bar(categories, values, color=colors)
                ax1.set_title('漲跌分布')
                ax1.set_ylabel('股票數量')
                ax1.tick_params(axis='x', rotation=45)
                
                # 價格分布
                if market_stats.get('price_distribution'):
                    price_dist = market_stats['price_distribution']
                    price_categories = ['<10元', '10-50元', '50-100元', '100-500元', '>500元']
                    price_values = [
                        price_dist['under_10'],
                        price_dist['range_10_50'],
                        price_dist['range_50_100'],
                        price_dist['range_100_500'],
                        price_dist['over_500']
                    ]
                    
                    ax2.pie(price_values, labels=price_categories, autopct='%1.1f%%', startangle=90)
                    ax2.set_title('價格分布')
                
                # 市值分布
                if market_stats.get('market_cap_distribution'):
                    cap_dist = market_stats['market_cap_distribution']
                    cap_categories = ['微型股', '小型股', '中型股', '大型股']
                    cap_values = [
                        cap_dist['micro_cap'],
                        cap_dist['small_cap'],
                        cap_dist['mid_cap'],
                        cap_dist['large_cap']
                    ]
                    
                    ax3.pie(cap_values, labels=cap_categories, autopct='%1.1f%%', startangle=90)
                    ax3.set_title('市值分布')
                
                # 成交量分布
                if self.stock_data.get('all_stocks'):
                    all_stocks_df = pd.DataFrame(self.stock_data['all_stocks'])
                    ax4.hist(all_stocks_df['TradeVolume']/1000000, bins=50, alpha=0.7, color='blue', edgecolor='black')
                    ax4.set_title('成交量分布')
                    ax4.set_xlabel('成交量 (百萬股)')
                    ax4.set_ylabel('股票數量')
                    ax4.set_xlim(0, 50)  # 限制x軸範圍以便觀察
                
                plt.tight_layout()
                chart_file = 'market_statistics_overview.png'
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)
                logger.info(f"市場統計概覽圖表已保存: {chart_file}")
            
            # 2. 推薦股票評分分布
            recommendations = self.generate_final_recommendations(20)
            
            if recommendations:
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
                fig.suptitle('推薦股票分析', fontsize=16, fontweight='bold')
                
                # 評分分布
                scores = [rec['total_score'] for rec in recommendations]
                ax1.hist(scores, bins=10, alpha=0.7, color='green', edgecolor='black')
                ax1.set_title('推薦股票評分分布')
                ax1.set_xlabel('評分')
                ax1.set_ylabel('股票數量')
                
                # 風險等級分布
                risk_levels = [rec['risk_level'] for rec in recommendations]
                risk_counts = {}
                for risk in risk_levels:
                    risk_counts[risk] = risk_counts.get(risk, 0) + 1
                
                ax2.pie(risk_counts.values(), labels=risk_counts.keys(), autopct='%1.1f%%', startangle=90)
                ax2.set_title('風險等級分布')
                
                plt.tight_layout()
                chart_file = 'recommendation_analysis.png'
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)
                logger.info(f"推薦股票分析圖表已保存: {chart_file}")
            
            return chart_files
            
        except Exception as e:
            logger.error(f"創建統計可視化時發生錯誤: {e}")
            return chart_files
    
    def generate_comprehensive_statistics(self) -> Dict:
        """生成綜合統計報告"""
        logger.info("開始生成綜合統計報告...")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'market_statistics': self.calculate_market_statistics(),
            'performance_metrics': self.calculate_performance_metrics(),
            'final_recommendations': self.generate_final_recommendations(20),
            'visualization_files': self.create_statistics_visualization()
        }
        
        # 計算摘要統計
        result['summary'] = self.calculate_summary_statistics(result)
        
        logger.info("綜合統計報告生成完成")
        return result
    
    def calculate_summary_statistics(self, data: Dict) -> Dict:
        """計算摘要統計"""
        try:
            summary = {}
            
            # 市場摘要
            if data.get('market_statistics', {}).get('basic_statistics'):
                basic = data['market_statistics']['basic_statistics']
                summary['market_summary'] = {
                    'total_stocks': basic['total_stocks'],
                    'trading_stocks': basic['trading_stocks'],
                    'market_direction': 'up' if basic['avg_change_percent'] > 0 else 'down' if basic['avg_change_percent'] < 0 else 'flat',
                    'avg_change': round(basic['avg_change_percent'], 2),
                    'total_volume_billion': round(basic['total_volume'] / 1000000000, 2),
                    'total_value_billion': round(basic['total_value'] / 100000000, 2)
                }
            
            # 推薦摘要
            if data.get('final_recommendations'):
                recommendations = data['final_recommendations']
                summary['recommendation_summary'] = {
                    'total_recommendations': len(recommendations),
                    'avg_score': round(np.mean([rec['total_score'] for rec in recommendations]), 2),
                    'high_potential_count': len([rec for rec in recommendations if rec['potential_assessment'] in ['極高潛力', '高潛力']]),
                    'low_risk_count': len([rec for rec in recommendations if rec['risk_level'] == '低風險']),
                    'top_recommendation': recommendations[0] if recommendations else None
                }
            
            # 績效摘要
            if data.get('performance_metrics'):
                perf = data['performance_metrics']
                summary['performance_summary'] = {
                    'limit_up_performance': perf.get('limit_up_performance', {}),
                    'strong_stocks_performance': perf.get('strong_stocks_performance', {}),
                    'technical_performance': perf.get('technical_performance', {})
                }
            
            return summary
            
        except Exception as e:
            logger.error(f"計算摘要統計時發生錯誤: {e}")
            return {}

def main():
    """主函數"""
    # 創建統計計算器
    calculator = StatisticsCalculator()
    
    # 生成綜合統計報告
    statistics_report = calculator.generate_comprehensive_statistics()
    
    # 保存統計報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stats_filename = f"statistics_report_{timestamp}.json"
    stats_filepath = os.path.join(STATISTICS_DIR, stats_filename)
    
    with open(stats_filepath, 'w', encoding='utf-8') as f:
        json.dump(statistics_report, f, ensure_ascii=False, indent=2)
    
    logger.info(f"統計報告已保存: {stats_filepath}")
    
    # 顯示摘要
    print("\n=== 統計數據和推薦評分計算完成 ===")
    print(f"統計報告文件: {stats_filepath}")
    
    if statistics_report.get('summary'):
        summary = statistics_report['summary']
        
        # 市場摘要
        if summary.get('market_summary'):
            market = summary['market_summary']
            print(f"\n=== 市場摘要 ===")
            print(f"總股票數: {market['total_stocks']}")
            print(f"交易股票數: {market['trading_stocks']}")
            print(f"市場方向: {market['market_direction']}")
            print(f"平均漲跌幅: {market['avg_change']}%")
            print(f"總成交量: {market['total_volume_billion']} 十億股")
            print(f"總成交值: {market['total_value_billion']} 億元")
        
        # 推薦摘要
        if summary.get('recommendation_summary'):
            rec = summary['recommendation_summary']
            print(f"\n=== 推薦摘要 ===")
            print(f"推薦股票數: {rec['total_recommendations']}")
            print(f"平均評分: {rec['avg_score']}")
            print(f"高潛力股票: {rec['high_potential_count']}")
            print(f"低風險股票: {rec['low_risk_count']}")
            
            if rec.get('top_recommendation'):
                top = rec['top_recommendation']
                print(f"首推股票: {top['name']} ({top['code']}) - 評分: {top['total_score']:.1f}")
    
    # 顯示前10名推薦
    if statistics_report.get('final_recommendations'):
        recommendations = statistics_report['final_recommendations']
        if recommendations:
            print(f"\n=== 前10名推薦股票 ===")
            for rec in recommendations[:10]:
                print(f"{rec['rank']}. {rec['name']} ({rec['code']}) - 評級: {rec['rating']} ({rec['total_score']:.1f}分) - 潛力: {rec['potential_assessment']}")
        else:
            print(f"\n=== 推薦結果 ===")
            print("⚠️ 本次分析沒有達到 A 級以上（A+ 或 A）的推薦股票")
            print("建議：觀望等待更好的投資機會")
    
    # 顯示生成的圖表
    if statistics_report.get('visualization_files'):
        print(f"\n=== 生成的圖表文件 ===")
        for chart_file in statistics_report['visualization_files']:
            print(f"- {chart_file}")
    
    return stats_filepath

if __name__ == "__main__":
    main()

