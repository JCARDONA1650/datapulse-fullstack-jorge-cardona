import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';
import { roleGuard } from './role.guard';

describe('roleGuard', () => {
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['tieneRol']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });
  });

  function rutaConRoles(roles?: string[]): ActivatedRouteSnapshot {
    return { data: { roles } } as unknown as ActivatedRouteSnapshot;
  }

  it('permite el acceso si la ruta no exige roles', () => {
    const resultado = TestBed.runInInjectionContext(() => roleGuard(rutaConRoles(undefined), {} as never));
    expect(resultado).toBeTrue();
  });

  it('permite el acceso si el usuario tiene el rol requerido', () => {
    authServiceSpy.tieneRol.and.returnValue(true);
    const resultado = TestBed.runInInjectionContext(() => roleGuard(rutaConRoles(['ADMIN']), {} as never));
    expect(resultado).toBeTrue();
  });

  it('redirige al dashboard si el usuario no tiene el rol requerido', () => {
    authServiceSpy.tieneRol.and.returnValue(false);
    const resultado = TestBed.runInInjectionContext(() => roleGuard(rutaConRoles(['ADMIN']), {} as never));
    expect(resultado).toBeFalse();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/dashboard']);
  });
});
