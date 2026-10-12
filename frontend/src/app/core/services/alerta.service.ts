import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from './api.service';
import { RespuestaPaginada } from './pais.service';

export type TipoAlerta = 'RIESGO' | 'TIPO_CAMBIO' | 'INDICADOR';
export type SeveridadAlerta = 'INFO' | 'WARNING' | 'CRITICAL';

export interface Alerta {
  id: number;
  usuario: number | null;
  pais: string;
  pais_nombre: string;
  tipo_alerta: TipoAlerta;
  severidad: SeveridadAlerta;
  titulo: string;
  mensaje: string;
  leida: boolean;
  fecha_creacion: string;
}

export interface ResumenAlertas {
  no_leidas: number;
  por_tipo: Record<string, number>;
  por_severidad: Record<string, number>;
}

export interface FiltrosAlertas {
  tipo_alerta?: TipoAlerta | '';
  severidad?: SeveridadAlerta | '';
  leida?: '' | 'true' | 'false';
}

@Injectable({ providedIn: 'root' })
export class AlertaService {
  private readonly api = inject(ApiService);

  listar(filtros?: FiltrosAlertas): Observable<RespuestaPaginada<Alerta>> {
    return this.api.get<RespuestaPaginada<Alerta>>('/alertas/', filtros);
  }

  marcarLeida(id: number): Observable<Alerta> {
    return this.api.put<Alerta>(`/alertas/${id}/leer/`, {});
  }

  marcarTodasLeidas(): Observable<unknown> {
    return this.api.put('/alertas/leer-todas/', {});
  }

  resumen(): Observable<ResumenAlertas> {
    return this.api.get<ResumenAlertas>('/alertas/resumen/');
  }
}
