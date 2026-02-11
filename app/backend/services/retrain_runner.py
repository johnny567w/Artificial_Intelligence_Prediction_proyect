"""
retrain_runner.py (arreglado):
- Encuentra el notebook 05 aunque esté en otra carpeta.
- Ejecuta el notebook con nbconvert.
- Devuelve status ERROR si no lo encuentra.
"""

from pathlib import Path
from typing import Dict
import subprocess

NB_CANDIDATES = [
    "05_continual_retrain_new_data.ipynb",
]

def _find_nb(project_root: Path) -> Path | None:
    # 1) ubicación estándar: IA-final/notebooks/
    nb_dir = (project_root / "notebooks").resolve()
    for name in NB_CANDIDATES:
        p = (nb_dir / name).resolve()
        if p.exists():
            return p

    # 2) buscar en todo el proyecto (una sola vez, es rápido)
    for name in NB_CANDIDATES:
        hits = list(project_root.rglob(name))
        if hits:
            # el más cercano al root
            hits = sorted(hits, key=lambda x: len(str(x)))
            return hits[0].resolve()

    return None

def run_incremental_retrain(project_root: Path, log_path: Path) -> Dict:
    nb_path = _find_nb(project_root)
    if nb_path is None:
        return {
            "status": "ERROR",
            "error": "No existe notebook 05 en el proyecto. Debe llamarse 05_incremental_retrain_new_data.ipynb (o similar).",
        }

    out_nb = (project_root / "notebooks" / "_last_run_05.ipynb").resolve()
    out_nb.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python", "-m", "nbconvert",
        "--to", "notebook",
        "--execute",
        "--ExecutePreprocessor.timeout=86400",
        "--output", str(out_nb),
        str(nb_path),
    ]

    p = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_root))

    if p.returncode != 0:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("\n[RETRAIN NOTEBOOK PATH]\n" + str(nb_path) + "\n")
            f.write("\n[RETRAIN STDERR]\n" + (p.stderr or "") + "\n")
            f.write("\n[RETRAIN STDOUT]\n" + (p.stdout or "") + "\n")
        return {
            "status": "ERROR",
            "error": "Notebook execution failed. Revisa logs.",
            "notebook": str(nb_path),
            "executed_output": str(out_nb),
        }

    return {
        "status": "DONE",
        "notebook": str(nb_path),
        "executed_output": str(out_nb),
    }
