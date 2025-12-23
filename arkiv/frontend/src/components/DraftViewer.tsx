import { useState } from 'react'
import './DraftViewer.css'

interface DraftViewerProps {
  draft: {
    text: string
    citations: Array<{ id: string; excerpt: string; confidence: number }>
    policy_violations: string[]
  }
}

export default function DraftViewer({ draft }: DraftViewerProps) {
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null)

  const handleCitationClick = (citationId: string) => {
    setSelectedCitation(selectedCitation === citationId ? null : citationId)
  }

  // Split text and highlight citations
  const renderText = () => {
    const parts = draft.text.split(/(\[source_\d+\])/g)
    return parts.map((part, i) => {
      if (part.match(/\[source_\d+\]/)) {
        const citationId = part.replace(/[\[\]]/g, '')
        return (
          <span
            key={i}
            className={`citation-marker ${selectedCitation === citationId ? 'highlighted' : ''}`}
            onClick={() => handleCitationClick(citationId)}
            style={{ cursor: 'pointer', color: '#0066cc', textDecoration: 'underline' }}
          >
            {part}
          </span>
        )
      }
      return <span key={i}>{part}</span>
    })
  }

  return (
    <div className="draft-viewer">
      <h2>Generated Draft</h2>
      <div className="draft-text">{renderText()}</div>
      {draft.policy_violations.length > 0 && (
        <div className="policy-violations">
          <h3>Policy Violations:</h3>
          <ul>
            {draft.policy_violations.map((violation, i) => (
              <li key={i}>{violation}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

