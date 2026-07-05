#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
台股休市日檢查腳本
用於 Cron 任務判斷是否為交易日
"""

import sys
from datetime import datetime, date

# 2026 年台股休市日 (根據證交所公告)
HOLIDAYS_2026 = [
    # 元旦
    date(2026, 1, 1),
    date(2026, 1, 2),  # 補假
    
    # 農曆春節 (2026年農曆新年約在2月17日)
    date(2026, 2, 14),  # 小年夜補假
    date(2026, 2, 15),  # 除夕
    date(2026, 2, 16),  # 初一
    date(2026, 2, 17),  # 初二
    date(2026, 2, 18),  # 初三
    date(2026, 2, 19),  # 初四
    date(2026, 2, 20),  # 初五
    
    # 和平紀念日
    date(2026, 2, 28),
    date(2026, 2, 27),  # 補假 (如遇週六)
    
    # 兒童節 & 清明節
    date(2026, 4, 3),   # 兒童節補假
    date(2026, 4, 4),   # 兒童節
    date(2026, 4, 5),   # 清明節
    date(2026, 4, 6),   # 補假
    
    # 勞動節
    date(2026, 5, 1),
    
    # 端午節 (2026年約在5月31日)
    date(2026, 5, 30),  # 補假
    date(2026, 5, 31),  # 端午節
    
    # 中秋節 (2026年約在9月25日)
    date(2026, 9, 25),  # 中秋節
    date(2026, 9, 26),  # 補假
    
    # 國慶日
    date(2026, 10, 10),
    date(2026, 10, 9),  # 補假
]

# 2027 年台股休市日 (預估，需每年更新)
HOLIDAYS_2027 = [
    date(2027, 1, 1),   # 元旦
    # ... 需根據證交所公告更新
]

# 合併所有休市日
ALL_HOLIDAYS = set(HOLIDAYS_2026 + HOLIDAYS_2027)


def is_trading_day(check_date: date = None) -> bool:
    """
    檢查指定日期是否為交易日
    
    Args:
        check_date: 要檢查的日期，預設為今天
        
    Returns:
        True 如果是交易日，False 如果是休市日
    """
    if check_date is None:
        check_date = date.today()
    
    # 週末不開盤
    if check_date.weekday() >= 5:  # 5=週六, 6=週日
        return False
    
    # 國定假日不開盤
    if check_date in ALL_HOLIDAYS:
        return False
    
    return True


def main():
    """主程式 - 用於 Cron 任務檢查"""
    today = date.today()
    
    if is_trading_day(today):
        print(f"✓ {today} 是交易日")
        sys.exit(0)  # 成功退出，繼續執行後續命令
    else:
        weekday_names = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
        reason = "週末" if today.weekday() >= 5 else "國定假日"
        print(f"✗ {today} ({weekday_names[today.weekday()]}) 是{reason}，台股休市")
        sys.exit(1)  # 錯誤退出，終止後續命令


if __name__ == "__main__":
    main()
