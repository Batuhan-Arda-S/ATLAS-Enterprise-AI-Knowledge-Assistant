import { useState } from "react"
import type { FormEvent } from "react"
import type { Conversation } from "../types/chat"
import type { DocumentResponse } from "../types/document"

type Props = {
    documents: DocumentResponse[]
    documentsLoading: boolean
    documentsError: string | null
    selectedDocumentId: number | null
    onSelectDocument: (id: number) => void
    onUpload: (title: string,department: string,file: File) => Promise<void>
    onUpdate: (id: number,title: string,department: string) => Promise<void>
    onDelete: (id: number) => Promise<void>
    conversations: Conversation[]
    conversationsError: string | null
    selectedConversationId: number | null
    onSelectConversation: (conversation: Conversation) => void
    onNewChat: () => void
    mobileOpen: boolean
}

function WorkspaceSidebar({documents,documentsLoading,documentsError,selectedDocumentId,
                           onSelectDocument,onUpload,onUpdate,onDelete,conversations,conversationsError,
                           selectedConversationId,onSelectConversation,onNewChat,mobileOpen}: Props) {
    const [department,setDepartment] = useState("All documents")
    const [uploadOpen,setUploadOpen] = useState(false)
    const [title,setTitle] = useState("")
    const [uploadDepartment,setUploadDepartment] = useState("")
    const [file,setFile] = useState<File | null>(null)
    const [uploading,setUploading] = useState(false)
    const [uploadError,setUploadError] = useState<string | null>(null)
    const [uploadNotice,setUploadNotice] = useState<string | null>(null)
    const [editingId,setEditingId] = useState<number | null>(null)
    const [editTitle,setEditTitle] = useState("")
    const [editDepartment,setEditDepartment] = useState("")
    const [managing,setManaging] = useState(false)
    const [manageError,setManageError] = useState<string | null>(null)
    const departments = ["All documents",...new Set(documents.map(item => item.department))]
    const filtered = department === "All documents" ? documents : documents.filter(item => item.department === department)
    const selected = documents.find(item => item.id === selectedDocumentId)

    async function submitUpload(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        if (!file || !title.trim() || !uploadDepartment.trim()) return
        setUploading(true)
        setUploadError(null)
        setUploadNotice(null)
        try {
            await onUpload(title,uploadDepartment,file)
            setUploadNotice("Document uploaded and added to the library.")
            setTitle("")
            setFile(null)
            setDepartment("All documents")
            setUploadOpen(false)
        } catch (error) {
            setUploadError(error instanceof Error ? error.message : "Upload failed")
        } finally { setUploading(false) }
    }

    async function saveChanges(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        if (editingId === null || !editTitle.trim() || !editDepartment.trim()) return
        setManaging(true)
        setManageError(null)
        try {
            await onUpdate(editingId,editTitle,editDepartment)
            setEditingId(null)
            setDepartment("All documents")
        } catch (error) {
            setManageError(error instanceof Error ? error.message : "Update failed")
        } finally {setManaging(false)}
    }

    async function removeDocument() {
        if (editingId === null || !window.confirm("Delete this document? This cannot be undone.")) return
        setManaging(true)
        setManageError(null)
        try {
            await onDelete(editingId)
            setEditingId(null)
        } catch (error) {
            setManageError(error instanceof Error ? error.message : "Delete failed")
        } finally {setManaging(false)}
    }

    return <aside id="workspace-library" className={`workspace-panel workspace-sidebar ${mobileOpen ? "mobile-open" : ""}`} aria-label="Workspace navigation">
        <div className="workspace-sidebar-top">
            <span className="workspace-section-heading">Documents</span>
            <button className="workspace-new-chat" type="button" onClick={onNewChat} aria-label="New chat">
                <span aria-hidden="true">+</span> New chat
            </button>
        </div>
        {documentsLoading && <p className="sidebar-note" role="status">Loading documents...</p>}
        {documentsError && <p className="sidebar-error" role="alert">{documentsError}</p>}
        {!documentsLoading && !documentsError && documents.length === 0 && <p className="sidebar-note">No documents yet. Upload one to start.</p>}
        {documents.length > 0 && <div className="workspace-category-list" aria-label="Department filters">
            {departments.map(item => <button key={item} type="button" className="workspace-category"
                aria-pressed={department === item} onClick={() => setDepartment(item)}>{item}</button>)}
        </div>}
        <div className="workspace-document-list" aria-label="Documents">
            {filtered.map(item => <button key={item.id} type="button" className="workspace-document-button"
                aria-current={selectedDocumentId === item.id ? "page" : undefined}
                onClick={() => onSelectDocument(item.id)}>
                <span className="workspace-document-title">{item.title}</span>
                <span className="workspace-document-meta">{item.department}{item.processing_status && item.processing_status !== "processed" ? ` · ${item.processing_status}` : ""}</span>
            </button>)}
            {documents.length > 0 && filtered.length === 0 && <p className="sidebar-note">No documents in this department.</p>}
        </div>
        {selected && <button type="button" className="workspace-manage-toggle" onClick={() => {
            setEditingId(editingId === selected.id ? null : selected.id)
            setEditTitle(selected.title)
            setEditDepartment(selected.department)
            setManageError(null)
        }}>Edit document details</button>}
        {selected && editingId === selected.id && <form className="workspace-upload-form" onSubmit={saveChanges}>
            <label>Document title<input value={editTitle} onChange={event => setEditTitle(event.target.value)}
                required maxLength={225} /></label>
            <label>Document department<input value={editDepartment}
                onChange={event => setEditDepartment(event.target.value)} required maxLength={100} /></label>
            <button type="submit" disabled={managing || !editTitle.trim() || !editDepartment.trim()}>Save changes</button>
            <button type="button" className="workspace-delete-button" disabled={managing}
                onClick={() => void removeDocument()}>Delete document</button>
            {manageError && <p role="alert" className="sidebar-error">{manageError}</p>}
        </form>}
        <button type="button" className="workspace-upload-toggle" onClick={() => setUploadOpen(!uploadOpen)}
            aria-expanded={uploadOpen}>Upload document <span aria-hidden="true">{uploadOpen ? "−" : "+"}</span></button>
        {uploadNotice && <p role="status" className="sidebar-note">{uploadNotice}</p>}
        {uploadOpen && <form className="workspace-upload-form" onSubmit={submitUpload}>
            <label>Title<input value={title} onChange={event => setTitle(event.target.value)} required maxLength={225} /></label>
            <label>Department<input value={uploadDepartment} onChange={event => setUploadDepartment(event.target.value)} required maxLength={100} /></label>
            <label>File<input type="file" accept=".pdf,.docx,.txt,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={event => setFile(event.target.files?.[0] ?? null)} required={!file} /></label>
            <button type="submit" disabled={uploading || !file || !title.trim() || !uploadDepartment.trim()}>{uploading ? "Uploading..." : "Upload"}</button>
            {uploadError && <p role="alert" className="sidebar-error">{uploadError}</p>}
        </form>}
        <div className="workspace-sidebar-divider" />
        <div className="workspace-nav-label">Recent chats</div>
        {conversationsError && <p role="alert" className="sidebar-error">{conversationsError}</p>}
        <nav className="workspace-recent-list" aria-label="Recent conversations">
            {conversations.map(item => <button key={item.id} type="button" className="workspace-recent-button"
                aria-current={selectedConversationId === item.id ? "page" : undefined}
                onClick={() => onSelectConversation(item)}>{item.title || `Chat #${item.id}`}</button>)}
            {conversations.length === 0 && !conversationsError && <p className="sidebar-note">No conversations yet.</p>}
        </nav>
    </aside>
}

export default WorkspaceSidebar
