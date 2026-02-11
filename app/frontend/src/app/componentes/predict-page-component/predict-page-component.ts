import { Component, inject } from '@angular/core';
import { AppStateService } from '../../state/app-state.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-predict-page-component',
  imports: [CommonModule],
  templateUrl: './predict-page-component.html',
  styleUrl: './predict-page-component.css',
})
export class PredictPageComponent {
  state = inject(AppStateService);

}
