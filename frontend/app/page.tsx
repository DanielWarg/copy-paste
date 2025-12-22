"use client";

import { useState } from "react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Use server-side API proxy (not direct backend call)
      const response = await fetch("/api/proxy/ingest", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({ error: "Failed to ingest URL" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <h1>Copy/Paste - Nyhetsdesk Copilot</h1>
      
      <form onSubmit={handleSubmit} style={{ marginTop: "2rem" }}>
        <input
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Ange URL (HTTPS endast)"
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
          {loading ? "Laddar..." : "Skapa brief"}
        </button>
      </form>

      {result && (
        <div style={{ marginTop: "2rem", padding: "1rem", border: "1px solid #ccc", borderRadius: "4px" }}>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </main>
  );
}

