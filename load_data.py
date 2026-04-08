import pymssql
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()

conn = pymssql.connect(
    server=os.getenv('DB_SERVER'),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)

query = """
SELECT  [КодСтроки]
      ,[Подразделение]
      ,[Отделы]
      ,[Затраты]
      ,[Дата]
      ,[Сумма]
      ,[Курс]
      ,[РосРубль]
      ,[Код]
      ,[Наименование]
      ,[Получатель]
      ,[Проекты]
      ,[ЮрЛицо]
  FROM [FinDWH].[dbo].[AccessRU]
"""

df = pd.read_sql(query, conn)
conn.close()

print(f"Загружено строк: {len(df)}")
print(f"Колоники: {df.columns.tolist()}")
print(f"\nПервые 5 строк:")
print(df.head())
print(f"\nТипы данных:")
print(df.dtypes)
print(f"\nПропущенные значения:")
print(df.isnull().sum())
