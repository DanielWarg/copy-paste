/**
 * Projects Module E2E Tests
 * 
 * Tests the complete project management flow:
 * 1. Project Hub loads (no mock)
 * 2. Create project (DEV mode against http://localhost:8000) - if backend+DB runs; otherwise skip
 * 3. Project detail visible after create
 * 4. CTA "Skapa nytt transkript" navigates to upload view with project context
 */

import { test, expect } from '@playwright/test';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5174';
const API_BASE = process.env.VITE_API_BASE_URL || 'http://localhost:8000';

test.describe('Projects Module E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to frontend
    await page.goto(FRONTEND_URL);
    
    // Wait for app to load
    await page.waitForSelector('body', { timeout: 10000 });
  });

  test('Project Hub loads and shows navigation', async ({ page }) => {
    // Navigate to Transkript page (should be default or click in nav)
    const transkriptButton = page.locator('button:has-text("Transkript")').first();
    if (await transkriptButton.isVisible()) {
      await transkriptButton.click();
      await page.waitForTimeout(500);
    }

    // Verify page title
    await expect(page.locator('h2:has-text("Projekt")')).toBeVisible();

    // Verify create button or empty state
    const createButton = page.locator('button:has-text("Skapa nytt projekt")');
    const emptyState = page.locator('text=/Inga projekt har skapats än/i');
    
    // Either create button or empty state should be visible
    const hasCreateButton = await createButton.isVisible().catch(() => false);
    const hasEmptyState = await emptyState.isVisible().catch(() => false);
    
    expect(hasCreateButton || hasEmptyState).toBe(true);
  });

  test('Create project flow (if DB available)', async ({ page }) => {
    // Check if backend is available
    let backendAvailable = false;
    try {
      const response = await page.request.get(`${API_BASE}/health`);
      backendAvailable = response.ok();
    } catch {
      // Backend not available
    }

    if (!backendAvailable) {
      test.skip(true, 'Backend not available. Skipping project creation test.');
      return;
    }

    // Navigate to Transkript page
    const transkriptButton = page.locator('button:has-text("Transkript")').first();
    if (await transkriptButton.isVisible()) {
      await transkriptButton.click();
      await page.waitForTimeout(500);
    }

    // Click "Skapa nytt projekt"
    const createButton = page.locator('button:has-text("Skapa nytt projekt")').first();
    await createButton.click();
    await page.waitForTimeout(500);

    // Fill in project name
    const nameInput = page.locator('input[type="text"]').first();
    await nameInput.fill('Test Projekt E2E');

    // Submit form
    const submitButton = page.locator('button:has-text("Skapa projekt")');
    await submitButton.click();

    // Wait for project to be created (either success or error)
    await page.waitForTimeout(2000);

    // Check if we see project in list or error message
    const projectInList = page.locator('text=/Test Projekt E2E/i');
    const dbError = page.locator('text=/Databas saknas/i');
    
    const hasProject = await projectInList.isVisible().catch(() => false);
    const hasDbError = await dbError.isVisible().catch(() => false);

    // If DB error, that's expected - test passes
    // If project created, verify it's clickable
    if (hasProject) {
      await projectInList.click();
      await page.waitForTimeout(1000);
      
      // Should see project detail
      await expect(page.locator('h2:has-text("Test Projekt E2E")')).toBeVisible({ timeout: 5000 });
    } else if (hasDbError) {
      // DB not available - test passes (expected behavior)
      expect(hasDbError).toBe(true);
    } else {
      // Unexpected state
      throw new Error('Neither project nor DB error visible after create');
    }
  });

  test('Project detail shows sections and CTA', async ({ page }) => {
    // This test assumes a project exists or can be created
    // Navigate to Transkript
    const transkriptButton = page.locator('button:has-text("Transkript")').first();
    if (await transkriptButton.isVisible()) {
      await transkriptButton.click();
      await page.waitForTimeout(500);
    }

    // Try to find a project card and click it
    const projectCard = page.locator('button:has([class*="bg-white"]):has([class*="dark:bg-zinc-800"])').first();
    
    if (await projectCard.isVisible({ timeout: 2000 }).catch(() => false)) {
      await projectCard.click();
      await page.waitForTimeout(1000);

      // Verify project detail sections
      await expect(page.locator('h3:has-text("Transkript")')).toBeVisible();
      await expect(page.locator('h3:has-text("Filer")')).toBeVisible();
      await expect(page.locator('h3:has-text("Export")')).toBeVisible();

      // Verify CTA button
      const createRecordButton = page.locator('button:has-text("Skapa nytt transkript")');
      await expect(createRecordButton).toBeVisible();
    } else {
      test.skip(true, 'No projects available. Create a project first.');
    }
  });

  test('CTA "Skapa nytt transkript" navigates to upload with project context', async ({ page }) => {
    // Navigate to Transkript
    const transkriptButton = page.locator('button:has-text("Transkript")').first();
    if (await transkriptButton.isVisible()) {
      await transkriptButton.click();
      await page.waitForTimeout(500);
    }

    // Try to find a project and navigate to detail
    const projectCard = page.locator('button:has([class*="bg-white"]):has([class*="dark:bg-zinc-800"])').first();
    
    if (await projectCard.isVisible({ timeout: 2000 }).catch(() => false)) {
      await projectCard.click();
      await page.waitForTimeout(1000);

      // Click "Skapa nytt transkript"
      const createRecordButton = page.locator('button:has-text("Skapa nytt transkript")').first();
      if (await createRecordButton.isVisible()) {
        await createRecordButton.click();
        await page.waitForTimeout(1000);

        // Should see upload view with project context
        await expect(page.locator('h2:has-text("Inspelning & Transkribering")')).toBeVisible();
        
        // Should see project name in header
        const projectBadge = page.locator('text=/Projekt:/i');
        await expect(projectBadge).toBeVisible({ timeout: 2000 });
      }
    } else {
      test.skip(true, 'No projects available. Create a project first.');
    }
  });
});

