import { DatePipe } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { Component, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { Subject, combineLatest, startWith } from 'rxjs';
import { switchMap } from 'rxjs/operators';

import { Alerta, AlertaService, SeveridadAlerta, TipoAlerta } from '../../../core/services/alerta.service';

const ICONO_POR_SEVERIDAD: Record<SeveridadAlerta, string> = {
  INFO: 'info',
  WARNING: 'warning',
  CRITICAL: 'error',
};

const COLOR_POR_SEVERIDAD: Record<SeveridadAlerta, string> = {
  INFO: '#3b82f6',
  WARNING: '#eab308',
  CRITICAL: '#ef4444',
};

@Component({
  selector: 'app-panel-alertas',
  imports: [
    DatePipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSelectModule,
  ],
  templateUrl: './panel-alertas.html',
  styleUrl: './panel-alertas.scss',
})
export class PanelAlertas {
  private readonly alertaService = inject(AlertaService);
  private readonly recargar$ = new Subject<void>();

  protected readonly iconoPorSeveridad = ICONO_POR_SEVERIDAD;
  protected readonly colorPorSeveridad = COLOR_POR_SEVERIDAD;

  protected readonly tipoAlerta = new FormControl<TipoAlerta | ''>('');
  protected readonly severidad = new FormControl<SeveridadAlerta | ''>('');
  protected readonly leida = new FormControl<'' | 'true' | 'false'>('');

  private readonly filtros$ = combineLatest([
    this.tipoAlerta.valueChanges.pipe(startWith('')),
    this.severidad.valueChanges.pipe(startWith('')),
    this.leida.valueChanges.pipe(startWith('')),
    this.recargar$.pipe(startWith(undefined)),
  ]);

  protected readonly respuesta = toSignal(
    this.filtros$.pipe(
      switchMap(([tipoAlerta, severidad, leida]) =>
        this.alertaService.listar({
          tipo_alerta: (tipoAlerta ?? '') as TipoAlerta | '',
          severidad: (severidad ?? '') as SeveridadAlerta | '',
          leida: (leida ?? '') as '' | 'true' | 'false',
        }),
      ),
    ),
    { initialValue: null },
  );

  protected marcarLeida(alerta: Alerta): void {
    this.alertaService.marcarLeida(alerta.id).subscribe(() => this.recargar$.next());
  }

  protected marcarTodasLeidas(): void {
    this.alertaService.marcarTodasLeidas().subscribe(() => this.recargar$.next());
  }
}
