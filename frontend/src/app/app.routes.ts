import { Routes } from '@angular/router';

import { authGuard } from './core/auth/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
  { path: 'login', loadComponent: () => import('./modules/auth/login/login').then((m) => m.Login) },
  { path: 'register', loadComponent: () => import('./modules/auth/register/register').then((m) => m.Register) },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./modules/dashboard/dashboard').then((m) => m.Dashboard),
  },
  {
    path: 'paises',
    canActivate: [authGuard],
    loadChildren: () => import('./modules/paises/paises.routes').then((m) => m.paisesRoutes),
  },
  {
    path: 'alertas',
    canActivate: [authGuard],
    loadChildren: () => import('./modules/alertas/alertas.routes').then((m) => m.alertasRoutes),
  },
  {
    path: 'portafolios',
    canActivate: [authGuard],
    loadChildren: () => import('./modules/portafolios/portafolios.routes').then((m) => m.portafoliosRoutes),
  },
  { path: '**', loadComponent: () => import('./shared/not-found/not-found').then((m) => m.NotFound) },
];
