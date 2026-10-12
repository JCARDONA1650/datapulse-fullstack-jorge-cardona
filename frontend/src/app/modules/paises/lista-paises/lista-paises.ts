import { DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { toSignal } from '@angular/core/rxjs-interop';
import { Component, inject, signal } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { Router } from '@angular/router';
import { Subject, combineLatest, startWith } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

import { AuthService } from '../../../core/auth/services/auth.service';
import { PaisService, Region } from '../../../core/services/pais.service';
import { RiesgoService } from '../../../core/services/riesgo.service';

@Component({
  selector: 'app-lista-paises',
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
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
  private readonly riesgoService = inject(RiesgoService);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);
  private readonly recargar$ = new Subject<void>();

  protected readonly columnas = ['codigo_iso', 'nombre', 'region', 'moneda_codigo', 'poblacion'];
  protected readonly busqueda = new FormControl('');
  protected readonly region = new FormControl<Region | ''>('');

  protected readonly sincronizando = signal(false);
  protected readonly recalculando = signal(false);

  protected readonly regiones: { valor: Region; etiqueta: string }[] = [
    { valor: 'ANDINA', etiqueta: 'Andina' },
    { valor: 'CONO_SUR', etiqueta: 'Cono Sur' },
    { valor: 'CENTROAMERICA', etiqueta: 'Centroamerica' },
    { valor: 'CARIBE', etiqueta: 'Caribe' },
  ];

  private readonly filtros$ = combineLatest([
    this.busqueda.valueChanges.pipe(startWith(''), debounceTime(300), distinctUntilChanged()),
    this.region.valueChanges.pipe(startWith('')),
    this.recargar$.pipe(startWith(undefined)),
  ]);

  protected readonly respuesta = toSignal(
    this.filtros$.pipe(
      switchMap(([busqueda, region]) =>
        this.paisService.listar({ search: busqueda ?? '', region: (region ?? '') as Region | '', ordering: 'nombre' }),
      ),
    ),
    { initialValue: null },
  );

  protected esAdmin(): boolean {
    return this.authService.tieneRol(['ADMIN']);
  }

  protected irADetalle(codigoIso: string): void {
    this.router.navigate(['/paises', codigoIso]);
  }

  protected sincronizarIndicadores(): void {
    this.sincronizando.set(true);
    this.paisService.sincronizarIndicadores().subscribe({
      next: (resultado) => {
        this.sincronizando.set(false);
        const partes = [`${resultado.paises_procesados.length} paises actualizados`];
        if (resultado.indicadores_con_error.length > 0) {
          const plural = resultado.indicadores_con_error.length > 1 ? 'es' : '';
          partes.push(`${resultado.indicadores_con_error.length} indicador${plural} con error (${resultado.indicadores_con_error.join(', ')})`);
        }
        this.snackBar.open(`Sincronizacion completa: ${partes.join(', ')}.`, 'Cerrar', { duration: 6000 });
        this.recargar$.next();
      },
      error: (error: HttpErrorResponse) => {
        this.sincronizando.set(false);
        this.snackBar.open(error.error?.mensaje ?? 'No se pudo sincronizar los indicadores.', 'Cerrar', { duration: 5000 });
      },
    });
  }

  protected recalcularRiesgo(): void {
    this.recalculando.set(true);
    this.riesgoService.calcular().subscribe({
      next: (resultados) => {
        this.recalculando.set(false);
        this.snackBar.open(`Riesgo recalculado para ${resultados.length} paises.`, 'Cerrar', { duration: 5000 });
        this.recargar$.next();
      },
      error: (error: HttpErrorResponse) => {
        this.recalculando.set(false);
        this.snackBar.open(error.error?.mensaje ?? 'No se pudo recalcular el riesgo.', 'Cerrar', { duration: 5000 });
      },
    });
  }
}
