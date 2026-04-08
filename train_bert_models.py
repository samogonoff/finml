import pymssql
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import warnings
import pickle
import os
warnings.filterwarnings('ignore')

print("="*70)
print("ЗАГРУЗКА ДАННЫХ ИЗ SQL")
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

print("\n" + "="*70)
print("РАЗДЕЛЕНИЕ КОДА НА PL И CFO")
print("="*70)

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
print(f"Уникальных CFO: {df['CFO'].nunique()}")
print(f"Уникальных PL: {df['PL'].nunique()}")

print("\nТоп-10 PL:")
print(df['PL'].value_counts().head(10))

print("\n" + "="*70)
print("СОЗДАНИЕ BERT ЭМБЕДИНГОВ")
print("="*70)

df['Текст'] = df['Наименование'].fillna('').astype(str) + ' ' + df['Получатель'].fillna('').astype(str)

model_name = 'paraphrase-multilingual-MiniLM-L12-v2'
print(f"Модель: {model_name}")

encoder = SentenceTransformer(model_name, device='cuda')

batch_size = 512
texts = df['Текст'].tolist()
embeddings = []

for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    batch_embeddings = encoder.encode(batch, show_progress_bar=False, convert_to_numpy=True)
    embeddings.extend(batch_embeddings)
    if (i + batch_size) % 5000 == 0:
        print(f"  Обработано: {min(i + batch_size, len(texts)):,} / {len(texts):,}")

embeddings = np.array(embeddings)
print(f"Размер эмбедингов: {embeddings.shape}")

print("\n" + "="*70)
print("ОБУЧЕНИЕ МОДЕЛИ PL")
print("="*70)

le_pl = LabelEncoder()
y_pl = le_pl.fit_transform(df['PL'].values)

X_train, X_test, y_train_pl, y_test_pl = train_test_split(embeddings, y_pl, test_size=0.2, random_state=42)

print(f"X_train: {X_train.shape}")
print(f"Классов PL: {len(le_pl.classes_)}")

model_pl = RandomForestClassifier(n_estimators=100, max_depth=20, min_samples_leaf=5, random_state=42, n_jobs=-1)
model_pl.fit(X_train, y_train_pl)

y_pred_pl_test = model_pl.predict(X_test)
acc_pl = accuracy_score(y_test_pl, y_pred_pl_test)
print(f"PL Accuracy: {acc_pl:.4f}")

print("\n" + "="*70)
print("ОБУЧЕНИЕ МОДЕЛИ CFO (с ПРЕДСКАЗАННЫМ PL)")
print("="*70)

train_indices = X_train.shape[0]

pl_predicted_train = y_train_pl

X_train_cfo = np.column_stack([X_train, pl_predicted_train])

le_cfo = LabelEncoder()
le_cfo.fit([str(x) for x in df['CFO'].unique()] + ['UNKNOWN'])

y_train_cfo_orig = df['CFO'].values[:train_indices]
y_train_cfo_enc = np.array([le_cfo.transform([str(x)])[0] for x in y_train_cfo_orig])

print(f"X_train: {X_train_cfo.shape}")
print(f"Классов CFO: {len(le_cfo.classes_)}")

model_cfo = RandomForestClassifier(n_estimators=100, max_depth=20, min_samples_leaf=5, random_state=42, n_jobs=-1)
model_cfo.fit(X_train_cfo, y_train_cfo_enc)

print("\n" + "="*70)
print("ТЕСТ НА TEST ВЫБОРКЕ (реальный сценарий)")
print("="*70)

pl_predicted_test = model_pl.predict(X_test)
X_test_cfo = np.column_stack([X_test, pl_predicted_test])

y_pred_cfo = model_cfo.predict(X_test_cfo)
y_test_cfo_orig = df['CFO'].values[train_indices:train_indices + len(y_pred_cfo)]
y_test_cfo_enc = np.array([le_cfo.transform([str(x)])[0] if str(x) in le_cfo.classes_ else le_cfo.transform(['UNKNOWN'])[0] for x in y_test_cfo_orig])

acc_cfo = accuracy_score(y_test_cfo_enc, y_pred_cfo)
print(f"CFO Accuracy (с предсказанным PL): {acc_cfo:.4f}")

print("\n" + "="*70)
print("СОХРАНЕНИЕ МОДЕЛЕЙ")
print("="*70)

model_bundle = {
    'model_pl': model_pl,
    'model_cfo': model_cfo,
    'le_pl': le_pl,
    'le_cfo': le_cfo,
    'encoder': encoder,
    'embedding_dim': embeddings.shape[1]
}

with open('models_pl_cfo.pkl', 'wb') as f:
    pickle.dump(model_bundle, f)

print("Модели сохранены в models_pl_cfo.pkl")

print("\n" + "="*70)
print("ИТОГИ")
print("="*70)
print(f"""
PL Accuracy: {acc_pl:.2%}
CFO Accuracy (с предсказанным PL): {acc_cfo:.2%}

PL классы: {len(le_pl.classes_)}
CFO классы: {len(le_cfo.classes_)}
""")
