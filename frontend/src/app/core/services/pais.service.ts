import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from './api.service';

export type Region = 'ANDINA' | 'CONO_SUR' | 'CENTROAMERICA' | 'CARIBE';
export type TipoIndicador = 'PIB' | 'INFLACION' | 'DESEMPLEO' | 'BALANZA_COMERCIAL' | 'DEUDA_PIB' | 'PIB_PERCAPITA';

export interface Pais {
  codigo_iso: string;
  nombre: string;
  moneda_codigo: string;
  moneda_nombre: string;
  region: Region;
  latitud: string;
  longitud: string;
  poblacion: number;
  activo: boolean;
}

export interface IndicadorEconomico {
  id: number;
  pais: string;
  tipo: TipoIndicador;
  valor: string;
  unidad: string;
  anio: number;
  fuente: string;
  fecha_actualizacion: string;
}

export interface TipoCambio {
  id: number;
  moneda_origen: string;
  moneda_destino: string;
  tasa: string;
  fecha: string;
  variacion_porcentual: string | null;
  fuente: string;
}

export interface RespuestaPaginada<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface FiltrosPaises {
  region?: Region | '';
  search?: string;
  ordering?: string;
}

@Injectable({ providedIn: 'root' })
export class PaisService {
  private readonly api = inject(ApiService);

  listar(filtros?: FiltrosPaises): Observable<RespuestaPaginada<Pais>> {
    return this.api.get<RespuestaPaginada<Pais>>('/paises/', filtros);
  }

  obtener(codigoIso: string): Observable<Pais> {
    return this.api.get<Pais>(`/paises/${codigoIso}/`);
  }

  indicadores(
    codigoIso: string,
    filtros?: { tipo?: TipoIndicador; anio?: number; page_size?: number },
  ): Observable<RespuestaPaginada<IndicadorEconomico>> {
    return this.api.get<RespuestaPaginada<IndicadorEconomico>>(`/paises/${codigoIso}/indicadores/`, filtros);
  }

  tipoCambio(
    codigoIso: string,
    filtros?: { fecha_desde?: string; fecha_hasta?: string; page_size?: number },
  ): Observable<RespuestaPaginada<TipoCambio>> {
    return this.api.get<RespuestaPaginada<TipoCambio>>(`/paises/${codigoIso}/tipo-cambio/`, filtros);
  }

  sincronizarIndicadores(): Observable<unknown> {
    return this.api.post('/paises/sync-indicadores/', {});
  }
}
