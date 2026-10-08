import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class LoadingService {
  private contador = 0;
  private readonly cargandoSubject = new BehaviorSubject<boolean>(false);
  readonly cargando$ = this.cargandoSubject.asObservable();

  iniciar(): void {
    this.contador++;
    this.cargandoSubject.next(true);
  }

  finalizar(): void {
    this.contador = Math.max(0, this.contador - 1);
    this.cargandoSubject.next(this.contador > 0);
  }
}
