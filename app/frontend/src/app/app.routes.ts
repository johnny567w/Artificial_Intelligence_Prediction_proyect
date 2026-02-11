import { Routes } from '@angular/router';
import { App } from './app';
import { HomePage } from './componentes/home-page/home-page';
import { PredictPageComponent } from './componentes/predict-page-component/predict-page-component';
import { AnnotatePageComponent } from './componentes/annotate-page-component/annotate-page-component';
import { RetrainPageComponent } from './componentes/retrain-page-component/retrain-page-component';


export const routes: Routes = [
  { path: '', component: HomePage },
  { path: 'predict', component: PredictPageComponent },
  { path: 'annotate', component: AnnotatePageComponent },
  { path: 'retrain', component: RetrainPageComponent },
  { path: '**', redirectTo: '' },
];