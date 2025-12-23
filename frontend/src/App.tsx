import { useState } from 'react'
import UniversalBox from './components/UniversalBox'
import ProductionModeToggle from './components/ProductionModeToggle'
import DraftViewer from './components/DraftViewer'
import SourcePanel from './components/SourcePanel'
import './App.css'

function App() {
  const [productionMode, setProductionMode] = useState(true)
  const [eventId, setEventId] = useState<string | null>(null)
  const [draft, setDraft] = useState<any>(null)
  const [sources, setSources] = useState<any[]>([])

  return (
    <div className="app">
      <header className="app-header">
        <h1>Copy/Paste - Editorial AI Pipeline</h1>
        <ProductionModeToggle
          productionMode={productionMode}
          onToggle={setProductionMode}
        />
      </header>
      
      <main className="app-main">
        <div className="app-section">
          <UniversalBox
            productionMode={productionMode}
            onEventCreated={(id) => setEventId(id)}
            onDraftGenerated={setDraft}
            onSourcesLoaded={setSources}
          />
        </div>
        
        {draft && (
          <div className="app-section">
            <DraftViewer draft={draft} />
            <SourcePanel sources={sources} />
          </div>
        )}
      </main>
    </div>
  )
}

export default App

