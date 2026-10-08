import { toSignal } from '@angular/core/rxjs-interop';
import { Component, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { Subject, combineLatest, startWith } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';

import { AuthService } from '../../../core/auth/services/auth.service';
import { Portafolio, PortafolioService } from '../../../core/services/portafolio.service';
import { ConfirmDialog } from '../../../shared/confirm-dialog/confirm-dialog';

@Component({
  selector: 'app-lista',
  imports: [
    ReactiveFormsModule,
    MatButtonModule,
    MatCardModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './lista.html',
  styleUrl: './lista.scss',
})
export class Lista {
  private readonly portafolioService = inject(PortafolioService);
  private readonly authService = inject(AuthService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly router = inject(Router);
  private readonly recargar$ = new Subject<void>();

  protected readonly busqueda = new FormControl('');

  private readonly filtros$ = combineLatest([
    this.busqueda.valueChanges.pipe(startWith(''), debounceTime(300), distinctUntilChanged()),
    this.recargar$.pipe(startWith(undefined)),
  ]);

  protected readonly respuesta = toSignal(
    this.filtros$.pipe(switchMap(([busqueda]) => this.portafolioService.listar({ search: busqueda ?? '' }))),
    { initialValue: null },
  );

  protected puedeGestionar(): boolean {
    return !this.authService.tieneRol(['VIEWER']);
  }

  protected irACrear(): void {
    this.router.navigate(['/portafolios/crear']);
  }

  protected irAEditar(portafolio: Portafolio): void {
    this.router.navigate(['/portafolios', portafolio.id, 'editar']);
  }

  protected irADetalle(portafolio: Portafolio): void {
    this.router.navigate(['/portafolios', portafolio.id]);
  }

  protected eliminar(portafolio: Portafolio): void {
    const ref = this.dialog.open(ConfirmDialog, {
      data: {
        titulo: 'Eliminar portafolio',
        mensaje: `¿Seguro que deseas eliminar "${portafolio.nombre}"? Esta accion no se puede deshacer.`,
      },
    });

    ref.afterClosed().subscribe((confirmado) => {
      if (confirmado) {
        this.portafolioService.eliminar(portafolio.id).subscribe(() => {
          this.snackBar.open('Portafolio eliminado.', 'Cerrar', { duration: 3000 });
          this.recargar$.next();
        });
      }
    });
  }
}
