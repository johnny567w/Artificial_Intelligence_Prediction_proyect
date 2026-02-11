

import { Injectable, inject } from '@angular/core';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription, interval } from 'rxjs';
import { switchMap } from 'rxjs/operators';

import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { ApiService } from '../api.service';

@Injectable({ providedIn: 'root' })
export class AppStateService  {


  activeInfo: any = null;
  modelExpanded = false;
  reloadBusy = false;

 
  // ---- Estado: predicción múltiple ----
  predictFiles: File[] = [];
  predictPreviews: { name: string; url: string }[] = [];
  predictResults: any[] = [];
  scoreThreshold = 0.5;
  predictBusy = false;

  // ---- Estado: nuevos datos para reentrenamiento ----
  newFile: File | null = null;
  yoloText = '0 0.5 0.5 0.4 0.4';
  newDataBusy = false;
  newDataResult: any = null;

  // ---- Estado: reentrenamiento ----
  retrainBusy = false;
  retrainResult: any = null;

  // ---- Estado: logs ----
  logs = '';
  showLogs = true;
// ---- Anotador (nuevo data) ----
annotFile: File | null = null;
annotPreviewUrl: string | null = null;

annotCanvasId = "annot_canvas";
annotImgW = 0;
annotImgH = 0;
retrainLogText = '';

selectedClass = "airplane"; // por defecto
classToId: Record<string, number> = { person: 0, car: 1, airplane: 2 };

// cajas: coords en pixeles (sobre la imagen original cargada)
boxes: Array<{ cls: number; x1: number; y1: number; x2: number; y2: number }> = [];

private isDrawing = false;
private startX = 0;
private startY = 0;
private currentRect: { x1: number; y1: number; x2: number; y2: number } | null = null;

  private sub = new Subscription();
constructor(private api: ApiService) {
  this.ngOnInit();
}


ngOnInit(): void {
  // llamadas iniciales
  this.refreshHealth();
  this.refreshLogs();
  this.refreshRetrainProgress();

  // refrescar logs cada 2.5s
  const logSub = interval(2500)
    .pipe(switchMap(() => this.api.logs(200)))
    .subscribe({
      next: (t) => (this.logs = t),
      error: () => {}
    });
  this.sub.add(logSub);

  // refrescar estado de salud cada 10s
  const healthSub = interval(10000).subscribe(() => this.refreshHealth());
  this.sub.add(healthSub);

  // ✅ refrescar progreso de reentrenamiento cada 2.5s (USANDO PARSER)
  const progressSub = interval(2500)
    .pipe(switchMap(() => this.api.retrainProgress(120)))
    .subscribe({
      next: (t) => this.parseProgressFromLog(t),
      error: () => {}
    });
  this.sub.add(progressSub);
}

refreshRetrainProgress(): void {
  this.api.retrainProgress(120).subscribe({
    next: (t) => this.parseProgressFromLog(t),
    error: () => {}
  });
}

  ngOnDestroy(): void {
    // liberar URLs creadas con createObjectURL
    this.predictPreviews.forEach((p) => URL.revokeObjectURL(p.url));
    this.sub.unsubscribe();
  }
 
  // ---------------------------
  // UI helpers
  // ---------------------------
  toggleLogs(): void {
    this.showLogs = !this.showLogs;
  }

  // ---------------------------
  // Modelo activo
  // ---------------------------
  refreshHealth(): void {
    this.api.health().subscribe({
      next: (r) => (this.activeInfo = r),
      error: (e) => (this.activeInfo = { ok: false, error: String(e) }),
    });
  }

  // ---------------------------
  // Logs
  // ---------------------------
  refreshLogs(): void {
    this.api.logs(200).subscribe({
      next: (t) => (this.logs = t),
      error: () => {},
    });
  }

  // ---------------------------
  // Predicción (múltiples imágenes)
  // ---------------------------
  onPickPredictFiles(ev: Event): void {
    const input = ev.target as HTMLInputElement;
    const files = input.files ? Array.from(input.files) : [];
    this.predictFiles = files;

    // reset resultados
    this.predictResults = [];

    // limpiar previews anteriores
    this.predictPreviews.forEach((p) => URL.revokeObjectURL(p.url));
    this.predictPreviews = files.map((f) => ({
      name: f.name,
      url: URL.createObjectURL(f),
    }));

    // dibujar imagen base (sin boxes) en cada canvas
    setTimeout(() => this.drawAllCanvases(), 0);
  }

  onPredict(): void {
    if (!this.predictFiles.length) return;

    this.predictBusy = true;
    this.predictResults = [];

    this.api.predictMulti(this.predictFiles, this.scoreThreshold).subscribe({
      next: (r) => {
        this.predictResults = (r?.results ?? []).map((x: any) => x);
        // dibujar boxes
        setTimeout(() => this.drawAllCanvases(), 0);
      },
      error: (e) => {
        this.predictResults = [{ ok: false, error: String(e) }];
        setTimeout(() => this.drawAllCanvases(), 0);
      },
      complete: () => (this.predictBusy = false),
    });
  }

  private drawAllCanvases(): void {
    for (let i = 0; i < this.predictPreviews.length; i++) {
      this.drawCanvas(i);
    }
  }

  private drawCanvas(i: number): void {
    const preview = this.predictPreviews[i];
    const res = this.predictResults[i];

    const canvas = document.getElementById(`cv_${i}`) as HTMLCanvasElement | null;
    if (!canvas) return;

    const img = new Image();
    img.onload = () => {
      // Ajustar canvas al tamaño real de la imagen mostrada
      canvas.width = img.width;
      canvas.height = img.height;

      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // Dibuja imagen
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0);

      // Si no hay detecciones, no dibujamos boxes
      if (!res?.ok || !res?.detections?.length) return;

      // Si el backend redimensiona para inferencia, ajustamos boxes al tamaño del preview
      const infW = res.image_w ?? img.width;
      const infH = res.image_h ?? img.height;
      const sx = img.width / infW;
      const sy = img.height / infH;

      // Estilo de boxes/texto
      ctx.lineWidth = 3;
      ctx.font = '16px sans-serif';

      for (const d of res.detections) {
        const [x1, y1, x2, y2] = d.xyxy as [number, number, number, number];

        // reescalar coords de inferencia a coords del preview
        const rx1 = x1 * sx;
        const ry1 = y1 * sy;
        const rx2 = x2 * sx;
        const ry2 = y2 * sy;

        // box
        ctx.strokeStyle = '#22c55e';
        ctx.fillStyle = 'rgba(34,197,94,0.2)';
        ctx.strokeRect(rx1, ry1, rx2 - rx1, ry2 - ry1);
        ctx.fillRect(rx1, ry1, rx2 - rx1, ry2 - ry1);

        // label + %
        const label = `${d.label} ${(d.score * 100).toFixed(1)}%`;

        const tx = rx1;
        const ty = Math.max(18, ry1 - 6);

        ctx.fillStyle = 'rgba(0,0,0,0.75)';
        ctx.fillRect(tx, ty - 18, ctx.measureText(label).width + 10, 20);

        ctx.fillStyle = '#ffffff';
        ctx.fillText(label, tx + 5, ty - 3);
      }
    };

    img.src = preview.url;
  }

  // ---------------------------
  // Nuevos datos (guardar imagen + label YOLO)
  // ---------------------------
  onPickNewFile(ev: Event): void {
    const input = ev.target as HTMLInputElement;
    this.newFile = input.files && input.files[0] ? input.files[0] : null;
  }

  onSaveNewData(): void {
    if (!this.newFile) return;

    this.newDataBusy = true;
    this.newDataResult = null;

    this.api.uploadNewData(this.newFile, this.yoloText).subscribe({
      next: (r) => (this.newDataResult = r),
      error: (e) => (this.newDataResult = { ok: false, error: String(e) }),
      complete: () => {
        this.newDataBusy = false;
        this.refreshLogs();
      },
    });
  }

  // ---------------------------
  // Reentrenamiento incremental
  // ---------------------------
onRetrain(): void {
  this.retrainBusy = true;
  this.retrainResult = null;

  this.api.retrain().subscribe({
    next: (r) => {
      this.retrainResult = r;

      if (r?.status === "DONE") {
        this.api.reloadModel().subscribe({
          next: () => {
            this.refreshHealth();
            this.refreshLogs();
          },
          error: () => {
            this.refreshHealth();
            this.refreshLogs();
          },
        });
      } else {
        this.refreshHealth();
        this.refreshLogs();
      }
    },
    error: (e) => {
      this.retrainResult = { ok: false, error: String(e) };
      this.refreshLogs();
    },
    complete: () => {
      this.retrainBusy = false;
    },
  });
}

onPickAnnotFile(ev: Event): void {
  const input = ev.target as HTMLInputElement;
  const f = input.files && input.files[0] ? input.files[0] : null;
  if (!f) return;

  this.annotFile = f;

  if (this.annotPreviewUrl) URL.revokeObjectURL(this.annotPreviewUrl);
  this.annotPreviewUrl = URL.createObjectURL(f);

  // reset boxes
  this.boxes = [];
  this.currentRect = null;

  setTimeout(() => this.drawAnnotCanvas(), 0);
}

private drawAnnotCanvas(): void {
  const canvas = document.getElementById(this.annotCanvasId) as HTMLCanvasElement | null;
  if (!canvas || !this.annotPreviewUrl) return;

  const img = new Image();
  img.onload = () => {
    this.annotImgW = img.width;
    this.annotImgH = img.height;

    canvas.width = img.width;
    canvas.height = img.height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0);

    // dibujar cajas guardadas
    ctx.lineWidth = 3;
    ctx.font = "16px sans-serif";

    for (const b of this.boxes) {
      ctx.strokeStyle = "#f97316";
      ctx.strokeRect(b.x1, b.y1, b.x2 - b.x1, b.y2 - b.y1);

      const name = Object.keys(this.classToId).find(k => this.classToId[k] === b.cls) ?? String(b.cls);
      const label = `${name}`;
      ctx.fillStyle = "rgba(0,0,0,0.75)";
      ctx.fillRect(b.x1, Math.max(0, b.y1 - 18), ctx.measureText(label).width + 10, 20);
      ctx.fillStyle = "#fff";
      ctx.fillText(label, b.x1 + 5, Math.max(14, b.y1 - 3));
    }

    // rect actual (mientras dibujas)
    if (this.currentRect) {
      const r = this.currentRect;
      ctx.strokeStyle = "#22c55e";
      ctx.setLineDash([6, 4]);
      ctx.strokeRect(r.x1, r.y1, r.x2 - r.x1, r.y2 - r.y1);
      ctx.setLineDash([]);
    }
  };

  img.src = this.annotPreviewUrl;
}

onAnnotMouseDown(ev: MouseEvent): void {
  const canvas = ev.target as HTMLCanvasElement;
  const rect = canvas.getBoundingClientRect();

  const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
  const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

  this.isDrawing = true;
  this.startX = x;
  this.startY = y;
  this.currentRect = { x1: x, y1: y, x2: x, y2: y };

  this.drawAnnotCanvas();
}

onAnnotMouseMove(ev: MouseEvent): void {
  if (!this.isDrawing || !this.currentRect) return;
  const canvas = ev.target as HTMLCanvasElement;
  const rect = canvas.getBoundingClientRect();

  const x = (ev.clientX - rect.left) * (canvas.width / rect.width);
  const y = (ev.clientY - rect.top) * (canvas.height / rect.height);

  this.currentRect.x2 = x;
  this.currentRect.y2 = y;

  this.drawAnnotCanvas();
}

onAnnotMouseUp(ev: MouseEvent): void {
  if (!this.isDrawing || !this.currentRect) return;
  this.isDrawing = false;

  const r = this.normalizeRect(this.currentRect);
  this.currentRect = null;

  // ignorar cajas muy pequeñas
  if (Math.abs(r.x2 - r.x1) < 5 || Math.abs(r.y2 - r.y1) < 5) {
    this.drawAnnotCanvas();
    return;
  }

  const clsId = this.classToId[this.selectedClass] ?? 2;
  this.boxes.push({ cls: clsId, x1: r.x1, y1: r.y1, x2: r.x2, y2: r.y2 });

  this.drawAnnotCanvas();
}

private normalizeRect(r: { x1: number; y1: number; x2: number; y2: number }) {
  const x1 = Math.min(r.x1, r.x2);
  const x2 = Math.max(r.x1, r.x2);
  const y1 = Math.min(r.y1, r.y2);
  const y2 = Math.max(r.y1, r.y2);
  return { x1, y1, x2, y2 };
}

removeLastBox(): void {
  this.boxes.pop();
  this.drawAnnotCanvas();
}

clearBoxes(): void {
  this.boxes = [];
  this.drawAnnotCanvas();
}

 boxesToYoloText(): string {
  if (!this.annotImgW || !this.annotImgH) return "";

  const lines: string[] = [];
  for (const b of this.boxes) {
    const bw = b.x2 - b.x1;
    const bh = b.y2 - b.y1;
    const cx = b.x1 + bw / 2;
    const cy = b.y1 + bh / 2;

    const x = cx / this.annotImgW;
    const y = cy / this.annotImgH;
    const w = bw / this.annotImgW;
    const h = bh / this.annotImgH;

    // limitar a 6 decimales
    lines.push(`${b.cls} ${x.toFixed(6)} ${y.toFixed(6)} ${w.toFixed(6)} ${h.toFixed(6)}`);
  }
  return lines.join("\n");
}

saveAnnotatedAsNewData(): void {
  if (!this.annotFile) return;

  const yolo = this.boxesToYoloText();
  // si no hay boxes, igualmente puedes guardar como "sin objetos" o bloquear:
  if (!yolo.trim()) {
    this.newDataResult = { ok: false, error: "No hay cajas dibujadas." };
    return;
  }

  this.newDataBusy = true;
  this.newDataResult = null;

  this.api.uploadNewData(this.annotFile, yolo).subscribe({
    next: (r) => (this.newDataResult = r),
    error: (e) => (this.newDataResult = { ok: false, error: String(e) }),
    complete: () => {
      this.newDataBusy = false;
      this.refreshLogs();
      this.refreshHealth();
    },
  });
}


  // ---------------------------
  // Recargar modelo (si hay nuevo Production)
  // ---------------------------
onReloadModel(): void {
  this.reloadBusy = true;

  this.api.reloadModel().subscribe({
    next: () => {
      this.refreshHealth();
      this.refreshLogs();

      setTimeout(() => {
        this.reloadBusy = false;
      }, 1200);
    },
    error: (e) => {
      console.error(e);
      this.reloadBusy = false;
    }
  });
}


  retrainTextLog = '';

retrainParsed = {
  status: 'IDLE' as 'IDLE' | 'RUNNING' | 'DONE' | 'ERROR',
  epoch: 0,
  epochsTotal: 0,
  trainLoss: null as number | null,
  valLoss: null as number | null,
  epochTimeSec: null as number | null,
  etaSec: null as number | null,
};
private parseProgressFromLog(text: string) {
  this.retrainTextLog = text;

  const lines = text.split('\n').map(l => l.trim()).filter(Boolean);

  let lastEpoch: any = null;
  let lastDone: any = null;

  for (const ln of lines) {
    if (!ln.startsWith('{')) continue;
    try {
      const obj = JSON.parse(ln);

      if (obj.type === 'start') {
        this.retrainParsed.status = 'RUNNING';
        this.retrainParsed.epochsTotal = obj.epochs_total ?? 0;
      }

      if (obj.type === 'epoch') lastEpoch = obj;
      if (obj.type === 'done') lastDone = obj;

    } catch {}
  }

  if (lastEpoch) {
    this.retrainParsed.status = 'RUNNING';
    this.retrainParsed.epoch = lastEpoch.epoch ?? 0;
    this.retrainParsed.epochsTotal = lastEpoch.epochs_total ?? this.retrainParsed.epochsTotal;
    this.retrainParsed.trainLoss = lastEpoch.train_loss ?? null;
    this.retrainParsed.epochTimeSec = lastEpoch.epoch_time_sec ?? null;

    if (this.retrainParsed.epochsTotal > 0 && this.retrainParsed.epochTimeSec) {
      const remaining = this.retrainParsed.epochsTotal - this.retrainParsed.epoch;
      this.retrainParsed.etaSec = remaining * this.retrainParsed.epochTimeSec;
    }
  }

  if (lastDone) {
    this.retrainParsed.status = lastDone.status === 'OK' ? 'DONE' : 'ERROR';
  }
}
}
