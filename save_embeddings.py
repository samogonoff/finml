import pymssql
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import pickle
import os

print("="*70)
print("ЗАГРУЗКА И СОХРАНЕНИЕ ДАННЫХ")
print("="*70)

conn = pymssql.connect(
    server='10.10.6.15',
    database='FinDWH',
    user='sa',
    password='11-future'
)

query = "SELECT [Дата], [Наименование], [Получатель], [Код] FROM [FinDWH].[dbo].[AccessRU]"
df = pd.read_sql(query, conn)
conn.close()

print(f"Загружено: {len(df):,} строк")

df = df.dropna(subset=['Код', 'Наименование'])
df['Получатель'] = df['Наименование'].str.split('/').str[0].str.strip()
df['Получатель'] = df['Получатель'].replace('', 'нет значения')
df['Получатель'] = df['Получатель'].fillna('нет значения')

df = df[df['Дата'] >= '2025-01-01']
df = df[df['Код'] != '-']
df = df[df['Код'].str.len() >= 3]

df['CFO'] = df['Код'].str[:-2]
df['PL'] = df['Код'].str[-2:]

print(f"После очистки: {len(df):,} строк")

df['Текст'] = df['Наименование'].fillna('').astype(str) + ' ' + df['Получатель'].fillna('').astype(str)

print("\nСоздание эмбедингов...")
encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cuda')

batch_size = 512
texts = df['Текст'].tolist()
embeddings = []

for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    batch_embeddings = encoder.encode(batch, show_progress_bar=True, convert_to_numpy=True)
    embeddings.extend(batch_embeddings)

embeddings = np.array(embeddings)
print(f"Эмбединги: {embeddings.shape}")

print("\nСохранение...")
np.save('embeddings.npy', embeddings)
df.to_pickle('data.pkl')

print("Сохранено:")
print("  - embeddings.npy")
print("  - data.pkl")
