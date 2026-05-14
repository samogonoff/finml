"""
Pipeline: еженедельное переобучение моделей PL и CFO
Flow: SQL → эмбеддинги → обучение → сравнение → сохранение (если лучше)
"""
import time
import json
import warnings
import numpy as np
import pandas as pd
warnings.filterwarnings('ignore')

import pymssql
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import accuracy_score
import xgboost as xgb
import pickle

DB_CONFIG = {
    'server': '10.10.6.15',
    'database': 'FinDWH',
    'user': 'sa',
    'password': '11-future',
}

SQL_QUERY = "SELECT [Дата], [Наименование], [Получатель], [Код] FROM [FinDWH].[dbo].[AccessRU]"
EMBEDDING_MODEL = 'paraphrase-multilingual-MiniLM-L12-v2'
BATCH_SIZE = 512

CURRENT_MODEL_PATH = 'model_final.pkl'
NEW_MODEL_PATH = 'model_final_new.pkl'
RESULTS_PATH = 'results_final.json'

MIN_SAMPLES = 2
TEST_SPLIT = 0.2
RANDOM_STATE = 42


def step(msg):
    print(f"\n{'='*70}")
    print(f"  {msg}")
    print(f"{'='*70}")


def load_data():
    step("ЗАГРУЗКА ДАННЫХ ИЗ SQL")
    conn = pymssql.connect(**DB_CONFIG)
    df = pd.read_sql(SQL_QUERY, conn)
    conn.close()
    print(f"Загружено: {len(df):,} строк")

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
    return df


def create_embeddings(texts):
    step("СОЗДАНИЕ ЭМБЕДДИНГОВ")
    encoder = SentenceTransformer(EMBEDDING_MODEL, device='cuda')
    all_embeddings = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_emb = encoder.encode(batch, show_progress_bar=True, convert_to_numpy=True)
        all_embeddings.extend(batch_emb)
    embeddings = np.array(all_embeddings)
    print(f"Эмбединги: {embeddings.shape}")
    return embeddings


def train_pl(embeddings, df, date_features):
    step("ОБУЧЕНИЕ PL (MLP + дата)")
    le_pl = LabelEncoder()
    y_pl_orig = df['PL'].values
    y_pl = le_pl.fit_transform(y_pl_orig)

    vc = pd.Series(y_pl).value_counts()
    rare_labels = vc[vc < MIN_SAMPLES].index.tolist()

    y_pl_train = y_pl.copy()
    for rare in rare_labels:
        original_label = le_pl.inverse_transform([rare])[0]
        most_common = df[df['PL'] != original_label]['PL'].mode()[0]
        mask = y_pl_orig == original_label
        y_pl_train[mask] = le_pl.transform([most_common])[0]

    y_pl_train_enc = le_pl.fit_transform(y_pl_train)

    indices = np.arange(len(embeddings))
    np.random.seed(RANDOM_STATE)
    np.random.shuffle(indices)
    split = int((1 - TEST_SPLIT) * len(indices))
    train_idx, test_idx = indices[:split], indices[split:]

    X_train_emb = embeddings[train_idx]
    X_test_emb = embeddings[test_idx]
    X_train_date = date_features[train_idx]
    X_test_date = date_features[test_idx]

    X_train_pl = np.hstack([X_train_emb, X_train_date])
    X_test_pl = np.hstack([X_test_emb, X_test_date])

    y_train_pl = y_pl_train_enc[train_idx]
    y_test_pl_orig = le_pl.inverse_transform(y_pl_train_enc[test_idx])

    scaler_pl = StandardScaler()
    X_train_pl_scaled = scaler_pl.fit_transform(X_train_pl)
    X_test_pl_scaled = scaler_pl.transform(X_test_pl)

    model_pl = MLPClassifier(
        hidden_layer_sizes=(128, 64), max_iter=50,
        random_state=RANDOM_STATE, early_stopping=True
    )
    model_pl.fit(X_train_pl_scaled, y_train_pl)

    y_pred_pl = le_pl.inverse_transform(model_pl.predict(X_test_pl_scaled))
    acc_pl = accuracy_score(y_test_pl_orig, y_pred_pl)
    print(f"PL Accuracy: {acc_pl:.4f}")

    return model_pl, le_pl, scaler_pl, acc_pl, train_idx, test_idx, y_pred_pl


def train_cfo(embeddings, df, train_idx, test_idx, y_pred_pl, le_pl):
    step("ОБУЧЕНИЕ CFO (XGBoost)")
    le_cfo = LabelEncoder()
    y_train_cfo_orig = df['CFO'].values[train_idx]
    le_cfo.fit([str(x) for x in y_train_cfo_orig])
    y_train_cfo_enc = le_cfo.transform([str(x) for x in y_train_cfo_orig])

    X_train_emb = embeddings[train_idx]
    X_test_emb = embeddings[test_idx]

    X_train_cfo = np.column_stack([X_train_emb, y_pred_pl])
    X_test_cfo = np.column_stack([X_test_emb, le_pl.transform(y_pred_pl)])

    model_cfo = xgb.XGBClassifier(
        n_estimators=50, max_depth=8, learning_rate=0.1,
        random_state=RANDOM_STATE, n_jobs=-1, eval_metric='mlogloss'
    )
    model_cfo.fit(X_train_cfo, y_train_cfo_enc)

    y_pred_cfo_enc = model_cfo.predict(X_test_cfo)
    y_pred_cfo = le_cfo.inverse_transform(y_pred_cfo_enc)
    acc_cfo = accuracy_score(df['CFO'].values[test_idx], y_pred_cfo)
    print(f"CFO Accuracy: {acc_cfo:.4f}")

    return model_cfo, le_cfo, acc_cfo


def load_current_metrics():
    if not os.path.exists(RESULTS_PATH):
        return None
    with open(RESULTS_PATH) as f:
        return json.load(f)


def save_results(acc_pl, acc_cfo, pl_time, cfo_time):
    results = {
        'model': 'MLP(PL+date) + XGBoost(CFO)',
        'pl_accuracy': float(acc_pl),
        'cfo_accuracy': float(acc_cfo),
        'pl_time': float(pl_time),
        'cfo_time': float(cfo_time),
        'description': 'PL: MLP + embeddings + date | CFO: XGBoost + embeddings + PL'
    }
    with open(RESULTS_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    return results


def main():
    import os

    print("=" * 70)
    print("  PIPELINE: ЕЖЕНЕДЕЛЬНОЕ ПЕРЕОБУЧЕНИЕ МОДЕЛЕЙ")
    print("=" * 70)

    # 1. Load data from SQL
    df = load_data()
    df['Текст'] = df['Наименование'].fillna('').astype(str) + ' ' + df['Получатель'].fillna('').astype(str)

    # 2. Create embeddings
    embeddings = create_embeddings(df['Текст'].tolist())

    # 3. Extract date features
    df['Дата'] = pd.to_datetime(df['Дата'], errors='coerce')
    df['Год'] = df['Дата'].dt.year.fillna(0).astype(int)
    df['Месяц'] = df['Дата'].dt.month.fillna(0).astype(int)
    df['День'] = df['Дата'].dt.day.fillna(0).astype(int)
    df['День_недели'] = df['Дата'].dt.dayofweek.fillna(0).astype(int)
    date_features = df[['Год', 'Месяц', 'День', 'День_недели']].values.astype(float)

    # 4. Train PL
    pl_start = time.time()
    model_pl, le_pl, scaler_pl, acc_pl, train_idx, test_idx, y_pred_pl = train_pl(
        embeddings, df, date_features
    )
    pl_time = time.time() - pl_start

    # 5. Train CFO
    cfo_start = time.time()
    model_cfo, le_cfo, acc_cfo = train_cfo(
        embeddings, df, train_idx, test_idx, y_pred_pl, le_pl
    )
    cfo_time = time.time() - cfo_start

    # 6. Compare with current model
    step("СРАВНЕНИЕ С ТЕКУЩЕЙ МОДЕЛЬЮ")
    current = load_current_metrics()
    if current is not None:
        print(f"Текущая: PL={current['pl_accuracy']:.4f}, CFO={current['cfo_accuracy']:.4f}")
        print(f"Новая:   PL={acc_pl:.4f}, CFO={acc_cfo:.4f}")
        pl_diff = acc_pl - current['pl_accuracy']
        cfo_diff = acc_cfo - current['cfo_accuracy']
        print(f"PL diff: {pl_diff:+.4f}, CFO diff: {cfo_diff:+.4f}")
        replace = (acc_pl >= current['pl_accuracy']) and (acc_cfo >= current['cfo_accuracy'])
    else:
        print("Текущих результатов нет — сохраняю новую модель")
        replace = True

    # 7. Save if better or first run
    step("СОХРАНЕНИЕ")
    if replace or current is None:
        model_bundle = {
            'model_pl': model_pl,
            'model_cfo': model_cfo,
            'le_pl': le_pl,
            'le_cfo': le_cfo,
            'scaler_pl': scaler_pl,
            'pl_features': 'embeddings + date (год, месяц, день, день_недели)',
            'cfo_features': 'embeddings + PL'
        }
        with open(CURRENT_MODEL_PATH, 'wb') as f:
            pickle.dump(model_bundle, f)
        save_results(acc_pl, acc_cfo, pl_time, cfo_time)
        print(f"✓ Модель сохранена: {CURRENT_MODEL_PATH}")
        print(f"  PL={acc_pl:.4f}, CFO={acc_cfo:.4f} (за {pl_time + cfo_time:.1f}s)")
    else:
        print("✗ Новая модель не превзошла текущую — пропускаю сохранение")

    print("\n" + "=" * 70)
    print("  PIPELINE ЗАВЕРШЁН")
    print("=" * 70)


if __name__ == '__main__':
    main()
