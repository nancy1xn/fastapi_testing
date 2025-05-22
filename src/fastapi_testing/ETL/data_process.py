
#ETL
# 1.用python load csv File
# 2.用python寫SQL statement驗證：
# Extract（擷取）階段的驗證-確保從來源系統擷取的資料正確無誤，無遺漏或異常。
#  a.筆數驗證
#  b.欄位完整性
#    -欄位是否都有抓到？
#    -欄位型別、格式是否與定義一致？
#  c.值的合法性
#    -日期格式正確？
#    -ID是唯一？
#    -是否有Null？->（填補、剃除）
#  d.timestamp
#   -日期是最新？
# Transform（轉換）階段的驗證-確保清理、轉換、合併、計算等邏輯正確，轉換後資料無誤
#  e. 邏輯驗證
#  f. 格式驗證
#  g. 資料一致性:Join後重複？
#  h. 缺值處理驗證
# 3. Load（載入）階段的驗證-確保資料正確寫入資料倉儲或目的地，沒有丟失或格式錯誤。
#   i.筆數驗證
#   j.資料比對
#     -關鍵欄位比對（例如總金額、最大日期是否一致。）
#   k.Primary key驗證
#   l.約束條件檢查
#     -是否有Null？
#     -資料型別等是否符合目標表格定義？
#   m.錯誤處理日誌
# 3.Crontab 每日凌晨執行以上檔案
# 4.改用ELT: 傳統 ETL 預處理後再寫入，但 ELT 會先 Load 到資料倉儲，再用 SQL 做 Transform，擁有更好延展性

import os
import pandas as pd
import MySQLdb
from datetime import datetime



desktop = os.path.join(os.path.expanduser("~"), "Desktop")
csv_file = os.path.join(desktop, "ETL_test_wrong.csv")
csv_file2 = os.path.join(desktop, "ETL_test2.csv")

#read csv
df = pd.read_csv(csv_file)
df2 = pd.read_csv(csv_file2)


#validation
#檢查筆數等於來源系統筆數
assert len(df) ==7

#檢查欄位是否存在
required_columns =["ID", "USER_ID", "Timestamp", "Action"]
for required_column in required_columns:
    if required_column not in df.columns:
        print(f"missing {required_column}")

#缺值
#檢查整張表中所有欄位是否有缺值：
print(df.isnull().sum())
missing_rows = df[df.isnull().any(axis=1)]
# 找出有缺值的資料列（哪幾列有欄位是空的）：
print("有缺值的列：")
print(missing_rows)

#檢查特定欄位是否有缺值:假設你希望 USER_ID 一定要有值：
print("檢查特定欄位是否有缺值：")

print(df[df['Timestamp'].isnull()])
# --- 缺值處理
#刪除有缺值的列（只保留乾淨資料）
df = df.dropna(subset=['USER_ID', 'Timestamp'])

# ---
assert df['USER_ID'].isnull().all()

#檢查欄位型別、格式是否與定義一致？
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
df["Timestamp_str"] = df["Timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
# 查看轉換結果
print(df.head())
# 把 Timestamp 是 NaT 的行刪掉（也就是格式錯誤的資料）
df = df.dropna(subset=['Timestamp'])

# 1. 檢查 id 是否唯一（整欄都不重複）
is_unique = df['ID'].is_unique
print("id 是否唯一:", is_unique)

# 假設 df 是你的資料 DataFrame，Timestamp 欄位名稱為 'Timestamp'
df['Timestamp'] = pd.to_datetime(df['Timestamp'])
# 找最大時間
max_timestamp = df['Timestamp'].max()
print("資料中最新時間為：", max_timestamp)


db = MySQLdb.connect(
        host="127.0.0.1",
        user="root",
        password="my-secret-pw",
    )

cur = db.cursor()
db.select_db("ETL_DB")

cur.execute("""CREATE TABLE USERS (
            ID INT PRIMARY KEY,
            USER_ID VARCHAR(300), 
            Timestamp DATETIME, 
            Action VARCHAR(300));""")

cur.execute("""CREATE TABLE USERS2 (
            ID INT PRIMARY KEY,
            USER_ID VARCHAR(300),  
            TODO VARCHAR(300));""")

# Load寫入 MySQL 資料表
for index, row in df.iterrows():
    sql = "INSERT INTO USERS(ID, USER_ID, Timestamp, Action) VALUES (%s, %s, %s, %s)"
    values = (row['ID'], row['USER_ID'], row['Timestamp'], row['Action'])
    cur.execute(sql, values)

for index, row in df2.iterrows():
    sql = "INSERT INTO USERS2(ID, USER_ID, TODO) VALUES (%s, %s, %s)"
    values = (row['ID'], row['USER_ID'], row['TODO'])
    cur.execute(sql, values)

db.commit()

cur.close()
db.close()