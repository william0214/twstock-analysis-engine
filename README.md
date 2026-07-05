# TWstock Analysis Engine

> **使用限制:本專案僅供學術研究與技術參考使用,不允許任何商業用途。**
> 禁止用於實際交易、投資顧問服務、付費產品或其他營利行為。詳見 [LICENSE](LICENSE)。

台股小型股漲停潛力分析系統的**分析與報告生成核心程式**。

這個 repo 包含資料擷取(TWSE 公開 OpenAPI)、選股評分、技術分析、產業分類、策略驗證、
統計計算與報告生成的邏輯,**不包含** Email 寄送、後台管理、部署腳本與任何憑證設定 ——
那些是另一個私有 production repo 的部分,這裡只放「擷取行情資料 → 產出分析與報告」這段
核心邏輯,方便研究或參考。

## 功能

### 1. 資料擷取(`stock_data_crawler.py` / `crawl_latest_data.py` / `api_data_updater.py`)
- 從台灣證券交易所(TWSE)公開 OpenAPI(`https://openapi.twse.com.tw/v1`,無需金鑰)
  爬取全市場行情,篩出漲停股、強勢股與小型股子集
- 包含股價(開高低收)、成交量、市值、本益比等資訊
- 對連線逾時、JSON 解析錯誤等例外都有捕捉處理;目前是單次請求失敗即記錄並跳過,
  **沒有自動重試迴圈**

### 2. 技術分析(`technical_analysis.py` / `multi_agent_analyzer.py` / `sector_momentum_analyzer.py` / `stock_selector.py`)
- 計算一組**自建**技術指標(非傳統 RSI / 布林帶 / 變異係數):動能分數、量能強度、
  價格波動度、籌碼集中度、流動性分數、風險等級
- 綜合多個面向算出 0-100 分的技術評分,並由四個獨立 Agent(技術面/籌碼面/類股面/風險面)
  交叉評估後彙總,模擬多角度會診而非單一評分模型
- 依評分將個股分為 `A+`/`A`(頂級推薦)與 `B+`(高勝率推薦),識別具漲停潛力的股票

### 3. 策略優化(`auto_strategy_optimizer.py`)
- 每 20 個交易日自動回測和優化
- 基於勝率(推薦後 3 日正報酬比例)和平均報酬調整評分參數
- 保存優化歷史記錄

### 4. 報告生成(`market_report_generator.py` / `statistics_calculator.py` / `strategy_validation_analyzer.py`)
- Markdown 格式的每日市場分析報告與策略驗證報告
- PNG 圖表:`market_statistics_overview.png`、`recommendation_analysis.png`、
  `strategy_validation_analysis.png`
- CSV 格式的漲停股 / 強勢股清單
- JSON 格式的技術分析與統計計算詳細數據

## 檔案說明

| 檔案 | 說明 |
| --- | --- |
| `stock_data_crawler.py` | TWSE OpenAPI 資料擷取(全市場行情、大盤指數、本益比) |
| `crawl_latest_data.py` | 每日快照擷取入口,呼叫 `stock_data_crawler` 並存檔 |
| `api_data_updater.py` | 依擷取結果更新各分析報告資料夾 |
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

`stock_data_crawler.py` 向 TWSE OpenAPI 取得當日快照(`latest_stock_data_*.json`)後,
其餘檔案依序讀取該快照進行分析,輸出到 `reports/` 各子資料夾。排程(如何觸發每日執行)
與 Email 寄送另有一套 production 程式(未公開)。

## 範例輸出(`reports/`,2026 年 6 月)

按日期分資料夾,附上 2026 年 6 月實際產出的報告組,作為輸出格式範例:

| 資料夾 | 內容 |
| --- | --- |
| `2026-06-04` | 僅策略驗證報告(其餘三份已於 production 端滾動清除) |
| `2026-06-05`, `06-08`~`06-12`, `06-15`~`06-19`, `06-22`~`06-24` | 完整四份報告 |

每個完整資料夾包含:

- `market_analysis_report_YYYYMMDD.md` — 每日市場分析報告
- `technical_analysis_report_YYYYMMDD.json` — 技術分析原始輸出
- `statistics_report_YYYYMMDD.json` — 統計計算原始輸出
- `strategy_validation_report_YYYYMMDD.md` — 策略驗證報告(含歷史成功率)

缺日說明:6/6-6/7、6/13-6/14、6/20-6/21 為週末非交易日;6/1-6/3 為交易日,但當時的報告
在 production 端已滾動清除(取得本資料時已超過保留期限),非本 repo 遺漏。

## 使用授權

本專案採**僅限非商業使用**授權(詳見 [LICENSE](LICENSE)):

- ✅ 允許:個人學習、學術研究、程式碼閱讀與參考
- ❌ 不允許:商業使用、實際交易 / 投顧服務、任何形式的付費產品或轉售、對外提供付費分析服務

如需商業使用,請先聯繫作者取得授權。

## 免責聲明

所有評級與推薦皆為演算法輸出,僅供技術研究與參考,不構成投資建議。
