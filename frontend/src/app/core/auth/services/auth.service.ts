import { Injectable, inject } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { switchMap, tap } from 'rxjs/operators';

import { ApiService } from '../../services/api.service';

export type Rol = 'ADMIN' | 'ANALISTA' | 'VIEWER';

export interface Usuario {
  id: number;
  email: string;
  nombre_completo: string;
  rol: Rol;
  activo: boolean;
  fecha_creacion: string;
}

export interface DatosRegistro {
  email: string;
  nombre_completo: string;
  password: string;
  password2: string;
}

interface TokensRespuesta {
  access: string;
  refresh: string;
}

const CLAVE_ACCESS = 'datapulse_access';
const CLAVE_REFRESH = 'datapulse_refresh';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly api = inject(ApiService);
  private readonly usuarioSubject = new BehaviorSubject<Usuario | null>(null);
  readonly usuario$ = this.usuarioSubject.asObservable();

  login(email: string, password: string): Observable<Usuario> {
    return this.api.post<TokensRespuesta>('/auth/login/', { email, password }).pipe(
      tap((tokens) => this.guardarTokens(tokens)),
      switchMap(() => this.cargarPerfil()),
    );
  }

  registrar(datos: DatosRegistro): Observable<Usuario> {
    return this.api.post<Usuario>('/auth/register/', datos);
  }

  cargarPerfil(): Observable<Usuario> {
    return this.api.get<Usuario>('/auth/me/').pipe(tap((usuario) => this.usuarioSubject.next(usuario)));
  }

  actualizarPerfil(datos: Partial<Pick<Usuario, 'nombre_completo'>>): Observable<Usuario> {
    return this.api.put<Usuario>('/auth/me/', datos).pipe(tap((usuario) => this.usuarioSubject.next(usuario)));
  }

  logout(): void {
    localStorage.removeItem(CLAVE_ACCESS);
    localStorage.removeItem(CLAVE_REFRESH);
    this.usuarioSubject.next(null);
  }

  get accessToken(): string | null {
    return localStorage.getItem(CLAVE_ACCESS);
  }

  get refreshTokenValue(): string | null {
    return localStorage.getItem(CLAVE_REFRESH);
  }

  estaAutenticado(): boolean {
    return !!this.accessToken;
  }

  tieneRol(roles: Rol[]): boolean {
    const usuario = this.usuarioSubject.value;
    return !!usuario && roles.includes(usuario.rol);
  }

  private guardarTokens(tokens: TokensRespuesta): void {
    localStorage.setItem(CLAVE_ACCESS, tokens.access);
    localStorage.setItem(CLAVE_REFRESH, tokens.refresh);
  }
}
