import type { SourcePreview } from "../types/source"


type EvidencePreviewProps = {
    sources: SourcePreview[]
    selectedSource: SourcePreview
    onSelect: (chunkId: number) => void
}


function EvidencePreview({sources,selectedSource,onSelect}: EvidencePreviewProps) {
    return (
        <aside className="evidence-preview">
            <div className="evidence-header">
                <span>EXAMPLE SOURCES</span>
                <span>{selectedSource.chunkId} / EVIDENCE</span>
            </div>

            <div className="source-options" aria-label="Example sources">
                {sources.map(source => (
                    <button key={source.chunkId}
                            type="button"
                            className="source-option"
                            aria-pressed={source.chunkId === selectedSource.chunkId}
                            onClick={() => onSelect(source.chunkId)}>
                        {source.title}
                    </button>
                ))}
            </div>

            <h2>{selectedSource.title}</h2>
            <p>{selectedSource.excerpt}</p>

            <div className="source-reference">
                Source reference · chunk:{selectedSource.chunkId}
            </div>
        </aside>
    )
}

export default EvidencePreview