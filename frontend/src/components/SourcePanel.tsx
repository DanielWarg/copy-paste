import './SourcePanel.css'

interface SourcePanelProps {
  sources: Array<{ id: string; excerpt: string; confidence: number }>
}

export default function SourcePanel({ sources }: SourcePanelProps) {
  return (
    <div className="source-panel">
      <h3>Källor</h3>
      {sources.length === 0 ? (
        <div className="no-sources">Inga källor tillgängliga</div>
      ) : (
        <div className="sources-list">
          {sources.map((source) => (
            <div key={source.id} className="source-item">
              <div className="source-id">{source.id} (confidence: {source.confidence.toFixed(2)})</div>
              <div className="source-content">{source.excerpt}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

