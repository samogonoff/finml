"""
Исследование данных из Excel файла
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

file_path = 'Реестр платежей март РФ.xlsx'

print("="*70)
print("ИССЛЕДОВАНИЕ ДАННЫХ ИЗ EXCEL ФАЙЛА")
print("="*70)

print(f"\nФайл: {file_path}")
print(f"Существует: {os.path.exists(file_path)}")

print("\n" + "="*70)
print("1. ЗАГРУЗКА ДАННЫХ")
print("="*70)

df_raw = pd.read_excel(file_path, header=None)
print(f"Размер (raw): {df_raw.shape}")

print("\nПервые 10 строк (raw):")
for i in range(10):
    print(f"Строка {i}: {str(df_raw.iloc[i, 0])[:80]}...")

print("\n" + "="*70)
print("2. ПОИСК СТРОКИ С ЗАГОЛОВКАМИ")
print("="*70)

for i in range(10):
    row_values = [str(v)[:30] for v in df_raw.iloc[i].tolist()[:10]]
    if '№ п/п' in str(df_raw.iloc[i].tolist()):
        print(f"Заголовки найдены в строке {i}")
        header_row = i
        break

print("\n" + "="*70)
print("3. ЗАГРУЗКА С ПРАВИЛЬНЫМ СМЕЩЕНИЕМ")
print("="*70)

df = pd.read_excel(file_path, header=5)
df.columns = df.columns.str.strip()

cols_to_drop = [c for c in df.columns if 'Unnamed' in str(c)]
df = df.drop(columns=cols_to_drop, errors='ignore')

print(f"Размер после очистки: {df.shape}")
print(f"\nКолоники: {df.columns.tolist()}")

print("\n" + "="*70)
print("4. ТИПЫ ДАННЫХ И ПРОПУСКИ")
print("="*70)

print("\nТипы данных:")
print(df.dtypes)

print("\nПропуски:")
print(df.isnull().sum())

print("\n" + "="*70)
print("5. ПЕРВЫЕ СТРОКИ")
print("="*70)

print(df.head(10).to_string())

print("\n" + "="*70)
print("6. СТАТИСТИКА")
print("="*70)

print(df.describe())

print("\n" + "="*70)
print("7. АНАЛИЗ ЦЕЛЕВОЙ ПЕРЕМЕННОЙ (Код УФ)")
print("="*70)

target_col = 'Код УФ'
print(f"\nУникальных значений: {df[target_col].nunique()}")
print(f"Пропусков: {df[target_col].isnull().sum()} ({df[target_col].isnull().sum()/len(df)*100:.1f}%)")

print("\nТоп-15 кодов:")
print(df[target_col].value_counts().head(15))

print("\n" + "="*70)
print("8. АНАЛИЗ ТЕКСТОВЫХ ПОЛЕЙ")
print("="*70)

print("\nПоле 'Информация':")
print(f"Пропусков: {df['Информация'].isnull().sum()}")
print("Примеры:")
for i, text in enumerate(df['Информация'].dropna().head(5)):
    print(f"  {i+1}. {text[:150]}...")

print("\nПоле 'Информация' (аналог Наименования):")
print(f"Пропусков: {df['Информация'].isnull().sum()}")
print("Примеры:")
for i, text in enumerate(df['Информация'].dropna().head(10)):
    print(f"  {i+1}. {text}")

print("\n" + "="*70)
print("9. ИЗВЛЕЧЕНИЕ ПОЛУЧАТЕЛЯ ИЗ НАИМЕНОВАНИЯ")
print("="*70)

df['Получатель'] = df['Информация'].str.split('/').str[0].str.strip()

print(f"\nУникальных получателей: {df['Получатель'].nunique()}")
print("\nТоп-15 получателей:")
print(df['Получатель'].value_counts().head(15))

print("\n" + "="*70)
print("10. АНАЛИЗ СУММ")
print("="*70)

print("\nСумма СНДС:")
print(df['Сумма СНДС'].describe())

print("\n" + "="*70)
print("11. ПОДГОТОВКА ДАННЫХ ДЛЯ МОДЕЛИ")
print("="*70)

df['Текст'] = df['Информация'].fillna('').astype(str) + ' ' + df['Получатель'].fillna('')

df_model = df.dropna(subset=['Код УФ']).copy()
print(f"\nЗаписей с кодом: {len(df_model)} ({len(df_model)/len(df)*100:.1f}%)")

df_model['Код_стр'] = df_model['Код УФ'].astype(int).astype(str)
df_model['CFO'] = df_model['Код_стр'].str[:-2]
df_model['PL'] = df_model['Код_стр'].str[-2:]

print(f"Уникальных CFO: {df_model['CFO'].nunique()}")
print(f"Уникальных PL: {df_model['PL'].nunique()}")

print("\nТоп-10 PL:")
print(df_model['PL'].value_counts().head(10))

print("\nТоп-10 CFO:")
print(df_model['CFO'].value_counts().head(10))

df_model.to_pickle('excel_data_prepared.pkl')
print("\nДанные сохранены в excel_data_prepared.pkl")

print("\n" + "="*70)
print("ИТОГОВАЯ СВОДКА")
print("="*70)
print(f"Всего записей: {len(df)}")
print(f"Записей с кодом: {len(df_model)}")
print(f"Уникальных CFO: {df_model['CFO'].nunique()}")
print(f"Уникальных PL: {df_model['PL'].nunique()}")
print(f"\nСуммы (СНДС):")
print(f"  Мин: {df_model['Сумма СНДС'].min():,.2f}")
print(f"  Макс: {df_model['Сумма СНДС'].max():,.2f}")
print(f"  Среднее: {df_model['Сумма СНДС'].mean():,.2f}")
