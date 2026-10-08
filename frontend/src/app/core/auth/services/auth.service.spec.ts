import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';

import { environment } from '../../../../environments/environment';
import { AuthService } from './auth.service';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('no esta autenticado si no hay token guardado', () => {
    expect(service.estaAutenticado()).toBeFalse();
  });

  it('guarda los tokens y carga el perfil al iniciar sesion', () => {
    const usuario = {
      id: 1,
      email: 'analista@datapulse.com',
      nombre_completo: 'Analista',
      rol: 'ANALISTA' as const,
      activo: true,
      fecha_creacion: '2026-01-01T00:00:00Z',
    };

    service.login('analista@datapulse.com', 'ClaveSegura123').subscribe((respuesta) => {
      expect(respuesta).toEqual(usuario);
    });

    const loginReq = httpMock.expectOne(`${environment.apiUrl}/auth/login/`);
    loginReq.flush({ access: 'access-token', refresh: 'refresh-token' });

    const meReq = httpMock.expectOne(`${environment.apiUrl}/auth/me/`);
    meReq.flush(usuario);

    expect(service.accessToken).toBe('access-token');
    expect(service.estaAutenticado()).toBeTrue();
    expect(service.tieneRol(['ANALISTA'])).toBeTrue();
    expect(service.tieneRol(['ADMIN'])).toBeFalse();
  });

  it('logout limpia los tokens', () => {
    localStorage.setItem('datapulse_access', 'algo');
    service.logout();
    expect(service.accessToken).toBeNull();
    expect(service.estaAutenticado()).toBeFalse();
  });
});
