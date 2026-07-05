#!/usr/bin/env python3
"""
強勢族群分析模組
分析產業族群的動能、輪動趨勢、領頭股識別、族群間關聯度
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from collections import defaultdict

from industry_classifier import get_classifier, IndustryClassifier
from config import TECHNICAL_ANALYSIS_DIR

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SectorMomentumAnalyzer:
    """族群動能分析器"""
    
    def __init__(self, stock_data: Dict):
        """
        初始化族群動能分析器
        
        Args:
            stock_data: 股票數據字典，包含所有股票的交易資訊
        """
        self.stock_data = stock_data
        self.classifier = get_classifier()
        self.sector_data = self._prepare_sector_data()
        logger.info(f"族群動能分析器初始化完成，共分析 {len(self.sector_data)} 個產業族群")
    
    def _prepare_sector_data(self) -> Dict[str, List[Dict]]:
        """
        準備產業族群數據
        
        Returns:
            Dict[產業代碼, List[股票數據]]
        """
        sector_map = defaultdict(list)
        
        # 將股票按產業分組
        all_stocks = []
        if 'small_cap_limit_up' in self.stock_data:
            all_stocks.extend(self.stock_data['small_cap_limit_up'])
        if 'small_cap_strong' in self.stock_data:
            all_stocks.extend(self.stock_data['small_cap_strong'])
        
        for stock in all_stocks:
            stock_code = stock.get('Code', '')
            industry_info = self.classifier.get_stock_industry(stock_code)
            
            if industry_info:
                industry_code, industry_name, sub_industry = industry_info
                stock['IndustryCode'] = industry_code
                stock['IndustryName'] = industry_name
                stock['SubIndustry'] = sub_industry
                sector_map[industry_code].append(stock)
        
        return dict(sector_map)
    
    def calculate_sector_momentum(self) -> List[Dict]:
        """
        計算各產業族群的動能指標
        
        Returns:
            List[Dict]: 族群動能排名列表
        """
        sector_momentum = []
        
        for industry_code, stocks in self.sector_data.items():
            if not stocks:
                continue
            
            industry_name = self.classifier.get_industry_name(industry_code)
            
            # 計算族群平均漲幅
            changes = [float(s.get('ChangePercent', 0)) for s in stocks if s.get('ChangePercent')]
            avg_change = np.mean(changes) if changes else 0
            
            # 計算族群總成交量
            volumes = [float(s.get('TradeVolume', 0)) for s in stocks if s.get('TradeVolume')]
            total_volume = sum(volumes) if volumes else 0
            avg_volume = np.mean(volumes) if volumes else 0
            
            # 計算族群總成交值
            values = [float(s.get('TradeValue', 0)) for s in stocks if s.get('TradeValue')]
            total_value = sum(values) if values else 0
            
            # 計算上漲股票比例
            rising_stocks = [s for s in stocks if float(s.get('ChangePercent', 0)) > 0]
            rising_ratio = len(rising_stocks) / len(stocks) if stocks else 0
            
            # 計算漲停股票數量
            limit_up_stocks = [s for s in stocks if float(s.get('ChangePercent', 0)) >= 9.5]
            limit_up_count = len(limit_up_stocks)
            
            # 計算強勢股票數量（漲幅>3%）
            strong_stocks = [s for s in stocks if float(s.get('ChangePercent', 0)) >= 3]
            strong_count = len(strong_stocks)
            
            # 計算族群動能分數
            momentum_score = self._calculate_momentum_score(
                avg_change, rising_ratio, limit_up_count, strong_count, len(stocks)
            )
            
            # 識別領頭股（前3名）
            leader_stocks = sorted(
                stocks,
                key=lambda x: float(x.get('ChangePercent', 0)),
                reverse=True
            )[:3]
            
            sector_info = {
                'industry_code': industry_code,
                'industry_name': industry_name,
                'stock_count': len(stocks),
                'avg_change_percent': round(avg_change, 2),
                'total_volume': total_volume,
                'avg_volume': round(avg_volume, 0),
                'total_value': round(total_value, 0),
                'rising_ratio': round(rising_ratio * 100, 1),
                'limit_up_count': limit_up_count,
                'strong_count': strong_count,
                'momentum_score': round(momentum_score, 2),
                'leader_stocks': [
                    {
                        'code': s.get('Code'),
                        'name': s.get('Name'),
                        'change_percent': float(s.get('ChangePercent', 0))
                    }
                    for s in leader_stocks
                ],
                'stocks': stocks
            }
            
            sector_momentum.append(sector_info)
        
        # 按動能分數排序
        sector_momentum.sort(key=lambda x: x['momentum_score'], reverse=True)
        
        logger.info(f"完成 {len(sector_momentum)} 個產業族群的動能計算")
        return sector_momentum
    
    def _calculate_momentum_score(
        self,
        avg_change: float,
        rising_ratio: float,
        limit_up_count: int,
        strong_count: int,
        total_count: int
    ) -> float:
        """
        計算族群動能分數
        
        Args:
            avg_change: 平均漲幅
            rising_ratio: 上漲比例
            limit_up_count: 漲停數量
            strong_count: 強勢股數量
            total_count: 總股票數
            
        Returns:
            float: 動能分數 (0-100)
        """
        # 漲幅分數（0-30分）
        change_score = min(avg_change * 3, 30)
        
        # 上漲比例分數（0-25分）
        ratio_score = rising_ratio * 25
        
        # 漲停數量分數（0-25分）
        limit_score = min((limit_up_count / max(total_count, 1)) * 100, 25)
        
        # 強勢股比例分數（0-20分）
        strong_score = min((strong_count / max(total_count, 1)) * 100, 20)
        
        total_score = change_score + ratio_score + limit_score + strong_score
        return total_score
    
    def detect_sector_rotation(self, historical_data: Optional[List[Dict]] = None) -> Dict:
        """
        偵測產業輪動趨勢
        
        Args:
            historical_data: 歷史族群數據（可選，用於判斷輪動趨勢）
            
        Returns:
            Dict: 輪動分析結果
        """
        current_momentum = self.calculate_sector_momentum()
        
        # 識別當前領漲族群（動能分數前5名）
        leading_sectors = current_momentum[:5]
        
        # 識別潛力族群（上漲比例>60%但動能分數中等）
        potential_sectors = [
            s for s in current_momentum[5:15]
            if s['rising_ratio'] > 60 and s['avg_change_percent'] > 2
        ]
        
        # 識別弱勢族群（動能分數後5名）
        weak_sectors = current_momentum[-5:]
        
        rotation_analysis = {
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'leading_sectors': [
                {
                    'rank': i + 1,
                    'industry_name': s['industry_name'],
                    'momentum_score': s['momentum_score'],
                    'avg_change': s['avg_change_percent'],
                    'rising_ratio': s['rising_ratio'],
                    'leader_stock': s['leader_stocks'][0] if s['leader_stocks'] else None
                }
                for i, s in enumerate(leading_sectors)
            ],
            'potential_sectors': [
                {
                    'industry_name': s['industry_name'],
                    'momentum_score': s['momentum_score'],
                    'avg_change': s['avg_change_percent'],
                    'rising_ratio': s['rising_ratio']
                }
                for s in potential_sectors
            ],
            'weak_sectors': [
                {
                    'industry_name': s['industry_name'],
                    'momentum_score': s['momentum_score'],
                    'avg_change': s['avg_change_percent']
                }
                for s in weak_sectors
            ],
            'rotation_signal': self._generate_rotation_signal(leading_sectors)
        }
        
        logger.info(f"完成產業輪動偵測，識別出 {len(leading_sectors)} 個領漲族群")
        return rotation_analysis
    
    def _generate_rotation_signal(self, leading_sectors: List[Dict]) -> str:
        """
        生成輪動訊號
        
        Args:
            leading_sectors: 領漲族群列表
            
        Returns:
            str: 輪動訊號描述
        """
        if not leading_sectors:
            return "市場無明確輪動趨勢"
        
        top_sector = leading_sectors[0]
        industry_name = top_sector['industry_name']
        momentum_score = top_sector['momentum_score']
        
        if momentum_score > 70:
            return f"強勢輪動至【{industry_name}】，建議重點關注"
        elif momentum_score > 50:
            return f"溫和輪動至【{industry_name}】，可適度配置"
        else:
            return "市場處於整理階段，無明顯輪動"
    
    def identify_sector_leaders(self, sector_code: str) -> List[Dict]:
        """
        識別特定產業的領頭股
        
        Args:
            sector_code: 產業代碼
            
        Returns:
            List[Dict]: 領頭股列表
        """
        if sector_code not in self.sector_data:
            logger.warning(f"產業代碼 {sector_code} 無股票數據")
            return []
        
        stocks = self.sector_data[sector_code]
        
        # 計算每支股票的領導力分數
        leaders = []
        for stock in stocks:
            change_percent = float(stock.get('ChangePercent', 0))
            volume = float(stock.get('TradeVolume', 0))
            value = float(stock.get('TradeValue', 0))
            
            # 領導力分數 = 漲幅(40%) + 成交量排名(30%) + 成交值排名(30%)
            change_score = change_percent * 4
            
            # 計算成交量和成交值在族群中的相對排名
            volumes = [float(s.get('TradeVolume', 0)) for s in stocks]
            values = [float(s.get('TradeValue', 0)) for s in stocks]
            
            volume_rank = (sum(1 for v in volumes if volume > v) / len(volumes)) * 30 if volumes else 0
            value_rank = (sum(1 for v in values if value > v) / len(values)) * 30 if values else 0
            
            leadership_score = change_score + volume_rank + value_rank
            
            leaders.append({
                'code': stock.get('Code'),
                'name': stock.get('Name'),
                'change_percent': change_percent,
                'volume': volume,
                'value': value,
                'leadership_score': round(leadership_score, 2)
            })
        
        # 按領導力分數排序
        leaders.sort(key=lambda x: x['leadership_score'], reverse=True)
        
        logger.info(f"識別出產業 {sector_code} 的 {len(leaders)} 支領頭股")
        return leaders[:10]  # 返回前10名
    
    def calculate_sector_correlation(self) -> pd.DataFrame:
        """
        計算產業間的關聯度矩陣
        
        Returns:
            pd.DataFrame: 關聯度矩陣
        """
        # 建立產業漲幅矩陣
        sector_changes = {}
        for industry_code, stocks in self.sector_data.items():
            if stocks:
                industry_name = self.classifier.get_industry_name(industry_code)
                changes = [float(s.get('ChangePercent', 0)) for s in stocks]
                sector_changes[industry_name] = np.mean(changes) if changes else 0
        
        # 注意：單日數據無法計算真正的相關係數
        # 這裡提供一個基於漲幅接近度的相似度矩陣
        sector_names = list(sector_changes.keys())
        n = len(sector_names)
        correlation_matrix = np.zeros((n, n))
        
        for i, sector1 in enumerate(sector_names):
            for j, sector2 in enumerate(sector_names):
                if i == j:
                    correlation_matrix[i][j] = 1.0
                else:
                    # 使用漲幅差異的反向作為相似度
                    change_diff = abs(sector_changes[sector1] - sector_changes[sector2])
                    similarity = max(0, 1 - (change_diff / 10))  # 假設10%漲幅差為完全不相關
                    correlation_matrix[i][j] = similarity
        
        df_correlation = pd.DataFrame(
            correlation_matrix,
            index=sector_names,
            columns=sector_names
        )
        
        logger.info(f"完成 {len(sector_names)} 個產業的關聯度矩陣計算")
        return df_correlation
    
    def find_related_sectors(self, sector_code: str, threshold: float = 0.7) -> List[Dict]:
        """
        尋找與指定產業高度相關的其他產業
        
        Args:
            sector_code: 產業代碼
            threshold: 相關度門檻（0-1）
            
        Returns:
            List[Dict]: 相關產業列表
        """
        correlation_matrix = self.calculate_sector_correlation()
        target_name = self.classifier.get_industry_name(sector_code)
        
        if target_name not in correlation_matrix.index:
            logger.warning(f"產業 {target_name} 無相關數據")
            return []
        
        # 獲取相關度
        correlations = correlation_matrix[target_name]
        
        # 篩選高相關產業
        related = []
        for sector_name, corr in correlations.items():
            if sector_name != target_name and corr >= threshold:
                related.append({
                    'industry_name': sector_name,
                    'correlation': round(corr, 3)
                })
        
        # 按相關度排序
        related.sort(key=lambda x: x['correlation'], reverse=True)
        
        logger.info(f"找到 {len(related)} 個與 {target_name} 相關的產業")
        return related
    
    def generate_sector_report(self) -> Dict:
        """
        生成族群分析完整報告
        
        Returns:
            Dict: 族群分析報告
        """
        momentum = self.calculate_sector_momentum()
        rotation = self.detect_sector_rotation()
        
        # 識別電子族群（最重要的族群）
        electronics_sectors = [
            s for s in momentum
            if s['industry_code'] in ['24', '25', '26', '27', '28', '29', '30', '31']
        ]
        
        # 識別傳產族群
        traditional_sectors = [
            s for s in momentum
            if s['industry_code'] not in ['17', '24', '25', '26', '27', '28', '29', '30', '31']
        ]
        
        # 識別金融族群
        finance_sectors = [s for s in momentum if s['industry_code'] == '17']
        
        report = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_sectors': len(momentum),
                'strong_sectors': len([s for s in momentum if s['momentum_score'] > 50]),
                'weak_sectors': len([s for s in momentum if s['momentum_score'] < 30]),
                'top_sector': momentum[0] if momentum else None
            },
            'sector_ranking': momentum[:10],  # TOP 10
            'rotation_analysis': rotation,
            'category_analysis': {
                'electronics': {
                    'count': len(electronics_sectors),
                    'avg_momentum': np.mean([s['momentum_score'] for s in electronics_sectors]) if electronics_sectors else 0,
                    'top_sectors': electronics_sectors[:3]
                },
                'traditional': {
                    'count': len(traditional_sectors),
                    'avg_momentum': np.mean([s['momentum_score'] for s in traditional_sectors]) if traditional_sectors else 0,
                    'top_sectors': traditional_sectors[:3]
                },
                'finance': {
                    'count': len(finance_sectors),
                    'avg_momentum': np.mean([s['momentum_score'] for s in finance_sectors]) if finance_sectors else 0,
                    'sectors': finance_sectors
                }
            },
            'full_momentum_data': momentum
        }
        
        logger.info("完成族群分析報告生成")
        return report
    
    def save_report(self, report: Dict, filename: Optional[str] = None):
        """
        儲存族群分析報告
        
        Args:
            report: 報告數據
            filename: 檔案名稱（可選）
        """
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'sector_momentum_analysis_{timestamp}.json'
        
        filepath = os.path.join(TECHNICAL_ANALYSIS_DIR, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            logger.info(f"族群分析報告已儲存至: {filepath}")
        except Exception as e:
            logger.error(f"儲存報告失敗: {e}")


def analyze_sector_momentum(data_file: str) -> Dict:
    """
    執行族群動能分析（便利函數）
    
    Args:
        data_file: 股票數據JSON文件路徑
        
    Returns:
        Dict: 族群分析報告
    """
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            stock_data = json.load(f)
        
        analyzer = SectorMomentumAnalyzer(stock_data)
        report = analyzer.generate_sector_report()
        analyzer.save_report(report)
        
        return report
    except Exception as e:
        logger.error(f"族群動能分析失敗: {e}")
        return {}


if __name__ == '__main__':
    # 測試代碼
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: python sector_momentum_analyzer.py <股票數據JSON檔案>")
        sys.exit(1)
    
    data_file = sys.argv[1]
    
    if not os.path.exists(data_file):
        print(f"錯誤: 找不到檔案 {data_file}")
        sys.exit(1)
    
    print("=" * 70)
    print("強勢族群分析系統")
    print("=" * 70)
    
    report = analyze_sector_momentum(data_file)
    
    if report:
        print("\n" + "=" * 70)
        print("分析摘要")
        print("=" * 70)
        print(f"分析時間: {report['generated_at']}")
        print(f"總族群數: {report['summary']['total_sectors']}")
        print(f"強勢族群: {report['summary']['strong_sectors']}")
        print(f"弱勢族群: {report['summary']['weak_sectors']}")
        
        if report['summary']['top_sector']:
            top = report['summary']['top_sector']
            print(f"\n最強族群: {top['industry_name']}")
            print(f"  動能分數: {top['momentum_score']}")
            print(f"  平均漲幅: {top['avg_change_percent']}%")
            print(f"  上漲比例: {top['rising_ratio']}%")
        
        print("\n分析完成！報告已儲存。")
