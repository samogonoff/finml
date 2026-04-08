import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from catboost import CatBoostClassifier
import pickle
import time
import json

print("="*70)
print("CATBOOST MODEL")
print("="*70)

embeddings = np.load('embeddings.npy')
df = pd.read_pickle('data.pkl')

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

y_pl_train = le_pl.fit_transform(y_pl_train)

indices = np.arange(len(embeddings))
np.random.seed(42)
np.random.shuffle(indices)
split = int(0.8 * len(indices))
train_idx, test_idx = indices[:split], indices[split:]
train_size = len(train_idx)

X_train = embeddings[train_idx]
X_test = embeddings[test_idx]
y_train_pl = y_pl_train[train_idx]
y_test_pl = y_pl[test_idx]
y_test_pl_orig = le_pl.inverse_transform(y_pl_train[test_idx])

print(f"Train: {X_train.shape}, Test: {X_test.shape}")
print(f"PL classes: {len(le_pl.classes_)}")

start = time.time()
model_pl = CatBoostClassifier(iterations=50, depth=6, learning_rate=0.1, random_state=42, verbose=0)
model_pl.fit(X_train, y_train_pl)
pl_time = time.time() - start
y_pred_pl = le_pl.inverse_transform(model_pl.predict(X_test))
acc_pl = accuracy_score(y_test_pl_orig, y_pred_pl)
print(f"PL Accuracy: {acc_pl:.4f}, Time: {pl_time:.1f}s")

le_cfo = LabelEncoder()
y_train_cfo_orig = df['CFO'].values[train_idx]
le_cfo.fit([str(x) for x in y_train_cfo_orig])
y_train_cfo_enc = le_cfo.transform([str(x) for x in y_train_cfo_orig])

X_train_cfo = np.column_stack([X_train, y_train_pl])
X_test_cfo = np.column_stack([X_test, le_pl.transform(y_pred_pl)])

start = time.time()
model_cfo = CatBoostClassifier(iterations=50, depth=6, learning_rate=0.1, random_state=42, verbose=0)
model_cfo.fit(X_train_cfo, y_train_cfo_enc)
cfo_time = time.time() - start

y_test_cfo_orig = df['CFO'].values[test_idx]
y_pred_cfo_enc = model_cfo.predict(X_test_cfo)
y_pred_cfo = le_cfo.inverse_transform(y_pred_cfo_enc)
acc_cfo = accuracy_score(y_test_cfo_orig, y_pred_cfo)
print(f"CFO Accuracy: {acc_cfo:.4f}, Time: {cfo_time:.1f}s")

model_bundle = {'model_pl': model_pl, 'model_cfo': model_cfo, 'le_pl': le_pl, 'le_cfo': le_cfo}
with open('model_catboost.pkl', 'wb') as f:
    pickle.dump(model_bundle, f)

results = {'model': 'CatBoost', 'pl_accuracy': float(acc_pl), 'cfo_accuracy': float(acc_cfo), 'pl_time': float(pl_time), 'cfo_time': float(cfo_time)}
with open('results_catboost.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nSaved: model_catboost.pkl, results_catboost.json")
