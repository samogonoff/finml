import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import warnings
warnings.filterwarnings('ignore')

# Загрузка данных
print("="*70)
print("ЗАГРУЗКА И ПОДГОТОВКА ДАННЫХ")
print("="*70)

df = pd.read_excel('Реестр платежей март РФ.xlsx', header=5)
df.columns = df.columns.str.strip()

# Удаляем служебные колонки
cols_to_drop = [c for c in df.columns if 'Unnamed' in c or c == 'Unnamed: 1' or c == 'Unnamed: 3' or c == 'Unnamed: 5' or c == 'Unnamed: 7']
df = df.drop(columns=cols_to_drop, errors='ignore')

print(f"Размер данных: {df.shape}")
print(f"Колоники: {df.columns.tolist()}")

# Целевая переменная
TARGET = 'Код УФ'

# Удаляем строки без целевой переменной
df_model = df.dropna(subset=[TARGET]).copy()
print(f"\nЗаписей с известным '{TARGET}': {len(df_model)}")

# Преобразуем дату
df_model['Дата док'] = pd.to_datetime(df_model['Дата док'], format='%d.%m.%Y', errors='coerce')
df_model['День'] = df_model['Дата док'].dt.day
df_model['Месяц'] = df_model['Дата док'].dt.month
df_model['День_недели'] = df_model['Дата док'].dt.dayofweek

print("\n" + "="*70)
print("РАЗВЕДОЧИТЕЛЬНЫЙ АНАЛИЗ ДАННЫХ (EDA)")
print("="*70)

# 1. Анализ целевой переменной
print("\n1. АНАЛИЗ ЦЕЛЕВОЙ ПЕРЕМЕННОЙ")
print(f"   Количество классов: {df_model[TARGET].nunique()}")
print(f"   Распределение топ-10:")
print(df_model[TARGET].value_counts().head(10))

# 2. Анализ признаков
print("\n2. АНАЛИЗ ПРИЗНАКОВ")
cat_features = ['Документ', 'Организация', 'Валюта', 'Подразделение УФ']
num_features = ['Сумма СНДС', 'Сумма НДС', 'Сумма без НДС', 'День', 'Месяц', 'День_недели']

for col in cat_features:
    if col in df_model.columns:
        print(f"   {col}: {df_model[col].nunique()} уникальных")

for col in num_features:
    if col in df_model.columns:
        print(f"   {col}: min={df_model[col].min():.2f}, max={df_model[col].max():.2f}")

# 3. Подготовка данных для модели
print("\n" + "="*70)
print("ПОДГОТОВКА К ОБУЧЕНИЮ")
print("="*70)

# Кодируем категориальные признаки
label_encoders = {}
df_encoded = df_model.copy()

for col in cat_features:
    if col in df_encoded.columns:
        le = LabelEncoder()
        df_encoded[col] = df_encoded[col].fillna('Unknown')
        df_encoded[col] = le.fit_transform(df_encoded[col].astype(str))
        label_encoders[col] = le

# Выбираем признаки
feature_cols = ['Сумма СНДС', 'Сумма НДС', 'Сумма без НДС', 
                'Организация', 'День', 'Месяц', 'День_недели']
feature_cols = [c for c in feature_cols if c in df_encoded.columns]

X = df_encoded[feature_cols].fillna(0)
y = df_encoded[TARGET].astype(int)

print(f"\nРазмер признаков: {X.shape}")
print(f"Количество классов: {y.nunique()}")

# Объединяем редкие классы (менее 3 представителей)
min_samples = 3
class_counts = y.value_counts()
rare_classes = class_counts[class_counts < min_samples].index
y_grouped = y.copy()
y_grouped = y_grouped.apply(lambda x: -1 if x in rare_classes else int(x))

print(f"\nПосле объединения редких классов:")
print(f"  Уникальных классов: {y_grouped.nunique()}")

# Разделение на train/test (без стратификации для упрощения)
X_train, X_test, y_train, y_test = train_test_split(X, y_grouped, test_size=0.2, random_state=42)
print(f"Train: {len(X_train)}, Test: {len(X_test)}")

# Обучение Random Forest
print("\n" + "="*70)
print("ОБУЧЕНИЕ МОДЕЛИ Random Forest")
print("="*70)

model = RandomForestClassifier(n_estimators=100, max_depth=15, min_samples_leaf=2, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

# Оценка
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"\nAccuracy: {accuracy:.4f}")

print("\nТоп-5 важных признаков:")
importances = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
print(importances)

print("\n" + "="*70)
print("ВЫВОДЫ")
print("="*70)
print("""
1. Данные содержат 1967 записей для обучения
2. 725 уникальных кодов (классов) - многоклассовая классификация
3. Точность модели зависит от распределения классов
4. Для улучшения модели можно:
   - Добавить текстовые признаки из 'Информация'
   - Использовать иерархическую классификацию
   - Применить методы обработки несбалансированных данных
""")
