import { Routes } from '@angular/router';

export const paisesRoutes: Routes = [
  { path: '', loadComponent: () => import('./lista-paises/lista-paises').then((m) => m.ListaPaises) },
  { path: ':codigoIso', loadComponent: () => import('./detalle-pais/detalle-pais').then((m) => m.DetallePais) },
];
