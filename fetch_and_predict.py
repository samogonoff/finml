"""
Fetch data from 1C endpoint and predict PL/CFO codes
Usage: python fetch_and_predict.py <region> <date_from> <date_to>
  date format: YYYYMMDD
"""
import sys
import json
import base64
import urllib.request
import warnings
warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import pickle
import tempfile
import os
import re

ENDPOINTS = {
    'RU': 'http://10.10.6.64/buh_rf/hs/Exchange/CashTransactions?DateN={start}&DateK={end}',
}

AUTH = ('Обмен1С', '4AfS2%p-#L^%T$S')


def fetch_from_1c(url):
    credentials = base64.b64encode(
        f'{AUTH[0]}:{AUTH[1]}'.encode('utf-8')
    ).decode('ascii')
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Basic {credentials}')
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def parse_doc_ref(s):
    doc_type = ''
    num = ''
    details = s or ''
    if not s:
        return doc_type, num, details
    parts = s.split()
    if len(parts) >= 1:
        doc_type = parts[0]
    for part in parts:
        if re.match(r'^[А-Я]+-\d+', part):
            num = part
            break
    return doc_type, num, details


def map_1c_record(rec):
    doc_type, num, details = parse_doc_ref(rec.get('Ссылка', ''))
    info = rec.get('Информация', '') or ''
    recipient = info.split('/')[0].strip() if '/' in info else ''

    currency_map = {'643': 'руб.', '156': 'юань', '978': 'евро', '840': 'долл.'}
    currency = currency_map.get(str(rec.get('Валюта', '')), str(rec.get('Валюта', '')))

    raw_date = rec.get('ДатаДок', '')
    date_display = ''
    if raw_date and len(raw_date) >= 10:
        parts = raw_date[:10].split('-')
        date_display = f'{parts[2]}.{parts[1]}.{parts[0]}'

    return {
        'num': num,
        'op_type': rec.get('Документ', ''),
        'doc_type': doc_type,
        'details': details,
        'date': date_display,
        'currency': currency,
        'amount_doc': str(rec.get('СуммаСНДС', '')),
        'amount_cur': '',
        'amount_rub': str(rec.get('СуммаСНДС', '')),
        'info': info,
        'recipient': recipient,
        'code_uf': str(rec.get('КодУФ', '')),
        'department': str(rec.get('ПодразделениеУФ', '')),
        'debit': str(rec.get('СуммаСНДС', '')) if rec.get('Документ', '').startswith('Списание') else '',
        'debit2': str(rec.get('СуммаСНДС', '')) if rec.get('Документ', '').startswith('Списание') else '',
        'credit': str(rec.get('СуммаСНДС', '')) if not rec.get('Документ', '').startswith('Списание') else '',
        'credit2': str(rec.get('СуммаСНДС', '')) if not rec.get('Документ', '').startswith('Списание') else '',
    }


def load_model():
    with open('model_final.pkl', 'rb') as f:
        return pickle.load(f)


def predict(records):
    model_bundle = load_model()
    model_pl = model_bundle['model_pl']
    model_cfo = model_bundle['model_cfo']
    le_pl = model_bundle['le_pl']
    le_cfo = model_bundle['le_cfo']
    scaler_pl = model_bundle['scaler_pl']

    df = pd.DataFrame(records)

    df['recipient'] = df['info'].astype(str).str.split('/').str[0].str.strip()
    df['text'] = df['info'].fillna('').astype(str) + ' ' + df['recipient'].fillna('')

    df['date_parsed'] = pd.to_datetime(df['date'], format='%d.%m.%Y', errors='coerce')
    df['year'] = df['date_parsed'].dt.year.fillna(0).astype(int)
    df['month'] = df['date_parsed'].dt.month.fillna(0).astype(int)
    df['day'] = df['date_parsed'].dt.day.fillna(0).astype(int)
    df['weekday'] = df['date_parsed'].dt.dayofweek.fillna(0).astype(int)

    df['pl_from_code'] = df['code_uf'].apply(
        lambda x: str(int(x))[-2:] if pd.notna(x) and str(x).replace('.', '', 1).replace('-', '', 1).isdigit() and len(str(int(x))) >= 2 else None
    )
    df['cfo_from_code'] = df['code_uf'].apply(
        lambda x: str(int(x))[:-2] if pd.notna(x) and str(x).replace('.', '', 1).replace('-', '', 1).isdigit() and len(str(int(x))) > 2 else None
    )

    mask_no_code = df['pl_from_code'].isna()
    rows_to_predict = df[mask_no_code].copy()

    if len(rows_to_predict) > 0:
        device = 'cuda'
        from sentence_transformers import SentenceTransformer
        encoder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2', device=device)
        texts = rows_to_predict['text'].tolist()
        embeddings = encoder.encode(texts, show_progress_bar=False, convert_to_numpy=True)

        date_features = rows_to_predict[['year', 'month', 'day', 'weekday']].values.astype(float)
        X_pl = np.hstack([embeddings, date_features])
        X_pl_scaled = scaler_pl.transform(X_pl)

        y_pred_pl = le_pl.inverse_transform(model_pl.predict(X_pl_scaled))

        pl_encoded = le_pl.transform(y_pred_pl)
        X_cfo = np.column_stack([embeddings, pl_encoded])
        y_pred_cfo = le_cfo.inverse_transform(model_cfo.predict(X_cfo))

        df.loc[mask_no_code, 'pl_predicted'] = y_pred_pl
        df.loc[mask_no_code, 'cfo_predicted'] = y_pred_cfo

    df['pl'] = df['pl_from_code'].fillna(df.get('pl_predicted', '')).astype(str)
    df['cfo'] = df['cfo_from_code'].fillna(df.get('cfo_predicted', '')).astype(str)
    df['pl_source'] = df['pl_from_code'].apply(lambda x: 'code' if pd.notna(x) else 'predicted')
    df['cfo_source'] = df['cfo_from_code'].apply(lambda x: 'code' if pd.notna(x) else 'predicted')
    df['pl'] = df['pl'].str.replace(r'\.0$', '', regex=True)
    df['cfo'] = df['cfo'].str.replace(r'\.0$', '', regex=True)

    result = []
    for _, row in df.iterrows():
        result.append({
            'num': str(row.get('num', '')),
            'op_type': str(row.get('op_type', '')),
            'doc_type': str(row.get('doc_type', '')),
            'details': str(row.get('details', '')),
            'date': str(row.get('date', '')),
            'currency': str(row.get('currency', '')),
            'amount_doc': str(row.get('amount_doc', '')),
            'amount_cur': str(row.get('amount_cur', '')),
            'amount_rub': str(row.get('amount_rub', '')),
            'info': str(row.get('info', '')),
            'recipient': str(row.get('recipient', '')),
            'code_uf': str(row.get('code_uf', '')),
            'department': str(row.get('department', '')),
            'debit': str(row.get('debit', '')),
            'debit2': str(row.get('debit2', '')),
            'credit': str(row.get('credit', '')),
            'credit2': str(row.get('credit2', '')),
            'pl': str(row.get('pl', '')),
            'cfo': str(row.get('cfo', '')),
            'pl_source': str(row.get('pl_source', 'predicted')),
            'cfo_source': str(row.get('cfo_source', 'predicted')),
            'is_modified': False,
        })
    return result


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: python fetch_and_predict.py <region> <date_from> <date_to>", file=sys.stderr)
        sys.exit(1)

    region = sys.argv[1]
    date_from = sys.argv[2]
    date_to = sys.argv[3]

    if region not in ENDPOINTS:
        print(f"Unknown region: {region}", file=sys.stderr)
        print(f"Available: {list(ENDPOINTS.keys())}", file=sys.stderr)
        sys.exit(1)

    url = ENDPOINTS[region].format(start=date_from, end=date_to)
    raw_records = fetch_from_1c(url)
    mapped_records = [map_1c_record(r) for r in raw_records]
    predicted_records = predict(mapped_records)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', encoding='utf-8', delete=False) as f:
        json.dump(predicted_records, f, ensure_ascii=False)
        output_path = f.name

    print(output_path)
