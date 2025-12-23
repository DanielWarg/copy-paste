import { useState } from 'react'
import axios from 'axios'
import './UniversalBox.css'

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
  const [inputType, setInputType] = useState<'url' | 'text' | 'audio'>('url')
  const [inputValue, setInputValue] = useState('')
  const [audioFile, setAudioFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [eventId, setEventId] = useState<string | null>(null)

  const handleAudioUpload = async (file: File) => {
    setLoading(true)
    setError(null)

    try {
      // Step 1: Upload and transcribe audio
      const formData = new FormData()
      formData.append('file', file)
      
      const audioRes = await axios.post(`${API_BASE}/api/v1/ingest/audio`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      
      const newEventId = audioRes.data.event_id
      setEventId(newEventId)
      onEventCreated(newEventId)

      // Step 2: Scrub v2 (anonymisera transkriptet)
      const scrubRes = await axios.post(`${API_BASE}/api/v1/privacy/scrub_v2`, {
        event_id: newEventId,
        production_mode: productionMode,
        max_retries: 2
      })
      
      // Check if approval is required
      if (scrubRes.data.approval_required) {
        setError(`Godkännande krävs: ${scrubRes.data.semantic_risk || 'Semantic risk detected'}. Använd approval_token för att fortsätta.`)
        return
      }

      // Step 3: Generate draft from anonymized transcript
      const draftRes = await axios.post(`${API_BASE}/api/v1/draft/generate`, {
        event_id: newEventId,
        clean_text: scrubRes.data.clean_text,
        production_mode: productionMode
      })

      onDraftGenerated(draftRes.data)
      onSourcesLoaded(draftRes.data.citations || [])
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Ett fel uppstod vid audio upload')
    } finally {
      setLoading(false)
    }
  }

  const handleIngest = async () => {
    if (inputType === 'audio') {
      if (!audioFile) {
        setError('Vänligen välj en audio-fil')
        return
      }
      await handleAudioUpload(audioFile)
      return
    }

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

      // Step 2: Scrub v2
      const scrubRes = await axios.post(`${API_BASE}/api/v1/privacy/scrub_v2`, {
        event_id: newEventId,
        production_mode: productionMode,
        max_retries: 2
      })
      
      // Check if approval is required
      if (scrubRes.data.approval_required) {
        setError(`Godkännande krävs: ${scrubRes.data.semantic_risk || 'Semantic risk detected'}. Använd approval_token för att fortsätta.`)
        return
      }

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
          onChange={(e) => {
            setInputType(e.target.value as 'url' | 'text' | 'audio')
            setAudioFile(null)
            setInputValue('')
          }}
        >
          <option value="url">URL</option>
          <option value="text">Text</option>
          <option value="audio">Audio</option>
        </select>
        {inputType === 'audio' ? (
          <input
            type="file"
            accept="audio/*"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) {
                setAudioFile(file)
                setInputValue(file.name)
              }
            }}
          />
        ) : (
          <input
            type={inputType === 'url' ? 'url' : 'text'}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={inputType === 'url' ? 'https://...' : 'Klistra in text...'}
          />
        )}
        <button onClick={handleIngest} disabled={loading}>
          {loading ? 'Bearbetar...' : 'Ingest'}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      {eventId && <div className="success">Event ID: {eventId}</div>}
    </div>
  )
}

