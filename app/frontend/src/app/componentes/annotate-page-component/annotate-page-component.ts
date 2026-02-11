import { Component, inject } from '@angular/core';
import { AppStateService } from '../../state/app-state.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-annotate-page-component',
  imports: [CommonModule,FormsModule],
  templateUrl: './annotate-page-component.html',
  styleUrl: './annotate-page-component.css',
})
export class AnnotatePageComponent {
state = inject(AppStateService);

}
