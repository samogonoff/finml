# FinML Classifier Service

ML сервис для предсказания кодов PL и CFO по текстовым данным платежей.

## Возможности

- Загрузка данных из Excel файла (кнопка "Загрузить данные")
- Автоматическое предсказание кодов PL и CFO для записей без кода
- Извлечение кодов из поля "Код УФ" (если заполнено)
- Ручная корректировка предсказанных кодов в таблице
- Сохранение проверенных данных в JSON и CSV форматы

## Структура проекта

```
service/
├── app/
│   ├── api/
│   │   ├── upload/route.ts   # API для загрузки и обработки Excel
│   │   └── save/route.ts     # API для сохранения данных
│   ├── page.tsx               # Главная страница
│   ├── layout.tsx             # Layout приложения
│   └── globals.css            # Стили
├── components/
│   ├── header.tsx             # Шапка с кнопками
│   ├── data-table.tsx         # Таблица с данными
│   └── stats-panel.tsx        # Панель статистики
└── lib/
    └── predictor.ts           # Вызов Python скрипта для предсказаний

predict_excel_api.py           # Python скрипт для ML предсказаний (в корне)
```

## Запуск

1. Установите зависимости:
```bash
cd service
npm install
```

2. Запустите dev сервер:
```bash
npm run dev
```

3. Откройте http://localhost:3000

## Зависимости от Python

Для работы ML моделей необходим Python 3 с зависимостями:
```bash
pip install pandas numpy scikit-learn xgbrains sentence-transformers
```

## API

### POST /api/upload
Загружает Excel файл и возвращает обработанные данные с предсказаниями.

### POST /api/save
Сохраняет проверенные данные в JSON и CSV файлы в папку `exports/`.

## Модели

Сервис использует предобученные модели из `model_final.pkl`:
- MLP для предсказания PL
- XGBoost для предсказания CFO
