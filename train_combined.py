import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score
import pickle
import time
import json

print("="*70)
print("COMBINED MODEL: MLP (PL) + XGBoost (CFO)")
print("="*70)

embeddings = np.load('embeddings.npy')
df = pd.read_pickle('data.pkl')

with open('model_mlp.pkl', 'rb') as f:
    mlp_bundle = pickle.load(f)
with open('model_xgboost.pkl', 'rb') as f:
    xgb_bundle = pickle.load(f)

model_pl = mlp_bundle['model_pl']
model_cfo = xgb_bundle['model_cfo']
le_pl = mlp_bundle['le_pl']
le_cfo_xgb = xgb_bundle['le_cfo']
scaler = mlp_bundle['scaler']

le_pl_full = LabelEncoder()
y_pl_orig = df['PL'].values
y_pl = le_pl_full.fit_transform(y_pl_orig)

min_samples = 2
vc = pd.Series(y_pl).value_counts()
rare_labels = vc[vc < min_samples].index.tolist()

y_pl_train = y_pl.copy()
for rare in rare_labels:
    original_label = le_pl_full.inverse_transform([rare])[0]
    most_common = df[df['PL'] != original_label]['PL'].mode()[0]
    mask = y_pl_orig == original_label
    y_pl_train[mask] = le_pl_full.transform([most_common])[0]

y_pl_train_enc = le_pl_full.fit_transform(y_pl_train)

indices = np.arange(len(embeddings))
np.random.seed(42)
np.random.shuffle(indices)
split = int(0.8 * len(indices))
train_idx, test_idx = indices[:split], indices[split:]

X_train = embeddings[train_idx]
X_test = embeddings[test_idx]
y_train_pl = y_pl_train_enc[train_idx]
y_test_pl = y_pl[test_idx]
y_test_pl_orig = le_pl_full.inverse_transform(y_pl_train_enc[test_idx])

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"Train: {X_train.shape}, Test: {X_test.shape}")

start = time.time()
y_pred_pl = le_pl_full.inverse_transform(model_pl.predict(X_test_scaled))
acc_pl = accuracy_score(y_test_pl_orig, y_pred_pl)
print(f"PL (MLP) Accuracy: {acc_pl:.4f}, Time: {time.time()-start:.1f}s")

le_cfo = LabelEncoder()
y_train_cfo_orig = df['CFO'].values[train_idx]
le_cfo.fit([str(x) for x in y_train_cfo_orig])
y_train_cfo_enc = le_cfo.transform([str(x) for x in y_train_cfo_orig])

X_train_cfo = np.column_stack([X_train, y_train_pl])
X_test_cfo = np.column_stack([X_test, le_pl_full.transform(y_pred_pl)])

start = time.time()
y_pred_cfo_enc = model_cfo.predict(X_test_cfo)
y_pred_cfo = le_cfo.inverse_transform(y_pred_cfo_enc)
acc_cfo = accuracy_score(df['CFO'].values[test_idx], y_pred_cfo)
print(f"CFO (XGBoost) Accuracy: {acc_cfo:.4f}, Time: {time.time()-start:.1f}s")

model_combined = {
    'model_pl': model_pl,
    'model_cfo': model_cfo,
    'le_pl': le_pl_full,
    'le_cfo': le_cfo,
    'scaler': scaler,
    'pl_source': 'MLP',
    'cfo_source': 'XGBoost'
}

with open('model_combined.pkl', 'wb') as f:
    pickle.dump(model_combined, f)

results = {
    'model': 'MLP+XGBoost',
    'pl_accuracy': float(acc_pl),
    'cfo_accuracy': float(acc_cfo),
    'pl_source': 'MLP',
    'cfo_source': 'XGBoost'
}
with open('results_combined.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nSaved: model_combined.pkl, results_combined.json")
print(f"\nFINAL RESULTS:")
print(f"  PL Accuracy: {acc_pl:.2%} (MLP)")
print(f"  CFO Accuracy: {acc_cfo:.2%} (XGBoost)")
