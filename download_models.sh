#!/bin/bash
# Скачивание ML моделей из последнего GitHub Release
# Запуск: bash download_models.sh

set -e

REPO="samogonoff/finml"
DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Скачивание моделей из последнего релиза $REPO..."

ASSETS=$(curl -sf "https://api.github.com/repos/$REPO/releases/latest" \
  | python3 -c "import sys,json; [print(a['browser_download_url']) for a in json.load(sys.stdin).get('assets',[])]" 2>/dev/null)

if [ -z "$ASSETS" ]; then
  echo "Ошибка: не удалось получить список файлов релиза"
  exit 1
fi

for url in $ASSETS; do
  filename=$(basename "$url")
  echo "  → $filename"
  curl -sL -o "$DIR/$filename" "$url"
done

echo ""
echo "Готово. Скачаны файлы:"
ls -lh "$DIR"/*.{pkl,npy} 2>/dev/null || echo "(файлы не найдены в текущей директории)"
