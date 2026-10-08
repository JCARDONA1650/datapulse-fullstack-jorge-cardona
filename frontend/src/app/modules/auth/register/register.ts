import { HttpErrorResponse } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router, RouterLink } from '@angular/router';

import { AuthService } from '../../../core/auth/services/auth.service';

function passwordsCoincidenValidator(control: AbstractControl): ValidationErrors | null {
  const password = control.get('password')?.value;
  const password2 = control.get('password2')?.value;
  return password && password2 && password !== password2 ? { passwordsNoCoinciden: true } : null;
}

@Component({
  selector: 'app-register',
  imports: [ReactiveFormsModule, RouterLink, MatButtonModule, MatCardModule, MatFormFieldModule, MatInputModule],
  templateUrl: './register.html',
  styleUrl: './register.scss',
})
export class Register {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);
  private readonly snackBar = inject(MatSnackBar);

  protected readonly enviando = signal(false);

  protected readonly form = this.fb.nonNullable.group(
    {
      email: ['', [Validators.required, Validators.email]],
      nombre_completo: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(150)]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      password2: ['', [Validators.required]],
    },
    { validators: passwordsCoincidenValidator },
  );

  protected enviar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.enviando.set(true);

    this.authService.registrar(this.form.getRawValue()).subscribe({
      next: () => {
        this.snackBar.open('Cuenta creada. Ahora puedes iniciar sesion.', 'Cerrar', { duration: 4000 });
        this.router.navigate(['/login']);
      },
      error: (error: HttpErrorResponse) => {
        this.enviando.set(false);
        this.aplicarErroresServidor(error);
      },
    });
  }

  private aplicarErroresServidor(error: HttpErrorResponse): void {
    const mensaje = error.error?.mensaje;
    if (!mensaje || typeof mensaje !== 'object') {
      return;
    }

    for (const campo of ['email', 'nombre_completo', 'password', 'password2'] as const) {
      const errorCampo = mensaje[campo];
      if (errorCampo) {
        const texto = Array.isArray(errorCampo) ? errorCampo[0] : errorCampo;
        this.form.get(campo)?.setErrors({ servidor: texto });
      }
    }
  }
}
