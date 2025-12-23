import { useState } from 'react'
import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface UniversalBoxProps {
  productionMode: boolean
  onEventCreated: (eventId: string) => void
  onDraftGenerated: (draft: any) => void
  onSourcesLoaded: (sources: any[]) => void
}

export default function UniversalBox({
  productionMode,
  onEventCreated,
  onDraftGenerated,
  onSourcesLoaded
}: UniversalBoxProps) {
  const [inputType, setInputType] = useState<'url' | 'text'>('url')
  const [inputValue, setInputValue] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [eventId, setEventId] = useState<string | null>(null)

  const handleIngest = async () => {
    if (!inputValue.trim()) {
      setError('Vänligen ange URL eller text')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Step 1: Ingest
      const ingestRes = await axios.post(`${API_BASE}/api/v1/ingest`, {
        input_type: inputType,
        value: inputValue
      })

      const newEventId = ingestRes.data.event_id
      setEventId(newEventId)
      onEventCreated(newEventId)

      // Step 2: Scrub
      const scrubRes = await axios.post(`${API_BASE}/api/v1/privacy/scrub`, {
        event_id: newEventId,
        production_mode: productionMode
      })

      // Step 3: Generate draft
      const draftRes = await axios.post(`${API_BASE}/api/v1/draft/generate`, {
        event_id: newEventId,
        clean_text: scrubRes.data.clean_text,
        production_mode: productionMode
      })

      onDraftGenerated(draftRes.data)
      onSourcesLoaded(draftRes.data.citations || [])

    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Ett fel uppstod')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="universal-box">
      <h2>Ingest Source (Event/Source)</h2>
      <div className="input-group">
        <select
          value={inputType}
          onChange={(e) => setInputType(e.target.value as 'url' | 'text')}
        >
          <option value="url">URL</option>
          <option value="text">Text</option>
        </select>
        <input
          type={inputType === 'url' ? 'url' : 'text'}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={inputType === 'url' ? 'https://...' : 'Klistra in text...'}
        />
        <button onClick={handleIngest} disabled={loading}>
          {loading ? 'Bearbetar...' : 'Ingest'}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      {eventId && <div className="success">Event ID: {eventId}</div>}
    </div>
  )
}

