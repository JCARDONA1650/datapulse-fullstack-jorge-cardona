import { DecimalPipe } from '@angular/common';
import { Component, input } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';

import { IndiceRiesgo } from '../../../core/services/riesgo.service';

@Component({
  selector: 'app-tabla-ranking',
  imports: [DecimalPipe, MatIconModule, MatTableModule],
  templateUrl: './tabla-ranking.html',
  styleUrl: './tabla-ranking.scss',
})
export class TablaRanking {
  readonly ranking = input<IndiceRiesgo[]>([]);
  protected readonly columnas = ['pais_nombre', 'indice_compuesto', 'nivel_riesgo', 'variacion', 'tendencia'];

  protected icono(variacion: number | null): string {
    if (variacion === null) {
      return 'remove';
    }
    if (variacion > 0) {
      return 'trending_up';
    }
    if (variacion < 0) {
      return 'trending_down';
    }
    return 'trending_flat';
  }
}
