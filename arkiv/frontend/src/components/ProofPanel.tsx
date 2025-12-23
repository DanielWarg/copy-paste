import './ProofPanel.css'

interface ReceiptStep {
  name: string
  status: "ok" | "retry" | "blocked" | "failed"
  model_id?: string
  started_at: string
  ended_at: string
  metrics: Record<string, any>
}

interface Receipt {
  steps: ReceiptStep[]
  flags: string[]
  clean_text_sha256: string
}

interface ProofPanelProps {
  receipt: Receipt | null
  approvalRequired: boolean
  approvalToken: string | null
  onApprove: (token: string) => void
}

export default function ProofPanel({ receipt, approvalRequired, approvalToken, onApprove }: ProofPanelProps) {
  if (!receipt) return null

  const getStatusColor = (status: string) => {
    switch (status) {
      case "ok": return "green"
      case "retry": return "orange"
      case "blocked": return "red"
      case "failed": return "red"
      default: return "gray"
    }
  }

  return (
    <div className="proof-panel">
      <h3>Privacy Shield Proof</h3>
      
      {approvalRequired && (
        <div className="approval-required">
          <p>⚠️ Approval required: {receipt.flags.join(", ")}</p>
          {approvalToken && (
            <button onClick={() => onApprove(approvalToken)}>
              Approve & Continue
            </button>
          )}
        </div>
      )}
      
      <div className="receipt-steps">
        {receipt.steps.map((step, i) => (
          <div key={i} className={`step step-${step.status}`}>
            <span className="step-name">{step.name}</span>
            <span className={`step-status status-${getStatusColor(step.status)}`}>
              {step.status}
            </span>
            {step.model_id && <span className="model-id">{step.model_id}</span>}
          </div>
        ))}
      </div>
      
      <div className="receipt-flags">
        {receipt.flags.length > 0 && (
          <div>
            <strong>Flags:</strong> {receipt.flags.join(", ")}
          </div>
        )}
      </div>
      
      <div className="receipt-hash">
        <small>Text Hash: {receipt.clean_text_sha256.substring(0, 16)}...</small>
      </div>
    </div>
  )
}

