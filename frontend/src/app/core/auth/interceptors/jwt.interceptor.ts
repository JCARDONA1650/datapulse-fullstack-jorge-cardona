import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';

import { AuthService } from '../services/auth.service';

const RUTAS_PUBLICAS = ['/auth/login/', '/auth/register/', '/auth/refresh/'];

export const jwtInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const esPublica = RUTAS_PUBLICAS.some((ruta) => req.url.includes(ruta));

  if (esPublica || !authService.accessToken) {
    return next(req);
  }

  const clonado = req.clone({
    setHeaders: { Authorization: `Bearer ${authService.accessToken}` },
  });
  return next(clonado);
};
