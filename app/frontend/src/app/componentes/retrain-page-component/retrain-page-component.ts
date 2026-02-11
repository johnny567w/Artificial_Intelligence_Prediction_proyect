import { Component, inject } from '@angular/core';
import { AppStateService } from '../../state/app-state.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-retrain-page-component',
  imports: [CommonModule],
  templateUrl: './retrain-page-component.html',
  styleUrl: './retrain-page-component.css',
})
export class RetrainPageComponent {
  state = inject(AppStateService);

}
