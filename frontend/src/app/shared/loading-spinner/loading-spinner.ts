import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { LoadingService } from '../../core/services/loading.service';

@Component({
  selector: 'app-loading-spinner',
  imports: [MatProgressBarModule],
  templateUrl: './loading-spinner.html',
  styleUrl: './loading-spinner.scss',
})
export class LoadingSpinner {
  private readonly loadingService = inject(LoadingService);
  protected readonly cargando = toSignal(this.loadingService.cargando$, { initialValue: false });
}
