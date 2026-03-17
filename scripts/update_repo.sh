#!/bin/bash
PROJECT_DIR="/home/dietpi/geopol_dashboard"
cd $PROJECT_DIR

source venv/bin/activate
python3 scripts/etl_geopol.py >> $PROJECT_DIR/data/etl_log.txt 2>&1
deactivate

git add .
git commit -m "Actualizacion Automatica de Inteligencia: $(date +'%Y-%m-%d %H:%M')"
git push origin main
