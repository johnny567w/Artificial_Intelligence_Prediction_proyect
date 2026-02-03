"""
predictor.py
- Carga checkpoint local best_*.pt por defecto.
- Puede recargar desde MLflow Model Registry descargando el artifact .pt.
"""

import io
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse, unquote

import torch
from PIL import Image
from torchvision.transforms import functional as F
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor

from mlflow.tracking import MlflowClient

TARGET_CLASSES = ["person", "car", "airplane"]

print("LOADED PREDICTOR FROM:", __file__)

class Predictor:
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.models_dir = (self.project_root / "models" / "local_checkpoints").resolve()
        self.models_dir.mkdir(parents=True, exist_ok=True)

        self.device = torch.device("cpu")
        self.model = None
        self.internal_to_name = None
        self.ckpt_path: Optional[Path] = None

        # info activo
        self.active_source = "local"  # local | mlflow-registry
        self.active_version: Optional[int] = None
        self.active_source = "local"
        self.active_version = None
        self.ckpt_path = None

        self._load_latest_local()

    # -------------------------
    # Build model
    # -------------------------
    def _build_model(self, num_classes: int):
        m = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None)
        in_features = m.roi_heads.box_predictor.cls_score.in_features
        m.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        return m

    # -------------------------
    # Local load
    # -------------------------
    def _find_latest_best(self) -> Path:
        cands = sorted(
            self.models_dir.glob("best_*.pt"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not cands:
            raise FileNotFoundError("No hay best_*.pt en models/local_checkpoints.")
        return cands[0]

    def _load_from_ckpt_path(self, ckpt_path: Path):
        ckpt = torch.load(ckpt_path, map_location="cpu")

        target_classes = ckpt.get("target_classes", TARGET_CLASSES)
        num_classes = len(target_classes) + 1  # + background

        internal_to_name = ckpt.get("internal_to_name")
        if internal_to_name is None:
            internal_to_name = {i + 1: name for i, name in enumerate(target_classes)}

        # normalizar keys string->int
        internal_to_name = {int(k): v for k, v in internal_to_name.items()}

        model = self._build_model(num_classes)
        model.load_state_dict(ckpt["model_state_dict"])
        model.to(self.device)
        model.eval()

        self.model = model
        self.internal_to_name = internal_to_name
        self.ckpt_path = ckpt_path

    def _load_latest_local(self):
        ckpt_path = self._find_latest_best()
        self._load_from_ckpt_path(ckpt_path)
        self.active_source = "local"
        self.active_version = None

    # -------------------------
    # MLflow registry load (download .pt artifact)
    # -------------------------
    def reload_from_registry(self, model_name: str, stage: str = "Production") -> bool:
        client = MlflowClient()
        latest = client.get_latest_versions(model_name, stages=[stage])
        if not latest:
            return False

        mv = latest[0]
        version = int(mv.version)

        # ya cargado
        if self.active_source == "mlflow-registry" and self.active_version == version:
            return True

        src = (mv.source or "").strip()

        # --------------------------
        # Caso A: runs:/<run_id>/path
        # --------------------------
        if src.startswith("runs:/"):
            # runs:/RUNID/checkpoints/file.pt
            rest = src[len("runs:/") :]
            run_id, artifact_rel = rest.split("/", 1)

            dst_name = f"mlflow_v{version}_{Path(artifact_rel).name}"
            dst_dir = self.models_dir.resolve()

            downloaded = client.download_artifacts(run_id, artifact_rel, dst_dir.as_posix())
            downloaded_path = Path(downloaded)

            # download_artifacts puede devolver el directorio; ajustamos al archivo
            if downloaded_path.is_dir():
                downloaded_path = downloaded_path / Path(artifact_rel).name

            self._load_from_ckpt_path(downloaded_path)

            self.active_source = "mlflow-registry"
            self.active_version = version
            self.ckpt_path = downloaded_path
            return True

        # --------------------------
        # Caso B: file:/... o file:c:/...
        # --------------------------
        if src.startswith("file:"):
            parsed = urlparse(src)

            # Si viene file:c:/... => parsed.path puede venir vacío
            path_part = parsed.path if parsed.scheme == "file" and parsed.path else src[len("file:") :]
            file_path = unquote(path_part)

            # En Windows a veces queda /C:/..., quitamos slash inicial
            if len(file_path) >= 3 and file_path[0] == "/" and file_path[2] == ":":
                file_path = file_path[1:]

            ckpt_path = Path(file_path)

            if not ckpt_path.exists():
                raise FileNotFoundError(f"No existe el checkpoint apuntado por MLflow: {ckpt_path}")

            # Copiar a local_checkpoints para tenerlo consistente
            dst_name = f"mlflow_v{version}_{ckpt_path.name}"
            dst_path = (self.models_dir / dst_name).resolve()

            if dst_path != ckpt_path:
                dst_path.write_bytes(ckpt_path.read_bytes())
                ckpt_path = dst_path

            self._load_from_ckpt_path(ckpt_path)

            self.active_source = "mlflow-registry"
            self.active_version = version
            self.ckpt_path = ckpt_path
            return True

        raise RuntimeError(f"ModelVersion.source inesperado: {mv.source}")

    def reload(self):
        """Recarga desde el último best_*.pt local (fallback)."""
        self._load_latest_local()

    def get_active_info(self) -> Dict:
        return {
            "source": self.active_source,
            "mlflow_version": self.active_version,
            "checkpoint": str(self.ckpt_path) if self.ckpt_path else None,
        }
    def get_active_info(self) -> Dict:
        return {
            "source": getattr(self, "active_source", "local"),
            "mlflow_version": getattr(self, "active_version", None),
            "checkpoint": str(self.ckpt_path) if getattr(self, "ckpt_path", None) else None,
        }
    # -------------------------
    # Predict
    # -------------------------
    @torch.no_grad()
    def predict_bytes(self, img_bytes: bytes, score_threshold: float = 0.5) -> Dict:
        if self.model is None:
            raise RuntimeError("El modelo no está cargado. Llama a reload() o reload_from_registry().")

        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        x = F.to_tensor(img).to(self.device)

        out = self.model([x])[0]
        boxes = out["boxes"].cpu().tolist()
        scores = out["scores"].cpu().tolist()
        labels = out["labels"].cpu().tolist()

        dets = []
        for b, s, l in zip(boxes, scores, labels):
            if float(s) < float(score_threshold):
                continue
            name = self.internal_to_name.get(int(l), f"class_{l}")
            dets.append({"xyxy": b, "score": float(s), "label": name})

        dets = sorted(dets, key=lambda d: d["score"], reverse=True)[:3]

        return {
            "ok": True,
            "checkpoint": self.ckpt_path.name if self.ckpt_path else None,
            "found": len(dets) > 0,
            "message": "no se ha encontrado" if not dets else "ok",
            "detections": dets,
        }
