# FinML Agent Instructions

## Project Overview

ML service for predicting PL and CFO codes from payment text data. Target "Код" split into:
- **PL**: last 2 characters of code
- **CFO**: all characters except last 2

## Project Structure

```
D:\FinML\                    # Root project
├── finml\                   # Python ML files
│   ├── model_final.pkl      # Best model bundle (MLP for PL + XGBoost for CFO)
│   ├── embeddings.npy       # Pre-computed BERT embeddings (384 features)
│   ├── predict_excel_api.py # Python API script for predictions
│   ├── train_final.py       # Final model training script
│   └── requirements.txt     # Python dependencies
└── service\                 # Next.js frontend
    ├── app\                # Pages and API routes
    ├── components\         # UI components
    └── uploads\            # Uploaded files
```

## Quick Start

1. **Установить Node.js v20**: https://nodejs.org/v20.20.2

2. **Установить Python зависимости**:
```cmd
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install xgboost scikit-learn sentence-transformers pandas openpyxl
```

3. **Запустить сервер**:
```cmd
cmd /c "cd /d D:\FinML\finml\service && npm run dev"
```

4. **Открыть в браузере**: http://localhost:3000

5. **Загрузить Excel файл** через кнопку "Загрузить данные"

## Developer Commands

### Start Next.js Service (Windows) - РЕКОМЕНДУЕТСЯ

Запускать через cmd.exe:

```cmd
cd /d D:\FinML\finml\service
npm run dev
```

Или одной строкой:
```cmd
cmd /c "cd /d D:\FinML\finml\service && npm run dev"
```

Then open http://localhost:3000

### Alternative: Start via PowerShell

```powershell
cd D:\FinML\finml\service
npm run dev
```

### Run Prediction Script Directly

```cmd
cd /d D:\FinML\finml
C:\Users\Андрей\AppData\Local\Programs\Python\Python314\python.exe predict_excel_api.py "path/to/file.xlsx"
```

### Install Dependencies

```cmd
# Python (global Python, not venv)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install xgboost scikit-learn sentence-transformers pandas openpyxl
```

```cmd
# Node.js (service)
cd /d D:\FinML\finml\service
npm install
```

## Architecture Notes

1. **ML Model**: Python-based, loaded from `model_final.pkl`
2. **Frontend**: Next.js 15 (runs on Windows Node.js)
3. **Prediction Flow**: 
   - Excel → Next.js API → Python script → ML model → JSON response
4. **Embedding Model**: paraphrase-multilingual-MiniLM-L12-v2 (384 dims)
5. **Best Models**: MLP (PL with date features) + XGBoost (CFO)
6. **Model Performance**: PL accuracy ~91.5%, CFO accuracy ~61%

## Python Configuration

- **Python**: `C:\Users\Андрей\AppData\Local\Programs\Python\Python314\python.exe`
- **Node.js**: `C:\Program Files\nodejs\node.exe`
- **Model path**: `D:\FinML\finml\model_final.pkl`
- **Embeddings path**: `D:\FinML\finml\embeddings.npy`

Note: Python script uses `SCRIPT_DIR` to locate model files relative to its location.

## Data Source

- SQL Server: `10.10.6.15`, Database: `FinDWH`, Table: `[FinDWH].[dbo].[AccessRU]`
- Excel file fields: "Информация", "Код УФ" (if present)

## Key Files

| File | Purpose |
|------|---------|
| `model_final.pkl` | Serialized model bundle with MLP + XGBoost |
| `predict_excel_api.py` | Python script called by Next.js API |
| `train_final.py` | Script for training final models |
| `embeddings.npy` | Pre-computed BERT embeddings |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/upload` | POST | Upload Excel, return predictions |
| `/api/save` | POST | Save corrected data to JSON/CSV |

## Code Logic for "Код УФ"

- If "Код УФ" is filled: extract PL (last 2 chars) and CFO (all except last 2)
- If "Код УФ" is empty: use ML model to predict PL and CFO

## Git Repository

Remote: https://github.com/samogonoff/finml.git

### Large Files (.gitignore)

The following files are excluded from git (too large for GitHub):
- `embeddings.npy` (102MB) - BERT embeddings
- `*.pkl`, `model_*.pkl` - Python pickle files

### Setup on New Machine

1. Clone repository:
```cmd
git clone https://github.com/samogonoff/finml.git
```

2. Download model files from releases or copy from another machine:
   - `embeddings.npy`
   - `model_final.pkl`

3. Install dependencies and run (see Quick Start above)
