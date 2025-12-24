interface ProductionModeToggleProps {
  productionMode: boolean
  onToggle: (mode: boolean) => void
}

export default function ProductionModeToggle({
  productionMode,
  onToggle
}: ProductionModeToggleProps) {
  return (
    <div className="production-mode-toggle">
      <label>
        <input
          type="checkbox"
          checked={productionMode}
          onChange={(e) => onToggle(e.target.checked)}
        />
        Production Mode {productionMode ? 'ON' : 'OFF'}
      </label>
      {productionMode && (
        <div className="warning">
          ⚠️ Anonymisering krävs. Externa API-anrop kräver anonymisering även i OFF-läge.
        </div>
      )}
    </div>
  )
}

