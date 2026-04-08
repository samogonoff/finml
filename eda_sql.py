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
SELECT  [КодСтроки], [Подразделение], [Отделы], [Затраты], [Дата], 
        [Сумма], [Курс], [РосРубль], [Код], [Наименование], 
        [Получатель], [Проекты], [ЮрЛицо]
  FROM [FinDWH].[dbo].[AccessRU]
"""

df = pd.read_sql(query, conn)
conn.close()

print("="*70)
print("РАЗВЕДОЧИТЕЛЬНЫЙ АНАЛИЗ ДАННЫХ (EDA)")
print("="*70)

print(f"\n1. РАЗМЕР: {df.shape[0]:,} строк, {df.shape[1]} колонок")

print("\n2. ПРОПУСКИ:")
missing = df.isnull().sum()
print(f"   Код: {missing['Код']:,} ({missing['Код']/len(df)*100:.1f}%)")
print(f"   Получатель: {missing['Получатель']:,} ({missing['Получатель']/len(df)*100:.1f}%)")

print("\n3. ЦЕЛЕВАЯ ПЕРЕМЕННАЯ 'Код':")
print(f"   Уникальных: {df['Код'].nunique()}")
print(f"   Пропусков: {df['Код'].isnull().sum():,}")
print(f"\n   Топ-15:")
print(df['Код'].value_counts().head(15))

print("\n4. КАТЕГОРИАЛЬНЫЕ ПРИЗНАКИ:")
for col in ['Подразделение', 'Отделы', 'Затраты', 'ЮрЛицо']:
    print(f"   {col}: {df[col].nunique()} уникальных")

print("\n5. ЧИСЛОВЫЕ ПРИЗНАКИ:")
print(df[['Сумма', 'Курс', 'РосРубль']].describe())

print("\n6. ДИАПАЗОН ДАТ:")
print(f"   От: {df['Дата'].min()}")
print(f"   До: {df['Дата'].max()}")

print("\n" + "="*70)
print("ПОДГОТОВКА К ОБУЧЕНИЮ")
print("="*70)

df_model = df.dropna(subset=['Код']).copy()
print(f"\nЗаписей с известным Код: {len(df_model):,} ({len(df_model)/len(df)*100:.1f}%)")
print(f"Уникальных кодов: {df_model['Код'].nunique()}")
