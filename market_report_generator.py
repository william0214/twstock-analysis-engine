#!/usr/bin/env python3
"""
市場分析報告生成器
整合所有分析結果，生成綜合的市場分析報告和投資建議
"""

import json
import os
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List
import glob
from config import STOCK_DATA_DIR, TECHNICAL_ANALYSIS_DIR, MARKET_ANALYSIS_DIR

# 報告版本資訊
REPORT_VERSION = "第2版"

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarketReportGenerator:
    """市場分析報告生成器"""
    
    def __init__(self):
        """初始化報告生成器"""
        # 優先嘗試載入 API 產生的 latest_analysis.json，確保報表與 API 一致
        api_data = self.load_latest_api_data()
        if api_data:
            self.stock_data = api_data
            # 若載入 API 資料，進行欄位正規化
            self._normalize_api_records()
        else:
            self.stock_data = self.load_latest_stock_data()
        self.analysis_data = self.load_latest_analysis_data()
        self.technical_data = self.load_latest_technical_data()
        # 確保 small_cap 欄位存在且一致
        self._ensure_small_cap_fields()
        # 載入統計數據 (final_recommendations)
        self.statistics_data = self.load_latest_statistics_data()

    def load_latest_statistics_data(self) -> Dict:
        """載入最新 statistics report (包含 final_recommendations)"""
        try:
            stats_files = glob.glob(os.path.join(MARKET_ANALYSIS_DIR, '..', 'reports', 'statistics', 'statistics_report_*.json'))
            # try alternative folder
            stats_files = glob.glob(os.path.join('reports', 'statistics', 'statistics_report_*.json')) if not stats_files else stats_files
            if not stats_files:
                logger.warning('找不到 statistics report 檔案')
                return {}
            latest = max(stats_files)
            with open(latest, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f'載入統計數據: {latest}')
            return data
        except Exception as e:
            logger.error(f'載入統計數據失敗: {e}')
            return {}

    def load_latest_api_data(self) -> Dict:
        """若存在 latest_analysis.json，載入並回傳（用於使報表與 API 一致）"""
        try:
            api_file = os.path.join(os.getcwd(), 'latest_analysis.json')
            if os.path.exists(api_file):
                with open(api_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"載入 API 資料: {api_file}")
                # API 的結構與原本 stock_data 可能不同，但報表使用的字段（small_cap_limit_up / small_cap_strong）會存在
                return data
            return {}
        except Exception as e:
            logger.error(f"載入 latest_analysis.json 失敗: {e}")
            return {}

    def _ensure_small_cap_fields(self, market_cap_threshold: float = 10000000000):
        """如果 stock_data 中缺少 small_cap_limit_up / small_cap_strong，從 limit_up_stocks / strong_stocks 計算之"""
        try:
            if not self.stock_data:
                return

            # 若已存在且為非空列表，則跳過
            if self.stock_data.get('small_cap_limit_up') and self.stock_data.get('small_cap_strong'):
                return

            # 從 limit_up_stocks 計算小型股漲停
            limit_up = self.stock_data.get('limit_up_stocks', [])
            strong = self.stock_data.get('strong_stocks', [])

            def filter_small(items):
                res = []
                for s in items:
                    mv = s.get('MarketValue')
                    if mv is None:
                        # 嘗試計算 MarketValue
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
            logger.info(f"自動產生 small_cap fields: {len(self.stock_data['small_cap_limit_up'])} 漲停 / {len(self.stock_data['small_cap_strong'])} 強勢")
        except Exception as e:
            logger.error(f"確保 small_cap 欄位時發生錯誤: {e}")

    def _normalize_api_records(self):
        """若 self.stock_data 來源為 API（欄位使用小寫），將欄位轉換為報表使用的命名。"""
        try:
            if not self.stock_data:
                return
            # detect API style by checking keys in first limit_up entry
            sample = None
            if isinstance(self.stock_data.get('limit_up_stocks'), list) and self.stock_data['limit_up_stocks']:
                sample = self.stock_data['limit_up_stocks'][0]
            elif isinstance(self.stock_data.get('strong_stocks'), list) and self.stock_data['strong_stocks']:
                sample = self.stock_data['strong_stocks'][0]
            if not sample:
                return

            # If sample uses lowercase 'code' assume API format
            if 'code' in sample:
                def to_report_fields(item):
                    return {
                        'Code': item.get('code'),
                        'Name': item.get('name'),
                        'ClosingPrice': item.get('closing_price') or item.get('ClosingPrice'),
                        'ChangePercent': item.get('change_percent') or item.get('ChangePercent'),
                        'TradeVolume': item.get('volume') or item.get('TradeVolume'),
                        'TradeValue': item.get('value') or item.get('TradeValue'),
                        'MarketValue': item.get('market_value') or item.get('MarketValue'),
                        'Transaction': item.get('transactions') or item.get('Transaction'),
                        'Score': item.get('score') or item.get('Score')
                    }

                if isinstance(self.stock_data.get('limit_up_stocks'), list):
                    self.stock_data['limit_up_stocks'] = [to_report_fields(x) for x in self.stock_data['limit_up_stocks']]
                if isinstance(self.stock_data.get('strong_stocks'), list):
                    self.stock_data['strong_stocks'] = [to_report_fields(x) for x in self.stock_data['strong_stocks']]
                if isinstance(self.stock_data.get('small_cap_limit_up'), list):
                    self.stock_data['small_cap_limit_up'] = [to_report_fields(x) for x in self.stock_data['small_cap_limit_up']]
                if isinstance(self.stock_data.get('small_cap_strong'), list):
                    self.stock_data['small_cap_strong'] = [to_report_fields(x) for x in self.stock_data['small_cap_strong']]
                logger.info('已將 API stock records 正規化為報表格式')
        except Exception as e:
            logger.error(f"正規化 API records 時發生錯誤: {e}")
        
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
    
    def load_latest_analysis_data(self) -> Dict:
        """載入最新分析數據"""
        try:
            analysis_files = glob.glob(os.path.join(TECHNICAL_ANALYSIS_DIR, "stock_analysis_report_*.json"))
            if not analysis_files:
                logger.warning("找不到分析報告文件")
                return {}
            
            latest_file = max(analysis_files)
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"載入分析數據: {latest_file}")
            return data
        except Exception as e:
            logger.error(f"載入分析數據失敗: {e}")
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
    
    def compute_market_breadth(self):
        """計算全市場寬度：4 位數普通股中上漲家數占比（%）。資料不足回傳 None。

        用「訊號日收盤」的全市場資料——報告當天早上即可得的前一交易日收盤，
        不偷看未來。只算 4 位數普通股（濾掉 ETF / 權證等），與回測口徑一致。
        """
        try:
            stocks = self.stock_data.get('all_stocks') if self.stock_data else None
            if not stocks:
                # production 的 self.stock_data 來自 API（latest_analysis.json），
                # 精簡結構不含 all_stocks；退而直接讀最新原始快照計算全市場寬度。
                snap = self.load_latest_stock_data()
                stocks = snap.get('all_stocks') if snap else None
            if not stocks:
                return None
            up = tot = 0
            for s in stocks:
                code = str(s.get('Code', ''))
                if len(code) != 4 or not code[0].isdigit():
                    continue
                try:
                    chg = float(s.get('ChangePercent', 0))
                except (TypeError, ValueError):
                    continue
                tot += 1
                if chg > 0:
                    up += 1
            if tot == 0:
                return None
            return up / tot * 100
        except Exception as e:
            logger.error(f"計算市場寬度時發生錯誤: {e}")
            return None

    def generate_regime_flag(self) -> str:
        """生成市場寬度脈絡（純數字呈現，非訊號）

        原本附有綠/紅燈 go-no-go 建議（寬度≥50% 濾網），但 2025 全年 240 交易日
        walk-forward 檢驗顯示該濾網無法 generalize（綠紅燈勝率無差、分季反覆），
        故移除燈號與回測宣稱，只保留寬度數字作為誠實的行情脈絡。
        """
        breadth = self.compute_market_breadth()
        if breadth is None:
            return ""  # 資料不足則不顯示，不影響其餘報告
        parts = []
        parts.append("## 📊 市場寬度\n\n")
        parts.append(f"- **今日全市場寬度：** {breadth:.1f}%（4 位數普通股上漲家數占比）\n\n")
        parts.append("> 市場寬度反映前一交易日全市場的漲跌家數結構，僅為行情脈絡參考，"
                     "**不構成任何進出場或投資建議**。\n\n")
        parts.append("---\n\n")
        return "".join(parts)

    def generate_executive_summary(self) -> str:
        """生成執行摘要"""
        try:
            summary_parts = []
            
            # 市場概況
            if self.stock_data:
                # 若是 API 資料，total_stocks 在 market_overview 中；否則在根層
                market_overview = self.stock_data.get('market_overview', {})
                total_stocks = market_overview.get('total_stocks', 0) or self.stock_data.get('total_stocks', 0)
                
                # 統計數據優先從 market_overview 讀取，若無則從 statistics 讀取
                if market_overview:
                    statistics = {
                        'limit_up_count': market_overview.get('limit_up_count', 0),
                        'strong_stocks_count': market_overview.get('strong_stocks_count', 0),
                        'small_cap_limit_up_count': market_overview.get('small_cap_limit_up_count', 0),
                        'small_cap_strong_count': market_overview.get('small_cap_strong_count', 0)
                    }
                else:
                    statistics = self.stock_data.get('statistics', {})
                
                summary_parts.append(f"## 執行摘要\n")
                summary_parts.append(f"**分析時間：** {datetime.now().strftime('%Y年%m月%d日 %H:%M')}\n")
                summary_parts.append(f"**分析範圍：** 台股上市公司 {total_stocks} 檔\n\n")
                
                # 市場情緒（優先從 market_overview，再從 market_analysis）
                sentiment = market_overview.get('market_sentiment') or self.stock_data.get('market_analysis', {}).get('market_sentiment', {})
                if sentiment:
                    rising_ratio = sentiment.get('rising_ratio', 0)
                    falling_ratio = sentiment.get('falling_ratio', 0)
                    summary_parts.append(f"**市場情緒：** {'偏多' if rising_ratio > falling_ratio else '偏空' if falling_ratio > rising_ratio else '中性'} (上漲 {rising_ratio}% vs 下跌 {falling_ratio}%)\n")
                
                summary_parts.append(f"**重點發現：**\n")
                summary_parts.append(f"- 漲停股票：{statistics.get('limit_up_count', 0)} 檔\n")
                summary_parts.append(f"- 強勢股票：{statistics.get('strong_stocks_count', 0)} 檔\n")
                summary_parts.append(f"- 小型股漲停：{statistics.get('small_cap_limit_up_count', 0)} 檔\n")
                summary_parts.append(f"- 小型股強勢：{statistics.get('small_cap_strong_count', 0)} 檔\n\n")
            
            # 技術分析摘要
            if self.technical_data.get('summary_statistics'):
                tech_summary = self.technical_data['summary_statistics']
                summary_parts.append(f"**技術分析結果：**\n")
                
                if tech_summary.get('limit_up_summary'):
                    limit_summary = tech_summary['limit_up_summary']
                    summary_parts.append(f"- 漲停股票平均評分：{limit_summary.get('avg_score', 0):.1f}分\n")
                
                if tech_summary.get('strong_stocks_summary'):
                    strong_summary = tech_summary['strong_stocks_summary']
                    summary_parts.append(f"- 強勢股票平均評分：{strong_summary.get('avg_score', 0):.1f}分\n")
                
                if tech_summary.get('rating_distribution'):
                    rating_dist = tech_summary['rating_distribution']
                    a_plus_count = rating_dist.get('A+', 0)
                    a_count = rating_dist.get('A', 0)
                    summary_parts.append(f"- 高評級股票：A+級 {a_plus_count} 檔，A級 {a_count} 檔\n\n")
            
            return "".join(summary_parts)
            
        except Exception as e:
            logger.error(f"生成執行摘要時發生錯誤: {e}")
            return "## 執行摘要\n\n無法生成執行摘要\n\n"
    
    def generate_market_analysis(self) -> str:
        """生成市場分析"""
        try:
            analysis_parts = []
            analysis_parts.append("## 市場分析\n\n")
            
            if self.stock_data.get('market_analysis'):
                market_data = self.stock_data['market_analysis']
                
                # 市場情緒分析
                if market_data.get('market_sentiment'):
                    sentiment = market_data['market_sentiment']
                    analysis_parts.append("### 市場情緒分析\n\n")
                    analysis_parts.append(f"今日台股共有 {sentiment.get('total_stocks', 0)} 檔股票交易，")
                    analysis_parts.append(f"其中上漲股票 {sentiment.get('rising_stocks', 0)} 檔 ({sentiment.get('rising_ratio', 0)}%)，")
                    analysis_parts.append(f"下跌股票 {sentiment.get('falling_stocks', 0)} 檔 ({sentiment.get('falling_ratio', 0)}%)，")
                    analysis_parts.append(f"平盤股票 {sentiment.get('flat_stocks', 0)} 檔。\n\n")
                    
                    # 市場方向判斷
                    rising_ratio = sentiment.get('rising_ratio', 0)
                    if rising_ratio > 55:
                        market_direction = "市場呈現明顯多頭格局，投資情緒樂觀。"
                    elif rising_ratio > 45:
                        market_direction = "市場呈現震盪格局，多空力量相當。"
                    else:
                        market_direction = "市場呈現空頭格局，投資情緒謹慎。"
                    
                    analysis_parts.append(f"{market_direction}\n\n")
                
                # 價格動能分析
                if market_data.get('price_movement'):
                    price_movement = market_data['price_movement']
                    analysis_parts.append("### 價格動能分析\n\n")
                    avg_change = price_movement.get('average_change_percent', 0)
                    analysis_parts.append(f"整體市場平均漲跌幅為 {avg_change:.2f}%，")
                    
                    if avg_change > 1:
                        analysis_parts.append("顯示市場具有正向動能，多方力量較強。\n\n")
                    elif avg_change > -1:
                        analysis_parts.append("市場動能中性，呈現盤整格局。\n\n")
                    else:
                        analysis_parts.append("市場動能偏弱，空方力量較強。\n\n")
                
                # 成交量分析
                if market_data.get('volume_analysis'):
                    volume_data = market_data['volume_analysis']
                    analysis_parts.append("### 成交量分析\n\n")
                    total_volume = volume_data.get('total_volume', 0)
                    avg_volume = volume_data.get('average_volume', 0)
                    
                    analysis_parts.append(f"今日總成交量為 {total_volume:,.0f} 股，")
                    analysis_parts.append(f"平均每檔股票成交量為 {avg_volume:,.0f} 股。")
                    
                    if avg_volume > 2000000:
                        analysis_parts.append("整體成交量活躍，市場參與度高。\n\n")
                    elif avg_volume > 1000000:
                        analysis_parts.append("成交量適中，市場流動性正常。\n\n")
                    else:
                        analysis_parts.append("成交量偏低，市場交投清淡。\n\n")
            
            return "".join(analysis_parts)
            
        except Exception as e:
            logger.error(f"生成市場分析時發生錯誤: {e}")
            return "## 市場分析\n\n無法生成市場分析\n\n"
    
    def generate_limit_up_analysis(self) -> str:
        """生成漲停股票分析"""
        try:
            analysis_parts = []
            analysis_parts.append("## 漲停股票分析\n\n")
            
            if self.stock_data.get('small_cap_limit_up'):
                limit_up_stocks = self.stock_data['small_cap_limit_up']
                analysis_parts.append(f"今日共有 {len(limit_up_stocks)} 檔小型股漲停，顯示市場對小型股的關注度較高。\n\n")
                
                # 漲停股票特徵分析
                if self.analysis_data.get('limit_up_analysis'):
                    limit_analysis = self.analysis_data['limit_up_analysis']
                    basic_stats = limit_analysis.get('basic_stats', {})
                    
                    analysis_parts.append("### 漲停股票特徵\n\n")
                    analysis_parts.append(f"- **平均漲幅：** {basic_stats.get('avg_change_percent', 0):.2f}%\n")
                    analysis_parts.append(f"- **平均成交量：** {basic_stats.get('avg_volume', 0):,.0f} 股\n")
                    analysis_parts.append(f"- **平均市值：** {basic_stats.get('avg_market_value', 0)/100000000:.1f} 億元\n")
                    analysis_parts.append(f"- **總成交金額：** {basic_stats.get('total_trade_value', 0)/100000000:.1f} 億元\n\n")
                
                # 重點漲停股票
                analysis_parts.append("### 重點漲停股票\n\n")
                analysis_parts.append("| 股票代號 | 股票名稱 | 漲幅(%) | 成交量(萬股) | 收盤價(元) |\n")
                analysis_parts.append("|---------|---------|---------|-------------|----------|\n")
                
                for i, stock in enumerate(limit_up_stocks[:10]):
                    analysis_parts.append(f"| {stock['Code']} | {stock['Name']} | {stock['ChangePercent']:.2f} | {stock['TradeVolume']/10000:.0f} | {stock['ClosingPrice']:.2f} |\n")
                
                analysis_parts.append("\n")
            
            return "".join(analysis_parts)
            
        except Exception as e:
            logger.error(f"生成漲停股票分析時發生錯誤: {e}")
            return "## 漲停股票分析\n\n無法生成漲停股票分析\n\n"
    
    def generate_strong_stocks_analysis(self) -> str:
        """生成強勢股票分析"""
        try:
            analysis_parts = []
            analysis_parts.append("## 強勢股票分析\n\n")
            
            if self.stock_data.get('small_cap_strong'):
                strong_stocks = self.stock_data['small_cap_strong']
                analysis_parts.append(f"今日共識別出 {len(strong_stocks)} 檔小型強勢股票，這些股票具有良好的成交量和漲幅表現。\n\n")
                
                # 強勢股票特徵分析
                if self.analysis_data.get('strong_stocks_analysis'):
                    strong_analysis = self.analysis_data['strong_stocks_analysis']
                    basic_stats = strong_analysis.get('basic_stats', {})
                    
                    analysis_parts.append("### 強勢股票特徵\n\n")
                    analysis_parts.append(f"- **平均漲幅：** {basic_stats.get('avg_change_percent', 0):.2f}%\n")
                    analysis_parts.append(f"- **平均成交量：** {basic_stats.get('avg_volume', 0):,.0f} 股\n")
                    analysis_parts.append(f"- **平均評分：** {basic_stats.get('avg_score', 0):.2f}分\n")
                    analysis_parts.append(f"- **平均市值：** {basic_stats.get('avg_market_value', 0)/100000000:.1f} 億元\n\n")
                    
                    # 成長分布
                    if strong_analysis.get('change_distribution'):
                        change_dist = strong_analysis['change_distribution']
                        analysis_parts.append("### 漲幅分布\n\n")
                        analysis_parts.append(f"- **強勢成長 (≥7%)：** {change_dist.get('strong_growth', 0)} 檔\n")
                        analysis_parts.append(f"- **中等成長 (5-7%)：** {change_dist.get('moderate_growth', 0)} 檔\n")
                        analysis_parts.append(f"- **溫和成長 (3-5%)：** {change_dist.get('mild_growth', 0)} 檔\n\n")
                
                # 前10名強勢股票
                analysis_parts.append("### 前10名強勢股票\n\n")
                analysis_parts.append("| 股票代號 | 股票名稱 | 漲幅(%) | 成交量(萬股) | 評分 |\n")
                analysis_parts.append("|---------|---------|---------|-------------|------|\n")
                
                for i, stock in enumerate(strong_stocks[:10]):
                    score = stock.get('Score', 0)
                    analysis_parts.append(f"| {stock['Code']} | {stock['Name']} | {stock['ChangePercent']:.2f} | {stock['TradeVolume']/10000:.0f} | {score:.2f} |\n")
                
                analysis_parts.append("\n")
            
            return "".join(analysis_parts)
            
        except Exception as e:
            logger.error(f"生成強勢股票分析時發生錯誤: {e}")
            return "## 強勢股票分析\n\n無法生成強勢股票分析\n\n"
    
    def generate_technical_analysis_summary(self) -> str:
        """生成技術分析摘要"""
        try:
            analysis_parts = []
            analysis_parts.append("## 技術分析摘要\n\n")
            
            if self.technical_data:
                # 評級分布
                if self.technical_data.get('summary_statistics', {}).get('rating_distribution'):
                    rating_dist = self.technical_data['summary_statistics']['rating_distribution']
                    analysis_parts.append("### 評級分布\n\n")
                    
                    total_analyzed = sum(rating_dist.values())
                    for rating in ['A+', 'A', 'B+', 'B', 'C+', 'C', 'D']:
                        count = rating_dist.get(rating, 0)
                        if count > 0:
                            percentage = (count / total_analyzed) * 100
                            analysis_parts.append(f"- **{rating}級：** {count} 檔 ({percentage:.1f}%)\n")
                    
                    analysis_parts.append("\n")
                
                # 風險分布
                if self.technical_data.get('summary_statistics', {}).get('risk_distribution'):
                    risk_dist = self.technical_data['summary_statistics']['risk_distribution']
                    analysis_parts.append("### 風險分布\n\n")
                    
                    for risk_level in ['低風險', '中風險', '高風險']:
                        count = risk_dist.get(risk_level, 0)
                        if count > 0:
                            analysis_parts.append(f"- **{risk_level}：** {count} 檔\n")
                    
                    analysis_parts.append("\n")
                
                # 技術指標分析
                analysis_parts.append("### 技術指標分析\n\n")
                analysis_parts.append("基於技術面和籌碼面的綜合分析，我們對每檔股票進行了多維度評估：\n\n")
                analysis_parts.append("- **動能分析：** 結合價格動能、位置動能和成交量動能\n")
                analysis_parts.append("- **相對強度：** 評估股票相對於市場的表現\n")
                analysis_parts.append("- **流動性評估：** 分析成交量和交易活躍度\n")
                analysis_parts.append("- **籌碼分析：** 評估投資人行為和籌碼集中度\n")
                analysis_parts.append("- **風險評估：** 綜合考量各種風險因子\n\n")
            
            return "".join(analysis_parts)
            
        except Exception as e:
            logger.error(f"生成技術分析摘要時發生錯誤: {e}")
            return "## 技術分析摘要\n\n無法生成技術分析摘要\n\n"
    
    def generate_investment_recommendations(self) -> str:
        """生成投資建議"""
        try:
            recommendations = []
            recommendations.append("## 投資建議\n\n")
            
            # 優先使用 statistics report 的 final_recommendations（若存在），以確保與 API recommendations 一致
            final_recs = []
            if self.statistics_data.get('final_recommendations'):
                final_recs = self.statistics_data['final_recommendations']
            elif self.stock_data.get('recommendations'):
                final_recs = self.stock_data['recommendations']
            else:
                # fallback: 從技術分析中擷取
                final_recs = []
                top_stocks = self.get_top_recommended_stocks(10)
                for s in top_stocks:
                    rec = {
                        'rank': None,
                        'code': s['stock_info']['Code'],
                        'name': s['stock_info']['Name'],
                        'closing_price': s['stock_info'].get('ClosingPrice', 0),
                        'change_percent': s['stock_info'].get('ChangePercent', 0),
                        'market_value': s['stock_info'].get('MarketValue', 0),
                        'total_score': s['rating']['total_score'],
                        'rating': s['rating']['rating'],
                        'recommendation': s['rating'].get('recommendation', ''),
                        'risk_level': s['rating'].get('risk_level', ''),
                        'key_strengths': s['rating'].get('key_strengths', []),
                        'key_risks': s['rating'].get('key_risks', [])
                    }
                    final_recs.append(rec)

            # prepare top_stocks for detailed reasons (fallback to technical ranking)
            top_stocks = self.get_top_recommended_stocks(5)
            if final_recs:
                recommendations.append("### 重點推薦股票\n\n")
                recommendations.append("基於技術面、籌碼面和基本面的綜合分析，以下為重點推薦的小型股：\n\n")
                
                recommendations.append("| 排名 | 股票代號 | 股票名稱 | 評級 | 評分 | 建議 | 風險等級 | 漲幅(%) |\n")
                recommendations.append("|------|---------|---------|------|------|------|----------|--------|\n")

                for i, rec in enumerate(final_recs[:10], 1):
                    recommendations.append(f"| {i} | {rec.get('code')} | {rec.get('name')} | {rec.get('rating')} | {rec.get('total_score', rec.get('recommendation_score',0)):.1f} | {rec.get('recommendation')} | {rec.get('risk_level')} | {rec.get('change_percent',0):.2f} |\n")

                recommendations.append("\n")
                
                # === B+ 級推薦區塊 ===
                # 從技術分析數據中提取 B+ 級股票（因為 final_recommendations 只包含 A 級以上）
                b_plus_recs = []
                if self.technical_data:
                    all_analyzed_stocks = []
                    for section in ['limit_up_analysis', 'strong_stocks_analysis', 'potential_stocks_analysis']:
                        all_analyzed_stocks.extend(self.technical_data.get(section, []))
                    
                    for stock in all_analyzed_stocks:
                        rating_info = stock.get('rating', {})
                        if rating_info.get('rating') == 'B+':
                            stock_info = stock.get('stock_info', {})
                            rec = {
                                'code': stock_info.get('Code'),
                                'name': stock_info.get('Name'),
                                'rating': 'B+',
                                'total_score': rating_info.get('total_score', 0),
                                'recommendation': rating_info.get('recommendation', ''),
                                'risk_level': rating_info.get('risk_level', ''),
                                'closing_price': stock_info.get('ClosingPrice', 0),
                                'trade_volume': stock_info.get('TradeVolume', 0),
                                'change_percent': stock_info.get('ChangePercent', 0)
                            }
                            b_plus_recs.append(rec)
                    
                    # 按評分排序
                    b_plus_recs.sort(key=lambda x: x.get('total_score', 0), reverse=True)
                
                if b_plus_recs:
                    recommendations.append("---\n\n")
                    recommendations.append("### 🎯 B+ 級推薦\n\n")
                    recommendations.append("> B+ 級為技術面剛轉強、但尚未達 A/A+ 門檻的標的，市場關注度通常較低。\n")
                    recommendations.append("> **本系統目前未對 B+ 級進行歷史勝率回測驗證**，請勿依賴任何具體勝率/報酬數字，\n")
                    recommendations.append("> 僅供技術面參考，投資前請自行評估風險。\n\n")

                    recommendations.append("| 排名 | 股票代號 | 股票名稱 | 綜合評分 | 收盤價 | 成交量(萬股) | 漲幅(%) |\n")
                    recommendations.append("|------|----------|----------|----------|--------|-------------|---------|\n")

                    for i, rec in enumerate(b_plus_recs[:5], 1):
                        code = rec.get('code')
                        name = rec.get('name')
                        score = rec.get('total_score', rec.get('recommendation_score', 0))
                        close = rec.get('closing_price', 0)
                        volume = rec.get('trade_volume', 0) / 10000 if rec.get('trade_volume') else 0
                        change_pct = rec.get('change_percent', 0)
                        recommendations.append(f"| {i} | {code} | {name} | {score:.1f} | ${close:.2f} | {volume:.0f} | {change_pct:.2f} |\n")

                    recommendations.append("\n**⚠️ 投資提醒：**\n")
                    recommendations.append("- B+ 級尚未經過歷史回測驗證，風險特性未知，請務必自行評估基本面\n")
                    recommendations.append("- 建議分批買入，設定停損點\n")
                    recommendations.append("- 密切關注成交量變化和技術指標\n\n")
                    recommendations.append("---\n\n")
                
                # 詳細推薦理由
                recommendations.append("### 推薦理由分析\n\n")
                
                for i, stock in enumerate(top_stocks[:5], 1):
                    stock_info = stock['stock_info']
                    rating = stock['rating']
                    
                    recommendations.append(f"#### {i}. {stock_info['Name']} ({stock_info['Code']})\n\n")
                    recommendations.append(f"**評級：** {rating['rating']} | **評分：** {rating['total_score']:.1f}分 | **風險：** {rating['risk_level']}\n\n")
                    
                    # 優勢
                    if rating.get('key_strengths'):
                        recommendations.append("**主要優勢：**\n")
                        for strength in rating['key_strengths']:
                            recommendations.append(f"- {strength}\n")
                        recommendations.append("\n")
                    
                    # 風險
                    if rating.get('key_risks'):
                        recommendations.append("**主要風險：**\n")
                        for risk in rating['key_risks']:
                            recommendations.append(f"- {risk}\n")
                        recommendations.append("\n")
                    
                    # 投資建議
                    recommendations.append(f"**投資建議：** {rating['recommendation']}\n\n")
                    recommendations.append("---\n\n")
            
            # 投資策略建議
            recommendations.append("### 投資策略建議\n\n")
            
            # 根據市場情況給出策略建議
            if self.stock_data.get('market_analysis', {}).get('market_sentiment'):
                sentiment = self.stock_data['market_analysis']['market_sentiment']
                rising_ratio = sentiment.get('rising_ratio', 0)
                
                if rising_ratio > 55:
                    recommendations.append("**市場策略：** 積極進場\n\n")
                    recommendations.append("當前市場呈現多頭格局，建議：\n")
                    recommendations.append("- 可適度增加小型股配置\n")
                    recommendations.append("- 重點關注技術面強勢的股票\n")
                    recommendations.append("- 注意控制單一持股比重\n")
                    recommendations.append("- 設定適當的停利停損點\n\n")
                elif rising_ratio > 45:
                    recommendations.append("**市場策略：** 謹慎操作\n\n")
                    recommendations.append("當前市場呈現震盪格局，建議：\n")
                    recommendations.append("- 採取分批進場策略\n")
                    recommendations.append("- 優先選擇A級以上評級股票\n")
                    recommendations.append("- 密切關注市場變化\n")
                    recommendations.append("- 保持適當現金部位\n\n")
                else:
                    recommendations.append("**市場策略：** 保守觀望\n\n")
                    recommendations.append("當前市場呈現空頭格局，建議：\n")
                    recommendations.append("- 暫緩新增投資\n")
                    recommendations.append("- 僅考慮A+級評級股票\n")
                    recommendations.append("- 嚴格控制風險\n")
                    recommendations.append("- 等待更好的進場時機\n\n")
            
            # 風險提醒
            recommendations.append("### 風險提醒\n\n")
            recommendations.append("**投資風險提醒：**\n")
            recommendations.append("- 小型股波動性較大，請注意風險控制\n")
            recommendations.append("- 漲停股票存在回檔風險，建議分批進場\n")
            recommendations.append("- 技術分析僅供參考，請結合基本面分析\n")
            recommendations.append("- 投資前請詳細了解公司基本面\n")
            recommendations.append("- 建議設定停損點，控制下檔風險\n")
            recommendations.append("- 不建議單一股票投入過多資金\n\n")
            
            return "".join(recommendations)
            
        except Exception as e:
            logger.error(f"生成投資建議時發生錯誤: {e}")
            return "## 投資建議\n\n無法生成投資建議\n\n"

    def compose_full_report(self) -> str:
        """組合整份報告的 Markdown 內容"""
        parts = []
        parts.append(f"# 台股小型股漲停潛力分析報告\n\n")
        parts.append(f"**報告版本：** {REPORT_VERSION}\n")
        parts.append(f"**報告日期：** {datetime.now().strftime('%Y年%m月%d日')}\n")
        parts.append(f"**分析時間：** {datetime.now().strftime('%H:%M:%S')}\n\n")
        parts.append(self.generate_executive_summary())
        parts.append(self.generate_market_analysis())
        parts.append(self.generate_limit_up_analysis())
        parts.append(self.generate_strong_stocks_analysis())
        parts.append(self.generate_technical_analysis_summary())
        parts.append(self.generate_investment_recommendations())
        parts.append("\n## 免責聲明\n\n本報告僅供參考，不構成投資建議。\n")
        return "".join(parts)

    def save_report(self) -> str:
        """將報告寫入 `reports/market_analysis/market_analysis_report_{timestamp}.md` 並回傳檔名"""
        try:
            content = self.compose_full_report()
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            fname = os.path.join(MARKET_ANALYSIS_DIR, f"market_analysis_report_{ts}.md")
            with open(fname, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"已保存市場分析報告: {fname}")
            return fname
        except Exception as e:
            logger.error(f"保存市場分析報告失敗: {e}")
            return ''
    
    def get_top_recommended_stocks(self, count: int = 10) -> List[Dict]:
        """獲取前N名推薦股票"""
        try:
            all_stocks = []
            
            # 合併漲停股票和強勢股票的技術分析結果
            if self.technical_data.get('limit_up_analysis'):
                all_stocks.extend(self.technical_data['limit_up_analysis'])
            
            if self.technical_data.get('strong_stocks_analysis'):
                all_stocks.extend(self.technical_data['strong_stocks_analysis'])
            
            # 按評分排序
            sorted_stocks = sorted(all_stocks, key=lambda x: x['rating']['total_score'], reverse=True)
            
            # 去重（避免同一股票出現多次）
            seen_codes = set()
            unique_stocks = []
            
            for stock in sorted_stocks:
                code = stock['stock_info']['Code']
                if code not in seen_codes:
                    seen_codes.add(code)
                    unique_stocks.append(stock)
                    
                    if len(unique_stocks) >= count:
                        break
            
            return unique_stocks
            
        except Exception as e:
            logger.error(f"獲取推薦股票時發生錯誤: {e}")
            return []
    
    def generate_complete_report(self) -> str:
        """生成完整報告"""
        logger.info("開始生成市場分析報告...")
        
        report_parts = []
        
        # 報告標題
        report_parts.append("# 台股小型股漲停潛力分析報告\n\n")
        report_parts.append(f"**報告版本：** {REPORT_VERSION}\n")
        report_parts.append(f"**報告日期：** {datetime.now().strftime('%Y年%m月%d日')}\n")
        report_parts.append(f"**分析時間：** {datetime.now().strftime('%H:%M:%S')}\n\n")

        # 市場行情濾網旗標（research，資料不足時回傳空字串、自動略過）
        report_parts.append(self.generate_regime_flag())

        # 各個章節
        report_parts.append(self.generate_executive_summary())
        report_parts.append(self.generate_market_analysis())
        report_parts.append(self.generate_limit_up_analysis())
        report_parts.append(self.generate_strong_stocks_analysis())
        report_parts.append(self.generate_technical_analysis_summary())
        report_parts.append(self.generate_investment_recommendations())
        
        # 免責聲明
        report_parts.append("## 免責聲明\n\n")
        report_parts.append("本報告僅供參考，不構成投資建議。投資有風險，請謹慎評估自身風險承受能力。")
        report_parts.append("所有數據和分析結果基於公開資訊，不保證其完整性和準確性。")
        report_parts.append("投資決策應基於個人判斷，本報告不承擔任何投資損失責任。\n\n")
        
        logger.info("市場分析報告生成完成")
        return "".join(report_parts)

def main():
    """主函數"""
    # 創建報告生成器
    generator = MarketReportGenerator()
    
    # 生成完整報告
    report_content = generator.generate_complete_report()
    
    # 保存報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"market_analysis_report_{timestamp}.md"
    report_filepath = os.path.join(MARKET_ANALYSIS_DIR, report_filename)
    
    with open(report_filepath, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    logger.info(f"市場分析報告已保存: {report_filepath}")
    
    # 顯示摘要
    print("\n=== 市場分析報告生成完成 ===")
    print(f"報告文件: {report_filepath}")
    print(f"報告大小: {len(report_content)} 字符")
    
    # 顯示前5名推薦股票
    top_stocks = generator.get_top_recommended_stocks(5)
    if top_stocks:
        print("\n=== 前5名推薦股票 ===")
        for i, stock in enumerate(top_stocks, 1):
            stock_info = stock['stock_info']
            rating = stock['rating']
            print(f"{i}. {stock_info['Name']} ({stock_info['Code']}) - 評級: {rating['rating']} ({rating['total_score']:.1f}分)")
    
    return report_filepath

if __name__ == "__main__":
    main()

