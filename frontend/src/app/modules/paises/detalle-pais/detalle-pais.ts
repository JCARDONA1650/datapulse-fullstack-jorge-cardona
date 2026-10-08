import { DecimalPipe } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { Component, computed, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { ActivatedRoute } from '@angular/router';
import { ChartConfiguration } from 'chart.js';
import { BaseChartDirective } from 'ng2-charts';
import { switchMap } from 'rxjs/operators';

import { IndicadorEconomico, PaisService, TipoIndicador } from '../../../core/services/pais.service';

const ETIQUETAS_TIPO: Record<TipoIndicador, string> = {
  PIB: 'PIB',
  PIB_PERCAPITA: 'PIB per capita',
  INFLACION: 'Inflacion',
  DESEMPLEO: 'Desempleo',
  BALANZA_COMERCIAL: 'Balanza comercial',
  DEUDA_PIB: 'Deuda/PIB',
};

@Component({
  selector: 'app-detalle-pais',
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    MatCardModule,
    MatSelectModule,
    MatFormFieldModule,
    MatProgressSpinnerModule,
    BaseChartDirective,
  ],
  templateUrl: './detalle-pais.html',
  styleUrl: './detalle-pais.scss',
})
export class DetallePais {
  private readonly route = inject(ActivatedRoute);
  private readonly paisService = inject(PaisService);

  protected readonly tiposIndicador = Object.keys(ETIQUETAS_TIPO) as TipoIndicador[];
  protected readonly etiquetasTipo = ETIQUETAS_TIPO;
  protected readonly tipoSeleccionado = new FormControl<TipoIndicador>('PIB_PERCAPITA', { nonNullable: true });

  protected readonly pais = toSignal(
    this.route.paramMap.pipe(switchMap((params) => this.paisService.obtener(params.get('codigoIso')!))),
    { initialValue: null },
  );

  protected readonly indicadores = toSignal(
    this.route.paramMap.pipe(
      switchMap((params) => this.paisService.indicadores(params.get('codigoIso')!, { page_size: 100 })),
    ),
    { initialValue: null },
  );

  protected readonly tipoCambio = toSignal(
    this.route.paramMap.pipe(
      switchMap((params) => this.paisService.tipoCambio(params.get('codigoIso')!, { page_size: 30 })),
    ),
    { initialValue: null },
  );

  protected readonly indicadoresActuales = computed(() => {
    const resultados = this.indicadores()?.results ?? [];
    const porTipo = new Map<TipoIndicador, IndicadorEconomico>();
    for (const indicador of resultados) {
      const actual = porTipo.get(indicador.tipo);
      if (!actual || indicador.anio > actual.anio) {
        porTipo.set(indicador.tipo, indicador);
      }
    }
    return porTipo;
  });

  protected readonly datosGraficoIndicador = computed<ChartConfiguration<'line'>['data']>(() => {
    const tipo = this.tipoSeleccionado.value;
    const resultados = (this.indicadores()?.results ?? [])
      .filter((indicador) => indicador.tipo === tipo)
      .sort((a, b) => a.anio - b.anio);

    return {
      labels: resultados.map((indicador) => String(indicador.anio)),
      datasets: [
        { label: ETIQUETAS_TIPO[tipo], data: resultados.map((indicador) => Number(indicador.valor)), tension: 0.3 },
      ],
    };
  });

  protected readonly datosGraficoTipoCambio = computed<ChartConfiguration<'line'>['data']>(() => {
    const resultados = [...(this.tipoCambio()?.results ?? [])].sort((a, b) => a.fecha.localeCompare(b.fecha));

    return {
      labels: resultados.map((tipoCambio) => tipoCambio.fecha),
      datasets: [
        {
          label: `${this.pais()?.moneda_codigo ?? ''} / USD`,
          data: resultados.map((tipoCambio) => Number(tipoCambio.tasa)),
          tension: 0.3,
        },
      ],
    };
  });

  protected bandera(codigoIso: string): string {
    return `https://flagcdn.com/w80/${codigoIso.toLowerCase()}.png`;
  }
}
