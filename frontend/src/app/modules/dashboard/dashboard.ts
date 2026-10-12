import { toSignal } from '@angular/core/rxjs-interop';
import { Component, inject } from '@angular/core';
import { MatCardModule } from '@angular/material/card';

import { DashboardService } from '../../core/services/dashboard.service';
import { RiesgoService } from '../../core/services/riesgo.service';
import { GraficoTendencias } from './grafico-tendencias/grafico-tendencias';
import { KpiCards } from './kpi-cards/kpi-cards';
import { MapaRiesgo } from './mapa-riesgo/mapa-riesgo';
import { TablaRanking } from './tabla-ranking/tabla-ranking';

@Component({
  selector: 'app-dashboard',
  imports: [MatCardModule, KpiCards, MapaRiesgo, TablaRanking, GraficoTendencias],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class Dashboard {
  private readonly dashboardService = inject(DashboardService);
  private readonly riesgoService = inject(RiesgoService);

  protected readonly resumen = toSignal(this.dashboardService.resumen(), { initialValue: null });
  protected readonly mapa = toSignal(this.dashboardService.mapa(), { initialValue: [] });
  protected readonly ranking = toSignal(this.riesgoService.ranking(), { initialValue: null });
}
