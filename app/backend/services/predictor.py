"""
predictor.py:
- Carga el checkpoint local best_*.pt (o el más reciente) desde models/local_checkpoints
- Reconstruye Faster R-CNN y hace inferencia en CPU
- Devuelve detecciones para person/car/airplane
"""

import io
import json
from pathlib import Path
from typing import Dict, List

import torch
from PIL import Image
import time
import io
import torch
from PIL import Image
from torchvision.transforms import functional as F
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.transforms import functional as F

TARGET_CLASSES = ["person", "car", "airplane"]

class Predictor:
    MAX_SIDE = 960 
    def __init__(self, project_root: Path):
        self.project_root = project_root.resolve()
        self.models_dir = (self.project_root / "models" / "local_checkpoints").resolve()
        self.device = torch.device("cpu")
        self.model = None
        self.internal_to_name = None
        self._load_latest()

    def _find_latest_best(self) -> Path:
        cands = sorted(self.models_dir.glob("best_*.pt"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not cands:
            raise FileNotFoundError("No hay best_*.pt en models/local_checkpoints.")
        return cands[0]

    def _build_model(self, num_classes: int):
        m = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None)
        in_features = m.roi_heads.box_predictor.cls_score.in_features
        m.roi_heads.box_predictor = FastRCNNPredictor(in_features, num_classes)
        return m

    def _load_latest(self):
        ckpt_path = self._find_latest_best()
        ckpt = torch.load(ckpt_path, map_location="cpu")

        target_classes = ckpt.get("target_classes", TARGET_CLASSES)
        num_classes = len(target_classes) + 1

        internal_to_name = ckpt.get("internal_to_name", None)
        if internal_to_name is None:
            # fallback: 1..K => target_classes
            internal_to_name = {i + 1: name for i, name in enumerate(target_classes)}

        # normalizar keys si vienen como strings
        fixed = {}
        for k, v in internal_to_name.items():
            fixed[int(k)] = v
        internal_to_name = fixed

        model = self._build_model(num_classes)
        model.load_state_dict(ckpt["model_state_dict"])
        model.to(self.device)
        model.eval()

        self.model = model
        self.internal_to_name = internal_to_name
        self.ckpt_path = ckpt_path

    def reload(self):
        self._load_latest()

    @torch.no_grad()
    def predict_bytes(self, img_bytes: bytes, score_threshold: float = 0.5) -> Dict:
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

        # solo top 3 para tu requisito de 1/2/3 objetos
        dets = sorted(dets, key=lambda d: d["score"], reverse=True)[:3]

        return {
            "ok": True,
            "checkpoint": self.ckpt_path.name,
            "found": len(dets) > 0,
            "message": "no se ha encontrado" if len(dets) == 0 else "ok",
            "detections": dets,
        }
