import { Component } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ColorRiesgoDirective } from './color-riesgo.directive';

@Component({
  imports: [ColorRiesgoDirective],
  template: `
    <span id="texto" [appColorRiesgo]="color">texto</span>
    <span id="fondo" [appColorRiesgo]="color" appColorRiesgoModo="fondo">fondo</span>
  `,
})
class HostDePrueba {
  color = '#ef4444';
}

describe('ColorRiesgoDirective', () => {
  let fixture: ComponentFixture<HostDePrueba>;

  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [HostDePrueba] });
    fixture = TestBed.createComponent(HostDePrueba);
    fixture.detectChanges();
  });

  it('pinta el texto en modo "texto" (el default)', () => {
    const elemento: HTMLElement = fixture.nativeElement.querySelector('#texto');
    expect(elemento.style.color).toBe('rgb(239, 68, 68)');
    expect(elemento.style.backgroundColor).toBe('');
  });

  it('pinta el fondo en modo "fondo"', () => {
    const elemento: HTMLElement = fixture.nativeElement.querySelector('#fondo');
    expect(elemento.style.backgroundColor).toBe('rgb(239, 68, 68)');
    expect(elemento.style.color).toBe('');
  });
});
