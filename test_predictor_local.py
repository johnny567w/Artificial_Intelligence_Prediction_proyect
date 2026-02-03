import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

# Ruta exacta a predictor.py
PREDICTOR_DIR = PROJECT_ROOT / "app" / "backen" / "services"

# Asegura que existe
if not (PREDICTOR_DIR / "predictor.py").exists():
    raise FileNotFoundError(f"No existe predictor.py en: {PREDICTOR_DIR}")

# 1) Para que encuentre app/...
sys.path.insert(0, str(PROJECT_ROOT))
# 2) Para importar predictor.py directamente desde su carpeta
sys.path.insert(0, str(PREDICTOR_DIR))

from predictor import Predictor  # predictor.py de app/backen/services

pred = Predictor(PROJECT_ROOT)

# 🔹 FORZAR LOCAL
pred.reload()

print("=== LOCAL ===")
print(pred.get_active_info())
