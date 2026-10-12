import { DecimalPipe } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { Component, inject } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

import { PaisService } from '../../../core/services/pais.service';
import { Posicion, TipoActivo } from '../../../core/services/portafolio.service';

export interface PosicionFormData {
  posicion?: Posicion;
}

const TIPOS_ACTIVO: { valor: TipoActivo; etiqueta: string }[] = [
  { valor: 'RENTA_FIJA', etiqueta: 'Renta fija' },
  { valor: 'RENTA_VARIABLE', etiqueta: 'Renta variable' },
  { valor: 'COMMODITIES', etiqueta: 'Commodities' },
  { valor: 'MONEDA', etiqueta: 'Moneda' },
];

@Component({
  selector: 'app-posicion-form',
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
  ],
  templateUrl: './posicion-form.html',
  styleUrl: './posicion-form.scss',
})
export class PosicionForm {
  private readonly fb = inject(FormBuilder);
  private readonly paisService = inject(PaisService);
  private readonly dialogRef = inject(MatDialogRef<PosicionForm>);
  protected readonly data = inject<PosicionFormData>(MAT_DIALOG_DATA);

  protected readonly tiposActivo = TIPOS_ACTIVO;
  protected readonly hoy = new Date().toISOString().split('T')[0];
  protected readonly esEdicion = !!this.data?.posicion;

  protected readonly paises = toSignal(this.paisService.listar({ ordering: 'nombre' }), { initialValue: null });

  protected readonly form = this.fb.nonNullable.group({
    pais: [this.data?.posicion?.pais ?? '', [Validators.required]],
    tipo_activo: [this.data?.posicion?.tipo_activo ?? ('' as TipoActivo), [Validators.required]],
    monto_inversion_usd: [
      this.data?.posicion ? Number(this.data.posicion.monto_inversion_usd) : null,
      [Validators.required, Validators.min(1000), Validators.max(10_000_000)],
    ],
    fecha_entrada: [this.data?.posicion?.fecha_entrada ?? '', [Validators.required]],
    notas: [this.data?.posicion?.notas ?? '', [Validators.maxLength(200)]],
  });

  protected guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    this.dialogRef.close(this.form.getRawValue());
  }

  protected cancelar(): void {
    this.dialogRef.close(null);
  }
}
