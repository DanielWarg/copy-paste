"use client";

import { useState } from "react";

interface IngestResult {
  source_id?: string;
  status?: string;
  message?: string;
  error?: string;
}

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IngestResult | null>(null);
  const [sourceId, setSourceId] = useState<string | null>(null);
  const [briefResult, setBriefResult] = useState<any>(null);

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);
    
    try {
      // Use server-side API proxy (not direct backend call)
      const response = await fetch("/api/proxy/ingest", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url, source_type: "url" }),
      });
      
      const data = await response.json();
      setResult(data);
      if (data.source_id) {
        setSourceId(data.source_id);
      }
    } catch (error) {
      setResult({ error: "Failed to ingest URL" });
    } finally {
      setLoading(false);
    }
  };

  const handleIndex = async () => {
    if (!sourceId) return;
    
    setLoading(true);
    try {
      const response = await fetch("/api/proxy/index", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ source_ids: [sourceId] }),
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: "Failed to index" });
    } finally {
      setLoading(false);
    }
  };

  const handleBrief = async () => {
    if (!sourceId) return;
    
    setLoading(true);
    try {
      const response = await fetch("/api/proxy/brief", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ source_ids: [sourceId] }),
      });
      
      const data = await response.json();
      setBriefResult(data);
    } catch (error) {
      setBriefResult({ error: "Failed to generate brief" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <h1>Copy/Paste - Nyhetsdesk Copilot</h1>
      
      <form onSubmit={handleIngest} style={{ marginTop: "2rem" }}>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Ange URL (HTTPS endast, t.ex. https://www.example.com)"
          required
          style={{
            width: "100%",
            padding: "0.5rem",
            fontSize: "1rem",
            border: "1px solid #ccc",
            borderRadius: "4px",
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
            marginTop: "1rem",
            padding: "0.5rem 1rem",
            fontSize: "1rem",
            backgroundColor: "#0070f3",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Laddar..." : "1. Ingest URL"}
        </button>
      </form>

      {sourceId && (
        <div style={{ marginTop: "1rem", display: "flex", gap: "0.5rem" }}>
          <button
            onClick={handleIndex}
            disabled={loading}
            style={{
              padding: "0.5rem 1rem",
              fontSize: "1rem",
              backgroundColor: "#28a745",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            2. Index
          </button>
          <button
            onClick={handleBrief}
            disabled={loading}
            style={{
              padding: "0.5rem 1rem",
              fontSize: "1rem",
              backgroundColor: "#ffc107",
              color: "black",
              border: "none",
              borderRadius: "4px",
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            3. Generate Brief
          </button>
        </div>
      )}

      {result && (
        <div style={{ marginTop: "2rem", padding: "1rem", border: "1px solid #ccc", borderRadius: "4px", backgroundColor: "#f8f9fa" }}>
          <h3>Resultat:</h3>
          <pre style={{ overflow: "auto", maxHeight: "200px" }}>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}

      {briefResult && (
        <div style={{ marginTop: "2rem", padding: "1rem", border: "1px solid #28a745", borderRadius: "4px", backgroundColor: "#d4edda" }}>
          <h3>Brief:</h3>
          <pre style={{ overflow: "auto", maxHeight: "400px", whiteSpace: "pre-wrap" }}>{JSON.stringify(briefResult, null, 2)}</pre>
        </div>
      )}
    </main>
  );
}

