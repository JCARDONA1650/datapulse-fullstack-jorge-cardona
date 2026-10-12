import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { AbstractControl, AsyncValidatorFn, FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ActivatedRoute, Router } from '@angular/router';
import { catchError, map, of } from 'rxjs';

import { PortafolioService } from '../../../core/services/portafolio.service';

@Component({
  selector: 'app-crear',
  imports: [ReactiveFormsModule, MatButtonModule, MatCardModule, MatCheckboxModule, MatFormFieldModule, MatInputModule],
  templateUrl: './crear.html',
  styleUrl: './crear.scss',
})
export class Crear {
  private readonly fb = inject(FormBuilder);
  private readonly portafolioService = inject(PortafolioService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);

  protected readonly enviando = signal(false);
  private readonly idActual = Number(this.route.snapshot.paramMap.get('id')) || null;
  protected readonly esEdicion = this.idActual !== null;
  private fechaModificacion: string | null = null;

  protected readonly form = this.fb.nonNullable.group({
    nombre: this.fb.nonNullable.control('', {
      validators: [Validators.required, Validators.minLength(3), Validators.maxLength(100)],
      asyncValidators: [this.nombreUnicoValidator()],
      updateOn: 'blur',
    }),
    descripcion: ['', [Validators.maxLength(500)]],
    es_publico: [false],
  });

  constructor() {
    if (this.idActual) {
      this.portafolioService.obtener(this.idActual).subscribe((portafolio) => {
        this.fechaModificacion = portafolio.fecha_modificacion;
        this.form.patchValue({
          nombre: portafolio.nombre,
          descripcion: portafolio.descripcion,
          es_publico: portafolio.es_publico,
        });
      });
    }
  }

  protected contadorDescripcion(): number {
    return (this.form.controls.descripcion.value ?? '').length;
  }

  protected enviar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.enviando.set(true);
    const datos = this.form.getRawValue();

    const peticion = this.idActual
      ? this.portafolioService.actualizar(this.idActual, {
          ...datos,
          fecha_modificacion: this.fechaModificacion ?? undefined,
        })
      : this.portafolioService.crear(datos);

    peticion.subscribe({
      next: () => {
        this.snackBar.open(this.esEdicion ? 'Portafolio actualizado.' : 'Portafolio creado.', 'Cerrar', { duration: 3000 });
        this.router.navigate(['/portafolios']);
      },
      error: (error: HttpErrorResponse) => {
        this.enviando.set(false);
        const errorNombre = error.error?.mensaje?.nombre;
        if (error.status === 400 && errorNombre) {
          this.form.get('nombre')?.setErrors({ servidor: Array.isArray(errorNombre) ? errorNombre[0] : errorNombre });
        }
      },
    });
  }

  private nombreUnicoValidator(): AsyncValidatorFn {
    return (control: AbstractControl) => {
      const nombre = (control.value ?? '').trim();
      if (nombre.length < 3) {
        return of(null);
      }

      return this.portafolioService.listar({ search: nombre }).pipe(
        map((respuesta) => {
          const duplicado = respuesta.results.some(
            (p) => p.es_propio && p.nombre.toLowerCase() === nombre.toLowerCase() && p.id !== this.idActual,
          );
          return duplicado ? { nombreDuplicado: true } : null;
        }),
        catchError(() => of(null)),
      );
    };
  }
}
