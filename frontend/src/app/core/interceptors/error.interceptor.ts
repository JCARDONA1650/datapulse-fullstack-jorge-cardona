import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { AuthService } from '../auth/services/auth.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const snackBar = inject(MatSnackBar);
  const router = inject(Router);
  const authService = inject(AuthService);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status === 400) {
        return throwError(() => error);
      }

      let mensaje = extraerMensaje(error) ?? 'Ocurrio un error inesperado. Intenta de nuevo.';

      if (error.status === 0) {
        mensaje = 'No se pudo conectar con el servidor. Verifica tu conexion.';
      } else if (error.status === 401 && !req.url.includes('/auth/login/')) {
        mensaje = 'Tu sesion expiro. Inicia sesion nuevamente.';
        authService.logout();
        router.navigate(['/login']);
      }

      snackBar.open(mensaje, 'Cerrar', { duration: 5000 });
      return throwError(() => error);
    }),
  );
};

function extraerMensaje(error: HttpErrorResponse): string | null {
  const cuerpo = error.error?.mensaje;
  if (typeof cuerpo === 'string') {
    return cuerpo;
  }
  if (cuerpo && typeof cuerpo === 'object') {
    const primerCampo = Object.values(cuerpo)[0];
    return Array.isArray(primerCampo) ? String(primerCampo[0]) : String(primerCampo);
  }
  return null;
}
