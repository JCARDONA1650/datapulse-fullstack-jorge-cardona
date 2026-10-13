import { Pipe, PipeTransform } from '@angular/core';

import { IndicadorEconomico } from '../../core/services/pais.service';

/** Valor + unidad legibles en espanol: "USD 335.00 mil millones", "9.2%", "USD 16,700". */
@Pipe({ name: 'formatoIndicador' })
export class FormatoIndicadorPipe implements PipeTransform {
  transform(indicador: IndicadorEconomico | null | undefined): string {
    if (!indicador) {
      return '';
    }

    const valor = Number(indicador.valor);
    switch (indicador.unidad) {
      case 'USD_MILES_MILLONES':
        return `USD ${this.formatearNumero(valor, 0, 2)} mil millones`;
      case 'USD':
        return `USD ${this.formatearNumero(valor, 0, 0)}`;
      case 'PORCENTAJE':
        return `${this.formatearNumero(valor, 1, 1)}%`;
      default:
        return `${valor}`;
    }
  }

  private formatearNumero(valor: number, minDecimales: number, maxDecimales: number): string {
    return valor.toLocaleString('en-US', { minimumFractionDigits: minDecimales, maximumFractionDigits: maxDecimales });
  }
}
