#!/usr/bin/env python3
"""
專案配置檔
定義所有檔案路徑和資料夾結構
"""

import os

# 取得專案根目錄
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 資料夾路徑
LOGS_DIR = os.path.join(BASE_DIR, "logs")
DATA_DIR = os.path.join(BASE_DIR, "data")
STOCK_DATA_DIR = os.path.join(DATA_DIR, "stock_data")
MARKET_SUMMARY_DIR = os.path.join(DATA_DIR, "market_summary")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
MARKET_ANALYSIS_DIR = os.path.join(REPORTS_DIR, "market_analysis")
TECHNICAL_ANALYSIS_DIR = os.path.join(REPORTS_DIR, "technical_analysis")
STATISTICS_DIR = os.path.join(REPORTS_DIR, "statistics")
STRATEGY_VALIDATION_DIR = os.path.join(REPORTS_DIR, "strategy_validation")
OPTIMIZATION_DIR = os.path.join(REPORTS_DIR, "optimization")

# 確保所有資料夾存在
DIRECTORIES = [
    LOGS_DIR,
    DATA_DIR,
    STOCK_DATA_DIR,
    MARKET_SUMMARY_DIR,
    REPORTS_DIR,
    MARKET_ANALYSIS_DIR,
    TECHNICAL_ANALYSIS_DIR,
    STATISTICS_DIR,
    STRATEGY_VALIDATION_DIR,
    OPTIMIZATION_DIR
]

def ensure_directories():
    """確保所有必要的資料夾都存在"""
    for directory in DIRECTORIES:
        os.makedirs(directory, exist_ok=True)

# 初始化時建立資料夾
ensure_directories()
