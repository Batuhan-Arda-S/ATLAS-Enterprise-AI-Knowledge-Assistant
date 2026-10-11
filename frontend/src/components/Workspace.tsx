import { useEffect,useRef,useState } from "react"

import Brand from "./Brand"
import ChatPanel from "./ChatPanel"
import EvidenceViewer from "./EvidenceViewer"
import WorkspaceSidebar from "./WorkspaceSidebar"
import { ApiError } from "../api/auth"
import { createConversation,getConversation,listConversations,streamChat } from "../api/chat"
import { deleteDocument,getDocument,getSource,listDocuments,updateDocument,uploadDocument } from "../api/documents"
import type { CurrentUser } from "../types/auth"
import type { Conversation,Message } from "../types/chat"
import type { DocumentResponse,SourceResponse } from "../types/document"
import "../Workspace.css"

type Props = {user: CurrentUser;token: string;onLogout: () => void}

function errorMessage(error: unknown) {
    if (error instanceof ApiError && error.status === 403) return "Access forbidden for this account."
    return error instanceof Error ? error.message : "Request failed"
}

function Workspace({user,token,onLogout}: Props) {
    const [documents,setDocuments] = useState<DocumentResponse[]>([])
    const [documentsLoading,setDocumentsLoading] = useState(true)
    const [documentsError,setDocumentsError] = useState<string | null>(null)
    const [selectedDocumentId,setSelectedDocumentId] = useState<number | null>(null)
    const [document,setDocument] = useState<DocumentResponse | null>(null)
    const [conversations,setConversations] = useState<Conversation[]>([])
    const [conversationsError,setConversationsError] = useState<string | null>(null)
    const [selectedConversationId,setSelectedConversationId] = useState<number | null>(null)
    const [messages,setMessages] = useState<Message[]>([])
    const [historyLoading,setHistoryLoading] = useState(false)
    const [chatError,setChatError] = useState<string | null>(null)
    const [sending,setSending] = useState(false)
    const [selectedChunkId,setSelectedChunkId] = useState<number | null>(null)
    const [sourceIds,setSourceIds] = useState<number[]>([])
    const [source,setSource] = useState<SourceResponse | null>(null)
    const [sourceLoading,setSourceLoading] = useState(false)
    const [sourceError,setSourceError] = useState<string | null>(null)
    const [mobilePanel,setMobilePanel] = useState<"library" | "evidence" | null>(null)
    const [refreshKey,setRefreshKey] = useState(0)
    const streamController = useRef<AbortController | null>(null)
    const sendingRef = useRef(false)
    const localConversationId = useRef<number | null>(null)

    useEffect(() => {
        const controller = new AbortController()
        queueMicrotask(() => {if (!controller.signal.aborted) setDocumentsLoading(true)})
        void listDocuments(token,controller.signal).then(items => {
            if (controller.signal.aborted) return
            setDocuments(items)
            setDocumentsError(null)
            setSelectedDocumentId(current => current && items.some(item => item.id === current) ? current : items[0]?.id ?? null)
        }).catch(error => {
            if (controller.signal.aborted) return
            if (error instanceof ApiError && error.status === 401) onLogout()
            else setDocumentsError(errorMessage(error))
        }).finally(() => { if (!controller.signal.aborted) setDocumentsLoading(false) })
        return () => controller.abort()
    },[token,refreshKey,onLogout])

    useEffect(() => {
        const controller = new AbortController()
        void listConversations(token,controller.signal).then(items => {
            if (!controller.signal.aborted) {setConversations(items);setConversationsError(null)}
        }).catch(error => {
            if (controller.signal.aborted) return
            if (error instanceof ApiError && error.status === 401) onLogout()
            else setConversationsError(errorMessage(error))
        })
        return () => controller.abort()
    },[token,refreshKey,onLogout])

    useEffect(() => {
        if (selectedDocumentId === null) return
        const controller = new AbortController()
        void getDocument(selectedDocumentId,token,controller.signal).then(item => {
            if (!controller.signal.aborted) setDocument(item)
        }).catch(error => {
            if (controller.signal.aborted) return
            if (error instanceof ApiError && error.status === 401) onLogout()
            else setDocumentsError(errorMessage(error))
        })
        return () => controller.abort()
    },[selectedDocumentId,token,refreshKey,onLogout])

    useEffect(() => {
        if (selectedConversationId === null || localConversationId.current === selectedConversationId) return
        const controller = new AbortController()
        queueMicrotask(() => {
            if (!controller.signal.aborted) {setHistoryLoading(true);setChatError(null)}
        })
        void getConversation(selectedConversationId,token,controller.signal).then(item => {
            if (controller.signal.aborted) return
            if (item.document_id !== selectedDocumentId) {
                setChatError("Conversation belongs to another document.")
                return
            }
            setMessages(item.messages)
        }).catch(error => {
            if (controller.signal.aborted) return
            if (error instanceof ApiError && error.status === 401) onLogout()
            else setChatError(errorMessage(error))
        }).finally(() => {if (!controller.signal.aborted) setHistoryLoading(false)})
        return () => controller.abort()
    },[selectedConversationId,selectedDocumentId,token,onLogout])

    useEffect(() => {
        if (selectedChunkId === null || selectedDocumentId === null) return
        const controller = new AbortController()
        queueMicrotask(() => {
            if (!controller.signal.aborted) {setSourceLoading(true);setSourceError(null)}
        })
        void getSource(selectedDocumentId,selectedChunkId,token,controller.signal).then(item => {
            if (!controller.signal.aborted) setSource(item)
        }).catch(error => {
            if (controller.signal.aborted) return
            if (error instanceof ApiError && error.status === 401) onLogout()
            else setSourceError(errorMessage(error))
        }).finally(() => {if (!controller.signal.aborted) setSourceLoading(false)})
        return () => controller.abort()
    },[selectedDocumentId,selectedChunkId,token,onLogout])

    useEffect(() => () => {
        streamController.current?.abort()
        streamController.current = null
    },[])

    useEffect(() => {
        if (!mobilePanel) return
        const closeOnEscape = (event: globalThis.KeyboardEvent) => {
            if (event.key === "Escape") setMobilePanel(null)
        }
        window.addEventListener("keydown",closeOnEscape)
        return () => window.removeEventListener("keydown",closeOnEscape)
    },[mobilePanel])

    function resetChat() {
        streamController.current?.abort()
        streamController.current = null
        sendingRef.current = false
        localConversationId.current = null
        setSending(false)
        setSelectedConversationId(null)
        setMessages([])
        setChatError(null)
        setSelectedChunkId(null)
        setSourceIds([])
        setSource(null)
        setMobilePanel(null)
    }

    function selectDocument(id: number) {
        if (id !== selectedDocumentId) {resetChat();setSelectedDocumentId(id)}
        setMobilePanel(null)
    }

    function selectConversation(item: Conversation) {
        if (item.id === selectedConversationId) {setMobilePanel(null);return}
        resetChat()
        setSelectedDocumentId(item.document_id)
        setSelectedConversationId(item.id)
    }

    async function handleUpload(title: string,department: string,file: File) {
        let uploaded
        try {uploaded = await uploadDocument(token,title,department,file)}
        catch (error) {
            if (error instanceof ApiError && error.status === 401) onLogout()
            throw error
        }
        setRefreshKey(value => value + 1)
        resetChat()
        setSelectedDocumentId(uploaded.id)
        if (uploaded.processing_status === "failed") throw new Error("The file uploaded, but text extraction failed.")
    }

    async function handleUpdate(id: number,title: string,department: string) {
        let updated
        try {updated = await updateDocument(id,token,title,department)}
        catch (error) {
            if (error instanceof ApiError && error.status === 401) onLogout()
            throw error
        }
        setDocuments(current => current.map(item => item.id === id ? updated : item))
        if (selectedDocumentId === id) setDocument(updated)
    }

    async function handleDelete(id: number) {
        try {await deleteDocument(id,token)}
        catch (error) {
            if (error instanceof ApiError && error.status === 401) onLogout()
            throw error
        }
        resetChat()
        setSelectedDocumentId(null)
        setDocuments(current => current.filter(item => item.id !== id))
        setRefreshKey(value => value + 1)
    }

    function selectSource(chunkId: number) {
        const message = [...messages].reverse().find(item => item.cited_chunk_ids?.includes(chunkId))
        setSourceIds(message?.cited_chunk_ids ?? [chunkId])
        setSelectedChunkId(chunkId)
        setMobilePanel("evidence")
    }

    async function handleSend(question: string) {
        if (sendingRef.current || !selectedDocumentId || !question.trim()) return
        sendingRef.current = true
        setSending(true)
        setChatError(null)
        const controller = new AbortController()
        streamController.current = controller
        const userId = `user-${Date.now()}`
        const assistantId = `assistant-${Date.now()}`
        setMessages(current => [...current,
            {id:userId,role:"user",content:question,answer_status:null,cited_chunk_ids:null},
            {id:assistantId,role:"assistant",content:"",answer_status:null,cited_chunk_ids:null,pending:true}])
        const timeout = window.setTimeout(() => controller.abort(),180000)
        try {
            let conversationId = selectedConversationId
            if (conversationId === null) {
                const created = await createConversation(selectedDocumentId,token,question,controller.signal)
                if (controller.signal.aborted) return
                conversationId = created.id
                localConversationId.current = created.id
                setSelectedConversationId(created.id)
                setRefreshKey(value => value + 1)
            }
            const result = await streamChat(conversationId,question,token,text => {
                if (controller.signal.aborted) return
                setMessages(current => current.map(item => item.id === assistantId ?
                    {...item,content:(item.content ?? "") + text} : item))
            },controller.signal)
            if (controller.signal.aborted) return
            setMessages(current => current.map(item => item.id === assistantId ?
                {...item,content:result.answer,answer_status:result.answer_status,
                    cited_chunk_ids:result.cited_sources.map(source => source.chunk_id),pending:false} : item))
            setRefreshKey(value => value + 1)
        } catch (error) {
            if (controller.signal.aborted && streamController.current !== controller) return
            if (error instanceof ApiError && error.status === 401) onLogout()
            const message = controller.signal.aborted ? "Chat request timed out or was cancelled." : errorMessage(error)
            setChatError(message)
            setMessages(current => current.map(item => item.id === assistantId ?
                {...item,pending:false,failed:true} : item))
        } finally {
            window.clearTimeout(timeout)
            if (streamController.current === controller) {
                streamController.current = null
                sendingRef.current = false
                setSending(false)
            }
        }
    }

    return <div className="workspace-page">
        <div className="workspace-frame">
            <header className="workspace-topbar">
                <div className="workspace-brand-group">
                    <button type="button" className="workspace-mobile-menu" onClick={() => setMobilePanel(mobilePanel === "library" ? null : "library")}
                        aria-label={mobilePanel === "library" ? "Close library" : "Open library"}
                        aria-expanded={mobilePanel === "library"} aria-controls="workspace-library">☰</button>
                    <Brand />
                </div>
                <div className="workspace-session">
                    <button type="button" className="workspace-mobile-evidence" onClick={() => setMobilePanel("evidence")}
                        aria-expanded={mobilePanel === "evidence"} aria-controls="workspace-evidence">Sources</button>
                    <span className="workspace-session-email">{user.email}</span>
                    <button type="button" onClick={onLogout}>Sign out</button>
                </div>
            </header>
            {mobilePanel && <button type="button" className={`workspace-mobile-scrim ${mobilePanel}`}
                aria-label="Close panel" onClick={() => setMobilePanel(null)} />}
            <div className="workspace-grid">
                <WorkspaceSidebar documents={documents} documentsLoading={documentsLoading} documentsError={documentsError}
                    selectedDocumentId={selectedDocumentId} onSelectDocument={selectDocument} onUpload={handleUpload}
                    onUpdate={handleUpdate} onDelete={handleDelete}
                    conversations={conversations} conversationsError={conversationsError}
                    selectedConversationId={selectedConversationId} onSelectConversation={selectConversation}
                    onNewChat={resetChat} mobileOpen={mobilePanel === "library"} />
                <ChatPanel document={document?.id === selectedDocumentId ? document : null}
                    documentLoading={selectedDocumentId !== null && document?.id !== selectedDocumentId && !documentsError}
                    messages={messages} loading={historyLoading} error={chatError}
                    sending={sending} onSend={handleSend} onSourceSelect={selectSource} />
                <EvidenceViewer source={source?.chunk_id === selectedChunkId && source.document_id === selectedDocumentId ? source : null}
                    answer={[...messages].reverse().find(item => item.cited_chunk_ids?.includes(selectedChunkId ?? -1))?.content ?? null}
                    sourceIds={sourceIds} selectedChunkId={selectedChunkId}
                    loading={sourceLoading} error={sourceError} onSelect={selectSource}
                    mobileOpen={mobilePanel === "evidence"} onClose={() => setMobilePanel(null)} />
            </div>
        </div>
    </div>
}

export default Workspace
