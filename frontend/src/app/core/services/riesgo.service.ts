import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from './api.service';
import { RespuestaPaginada } from './pais.service';

export type NivelRiesgo = 'BAJO' | 'MODERADO' | 'ALTO' | 'CRITICO';

export interface IndiceRiesgo {
  id: number;
  pais: string;
  pais_nombre: string;
  fecha_calculo: string;
  score_economico: string;
  score_cambiario: string;
  score_estabilidad: string;
  indice_compuesto: string;
  nivel_riesgo: NivelRiesgo;
  color: string;
  detalle_calculo: Record<string, unknown>;
}

@Injectable({ providedIn: 'root' })
export class RiesgoService {
  private readonly api = inject(ApiService);

  ranking(): Observable<RespuestaPaginada<IndiceRiesgo>> {
    return this.api.get<RespuestaPaginada<IndiceRiesgo>>('/riesgo/');
  }

  obtener(codigoIso: string): Observable<IndiceRiesgo> {
    return this.api.get<IndiceRiesgo>(`/riesgo/${codigoIso}/`);
  }

  historico(codigoIso: string, filtros?: { fecha_desde?: string; fecha_hasta?: string }): Observable<RespuestaPaginada<IndiceRiesgo>> {
    return this.api.get<RespuestaPaginada<IndiceRiesgo>>(`/riesgo/${codigoIso}/historico/`, filtros);
  }

  calcular(): Observable<IndiceRiesgo[]> {
    return this.api.post<IndiceRiesgo[]>('/riesgo/calcular/', {});
  }
}
