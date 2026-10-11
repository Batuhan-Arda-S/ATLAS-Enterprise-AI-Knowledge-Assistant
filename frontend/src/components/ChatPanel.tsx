import { useState } from "react"
import type { FormEvent,KeyboardEvent } from "react"
import type { Message } from "../types/chat"
import type { DocumentResponse } from "../types/document"

type Props = {
    document: DocumentResponse | null
    documentLoading?: boolean
    messages: Message[]
    loading: boolean
    error: string | null
    sending: boolean
    onSend: (question: string) => Promise<void>
    onSourceSelect: (chunkId: number) => void
}

function citedIds(message: Message) {
    if (!message.content || message.pending || message.failed) return []
    const verified = new Set(message.cited_chunk_ids ?? [])
    return [...new Set([...message.content.matchAll(/\[\[chunk:(\d+)\]\]/g)]
        .map(match => Number(match[1])).filter(id => verified.has(id)))]
}

function answerContent(message: Message) {
    if (!message.content) return null
    if (message.pending || message.failed) return message.content
    return message.content.replace(/[ \t]*\[\[chunk:\d+\]\]/g,"")
}

function ChatPanel({document,documentLoading = false,messages,loading,error,sending,onSend,onSourceSelect}: Props) {
    const [draft,setDraft] = useState("")

    function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        if (!draft.trim() || sending || !document || (document.processing_status && document.processing_status !== "processed")) return
        const question = draft.trim()
        setDraft("")
        void onSend(question)
    }

    function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
        if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault()
            event.currentTarget.form?.requestSubmit()
        }
    }

    const ready = document && (!document.processing_status || document.processing_status === "processed")

    return <main className="workspace-panel workspace-chat" aria-label="Policy assistant">
        <header className="workspace-chat-header">
            <div>
                <h1>Policy Assistant</h1>
                <span className="workspace-chat-header-context">{document ? `${document.title} · ${document.department}` :
                    documentLoading ? "Loading document…" : "Select a document"}</span>
            </div>
            {document?.processing_status && document.processing_status !== "processed" &&
                <span className="workspace-chat-header-status">{document.processing_status}</span>}
        </header>
        <div className="workspace-conversation">
            {loading && <p className="workspace-chat-state" role="status">Loading conversation…</p>}
            {documentLoading && <p className="workspace-chat-state" role="status">Loading document…</p>}
            {error && <p className="workspace-chat-state workspace-error" role="alert">{error}</p>}
            {!loading && !documentLoading && messages.length === 0 && <div className="workspace-empty-state">
                <h2>{document ? "Ask about this document" : "Select a document"}</h2>
                {!document && <p>Choose or upload a document to begin.</p>}
            </div>}
            {messages.length > 0 && <div className="workspace-message-column" aria-live="polite">
                {messages.map(message => {
                    if (message.role === "user") return <div key={message.id} className="workspace-user-row">
                        <span className="workspace-speaker">You</span>
                        <div className="workspace-user-message">{message.content}</div>
                    </div>
                    const sources = citedIds(message)
                    return <article key={message.id} className="workspace-assistant-message">
                        <span className="workspace-speaker workspace-assistant-label">Atlas</span>
                        <div className="workspace-assistant-body">
                            {message.answer_status === "no_candidates" && <p>No relevant passages were found in this document.</p>}
                            {message.answer_status === "insufficient_evidence" && <p>The retrieved passages do not support an answer.</p>}
                            {message.content && <p>{answerContent(message)}</p>}
                            {sources.length > 0 && <div className="workspace-source-list" aria-label="Answer sources">
                                {sources.map((chunkId,index) => <button key={chunkId} type="button"
                                    className="workspace-source-link" aria-label={`Open source #${chunkId}`}
                                    title={`Source preview · ${document?.title ?? "Document"}`}
                                    onClick={() => onSourceSelect(chunkId)}>
                                    <span className="workspace-source-arrow" aria-hidden="true">↪</span>
                                    <span>Source preview · {document?.title ?? "Document"}{sources.length > 1 ? ` · ${index + 1}` : ""}</span>
                                </button>)}
                            </div>}
                            {message.pending && <span className="workspace-message-status">Checking the source passages…</span>}
                            {message.failed && <span className="workspace-message-error">Response failed. The partial text is unverified.</span>}
                        </div>
                    </article>
                })}
            </div>}
        </div>
        <div className="workspace-composer-area">
            <form className="workspace-composer" onSubmit={handleSubmit}>
                <textarea value={draft} onChange={event => setDraft(event.target.value)}
                    onKeyDown={handleKeyDown} rows={2} placeholder="Ask about this document…"
                    aria-label="Ask about this document" disabled={!ready || sending} />
                <button type="submit" disabled={!draft.trim() || !ready || sending}
                    aria-label="Send message">{sending ? "…" : "Send"}</button>
            </form>
            {(sending || document?.processing_status === "failed" || document?.processing_status === "pending") &&
                <p className="workspace-composer-caption">{sending ? "Composing answer…" :
                document?.processing_status === "failed" ? "This document could not be processed." :
                "This document is still processing."}</p>}
        </div>
    </main>
}

export default ChatPanel
