#!/usr/bin/env bash
# Script peluncur CMS PT Arunika Loise Persada (ALP)

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Periksa Virtual Environment
if [ ! -d "venv" ]; then
    echo "[!] Virtualenv belum ditemukan. Membuat virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
fi

echo "=================================================="
echo "  PT ARUNIKA LOISE PERSADA - FLASK CMS"
echo "  URL Publik    : http://127.0.0.1:5001"
echo "  URL Admin CMS : http://127.0.0.1:5001/admin/login"
echo "  Akun Default  : admin / admin123"
echo "=================================================="

./venv/bin/python3 app.py
