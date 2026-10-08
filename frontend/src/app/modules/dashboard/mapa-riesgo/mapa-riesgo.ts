import { Component, computed, input } from '@angular/core';
import { ChartConfiguration } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';

import { PuntoMapa } from '../../../core/services/dashboard.service';

@Component({
  selector: 'app-mapa-riesgo',
  imports: [BaseChartDirective],
  templateUrl: './mapa-riesgo.html',
  styleUrl: './mapa-riesgo.scss',
})
export class MapaRiesgo {
  readonly puntos = input<PuntoMapa[]>([]);

  protected readonly datosGrafico = computed<ChartConfiguration<'scatter'>['data']>(() => ({
    datasets: this.puntos().map((punto) => ({
      label: `${punto.nombre} (${punto.indice_compuesto})`,
      data: [{ x: punto.longitud, y: punto.latitud }],
      backgroundColor: punto.color,
      pointRadius: 10,
      pointHoverRadius: 12,
    })),
  }));

  protected readonly opciones: ChartConfiguration<'scatter'>['options'] = {
    plugins: { legend: { display: true, position: 'bottom', labels: { boxWidth: 10 } } },
    scales: {
      x: { title: { display: true, text: 'Longitud' } },
      y: { title: { display: true, text: 'Latitud' } },
    },
  };
}
