import { AsyncPipe } from '@angular/common';
import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { AuthService } from './core/auth/services/auth.service';
import { LoadingSpinner } from './shared/loading-spinner/loading-spinner';
import { Navbar } from './shared/navbar/navbar';

@Component({
  selector: 'app-root',
  imports: [AsyncPipe, RouterOutlet, LoadingSpinner, Navbar],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly authService = inject(AuthService);

  protected readonly usuario$ = this.authService.usuario$;

  constructor() {
    if (this.authService.estaAutenticado()) {
      this.authService.cargarPerfil().subscribe();
    }
  }
}
