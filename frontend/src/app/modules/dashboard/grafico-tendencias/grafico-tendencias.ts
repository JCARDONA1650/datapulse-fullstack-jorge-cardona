import { toSignal } from '@angular/core/rxjs-interop';
import { Component, computed, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { ChartConfiguration } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import { combineLatest, startWith } from 'rxjs';
import { switchMap } from 'rxjs/operators';

import { DashboardService } from '../../../core/services/dashboard.service';
import { PaisService, TipoIndicador } from '../../../core/services/pais.service';

const ETIQUETAS_TIPO: Record<TipoIndicador, string> = {
  PIB: 'PIB',
  PIB_PERCAPITA: 'PIB per capita',
  INFLACION: 'Inflacion',
  DESEMPLEO: 'Desempleo',
  BALANZA_COMERCIAL: 'Balanza comercial',
  DEUDA_PIB: 'Deuda/PIB',
};

const MAXIMO_PAISES = 3;
const COLORES = ['#3b82f6', '#22c55e', '#f97316'];

@Component({
  selector: 'app-grafico-tendencias',
  imports: [ReactiveFormsModule, MatFormFieldModule, MatSelectModule, BaseChartDirective],
  templateUrl: './grafico-tendencias.html',
  styleUrl: './grafico-tendencias.scss',
})
export class GraficoTendencias {
  private readonly dashboardService = inject(DashboardService);
  private readonly paisService = inject(PaisService);

  protected readonly tiposIndicador = Object.keys(ETIQUETAS_TIPO) as TipoIndicador[];
  protected readonly etiquetasTipo = ETIQUETAS_TIPO;
  protected readonly maximoPaises = MAXIMO_PAISES;

  protected readonly tipoSeleccionado = new FormControl<TipoIndicador>('PIB_PERCAPITA', { nonNullable: true });
  protected readonly paisesSeleccionados = new FormControl<string[]>(['CO', 'BR', 'MX'], { nonNullable: true });

  protected readonly paises = toSignal(this.paisService.listar({ ordering: 'nombre' }), { initialValue: null });

  protected readonly tendencias = toSignal(
    combineLatest([
      this.tipoSeleccionado.valueChanges.pipe(startWith(this.tipoSeleccionado.value)),
      this.paisesSeleccionados.valueChanges.pipe(startWith(this.paisesSeleccionados.value)),
    ]).pipe(switchMap(([tipo, paises]) => this.dashboardService.tendencias(tipo, paises.slice(0, MAXIMO_PAISES)))),
    { initialValue: null },
  );

  protected readonly datosGrafico = computed<ChartConfiguration<'line'>['data']>(() => {
    const datos = this.tendencias() ?? {};
    const anios = [...new Set(Object.values(datos).flat().map((punto) => punto.anio))].sort((a, b) => a - b);

    return {
      labels: anios.map(String),
      datasets: Object.entries(datos).map(([codigo, puntos], indice) => {
        const porAnio = new Map(puntos.map((punto) => [punto.anio, punto.valor]));
        return {
          label: codigo,
          data: anios.map((anio) => porAnio.get(anio) ?? null),
          borderColor: COLORES[indice % COLORES.length],
          tension: 0.3,
        };
      }),
    };
  });
}
