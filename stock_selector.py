#!/usr/bin/env python3
"""
股票選擇器 - 核心選股邏輯
負責從技術分析報告中提取推薦股票，計算加分邏輯
"""

import json
import os
import glob
import logging
from typing import Dict, List, Optional
from datetime import datetime
from config import TECHNICAL_ANALYSIS_DIR, STATISTICS_DIR

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StockSelector:
    """股票選擇器 - 核心選股邏輯"""
    
    # 類別定義
    SECTION_NAMES = {
        'limit_up_stocks': '漲停',
        'strong_stocks': '強勢',
        'recommendations': '潛力'
    }
    
    # 多重出現加分比例
    MULTI_APPEARANCE_BONUS = 0.05  # 每多出現一次 +5%
    
    def __init__(self):
        """初始化選擇器"""
        self.work_dir = os.path.dirname(os.path.abspath(__file__))
        self.latest_analysis_path = os.path.join(self.work_dir, 'latest_analysis.json')
        self.technical_report_path = self._find_latest_technical_report()
        self.statistics_report_path = self._find_latest_statistics_report()
        
    def _find_latest_technical_report(self) -> Optional[str]:
        """找到最新的技術分析報告"""
        try:
            # 先嘗試標準目錄
            pattern = os.path.join(TECHNICAL_ANALYSIS_DIR, "technical_analysis_report_*.json")
            files = glob.glob(pattern)
            
            # 如果標準目錄沒有，嘗試工作目錄（遠端伺服器可能放在根目錄）
            if not files:
                pattern = os.path.join(self.work_dir, "technical_analysis_report_*.json")
                files = glob.glob(pattern)
            
            return max(files) if files else None
        except Exception as e:
            logger.error(f"找不到技術分析報告: {e}")
            return None
    
    def _find_latest_statistics_report(self) -> Optional[str]:
        """找到最新的統計報告"""
        try:
            pattern = os.path.join(STATISTICS_DIR, "statistics_report_*.json")
            files = glob.glob(pattern)
            return max(files) if files else None
        except Exception as e:
            logger.error(f"找不到統計報告: {e}")
            return None
    
    def load_technical_data(self) -> Dict:
        """
        載入技術分析數據（優先從技術分析報告讀取評級）
        
        流程:
        1. 優先嘗試直接從 technical_analysis_report_*.json 讀取完整評級資訊
        2. 如果技術分析報告不存在，再嘗試從 latest_analysis.json 讀取
        """
        # 方案 1: 優先從技術分析報告讀取（這裡有完整的評級資訊）
        if self.technical_report_path and os.path.exists(self.technical_report_path):
            try:
                with open(self.technical_report_path, 'r', encoding='utf-8') as f:
                    tech_report = json.load(f)
                    result = self._convert_tech_report_to_standard(tech_report)
                    if result.get('limit_up_stocks') or result.get('strong_stocks'):
                        logger.info(f"✓ 從技術分析報告載入數據")
                        return result
            except Exception as e:
                logger.warning(f"載入技術分析報告失敗: {e}")
        
        # 方案 2: 回退到 latest_analysis.json，並嘗試合併評級
        if os.path.exists(self.latest_analysis_path):
            try:
                with open(self.latest_analysis_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                # 如果有技術分析報告，嘗試合併評級資訊
                if self.technical_report_path and os.path.exists(self.technical_report_path):
                    result = self._merge_ratings_from_tech_report(result)
                
                return result
            except Exception as e:
                logger.warning(f"載入 latest_analysis.json 失敗: {e}")
        
        return {}
    
    def _merge_ratings_from_tech_report(self, data: Dict) -> Dict:
        """從技術分析報告合併評級資訊到現有數據"""
        try:
            with open(self.technical_report_path, 'r', encoding='utf-8') as f:
                tech_report = json.load(f)
        except Exception:
            return data
        
        # 建立評級索引表
        rating_map = {}
        
        for item in tech_report.get('limit_up_analysis', []):
            stock_info = item.get('stock_info', {})
            rating_info = item.get('rating', {})
            code = str(stock_info.get('Code', ''))
            if code and rating_info:
                rating_map[code] = {
                    'rating': rating_info.get('rating', ''),
                    'total_score': rating_info.get('total_score', 0),
                    'recommendation': rating_info.get('recommendation', ''),
                    'risk_level': rating_info.get('risk_level', ''),
                    'key_strengths': rating_info.get('key_strengths', []),
                    'key_risks': rating_info.get('key_risks', [])
                }
        
        for item in tech_report.get('strong_analysis', []):
            stock_info = item.get('stock_info', {})
            rating_info = item.get('rating', {})
            code = str(stock_info.get('Code', ''))
            if code and rating_info and code not in rating_map:
                rating_map[code] = {
                    'rating': rating_info.get('rating', ''),
                    'total_score': rating_info.get('total_score', 0),
                    'recommendation': rating_info.get('recommendation', ''),
                    'risk_level': rating_info.get('risk_level', ''),
                    'key_strengths': rating_info.get('key_strengths', []),
                    'key_risks': rating_info.get('key_risks', [])
                }
        
        # 合併評級到數據中
        for section in ['limit_up_stocks', 'strong_stocks', 'recommendations']:
            for stock in data.get(section, []):
                code = str(stock.get('code', ''))
                if code in rating_map:
                    stock.update(rating_map[code])
        
        logger.info(f"✓ 已合併 {len(rating_map)} 隻股票的評級資訊")
        return data
    
    def _convert_tech_report_to_standard(self, tech_report: Dict) -> Dict:
        """將技術分析報告轉換為標準格式"""
        result = {
            'limit_up_stocks': [],
            'strong_stocks': [],
            'recommendations': []
        }
        
        # 轉換 limit_up_analysis
        for item in tech_report.get('limit_up_analysis', []):
            stock_info = item.get('stock_info', {})
            rating_info = item.get('rating', {})
            result['limit_up_stocks'].append({
                'code': str(stock_info.get('Code', '')),
                'name': stock_info.get('Name', ''),
                'closing_price': stock_info.get('ClosingPrice', 0),
                'change_percent': stock_info.get('ChangePercent', 0),
                'volume': stock_info.get('TradeVolume', 0),
                'rating': rating_info.get('rating', ''),
                'total_score': rating_info.get('total_score', 0),
                'recommendation': rating_info.get('recommendation', ''),
                'risk_level': rating_info.get('risk_level', ''),
                'key_strengths': rating_info.get('key_strengths', []),
                'key_risks': rating_info.get('key_risks', [])
            })
        
        # 轉換 strong_stocks_analysis
        for item in tech_report.get('strong_stocks_analysis', []):
            stock_info = item.get('stock_info', {})
            rating_info = item.get('rating', {})
            result['strong_stocks'].append({
                'code': str(stock_info.get('Code', '')),
                'name': stock_info.get('Name', ''),
                'closing_price': stock_info.get('ClosingPrice', 0),
                'change_percent': stock_info.get('ChangePercent', 0),
                'volume': stock_info.get('TradeVolume', 0),
                'rating': rating_info.get('rating', ''),
                'total_score': rating_info.get('total_score', 0),
                'recommendation': rating_info.get('recommendation', ''),
                'risk_level': rating_info.get('risk_level', ''),
                'key_strengths': rating_info.get('key_strengths', []),
                'key_risks': rating_info.get('key_risks', [])
            })
        
        return result
    
    def load_statistics_data(self) -> Dict:
        """載入統計數據"""
        if not self.statistics_report_path:
            return {}
        try:
            with open(self.statistics_report_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"載入統計數據失敗: {e}")
            return {}
    
    def select_b_plus_stocks(self, data: Dict = None, top_n: int = 20) -> List[Dict]:
        """
        選取 B+ 級股票（核心選股邏輯）
        
        邏輯:
        1. 從技術分析報告的三個類別（漲停、強勢、潛力）中提取 B+ 股票
        2. 如果同一隻股票出現在多個類別，給予加分獎勵
        3. 按最終分數排序，取前 N 名
        
        Args:
            data: 外部傳入的數據（可選）
            top_n: 選取數量
            
        Returns:
            B+ 推薦股票列表
        """
        tech_data = data if data else self.load_technical_data()
        if not tech_data:
            logger.warning("無法載入技術分析數據")
            return []
        
        # 用 dict 追蹤每隻股票的出現情況
        stock_tracker = {}
        
        for section_key, section_label in self.SECTION_NAMES.items():
            stocks = tech_data.get(section_key, [])
            
            for stock in stocks:
                # latest_analysis.json 中 rating 直接是字串
                rating = stock.get('rating', '')
                if rating != 'B+':
                    continue
                
                # 直接從 stock 字典讀取欄位
                code = stock.get('code')
                code_str = str(code) if code else None
                
                if not code_str:
                    continue
                
                base_score = stock.get('total_score', 0) or 0
                
                if code_str in stock_tracker:
                    # 股票已存在，更新出現次數並取最高分
                    stock_tracker[code_str]['appear_count'] += 1
                    stock_tracker[code_str]['categories'].append(section_label)
                    if base_score > stock_tracker[code_str]['base_score']:
                        stock_tracker[code_str]['base_score'] = base_score
                else:
                    # 新股票
                    stock_tracker[code_str] = {
                        'name': stock.get('name'),
                        'code': code,
                        'rating': 'B+',
                        'base_score': base_score,
                        'appear_count': 1,
                        'categories': [section_label],
                        'change_percent': stock.get('change_percent'),
                        'closing_price': stock.get('closing_price'),
                        'recommendation': stock.get('recommendation'),
                        'technical_signals': stock.get('key_strengths', []),
                        'risk_level': stock.get('risk_level', '中風險')
                    }
        
        # 計算最終分數並構建結果列表
        results = []
        for code_str, data in stock_tracker.items():
            appear_count = data['appear_count']
            base_score = data['base_score']
            
            # 多重出現加分：2次+5%, 3次+10%
            bonus_multiplier = 1 + (appear_count - 1) * self.MULTI_APPEARANCE_BONUS
            final_score = min(100, base_score * bonus_multiplier)
            
            results.append({
                'name': data['name'],
                'code': data['code'],
                'rating': 'B+',
                'score': round(final_score, 2),
                'base_score': base_score,
                'appear_count': appear_count,
                'categories': data['categories'],
                'change_percent': data['change_percent'],
                'closing_price': data['closing_price'],
                'recommendation': data['recommendation'],
                'technical_signals': data['technical_signals'],
                'risk_level': data['risk_level']
            })
        
        # 按分數和出現次數排序
        results.sort(key=lambda x: (x['score'], x['appear_count']), reverse=True)
        
        logger.info(f"✓ 選出 {len(results)} 隻 B+ 級股票，取前 {top_n} 名")
        return results[:top_n]
    
    def select_top_recommendations(self, top_n: int = 5) -> List[Dict]:
        """
        選取頂級推薦（A+ 和 A 級）
        
        Args:
            top_n: 選取數量
            
        Returns:
            頂級推薦股票列表
        """
        tech_data = self.load_technical_data()
        if not tech_data:
            return []
        
        # 從 recommendations 或 limit_up_stocks/strong_stocks 中篩選 A/A+ 級
        results = []
        
        # 優先從 recommendations 取得
        recs = tech_data.get('recommendations', [])
        for stock in recs:
            rating = stock.get('rating', '')
            if rating in ['A+', 'A']:
                results.append(stock)
        
        # 如果 recommendations 不足，從 limit_up_stocks 和 strong_stocks 補充
        if len(results) < top_n:
            for section in ['limit_up_stocks', 'strong_stocks']:
                for stock in tech_data.get(section, []):
                    if stock.get('rating') in ['A+', 'A']:
                        # 避免重複
                        if not any(r.get('code') == stock.get('code') for r in results):
                            results.append(stock)
        
        # 按評分排序
        results.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        logger.info(f"✓ 選出 {len(results[:top_n])} 隻 A 級股票")
        return results[:top_n]
    
    def get_rating_distribution(self) -> Dict[str, int]:
        """取得評級分布"""
        stats_data = self.load_statistics_data()
        if not stats_data:
            return {}
        
        # 從 final_recommendations 計算
        from collections import Counter
        final_recs = stats_data.get('final_recommendations', [])
        return dict(Counter(rec.get('rating', 'N/A') for rec in final_recs))
    
    def get_summary(self) -> Dict:
        """取得選股摘要"""
        b_plus = self.select_b_plus_stocks()
        top_recs = self.select_top_recommendations()
        rating_dist = self.get_rating_distribution()
        
        # 計算多重出現股票數量
        multi_appear_count = sum(1 for s in b_plus if s['appear_count'] > 1)
        
        return {
            'b_plus_count': len(b_plus),
            'b_plus_multi_appear': multi_appear_count,
            'top_recommendations_count': len(top_recs),
            'rating_distribution': rating_dist,
            'b_plus_stocks': b_plus,
            'top_recommendations': top_recs,
            'generated_at': datetime.now().isoformat()
        }


# 便捷函數
def get_b_plus_recommendations(top_n: int = 20) -> List[Dict]:
    """快速取得 B+ 推薦股票"""
    selector = StockSelector()
    return selector.select_b_plus_stocks(top_n)


def get_top_recommendations(top_n: int = 10) -> List[Dict]:
    """快速取得頂級推薦股票"""
    selector = StockSelector()
    return selector.select_top_recommendations(top_n)


def get_selection_summary() -> Dict:
    """快速取得選股摘要"""
    selector = StockSelector()
    return selector.get_summary()


if __name__ == "__main__":
    # 測試
    print("=" * 60)
    print("股票選擇器測試")
    print("=" * 60)
    
    selector = StockSelector()
    
    print("\n📊 B+ 級推薦股票:")
    b_plus = selector.select_b_plus_stocks(top_n=10)
    for i, stock in enumerate(b_plus, 1):
        categories = '+'.join(stock['categories'])
        multi_tag = f" 🔥{categories}" if stock['appear_count'] > 1 else ""
        print(f"  {i}. {stock['name']} ({stock['code']}) - 分數: {stock['score']}{multi_tag}")
    
    print("\n📈 頂級推薦 (A+/A):")
    top_recs = selector.select_top_recommendations(5)
    for i, stock in enumerate(top_recs, 1):
        print(f"  {i}. {stock.get('name')} ({stock.get('code')}) - {stock.get('rating')}")
    
    print("\n📊 評級分布:")
    for rating, count in selector.get_rating_distribution().items():
        print(f"  {rating}: {count}")
