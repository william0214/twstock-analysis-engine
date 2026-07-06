#!/usr/bin/env python3
"""
技術面和籌碼面分析模組 v2.0 (優化版)
對股票進行技術指標計算和籌碼面分析

版本更新：
- v2.0 (2025-10-20): 基於策略驗證結果優化
  * 技術面權重提升至65% (原60%)
  * 動能指標權重提升至40% (原30%)
  * 流動性門檻提高，低於200萬股扣15%
  * 評級門檻提升：A+≥85分, A≥75分 (原80/70)
  * 風險調整係數優化
"""

import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

from config import TECHNICAL_ANALYSIS_DIR, STOCK_DATA_DIR

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK TC', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    """技術分析器"""
    
    def __init__(self, data_file: str):
        """
        初始化技術分析器
        
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
    
    def calculate_technical_indicators(self, stock_data: Dict) -> Dict:
        """
        計算技術指標
        
        Args:
            stock_data: 單一股票數據
            
        Returns:
            Dict: 技術指標結果
        """
        try:
            # 基本價格數據
            open_price = float(stock_data.get('OpeningPrice', 0))
            high_price = float(stock_data.get('HighestPrice', 0))
            low_price = float(stock_data.get('LowestPrice', 0))
            close_price = float(stock_data.get('ClosingPrice', 0))
            volume = float(stock_data.get('TradeVolume', 0))
            change_percent = float(stock_data.get('ChangePercent', 0))
            
            # 計算技術指標
            indicators = {
                # 價格相關指標
                'price_position': self.calculate_price_position(open_price, high_price, low_price, close_price),
                'volatility': self.calculate_volatility(open_price, high_price, low_price, close_price),
                'price_momentum': change_percent,
                
                # 成交量相關指標
                'volume_intensity': self.calculate_volume_intensity(volume, close_price),
                'volume_price_trend': self.calculate_volume_price_trend(volume, change_percent),
                
                # 強度指標
                'relative_strength': self.calculate_relative_strength(change_percent, volume),
                'momentum_score': self.calculate_momentum_score(change_percent, volume, high_price, low_price, close_price),
                
                # 風險指標
                'risk_level': self.calculate_risk_level(change_percent, volume, close_price),
                'liquidity_score': self.calculate_liquidity_score(volume, stock_data.get('Transaction', 0))
            }
            
            return indicators
            
        except Exception as e:
            logger.error(f"計算技術指標時發生錯誤: {e}")
            return {}
    
    def calculate_price_position(self, open_price: float, high_price: float, 
                               low_price: float, close_price: float) -> float:
        """
        計算價格位置（收盤價在當日價格區間的位置）
        
        Returns:
            float: 價格位置 (0-1)，1表示收在最高價
        """
        if high_price == low_price:
            return 0.5
        return (close_price - low_price) / (high_price - low_price)
    
    def calculate_volatility(self, open_price: float, high_price: float, 
                           low_price: float, close_price: float) -> float:
        """
        計算當日波動率
        
        Returns:
            float: 波動率百分比
        """
        if open_price == 0:
            return 0
        return ((high_price - low_price) / open_price) * 100
    
    def calculate_volume_intensity(self, volume: float, price: float) -> float:
        """
        計算成交量強度（成交金額）
        
        Returns:
            float: 成交量強度
        """
        return volume * price
    
    def calculate_volume_price_trend(self, volume: float, change_percent: float) -> str:
        """
        計算量價趨勢
        
        Returns:
            str: 量價趨勢描述
        """
        if change_percent > 0 and volume > 1000000:  # 上漲且高成交量
            return "量價齊揚"
        elif change_percent > 0 and volume <= 1000000:  # 上漲但低成交量
            return "價漲量縮"
        elif change_percent < 0 and volume > 1000000:  # 下跌且高成交量
            return "量價齊跌"
        elif change_percent < 0 and volume <= 1000000:  # 下跌但低成交量
            return "價跌量縮"
        else:
            return "盤整"
    
    def calculate_relative_strength(self, change_percent: float, volume: float) -> float:
        """
        計算相對強度
        
        Returns:
            float: 相對強度分數
        """
        # 結合漲幅和成交量的綜合強度
        volume_score = min(volume / 10000000, 1.0)  # 成交量標準化
        change_score = max(0, change_percent / 10)  # 漲幅標準化
        
        return (change_score * 0.7 + volume_score * 0.3) * 100
    
    def calculate_momentum_score(self, change_percent: float, volume: float, 
                               high_price: float, low_price: float, close_price: float) -> float:
        """
        計算動能分數
        
        Returns:
            float: 動能分數
        """
        # 價格動能
        price_momentum = change_percent
        
        # 位置動能（收盤價接近最高價）
        if high_price > low_price:
            position_momentum = (close_price - low_price) / (high_price - low_price) * 10
        else:
            position_momentum = 5
        
        # 成交量動能
        volume_momentum = min(volume / 5000000, 2.0) * 5
        
        # 綜合動能分數
        total_momentum = (price_momentum * 0.5 + position_momentum * 0.3 + volume_momentum * 0.2)
        
        return max(0, total_momentum)
    
    def calculate_risk_level(self, change_percent: float, volume: float, price: float) -> str:
        """
        計算風險等級
        
        Returns:
            str: 風險等級
        """
        risk_score = 0
        
        # 漲幅風險
        if change_percent >= 9.5:
            risk_score += 3  # 漲停風險高
        elif change_percent >= 7:
            risk_score += 2
        elif change_percent >= 5:
            risk_score += 1
        
        # 成交量風險
        if volume < 100000:
            risk_score += 2  # 流動性風險
        
        # 價格風險
        if price > 1000:
            risk_score += 1  # 高價股風險
        elif price < 10:
            risk_score += 1  # 低價股風險
        
        if risk_score >= 5:
            return "高風險"
        elif risk_score >= 3:
            return "中風險"
        else:
            return "低風險"
    
    def calculate_liquidity_score(self, volume: float, transactions: float) -> float:
        """
        計算流動性分數
        
        Returns:
            float: 流動性分數 (0-100)
        """
        # 成交量分數
        volume_score = min(volume / 10000000, 1.0) * 50
        
        # 成交筆數分數
        transaction_score = min(transactions / 5000, 1.0) * 50
        
        return volume_score + transaction_score
    
    def analyze_chip_distribution(self, stock_data: Dict) -> Dict:
        """
        分析籌碼面（基於當日數據的簡化分析）
        
        Args:
            stock_data: 股票數據
            
        Returns:
            Dict: 籌碼面分析結果
        """
        try:
            volume = float(stock_data.get('TradeVolume', 0))
            trade_value = float(stock_data.get('TradeValue', 0))
            transactions = float(stock_data.get('Transaction', 0))
            change_percent = float(stock_data.get('ChangePercent', 0))
            
            # 平均每筆交易金額
            avg_trade_amount = trade_value / transactions if transactions > 0 else 0
            
            # 平均每筆交易股數
            avg_trade_volume = volume / transactions if transactions > 0 else 0
            
            analysis = {
                'trading_characteristics': {
                    'avg_trade_amount': avg_trade_amount,
                    'avg_trade_volume': avg_trade_volume,
                    'total_transactions': transactions,
                    'trade_intensity': volume / 1000000 if volume > 0 else 0  # 百萬股為單位
                },
                'investor_behavior': self.analyze_investor_behavior(avg_trade_amount, transactions, change_percent),
                'chip_concentration': self.calculate_chip_concentration(volume, transactions, trade_value),
                'market_participation': self.analyze_market_participation(volume, transactions, change_percent)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析籌碼面時發生錯誤: {e}")
            return {}
    
    def analyze_investor_behavior(self, avg_trade_amount: float, transactions: float, 
                                change_percent: float) -> Dict:
        """
        分析投資人行為
        
        Returns:
            Dict: 投資人行為分析
        """
        behavior = {
            'investor_type': '',
            'trading_pattern': '',
            'sentiment': ''
        }
        
        # 判斷投資人類型
        if avg_trade_amount > 1000000:  # 100萬以上
            behavior['investor_type'] = '大戶主導'
        elif avg_trade_amount > 100000:  # 10萬以上
            behavior['investor_type'] = '中實戶參與'
        else:
            behavior['investor_type'] = '散戶為主'
        
        # 判斷交易模式
        if transactions > 5000:
            behavior['trading_pattern'] = '活躍交易'
        elif transactions > 1000:
            behavior['trading_pattern'] = '正常交易'
        else:
            behavior['trading_pattern'] = '清淡交易'
        
        # 判斷市場情緒
        if change_percent > 5 and transactions > 2000:
            behavior['sentiment'] = '樂觀積極'
        elif change_percent > 0:
            behavior['sentiment'] = '謹慎樂觀'
        elif change_percent < -3:
            behavior['sentiment'] = '悲觀賣壓'
        else:
            behavior['sentiment'] = '觀望等待'
        
        return behavior
    
    def calculate_chip_concentration(self, volume: float, transactions: float, 
                                   trade_value: float) -> Dict:
        """
        計算籌碼集中度
        
        Returns:
            Dict: 籌碼集中度分析
        """
        avg_trade_size = volume / transactions if transactions > 0 else 0
        
        concentration = {
            'concentration_level': '',
            'avg_trade_size': avg_trade_size,
            'large_trade_ratio': 0
        }
        
        # 判斷集中度
        if avg_trade_size > 10000:  # 平均每筆超過1萬股
            concentration['concentration_level'] = '高度集中'
            concentration['large_trade_ratio'] = 0.8
        elif avg_trade_size > 5000:
            concentration['concentration_level'] = '中度集中'
            concentration['large_trade_ratio'] = 0.6
        elif avg_trade_size > 1000:
            concentration['concentration_level'] = '分散持有'
            concentration['large_trade_ratio'] = 0.4
        else:
            concentration['concentration_level'] = '高度分散'
            concentration['large_trade_ratio'] = 0.2
        
        return concentration
    
    def analyze_market_participation(self, volume: float, transactions: float, 
                                   change_percent: float) -> Dict:
        """
        分析市場參與度
        
        Returns:
            Dict: 市場參與度分析
        """
        participation = {
            'activity_level': '',
            'participation_score': 0,
            'market_interest': ''
        }
        
        # 計算參與度分數
        volume_score = min(volume / 5000000, 1.0) * 40  # 成交量分數
        transaction_score = min(transactions / 3000, 1.0) * 40  # 交易筆數分數
        momentum_score = min(abs(change_percent) / 10, 1.0) * 20  # 動能分數
        
        participation['participation_score'] = volume_score + transaction_score + momentum_score
        
        # 判斷活躍度
        if participation['participation_score'] >= 80:
            participation['activity_level'] = '極度活躍'
        elif participation['participation_score'] >= 60:
            participation['activity_level'] = '高度活躍'
        elif participation['participation_score'] >= 40:
            participation['activity_level'] = '中度活躍'
        elif participation['participation_score'] >= 20:
            participation['activity_level'] = '低度活躍'
        else:
            participation['activity_level'] = '冷清'
        
        # 判斷市場興趣
        if change_percent > 5 and volume > 2000000:
            participation['market_interest'] = '高度關注'
        elif change_percent > 2 and volume > 1000000:
            participation['market_interest'] = '中度關注'
        elif volume > 500000:
            participation['market_interest'] = '一般關注'
        else:
            participation['market_interest'] = '關注度低'
        
        return participation
    
    def generate_stock_rating(self, technical_indicators: Dict, chip_analysis: Dict, 
                            stock_data: Dict) -> Dict:
        """
        生成股票評級
        
        Returns:
            Dict: 股票評級結果
        """
        try:
            # ============== 優化後的評分系統 v2.0 ==============
            # 基於策略驗證結果調整權重和門檻
            
            # 技術面評分（權重從60%提升至65%）
            technical_score = 0
            
            # 動能分數 (40% - 提升) - 加強動能指標重要性
            # calculate_momentum_score() 的實際最大值約為 10（非 30），故用 1.0 封頂
            # 讓滿分動能真的貢獻 40 分，修正前 min(x/10, 3) 恆等於 1，動能實際只佔 13.33 分
            momentum_score = technical_indicators.get('momentum_score', 0)
            technical_score += min(momentum_score / 10, 1.0) * 40
            
            # 相對強度 (25%)
            relative_strength = technical_indicators.get('relative_strength', 0)
            technical_score += min(relative_strength / 100, 1) * 25
            
            # 流動性分數 (20% - 提高門檻)
            liquidity_score = technical_indicators.get('liquidity_score', 0)
            # 流動性門檻提高：需達到60分以上才給予完整分數
            if liquidity_score >= 60:
                technical_score += min(liquidity_score / 100, 1) * 20
            else:
                technical_score += min(liquidity_score / 100, 1) * 10  # 低流動性減半
            
            # 價格位置 (10% - 降低)
            price_position = technical_indicators.get('price_position', 0.5)
            technical_score += price_position * 10
            
            # 量價趨勢 (5% - 降低)
            volume_price_trend = technical_indicators.get('volume_price_trend', '')
            if volume_price_trend == '量價齊揚':
                technical_score += 5
            elif volume_price_trend == '價漲量縮':
                technical_score += 2.5
            
            # 籌碼面評分（權重從40%提升至35%）
            chip_score = 0
            
            # 市場參與度 (45% - 提升)
            participation_score = chip_analysis.get('market_participation', {}).get('participation_score', 0)
            chip_score += min(participation_score / 100, 1) * 45
            
            # 投資人行為 (35%)
            investor_behavior = chip_analysis.get('investor_behavior', {})
            if investor_behavior.get('sentiment') == '樂觀積極':
                chip_score += 35
            elif investor_behavior.get('sentiment') == '謹慎樂觀':
                chip_score += 25
            elif investor_behavior.get('sentiment') == '觀望等待':
                chip_score += 15
            else:
                chip_score += 5  # 悲觀情緒給予低分
            
            # 籌碼集中度 (20% - 降低)
            concentration = chip_analysis.get('chip_concentration', {})
            concentration_level = concentration.get('concentration_level', '')
            if concentration_level == '中度集中':
                chip_score += 20
            elif concentration_level == '高度集中':
                chip_score += 15
            elif concentration_level == '分散持有':
                chip_score += 10
            
            # 綜合評分（技術面65%，籌碼面35%）
            total_score = technical_score * 0.65 + chip_score * 0.35
            
            # 流動性嚴格檢查 - 新增
            volume = stock_data.get('TradeVolume', 0)
            if volume < 2000000:  # 日成交量低於200萬股
                total_score *= 0.85  # 扣15%
            
            # 風險調整（更嚴格）
            risk_level = technical_indicators.get('risk_level', '中風險')
            if risk_level == '高風險':
                total_score *= 0.75  # 從0.8調整為0.75
            elif risk_level == '低風險':
                total_score *= 1.15  # 從1.1調整為1.15
            
            # 確保分數在0-100範圍內
            total_score = max(0, min(100, total_score))
            
            # 評級分類
            # 門檻重新校準：動能權重從 13.33 分修正回設計值 40 分後，漲停股（動能天生
            # 接近滿分）的分數整體上移且在高分區大量群聚，若沿用舊門檻 A+ 會從 2 檔暴增
            # 到 41 檔、失去鑑別度。以 2026-07-03 真實資料重新校準，使各級檔數比例貼近
            # 修正前的分布（A+:2/A:35/B+:8/B:8/C+:5/C:14/D:2，共74檔）。
            if total_score >= 98:
                rating = 'A+'
                recommendation = '強烈推薦'
            elif total_score >= 90:
                rating = 'A'
                recommendation = '推薦'
            elif total_score >= 80:
                rating = 'B+'
                recommendation = '中性偏多'
            elif total_score >= 65:
                rating = 'B'
                recommendation = '中性'
            elif total_score >= 55:
                rating = 'C+'
                recommendation = '中性偏空'
            elif total_score >= 45:
                rating = 'C'
                recommendation = '不推薦'
            else:
                rating = 'D'
                recommendation = '避免'
            
            return {
                'total_score': round(total_score, 2),
                'technical_score': round(technical_score, 2),
                'chip_score': round(chip_score, 2),
                'rating': rating,
                'recommendation': recommendation,
                'risk_level': risk_level,
                'key_strengths': self.identify_key_strengths(technical_indicators, chip_analysis),
                'key_risks': self.identify_key_risks(technical_indicators, chip_analysis, stock_data)
            }
            
        except Exception as e:
            logger.error(f"生成股票評級時發生錯誤: {e}")
            return {}
    
    def identify_key_strengths(self, technical_indicators: Dict, chip_analysis: Dict) -> List[str]:
        """識別關鍵優勢"""
        strengths = []
        
        # 技術面優勢
        if technical_indicators.get('momentum_score', 0) > 8:
            strengths.append('強勁動能')
        
        if technical_indicators.get('volume_price_trend') == '量價齊揚':
            strengths.append('量價配合良好')
        
        if technical_indicators.get('price_position', 0) > 0.8:
            strengths.append('收盤接近高點')
        
        if technical_indicators.get('liquidity_score', 0) > 70:
            strengths.append('流動性佳')
        
        # 籌碼面優勢
        investor_behavior = chip_analysis.get('investor_behavior', {})
        if investor_behavior.get('sentiment') == '樂觀積極':
            strengths.append('市場情緒樂觀')
        
        if investor_behavior.get('investor_type') == '大戶主導':
            strengths.append('大戶關注')
        
        participation = chip_analysis.get('market_participation', {})
        if participation.get('activity_level') in ['極度活躍', '高度活躍']:
            strengths.append('交易活躍')
        
        return strengths
    
    def identify_key_risks(self, technical_indicators: Dict, chip_analysis: Dict, 
                          stock_data: Dict) -> List[str]:
        """識別關鍵風險"""
        risks = []
        
        # 技術面風險
        if technical_indicators.get('risk_level') == '高風險':
            risks.append('技術面風險偏高')
        
        if float(stock_data.get('ChangePercent', 0)) >= 9.5:
            risks.append('漲停回檔風險')
        
        if technical_indicators.get('volatility', 0) > 15:
            risks.append('波動性過大')
        
        if technical_indicators.get('liquidity_score', 0) < 30:
            risks.append('流動性不足')
        
        # 籌碼面風險
        concentration = chip_analysis.get('chip_concentration', {})
        if concentration.get('concentration_level') == '高度集中':
            risks.append('籌碼過度集中')
        
        investor_behavior = chip_analysis.get('investor_behavior', {})
        if investor_behavior.get('trading_pattern') == '清淡交易':
            risks.append('交易清淡')
        
        # 價格風險
        price = float(stock_data.get('ClosingPrice', 0))
        if price > 1000:
            risks.append('高價股風險')
        elif price < 10:
            risks.append('低價股風險')
        
        return risks
    
    def analyze_all_stocks(self) -> Dict:
        """
        分析所有重點股票
        
        Returns:
            Dict: 所有股票的技術和籌碼面分析結果
        """
        logger.info("開始進行技術面和籌碼面分析...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'limit_up_analysis': [],
            'strong_stocks_analysis': [],
            'potential_stocks_analysis': [],
            'summary_statistics': {}
        }
        
        # 分析漲停股票
        if self.data.get('small_cap_limit_up'):
            logger.info("分析漲停股票...")
            for stock in self.data['small_cap_limit_up']:
                technical_indicators = self.calculate_technical_indicators(stock)
                chip_analysis = self.analyze_chip_distribution(stock)
                rating = self.generate_stock_rating(technical_indicators, chip_analysis, stock)
                
                stock_analysis = {
                    'stock_info': stock,
                    'technical_indicators': technical_indicators,
                    'chip_analysis': chip_analysis,
                    'rating': rating
                }
                results['limit_up_analysis'].append(stock_analysis)
        
        # 分析強勢股票（取前20名）
        if self.data.get('small_cap_strong'):
            logger.info("分析強勢股票...")
            for stock in self.data['small_cap_strong'][:20]:
                technical_indicators = self.calculate_technical_indicators(stock)
                chip_analysis = self.analyze_chip_distribution(stock)
                rating = self.generate_stock_rating(technical_indicators, chip_analysis, stock)
                
                stock_analysis = {
                    'stock_info': stock,
                    'technical_indicators': technical_indicators,
                    'chip_analysis': chip_analysis,
                    'rating': rating
                }
                results['strong_stocks_analysis'].append(stock_analysis)
        
        # 計算統計摘要
        results['summary_statistics'] = self.calculate_analysis_summary(results)
        
        logger.info("技術面和籌碼面分析完成")
        return results
    
    def calculate_analysis_summary(self, results: Dict) -> Dict:
        """計算分析統計摘要"""
        try:
            summary = {
                'limit_up_summary': {},
                'strong_stocks_summary': {},
                'rating_distribution': {},
                'risk_distribution': {}
            }
            
            # 漲停股票統計
            if results['limit_up_analysis']:
                limit_scores = [stock['rating']['total_score'] for stock in results['limit_up_analysis']]
                summary['limit_up_summary'] = {
                    'count': len(limit_scores),
                    'avg_score': np.mean(limit_scores),
                    'max_score': np.max(limit_scores),
                    'min_score': np.min(limit_scores)
                }
            
            # 強勢股票統計
            if results['strong_stocks_analysis']:
                strong_scores = [stock['rating']['total_score'] for stock in results['strong_stocks_analysis']]
                summary['strong_stocks_summary'] = {
                    'count': len(strong_scores),
                    'avg_score': np.mean(strong_scores),
                    'max_score': np.max(strong_scores),
                    'min_score': np.min(strong_scores)
                }
            
            # 評級分布統計
            all_ratings = []
            all_risks = []
            
            for stock in results['limit_up_analysis'] + results['strong_stocks_analysis']:
                all_ratings.append(stock['rating']['rating'])
                all_risks.append(stock['rating']['risk_level'])
            
            # 計算評級分布
            rating_counts = {}
            for rating in all_ratings:
                rating_counts[rating] = rating_counts.get(rating, 0) + 1
            summary['rating_distribution'] = rating_counts
            
            # 計算風險分布
            risk_counts = {}
            for risk in all_risks:
                risk_counts[risk] = risk_counts.get(risk, 0) + 1
            summary['risk_distribution'] = risk_counts
            
            return summary
            
        except Exception as e:
            logger.error(f"計算統計摘要時發生錯誤: {e}")
            return {}

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
        # 優先使用 config.py 定義的 STOCK_DATA_DIR
        data_files = glob.glob(os.path.join(STOCK_DATA_DIR, "latest_stock_data_*.json"))
        # fallback: try relative path from project root
        if not data_files:
            data_files = glob.glob(os.path.join(os.path.dirname(__file__), "data", "stock_data", "latest_stock_data_*.json"))
        # fallback: try current directory
        if not data_files:
            data_files = glob.glob("latest_stock_data_*.json")
        
        if not data_files:
            logger.error("找不到股票數據文件（已在 STOCK_DATA_DIR 及當前目錄尋找）")
            return
        
        data_file = max(data_files)
    
    logger.info(f"使用數據文件: {data_file}")
    
    # 創建技術分析器
    analyzer = TechnicalAnalyzer(data_file)
    
    # 進行技術和籌碼面分析
    analysis_results = analyzer.analyze_all_stocks()
    
    # 保存分析結果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"technical_analysis_report_{timestamp}.json"
    output_filepath = os.path.join(TECHNICAL_ANALYSIS_DIR, output_file)
    
    with open(output_filepath, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"技術分析報告已保存: {output_filepath}")
    
    # 顯示摘要
    print("\n=== 技術面和籌碼面分析摘要 ===")
    
    summary = analysis_results.get('summary_statistics', {})
    
    if summary.get('limit_up_summary'):
        limit_summary = summary['limit_up_summary']
        print(f"漲停股票分析: {limit_summary['count']} 檔")
        print(f"平均評分: {limit_summary['avg_score']:.2f}")
        print(f"最高評分: {limit_summary['max_score']:.2f}")
    
    if summary.get('strong_stocks_summary'):
        strong_summary = summary['strong_stocks_summary']
        print(f"強勢股票分析: {strong_summary['count']} 檔")
        print(f"平均評分: {strong_summary['avg_score']:.2f}")
        print(f"最高評分: {strong_summary['max_score']:.2f}")
    
    if summary.get('rating_distribution'):
        print(f"\n評級分布:")
        for rating, count in summary['rating_distribution'].items():
            print(f"  {rating}: {count} 檔")
    
    if summary.get('risk_distribution'):
        print(f"\n風險分布:")
        for risk, count in summary['risk_distribution'].items():
            print(f"  {risk}: {count} 檔")
    
    # 顯示前5名推薦股票
    all_stocks = analysis_results['limit_up_analysis'] + analysis_results['strong_stocks_analysis']
    top_stocks = sorted(all_stocks, key=lambda x: x['rating']['total_score'], reverse=True)[:5]
    
    print(f"\n=== 前5名推薦股票 ===")
    for i, stock in enumerate(top_stocks, 1):
        stock_info = stock['stock_info']
        rating = stock['rating']
        print(f"{i}. {stock_info['Name']} ({stock_info['Code']})")
        print(f"   評分: {rating['total_score']:.2f} | 評級: {rating['rating']} | 建議: {rating['recommendation']}")
        print(f"   風險: {rating['risk_level']} | 漲幅: {stock_info['ChangePercent']:.2f}%")
    
    print(f"\n完整技術分析報告: {output_filepath}")

if __name__ == "__main__":
    main()

