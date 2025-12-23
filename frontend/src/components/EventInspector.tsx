import { useState, useEffect } from 'react'
import axios from 'axios'
import DraftViewer from './DraftViewer'
import SourcePanel from './SourcePanel'
import './EventInspector.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const SCOUT_URL = import.meta.env.VITE_SCOUT_URL || 'http://localhost:8001'

interface EventInspectorProps {
  eventId: string | null
  productionMode: boolean
  onSendToPipeline: (eventId: string) => void
}

export default function EventInspector({ eventId, productionMode, onSendToPipeline }: EventInspectorProps) {
  const [event, setEvent] = useState<any>(null)
  const [draft, setDraft] = useState<any>(null)
  const [sources, setSources] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedsMap, setFeedsMap] = useState<Record<string, any>>({})

  useEffect(() => {
    const fetchFeeds = async () => {
      try {
        const response = await axios.get(`${SCOUT_URL}/scout/feeds`)
        const feeds = response.data.feeds || []
        const map: Record<string, any> = {}
        feeds.forEach((feed: any) => {
          map[feed.id] = feed
        })
        setFeedsMap(map)
      } catch (err) {
        // Ignore
      }
    }
    fetchFeeds()
  }, [])

  useEffect(() => {
    if (!eventId) {
      setEvent(null)
      setDraft(null)
      setSources([])
      return
    }

    const fetchEvent = async () => {
      try {
        const response = await axios.get(`${SCOUT_URL}/scout/events?hours=168&limit=200`)
        const foundEvent = response.data.events.find((e: any) => e.event_id === eventId)
        setEvent(foundEvent || null)
      } catch (err: any) {
        setError(err.message || 'Kunde inte hämta event')
      }
    }

    fetchEvent()
  }, [eventId])

  const handleScrubAndDraft = async () => {
    if (!eventId) return

    setLoading(true)
    setError(null)

    try {
      // Step 1: Scrub
      const scrubRes = await axios.post(`${API_BASE}/api/v1/privacy/scrub`, {
        event_id: eventId,
        production_mode: productionMode
      })

      // Step 2: Generate draft
      const draftRes = await axios.post(`${API_BASE}/api/v1/draft/generate`, {
        event_id: eventId,
        clean_text: scrubRes.data.clean_text,
        production_mode: productionMode
      })

      setDraft(draftRes.data)
      setSources(draftRes.data.citations || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Ett fel uppstod')
    } finally {
      setLoading(false)
    }
  }

  const handleSendToTeams = async () => {
    if (!eventId) return

    try {
      const response = await axios.post(`${SCOUT_URL}/scout/notify`, { event_id: eventId })
      if (response.data.ok) {
        alert('Notifiering skickad!')
      } else {
        alert(`Fel: ${response.data.error}`)
      }
    } catch (err: any) {
      alert(`Fel: ${err.response?.data?.error || err.message}`)
    }
  }

  if (!eventId) {
    return (
      <div className="event-inspector">
        <h3>Event Inspector</h3>
        <p>Välj ett event från signalstream för att se detaljer.</p>
      </div>
    )
  }

  const feed = event ? feedsMap[event.feed_id] : null

  return (
    <div className="event-inspector">
      <h3>Event Inspector</h3>

      {event && (
        <div className="event-metadata">
          <div><strong>Feed:</strong> {feed?.name || event.feed_url}</div>
          <div><strong>Detected:</strong> {new Date(event.detected_at).toLocaleString('sv-SE')}</div>
          <div><strong>Score:</strong> {event.score !== null ? event.score : 'N/A'}</div>
          <div><strong>Event ID:</strong> {event.event_id}</div>
        </div>
      )}

      <div className="event-actions">
        <button onClick={handleScrubAndDraft} disabled={loading}>
          {loading ? 'Bearbetar...' : 'Scrub & Draft'}
        </button>
        <button onClick={handleSendToTeams} disabled={!eventId}>
          Send to Teams
        </button>
        <button onClick={() => onSendToPipeline(eventId)}>
          Send to Pipeline
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {draft && (
        <div className="draft-preview">
          <DraftViewer draft={draft} />
          <SourcePanel sources={sources} />
        </div>
      )}
    </div>
  )
}

