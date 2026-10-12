import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { toSignal } from '@angular/core/rxjs-interop';
import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';

import { AuthService } from '../../core/auth/services/auth.service';

@Component({
  selector: 'app-perfil',
  imports: [DatePipe, ReactiveFormsModule, MatButtonModule, MatCardModule, MatFormFieldModule, MatInputModule],
  templateUrl: './perfil.html',
  styleUrl: './perfil.scss',
})
export class Perfil {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly snackBar = inject(MatSnackBar);

  protected readonly guardando = signal(false);
  protected readonly usuario = toSignal(this.authService.usuario$, { initialValue: null });

  protected readonly form = this.fb.nonNullable.group({
    nombre_completo: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(150)]],
  });

  constructor() {
    this.authService.cargarPerfil().subscribe((usuario) => {
      this.form.patchValue({ nombre_completo: usuario.nombre_completo });
    });
  }

  protected guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.guardando.set(true);
    this.authService.actualizarPerfil(this.form.getRawValue()).subscribe({
      next: () => {
        this.guardando.set(false);
        this.snackBar.open('Perfil actualizado.', 'Cerrar', { duration: 3000 });
      },
      error: (error: HttpErrorResponse) => {
        this.guardando.set(false);
        const errorNombre = error.error?.mensaje?.nombre_completo;
        if (errorNombre) {
          this.form.get('nombre_completo')?.setErrors({ servidor: Array.isArray(errorNombre) ? errorNombre[0] : errorNombre });
        }
      },
    });
  }
}
