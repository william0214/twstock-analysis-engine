#!/usr/bin/env python3
"""
多智能體分析框架
引入技術、籌碼、族群、風險四大智能體進行協作分析和辯論
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BaseAgent:
    """智能體基類"""
    
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.confidence = 0.0
        self.reasoning = []
    
    def analyze(self, stock_data: Dict) -> Dict:
        """分析股票（由子類實現）"""
        raise NotImplementedError
    
    def get_opinion(self) -> str:
        """獲取觀點（看多/看空/中性）"""
        if self.confidence > 0.6:
            return "看多"
        elif self.confidence < 0.4:
            return "看空"
        else:
            return "中性"


class TechnicalAgent(BaseAgent):
    """技術分析智能體"""
    
    def __init__(self):
        super().__init__("技術分析師", "分析價格走勢、技術指標、動能")
        
    def analyze(self, stock_data: Dict) -> Dict:
        """
        技術面分析
        
        Args:
            stock_data: 股票數據
            
        Returns:
            Dict: 技術分析結果
        """
        self.reasoning = []
        score = 0
        max_score = 100
        
        try:
            # 1. 價格動能 (30分)
            change_percent = float(stock_data.get('ChangePercent', 0))
            if change_percent >= 9:
                score += 30
                self.reasoning.append(f"✓ 強勁漲勢 {change_percent:.2f}%，接近漲停")
            elif change_percent >= 7:
                score += 25
                self.reasoning.append(f"✓ 明顯上漲 {change_percent:.2f}%，動能強勁")
            elif change_percent >= 5:
                score += 20
                self.reasoning.append(f"✓ 穩健上漲 {change_percent:.2f}%")
            elif change_percent >= 3:
                score += 15
                self.reasoning.append(f"○ 溫和上漲 {change_percent:.2f}%")
            else:
                score += 5
                self.reasoning.append(f"✗ 漲幅較小 {change_percent:.2f}%，動能不足")
            
            # 2. 價格位置 (20分)
            open_price = float(stock_data.get('OpeningPrice', 0))
            high_price = float(stock_data.get('HighestPrice', 0))
            low_price = float(stock_data.get('LowestPrice', 0))
            close_price = float(stock_data.get('ClosingPrice', 0))
            
            if high_price > low_price:
                price_position = (close_price - low_price) / (high_price - low_price)
                if price_position >= 0.9:
                    score += 20
                    self.reasoning.append("✓ 收盤接近最高價，強勢態勢")
                elif price_position >= 0.7:
                    score += 15
                    self.reasoning.append("✓ 收盤價位偏高，多方掌控")
                elif price_position >= 0.5:
                    score += 10
                    self.reasoning.append("○ 收盤價位中等")
                else:
                    score += 5
                    self.reasoning.append("✗ 收盤價位偏低，上影線較長")
            
            # 3. 成交量能 (25分)
            volume = float(stock_data.get('TradeVolume', 0))
            if volume >= 5000000:  # 500萬股以上
                score += 25
                self.reasoning.append(f"✓ 成交量充沛 {volume/10000:.1f}萬股，資金活躍")
            elif volume >= 2000000:  # 200萬股以上
                score += 20
                self.reasoning.append(f"✓ 成交量良好 {volume/10000:.1f}萬股")
            elif volume >= 1000000:  # 100萬股以上
                score += 15
                self.reasoning.append(f"○ 成交量尚可 {volume/10000:.1f}萬股")
            else:
                score += 5
                self.reasoning.append(f"✗ 成交量不足 {volume/10000:.1f}萬股，流動性風險")
            
            # 4. 波動度評估 (15分)
            if open_price > 0:
                volatility = ((high_price - low_price) / open_price) * 100
                if 3 <= volatility <= 10:
                    score += 15
                    self.reasoning.append(f"✓ 波動度適中 {volatility:.2f}%")
                elif volatility < 3:
                    score += 10
                    self.reasoning.append(f"○ 波動度較小 {volatility:.2f}%")
                else:
                    score += 5
                    self.reasoning.append(f"⚠ 波動度較大 {volatility:.2f}%，注意風險")
            
            # 5. 量價配合 (10分)
            if change_percent > 5 and volume > 2000000:
                score += 10
                self.reasoning.append("✓ 量價齊揚，突破態勢明確")
            elif change_percent > 3 and volume > 1000000:
                score += 7
                self.reasoning.append("○ 量價配合尚可")
            else:
                score += 3
                self.reasoning.append("○ 量價配合一般")
            
            # 計算信心度
            self.confidence = score / max_score
            
            return {
                'agent': self.name,
                'score': score,
                'max_score': max_score,
                'confidence': self.confidence,
                'opinion': self.get_opinion(),
                'reasoning': self.reasoning,
                'weight': 0.35  # 技術面權重35%
            }
            
        except Exception as e:
            logger.error(f"技術分析失敗: {e}")
            return {
                'agent': self.name,
                'score': 0,
                'max_score': max_score,
                'confidence': 0,
                'opinion': "無法分析",
                'reasoning': [f"分析錯誤: {str(e)}"],
                'weight': 0.35
            }


class ChipAgent(BaseAgent):
    """籌碼分析智能體"""
    
    def __init__(self):
        super().__init__("籌碼分析師", "分析主力動向、籌碼集中度")
    
    def analyze(self, stock_data: Dict, dealer_data: Optional[Dict] = None) -> Dict:
        """
        籌碼面分析
        
        Args:
            stock_data: 股票數據
            dealer_data: 三大法人數據（可選）
            
        Returns:
            Dict: 籌碼分析結果
        """
        self.reasoning = []
        score = 0
        max_score = 100
        
        try:
            # 1. 成交筆數分析 (30分)
            transaction = float(stock_data.get('Transaction', 0))
            volume = float(stock_data.get('TradeVolume', 0))
            
            if transaction > 0 and volume > 0:
                avg_per_trade = volume / transaction
                if avg_per_trade >= 10000:  # 單筆萬股以上
                    score += 30
                    self.reasoning.append(f"✓ 大額交易活躍，單筆{avg_per_trade:.0f}股，主力進場跡象")
                elif avg_per_trade >= 5000:
                    score += 25
                    self.reasoning.append(f"✓ 中大戶參與，單筆{avg_per_trade:.0f}股")
                elif avg_per_trade >= 2000:
                    score += 20
                    self.reasoning.append(f"○ 散戶為主，單筆{avg_per_trade:.0f}股")
                else:
                    score += 10
                    self.reasoning.append(f"○ 小額交易為主，單筆{avg_per_trade:.0f}股")
            
            # 2. 成交值分析 (25分)
            trade_value = float(stock_data.get('TradeValue', 0))
            if trade_value >= 100000000:  # 1億以上
                score += 25
                self.reasoning.append(f"✓ 成交值充裕 {trade_value/100000000:.2f}億，資金充沛")
            elif trade_value >= 50000000:  # 5000萬以上
                score += 20
                self.reasoning.append(f"✓ 成交值良好 {trade_value/10000000:.1f}千萬")
            elif trade_value >= 20000000:  # 2000萬以上
                score += 15
                self.reasoning.append(f"○ 成交值尚可 {trade_value/10000000:.1f}千萬")
            else:
                score += 5
                self.reasoning.append(f"✗ 成交值偏低 {trade_value/10000000:.1f}千萬")
            
            # 3. 三大法人買賣超 (25分) - 如果有數據
            if dealer_data:
                foreign = dealer_data.get('foreign', 0)
                trust = dealer_data.get('trust', 0)
                total = dealer_data.get('total', 0)
                
                if total > 1000:
                    score += 25
                    self.reasoning.append(f"✓ 法人大舉買超 {total/1000:.1f}張")
                elif total > 500:
                    score += 20
                    self.reasoning.append(f"✓ 法人買超 {total/1000:.1f}張")
                elif total > 0:
                    score += 15
                    self.reasoning.append(f"○ 法人小幅買超 {total/1000:.1f}張")
                elif total > -500:
                    score += 10
                    self.reasoning.append(f"○ 法人小幅賣超 {abs(total)/1000:.1f}張")
                else:
                    score += 5
                    self.reasoning.append(f"✗ 法人大舉賣超 {abs(total)/1000:.1f}張")
            else:
                # 無法人數據時，此項給予基準分
                score += 15
                self.reasoning.append("○ 無三大法人數據")
            
            # 4. 流動性評估 (20分)
            if volume >= 2000000:
                score += 20
                self.reasoning.append("✓ 流動性佳，進出容易")
            elif volume >= 1000000:
                score += 15
                self.reasoning.append("○ 流動性尚可")
            else:
                score += 5
                self.reasoning.append("⚠ 流動性不足，進出需謹慎")
            
            # 計算信心度
            self.confidence = score / max_score
            
            return {
                'agent': self.name,
                'score': score,
                'max_score': max_score,
                'confidence': self.confidence,
                'opinion': self.get_opinion(),
                'reasoning': self.reasoning,
                'weight': 0.30  # 籌碼面權重30%
            }
            
        except Exception as e:
            logger.error(f"籌碼分析失敗: {e}")
            return {
                'agent': self.name,
                'score': 0,
                'max_score': max_score,
                'confidence': 0,
                'opinion': "無法分析",
                'reasoning': [f"分析錯誤: {str(e)}"],
                'weight': 0.30
            }


class SectorAgent(BaseAgent):
    """族群分析智能體"""
    
    def __init__(self):
        super().__init__("族群分析師", "分析產業輪動、族群強勢")
    
    def analyze(self, stock_data: Dict, sector_momentum: Optional[Dict] = None) -> Dict:
        """
        族群面分析
        
        Args:
            stock_data: 股票數據
            sector_momentum: 族群動能數據（可選）
            
        Returns:
            Dict: 族群分析結果
        """
        self.reasoning = []
        score = 0
        max_score = 100
        
        try:
            # 從 stock_data 獲取產業資訊
            industry = stock_data.get('IndustryName', stock_data.get('industry', '未知'))
            
            # 1. 族群輪動狀態 (40分)
            if sector_momentum:
                sector_rank = sector_momentum.get('rank', 999)
                sector_change = sector_momentum.get('avg_change', 0)
                is_leading = sector_momentum.get('is_leading', False)
                
                if sector_rank <= 3 and is_leading:
                    score += 40
                    self.reasoning.append(f"✓ {industry} 為領漲族群(第{sector_rank}名)，族群輪動進行中")
                elif sector_rank <= 5:
                    score += 35
                    self.reasoning.append(f"✓ {industry} 表現優異(第{sector_rank}名)，資金關注度高")
                elif sector_rank <= 10:
                    score += 25
                    self.reasoning.append(f"○ {industry} 表現良好(第{sector_rank}名)")
                else:
                    score += 10
                    self.reasoning.append(f"○ {industry} 表現一般(第{sector_rank}名)")
            else:
                # 無族群數據時給予基準分
                score += 20
                self.reasoning.append(f"○ {industry} 族群，無詳細族群動能數據")
            
            # 2. 個股在族群中的地位 (30分)
            change_percent = float(stock_data.get('ChangePercent', 0))
            volume = float(stock_data.get('TradeVolume', 0))
            
            if sector_momentum:
                sector_avg_change = sector_momentum.get('avg_change', 0)
                is_sector_leader = change_percent > sector_avg_change * 1.2
                
                if is_sector_leader and volume > 2000000:
                    score += 30
                    self.reasoning.append(f"✓ 族群內領頭羊，漲幅({change_percent:.2f}%)遠超族群平均")
                elif is_sector_leader:
                    score += 25
                    self.reasoning.append(f"✓ 族群內強勢股，表現優於族群")
                elif change_percent >= sector_avg_change:
                    score += 20
                    self.reasoning.append(f"○ 與族群同步上漲")
                else:
                    score += 10
                    self.reasoning.append(f"○ 漲幅落後族群平均")
            else:
                # 無族群數據時，根據絕對漲幅評估
                if change_percent >= 7:
                    score += 25
                    self.reasoning.append("✓ 個股漲幅優異")
                elif change_percent >= 5:
                    score += 20
                    self.reasoning.append("○ 個股漲幅良好")
                else:
                    score += 15
                    self.reasoning.append("○ 個股漲幅尚可")
            
            # 3. 產業政策支持 (15分)
            # 特定產業加分（半導體、AI、電動車等政策支持產業）
            hot_sectors = ['半導體業', '電腦及週邊設備業', '光電業', '電子零組件業']
            if industry in hot_sectors:
                score += 15
                self.reasoning.append(f"✓ {industry} 為政策支持產業")
            else:
                score += 8
                self.reasoning.append(f"○ {industry} 產業")
            
            # 4. 族群資金流入 (15分)
            if sector_momentum:
                sector_volume_rank = sector_momentum.get('volume_rank', 999)
                if sector_volume_rank <= 5:
                    score += 15
                    self.reasoning.append(f"✓ 族群成交量居前(第{sector_volume_rank}名)，資金持續流入")
                elif sector_volume_rank <= 10:
                    score += 10
                    self.reasoning.append(f"○ 族群成交量良好")
                else:
                    score += 5
                    self.reasoning.append(f"○ 族群成交量一般")
            else:
                score += 8
                self.reasoning.append("○ 無族群資金流向數據")
            
            # 計算信心度
            self.confidence = score / max_score
            
            return {
                'agent': self.name,
                'score': score,
                'max_score': max_score,
                'confidence': self.confidence,
                'opinion': self.get_opinion(),
                'reasoning': self.reasoning,
                'weight': 0.25  # 族群面權重25%
            }
            
        except Exception as e:
            logger.error(f"族群分析失敗: {e}")
            return {
                'agent': self.name,
                'score': 0,
                'max_score': max_score,
                'confidence': 0,
                'opinion': "無法分析",
                'reasoning': [f"分析錯誤: {str(e)}"],
                'weight': 0.25
            }


class RiskAgent(BaseAgent):
    """風險管理智能體"""
    
    def __init__(self):
        super().__init__("風險管理師", "評估投資風險、制定風控策略")
    
    def analyze(self, stock_data: Dict) -> Dict:
        """
        風險面分析
        
        Args:
            stock_data: 股票數據
            
        Returns:
            Dict: 風險分析結果
        """
        self.reasoning = []
        score = 100  # 風險評分：100分最低風險，0分最高風險
        max_score = 100
        risk_factors = []
        
        try:
            # 1. 波動風險 (30分)
            open_price = float(stock_data.get('OpeningPrice', 0))
            high_price = float(stock_data.get('HighestPrice', 0))
            low_price = float(stock_data.get('LowestPrice', 0))
            close_price = float(stock_data.get('ClosingPrice', 0))
            
            if open_price > 0:
                volatility = ((high_price - low_price) / open_price) * 100
                if volatility > 15:
                    score -= 30
                    risk_factors.append(f"✗ 波動度過高 {volatility:.2f}%，風險極大")
                elif volatility > 10:
                    score -= 20
                    risk_factors.append(f"⚠ 波動度較大 {volatility:.2f}%，需謹慎")
                elif volatility > 7:
                    score -= 10
                    risk_factors.append(f"○ 波動度中等 {volatility:.2f}%")
                else:
                    self.reasoning.append(f"✓ 波動度適中 {volatility:.2f}%，風險可控")
            
            # 2. 流動性風險 (25分)
            volume = float(stock_data.get('TradeVolume', 0))
            if volume < 500000:
                score -= 25
                risk_factors.append(f"✗ 成交量極低 {volume/10000:.1f}萬股，流動性風險高")
            elif volume < 1000000:
                score -= 15
                risk_factors.append(f"⚠ 成交量偏低 {volume/10000:.1f}萬股，流動性不足")
            elif volume < 2000000:
                score -= 5
                risk_factors.append(f"○ 成交量尚可 {volume/10000:.1f}萬股")
            else:
                self.reasoning.append(f"✓ 成交量充足 {volume/10000:.1f}萬股，流動性佳")
            
            # 3. 價格風險 (20分)
            change_percent = float(stock_data.get('ChangePercent', 0))
            if change_percent >= 9.5:
                score -= 20
                risk_factors.append(f"⚠ 已接近漲停 {change_percent:.2f}%，追高風險大")
            elif change_percent >= 8:
                score -= 10
                risk_factors.append(f"○ 漲幅較大 {change_percent:.2f}%，追高需謹慎")
            elif change_percent >= 3:
                self.reasoning.append(f"✓ 漲幅合理 {change_percent:.2f}%")
            else:
                score -= 5
                risk_factors.append(f"○ 漲幅較小，動能不足")
            
            # 4. 市值風險 (15分)
            market_value = float(stock_data.get('MarketValue', 0))
            if market_value < 500000000:  # 5億以下
                score -= 15
                risk_factors.append(f"✗ 超小型股，市值僅{market_value/100000000:.2f}億")
            elif market_value < 2000000000:  # 20億以下
                score -= 10
                risk_factors.append(f"⚠ 小型股，市值{market_value/100000000:.2f}億")
            elif market_value < 5000000000:  # 50億以下
                score -= 5
                risk_factors.append(f"○ 中小型股，市值{market_value/100000000:.2f}億")
            else:
                self.reasoning.append(f"✓ 市值規模適中 {market_value/100000000:.2f}億")
            
            # 5. 位階風險 (10分)
            price_position = 0.5
            if high_price > low_price:
                price_position = (close_price - low_price) / (high_price - low_price)
            
            if price_position < 0.3:
                score -= 10
                risk_factors.append("⚠ 收在低檔，多方力道不足")
            elif price_position < 0.5:
                score -= 5
                risk_factors.append("○ 收盤位置偏低")
            else:
                self.reasoning.append("✓ 收盤位置佳")
            
            # 建議停損點
            suggested_stop_loss = close_price * (1 - self._calculate_stop_loss_ratio(volatility, market_value))
            self.reasoning.append(f"📍 建議停損價: {suggested_stop_loss:.2f} 元")
            
            # 計算信心度（風險越低信心越高）
            self.confidence = max(0, score / max_score)
            
            # 綜合所有風險因素
            all_info = risk_factors + self.reasoning
            
            return {
                'agent': self.name,
                'score': score,
                'max_score': max_score,
                'confidence': self.confidence,
                'opinion': "低風險" if score >= 70 else ("中風險" if score >= 50 else "高風險"),
                'reasoning': all_info,
                'risk_level': self._get_risk_level(score),
                'stop_loss_price': suggested_stop_loss,
                'weight': 0.10  # 風險面權重10%
            }
            
        except Exception as e:
            logger.error(f"風險分析失敗: {e}")
            return {
                'agent': self.name,
                'score': 0,
                'max_score': max_score,
                'confidence': 0,
                'opinion': "無法分析",
                'reasoning': [f"分析錯誤: {str(e)}"],
                'risk_level': "未知",
                'weight': 0.10
            }
    
    def _calculate_stop_loss_ratio(self, volatility: float, market_value: float) -> float:
        """
        根據波動度和市值計算停損比例
        
        Args:
            volatility: 波動度
            market_value: 市值
            
        Returns:
            float: 停損比例
        """
        base_ratio = 0.07  # 基礎7%
        
        # 根據波動度調整
        if volatility > 10:
            base_ratio += 0.03
        elif volatility < 5:
            base_ratio -= 0.02
        
        # 根據市值調整
        if market_value < 1000000000:  # 10億以下
            base_ratio += 0.03
        elif market_value > 10000000000:  # 100億以上
            base_ratio -= 0.02
        
        return min(0.15, max(0.05, base_ratio))  # 限制在5%-15%
    
    def _get_risk_level(self, score: float) -> str:
        """獲取風險等級"""
        if score >= 80:
            return "低風險"
        elif score >= 60:
            return "中低風險"
        elif score >= 40:
            return "中風險"
        elif score >= 20:
            return "中高風險"
        else:
            return "高風險"


class MultiAgentAnalyzer:
    """多智能體分析器（統籌）"""
    
    def __init__(self):
        self.technical_agent = TechnicalAgent()
        self.chip_agent = ChipAgent()
        self.sector_agent = SectorAgent()
        self.risk_agent = RiskAgent()
        
    def analyze_stock(self, stock_data: Dict, 
                     dealer_data: Optional[Dict] = None,
                     sector_momentum: Optional[Dict] = None) -> Dict:
        """
        執行完整的多智能體分析
        
        Args:
            stock_data: 股票數據
            dealer_data: 三大法人數據
            sector_momentum: 族群動能數據
            
        Returns:
            Dict: 綜合分析結果
        """
        logger.info(f"開始多智能體分析: {stock_data.get('Code', 'N/A')} {stock_data.get('Name', '')}")
        
        # 各智能體進行分析
        technical_result = self.technical_agent.analyze(stock_data)
        chip_result = self.chip_agent.analyze(stock_data, dealer_data)
        sector_result = self.sector_agent.analyze(stock_data, sector_momentum)
        risk_result = self.risk_agent.analyze(stock_data)
        
        # 計算加權總分
        weighted_score = (
            technical_result['score'] * technical_result['weight'] +
            chip_result['score'] * chip_result['weight'] +
            sector_result['score'] * sector_result['weight'] +
            risk_result['score'] * risk_result['weight']
        )
        
        # 辯論機制：如果智能體意見分歧嚴重，進行二次評估
        opinions = [
            technical_result['opinion'],
            chip_result['opinion'],
            sector_result['opinion']
        ]
        
        # 計算意見一致性
        bullish_count = opinions.count("看多")
        bearish_count = opinions.count("看空")
        consensus = "強烈看多" if bullish_count >= 3 else (
            "看多" if bullish_count >= 2 else (
            "看空" if bearish_count >= 2 else "中性"
            )
        )
        
        # 評級判定（基於優化後的門檻）
        if weighted_score >= 85 and risk_result['score'] >= 60:
            rating = 'A+'
        elif weighted_score >= 75 and risk_result['score'] >= 50:
            rating = 'A'
        elif weighted_score >= 65 and risk_result['score'] >= 40:
            rating = 'B+'
        elif weighted_score >= 55:
            rating = 'B'
        else:
            rating = 'C'
        
        return {
            'stock_code': stock_data.get('Code', ''),
            'stock_name': stock_data.get('Name', ''),
            'weighted_score': round(weighted_score, 2),
            'rating': rating,
            'consensus': consensus,
            'agents_analysis': {
                'technical': technical_result,
                'chip': chip_result,
                'sector': sector_result,
                'risk': risk_result
            },
            'recommendation': self._generate_recommendation(
                weighted_score, consensus, risk_result
            )
        }
    
    def _generate_recommendation(self, score: float, consensus: str, risk_result: Dict) -> str:
        """生成投資建議"""
        if score >= 85 and consensus in ["強烈看多", "看多"] and risk_result['score'] >= 60:
            return "強力推薦：多項指標優異，建議分批進場"
        elif score >= 75 and consensus == "看多":
            return "推薦買入：表現良好，建議適度配置"
        elif score >= 65:
            return "謹慎買入：尚可關注，建議小額試單"
        elif score >= 55:
            return "觀望：表現平平，建議持續追蹤"
        else:
            return "不建議：指標偏弱，建議觀望"


if __name__ == '__main__':
    # 測試程式
    print("=== 多智能體分析框架測試 ===\n")
    
    # 模擬股票數據
    test_stock = {
        'Code': '2330',
        'Name': '台積電',
        'ChangePercent': 8.5,
        'OpeningPrice': 580,
        'HighestPrice': 595,
        'LowestPrice': 578,
        'ClosingPrice': 593,
        'TradeVolume': 35000000,
        'TradeValue': 20650000000,
        'Transaction': 28000,
        'MarketValue': 15360000000000,
        'IndustryName': '半導體業'
    }
    
    analyzer = MultiAgentAnalyzer()
    result = analyzer.analyze_stock(test_stock)
    
    print(f"股票: {result['stock_name']} ({result['stock_code']})")
    print(f"綜合評分: {result['weighted_score']:.2f}")
    print(f"評級: {result['rating']}")
    print(f"智能體共識: {result['consensus']}")
    print(f"投資建議: {result['recommendation']}\n")
    
    print("=== 各智能體分析詳情 ===")
    for agent_name, agent_result in result['agents_analysis'].items():
        print(f"\n【{agent_result['agent']}】")
        print(f"評分: {agent_result['score']}/{agent_result['max_score']}")
        print(f"觀點: {agent_result['opinion']}")
        print(f"推理過程:")
        for reason in agent_result['reasoning']:
            print(f"  {reason}")
