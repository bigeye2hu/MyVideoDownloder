#!/usr/bin/env python3
"""检查并修复metrics数据"""
import sqlite3

conn = sqlite3.connect("/app/data/credits.db")
c = conn.cursor()

# 查看当前外部API统计
print("=== 当前外部API调用统计 ===")
c.execute("SELECT external_api, COUNT(*) FROM api_metrics WHERE is_external=1 GROUP BY external_api")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} 次")

# 统一 TikHub (downloads) 为 TikHub
print("\n=== 统一名称 ===")
c.execute("UPDATE api_metrics SET external_api='TikHub' WHERE external_api='TikHub (downloads)'")
updated = c.rowcount
conn.commit()
print(f"已更新 {updated} 条记录")

# 再次查看
print("\n=== 修复后的统计 ===")
c.execute("SELECT external_api, COUNT(*) FROM api_metrics WHERE is_external=1 GROUP BY external_api")
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]} 次")

conn.close()


