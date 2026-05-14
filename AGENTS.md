# FinML Agent Instructions

## Project Overview

ML service for predicting PL and CFO codes from payment text data. Target "Код" split into:
- **PL**: last 2 characters of code
- **CFO**: all characters except last 2

## Project Structure

```
/mnt/d/FinML/           # Root project (Windows path: D:\FinML\)
├── service/             # Next.js frontend service
│   ├── app/            # Pages and API routes
│   │   ├── api/
│   │   │   ├── fetch-from-1c/   # POST: fetch data from 1C endpoint
│   │   │   ├── upload/          # POST: upload Excel + predict
│   │   │   └── save/            # POST: save edited data to JSON/CSV
│   ├── components/      # UI components
│   ├── lib/             # Utilities
│   └── uploads/         # Uploaded files
├── fetch_and_predict.py # Python script: fetch from 1C + ML predict
├── predict_excel_api.py # Python script: Excel + ML predict (legacy)
├── model_final.pkl      # Best model bundle (MLP for PL + XGBoost for CFO)
├── embeddings.npy       # Pre-computed BERT embeddings (384 features)
├── data.pkl             # Training data from SQL
├── train_final.py       # Final model training script
├── requirements.txt     # Python dependencies
└── AGENTS.md           # This file
```

## Developer Commands

### Start Next.js Service (Windows)

```bash
cd D:\FinML\service
npm run dev
```

Then open http://localhost:3000

### Start Next.js Service (WSL)

```bash
cd /mnt/d/FinML/service
(npm run dev &)
```

Note: Use subshell `(npm run dev &)` for background process - without it the process dies.

### Train Models

```bash
cd D:\FinML
D:\FinML\.venv\Scripts\activate
python train_final.py
```

### Run Prediction Script Directly

```bash
cd D:\FinML
D:\FinML\.venv\Scripts\activate
python predict_excel_api.py "path/to/file.xlsx"
```

### Install Dependencies

```bash
# Python (Windows)
D:\FinML\.venv\Scripts\activate
pip install -r requirements.txt

# Install PyTorch with CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

```bash
# Node.js (service)
cd D:\FinML\service
npm install
```

## Architecture Notes

1. **ML Model**: Python-based, loaded from `model_final.pkl`
2. **Frontend**: Next.js 16 with Turbopack
3. **Prediction Flow**: 
   - 1C via API → Next.js API → Python script → ML model → JSON response
   - Excel (alternative) → Next.js API → Python script → ML model → JSON response
4. **Embedding Model**: paraphrase-multilingual-MiniLM-L12-v2 (384 dims)
5. **Best Models**: MLP (PL with date features) + XGBoost (CFO)
6. **Model Performance**: PL accuracy ~91.5%, CFO accuracy ~61%

## Data Source

- SQL Server: `10.10.6.15`, Database: `FinDWH`, Table: `[FinDWH].[dbo].[AccessRU]`
- Excel file fields: "Информация", "Код УФ" (if present)

## Key Files

| File | Purpose |
|------|---------|
| `model_final.pkl` | Serialized model bundle with MLP + XGBoost |
| `fetch_and_predict.py` | Python script: fetch from 1C + ML predict |
| `predict_excel_api.py` | Python script called by Next.js API (Excel fallback) |
| `train_final.py` | Script for training final models |
| `embeddings.npy` | Pre-computed BERT embeddings |

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/fetch-from-1c` | POST | Fetch data from 1C endpoint, return predictions |
| `/api/upload` | POST | Upload Excel, return predictions |
| `/api/save` | POST | Save corrected data to JSON/CSV |

## Frontend Features

- **Region filter**: Dropdown with 7 options (BR, BY, RU, KZ, UZ, CN, TR). Default: RU
- **Date range filter**: Start date and end date inputs
- **Data loading**: From 1C API (main) or Excel file (alternative)
- **ML prediction**: Auto-predicts PL/CFO when "Код УФ" is empty

## 1C Endpoint Configuration

Defined in `fetch_and_predict.py`:
- Only RU configured: `http://10.10.6.64/buh_rf/hs/Exchange/CashTransactions?DateN={start}&DateK={end}`
- Auth: `Обмен1С` / `4AfS2%p-#L^%T$S`
- Field mapping: Документ→op_type, ДатаДок→date, Информация→info, КодУФ→code_uf, etc.

## Git Repository

Remote: https://github.com/samogonoff/finml.git

### Large Files (.gitignore)

The following files are excluded from git (too large for GitHub) and downloaded from Releases:
- `embeddings.npy` (102MB) - BERT embeddings
- `model_final.pkl` (22MB) - ML model bundle

Download command:
```bash
bash download_models.sh
```

### Setup on New Machine (Linux/WSL)

```bash
git clone https://github.com/samogonoff/finml.git
cd finml

# 1. Install Python dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Install Node.js dependencies
cd service
npm install
cd ..

# 3. Download large files separately
bash download_models.sh

# 4. Start the service
cd service
npm run dev
# Open http://localhost:3000
```

### Setup on New Machine (Windows)

```cmd
git clone https://github.com/samogonoff/finml.git
cd finml

:: 1. Install Python dependencies
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

:: 2. Install Node.js dependencies
cd service
npm install
cd ..

:: 3. Download large files separately
bash download_models.sh

:: 4. Start the service
cd service
npm run dev
:: Open http://localhost:3000
```

## WSL/Windows Development Notes

### CRITICAL: How to Start the App from WSL (The Only Way That Works)

The app MUST run from WSL because:
- Python packages (pandas, torch, sentence-transformers) are installed in WSL's system Python
- Windows venv (`D:\FinML\.venv\Scripts\python.exe`) does NOT work from WSL
- Next.js must use WSL Python to call `predict_excel_api.py`

**Correct startup procedure:**

```bash
# 1. Ensure Python dependencies are installed (one-time setup)
pip3 install --break-system-packages -r /mnt/d/FinML/requirements.txt

# 2. Install Node dependencies (one-time setup, or after package.json changes)
cd /mnt/d/FinML/service && npm install && cd /mnt/d/FinML

# 3. Start the Next.js server in background
nohup npx next dev -H 172.31.20.1 -p 3000 > /tmp/next.log 2>&1 &

# 4. Wait for server to be ready
sleep 10

# 5. Verify it's running
curl -s -o /dev/null -w "%{http_code}" http://172.31.20.1:3000
# Should return: 200
```

**Open in browser:** `http://172.31.20.1:3000` (NOT localhost)

**Key fixes applied to the codebase:**
- `service/app/api/upload/route.ts`: Uses `process.platform === 'win32' ? "D:\\FinML\\.venv\\Scripts\\python.exe" : "python3"` to select correct Python

**To stop the server:**
```bash
pkill -f "next dev"
```

### Old Notes (for reference)
- Node.js runs as Windows process (not WSL native)
- CUDA auto-detection: script checks `torch.cuda.is_available()`
