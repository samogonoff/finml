# FinML Classifier Service

ML сервис для предсказания кодов PL и CFO по текстовым данным платежей.

## Возможности

- Загрузка данных из 1С по API с фильтрами региона и дат
- Загрузка данных из Excel файла (альтернатива)
- Автоматическое предсказание кодов PL и CFO для записей без кода
- Извлечение кодов из поля "Код УФ" (если заполнено)
- Ручная корректировка предсказанных кодов в таблице
- Сохранение проверенных данных в JSON и CSV форматы

## Структура проекта

```
finml/
├── service/
│   ├── app/
│   │   ├── api/
│   │   │   ├── fetch-from-1c/   # API: получение данных из 1С
│   │   │   ├── upload/          # API: загрузка Excel
│   │   │   └── save/            # API: сохранение данных
│   │   ├── page.tsx             # Главная страница
│   │   ├── layout.tsx           # Layout приложения
│   │   └── globals.css          # Стили
│   ├── components/
│   │   ├── header.tsx           # Шапка с фильтрами и кнопками
│   │   ├── data-table.tsx       # Таблица с данными
│   │   └── stats-panel.tsx      # Панель статистики
│   └── ui/                     # Shadcn UI компоненты
├── fetch_and_predict.py          # Python: 1С → ML предсказание
├── predict_excel_api.py          # Python: Excel → ML предсказание
├── model_final.pkl               # ML модель (MLP + XGBoost)
├── embeddings.npy                # BERT эмбеддинги
└── requirements.txt              # Python зависимости
```

## Запуск (WSL/Linux)

```bash
# 1. Клонировать репозиторий
git clone https://github.com/samogonoff/finml.git
cd finml

# 2. Установить Python зависимости
pip3 install --break-system-packages -r requirements.txt

# 3. Установить Node.js зависимости
cd service && npm install && cd ..

# 4. Скачать model_final.pkl в корень проекта
# (файл слишком большой для GitHub, скачайте отдельно)

# 5. Запустить dev сервер
nohup npx next dev -H 172.31.20.1 -p 3000 > /tmp/next.log 2>&1 &

# 6. Открыть http://172.31.20.1:3000
```

## Фронтенд

- **Фильтр региона**: BR, BY, RU, KZ, UZ, CN, TR (default RU)
- **Фильтр дат**: DateFrom / DateTo
- **Загрузка из 1С**: кнопка "Загрузить данные"
- **Загрузка из Excel**: кнопка "Excel"
- **Сохранение**: кнопка "Записать данные"

## API

### POST /api/fetch-from-1c
Получение данных из 1С endpoint + ML предсказание.
```json
{ "region": "RU", "dateFrom": "20260501", "dateTo": "20260531" }
```

### POST /api/upload
Загрузка Excel файла + ML предсказание (FormData с полем "file").

### POST /api/save
Сохранение проверенных данных в JSON и CSV файлы.

## Модели

Сервис использует предобученные модели из `model_final.pkl`:
- **PL**: MLPClassifier (embeddings + date features)
- **CFO**: XGBClassifier (embeddings + predicted PL)

Точность: PL ~91.5%, CFO ~61%
