import { useState } from 'react'
import axios from 'axios'
import { getAxiosConfigWithRequestId } from '../utils/requestId'
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
      
      // Use record/audio endpoint (ingest/audio doesn't exist)
      // First create record, then upload audio
      const createRes = await axios.post(`${API_BASE}/api/v1/record/create`, {
        title: file.name || 'Audio upload'
      }, getAxiosConfigWithRequestId());
      
      const transcriptId = createRes.data.transcript_id;
      const audioRes = await axios.post(`${API_BASE}/api/v1/record/${transcriptId}/audio`, formData, {
        ...getAxiosConfigWithRequestId(),
        headers: {
          'Content-Type': 'multipart/form-data',
          ...getAxiosConfigWithRequestId().headers,
        }
      })
      
      const newEventId = transcriptId.toString()
      
      const newEventId = audioRes.data.event_id
      setEventId(newEventId)
      onEventCreated(newEventId)

      // Step 2: Privacy mask (use /privacy/mask endpoint)
      // Get transcript text first (simplified - in real flow would get from transcript endpoint)
      const scrubRes = await axios.post(`${API_BASE}/api/v1/privacy/mask`, {
        text: '', // Would need to get transcript text from /api/v1/transcripts/{id}
        mode: productionMode ? 'strict' : 'balanced'
      }, getAxiosConfigWithRequestId())
      
      // Check if approval is required
      if (scrubRes.data.approval_required) {
        setError(`Godkännande krävs: ${scrubRes.data.semantic_risk || 'Semantic risk detected'}. Använd approval_token för att fortsätta.`)
        return
      }

      // Step 3: Generate draft (use correct endpoint: /events/{id}/draft)
      // Note: This requires event_id as integer, and draft endpoint expects raw_text (will be masked by Privacy Gate)
      const draftRes = await axios.post(`${API_BASE}/api/v1/events/${parseInt(newEventId)}/draft`, {
        raw_text: scrubRes.data.maskedText || '', // Use masked text from privacy/mask
        mode: productionMode ? 'strict' : 'balanced'
      }, getAxiosConfigWithRequestId())

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
      // Step 1: Create record/project (ingest endpoint doesn't exist)
      const createRes = await axios.post(`${API_BASE}/api/v1/record/create`, {
        title: inputType === 'url' ? `URL: ${inputValue.substring(0, 50)}` : 'Text input'
      }, getAxiosConfigWithRequestId())

      const transcriptId = createRes.data.transcript_id
      const newEventId = transcriptId.toString()
      setEventId(newEventId)
      onEventCreated(newEventId)

      // Step 2: Privacy mask (use /privacy/mask endpoint)
      const scrubRes = await axios.post(`${API_BASE}/api/v1/privacy/mask`, {
        text: inputValue,
        mode: productionMode ? 'strict' : 'balanced'
      }, getAxiosConfigWithRequestId())

      // Step 3: Generate draft (use correct endpoint: /events/{id}/draft)
      // Draft endpoint expects raw_text and will apply Privacy Gate internally
      const draftRes = await axios.post(`${API_BASE}/api/v1/events/${transcriptId}/draft`, {
        raw_text: inputValue, // Privacy Gate will mask this
        mode: productionMode ? 'strict' : 'balanced'
      }, getAxiosConfigWithRequestId())

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

