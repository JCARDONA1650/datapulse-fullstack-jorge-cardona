import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = environment.apiUrl;

  get<T>(path: string, params?: object): Observable<T> {
    return this.http.get<T>(`${this.baseUrl}${path}`, { params: this.limpiarParams(params) });
  }

  post<T>(path: string, body: unknown): Observable<T> {
    return this.http.post<T>(`${this.baseUrl}${path}`, body);
  }

  put<T>(path: string, body: unknown): Observable<T> {
    return this.http.put<T>(`${this.baseUrl}${path}`, body);
  }

  delete<T>(path: string): Observable<T> {
    return this.http.delete<T>(`${this.baseUrl}${path}`);
  }

  getBlob(path: string): Observable<Blob> {
    return this.http.get(`${this.baseUrl}${path}`, { responseType: 'blob' });
  }

  private limpiarParams(params?: object): Record<string, string> | undefined {
    if (!params) {
      return undefined;
    }

    const limpio: Record<string, string> = {};
    for (const [clave, valor] of Object.entries(params as Record<string, unknown>)) {
      if (valor !== undefined && valor !== null && valor !== '') {
        limpio[clave] = String(valor);
      }
    }
    return limpio;
  }
}
