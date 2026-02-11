/**
 * App (standalone):
 * - UI Tailwind: modelo activo, predicción (múltiples imágenes con canvas), nuevos datos, reentrenamiento y logs.
 * - Usa ApiService para comunicar con FastAPI.
 * - Dibuja bounding boxes y etiquetas con porcentaje sobre un canvas por imagen.
 */

import { Component, inject, OnDestroy, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription, interval } from 'rxjs';
import { switchMap } from 'rxjs/operators';

import { ApiService } from './api.service';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AppStateService } from './state/app-state.service';
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule,RouterOutlet,RouterLink,RouterLinkActive],
  templateUrl: './app.html',
})
export class App {
  state = inject(AppStateService);
}
