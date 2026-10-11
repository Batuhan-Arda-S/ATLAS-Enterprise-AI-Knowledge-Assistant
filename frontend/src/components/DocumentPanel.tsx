import type { DocumentResponse } from "../types/document"


type DocumentPanelProps = {
    document: DocumentResponse | null
    loading: boolean
    error: string | null
}


function DocumentPanel({document,loading,error}: DocumentPanelProps) {
    if (loading) {
        return <section className="document-panel">Loading document...</section>
    }

    if (error) {
        return <section className="document-panel" role="alert">Error: {error}</section>
    }

    if (!document) {
        return <section className="document-panel">No document loaded.</section>
    }

    return (
        <section className="document-panel">
            <span className="panel-caption">LIVE BACKEND DOCUMENT</span>

            <h2>{document.title}</h2>
            <p className="document-department">{document.department} · Document #{document.id}</p>

            <p>{document.content.slice(0,250)}{document.content.length > 250 ? "..." : ""}</p>
        </section>
    )
}

export default DocumentPanel