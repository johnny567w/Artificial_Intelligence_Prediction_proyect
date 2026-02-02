/**
 * ApiService:
 * - Centraliza llamadas a FastAPI backend.
 * - Endpoints:
 *   GET  /health
 *   POST /predict (multipart)
 *   POST /predict-multi (multipart)
 *   POST /new-data (multipart)
 *   POST /retrain
 *   GET  /logs
 *   POST /reload-model
 */

import { Injectable } from "@angular/core";
import { HttpClient, HttpParams } from "@angular/common/http";
import { Observable } from "rxjs";

/** Tipos de respuesta */
export interface Detection {
  xyxy: [number, number, number, number];
  score: number;
  label: string;
}

export interface PredictItem {
  ok: boolean;
  filename?: string;
  image_w?: number;
  image_h?: number;
  inference_ms?: number;
  found?: boolean;
  detections?: Detection[];
  message?: string;
  error?: string;
}

export interface PredictMultiResponse {
  ok: boolean;
  results: PredictItem[];
}

@Injectable({ providedIn: "root" })
export class ApiService {
  private readonly base = "http://127.0.0.1:8000";

  constructor(private http: HttpClient) {}

  health(): Observable<{ ok?: boolean; status?: string } | any> {
    return this.http.get<{ ok?: boolean; status?: string }>(`${this.base}/health`);
  }

  /** Predict de 1 imagen */
  predict(file: File, scoreThreshold: number): Observable<PredictItem> {
    const fd = new FormData();
    fd.append("image", file);
    fd.append("score_threshold", String(scoreThreshold));
    return this.http.post<PredictItem>(`${this.base}/predict`, fd);
  }

  /** Predict de múltiples imágenes */
  predictMulti(files: File[], scoreThreshold: number): Observable<PredictMultiResponse> {
    const fd = new FormData();
    for (const f of files) fd.append("images", f);
    fd.append("score_threshold", String(scoreThreshold));
    return this.http.post<PredictMultiResponse>(`${this.base}/predict-multi`, fd);
  }

  /** Subir nueva data (imagen + label YOLO en texto) */
  uploadNewData(file: File, yoloLabelText: string): Observable<any> {
    const fd = new FormData();
    fd.append("image", file);
    fd.append("yolo_label_text", yoloLabelText);
    return this.http.post(`${this.base}/new-data`, fd);
  }

  retrain(): Observable<any> {
    return this.http.post(`${this.base}/retrain`, {});
  }

  reloadModel(): Observable<any> {
    return this.http.post(`${this.base}/reload-model`, {});
  }

  logs(lines: number = 200) {
  const ts = Date.now();
  const params = new HttpParams()
    .set('lines', String(lines))
    .set('ts', String(ts));
  return this.http.get(`${this.base}/logs`, { params, responseType: 'text' });
}

retrainProgress(lines: number = 120) {
  const ts = Date.now();
  const params = new HttpParams()
    .set('lines', String(lines))
    .set('ts', String(ts));
  return this.http.get(`${this.base}/retrain-progress`, { params, responseType: 'text' });
}

  getRetrainProgress(lines = 50) {
  return this.http.get<any>(`${this.base}/retrain-progress?lines=${lines}`);
}

}
