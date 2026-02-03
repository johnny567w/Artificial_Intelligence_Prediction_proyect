"""
main.py (FastAPI) - completo y corregido para tu Predictor

Tu Predictor tiene firma:
Predictor(project_root: Path)

Incluye:
- /health
- /predict (1 imagen)
- /predict-multi (múltiples imágenes)
- /new-data (guardar imagen + label YOLO)
- /retrain (ejecuta notebook 05 por nbconvert)
- /reload-model (recarga último checkpoint local)
- /logs (texto plano)
- /retrain-progress (texto plano)

Notas:
- PROJECT_ROOT se calcula desde app/backend/main.py subiendo 2 niveles a IA-final.
- ts es anti-cache (se ignora en backend).
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from matplotlib.units import registry

from services.predictor import Predictor
from services.retrain_runner import run_incremental_retrain

import mlflow
from mlflow.tracking import MlflowClient

# --------------------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------------------

# main.py está en: IA-final/app/backend/main.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # -> IA-final
CURRENT_PROD_VERSION = None

MLFLOW_DB = (PROJECT_ROOT / "mlflow_new.db").resolve()
MLFLOW_URI = f"sqlite:///{MLFLOW_DB.as_posix()}"
mlflow.set_tracking_uri(MLFLOW_URI)

DATA_DIR = PROJECT_ROOT / "data"
NEW_DATA_DIR = DATA_DIR / "new_data"
NEW_IMG_DIR = NEW_DATA_DIR / "images"
NEW_LBL_DIR = NEW_DATA_DIR / "labels"

MODELS_DIR = PROJECT_ROOT / "models"
LOCAL_CKPTS_DIR = MODELS_DIR / "local_checkpoints"

LOGS_DIR = PROJECT_ROOT / "logs"
APP_LOG = LOGS_DIR / "app.log"
RETRAIN_LOG = LOGS_DIR / "retrain_progress.log"

for p in [NEW_IMG_DIR, NEW_LBL_DIR, LOCAL_CKPTS_DIR, LOGS_DIR]:
    p.mkdir(parents=True, exist_ok=True)


def write_app_log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(APP_LOG, "a", encoding="utf-8", errors="ignore") as f:
        f.write(f"[{ts}] {msg}\n")


# --------------------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------------------

app = FastAPI(title="IA-FINAL Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en prod limita a tu dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------------------
# Predictor (TU FIRMA)
# --------------------------------------------------------------------------------------

# Tu Predictor requiere project_root
predictor = Predictor(project_root=PROJECT_ROOT)

# --------------------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------------------

@app.get("/")
def root():
    return {"ok": True, "message": "IA-FINAL backend running"}


REGISTERED_MODEL_NAME = "frcnn_coco_cpu_person_car_airplane"


def _get_registry_info():
    """
    Devuelve info del registry: latest production version si existe.
    """
    try:
        client = MlflowClient(tracking_uri=MLFLOW_URI)
        versions = client.search_model_versions(
            f"name='{REGISTERED_MODEL_NAME}'"
        )

        prod = [
            v for v in versions
            if getattr(v, "current_stage", "") == "Production"
        ]
        prod_sorted = sorted(
            prod, key=lambda x: int(x.version), reverse=True
        ) if prod else []

        if prod_sorted:
            mv = prod_sorted[0]
            return {
                "tracking_db": str(MLFLOW_DB),
                "registered_model": REGISTERED_MODEL_NAME,
                "production_version": int(mv.version),
                "production_run_id": mv.run_id,
                "production_stage": mv.current_stage,
            }

        all_sorted = sorted(
            versions, key=lambda x: int(x.version), reverse=True
        ) if versions else []

        if all_sorted:
            mv = all_sorted[0]
            return {
                "tracking_db": str(MLFLOW_DB),
                "registered_model": REGISTERED_MODEL_NAME,
                "production_version": None,
                "latest_version": int(mv.version),
                "latest_run_id": mv.run_id,
                "latest_stage": mv.current_stage,
            }

        return {
            "tracking_db": str(MLFLOW_DB),
            "registered_model": REGISTERED_MODEL_NAME,
            "production_version": None,
            "note": "No hay versiones registradas en Model Registry.",
        }

    except Exception as e:
        return {
            "tracking_db": str(MLFLOW_DB),
            "registered_model": REGISTERED_MODEL_NAME,
            "production_version": None,
            "error": str(e),
        }


CURRENT_PROD_VERSION = None

@app.get("/health")
def health():
    global CURRENT_PROD_VERSION

    registry = _get_registry_info()
    prod_version = registry.get("production_version")

    # 🔥 intentar recargar desde MLflow Registry siempre que haya Production
    if prod_version is not None and prod_version != CURRENT_PROD_VERSION:
        try:
            loaded = predictor.reload_from_registry(REGISTERED_MODEL_NAME, stage="Production")
            if loaded:
                write_app_log(f"Auto-reload OK -> Production v{prod_version}")
                CURRENT_PROD_VERSION = prod_version
        except Exception as e:
            write_app_log(f"Auto-reload from registry failed: {e}")

    # info del predictor
    active = {}
    if hasattr(predictor, "get_active_info") and callable(getattr(predictor, "get_active_info")):
        try:
            active = predictor.get_active_info()
        except Exception as e:
            active = {"error": str(e)}

    return {
        "ok": True,
        "active_model": active,
        **registry,
        "project_root": str(PROJECT_ROOT),
        "models_dir": str(LOCAL_CKPTS_DIR),
    }



@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    score_threshold: float = Form(0.5),
):
    """
    Predice objetos en 1 imagen.
    """
    t0 = time.perf_counter()
    content = await image.read()

    write_app_log(f"/predict file={image.filename}")

    result = predictor.predict_bytes(
        content, score_threshold=score_threshold
    )
    result["filename"] = image.filename
    result["request_ms"] = (time.perf_counter() - t0) * 1000.0

    return result


@app.post("/predict-multi")
async def predict_multi(
    images: List[UploadFile] = File(...),
    score_threshold: float = Form(0.5),
):
    """
    Predice objetos en múltiples imágenes.
    """
    write_app_log(f"/predict-multi n={len(images)}")

    results = []
    for img in images:
        content = await img.read()
        r = predictor.predict_bytes(
            content, score_threshold=score_threshold
        )
        r["filename"] = img.filename
        results.append(r)

    return {"ok": True, "results": results}


@app.post("/new-data")
async def new_data(
    image: UploadFile = File(...),
    yolo_label_text: str = Form(...),
):
    """
    Guarda imagen + label YOLO para reentrenamiento incremental.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = (image.filename or "image").replace(" ", "_")
    base_name = f"imagen_{ts}_{safe_name}"

    img_path = NEW_IMG_DIR / base_name
    lbl_path = NEW_LBL_DIR / (Path(base_name).stem + ".txt")

    content = await image.read()
    with open(img_path, "wb") as f:
        f.write(content)

    with open(lbl_path, "w", encoding="utf-8") as f:
        f.write((yolo_label_text or "").strip() + "\n")

    write_app_log(
        f"/new-data saved image={img_path.name} label={lbl_path.name}"
    )

    return {
        "ok": True,
        "saved_image": str(img_path),
        "saved_label": str(lbl_path),
    }


@app.post("/retrain")
def retrain():
    """
    Ejecuta el notebook 05 por nbconvert.
    El notebook debe escribir progreso en logs/retrain_progress.log
    """
    write_app_log("/retrain requested")

    with open(RETRAIN_LOG, "w", encoding="utf-8", errors="ignore") as f:
        f.write(
            f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] === RETRAIN START ===\n"
        )

    res = run_incremental_retrain(PROJECT_ROOT, APP_LOG)
    status = res.get("status", "ERROR")

    write_app_log(f"/retrain done status={status}")

    return {"ok": True, **res}


@app.post("/reload-model")
def reload_model():
    """
    Recarga el modelo desde el último checkpoint local.
    """
    write_app_log("/reload-model triggered")

    if hasattr(predictor, "reload") and callable(
        getattr(predictor, "reload")
    ):
        predictor.reload(REGISTERED_MODEL_NAME)

    else:
        if hasattr(predictor, "_load_latest") and callable(
            getattr(predictor, "_load_latest")
        ):
            predictor._load_latest()

    return {"ok": True}


@app.get("/logs", response_class=PlainTextResponse)
def get_logs(lines: int = 200, ts: Optional[int] = None):
    """
    Logs generales del backend (texto plano).
    ts se ignora (anti-cache).
    """
    if not APP_LOG.exists():
        return ""

    with open(APP_LOG, "r", encoding="utf-8", errors="ignore") as f:
        content = f.readlines()

    return "".join(content[-lines:])


@app.get("/retrain-progress", response_class=PlainTextResponse)
def get_retrain_progress(lines: int = 200, ts: Optional[int] = None):
    """
    Logs del progreso del notebook 05 (texto plano).
    ts se ignora (anti-cache).
    """
    if not RETRAIN_LOG.exists():
        return ""

    with open(RETRAIN_LOG, "r", encoding="utf-8", errors="ignore") as f:
        content = f.readlines()

    return "".join(content[-lines:])
