import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService, Rol } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const rolesPermitidos = (route.data['roles'] as Rol[] | undefined) ?? [];

  if (rolesPermitidos.length === 0 || authService.tieneRol(rolesPermitidos)) {
    return true;
  }

  router.navigate(['/dashboard']);
  return false;
};
