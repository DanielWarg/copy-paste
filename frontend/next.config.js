/** @type {import('next').NextConfig} */
const nextConfig = {
  // Security: Disable source maps in production
  productionBrowserSourceMaps: false,
  
  // Security: Headers
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
        ],
      },
    ];
  },
  
  // Security: Rate limiting handled by backend
  // Note: Next.js 15.1.0+ includes patches for CVE-2025-55184 and CVE-2025-55183
  // Ensure you're running the latest patched version
  
  // Environment variables
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

module.exports = nextConfig;

