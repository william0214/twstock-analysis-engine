# TWstock Analysis Engine

> **使用限制:本專案僅供學術研究與技術參考使用,不允許任何商業用途。**
> 禁止用於實際交易、投資顧問服務、付費產品或其他營利行為。詳見 [LICENSE](LICENSE)。

台股小型股漲停潛力分析系統的**分析與報告生成核心程式**。

這個 repo 包含資料擷取(TWSE 公開 OpenAPI)、選股評分、技術分析、產業分類、策略驗證、
統計計算與報告生成的邏輯,**不包含** Email 寄送、後台管理、部署腳本與任何憑證設定 ——
那些是另一個私有 production repo 的部分,這裡只放「擷取行情資料 → 產出分析與報告」這段
核心邏輯,方便研究或參考。

## 功能

系統每日從台灣證券交易所 OpenAPI 擷取全市場行情快照,跑過以下步驟並輸出四類報告
(見下方「範例輸出」):

1. **資料擷取**(`stock_data_crawler.py` + `crawl_latest_data.py` + `api_data_updater.py`):
   向 `https://openapi.twse.com.tw/v1`(政府公開資料,無需金鑰)取得全市場個股行情、
   大盤指數與本益比資料,篩出漲停股、強勢股與小型股子集,存成每日快照。
2. **技術面評分**(`technical_analysis.py`):針對每檔個股計算動能分數、量能強度、
   價格波動度、籌碼集中度、流動性分數與風險等級等自建指標,不依賴單一傳統指標
   (如 RSI/MACD),而是綜合多個面向算出一個 0-100 的技術評分。
3. **多代理人分析**(`multi_agent_analyzer.py`):由四個獨立 Agent 各自給出意見再彙總——
   `TechnicalAgent`(技術面)、`ChipAgent`(籌碼面)、`SectorAgent`(類股面)、
   `RiskAgent`(風險面),模擬多角度會診而非單一評分模型。
4. **產業/類股動能**(`industry_classifier.py` + `sector_momentum_analyzer.py`):
   先將個股分類到產業,再計算該產業類股當日的整體動能強弱。
5. **選股分級**(`stock_selector.py`):綜合上述評分,將個股分成 `A+`/`A`(頂級推薦)
   與 `B+`(高勝率推薦)兩組推薦名單。
6. **市場統計**(`statistics_calculator.py`)與**報告生成**(`market_report_generator.py`):
   彙整當日市場漲跌家數、情緒方向、產業表現等統計,產出 Markdown 格式的每日市場分析報告。
7. **策略回測驗證**(`strategy_validation_analyzer.py`):追蹤每筆推薦在 1/3/5/10 日後的
   實際報酬,以「推薦後 3 日報酬 > 0」為成功標準計算歷史勝率,產出驗證報告。
8. **參數自動優化**(`auto_strategy_optimizer.py`):定期依驗證結果調整選股評分權重與門檻。

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
