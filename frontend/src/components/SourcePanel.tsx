interface SourcePanelProps {
  sources: Array<{ id: string; excerpt: string; confidence: number }>
}

export default function SourcePanel({ sources }: SourcePanelProps) {
  return (
    <div className="source-panel">
      <h2>Sources</h2>
      {sources.length === 0 ? (
        <p>Inga sources tillgängliga</p>
      ) : (
        <ul>
          {sources.map((source) => (
            <li key={source.id}>
              <strong>{source.id}</strong> (confidence: {source.confidence.toFixed(2)})
              <p>{source.excerpt}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

