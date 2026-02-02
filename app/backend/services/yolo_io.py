"""
yolo_io.py:
- Guarda imagen y label YOLO en data/new_data/images y data/new_data/labels
"""

from pathlib import Path
from typing import Dict
import time

def save_new_sample(project_root: Path, image_filename: str, image_bytes: bytes, yolo_label_text: str) -> Dict:
    new_dir = (project_root / "data" / "new_data").resolve()
    img_dir = (new_dir / "images").resolve()
    lbl_dir = (new_dir / "labels").resolve()

    img_dir.mkdir(parents=True, exist_ok=True)
    lbl_dir.mkdir(parents=True, exist_ok=True)

    # nombre único
    stem = Path(image_filename).stem
    ext = Path(image_filename).suffix.lower() or ".jpg"
    ts = time.strftime("%Y%m%d_%H%M%S")
    safe_name = f"{stem}_{ts}{ext}"
    safe_stem = Path(safe_name).stem

    img_path = img_dir / safe_name
    lbl_path = lbl_dir / f"{safe_stem}.txt"

    with open(img_path, "wb") as f:
        f.write(image_bytes)

    # limpiar texto
    yolo_label_text = yolo_label_text.strip() + "\n"
    with open(lbl_path, "w", encoding="utf-8") as f:
        f.write(yolo_label_text)

    return {"image_name": img_path.name, "label_name": lbl_path.name, "image_path": str(img_path), "label_path": str(lbl_path)}
