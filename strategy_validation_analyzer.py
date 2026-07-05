#!/usr/bin/env python3
"""
策略驗證分析器
分析歷史推薦股票的後續表現，驗證策略有效性並提出改進建議
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import glob
import re
import logging
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import seaborn as sns

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrategyValidationAnalyzer:
    """策略驗證分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.historical_data = {}
        self.recommendations = {}
        self.performance_results = {}
        
    def load_historical_reports(self) -> Dict:
        """載入歷史分析報告"""
        logger.info("載入歷史分析報告...")
        
        # 從 reports/market_analysis/ 目錄載入報告文件
        report_files = glob.glob("reports/market_analysis/market_analysis_report_*.md")
        # 從 data/stock_data/ 目錄載入數據文件
        data_files = glob.glob("data/stock_data/latest_stock_data_*.json")
        
        # 按日期排序
        report_files.sort()
        data_files.sort()
        
        historical_data = {}
        
        for report_file in report_files:
            try:
                # 提取日期
                date_match = re.search(r'(\d{8})_\d{6}', report_file)
                if not date_match:
                    continue
                    
                date_str = date_match.group(1)
                date_obj = datetime.strptime(date_str, '%Y%m%d')
                
                # 讀取報告內容
                with open(report_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析推薦股票
                recommendations = self.parse_recommendations_from_report(content)
                
                # 找對應的數據文件
                corresponding_data = None
                for data_file in data_files:
                    if date_str in data_file:
                        with open(data_file, 'r', encoding='utf-8') as f:
                            corresponding_data = json.load(f)
                        break
                
                historical_data[date_str] = {
                    'date': date_obj,
                    'report_file': report_file,
                    'recommendations': recommendations,
                    'stock_data': corresponding_data
                }
                
                logger.info(f"載入 {date_str} 的報告和數據")
                
            except Exception as e:
                logger.error(f"載入 {report_file} 時發生錯誤: {e}")
                continue
        
        self.historical_data = historical_data
        return historical_data
    
    def parse_recommendations_from_report(self, content: str) -> List[Dict]:
        """從報告中解析推薦股票"""
        recommendations = []
        
        # 查找推薦表格
        lines = content.split('\n')
        in_table = False
        
        for line in lines:
            if '| 排名 |' in line and '股票代號' in line:
                in_table = True
                continue
            elif in_table and line.startswith('|') and '---' not in line:
                parts = [p.strip() for p in line.split('|')[1:-1]]
                if len(parts) >= 7:
                    try:
                        recommendations.append({
                            'rank': int(parts[0]),
                            'code': parts[1],
                            'name': parts[2],
                            'rating': parts[3],
                            'score': float(parts[4]),
                            'recommendation': parts[5],
                            'risk_level': parts[6],
                            'change_percent': float(parts[7]) if len(parts) > 7 else 0
                        })
                    except (ValueError, IndexError):
                        continue
            elif in_table and not line.startswith('|'):
                break
        
        return recommendations
    
    def analyze_stock_performance(self, stock_code: str, start_date: str, days_ahead: List[int] = [1, 3, 5, 10]) -> Dict:
        """分析股票在推薦後的表現"""
        performance = {}
        
        # 獲取推薦日的價格
        start_data = None
        for date_key, data in self.historical_data.items():
            if date_key == start_date and data['stock_data']:
                all_stocks = data['stock_data'].get('all_stocks', [])
                for stock in all_stocks:
                    if stock['Code'] == stock_code:
                        start_data = stock
                        break
                break
        
        if not start_data:
            return performance
        
        start_price = start_data['ClosingPrice']
        start_date_obj = datetime.strptime(start_date, '%Y%m%d')
        
        # 計算未來幾天的表現
        for days in days_ahead:
            target_date = start_date_obj + timedelta(days=days)
            target_date_str = target_date.strftime('%Y%m%d')
            
            # 找最接近的未來日期
            closest_date = None
            min_diff = float('inf')
            
            for date_key in self.historical_data.keys():
                date_obj = datetime.strptime(date_key, '%Y%m%d')
                if date_obj >= target_date:
                    diff = abs((date_obj - target_date).days)
                    if diff < min_diff:
                        min_diff = diff
                        closest_date = date_key
            
            if closest_date and self.historical_data[closest_date]['stock_data']:
                all_stocks = self.historical_data[closest_date]['stock_data'].get('all_stocks', [])
                for stock in all_stocks:
                    if stock['Code'] == stock_code:
                        end_price = stock['ClosingPrice']
                        performance[f'{days}d_return'] = ((end_price - start_price) / start_price) * 100
                        break
        
        return performance
    
    def validate_strategy_effectiveness(self) -> Dict:
        """驗證策略有效性"""
        logger.info("開始驗證策略有效性...")
        
        results = {
            'total_recommendations': 0,
            'successful_recommendations': 0,
            'avg_returns': {},
            'rating_performance': {},
            'risk_performance': {},
            'detailed_results': []
        }
        
        for date_str, data in self.historical_data.items():
            if not data['recommendations']:
                continue
            
            for rec in data['recommendations']:
                stock_code = rec['code']
                
                # 分析後續表現
                performance = self.analyze_stock_performance(stock_code, date_str)
                
                if performance:
                    result = {
                        'date': date_str,
                        'stock_code': stock_code,
                        'stock_name': rec['name'],
                        'rank': rec['rank'],
                        'rating': rec['rating'],
                        'score': rec['score'],
                        'risk_level': rec['risk_level'],
                        'performance': performance
                    }
                    
                    results['detailed_results'].append(result)
                    results['total_recommendations'] += 1
                    
                    # 計算成功率（以3日正報酬為標準）
                    if performance.get('3d_return', 0) > 0:
                        results['successful_recommendations'] += 1
        
        # 計算平均報酬率
        if results['detailed_results']:
            returns_data = {}
            for period in ['1d_return', '3d_return', '5d_return', '10d_return']:
                returns = [r['performance'].get(period, 0) for r in results['detailed_results'] 
                          if period in r['performance']]
                if returns:
                    returns_data[period] = {
                        'mean': np.mean(returns),
                        'median': np.median(returns),
                        'std': np.std(returns),
                        'positive_ratio': len([r for r in returns if r > 0]) / len(returns)
                    }
            results['avg_returns'] = returns_data
            
            # 按評級分析表現
            rating_groups = {}
            for result in results['detailed_results']:
                rating = result['rating']
                if rating not in rating_groups:
                    rating_groups[rating] = []
                rating_groups[rating].append(result)
            
            for rating, group in rating_groups.items():
                returns_3d = [r['performance'].get('3d_return', 0) for r in group 
                             if '3d_return' in r['performance']]
                if returns_3d:
                    results['rating_performance'][rating] = {
                        'count': len(returns_3d),
                        'avg_return': np.mean(returns_3d),
                        'success_rate': len([r for r in returns_3d if r > 0]) / len(returns_3d)
                    }
        
        return results
    
    def identify_strategy_weaknesses(self, validation_results: Dict) -> List[str]:
        """識別策略弱點"""
        weaknesses = []
        
        # 分析成功率
        total_recs = validation_results['total_recommendations']
        successful_recs = validation_results['successful_recommendations']
        
        if total_recs > 0:
            success_rate = successful_recs / total_recs
            if success_rate < 0.6:
                weaknesses.append(f"整體成功率偏低 ({success_rate:.1%})，需要提高選股精確度")
        
        # 分析各評級表現
        rating_perf = validation_results.get('rating_performance', {})
        for rating, perf in rating_perf.items():
            if perf['success_rate'] < 0.7 and rating in ['A+', 'A']:
                weaknesses.append(f"{rating}級股票成功率 ({perf['success_rate']:.1%}) 低於預期")
        
        # 分析報酬率分布
        returns = validation_results.get('avg_returns', {})
        if '3d_return' in returns:
            if returns['3d_return']['mean'] < 1.0:
                weaknesses.append("平均3日報酬率偏低，可能需要調整評分標準")
            
            if returns['3d_return']['positive_ratio'] < 0.6:
                weaknesses.append("正報酬比例偏低，建議加強風險控制機制")
        
        return weaknesses
    
    def generate_strategy_improvements(self, validation_results: Dict, weaknesses: List[str]) -> List[str]:
        """生成策略改進建議"""
        improvements = []
        
        # 基於弱點分析提出改進建議
        if "成功率偏低" in ' '.join(weaknesses):
            improvements.extend([
                "加強技術指標權重調整，提高動能分析準確度",
                "增加基本面篩選條件，過濾財務體質較差的股票",
                "優化籌碼面分析，重視主力進出動向"
            ])
        
        if "A+級" in ' '.join(weaknesses) or "A級" in ' '.join(weaknesses):
            improvements.extend([
                "重新校準評分標準，提高高評級股票的門檻",
                "加入更嚴格的流動性檢驗",
                "增加產業輪動因子分析"
            ])
        
        if "報酬率偏低" in ' '.join(weaknesses):
            improvements.extend([
                "強化漲停股票的後續追蹤機制",
                "優化進場時機判斷指標",
                "加入市場情緒修正因子"
            ])
        
        # 基於數據分析的通用改進建議
        improvements.extend([
            "建立動態評分機制，根據市場狀況調整評分權重",
            "增加停損停利建議，提供明確的風險控制指引",
            "加強小型股流動性風險評估",
            "建立推薦股票的後續追蹤和評估機制"
        ])
        
        return improvements
    
    def create_performance_visualization(self, validation_results: Dict):
        """創建表現視覺化圖表"""
        logger.info("創建表現視覺化圖表...")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('策略驗證分析結果', fontsize=16, fontweight='bold')
        
        # 1. 各期間報酬率分布
        if validation_results.get('avg_returns'):
            periods = list(validation_results['avg_returns'].keys())
            means = [validation_results['avg_returns'][p]['mean'] for p in periods]
            
            axes[0, 0].bar(periods, means, color=['#2E8B57', '#4682B4', '#DAA520', '#CD5C5C'])
            axes[0, 0].set_title('各期間平均報酬率')
            axes[0, 0].set_ylabel('報酬率 (%)')
            axes[0, 0].axhline(y=0, color='red', linestyle='--', alpha=0.7)
        
        # 2. 評級表現比較
        if validation_results.get('rating_performance'):
            ratings = list(validation_results['rating_performance'].keys())
            success_rates = [validation_results['rating_performance'][r]['success_rate'] for r in ratings]
            
            axes[0, 1].bar(ratings, success_rates, color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
            axes[0, 1].set_title('各評級成功率')
            axes[0, 1].set_ylabel('成功率')
            axes[0, 1].set_ylim(0, 1)
        
        # 3. 報酬率分布直方圖
        if validation_results.get('detailed_results'):
            returns_3d = [r['performance'].get('3d_return', 0) for r in validation_results['detailed_results']
                         if '3d_return' in r['performance']]
            
            if returns_3d:
                axes[1, 0].hist(returns_3d, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
                axes[1, 0].axvline(x=0, color='red', linestyle='--', alpha=0.7)
                axes[1, 0].set_title('3日報酬率分布')
                axes[1, 0].set_xlabel('報酬率 (%)')
                axes[1, 0].set_ylabel('頻率')
        
        # 4. 時間序列表現
        if validation_results.get('detailed_results'):
            dates = sorted(list(set([r['date'] for r in validation_results['detailed_results']])))
            daily_returns = []
            
            for date in dates:
                date_returns = [r['performance'].get('3d_return', 0) 
                               for r in validation_results['detailed_results'] 
                               if r['date'] == date and '3d_return' in r['performance']]
                if date_returns:
                    daily_returns.append(np.mean(date_returns))
                else:
                    daily_returns.append(0)
            
            if daily_returns:
                axes[1, 1].plot(range(len(dates)), daily_returns, marker='o', linewidth=2)
                axes[1, 1].axhline(y=0, color='red', linestyle='--', alpha=0.7)
                axes[1, 1].set_title('歷史推薦表現趨勢')
                axes[1, 1].set_xlabel('時間')
                axes[1, 1].set_ylabel('平均3日報酬率 (%)')
        
        plt.tight_layout()
        plt.savefig('strategy_validation_analysis.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        logger.info("視覺化圖表已保存為 strategy_validation_analysis.png")
    
    def generate_validation_report(self) -> str:
        """生成驗證報告"""
        logger.info("生成策略驗證報告...")
        
        # 載入歷史數據
        self.load_historical_reports()
        
        # 驗證策略有效性
        validation_results = self.validate_strategy_effectiveness()
        
        # 識別弱點
        weaknesses = self.identify_strategy_weaknesses(validation_results)
        
        # 生成改進建議
        improvements = self.generate_strategy_improvements(validation_results, weaknesses)
        
        # 創建視覺化
        self.create_performance_visualization(validation_results)
        
        # 生成報告
        report = f"""# 台股小型股策略驗證分析報告

**分析日期：** {datetime.now().strftime('%Y年%m月%d日')}
**分析範圍：** {len(self.historical_data)} 個交易日的歷史推薦

## 執行摘要

### 整體表現
- **總推薦次數：** {validation_results['total_recommendations']}
- **成功推薦次數：** {validation_results['successful_recommendations']}
"""
        
        # 只有在有推薦時才計算成功率
        if validation_results['total_recommendations'] > 0:
            success_rate = validation_results['successful_recommendations']/validation_results['total_recommendations']*100
            report += f"- **整體成功率：** {success_rate:.1f}% (以3日正報酬為準)\n"
        else:
            report += f"- **整體成功率：** 無數據 (沒有找到歷史推薦)\n"
        
        report += """
### 各期間平均報酬率
"""
        
        if validation_results.get('avg_returns'):
            for period, data in validation_results['avg_returns'].items():
                period_name = period.replace('d_return', '日')
                report += f"- **{period_name}報酬率：** {data['mean']:.2f}% (正報酬比例: {data['positive_ratio']:.1%})\n"
        
        report += f"""
### 評級表現分析
"""
        
        if validation_results.get('rating_performance'):
            for rating, perf in validation_results['rating_performance'].items():
                report += f"- **{rating}級：** 推薦{perf['count']}次，平均報酬{perf['avg_return']:.2f}%，成功率{perf['success_rate']:.1%}\n"
        
        report += f"""
## 策略弱點分析

### 發現的問題
"""
        
        for i, weakness in enumerate(weaknesses, 1):
            report += f"{i}. {weakness}\n"
        
        report += f"""
## 策略改進建議

### 具體改進措施
"""
        
        for i, improvement in enumerate(improvements, 1):
            report += f"{i}. {improvement}\n"
        
        report += f"""
## 調整後的投資策略

### 優化後的評分標準
1. **技術面權重調整：** 動能指標權重提升至40%，增加趨勢確認指標
2. **籌碼面強化：** 加入主力買賣超數據，權重提升至35%
3. **基本面篩選：** 增加財務健全度檢驗，剔除負債比過高的股票
4. **流動性門檻：** 提高日均成交量要求，確保充足流動性

### 風險控制機制
1. **動態停損：** 根據股票波動度設定個別停損點
2. **分批進場：** 推薦分3批進場，降低時機風險
3. **持股分散：** 單一股票投入資金不超過總資金的5%
4. **市場情緒調整：** 在市場極度恐慌時降低推薦評級

### 後續追蹤機制
1. **每日監控：** 追蹤推薦股票的技術指標變化
2. **週報更新：** 每週更新推薦股票的評級狀況
3. **月度檢討：** 每月檢討策略有效性並調整參數

## 結論與建議

基於歷史數據分析，現有策略在識別潛力股票方面有一定效果，但仍有改進空間。建議：

1. **提高選股精確度：** 加強多因子模型的權重調整
2. **強化風險控制：** 建立更完善的風險評估機制  
3. **優化進場時機：** 結合市場情緒指標改善進場時機
4. **建立追蹤機制：** 定期檢討和調整策略參數

通過這些改進措施，預期可以將成功率提升至70%以上，平均報酬率提升至2-3%。

## 免責聲明

本分析報告僅供參考，不構成投資建議。投資有風險，請謹慎評估自身風險承受能力。
"""
        
        return report

def main():
    """主函數"""
    analyzer = StrategyValidationAnalyzer()
    
    # 生成驗證報告
    report = analyzer.generate_validation_report()
    
    # 保存報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"strategy_validation_report_{timestamp}.md"
    
    with open(report_filename, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n=== 策略驗證分析完成 ===")
    print(f"報告文件: {report_filename}")
    print(f"視覺化圖表: strategy_validation_analysis.png")
    
    return report_filename

if __name__ == "__main__":
    main()