import { Routes } from '@angular/router';

import { roleGuard } from '../../core/auth/guards/role.guard';

export const portafoliosRoutes: Routes = [
  { path: '', loadComponent: () => import('./lista/lista').then((m) => m.Lista) },
  {
    path: 'crear',
    canActivate: [roleGuard],
    data: { roles: ['ADMIN', 'ANALISTA'] },
    loadComponent: () => import('./crear/crear').then((m) => m.Crear),
  },
  {
    path: ':id/editar',
    canActivate: [roleGuard],
    data: { roles: ['ADMIN', 'ANALISTA'] },
    loadComponent: () => import('./crear/crear').then((m) => m.Crear),
  },
  { path: ':id', loadComponent: () => import('./detalle/detalle').then((m) => m.Detalle) },
];
