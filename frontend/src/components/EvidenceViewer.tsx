import type { SourceResponse } from "../types/document"
import { findExactOverlap } from "../utils/evidence"

type Props = {
    source: SourceResponse | null
    answer: string | null
    sourceIds: number[]
    selectedChunkId: number | null
    loading: boolean
    error: string | null
    onSelect: (chunkId: number) => void
    mobileOpen: boolean
    onClose: () => void
}

function EvidenceViewer({source,answer,sourceIds,selectedChunkId,loading,error,onSelect,mobileOpen,onClose}: Props) {
    const overlap = source && findExactOverlap(source.content,answer)
    return <aside id="workspace-evidence" className={`workspace-panel workspace-evidence ${mobileOpen ? "mobile-open" : ""}`}
        aria-label="Evidence viewer">
        <div className="workspace-evidence-header">
            <span className="workspace-section-heading">Sources</span>
            <button type="button" className="workspace-evidence-close" onClick={onClose} aria-label="Close evidence">×</button>
        </div>
        {sourceIds.length > 1 && <div className="workspace-source-tabs" aria-label="Cited sources">
            {sourceIds.map((id,index) => <button type="button" key={id} aria-pressed={id === selectedChunkId}
                aria-label={`Source ${index + 1}, chunk ${id}`} onClick={() => onSelect(id)}>
                {index + 1}
            </button>)}
        </div>}
        {loading && <p className="workspace-evidence-placeholder" role="status">Loading source passage...</p>}
        {error && <p className="workspace-evidence-placeholder workspace-error" role="alert">{error}</p>}
        {!loading && !error && source && <div className="workspace-evidence-content">
            <h2>{source.document_title}</h2>
            <p className="workspace-evidence-meta">{source.department} · Passage {source.chunk_index + 1}</p>
            <blockquote className="workspace-evidence-excerpt">{overlap ?
                <>{source.content.slice(0,overlap.start)}<mark>{source.content.slice(overlap.start,overlap.end)}</mark>{source.content.slice(overlap.end)}</> :
                source.content}</blockquote>
            <p className="workspace-evidence-footnote">{overlap ?
                "Matching text is highlighted. Check the full passage before relying on the answer." :
                "Read the passage to assess the answer."}</p>
        </div>}
        {!loading && !error && !source && <div className="workspace-evidence-placeholder">
            <h2>No source selected</h2>
            <p>Open a source link in a reply to view its passage.</p>
        </div>}
    </aside>
}

export default EvidenceViewer
