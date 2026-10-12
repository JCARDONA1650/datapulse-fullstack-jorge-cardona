import { DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { toSignal } from '@angular/core/rxjs-interop';
import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialog } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTableModule } from '@angular/material/table';
import { ActivatedRoute } from '@angular/router';
import { Subject, startWith, switchMap } from 'rxjs';

import { AuthService } from '../../../core/auth/services/auth.service';
import { DatosPosicion, Posicion, PortafolioService } from '../../../core/services/portafolio.service';
import { ConfirmDialog } from '../../../shared/confirm-dialog/confirm-dialog';
import { DistribucionChart } from '../distribucion-chart/distribucion-chart';
import { PosicionForm } from '../posicion-form/posicion-form';

@Component({
  selector: 'app-detalle',
  imports: [
    DecimalPipe,
    MatButtonModule,
    MatCardModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatTableModule,
    DistribucionChart,
  ],
  templateUrl: './detalle.html',
  styleUrl: './detalle.scss',
})
export class Detalle {
  private readonly route = inject(ActivatedRoute);
  private readonly portafolioService = inject(PortafolioService);
  private readonly authService = inject(AuthService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly recargar$ = new Subject<void>();

  protected readonly columnasPosiciones = [
    'pais_nombre', 'tipo_activo', 'monto_inversion_usd', 'fecha_entrada', 'fecha_salida', 'acciones',
  ];

  private readonly portafolioId = Number(this.route.snapshot.paramMap.get('id'));

  protected readonly portafolio = toSignal(
    this.recargar$.pipe(startWith(undefined), switchMap(() => this.portafolioService.obtener(this.portafolioId))),
    { initialValue: null },
  );

  protected readonly resumen = toSignal(
    this.recargar$.pipe(startWith(undefined), switchMap(() => this.portafolioService.resumen(this.portafolioId))),
    { initialValue: null },
  );

  protected puedeGestionar(): boolean {
    const portafolio = this.portafolio();
    if (!portafolio || this.authService.tieneRol(['VIEWER'])) {
      return false;
    }
    return portafolio.es_propio || this.authService.tieneRol(['ADMIN']);
  }

  protected agregarPosicion(): void {
    const ref = this.dialog.open(PosicionForm, { data: {} });
    ref.afterClosed().subscribe((datos: DatosPosicion | null) => {
      if (datos) {
        this.portafolioService.crearPosicion(this.portafolioId, datos).subscribe({
          next: () => {
            this.snackBar.open('Posicion agregada.', 'Cerrar', { duration: 3000 });
            this.recargar$.next();
          },
          error: (error: HttpErrorResponse) => this.mostrarErrorValidacion(error),
        });
      }
    });
  }

  protected editarPosicion(posicion: Posicion): void {
    const ref = this.dialog.open(PosicionForm, { data: { posicion } });
    ref.afterClosed().subscribe((datos: DatosPosicion | null) => {
      if (datos) {
        this.portafolioService.actualizarPosicion(this.portafolioId, posicion.id, datos).subscribe({
          next: () => {
            this.snackBar.open('Posicion actualizada.', 'Cerrar', { duration: 3000 });
            this.recargar$.next();
          },
          error: (error: HttpErrorResponse) => this.mostrarErrorValidacion(error),
        });
      }
    });
  }

  protected cerrarPosicion(posicion: Posicion): void {
    const ref = this.dialog.open(ConfirmDialog, {
      data: {
        titulo: 'Cerrar posicion',
        mensaje: `Se cerrara la posicion en ${posicion.pais_nombre}. Esta accion no se puede deshacer.`,
        textoConfirmar: 'Cerrar posicion',
      },
    });

    ref.afterClosed().subscribe((confirmado) => {
      if (confirmado) {
        this.portafolioService.cerrarPosicion(this.portafolioId, posicion.id).subscribe(() => {
          this.snackBar.open('Posicion cerrada.', 'Cerrar', { duration: 3000 });
          this.recargar$.next();
        });
      }
    });
  }

  protected exportarPdf(): void {
    this.portafolioService.exportarPdf(this.portafolioId).subscribe((blob) => {
      const url = window.URL.createObjectURL(blob);
      const enlace = document.createElement('a');
      enlace.href = url;
      enlace.download = `portafolio_${this.portafolioId}.pdf`;
      enlace.click();
      window.URL.revokeObjectURL(url);
    });
  }

  private mostrarErrorValidacion(error: HttpErrorResponse): void {
    const mensaje = error.error?.mensaje;
    if (mensaje && typeof mensaje === 'object') {
      const primerError = Object.values(mensaje)[0];
      this.snackBar.open(Array.isArray(primerError) ? primerError[0] : String(primerError), 'Cerrar', { duration: 5000 });
    }
  }
}
