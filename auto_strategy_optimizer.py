#!/usr/bin/env python3
"""
台股小型股分析系統 - 自動策略優化器
每20個交易日自動評估和優化策略參數
"""

import os
import sys
import json
import glob
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
import argparse

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoStrategyOptimizer:
    """自動策略優化器"""
    
    def __init__(self, force_optimize: bool = False):
        """初始化優化器"""
        self.work_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file = os.path.join(self.work_dir, 'strategy_config.json')
        self.optimization_history_file = os.path.join(self.work_dir, 'optimization_history.json')
        self.trading_days_threshold = 20  # 20個交易日觸發優化
        self.force_optimize = force_optimize
        
    def should_optimize(self) -> Tuple[bool, int, str]:
        """
        檢查是否需要進行優化
        
        Returns:
            (是否需要優化, 累積交易日數, 原因)
        """
        # 讀取優化歷史
        optimization_history = self.load_optimization_history()
        
        # 獲取最後優化日期
        last_optimization_date = optimization_history.get('last_optimization_date')
        
        if not last_optimization_date:
            if self.force_optimize:
                return True, 0, "強制執行首次優化"
            return True, 0, "首次執行，需要建立基準"
        
        # 計算自上次優化後的交易日數
        trading_days = self.count_trading_days_since(last_optimization_date)

        if self.force_optimize:
            return True, trading_days, f"強制執行優化（累積{trading_days}個交易日）"
        
        if trading_days >= self.trading_days_threshold:
            return True, trading_days, f"已累積{trading_days}個交易日，達到優化門檻"
        
        return False, trading_days, f"僅累積{trading_days}個交易日，尚未達到{self.trading_days_threshold}個交易日門檻"
    
    def count_trading_days_since(self, start_date: str) -> int:
        """
        計算自指定日期以來的交易日數
        
        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            
        Returns:
            交易日數量
        """
        # 查找所有報告文件（在 reports/market_analysis/ 子目錄中）
        report_files = glob.glob(os.path.join(self.work_dir, 'reports', 'market_analysis', 'market_analysis_report_*.md'))
        
        # 解析日期並篩選
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        trading_dates = set()
        
        for report_file in report_files:
            # 從文件名提取日期: market_analysis_report_YYYYMMDD_HHMMSS.md
            basename = os.path.basename(report_file)
            try:
                date_str = basename.split('_')[3]  # YYYYMMDD
                file_date = datetime.strptime(date_str, '%Y%m%d')
                
                if file_date > start_dt:
                    # 只計算交易日（有報告生成的日期）
                    trading_dates.add(date_str)
            except (IndexError, ValueError):
                continue
        
        return len(trading_dates)
    
    def load_optimization_history(self) -> Dict:
        """載入優化歷史"""
        if os.path.exists(self.optimization_history_file):
            try:
                with open(self.optimization_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"載入優化歷史失敗: {e}")
        
        return {
            'last_optimization_date': None,
            'optimization_count': 0,
            'history': []
        }
    
    def save_optimization_history(self, history: Dict):
        """儲存優化歷史"""
        try:
            with open(self.optimization_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ 優化歷史已儲存: {self.optimization_history_file}")
        except Exception as e:
            logger.error(f"✗ 儲存優化歷史失敗: {e}")
    
    def load_config(self) -> Dict:
        """載入策略配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"載入配置失敗: {e}")
            return {}
    
    def save_config(self, config: Dict):
        """儲存策略配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ 策略配置已更新: {self.config_file}")
        except Exception as e:
            logger.error(f"✗ 儲存配置失敗: {e}")
    
    def run_validation(self) -> Dict:
        """
        執行策略驗證
        
        Returns:
            驗證結果字典
        """
        logger.info("執行策略驗證...")
        
        # 執行驗證分析器
        validation_script = os.path.join(self.work_dir, 'strategy_validation_analyzer.py')
        
        if not os.path.exists(validation_script):
            logger.error(f"找不到驗證腳本: {validation_script}")
            return {}
        
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, validation_script],
                cwd=self.work_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("✓ 策略驗證完成")
                
                # 讀取驗證結果（在 reports/strategy_validation/ 子目錄中）
                validation_files = glob.glob(os.path.join(self.work_dir, 'reports', 'strategy_validation', 'strategy_validation_report_*.md'))
                if validation_files:
                    latest_validation = max(validation_files, key=os.path.getctime)
                    return self.parse_validation_results(latest_validation)
            else:
                logger.error(f"策略驗證失敗: {result.stderr}")
                
        except Exception as e:
            logger.error(f"執行驗證時發生錯誤: {e}")
        
        return {}
    
    def parse_validation_results(self, report_file: str) -> Dict:
        """
        從驗證報告中提取關鍵指標
        
        Args:
            report_file: 驗證報告文件路徑
            
        Returns:
            驗證結果字典
        """
        results = {
            'success_rate': 0.0,
            'a_plus_success_rate': 0.0,
            'avg_return_3d': 0.0,
            'avg_return_10d': 0.0,
            'total_recommendations': 0
        }
        
        try:
            with open(report_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 簡單的文本解析（實際應該更robust）
                import re
                
                # 提取成功率
                match = re.search(r'整體成功率.*?(\d+\.?\d*)%', content)
                if match:
                    results['success_rate'] = float(match.group(1))
                
                # 提取A+成功率
                match = re.search(r'A\+.*?成功率.*?(\d+\.?\d*)%', content)
                if match:
                    results['a_plus_success_rate'] = float(match.group(1))
                
                # 提取平均回報
                match = re.search(r'平均.*?3.*?天.*?回報.*?(\d+\.?\d*)%', content)
                if match:
                    results['avg_return_3d'] = float(match.group(1))
                
                logger.info(f"驗證結果: 成功率={results['success_rate']}%, A+成功率={results['a_plus_success_rate']}%")
                
        except Exception as e:
            logger.error(f"解析驗證結果失敗: {e}")
        
        return results
    
    def optimize_parameters(self, validation_results: Dict, current_config: Dict) -> Dict:
        """
        基於驗證結果優化參數
        
        Args:
            validation_results: 驗證結果
            current_config: 當前配置
            
        Returns:
            優化後的配置
        """
        logger.info("開始參數優化...")
        
        new_config = current_config.copy()
        optimizations = []
        
        success_rate = validation_results.get('success_rate', 0)
        a_plus_success = validation_results.get('a_plus_success_rate', 0)
        
        # 優化邏輯
        if success_rate < 65:
            # 成功率過低，提高篩選標準
            logger.info("成功率低於65%，提高評級門檻")
            
            if 'thresholds' in new_config and 'rating_thresholds' in new_config['thresholds']:
                thresholds = new_config['thresholds']['rating_thresholds']
                for rating in thresholds:
                    thresholds[rating] += 2  # 每個評級提高2分
                optimizations.append("評級門檻全面提高2分")
        
        elif success_rate > 75:
            # 成功率很高，可以稍微放寬標準增加推薦數量
            logger.info("成功率高於75%，可適度放寬標準")
            
            if 'thresholds' in new_config and 'rating_thresholds' in new_config['thresholds']:
                thresholds = new_config['thresholds']['rating_thresholds']
                for rating in thresholds:
                    thresholds[rating] = max(thresholds[rating] - 1, 0)  # 降低1分，但不低於0
                optimizations.append("評級門檻適度降低1分")
        
        if a_plus_success < 70:
            # A+成功率不足，提高A+門檻
            logger.info("A+成功率低於70%，提高A+門檻")
            
            if 'thresholds' in new_config and 'rating_thresholds' in new_config['thresholds']:
                new_config['thresholds']['rating_thresholds']['A+'] += 3
                optimizations.append("A+門檻提高3分")
            
            # 增加技術面權重
            if 'scoring_weights' in new_config:
                old_tech = new_config['scoring_weights']['technical_weight']
                new_config['scoring_weights']['technical_weight'] = min(old_tech + 0.02, 0.70)
                new_config['scoring_weights']['chip_weight'] = 1.0 - new_config['scoring_weights']['technical_weight']
                optimizations.append(f"技術面權重從{old_tech:.0%}提升至{new_config['scoring_weights']['technical_weight']:.0%}")
        
        # 調整流動性要求
        if success_rate < 70:
            if 'thresholds' in new_config:
                old_min = new_config['thresholds'].get('min_volume', 2000000)
                new_config['thresholds']['min_volume'] = int(old_min * 1.2)
                optimizations.append(f"最低成交量從{old_min:,}提升至{new_config['thresholds']['min_volume']:,}")
        
        # 調整風險係數
        if validation_results.get('avg_return_3d', 0) < 2.0:
            if 'risk_adjustments' in new_config:
                # 加重低風險獎勵
                old_low = new_config['risk_adjustments']['low_risk_factor']
                new_config['risk_adjustments']['low_risk_factor'] = min(old_low + 0.03, 1.20)
                optimizations.append(f"低風險獎勵從{old_low:.2f}提升至{new_config['risk_adjustments']['low_risk_factor']:.2f}")
        
        # 更新版本和時間
        new_config['version'] = f"{float(current_config.get('version', '2.0')) + 0.1:.1f}"
        new_config['update_date'] = datetime.now().strftime('%Y-%m-%d')
        new_config['last_optimization'] = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'success_rate': success_rate,
            'a_plus_success_rate': a_plus_success,
            'optimizations': optimizations
        }
        
        logger.info(f"✓ 參數優化完成，執行了{len(optimizations)}項調整")
        for opt in optimizations:
            logger.info(f"  - {opt}")
        
        return new_config
    
    def generate_optimization_report(self, 
                                    validation_results: Dict, 
                                    old_config: Dict, 
                                    new_config: Dict,
                                    trading_days: int) -> str:
        """
        生成優化報告
        
        Returns:
            報告文件路徑
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = os.path.join(self.work_dir, f'auto_optimization_report_{timestamp}.md')
        
        report_content = f"""# 自動策略優化報告

**優化時間：** {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}
**累積交易日數：** {trading_days} 個交易日
**系統版本：** v{old_config.get('version', '2.0')} → v{new_config.get('version', '2.1')}

---

## 📊 驗證結果

### 績效指標

| 指標 | 當前值 | 目標值 | 狀態 |
|------|--------|--------|------|
| 整體成功率 | {validation_results.get('success_rate', 0):.1f}% | 70%+ | {'✅ 達標' if validation_results.get('success_rate', 0) >= 70 else '⚠️ 需改善'} |
| A+成功率 | {validation_results.get('a_plus_success_rate', 0):.1f}% | 75%+ | {'✅ 達標' if validation_results.get('a_plus_success_rate', 0) >= 75 else '⚠️ 需改善'} |
| 平均3日回報 | {validation_results.get('avg_return_3d', 0):.2f}% | 2.5%+ | {'✅ 達標' if validation_results.get('avg_return_3d', 0) >= 2.5 else '⚠️ 需改善'} |
| 平均10日回報 | {validation_results.get('avg_return_10d', 0):.2f}% | 4.0%+ | {'✅ 達標' if validation_results.get('avg_return_10d', 0) >= 4.0 else '⚠️ 需改善'} |

---

## 🔧 參數調整

### 評級門檻變化

| 評級 | 優化前 | 優化後 | 變化 |
|------|--------|--------|------|
"""
        
        # 評級門檻對比
        if 'thresholds' in old_config and 'rating_thresholds' in old_config['thresholds']:
            old_thresholds = old_config['thresholds']['rating_thresholds']
            new_thresholds = new_config['thresholds']['rating_thresholds']
            
            for rating in ['A+', 'A', 'B+', 'B', 'C+', 'C']:
                old_val = old_thresholds.get(rating, 0)
                new_val = new_thresholds.get(rating, 0)
                change = new_val - old_val
                change_str = f"+{change}" if change > 0 else str(change)
                report_content += f"| {rating} | {old_val} | {new_val} | {change_str} |\n"
        
        report_content += f"""
### 權重調整

| 項目 | 優化前 | 優化後 | 變化 |
|------|--------|--------|------|
"""
        
        # 權重對比
        if 'scoring_weights' in old_config:
            old_weights = old_config['scoring_weights']
            new_weights = new_config['scoring_weights']
            
            items = [
                ('技術面權重', 'technical_weight', '%'),
                ('籌碼面權重', 'chip_weight', '%')
            ]
            
            for label, key, unit in items:
                old_val = old_weights.get(key, 0) * 100 if unit == '%' else old_weights.get(key, 0)
                new_val = new_weights.get(key, 0) * 100 if unit == '%' else new_weights.get(key, 0)
                change = new_val - old_val
                report_content += f"| {label} | {old_val:.1f}{unit} | {new_val:.1f}{unit} | {change:+.1f}{unit} |\n"
        
        report_content += f"""
### 其他調整

| 項目 | 優化前 | 優化後 |
|------|--------|--------|
"""
        
        # 其他參數對比
        if 'thresholds' in old_config:
            old_min_vol = old_config['thresholds'].get('min_volume', 0)
            new_min_vol = new_config['thresholds'].get('min_volume', 0)
            report_content += f"| 最低成交量 | {old_min_vol:,} 股 | {new_min_vol:,} 股 |\n"
        
        if 'risk_adjustments' in old_config:
            old_risk = old_config['risk_adjustments']
            new_risk = new_config['risk_adjustments']
            
            report_content += f"| 高風險係數 | {old_risk.get('high_risk_factor', 0):.2f} | {new_risk.get('high_risk_factor', 0):.2f} |\n"
            report_content += f"| 低風險係數 | {old_risk.get('low_risk_factor', 0):.2f} | {new_risk.get('low_risk_factor', 0):.2f} |\n"
        
        # 優化摘要
        optimizations = new_config.get('last_optimization', {}).get('optimizations', [])
        
        report_content += f"""
---

## 📋 優化摘要

本次優化共執行 **{len(optimizations)}** 項調整：

"""
        for i, opt in enumerate(optimizations, 1):
            report_content += f"{i}. {opt}\n"
        
        report_content += f"""
---

## 🎯 優化策略

### 決策邏輯

"""
        
        success_rate = validation_results.get('success_rate', 0)
        a_plus_success = validation_results.get('a_plus_success_rate', 0)
        
        if success_rate < 65:
            report_content += "- **成功率低於65%**: 提高評級門檻，加強篩選標準\n"
        elif success_rate > 75:
            report_content += "- **成功率高於75%**: 適度放寬標準，增加推薦機會\n"
        
        if a_plus_success < 70:
            report_content += "- **A+成功率不足**: 提高A+門檻，增加技術面權重\n"
        
        if validation_results.get('avg_return_3d', 0) < 2.0:
            report_content += "- **平均回報偏低**: 加重低風險獎勵，優化風險控制\n"
        
        report_content += f"""
### 預期效果

經過本次優化，預期可以達到以下改善：

- ✅ 提升推薦質量，降低失敗率
- ✅ 增強A+評級的準確性
- ✅ 優化風險收益比
- ✅ 提高整體投資回報

---

## 📈 後續監控

### 監控指標

在接下來的 **20 個交易日** 內，將持續監控以下指標：

1. **整體成功率**: 目標提升至 70%+
2. **A+成功率**: 目標提升至 75%+
3. **平均回報**: 短期(3日) 2.5%+, 中期(10日) 4.0%+
4. **風險控制**: 最大回撤不超過 -10%

### 下次優化時間

預計在 **{(datetime.now() + timedelta(days=30)).strftime('%Y年%m月%d日')}** 左右（累積20個交易日後）進行下一次自動優化。

---

## 💡 使用建議

1. **立即應用**: 新參數已自動保存到 `strategy_config.json`
2. **執行測試**: 建議執行一次完整分析驗證新參數
3. **密切觀察**: 前3-5個交易日密切關注推薦表現
4. **記錄反饋**: 如發現異常，可手動回滾配置

---

## 📝 配置備份

舊版配置已備份至：`strategy_config.json.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}`

如需回滾，可執行：
```bash
cp strategy_config.json.backup_* strategy_config.json
```

---

**報告生成時間：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**下次優化預計：** 20個交易日後  
**系統狀態：** ✅ 優化完成，參數已更新
"""
        
        # 寫入報告
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"✓ 優化報告已生成: {report_file}")
        except Exception as e:
            logger.error(f"✗ 生成報告失敗: {e}")
        
        return report_file
    
    def backup_config(self, config: Dict):
        """備份當前配置"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{self.config_file}.backup_{timestamp}"
        
        try:
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"✓ 配置已備份: {backup_file}")
        except Exception as e:
            logger.error(f"✗ 備份配置失敗: {e}")
    
    def run(self):
        """執行自動優化流程"""
        print("\n" + "="*70)
        print("台股小型股分析系統 - 自動策略優化器")
        print("="*70 + "\n")
        
        # 1. 檢查是否需要優化
        should_opt, trading_days, reason = self.should_optimize()
        
        logger.info(f"優化檢查: {reason}")
        
        if not should_opt:
            logger.info(f"⏭ 跳過優化，還需要 {self.trading_days_threshold - trading_days} 個交易日")
            return
        
        logger.info(f"✓ 觸發優化條件，開始自動優化流程...")
        
        # 2. 執行策略驗證
        validation_results = self.run_validation()
        
        if not validation_results:
            logger.error("✗ 無法獲取驗證結果，終止優化")
            return
        
        # 3. 載入當前配置
        current_config = self.load_config()
        
        if not current_config:
            logger.error("✗ 無法載入策略配置，終止優化")
            return
        
        # 4. 備份配置
        self.backup_config(current_config)
        
        # 5. 優化參數
        new_config = self.optimize_parameters(validation_results, current_config)
        
        # 6. 儲存新配置
        self.save_config(new_config)
        
        # 7. 生成優化報告
        report_file = self.generate_optimization_report(
            validation_results, 
            current_config, 
            new_config,
            trading_days
        )
        
        # 8. 更新優化歷史
        history = self.load_optimization_history()
        history['last_optimization_date'] = datetime.now().strftime('%Y-%m-%d')
        history['optimization_count'] = history.get('optimization_count', 0) + 1
        history['history'].append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'trading_days': trading_days,
            'success_rate': validation_results.get('success_rate', 0),
            'a_plus_success_rate': validation_results.get('a_plus_success_rate', 0),
            'version': new_config.get('version', '2.0'),
            'report_file': report_file
        })
        self.save_optimization_history(history)
        
        # 9. 完成
        print("\n" + "="*70)
        print("✅ 自動優化完成！")
        print("="*70)
        print(f"\n📊 驗證結果:")
        print(f"   - 整體成功率: {validation_results.get('success_rate', 0):.1f}%")
        print(f"   - A+成功率: {validation_results.get('a_plus_success_rate', 0):.1f}%")
        print(f"   - 平均3日回報: {validation_results.get('avg_return_3d', 0):.2f}%")
        print(f"\n📁 優化報告: {os.path.basename(report_file)}")
        print(f"📅 下次優化: 累積20個交易日後")
        print(f"🎯 累積優化次數: {history['optimization_count']}\n")


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description="自動策略優化器")
    parser.add_argument('--force', action='store_true', help='忽略交易日門檻，立即執行優化')
    args = parser.parse_args()

    optimizer = AutoStrategyOptimizer(force_optimize=args.force)
    optimizer.run()


if __name__ == '__main__':
    main()
