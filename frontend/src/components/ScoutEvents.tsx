import { useState, useEffect } from 'react'
import axios from 'axios'

const SCOUT_API_BASE = 'http://localhost:8001'

interface ScoutEvent {
  dedupe_key: string
  feed_url: string
  event_id: string
  detected_at: string
  score: number | null
}

interface ScoutEventsProps {
  onEventClick?: (eventId: string) => void
}

export default function ScoutEvents({ onEventClick }: ScoutEventsProps) {
  const [events, setEvents] = useState<ScoutEvent[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchEvents = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${SCOUT_API_BASE}/scout/events?hours=24`)
      setEvents(response.data.events || [])
    } catch (err: any) {
      setError(err.message || 'Kunde inte hämta events')
      console.error('Error fetching scout events:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchEvents()
    // Refresh every 30 seconds
    const interval = setInterval(fetchEvents, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="scout-events">
      <div className="scout-events-header">
        <h3>Incoming RSS Events (24h)</h3>
        <button onClick={fetchEvents} disabled={loading}>
          {loading ? 'Laddar...' : 'Uppdatera'}
        </button>
      </div>

      {error && (
        <div className="error">
          {error}
        </div>
      )}

      {events.length === 0 && !loading && (
        <div className="no-events">
          Inga events hittades de senaste 24 timmarna.
        </div>
      )}

      <div className="events-list">
        {events.map((event, idx) => (
          <div
            key={idx}
            className="event-item"
            onClick={() => onEventClick?.(event.event_id)}
            style={{ cursor: onEventClick ? 'pointer' : 'default' }}
          >
            <div className="event-header">
              <span className="event-feed">{event.feed_url}</span>
              {event.score && (
                <span className="event-score">Score: {event.score}</span>
              )}
            </div>
            <div className="event-meta">
              <span className="event-id">Event: {event.event_id.substring(0, 8)}...</span>
              <span className="event-time">
                {new Date(event.detected_at).toLocaleString('sv-SE')}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

