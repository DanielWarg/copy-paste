import { useState } from 'react'
import FeedsPanel from '../components/FeedsPanel'
import SignalStream from '../components/SignalStream'
import EventInspector from '../components/EventInspector'
import NotificationsPanel from '../components/NotificationsPanel'
import './ConsolePage.css'

interface ConsolePageProps {
  productionMode: boolean
  onEventSelect: (eventId: string) => void
}

export default function ConsolePage({ productionMode, onEventSelect }: ConsolePageProps) {
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null)

  return (
    <div className="console-page">
      <div className="console-section feeds-section">
        <FeedsPanel />
      </div>
      
      <div className="console-section signal-section">
        <SignalStream
          onEventClick={(eventId) => setSelectedEventId(eventId)}
          selectedEventId={selectedEventId}
        />
      </div>
      
      <div className="console-section inspector-section">
        <EventInspector
          eventId={selectedEventId}
          productionMode={productionMode}
          onSendToPipeline={onEventSelect}
        />
      </div>
      
      <div className="console-section notifications-section">
        <NotificationsPanel eventId={selectedEventId} />
      </div>
    </div>
  )
}

