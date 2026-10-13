import { IndicadorEconomico } from '../../core/services/pais.service';
import { FormatoIndicadorPipe } from './formato-indicador.pipe';

function indicador(valor: string, unidad: string): IndicadorEconomico {
  return { id: 1, pais: 'CO', tipo: 'PIB', valor, unidad, anio: 2023, fuente: 'MANUAL', fecha_actualizacion: '' };
}

describe('FormatoIndicadorPipe', () => {
  const pipe = new FormatoIndicadorPipe();

  it('formatea USD_MILES_MILLONES agregando "mil millones"', () => {
    expect(pipe.transform(indicador('335', 'USD_MILES_MILLONES'))).toBe('USD 335 mil millones');
  });

  it('formatea USD con separador de miles y sin decimales', () => {
    expect(pipe.transform(indicador('16700', 'USD'))).toBe('USD 16,700');
  });

  it('formatea PORCENTAJE con un decimal y simbolo %', () => {
    expect(pipe.transform(indicador('9.2', 'PORCENTAJE'))).toBe('9.2%');
  });

  it('devuelve cadena vacia si no hay indicador', () => {
    expect(pipe.transform(null)).toBe('');
  });
});
