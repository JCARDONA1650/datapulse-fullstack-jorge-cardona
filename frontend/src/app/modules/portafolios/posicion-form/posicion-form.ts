import { DecimalPipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { toSignal } from '@angular/core/rxjs-interop';
import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';

import { Pais, PaisService } from '../../../core/services/pais.service';
import { DatosPosicion, Posicion, PortafolioService, TipoActivo } from '../../../core/services/portafolio.service';

export interface PosicionFormData {
  portafolioId: number;
  posicion?: Posicion;
  posicionesActivas: Posicion[];
}

const TIPOS_ACTIVO: { valor: TipoActivo; etiqueta: string }[] = [
  { valor: 'RENTA_FIJA', etiqueta: 'Renta fija' },
  { valor: 'RENTA_VARIABLE', etiqueta: 'Renta variable' },
  { valor: 'COMMODITIES', etiqueta: 'Commodities' },
  { valor: 'MONEDA', etiqueta: 'Moneda' },
];

// Deben coincidir con apps/portafolios/services.py para que el frontend detecte
// estas condiciones sin depender de la respuesta del backend.
const MONTO_MAXIMO_PORTAFOLIO = 50_000_000;
const MAXIMO_POSICIONES_ACTIVAS_MISMO_TIPO_PAIS = 2;

function fechaNoFuturaValidator(control: AbstractControl): ValidationErrors | null {
  if (!control.value) {
    return null;
  }
  const hoy = new Date().toISOString().split('T')[0];
  return control.value > hoy ? { fechaFutura: true } : null;
}

function crearValidadorCruzado(
  paises: () => Pais[],
  posicionesActivas: Posicion[],
  posicionIdExcluir?: number,
): ValidatorFn {
  return (group: AbstractControl): ValidationErrors | null => {
    const paisCodigo = group.get('pais')?.value;
    const tipoActivo = group.get('tipo_activo')?.value;
    const monto = Number(group.get('monto_inversion_usd')?.value) || 0;

    const paisSeleccionado = paises().find((pais) => pais.codigo_iso === paisCodigo);
    const activas = posicionesActivas.filter((posicion) => posicion.id !== posicionIdExcluir);

    if (paisSeleccionado && tipoActivo === 'MONEDA' && paisSeleccionado.moneda_codigo === 'USD') {
      return { monedaUsd: true };
    }

    if (paisSeleccionado && tipoActivo) {
      const mismoTipoPais = activas.filter(
        (posicion) => posicion.pais === paisCodigo && posicion.tipo_activo === tipoActivo,
      ).length;
      if (mismoTipoPais >= MAXIMO_POSICIONES_ACTIVAS_MISMO_TIPO_PAIS) {
        return { limitePosiciones: true };
      }
    }

    if (monto > 0) {
      const totalActual = activas.reduce((acumulado, posicion) => acumulado + Number(posicion.monto_inversion_usd), 0);
      if (totalActual + monto > MONTO_MAXIMO_PORTAFOLIO) {
        return { limiteTotal: true };
      }
    }

    return null;
  };
}

@Component({
  selector: 'app-posicion-form',
  imports: [
    DecimalPipe,
    ReactiveFormsModule,
    MatAutocompleteModule,
    MatButtonModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
  ],
  templateUrl: './posicion-form.html',
  styleUrl: './posicion-form.scss',
})
export class PosicionForm {
  private readonly fb = inject(FormBuilder);
  private readonly paisService = inject(PaisService);
  private readonly portafolioService = inject(PortafolioService);
  private readonly dialogRef = inject(MatDialogRef<PosicionForm>);
  protected readonly data = inject<PosicionFormData>(MAT_DIALOG_DATA);

  protected readonly tiposActivo = TIPOS_ACTIVO;
  protected readonly hoy = new Date().toISOString().split('T')[0];
  protected readonly esEdicion = !!this.data?.posicion;
  protected readonly enviando = signal(false);

  protected readonly paises = toSignal(this.paisService.listar({ ordering: 'nombre' }), { initialValue: null });

  protected readonly form = this.fb.nonNullable.group(
    {
      pais: [this.data?.posicion?.pais ?? '', [Validators.required]],
      tipo_activo: [this.data?.posicion?.tipo_activo ?? ('' as TipoActivo), [Validators.required]],
      monto_inversion_usd: [
        this.data?.posicion ? Number(this.data.posicion.monto_inversion_usd) : null,
        [Validators.required, Validators.min(1000), Validators.max(10_000_000)],
      ],
      fecha_entrada: [this.data?.posicion?.fecha_entrada ?? '', [Validators.required, fechaNoFuturaValidator]],
      notas: [this.data?.posicion?.notas ?? '', [Validators.maxLength(200)]],
    },
    {
      validators: crearValidadorCruzado(
        () => this.paises()?.results ?? [],
        this.data?.posicionesActivas ?? [],
        this.data?.posicion?.id,
      ),
    },
  );

  protected mostrarNombrePais = (codigoIso: string): string => {
    return (this.paises()?.results ?? []).find((pais) => pais.codigo_iso === codigoIso)?.nombre ?? codigoIso;
  };

  protected paisesFiltrados(): Pais[] {
    const texto = (this.form.controls.pais.value ?? '').toString().toLowerCase();
    const todos = this.paises()?.results ?? [];
    if (!texto) {
      return todos;
    }
    return todos.filter((pais) => pais.nombre.toLowerCase().includes(texto) || pais.codigo_iso.toLowerCase() === texto);
  }

  protected guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.enviando.set(true);
    const datos = this.form.getRawValue() as DatosPosicion;

    const peticion = this.data?.posicion
      ? this.portafolioService.actualizarPosicion(this.data.portafolioId, this.data.posicion.id, datos)
      : this.portafolioService.crearPosicion(this.data.portafolioId, datos);

    peticion.subscribe({
      next: () => this.dialogRef.close(true),
      error: (error: HttpErrorResponse) => {
        this.enviando.set(false);
        this.aplicarErroresServidor(error);
      },
    });
  }

  protected cancelar(): void {
    this.dialogRef.close(null);
  }

  private aplicarErroresServidor(error: HttpErrorResponse): void {
    const mensaje = error.error?.mensaje;
    if (!mensaje || typeof mensaje !== 'object') {
      return;
    }

    for (const campo of ['pais', 'tipo_activo', 'monto_inversion_usd', 'fecha_entrada', 'notas'] as const) {
      const errorCampo = mensaje[campo];
      if (errorCampo) {
        const texto = Array.isArray(errorCampo) ? errorCampo[0] : errorCampo;
        this.form.get(campo)?.setErrors({ servidor: texto });
      }
    }
  }
}
