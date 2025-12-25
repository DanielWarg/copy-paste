/**
 * Backend Status Indicator
 * 
 * Pings /health endpoint and displays connection status.
 * Detects mTLS requirements.
 */

import { useEffect, useState } from 'react';
import { Activity, AlertCircle, CheckCircle2 } from 'lucide-react';

interface BackendStatus {
  reachable: boolean;
  mTLSRequired: boolean;
  checking: boolean;
  error?: string;
}

export function BackendStatus() {
  const [status, setStatus] = useState<BackendStatus>({
    reachable: false,
    mTLSRequired: false,
    checking: true,
  });

  useEffect(() => {
    let mounted = true;
    let timeoutId: NodeJS.Timeout;

    const checkHealth = async () => {
      try {
        // Use same API base URL as client.ts
        // Default: http://localhost:8000 (direct backend in dev)
        // Prod: https://localhost (proxy for prod_brutal)
        const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
        const healthUrl = `${apiBase}/health`;
        
        // Fallback to HTTP if HTTPS fails (for health endpoint)
        const httpUrl = healthUrl.replace('https://', 'http://').replace(':443', ':80');
        
        try {
          const response = await fetch(httpUrl, {
            method: 'GET',
            headers: {
              'X-Request-Id': `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            },
          });

          if (mounted) {
            setStatus({
              reachable: response.ok,
              mTLSRequired: false,
              checking: false,
            });
          }
        } catch (error: any) {
          // If HTTP fails, try HTTPS (might require mTLS)
          try {
            const httpsUrl = healthUrl.replace('http://', 'https://');
            const httpsResponse = await fetch(httpsUrl, {
              method: 'GET',
              headers: {
                'X-Request-Id': `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              },
            });
            if (mounted) {
              setStatus({
                reachable: httpsResponse.ok,
                mTLSRequired: false,
                checking: false,
              });
            }
          } catch (httpsError: any) {
            // HTTPS failed - might be mTLS issue
            if (mounted) {
              setStatus({
                reachable: false,
                mTLSRequired: true,
                checking: false,
                error: 'mTLS handshake failed',
              });
            }
          }
        }
      } catch (error: any) {
        if (mounted) {
          setStatus({
            reachable: false,
            mTLSRequired: false,
            checking: false,
            error: 'Kunde inte ansluta till backend',
          });
        }
      }

      // Check again after 30 seconds (not spamming)
      if (mounted) {
        timeoutId = setTimeout(checkHealth, 30000);
      }
    };

    // Initial check
    checkHealth();

    return () => {
      mounted = false;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, []);

  if (status.checking) {
    return (
      <div className="flex items-center gap-2 text-xs text-zinc-500 dark:text-zinc-400">
        <Activity size={12} className="animate-pulse" />
        <span>Kontrollerar backend...</span>
      </div>
    );
  }

  if (!status.reachable) {
    return (
      <div className="flex items-center gap-2 text-xs text-red-500">
        <AlertCircle size={12} />
        <span>
          {status.mTLSRequired 
            ? 'mTLS krävs' 
            : 'Backend otillgänglig'}
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-500">
      <CheckCircle2 size={12} />
      <span>Backend ansluten</span>
    </div>
  );
}

