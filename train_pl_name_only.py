"""
Обучение модели PL только по Наименование (без Получателя)
"""
import pymssql
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.neural_network import MLPClassifier
from sentence_transformers import SentenceTransformer
import pickle
import time

print("="*70)
print("ОБУЧЕНИЕ PL ТОЛЬКО ПО НАИМЕНОВАНИЮ")
print("="*70)

conn = pymssql.connect(
    server='10.10.6.15',
    database='FinDWH',
    user='sa',
    password='11-future'
)

query = "SELECT [Наименование], [Код] FROM [FinDWH].[dbo].[AccessRU]"
df = pd.read_sql(query, conn)
conn.close()

print(f"\nЗагружено: {len(df):,} строк")

df = df.dropna(subset=['Код', 'Наименование'])
df = df[df['Код'] != '-']
df = df[df['Код'].str.len() >= 3]
df = df[df['Дата'] >= '2025-01-01'] if 'Дата' in df.columns else df

df['PL'] = df['Код'].str[-2:]

df = df[df['PL'].notna()]
df = df[df['PL'] != '']

print(f"После очистки: {len(df):,} строк")
print(f"Уникальных PL: {df['PL'].nunique()}")

print("\n" + "="*70)
print("СОЗДАНИЕ ЭМБЕДИНГОВ (ТОЛЬКО НАИМЕНОВАНИЕ)")
print("="*70)

encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device='cuda')

texts = df['Наименование'].fillna('').astype(str).tolist()
batch_size = 512
embeddings = []

for i in range(0, len(texts), batch_size):
    batch = texts[i:i+batch_size]
    batch_embeddings = encoder.encode(batch, show_progress_bar=True, convert_to_numpy=True)
    embeddings.extend(batch_embeddings)

embeddings = np.array(embeddings)
print(f"Эмбединги: {embeddings.shape}")

print("\n" + "="*70)
print("ОБУЧЕНИЕ PL (ТОЛЬКО НАИМЕНОВАНИЕ)")
print("="*70)

le_pl = LabelEncoder()
y_pl_orig = df['PL'].values
y_pl = le_pl.fit_transform(y_pl_orig)

min_samples = 2
vc = pd.Series(y_pl).value_counts()
rare_labels = vc[vc < min_samples].index.tolist()

y_pl_train = y_pl.copy()
for rare in rare_labels:
    original_label = le_pl.inverse_transform([rare])[0]
    most_common = df[df['PL'] != original_label]['PL'].mode()[0]
    mask = y_pl_orig == original_label
    y_pl_train[mask] = le_pl.transform([most_common])[0]

y_pl_train_enc = le_pl.fit_transform(y_pl_train)

indices = np.arange(len(embeddings))
np.random.seed(42)
np.random.shuffle(indices)
split = int(0.8 * len(indices))
train_idx, test_idx = indices[:split], indices[split:]

X_train = embeddings[train_idx]
X_test = embeddings[test_idx]
y_train_pl = y_pl_train_enc[train_idx]
y_test_pl = y_pl[test_idx]
y_test_pl_orig = le_pl.inverse_transform(y_pl_train_enc[test_idx])

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"X_train: {X_train.shape}")
print(f"PL classes: {len(le_pl.classes_)}")

start = time.time()
model_pl = MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=50, random_state=42, early_stopping=True)
model_pl.fit(X_train_scaled, y_train_pl)
train_time = time.time() - start

y_pred_pl = le_pl.inverse_transform(model_pl.predict(X_test_scaled))
acc_pl = accuracy_score(y_test_pl_orig, y_pred_pl)
print(f"PL Accuracy: {acc_pl:.4f} ({train_time:.1f}s)")

print("\n" + "="*70)
print("СРАВНЕНИЕ С МОДЕЛЬЮ С ПОЛУЧАТЕЛЕМ")
print("="*70)
print(f"""
| Модель                     | PL Accuracy |
|---------------------------|-------------|
| PL (Наименование)         | {acc_pl*100:.2f}%      |
| PL (Наименование + Получатель) | 91.50%     |

Изменение: {(acc_pl-0.9150)*100:+.2f}%
""")
