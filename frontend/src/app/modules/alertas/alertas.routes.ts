import { Routes } from '@angular/router';

export const alertasRoutes: Routes = [
  { path: '', loadComponent: () => import('./panel-alertas/panel-alertas').then((m) => m.PanelAlertas) },
];
