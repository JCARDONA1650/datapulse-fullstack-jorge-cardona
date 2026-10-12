import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { Login } from './login';

describe('Login', () => {
  let fixture: ComponentFixture<Login>;
  let component: Login;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Login],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(Login);
    component = fixture.componentInstance;
  });

  it('se crea correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('el formulario es invalido vacio', () => {
    expect(component['form'].invalid).toBeTrue();
  });

  it('requiere un email con formato valido', () => {
    const email = component['form'].controls.email;
    email.setValue('no-es-un-email');
    expect(email.hasError('email')).toBeTrue();

    email.setValue('analista@datapulse.com');
    expect(email.valid).toBeTrue();
  });

  it('requiere contraseña de al menos 8 caracteres', () => {
    const password = component['form'].controls.password;
    password.setValue('1234567');
    expect(password.hasError('minlength')).toBeTrue();

    password.setValue('12345678');
    expect(password.hasError('minlength')).toBeFalse();
  });

  it('no envia la peticion si el formulario es invalido', () => {
    component['enviar']();
    expect(component['enviando']()).toBeFalse();
  });
});
