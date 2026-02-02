"""
registry.py:
- Lee el modelo activo desde MLflow Model Registry (Production).
- Este proyecto registra checkpoints (.pt) como artifacts.
- Para simplificar operación offline, la app carga el checkpoint local más reciente.
- Igual devolvemos info de registry para mostrar en la UI.
"""

from pathlib import Path
from typing import Dict, Optional

import mlflow
from mlflow.tracking import MlflowClient

REGISTERED_MODEL_NAME = "frcnn_coco_cpu_person_car_airplane"

def get_active_model_info(project_root: Path) -> Dict:
    mlflow_db = (project_root / "mlflow_new.db").resolve()
    tracking_uri = f"sqlite:///{mlflow_db.as_posix()}"

    info = {
        "tracking_db": str(mlflow_db),
        "registered_model": REGISTERED_MODEL_NAME,
        "production_version": None,
    }

    try:
        mlflow.set_tracking_uri(tracking_uri)
        client = MlflowClient()
        versions = client.search_model_versions(f"name='{REGISTERED_MODEL_NAME}'")
        prod = [v for v in versions if getattr(v, "current_stage", "") == "Production"]
        if prod:
            prod_sorted = sorted(prod, key=lambda x: int(x.version), reverse=True)
            info["production_version"] = int(prod_sorted[0].version)
    except Exception as e:
        info["error"] = str(e)

    return info
