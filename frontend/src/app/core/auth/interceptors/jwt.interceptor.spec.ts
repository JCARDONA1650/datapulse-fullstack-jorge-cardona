import { HttpHandlerFn, HttpRequest } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { of } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { jwtInterceptor } from './jwt.interceptor';

describe('jwtInterceptor', () => {
  let authServiceStub: Partial<AuthService>;

  beforeEach(() => {
    authServiceStub = { accessToken: 'token-123' };
    TestBed.configureTestingModule({
      providers: [{ provide: AuthService, useValue: authServiceStub }],
    });
  });

  it('agrega el header Authorization cuando hay token y la ruta no es publica', (done) => {
    const peticion = new HttpRequest('GET', '/api/paises/');
    const next: HttpHandlerFn = (peticionModificada) => {
      expect(peticionModificada.headers.get('Authorization')).toBe('Bearer token-123');
      done();
      return of();
    };

    TestBed.runInInjectionContext(() => jwtInterceptor(peticion, next));
  });

  it('no agrega el header en rutas publicas de autenticacion', (done) => {
    const peticion = new HttpRequest('POST', '/api/auth/login/', {});
    const next: HttpHandlerFn = (peticionModificada) => {
      expect(peticionModificada.headers.has('Authorization')).toBeFalse();
      done();
      return of();
    };

    TestBed.runInInjectionContext(() => jwtInterceptor(peticion, next));
  });
});
