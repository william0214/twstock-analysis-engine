# TWstock Analysis Engine

> **使用限制:本專案僅供學術研究與技術參考使用,不允許任何商業用途。**
> 禁止用於實際交易、投資顧問服務、付費產品或其他營利行為。詳見 [LICENSE](LICENSE)。

台股小型股漲停潛力分析系統的**分析與報告生成核心程式**。

這個 repo 只包含 production 系統實際執行的 6 支核心分析程式,**不包含**選股後處理
(多代理人分析、產業分類等未整合進主流程的模組)、Email 寄送、後台管理、部署腳本
與任何憑證設定 —— 這裡只放「擷取行情資料 → 產出分析與報告」這段核心邏輯,方便
研究或參考。

## 功能

系統依序執行以下 6 個步驟(對應 production 端 `main_executor.py` 的執行順序):

### 1. 資料擷取(`crawl_latest_data.py` + `stock_data_crawler.py`)
- 從台灣證券交易所(TWSE)公開 OpenAPI(`https://openapi.twse.com.tw/v1`,無需金鑰)
  取得全市場個股行情、大盤指數、本益比資料
- 篩出漲停股(漲幅 ≥9.5%)、強勢股(成交量 ≥100 萬股且漲幅 ≥3%)、
  小型股(市值 ≤100 億)子集,存成每日 JSON 快照
- 對連線逾時、JSON 解析錯誤等例外都有捕捉處理;目前是單次請求失敗即記錄並跳過,
  **沒有自動重試迴圈**

### 2. 深度分析(`stock_analysis.py`)
- 對漲停股/強勢股計算敘述性統計(漲幅、成交量、股價、市值分布)與兩者的比較分析
- 以自訂公式(漲幅、成交量、成交筆數、市值倒數的加權組合)篩選「潛力股」
- 產出 3 張 PNG 圖表:`limit_up_analysis.png`、`strong_vs_limit_up_comparison.png`、
  `market_overview.png`

### 3. 技術分析(`technical_analysis.py`)
- 計算一組**自建**技術指標(非傳統 RSI / 布林帶 / 變異係數):動能分數、量能強度、
  價格波動度、籌碼集中度、流動性分數、風險等級
- 技術面(65%)與籌碼面(35%)加權算出 0-100 分綜合評分,依門檻分為
  `A+`(≥85)/`A`(≥75)/`B+`(≥65)/`B`/`C+`/`C`/`D` 七級
- 產出各檔股票的關鍵優勢與風險標籤

### 4. 統計計算(`statistics_calculator.py`)
- 彙整全市場漲跌分布、成交量/股價/市值分布等統計數據
- 讀取技術分析結果計算高評級比例、低風險比例等績效指標
- 產出最終推薦股票清單

### 5. 市場報告(`market_report_generator.py`)
- 整合前述統計與技術分析結果,生成完整 Markdown 格式的每日市場分析報告
  (執行摘要、市場概況、漲停/強勢股分析、投資建議)

### 6. API 數據(`api_data_updater.py`)
- 將分析結果整理成 `latest_analysis.json`,供其他應用程式讀取

> 以上皆已核對對應程式碼實際邏輯。production 另有策略回測驗證、參數自動優化、
> 多代理人分析等模組,但未整合進上述每日主流程,故不列入此 repo。

## 檔案說明

| 檔案 | 說明 |
| --- | --- |
| `crawl_latest_data.py` | 每日快照擷取入口,呼叫 `stock_data_crawler` 並存檔 |
| `stock_data_crawler.py` | TWSE OpenAPI 資料擷取(全市場行情、大盤指數、本益比) |
| `stock_analysis.py` | 深度分析:敘述性統計、比較分析、潛力股篩選、PNG 圖表 |
| `technical_analysis.py` | 技術指標分析與評分(A+/A/B+/B/C+/C/D 七級) |
| `statistics_calculator.py` | 市場統計計算與最終推薦清單 |
| `market_report_generator.py` | 每日市場分析報告產生器(輸出 Markdown) |
| `api_data_updater.py` | 產出 `latest_analysis.json` 供其他應用讀取 |
| `config.py` | 路徑設定(所有檔案共用) |

`config.py` 是共用相依模組(定義 `reports/`、`data/` 等路徑常數),雖非獨立分析步驟但為
其餘 6 支程式運作所必需,故一併附上。

## 執行環境

`crawl_latest_data.py` 向 TWSE OpenAPI 取得當日快照(`latest_stock_data_*.json`)後,
`stock_analysis.py` 與 `technical_analysis.py` 各自獨立讀取該快照進行分析(兩者無先後
資料依賴);`statistics_calculator.py` 讀取 `technical_analysis.py` 的輸出計算統計數據;
`market_report_generator.py` 整合前述結果生成報告;`api_data_updater.py` 最後更新
`latest_analysis.json`。輸出統一存到 `reports/` 各子資料夾。

排程(如何觸發每日執行)與 Email 寄送另有一套 production 程式(未公開)。

## 範例輸出(`reports/`,2026 年 6 月)

按日期分資料夾,附上 2026 年 6 月實際產出的報告組,作為輸出格式範例:

| 資料夾 | 內容 |
| --- | --- |
| `2026-06-04` | 僅策略驗證報告(其餘三份已於 production 端滾動清除) |
| `2026-06-05`, `06-08`~`06-12`, `06-15`~`06-19`, `06-22`~`06-24` | 完整四份報告 |

每個完整資料夾包含:

- `market_analysis_report_YYYYMMDD.md` — 每日市場分析報告(本 repo `market_report_generator.py` 的輸出)
- `technical_analysis_report_YYYYMMDD.json` — 技術分析原始輸出(本 repo `technical_analysis.py` 的輸出)
- `statistics_report_YYYYMMDD.json` — 統計計算原始輸出(本 repo `statistics_calculator.py` 的輸出)
- `strategy_validation_report_YYYYMMDD.md` — 策略驗證報告(含歷史成功率);由 production 端另一支
  **未包含於本 repo** 的驗證腳本產生,附上僅供參考該功能的輸出格式

缺日說明:6/6-6/7、6/13-6/14、6/20-6/21 為週末非交易日;6/1-6/3 為交易日,但當時的報告
在 production 端已滾動清除(取得本資料時已超過保留期限),非本 repo 遺漏。

## 使用授權

本專案採**僅限非商業使用**授權(詳見 [LICENSE](LICENSE)):

- ✅ 允許:個人學習、學術研究、程式碼閱讀與參考
- ❌ 不允許:商業使用、實際交易 / 投顧服務、任何形式的付費產品或轉售、對外提供付費分析服務

如需商業使用,請先聯繫作者取得授權。

## 免責聲明

所有評級與推薦皆為演算法輸出,僅供技術研究與參考,不構成投資建議。
