/**
 * Foundation E2E Test
 * 
 * Baseline test: App loads, shows shell, shows backend status.
 * 
 * This test verifies:
 * - UI Shell renders correctly
 * - Navigation is visible
 * - Backend status indicator is present
 * - Dark mode toggle works
 */

import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173';

test.describe('Foundation - UI Shell', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to frontend
    await page.goto(FRONTEND_URL);
    
    // Wait for app to load
    await page.waitForSelector('body', { timeout: 10000 });
  });

  test('App loads and shows shell', async ({ page }) => {
    // Check that main layout container exists
    const layout = page.locator('div.flex.h-screen');
    await expect(layout).toBeVisible();

    // Check sidebar is visible (on desktop)
    const sidebar = page.locator('aside.hidden.md\\:flex');
    await expect(sidebar).toBeVisible();

    // Check app name in sidebar header
    await expect(page.locator('text=REDAKTIONELLT STÖD')).toBeVisible();

    // Check status indicator (red pulse dot)
    const statusDot = page.locator('div.w-2.h-2.bg-red-600.rounded-full.animate-pulse');
    await expect(statusDot).toBeVisible();
  });

  test('Navigation menu is visible', async ({ page }) => {
    // Check "Produktion" section label
    await expect(page.locator('text=Produktion')).toBeVisible();

    // Check "Bibliotek & Data" section label
    await expect(page.locator('text=Bibliotek & Data')).toBeVisible();

    // Check navigation items exist
    await expect(page.locator('button:has-text("Översikt")')).toBeVisible();
    await expect(page.locator('button:has-text("Bevakning")')).toBeVisible();
    await expect(page.locator('button:has-text("Arbetsflöde")')).toBeVisible();
    await expect(page.locator('button:has-text("Inspelning")')).toBeVisible();
    await expect(page.locator('button:has-text("Transkriptioner")')).toBeVisible();
    await expect(page.locator('button:has-text("Källor")')).toBeVisible();
  });

  test('Header is visible with date and theme toggle', async ({ page }) => {
    // Check header exists
    const header = page.locator('header.h-14');
    await expect(header).toBeVisible();

    // Check date is displayed (Swedish format)
    const dateText = page.locator('div.text-sm.font-medium');
    await expect(dateText).toBeVisible();

    // Check theme toggle button exists
    const themeButton = page.locator('button').filter({ has: page.locator('svg') }).last();
    await expect(themeButton).toBeVisible();
  });

  test('Backend status indicator is visible', async ({ page }) => {
    // Backend status should be in header
    // It might show "Kontrollerar backend..." or "Backend ansluten" or "Backend otillgänglig"
    const statusText = page.locator('text=/Backend|Kontrollerar|mTLS/');
    await expect(statusText).toBeVisible({ timeout: 5000 });
  });

  test('Default page shows placeholder content', async ({ page }) => {
    // Default page is 'recorder'
    // Should show placeholder text
    await expect(page.locator('text=Inspelning')).toBeVisible();
    await expect(page.locator('text=/Kommer snart|Foundation phase/')).toBeVisible();
  });

  test('Navigation works', async ({ page }) => {
    // Click on "Transkriptioner"
    await page.locator('button:has-text("Transkriptioner")').click();
    
    // Wait for navigation
    await page.waitForTimeout(500);
    
    // Should show transcripts placeholder
    await expect(page.locator('text=Transkriptioner')).toBeVisible();
  });

  test('Theme toggle works', async ({ page }) => {
    // Check initial state (dark mode by default)
    const html = page.locator('html');
    await expect(html).toHaveClass(/dark/);

    // Click theme toggle
    const themeButton = page.locator('button').filter({ has: page.locator('svg') }).last();
    await themeButton.click();
    
    // Wait for theme change
    await page.waitForTimeout(200);
    
    // HTML should not have 'dark' class (light mode)
    await expect(html).not.toHaveClass(/dark/);
  });
});


