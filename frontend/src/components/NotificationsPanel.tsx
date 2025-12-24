import { useState, useEffect } from 'react'
import axios from 'axios'

const SCOUT_URL = import.meta.env.VITE_SCOUT_URL || 'http://localhost:8001'

interface NotificationsPanelProps {
  eventId: string | null
}

interface ConfigStatus {
  teams_configured: boolean
  notifications_enabled: boolean
  default_min_score: number
  feed_count: number
}

export default function NotificationsPanel({ eventId }: NotificationsPanelProps) {
  const [status, setStatus] = useState<ConfigStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchStatus = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${SCOUT_URL}/scout/config/status`)
      setStatus(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Kunde inte hämta status')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
  }, [])

  const handleTestNotification = async () => {
    if (!eventId) {
      alert('Välj ett event först')
      return
    }

    try {
      const response = await axios.post(`${SCOUT_URL}/scout/notify`, { event_id: eventId })
      if (response.data.ok) {
        alert('Testnotifiering skickad!')
      } else {
        alert(`Fel: ${response.data.error}`)
      }
    } catch (err: any) {
      alert(`Fel: ${err.response?.data?.error || err.message}`)
    }
  }

  if (loading && !status) {
    return (
      <div className="notifications-panel">
        <h3>Notifieringar</h3>
        <div>Laddar...</div>
      </div>
    )
  }

  return (
    <div className="notifications-panel">
      <h3>Notifieringar</h3>

      {status && (
        <div className="notification-status">
          <div>
            <strong>Teams konfigurerad:</strong> {status.teams_configured ? 'Ja' : 'Nej'}
          </div>
          <div>
            <strong>Notifieringar aktiverade:</strong> {status.notifications_enabled ? 'Ja' : 'Nej'}
          </div>
          <div>
            <strong>Min score:</strong> {status.default_min_score}
          </div>
          <div>
            <strong>Antal feeds:</strong> {status.feed_count}
          </div>
          <div className="webhook-info">
            Webhook URL: Konfigurerad via env (TEAMS_WEBHOOK_URL)
          </div>
        </div>
      )}

      <div className="notification-actions">
        <button onClick={handleTestNotification} disabled={!eventId || !status?.teams_configured}>
          Test Notification
        </button>
      </div>

      {error && <div className="error">{error}</div>}
    </div>
  )
}

