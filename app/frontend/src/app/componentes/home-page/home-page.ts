import { Component, inject } from '@angular/core';
import { AppStateService } from '../../state/app-state.service';

@Component({
  selector: 'app-home-page',
  imports: [],
  templateUrl: './home-page.html',
  styleUrl: './home-page.css',
})
export class HomePage {
  state = inject(AppStateService);

}
