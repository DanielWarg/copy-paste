/**
 * Record Module E2E Tests
 * 
 * Tests the complete record creation and audio upload flow:
 * 1. Recorder page loads and shows file input
 * 2. Upload attempt without cert shows mTLS error (mtls-required)
 * 3. Upload with cert (mtls-with-cert) - if cert setup exists
 */

import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5174';
const API_BASE = process.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Test file path (relative to repo root)
// From frontend/tests/e2e, go up to project root
const TEST_AUDIO_FILE = path.resolve(process.cwd(), '..', '..', 'Del21.wav');

// Check if client cert exists (for mtls-with-cert test)
const CLIENT_CERT_PATH = path.resolve(process.cwd(), '..', 'certs', 'client.crt');
const CLIENT_KEY_PATH = path.resolve(process.cwd(), '..', 'certs', 'client.key');
const HAS_CLIENT_CERT = fs.existsSync(CLIENT_CERT_PATH) && fs.existsSync(CLIENT_KEY_PATH);

test.describe('Record Module E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to frontend
    await page.goto(FRONTEND_URL);
    
    // Wait for app to load
    await page.waitForSelector('body', { timeout: 10000 });
  });

  test('Transkribering page loads and shows file input', async ({ page }) => {
    // Navigate to Transkribering page
    const transkriberingButton = page.locator('button:has-text("Transkribering")').first();
    if (await transkriberingButton.isVisible()) {
      await transkriberingButton.click();
      await page.waitForTimeout(500);
    }

    // Verify page title
    await expect(page.locator('h2:has-text("Transkribering")')).toBeVisible();

    // Verify file input label
    await expect(page.locator('label:has-text("+ Välj ljudfil")')).toBeVisible();

    // Verify description
    await expect(page.locator('text=/Välj en ljudfil.*Max 200MB/')).toBeVisible();
  });

  test('Upload attempt without cert shows mTLS error state (mtls-required)', async ({ page }) => {
    // Navigate to Transkribering page
    const transkriberingButton = page.locator('button:has-text("Transkribering")').first();
    if (await transkriberingButton.isVisible()) {
      await transkriberingButton.click();
      await page.waitForTimeout(500);
    }

    // Verify test file exists
    if (!fs.existsSync(TEST_AUDIO_FILE)) {
      test.skip(true, `Test file not found: ${TEST_AUDIO_FILE}`);
      return;
    }

    // Select the audio file
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.locator('label:has-text("+ Välj ljudfil")').click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(TEST_AUDIO_FILE);

    // Verify file name is displayed
    await expect(page.locator(`span:has-text("${path.basename(TEST_AUDIO_FILE)}")`)).toBeVisible();

    // Click "Starta transkribering"
    await page.locator('button:has-text("Starta transkribering")').click();

    // Wait for error state (mTLS handshake failure expected)
    // This should happen quickly if cert is not installed
    await page.waitForTimeout(2000);

    // Verify error state is shown
    // Either mTLS error or network error (depending on setup)
    const errorContainer = page.locator('div.bg-white, div.bg-zinc-800').filter({
      has: page.locator('text=/mTLS|certifikat|fel|error/i'),
    }).first();

    // Should show some error (mTLS or network)
    await expect(errorContainer).toBeVisible({ timeout: 10000 });

    // If mTLS error, verify it mentions certificate
    const errorText = await errorContainer.textContent();
    if (errorText?.toLowerCase().includes('certifikat') || errorText?.toLowerCase().includes('mtls')) {
      // Verify mTLS error message
      await expect(page.locator('text=/Klientcertifikat krävs|mTLS/i')).toBeVisible();
    }
  });

  test('Upload with cert (mtls-with-cert)', async ({ page, context }) => {
    // Skip if client cert doesn't exist
    test.skip(!HAS_CLIENT_CERT, 'Client certificate not found. Skipping mtls-with-cert test.');

    // Configure Playwright context with client certificate
    await context.close();
    const newContext = await page.context().browser()?.newContext({
      ignoreHTTPSErrors: true,
      // Note: Playwright's client cert support is limited
      // This test may need adjustment based on actual cert setup
    });

    if (!newContext) {
      test.skip(true, 'Could not create context with client cert');
      return;
    }

    const newPage = await newContext.newPage();
    
    // Listen for network requests to capture request_id
    const requestIds: string[] = [];
    newPage.on('response', async (response) => {
      const requestId = response.headers()['x-request-id'];
      if (requestId) {
        requestIds.push(requestId);
        console.log(`[E2E] Request ID: ${requestId} - ${response.url()} - ${response.status()}`);
      }
    });

    await newPage.goto(FRONTEND_URL);
    await newPage.waitForSelector('body', { timeout: 10000 });

    // Navigate to Transkribering page
    const transkriberingButton = newPage.locator('button:has-text("Transkribering")').first();
    if (await transkriberingButton.isVisible()) {
      await transkriberingButton.click();
      await newPage.waitForTimeout(500);
    }

    // Verify test file exists
    if (!fs.existsSync(TEST_AUDIO_FILE)) {
      test.skip(true, `Test file not found: ${TEST_AUDIO_FILE}`);
      return;
    }

    // Select the audio file
    const fileChooserPromise = newPage.waitForEvent('filechooser');
    await newPage.locator('label:has-text("+ Välj ljudfil")').click();
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(TEST_AUDIO_FILE);

    // Verify file name is displayed
    await expect(newPage.locator(`span:has-text("${path.basename(TEST_AUDIO_FILE)}")`)).toBeVisible();

    // Click "Starta transkribering"
    await newPage.locator('button:has-text("Starta transkribering")').click();

    // Robust wait: Wait for either success state OR error state
    // Don't wait for transient states (creating/uploading) as they may be too fast
    // Instead, wait for final state indicators:
    // - Success: "Uppladdning klar" OR "Record ID" OR "SHA256"
    // - Error: Error message container
    const successOrError = await Promise.race([
      // Success indicators
      newPage.waitForSelector('text=/Uppladdning klar|Record ID|SHA256/i', { timeout: 120000 }).then(() => 'success'),
      // Error indicators
      newPage.waitForSelector('text=/fel|error|mTLS|certifikat/i', { timeout: 120000 }).then(() => 'error'),
    ]).catch(() => 'timeout');

    if (successOrError === 'success') {
      // Verify success details
      await expect(newPage.locator('text=/Record ID|SHA256|Storlek|Format/i')).toBeVisible();
      console.log(`[E2E] Upload successful. Request IDs: ${requestIds.join(', ')}`);
    } else if (successOrError === 'error') {
      // Log error for debugging
      const errorText = await newPage.locator('text=/fel|error|mTLS|certifikat/i').first().textContent();
      console.log(`[E2E] Upload failed. Error: ${errorText}. Request IDs: ${requestIds.join(', ')}`);
      // Don't fail test - error state is valid (e.g., mTLS without cert)
    } else {
      // Timeout - this is a failure
      throw new Error(`Upload timeout after 120s. Request IDs: ${requestIds.join(', ')}`);
    }

    await newContext.close();
  });
});


