/**
 * Server-side API proxy
 * 
 * SECURITY: API keys are never exposed to the browser.
 * All backend calls go through this server-side route.
 * 
 * SECURITY: Mitigates CVE-2025-55184 (DoS) and CVE-2025-55183 (Source Code Exposure)
 * by validating requests server-side and limiting payload sizes.
 */
import { NextRequest, NextResponse } from "next/server";

const API_KEY = process.env.API_KEY || "demo-key-12345";
const BACKEND_URL = process.env.BACKEND_URL || "http://backend:8000";
const MAX_PAYLOAD_SIZE = 20 * 1024 * 1024; // 20MB

export async function POST(request: NextRequest) {
  try {
    // Security: Validate request size
    const contentLength = request.headers.get("content-length");
    if (contentLength && parseInt(contentLength) > MAX_PAYLOAD_SIZE) {
      return NextResponse.json(
        { error: "Payload too large" },
        { status: 413 }
      );
    }

    // Get request body
    const body = await request.json();

    // Security: Validate URL format (HTTPS only)
    if (body.url && !body.url.startsWith("https://")) {
      return NextResponse.json(
        { error: "Only HTTPS URLs are allowed" },
        { status: 400 }
      );
    }

    // Forward to backend with API key
    const backendResponse = await fetch(`${BACKEND_URL}/api/v1/ingest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY,
      },
      body: JSON.stringify(body),
    });

    const data = await backendResponse.json();
    return NextResponse.json(data, { status: backendResponse.status });
  } catch (error) {
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
