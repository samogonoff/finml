"""
Предсказание кодов PL и CFO для данных из Excel файла
"""
import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

print("="*70)
print("ПРЕДСКАЗАНИЕ КОДОВ PL И CFO")
print("="*70)

print("\n1. Загрузка модели...")
with open('model_final.pkl', 'rb') as f:
    model_bundle = pickle.load(f)

model_pl = model_bundle['model_pl']
model_cfo = model_bundle['model_cfo']
le_pl = model_bundle['le_pl']
le_cfo = model_bundle['le_cfo']
scaler_pl = model_bundle['scaler_pl']

print("   Модель загружена")

print("\n2. Загрузка данных из Excel...")
file_path = 'Реестр платежей март РФ.xlsx'
df = pd.read_excel(file_path, header=5)
df.columns = df.columns.str.strip()

cols_to_drop = [c for c in df.columns if 'Unnamed' in str(c)]
df = df.drop(columns=cols_to_drop, errors='ignore')

print(f"   Загружено: {len(df)} строк")

print("\n3. Обработка данных...")

df['Дата'] = pd.to_datetime(df['Дата док'], format='%d.%m.%Y', errors='coerce')
df['Год'] = df['Дата'].dt.year.fillna(0).astype(int)
df['Месяц'] = df['Дата'].dt.month.fillna(0).astype(int)
df['День'] = df['Дата'].dt.day.fillna(0).astype(int)
df['День_недели'] = df['Дата'].dt.dayofweek.fillna(0).astype(int)

df['Получатель'] = df['Информация'].str.split('/').str[0].str.strip()
df['Получатель'] = df['Получатель'].fillna('')
df['Текст'] = df['Информация'].fillna('').astype(str) + ' ' + df['Получатель'].fillna('')

print(f"   С 'Код УФ': {df['Код УФ'].notna().sum()}")
print(f"   Без 'Код УФ': {df['Код УФ'].isna().sum()}")

print("\n4. Извлечение PL и CFO из 'Код УФ'...")
df['PL_from_code'] = df['Код УФ'].apply(
    lambda x: str(int(x))[-2:] if pd.notna(x) and str(x).replace('.','',1).isdigit() else None
)
df['CFO_from_code'] = df['Код УФ'].apply(
    lambda x: str(int(x))[:-2] if pd.notna(x) and str(x).replace('.','',1).isdigit() and len(str(int(x))) > 2 else None
)

print("\n5. Предсказание PL и CFO для строк без 'Код УФ'...")
mask_no_code = df['PL_from_code'].isna()
rows_to_predict = df[mask_no_code].copy()

if len(rows_to_predict) > 0:
    print(f"   Строк для предсказания: {len(rows_to_predict)}")
    
    encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cuda')
    texts = rows_to_predict['Текст'].tolist()
    
    embeddings = encoder.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    
    date_features = rows_to_predict[['Год', 'Месяц', 'День', 'День_недели']].values.astype(float)
    X_pl = np.hstack([embeddings, date_features])
    X_pl_scaled = scaler_pl.transform(X_pl)
    
    y_pred_pl = le_pl.inverse_transform(model_pl.predict(X_pl_scaled))
    df.loc[mask_no_code, 'PL_predicted'] = y_pred_pl
    
    pl_encoded = le_pl.transform(y_pred_pl)
    X_cfo = np.column_stack([embeddings, pl_encoded])
    y_pred_cfo = le_cfo.inverse_transform(model_cfo.predict(X_cfo))
    df.loc[mask_no_code, 'CFO_predicted'] = y_pred_cfo

df['PL_final'] = df['PL_from_code'].fillna(df['PL_predicted'])
df['CFO_final'] = df['CFO_from_code'].fillna(df['CFO_predicted'])
df['Код_final'] = df['CFO_final'].astype(str) + df['PL_final'].astype(str)

print("\n" + "="*70)
print("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
print("="*70)

output_path = 'predictions_final_v2.xlsx'
df.to_excel(output_path, index=False)
print(f"\nСохранено: {output_path}")

print("\n" + "="*70)
print("СТАТИСТИКА")
print("="*70)
print(f"\nВсего записей: {len(df)}")
print(f"PL/CFO извлечено из 'Код УФ': {df['PL_from_code'].notna().sum()}")
print(f"PL предсказано моделью: {df['PL_predicted'].notna().sum() if 'PL_predicted' in df.columns else 0}")
print(f"CFO предсказано моделью: {df['CFO_predicted'].notna().sum() if 'CFO_predicted' in df.columns else 0}")

print("\nТоп-10 PL:")
print(df['PL_final'].value_counts().head(10))

print("\nТоп-10 CFO:")
print(df['CFO_final'].value_counts().head(10))
