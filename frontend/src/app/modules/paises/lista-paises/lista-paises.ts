import { DecimalPipe } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { Component, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';
import { Router } from '@angular/router';
import { combineLatest, startWith } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

import { PaisService, Region } from '../../../core/services/pais.service';

@Component({
  selector: 'app-lista-paises',
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatTableModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './lista-paises.html',
  styleUrl: './lista-paises.scss',
})
export class ListaPaises {
  private readonly paisService = inject(PaisService);
  private readonly router = inject(Router);

  protected readonly columnas = ['codigo_iso', 'nombre', 'region', 'moneda_codigo', 'poblacion'];
  protected readonly busqueda = new FormControl('');
  protected readonly region = new FormControl<Region | ''>('');

  protected readonly regiones: { valor: Region; etiqueta: string }[] = [
    { valor: 'ANDINA', etiqueta: 'Andina' },
    { valor: 'CONO_SUR', etiqueta: 'Cono Sur' },
    { valor: 'CENTROAMERICA', etiqueta: 'Centroamerica' },
    { valor: 'CARIBE', etiqueta: 'Caribe' },
  ];

  private readonly filtros$ = combineLatest([
    this.busqueda.valueChanges.pipe(startWith(''), debounceTime(300), distinctUntilChanged()),
    this.region.valueChanges.pipe(startWith('')),
  ]);

  protected readonly respuesta = toSignal(
    this.filtros$.pipe(
      switchMap(([busqueda, region]) =>
        this.paisService.listar({ search: busqueda ?? '', region: (region ?? '') as Region | '', ordering: 'nombre' }),
      ),
    ),
    { initialValue: null },
  );

  protected irADetalle(codigoIso: string): void {
    this.router.navigate(['/paises', codigoIso]);
  }
}
