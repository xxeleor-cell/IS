#!/bin/bash
# Нарезка своих фотографий для сайта (macOS, встроенная утилита sips).
#
#   tools/optimize_images.sh ~/Photos/dom-ivanovo.jpg projects/dom-ivanovo
#
# Создаст src/assets/img/projects/dom-ivanovo-640.jpg, -1280.jpg, -1920.jpg.
# В content/*.json укажите  "src": "projects/dom-ivanovo".
# Фото лучше готовить в соотношении 3:2 — на сайте они обрезаются по центру
# (точку фокуса можно задать полем "position", например "50% 30%").
# На Linux/Windows используйте любой аналог (ImageMagick, Squoosh) с теми же именами файлов.
set -euo pipefail
[ $# -eq 2 ] || { echo "Использование: $0 <исходное фото> <папка/имя>"; exit 1; }
SRC="$1"; NAME="$2"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$ROOT/src/assets/img/$NAME"
mkdir -p "$(dirname "$OUT")"
for W in 640 1280 1920; do
  sips -s format jpeg -s formatOptions 72 --resampleWidth "$W" "$SRC" --out "$OUT-$W.jpg" >/dev/null
  echo "  $NAME-$W.jpg"
done
