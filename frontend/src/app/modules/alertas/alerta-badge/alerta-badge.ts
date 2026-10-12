import { toSignal } from '@angular/core/rxjs-interop';
import { Component, computed, inject } from '@angular/core';
import { MatBadgeModule } from '@angular/material/badge';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Router } from '@angular/router';
import { interval, startWith, switchMap } from 'rxjs';

import { AlertaService } from '../../../core/services/alerta.service';

const INTERVALO_POLLING_MS = 30000;

@Component({
  selector: 'app-alerta-badge',
  imports: [MatBadgeModule, MatButtonModule, MatIconModule],
  templateUrl: './alerta-badge.html',
  styleUrl: './alerta-badge.scss',
})
export class AlertaBadge {
  private readonly alertaService = inject(AlertaService);
  private readonly router = inject(Router);

  private readonly resumen = toSignal(
    interval(INTERVALO_POLLING_MS).pipe(
      startWith(0),
      switchMap(() => this.alertaService.resumen()),
    ),
    { initialValue: null },
  );

  protected readonly noLeidas = computed(() => this.resumen()?.no_leidas ?? 0);

  protected irAAlertas(): void {
    this.router.navigate(['/alertas']);
  }
}
