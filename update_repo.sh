#!/bin/bash
cd /home/dietpi/geopol_dashboard

# Activar venv y recolectar
source venv/bin/activate
python3 scripts/harvester.py

# Sincronizar Código y Datos
git add app.py scripts/harvester.py update_repo.sh data/geopol_data.csv
git commit -m "SITREP Auto-Update: $(date)"
git push origin main
