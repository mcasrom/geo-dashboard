#!/bin/bash
cd /home/dietpi/geopol_dashboard

# Activar entorno virtual
source venv/bin/activate

# Ejecutar el scrapper y NLP
python3 etl_geopol.py

# Subir a GitHub
git add data/geopol_data.csv
git commit -m "Auto-update geopolitical data: $(date)"
git push origin main
