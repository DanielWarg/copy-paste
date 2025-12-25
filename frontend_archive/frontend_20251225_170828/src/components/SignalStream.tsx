import { useState, useEffect } from 'react'
import axios from 'axios'
import { getAxiosConfigWithRequestId } from '../utils/requestId'
import './SignalStream.css'

const SCOUT_URL = import.meta.env.VITE_SCOUT_URL || 'http://localhost:8001'
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

interface Event {
  event_id: string
  feed_id: string
  feed_url: string
  detected_at: string
  score: number | null
  notification_sent: boolean
}

interface SignalStreamProps {
  onEventClick: (eventId: string) => void
  selectedEventId: string | null
}

export default function SignalStream({ onEventClick, selectedEventId }: SignalStreamProps) {
  const [events, setEvents] = useState<Event[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedsMap, setFeedsMap] = useState<Record<string, string>>({})

  const fetchFeeds = async () => {
    try {
      // Try backend /api/v1/sources first, fallback to scout
      try {
        const response = await axios.get(`${API_BASE}/api/v1/sources`, getAxiosConfigWithRequestId())
        const feeds = response.data.items || []
        const map: Record<string, string> = {}
        feeds.forEach((feed: any) => {
          map[feed.id] = feed.name
        })
        setFeedsMap(map)
      } catch {
        // Fallback to scout if backend sources not available
        const response = await axios.get(`${SCOUT_URL}/scout/feeds`, getAxiosConfigWithRequestId())
        const feeds = response.data.feeds || []
        const map: Record<string, string> = {}
        feeds.forEach((feed: any) => {
          map[feed.id] = feed.name
        })
        setFeedsMap(map)
      }
    } catch (err) {
      // Ignore feed fetch errors
    }
  }

  const fetchEvents = async () => {
    setLoading(true)
    setError(null)
    try {
      // Try backend /api/v1/events first, fallback to scout
      try {
        const response = await axios.get(`${API_BASE}/api/v1/events?limit=50`, getAxiosConfigWithRequestId())
        setEvents(response.data.items || [])
      } catch {
        // Fallback to scout if backend events not available
        const response = await axios.get(`${SCOUT_URL}/scout/events?hours=24&limit=50`, getAxiosConfigWithRequestId())
        setEvents(response.data.events || [])
      }
    } catch (err: any) {
      setError(err.response?.data?.error || err.message || 'Kunde inte hämta events')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFeeds()
    fetchEvents()
    const interval = setInterval(fetchEvents, 5000) // Poll every 5 seconds
    return () => clearInterval(interval)
  }, [])

  const getPriorityClass = (score: number | null) => {
    if (score === null) return 'priority-grey'
    if (score >= 8) return 'priority-red'
    if (score >= 6) return 'priority-orange'
    return 'priority-grey'
  }

  const formatTimeAgo = (isoString: string) => {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    
    if (diffMins < 1) return 'Nu'
    if (diffMins < 60) return `${diffMins}m sedan`
    const diffHours = Math.floor(diffMins / 60)
    if (diffHours < 24) return `${diffHours}h sedan`
    const diffDays = Math.floor(diffHours / 24)
    return `${diffDays}d sedan`
  }

  return (
    <div className="signal-stream">
      <div className="signal-stream-header">
        <h3>Live Signaler</h3>
        <span className="live-indicator">● Live</span>
      </div>

      {error && <div className="error">{error}</div>}

      {loading && events.length === 0 && <div>Laddar...</div>}

      <div className="events-list">
        {events.map((event) => (
          <div
            key={event.event_id}
            className={`event-row ${getPriorityClass(event.score)} ${selectedEventId === event.event_id ? 'selected' : ''}`}
            onClick={() => onEventClick(event.event_id)}
          >
            <div className="event-time">{formatTimeAgo(event.detected_at)}</div>
            <div className="event-feed">{feedsMap[event.feed_id] || event.feed_url}</div>
            <div className="event-score">
              {event.score !== null ? `Score: ${event.score}` : 'No score'}
            </div>
            <div className="event-id">{event.event_id.substring(0, 8)}...</div>
            {event.notification_sent && <span className="notification-badge">🔔</span>}
          </div>
        ))}
      </div>

      {events.length === 0 && !loading && (
        <div className="no-events">Inga events hittades de senaste 24 timmarna.</div>
      )}
    </div>
  )
}

