import { Directive, computed, input } from '@angular/core';

export type ModoColorRiesgo = 'texto' | 'fondo';

/**
 * Pinta el color por nivel de riesgo (el campo "color" que ya manda el backend segun
 * el IRPC) como texto o como fondo, sin repetir [style.color]/[style.background] en
 * cada plantilla: [appColorRiesgo]="fila.color" (texto) o con appColorRiesgoModo="fondo".
 */
@Directive({
  selector: '[appColorRiesgo]',
  host: {
    '[style.color]': 'colorTexto()',
    '[style.background-color]': 'colorFondo()',
  },
})
export class ColorRiesgoDirective {
  readonly appColorRiesgo = input<string | null | undefined>(null);
  readonly appColorRiesgoModo = input<ModoColorRiesgo>('texto');

  protected readonly colorTexto = computed(() => (this.appColorRiesgoModo() === 'texto' ? this.appColorRiesgo() : null));
  protected readonly colorFondo = computed(() => (this.appColorRiesgoModo() === 'fondo' ? this.appColorRiesgo() : null));
}
