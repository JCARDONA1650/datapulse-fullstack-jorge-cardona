import { KeyValuePipe } from '@angular/common';
import { Component, computed, input } from '@angular/core';
import { ChartConfiguration, ChartType } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

const PALETA = ['#1b75bb', '#29234f', '#06b6d4', '#8b5cf6', '#22c55e', '#eab308', '#f97316', '#64748b'];

@Component({
  selector: 'app-distribucion-chart',
  imports: [KeyValuePipe, BaseChartDirective],
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
