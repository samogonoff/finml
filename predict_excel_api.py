"""
API для предсказания кодов PL и CFO из Excel файла
Вызывается из Next.js сервиса
"""

import os
import sys
import json
import warnings

warnings.filterwarnings("ignore")
import pandas as pd
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

KEY_MAP = {
    "Номер": "num",
    "Вид_операции": "op_type",
    "Тип_документа": "doc_type",
    "Реквизиты": "details",
    "Дата": "date",
    "Валюта": "currency",
    "Сумма_документа": "amount_doc",
    "Сумма_вал": "amount_cur",
    "Сумма_руб": "amount_rub",
    "Информация": "info",
    "Получатель": "recipient",
    "Код_УФ": "code_uf",
    "Подразделение": "department",
    "Дебет": "debit",
    "Дебет2": "debit2",
    "Кредит": "credit",
    "Кредит2": "credit2",
    "PL": "pl",
    "CFO": "cfo",
    "PL_source": "pl_source",
    "CFO_source": "cfo_source",
    "isModified": "is_modified",
}

KEY_MAP_REVERSE = {v: k for k, v in KEY_MAP.items()}


def load_model():
    model_path = os.path.join(SCRIPT_DIR, "model_final.pkl")
    with open(model_path, "rb") as f:
        model_bundle = pickle.load(f)
    return model_bundle


def predict_codes(filepath):
    model_bundle = load_model()
    model_pl = model_bundle["model_pl"]
    model_cfo = model_bundle["model_cfo"]
    le_pl = model_bundle["le_pl"]
    le_cfo = model_bundle["le_cfo"]
    scaler_pl = model_bundle["scaler_pl"]

    df_raw = pd.read_excel(filepath, header=None)

    df = pd.DataFrame()
    df["num"] = df_raw.iloc[6:, 0]
    df["op_type"] = df_raw.iloc[6:, 2]
    df["doc_type"] = df_raw.iloc[6:, 4]
    df["details"] = df_raw.iloc[6:, 6]
    df["date"] = df_raw.iloc[6:, 8]
    df["currency"] = df_raw.iloc[6:, 9]
    df["amount_doc"] = df_raw.iloc[6:, 10]
    df["amount_cur"] = df_raw.iloc[6:, 11]
    df["amount_rub"] = df_raw.iloc[6:, 12]
    df["info"] = df_raw.iloc[6:, 13]
    df["code_uf"] = df_raw.iloc[6:, 14]
    df["department"] = df_raw.iloc[6:, 15]
    df["debit"] = df_raw.iloc[6:, 16]
    df["debit2"] = df_raw.iloc[6:, 17]
    df["credit"] = df_raw.iloc[6:, 18]
    df["credit2"] = df_raw.iloc[6:, 19]

    df = df.reset_index(drop=True)

    df["recipient"] = df["info"].astype(str).str.split("/").str[0].str.strip()
    df["text"] = df["info"].fillna("").astype(str) + " " + df["recipient"].fillna("")

    df["date_parsed"] = pd.to_datetime(df["date"], format="%d.%m.%Y", errors="coerce")
    df["year"] = df["date_parsed"].dt.year.fillna(0).astype(int)
    df["month"] = df["date_parsed"].dt.month.fillna(0).astype(int)
    df["day"] = df["date_parsed"].dt.day.fillna(0).astype(int)
    df["weekday"] = df["date_parsed"].dt.dayofweek.fillna(0).astype(int)
    df["date_display"] = df["date_parsed"].dt.strftime("%d.%m.%Y")

    df["pl_from_code"] = df["code_uf"].apply(
        lambda x: (
            str(int(x))[-2:]
            if pd.notna(x) and str(x).replace(".", "", 1).replace("-", "", 1).isdigit()
            else None
        )
    )
    df["cfo_from_code"] = df["code_uf"].apply(
        lambda x: (
            str(int(x))[:-2]
            if pd.notna(x)
            and str(x).replace(".", "", 1).replace("-", "", 1).isdigit()
            and len(str(int(x))) > 2
            else None
        )
    )

    mask_no_code = df["pl_from_code"].isna()
    rows_to_predict = df[mask_no_code].copy()

    if len(rows_to_predict) > 0:
        device = "cuda" if __import__("torch").cuda.is_available() else "cpu"
        encoder = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2", device=device
        )
        texts = rows_to_predict["text"].tolist()

        embeddings = encoder.encode(
            texts, show_progress_bar=False, convert_to_numpy=True
        )

        date_features = rows_to_predict[
            ["year", "month", "day", "weekday"]
        ].values.astype(float)
        X_pl = np.hstack([embeddings, date_features])
        X_pl_scaled = scaler_pl.transform(X_pl)

        y_pred_pl = le_pl.inverse_transform(model_pl.predict(X_pl_scaled))

        pl_encoded = le_pl.transform(y_pred_pl)
        X_cfo = np.column_stack([embeddings, pl_encoded])
        y_pred_cfo = le_cfo.inverse_transform(model_cfo.predict(X_cfo))

        df.loc[mask_no_code, "pl_predicted"] = y_pred_pl
        df.loc[mask_no_code, "cfo_predicted"] = y_pred_cfo

    df["pl"] = df["pl_from_code"].fillna(df.get("pl_predicted", "")).astype(str)
    df["cfo"] = df["cfo_from_code"].fillna(df.get("cfo_predicted", "")).astype(str)
    df["pl_source"] = df["pl_from_code"].apply(
        lambda x: "code" if pd.notna(x) else "predicted"
    )
    df["cfo_source"] = df["cfo_from_code"].apply(
        lambda x: "code" if pd.notna(x) else "predicted"
    )

    df["pl"] = df["pl"].replace(".0", "", regex=False)
    df["cfo"] = df["cfo"].replace(".0", "", regex=False)

    records = []
    for _, row in df.iterrows():

        def safe_str(val):
            if pd.isna(val):
                return ""
            return str(val)

        records.append(
            {
                "num": safe_str(row.get("num")),
                "op_type": safe_str(row.get("op_type")),
                "doc_type": safe_str(row.get("doc_type")),
                "details": safe_str(row.get("details")),
                "date": safe_str(row.get("date_display")),
                "currency": safe_str(row.get("currency")),
                "amount_doc": safe_str(row.get("amount_doc")),
                "amount_cur": safe_str(row.get("amount_cur")),
                "amount_rub": safe_str(row.get("amount_rub")),
                "info": safe_str(row.get("info")),
                "recipient": safe_str(row.get("recipient")),
                "code_uf": safe_str(row.get("code_uf")),
                "department": safe_str(row.get("department")),
                "debit": safe_str(row.get("debit")),
                "debit2": safe_str(row.get("debit2")),
                "credit": safe_str(row.get("credit")),
                "credit2": safe_str(row.get("credit2")),
                "pl": str(row.get("pl", "")),
                "cfo": str(row.get("cfo", "")),
                "pl_source": row.get("pl_source", "predicted"),
                "cfo_source": row.get("cfo_source", "predicted"),
                "is_modified": False,
            }
        )

    return records


if __name__ == "__main__":
    import tempfile
    import os

    if len(sys.argv) < 2:
        print("Usage: python predict_excel_api.py <filepath>")
        sys.exit(1)

    filepath = sys.argv[1]
    records = predict_codes(filepath)

    # Save to temp file with UTF-8
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", encoding="utf-8", delete=False
    ) as f:
        json.dump(records, f, ensure_ascii=False)
        output_path = f.name

    print(output_path)
