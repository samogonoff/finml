"""
Предсказание кодов PL и CFO для данных из Excel файла
"""
import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

# Путь к файлу
# Windows: r'D:\FinML\Реестр платежей март РФ.xlsx'
# Linux/WSL:
file_path = '/mnt/d/FinML/Реестр платежей март РФ.xlsx'

print("="*70)
print("ПРЕДСКАЗАНИЕ КОДОВ PL И CFO")
print("="*70)

print("\n1. Загрузка модели...")
with open('model_combined.pkl', 'rb') as f:
    model_bundle = pickle.load(f)

model_pl = model_bundle['model_pl']
model_cfo = model_bundle['model_cfo']
le_pl = model_bundle['le_pl']
le_cfo = model_bundle['le_cfo']
scaler = model_bundle['scaler']

print("   Модель загружена")

print("\n2. Загрузка данных из Excel...")

df_raw = pd.read_excel(file_path, header=5)
df_raw.columns = df_raw.columns.str.strip()
cols_to_drop = [c for c in df_raw.columns if 'Unnamed' in str(c)]
df = df_raw.drop(columns=cols_to_drop, errors='ignore')

print(f"   Загружено: {len(df)} строк")

print("\n3. Подготовка данных...")

df['Дата'] = pd.to_datetime(df['Дата док'], format='%d.%m.%Y', errors='coerce')
df['Получатель'] = df['Наименование'].str.split('/').str[0].str.strip()
df['Текст'] = df['Наименование'].fillna('').astype(str) + ' ' + df['Получатель'].fillna('')

df_for_predict = df[df['Текст'].str.len() > 0].copy()
print(f"   Для предсказания: {len(df_for_predict)} строк")

print("\n4. Создание эмбедингов...")
encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cuda')
texts = df_for_predict['Текст'].tolist()

batch_size = 256
embeddings = []
for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    batch_embeddings = encoder.encode(batch, show_progress_bar=True, convert_to_numpy=True)
    embeddings.extend(batch_embeddings)

embeddings = np.array(embeddings)
print(f"   Эмбединги: {embeddings.shape}")

print("\n5. Предсказание PL...")
X_scaled = scaler.transform(embeddings)
y_pred_pl_enc = model_pl.predict(X_scaled)
y_pred_pl = le_pl.inverse_transform(y_pred_pl_enc)

print(f"   PL предсказано: {len(y_pred_pl)}")

print("\n6. Предсказание CFO...")
X_with_pl = np.column_stack([embeddings, le_pl.transform(y_pred_pl)])
y_pred_cfo_enc = model_cfo.predict(X_with_pl)
y_pred_cfo = le_cfo.inverse_transform(y_pred_cfo_enc)

print(f"   CFO предсказано: {len(y_pred_cfo)}")

print("\n7. Формирование полного кода...")
df_for_predict['PL_pred'] = y_pred_pl
df_for_predict['CFO_pred'] = y_pred_cfo
df_for_predict['Код_pred'] = df_for_predict['CFO_pred'].astype(str) + df_for_predict['PL_pred'].astype(str)

print("\n" + "="*70)
print("РЕЗУЛЬТАТЫ")
print("="*70)

print("\nРаспределение предсказанных PL:")
print(df_for_predict['PL_pred'].value_counts().head(10))

print("\nРаспределение предсказанных CFO:")
print(df_for_predict['CFO_pred'].value_counts().head(10))

print("\n" + "="*70)
print("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
print("="*70)

df_for_predict.to_excel('predictions.xlsx', index=False)
print("\nРезультаты сохранены в predictions.xlsx")

print("\nПервые 10 строк с предсказаниями:")
print(df_for_predict[['Наименование', 'Сумма СНДС', 'PL_pred', 'CFO_pred', 'Код_pred']].head(10).to_string())
