import { expect, test } from '@playwright/test';

test.describe('Login', () => {
  test('redirige a login si se intenta acceder sin autenticacion', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page).toHaveURL(/\/login/);
  });

  test('login con credenciales validas redirige al dashboard', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('analista@datapulse.com');
    await page.locator('input[formcontrolname="password"]').fill('DataPulse2026!');
    await page.getByRole('button', { name: 'Ingresar' }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByText('Ranking de paises por IRPC')).toBeVisible();
  });

  test('login con credenciales invalidas muestra un mensaje de error', async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('analista@datapulse.com');
    await page.locator('input[formcontrolname="password"]').fill('contrasena-incorrecta');
    await page.getByRole('button', { name: 'Ingresar' }).click();

    await expect(page.getByText(/incorrect/i)).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
  });
});
