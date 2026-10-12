import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from './api.service';
import { RespuestaPaginada } from './pais.service';

export type TipoActivo = 'RENTA_FIJA' | 'RENTA_VARIABLE' | 'COMMODITIES' | 'MONEDA';

export interface Posicion {
  id: number;
  portafolio: number;
  pais: string;
  pais_nombre: string;
  tipo_activo: TipoActivo;
  monto_inversion_usd: string;
  fecha_entrada: string;
  fecha_salida: string | null;
  notas: string;
}

export interface Portafolio {
  id: number;
  nombre: string;
  descripcion: string;
  usuario: number;
  es_propio: boolean;
  fecha_creacion: string;
  fecha_modificacion: string;
  activo: boolean;
  es_publico: boolean;
}

export interface PortafolioDetalle extends Portafolio {
  posiciones: Posicion[];
}

export interface ResumenPortafolio {
  monto_total_usd: number;
  distribucion_por_pais: Record<string, number>;
  distribucion_por_tipo_activo: Record<string, number>;
  riesgo_promedio_ponderado: number | null;
}

export interface DatosPortafolio {
  nombre: string;
  descripcion: string;
  es_publico: boolean;
  fecha_modificacion?: string;
}

export interface DatosPosicion {
  pais: string;
  tipo_activo: TipoActivo;
  monto_inversion_usd: number;
  fecha_entrada: string;
  notas?: string;
}

@Injectable({ providedIn: 'root' })
export class PortafolioService {
  private readonly api = inject(ApiService);

  listar(filtros?: { search?: string; ordering?: string }): Observable<RespuestaPaginada<Portafolio>> {
    return this.api.get<RespuestaPaginada<Portafolio>>('/portafolios/', filtros);
  }

  obtener(id: number): Observable<PortafolioDetalle> {
    return this.api.get<PortafolioDetalle>(`/portafolios/${id}/`);
  }

  crear(datos: Omit<DatosPortafolio, 'fecha_modificacion'>): Observable<Portafolio> {
    return this.api.post<Portafolio>('/portafolios/', datos);
  }

  actualizar(id: number, datos: DatosPortafolio): Observable<Portafolio> {
    return this.api.put<Portafolio>(`/portafolios/${id}/`, datos);
  }

  eliminar(id: number): Observable<void> {
    return this.api.delete<void>(`/portafolios/${id}/`);
  }

  resumen(id: number): Observable<ResumenPortafolio> {
    return this.api.get<ResumenPortafolio>(`/portafolios/${id}/resumen/`);
  }

  exportarPdf(id: number): Observable<Blob> {
    return this.api.getBlob(`/portafolios/${id}/export/pdf/`);
  }

  crearPosicion(portafolioId: number, datos: DatosPosicion): Observable<Posicion> {
    return this.api.post<Posicion>(`/portafolios/${portafolioId}/posiciones/`, datos);
  }

  actualizarPosicion(portafolioId: number, posicionId: number, datos: DatosPosicion): Observable<Posicion> {
    return this.api.put<Posicion>(`/portafolios/${portafolioId}/posiciones/${posicionId}/`, datos);
  }

  cerrarPosicion(portafolioId: number, posicionId: number): Observable<Posicion> {
    return this.api.delete<Posicion>(`/portafolios/${portafolioId}/posiciones/${posicionId}/`);
  }
}
