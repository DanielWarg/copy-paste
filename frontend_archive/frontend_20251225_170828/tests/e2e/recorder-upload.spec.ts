/**
 * E2E Test: Recorder Upload Flow
 * 
 * Tests the complete recorder flow:
 * 1. Navigate to Transcripts page
 * 2. Upload Del21.wav file
 * 3. Verify record creation
 * 4. Verify audio upload
 * 5. Poll for transcription completion
 * 6. Verify transcript appears in list
 */

import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:5173';
const API_BASE = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
const TEST_AUDIO_FILE = path.join(process.cwd(), '..', 'Del21.wav');

test.describe('Recorder Upload E2E', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to frontend
    await page.goto(FRONTEND_URL);
    
    // Wait for app to load
    await page.waitForSelector('h1, h2', { timeout: 10000 });
  });

  test('Upload Del21.wav and verify transcription', async ({ page }) => {
    // Verify test file exists
    if (!fs.existsSync(TEST_AUDIO_FILE)) {
      test.skip(true, `Test file not found: ${TEST_AUDIO_FILE}`);
      return;
    }

    // Navigate to Recorder page (default startvy or via "Inspelning" menu)
    // Default startvy is now "recorder" (RealRecorderPage)
    const recorderButton = page.locator('button:has-text("Inspelning")').first();
    if (await recorderButton.isVisible()) {
      await recorderButton.click();
      await page.waitForTimeout(1000);
    }
    // If already on recorder page (default), no navigation needed

    // Wait for Recorder page to load
    await page.waitForSelector('h2:has-text("Inspelning"), h2:has-text("Transkript")', { timeout: 5000 });

    // Find upload button/label
    const uploadButton = page.locator('label[for="audio-upload-input"], button:has-text("Ladda upp"), label:has-text("Ladda upp")').first();
    await expect(uploadButton).toBeVisible({ timeout: 5000 });

    // Intercept API calls to verify request correlation
    const apiCalls: Array<{ url: string; method: string; requestId?: string }> = [];
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/api/v1/record') || url.includes('/api/v1/transcripts')) {
        const requestId = request.headers()['x-request-id'];
        apiCalls.push({
          url,
          method: request.method(),
          requestId,
        });
      }
    });

    // Upload file
    const fileInput = page.locator('input[type="file"][accept*="audio"]');
    await expect(fileInput).toBeVisible({ timeout: 5000 });
    
    await fileInput.setInputFiles(TEST_AUDIO_FILE);
    await page.waitForTimeout(500);

    // Verify file is selected (should show file name)
    const fileName = path.basename(TEST_AUDIO_FILE);
    await expect(page.locator(`text=${fileName}`)).toBeVisible({ timeout: 2000 });

    // Click "Starta transkribering" button
    const startButton = page.locator('button:has-text("Starta transkribering")');
    await expect(startButton).toBeVisible({ timeout: 2000 });
    await startButton.click();

    // Wait for upload progress
    await expect(page.locator('text=/Skapar record|Laddar upp|Transkriberar/i')).toBeVisible({ timeout: 5000 });

    // Verify API calls were made with request correlation
    expect(apiCalls.length).toBeGreaterThan(0);
    const createCall = apiCalls.find(c => c.url.includes('/api/v1/record/create'));
    expect(createCall).toBeTruthy();
    expect(createCall?.requestId).toBeTruthy();

    // Wait for transcription to complete (with timeout)
    // Poll for "Klart!" or transcript status "ready"
    const maxWaitTime = 120000; // 2 minutes max
    const startTime = Date.now();
    let transcriptionComplete = false;

    while (Date.now() - startTime < maxWaitTime && !transcriptionComplete) {
      // Check for success message
      const successMessage = page.locator('text=/Klart|Transkribering klar/i');
      if (await successMessage.isVisible({ timeout: 2000 }).catch(() => false)) {
        transcriptionComplete = true;
        break;
      }

      // Check if transcript appears in list
      const transcriptRow = page.locator('tr, [class*="transcript"]').filter({ hasText: fileName });
      if (await transcriptRow.isVisible({ timeout: 2000 }).catch(() => false)) {
        transcriptionComplete = true;
        break;
      }

      // Wait a bit before checking again
      await page.waitForTimeout(2000);
    }

    // Verify transcription completed
    expect(transcriptionComplete).toBe(true);

    // Verify transcript appears in list
    const transcriptInList = page.locator('tr, [class*="transcript"]').filter({ hasText: fileName });
    await expect(transcriptInList).toBeVisible({ timeout: 5000 });

    // Verify request correlation: all API calls should have X-Request-Id
    const callsWithoutRequestId = apiCalls.filter(c => !c.requestId);
    expect(callsWithoutRequestId.length).toBe(0);
  });

  test('Request correlation: X-Request-Id is sent and echoed', async ({ page }) => {
    // Navigate to Transcripts page
    const transcriptsButton = page.locator('button:has-text("Transkriptioner"), button:has-text("Inspelning")').first();
    if (await transcriptsButton.isVisible()) {
      await transcriptsButton.click();
      await page.waitForTimeout(1000);
    }

    // Intercept API responses to verify X-Request-Id is echoed
    const requestResponsePairs: Array<{ requestId: string; echoed: boolean }> = [];
    
    page.on('request', (request) => {
      const url = request.url();
      if (url.includes('/api/v1/')) {
        const requestId = request.headers()['x-request-id'];
        if (requestId) {
          requestResponsePairs.push({ requestId, echoed: false });
        }
      }
    });

    page.on('response', (response) => {
      const url = response.url();
      if (url.includes('/api/v1/')) {
        const responseRequestId = response.headers()['x-request-id'];
        if (responseRequestId) {
          const pair = requestResponsePairs.find(p => p.requestId === responseRequestId);
          if (pair) {
            pair.echoed = true;
          }
        }
      }
    });

    // Trigger an API call (load transcripts)
    await page.waitForTimeout(2000);

    // Verify at least one request had X-Request-Id and it was echoed
    const echoedRequests = requestResponsePairs.filter(p => p.echoed);
    expect(echoedRequests.length).toBeGreaterThan(0);
  });

  test('Error handling: shows error on upload failure', async ({ page }) => {
    // Navigate to Transcripts page
    const transcriptsButton = page.locator('button:has-text("Transkriptioner"), button:has-text("Inspelning")').first();
    if (await transcriptsButton.isVisible()) {
      await transcriptsButton.click();
      await page.waitForTimeout(1000);
    }

    // Intercept API calls and fail the upload
    await page.route('**/api/v1/record/create', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'server_error',
            message: 'Internal server error',
            request_id: 'test-request-id-123',
          },
        }),
      });
    });

    // Try to upload a file (create a dummy file)
    const fileInput = page.locator('input[type="file"][accept*="audio"]');
    if (await fileInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      // Create a dummy audio file for testing
      const dummyFile = path.join(process.cwd(), 'test-dummy.wav');
      fs.writeFileSync(dummyFile, Buffer.from('dummy audio data'));
      
      await fileInput.setInputFiles(dummyFile);
      await page.waitForTimeout(500);

      const startButton = page.locator('button:has-text("Starta transkribering")');
      if (await startButton.isVisible({ timeout: 2000 }).catch(() => false)) {
        await startButton.click();

        // Verify error is displayed (brutal-safe: no payloads, just error code)
        await expect(page.locator('.error, [class*="error"], text=/fel|error/i')).toBeVisible({ timeout: 5000 });
        
        // Clean up
        fs.unlinkSync(dummyFile);
      }
    }
  });
});

