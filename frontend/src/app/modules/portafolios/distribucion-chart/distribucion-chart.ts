import { Component, computed, input } from '@angular/core';
import { ChartConfiguration, ChartType } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

const PALETA = ['#3b82f6', '#22c55e', '#eab308', '#f97316', '#ef4444', '#8b5cf6', '#06b6d4', '#ec4899'];

@Component({
  selector: 'app-distribucion-chart',
  imports: [BaseChartDirective],
  templateUrl: './distribucion-chart.html',
  styleUrl: './distribucion-chart.scss',
})
export class DistribucionChart {
  readonly datos = input.required<Record<string, number>>();
  readonly tipo = input<ChartType>('pie');

  protected readonly datosGrafico = computed<ChartConfiguration['data']>(() => {
    const entradas = Object.entries(this.datos());
    return {
      labels: entradas.map(([clave]) => clave),
      datasets: [
        {
          data: entradas.map(([, valor]) => valor),
          backgroundColor: entradas.map((_, i) => PALETA[i % PALETA.length]),
        },
      ],
    };
  });
}
