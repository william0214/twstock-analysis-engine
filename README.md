# TWstock Analysis Engine

台股小型股漲停潛力分析系統的**分析與報告生成核心程式**。

這個 repo 只包含選股評分、技術分析、產業分類、策略驗證、統計計算與報告生成的邏輯,
**不包含**資料爬蟲、Email 寄送、後台管理、部署腳本與任何憑證設定 —— 那些是另一個私有
production repo 的部分,這裡只放「輸入行情資料 → 產出分析與報告」這段核心邏輯,方便
研究或參考。

## 檔案說明

| 檔案 | 說明 |
| --- | --- |
| `stock_selector.py` | 綜合評分後的推薦名單產生器(A+/A/B+ 分級) |
| `technical_analysis.py` | 技術指標分析與評分 |
| `industry_classifier.py` | 個股產業分類 |
| `sector_momentum_analyzer.py` | 產業類股動能分析 |
| `multi_agent_analyzer.py` | 多代理人(技術面/籌碼面/類股面/風險面)分析架構 |
| `statistics_calculator.py` | 市場統計計算 |
| `market_report_generator.py` | 每日市場分析報告產生器(輸出 Markdown) |
| `strategy_validation_analyzer.py` | 策略回測驗證(推薦後 3 日報酬率是否為正) |
| `auto_strategy_optimizer.py` | 選股參數自動優化 |
| `trading_day_checker.py` | 台股交易日判斷 |
| `config.py` | 路徑設定 |

## 執行環境

各檔案是同一套 pipeline 的分析階段,預期輸入為 TWSE OpenAPI 格式的每日行情快照
(`latest_stock_data_*.json`),輸出到 `reports/` 各子資料夾。實際的資料擷取、排程與
寄信另有一套 production 程式(未公開)。

## 範例輸出(`reports/2026-06-24/`)

附上 2026-06-24 這一天實際產出的完整報告組,作為輸出格式範例:

- `market_analysis_report_20260624.md` — 每日市場分析報告
- `technical_analysis_report_20260624.json` — 技術分析原始輸出
- `statistics_report_20260624.json` — 統計計算原始輸出
- `strategy_validation_report_20260624.md` — 策略驗證報告(含歷史成功率)

> 備註:production 系統自 2026-06-25 起因一個尚待修復的序列化錯誤
> (`stock_analysis.py` 深度分析步驟寫 JSON 時 numpy `int64` 型別未轉換為原生
> Python `int`)而暫停產出報告,06-24 是當時最後一份完整成功的輸出,故以此作為範例。

## 免責聲明

所有評級與推薦皆為演算法輸出,僅供技術研究與參考,不構成投資建議。
