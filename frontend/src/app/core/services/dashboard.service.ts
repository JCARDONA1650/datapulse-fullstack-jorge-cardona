import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from './api.service';
import { TipoIndicador } from './pais.service';

export interface ResumenDashboard {
  total_paises_monitoreados: number;
  alertas_activas: number;
  portafolios_usuario: number;
  promedio_irpc_region: number | null;
}

export interface PuntoMapa {
  codigo_iso: string;
  nombre: string;
  latitud: number;
  longitud: number;
  indice_compuesto: number;
  nivel_riesgo: string;
  color: string;
}

export interface PuntoTendencia {
  anio: number;
  valor: number;
}

export type Tendencias = Record<string, PuntoTendencia[]>;

@Injectable({ providedIn: 'root' })
export class DashboardService {
  private readonly api = inject(ApiService);

  resumen(): Observable<ResumenDashboard> {
    return this.api.get<ResumenDashboard>('/dashboard/resumen/');
  }

  mapa(): Observable<PuntoMapa[]> {
    return this.api.get<PuntoMapa[]>('/dashboard/mapa/');
  }

  tendencias(tipo: TipoIndicador, paises: string[]): Observable<Tendencias> {
    return this.api.get<Tendencias>('/dashboard/tendencias/', { tipo, paises: paises.join(',') });
  }
}
