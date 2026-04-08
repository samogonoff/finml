"""
Обучение модели MLP (PL) + XGBoost (CFO) с признаками из даты
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score
from sklearn.neural_network import MLPClassifier
import xgboost as xgb
import pickle
import time
import json

print("="*70)
print("ОБУЧЕНИЕ MLP+XGBOOST С ДАТОЙ")
print("="*70)

embeddings = np.load('embeddings.npy')
df = pd.read_pickle('data.pkl')

print(f"\nДанные: {embeddings.shape}")
print(f"Даты: {df['Дата'].min()} - {df['Дата'].max()}")

print("\n" + "="*70)
print("ИЗВЛЕЧЕНИЕ ПРИЗНАКОВ ИЗ ДАТЫ")
print("="*70)

df['Дата'] = pd.to_datetime(df['Дата'], errors='coerce')
df['Год'] = df['Дата'].dt.year.fillna(0).astype(int)
df['Месяц'] = df['Дата'].dt.month.fillna(0).astype(int)
df['День'] = df['Дата'].dt.day.fillna(0).astype(int)
df['День_недели'] = df['Дата'].dt.dayofweek.fillna(0).astype(int)

date_features = df[['Год', 'Месяц', 'День', 'День_недели']].values
print(f"Признаки даты: {date_features.shape}")

date_features_scaled = StandardScaler().fit_transform(date_features)

print("\n" + "="*70)
print("ОБУЧЕНИЕ PL (MLP)")
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

X_train_emb = embeddings[train_idx]
X_test_emb = embeddings[test_idx]
X_train_date = date_features_scaled[train_idx]
X_test_date = date_features_scaled[test_idx]

X_train = np.hstack([X_train_emb, X_train_date])
X_test = np.hstack([X_test_emb, X_test_date])

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
pl_time = time.time() - start

y_pred_pl = le_pl.inverse_transform(model_pl.predict(X_test_scaled))
acc_pl = accuracy_score(y_test_pl_orig, y_pred_pl)
print(f"PL Accuracy: {acc_pl:.4f} ({pl_time:.1f}s)")

print("\n" + "="*70)
print("ОБУЧЕНИЕ CFO (XGBoost)")
print("="*70)

le_cfo = LabelEncoder()
y_train_cfo_orig = df['CFO'].values[train_idx]
le_cfo.fit([str(x) for x in y_train_cfo_orig])
y_train_cfo_enc = le_cfo.transform([str(x) for x in y_train_cfo_orig])

X_train_cfo = np.hstack([X_train, np.column_stack([y_train_pl, date_features_scaled[train_idx]])])
X_test_cfo = np.hstack([X_test, np.column_stack([le_pl.transform(y_pred_pl), date_features_scaled[test_idx]])])

start = time.time()
model_cfo = xgb.XGBClassifier(n_estimators=30, max_depth=6, learning_rate=0.1, random_state=42, n_jobs=-1, eval_metric='mlogloss')
model_cfo.fit(X_train_cfo, y_train_cfo_enc)
cfo_time = time.time() - start

y_pred_cfo_enc = model_cfo.predict(X_test_cfo)
y_pred_cfo = le_cfo.inverse_transform(y_pred_cfo_enc)
acc_cfo = accuracy_score(df['CFO'].values[test_idx], y_pred_cfo)
print(f"CFO Accuracy: {acc_cfo:.4f} ({cfo_time:.1f}s)")

print("\n" + "="*70)
print("СОХРАНЕНИЕ МОДЕЛЕЙ")
print("="*70)

model_bundle = {
    'model_pl': model_pl,
    'model_cfo': model_cfo,
    'le_pl': le_pl,
    'le_cfo': le_cfo,
    'scaler': scaler,
    'features': ['embeddings', 'год', 'месяц', 'день', 'день_недели']
}

with open('model_combined_with_date.pkl', 'wb') as f:
    pickle.dump(model_bundle, f)

results = {
    'model': 'MLP+XGBoost+Date',
    'pl_accuracy': float(acc_pl),
    'cfo_accuracy': float(acc_cfo),
    'pl_time': float(pl_time),
    'cfo_time': float(cfo_time),
    'features': 'embeddings + date features (год, месяц, день, день_недели)'
}
with open('results_combined_with_date.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "="*70)
print("ИТОГИ")
print("="*70)
print(f"""
PL Accuracy: {acc_pl:.4f} (MLP)
CFO Accuracy: {acc_cfo:.4f} (XGBoost)

Сравнение с моделью без даты:
| Метрика  | Без даты | С датой  | Изменение |
|----------|----------|----------|-----------|
| PL       | 91.45%   | {acc_pl*100:.2f}%   | {(acc_pl-0.9145)*100:+.2f}%   |
| CFO      | 60.94%   | {acc_cfo*100:.2f}%   | {(acc_cfo-0.6094)*100:+.2f}%   |

Сохранено: model_combined_with_date.pkl
""")
