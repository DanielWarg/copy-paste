import { useState, useEffect } from 'react'
import axios from 'axios'

const SCOUT_URL = import.meta.env.VITE_SCOUT_URL || 'http://localhost:8001'

interface Feed {
  id: string
  name: string
  url: string
  enabled: boolean
  poll_interval: number
  score_threshold?: number
  notifications?: {
    enabled: boolean
    min_score: number
  }
}

export default function FeedsPanel() {
  const [feeds, setFeeds] = useState<Feed[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAddForm, setShowAddForm] = useState(false)
  const [newFeed, setNewFeed] = useState({
    name: '',
    url: '',
    poll_interval: 900,
    score_threshold: undefined as number | undefined,
    notifications: { enabled: false, min_score: 8 }
  })

  const fetchFeeds = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`${SCOUT_URL}/scout/feeds`)
      setFeeds(response.data.feeds || [])
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Kunde inte hämta feeds')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchFeeds()
  }, [])

  const handleToggleEnabled = async (feedId: string, enabled: boolean) => {
    try {
      await axios.patch(`${SCOUT_URL}/scout/feeds/${feedId}`, { enabled: !enabled })
      fetchFeeds()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kunde inte uppdatera feed')
    }
  }

  const handleAddFeed = async () => {
    if (!newFeed.name || !newFeed.url) {
      setError('Namn och URL krävs')
      return
    }

    try {
      await axios.post(`${SCOUT_URL}/scout/feeds`, newFeed)
      setShowAddForm(false)
      setNewFeed({ name: '', url: '', poll_interval: 900, notifications: { enabled: false, min_score: 8 } })
      fetchFeeds()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kunde inte lägga till feed')
    }
  }

  const handleDeleteFeed = async (feedId: string) => {
    if (!confirm('Är du säker på att du vill ta bort denna feed?')) {
      return
    }

    try {
      await axios.delete(`${SCOUT_URL}/scout/feeds/${feedId}`)
      fetchFeeds()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kunde inte ta bort feed')
    }
  }

  const handlePollNow = async (feedId: string) => {
    try {
      const response = await axios.post(`${SCOUT_URL}/scout/feeds/${feedId}/poll`)
      alert(`Polled feed: ${response.data.new_items} new items`)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Kunde inte polla feed')
    }
  }

  return (
    <div className="feeds-panel">
      <div className="feeds-panel-header">
        <h3>Feeds & Inkanaler</h3>
        <button onClick={() => setShowAddForm(!showAddForm)}>➕ Lägg till</button>
      </div>

      {error && <div className="error">{error}</div>}

      {showAddForm && (
        <div className="add-feed-form">
          <input
            type="text"
            placeholder="Feed namn"
            value={newFeed.name}
            onChange={(e) => setNewFeed({ ...newFeed, name: e.target.value })}
          />
          <input
            type="url"
            placeholder="RSS URL"
            value={newFeed.url}
            onChange={(e) => setNewFeed({ ...newFeed, url: e.target.value })}
          />
          <input
            type="number"
            placeholder="Poll interval (sekunder)"
            value={newFeed.poll_interval}
            onChange={(e) => setNewFeed({ ...newFeed, poll_interval: parseInt(e.target.value) || 900 })}
          />
          <button onClick={handleAddFeed}>Spara</button>
          <button onClick={() => setShowAddForm(false)}>Avbryt</button>
        </div>
      )}

      {loading && <div>Laddar...</div>}

      <div className="feeds-list">
        {feeds.map((feed) => (
          <div key={feed.id} className="feed-item">
            <div className="feed-header">
              <span className="feed-name">{feed.name}</span>
              <label>
                <input
                  type="checkbox"
                  checked={feed.enabled}
                  onChange={() => handleToggleEnabled(feed.id, feed.enabled)}
                />
                Enabled
              </label>
            </div>
            <div className="feed-details">
              <div>URL: {feed.url}</div>
              <div>Poll interval: {feed.poll_interval}s</div>
              {feed.score_threshold && <div>Score threshold: {feed.score_threshold}</div>}
              {feed.notifications && (
                <div>
                  Notifications: {feed.notifications.enabled ? 'ON' : 'OFF'} (min: {feed.notifications.min_score})
                </div>
              )}
            </div>
            <div className="feed-actions">
              <button onClick={() => handlePollNow(feed.id)}>Poll Now</button>
              <button onClick={() => handleDeleteFeed(feed.id)}>Ta bort</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

