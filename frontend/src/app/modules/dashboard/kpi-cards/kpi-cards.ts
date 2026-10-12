import { Component, input } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';

import { ResumenDashboard } from '../../../core/services/dashboard.service';

@Component({
  selector: 'app-kpi-cards',
  imports: [MatCardModule, MatIconModule],
  templateUrl: './kpi-cards.html',
  styleUrl: './kpi-cards.scss',
})
export class KpiCards {
  readonly resumen = input<ResumenDashboard | null>(null);
}
