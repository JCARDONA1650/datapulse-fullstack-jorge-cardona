import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router } from '@angular/router';
import { Observable, of } from 'rxjs';

import { AuthService, Usuario } from '../services/auth.service';
import { roleGuard } from './role.guard';

describe('roleGuard', () => {
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['tieneRol', 'perfilListo']);
    authServiceSpy.perfilListo.and.returnValue(of(null));
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

  function resolver(resultado: boolean | Observable<boolean>): Promise<boolean> {
    return resultado instanceof Observable ? new Promise((resolve) => resultado.subscribe(resolve)) : Promise.resolve(resultado);
  }

  it('permite el acceso si la ruta no exige roles', async () => {
    const resultado = TestBed.runInInjectionContext(() => roleGuard(rutaConRoles(undefined), {} as never));
    expect(await resolver(resultado as boolean)).toBeTrue();
  });

  it('espera el perfil y permite el acceso si el usuario tiene el rol requerido', async () => {
    authServiceSpy.perfilListo.and.returnValue(of({} as Usuario));
    authServiceSpy.tieneRol.and.returnValue(true);

    const resultado = TestBed.runInInjectionContext(() => roleGuard(rutaConRoles(['ADMIN']), {} as never));
    expect(await resolver(resultado as Observable<boolean>)).toBeTrue();
  });

  it('redirige al dashboard si el usuario no tiene el rol requerido', async () => {
    authServiceSpy.perfilListo.and.returnValue(of({} as Usuario));
    authServiceSpy.tieneRol.and.returnValue(false);

    const resultado = TestBed.runInInjectionContext(() => roleGuard(rutaConRoles(['ADMIN']), {} as never));
    expect(await resolver(resultado as Observable<boolean>)).toBeFalse();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/dashboard']);
  });
});
