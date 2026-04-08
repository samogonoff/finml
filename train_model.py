import pymssql
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import warnings
warnings.filterwarnings('ignore')

print("="*70)
print("ЗАГРУЗКА ДАННЫХ")
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
print("СОЗДАНИЕ ПРИЗНАКОВ ИЗ ДАТЫ")
print("="*70)

df['Дата'] = pd.to_datetime(df['Дата'], errors='coerce')
df['День'] = df['Дата'].dt.day
df['Месяц'] = df['Дата'].dt.month
df['Год'] = df['Дата'].dt.year
df['День_недели'] = df['Дата'].dt.dayofweek

print(f"Дата: {df['Дата'].min()} - {df['Дата'].max()}")
print(f"Год: {sorted(df['Год'].dropna().unique().astype(int))}")

print("\n" + "="*70)
print("ОЧИСТКА ДАННЫХ")
print("="*70)

df = df.dropna(subset=['Код', 'Наименование', 'Получатель'])
df = df[df['Код'] != '-']
print(f"После очистки: {len(df):,} строк")
print(f"Уникальных кодов: {df['Код'].nunique()}")

print("\n" + "="*70)
print("СОЗДАНИЕ TF-IDF ЭМБЕДИНГОВ")
print("="*70)

df['Текст'] = df['Наименование'].fillna('') + ' ' + df['Получатель'].fillna('')

tfidf = TfidfVectorizer(max_features=100, ngram_range=(1, 2), min_df=5)
tfidf_matrix = tfidf.fit_transform(df['Текст'])

print(f"Размер TF-IDF матрицы: {tfidf_matrix.shape}")
print(f"Количество признаков: {tfidf_matrix.shape[1]}")

feature_names = tfidf.get_feature_names_out()[:10]
print(f"Примеры признаков: {list(feature_names)}")

print("\n" + "="*70)
print("ПОДГОТОВКА К ОБУЧЕНИЮ")
print("="*70)

num_features = ['День', 'Месяц', 'Год', 'День_недели']
X_num = df[num_features].fillna(0).values

X = np.hstack([X_num, tfidf_matrix.toarray()])
y = df['Код'].values

le = LabelEncoder()
y_encoded = le.fit_transform(y)

X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

print(f"X_train: {X_train.shape}")
print(f"X_test: {X_test.shape}")
print(f"Количество классов: {len(le.classes_)}")

print("\n" + "="*70)
print("ОБУЧЕНИЕ МОДЕЛИ")
print("="*70)

model = RandomForestClassifier(n_estimators=100, max_depth=20, min_samples_leaf=5, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\nAccuracy: {accuracy:.4f}")

print("\n" + "="*70)
print("СОХРАНЕНИЕ МОДЕЛИ")
print("="*70)

import pickle

with open('model.pkl', 'wb') as f:
    pickle.dump({'model': model, 'tfidf': tfidf, 'le': le, 'num_features': num_features}, f)

print("Модель сохранена в model.pkl")

print("\n" + "="*70)
print("ВЫВОДЫ")
print("="*70)
print(f"""
Признаки:
- Числовые из даты: День, Месяц, Год, День_недели (4 признака)
- TF-IDF эмбединги: {tfidf_matrix.shape[1]} признаков
- Всего: {X.shape[1]} признаков

Результаты:
- Точность: {accuracy:.2%}
- Классов: {len(le.classes_)}
""")
