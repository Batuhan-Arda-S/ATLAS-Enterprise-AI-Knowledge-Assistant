export type DocumentResponse = {
    id: number
    title: string
    department: string
    content: string
    filename?: string | null
    content_type?: string | null
    file_size?: number | null
    processing_status?: "pending" | "processed" | "failed"
    created_at?: string
    updated_at?: string
}

export type DocumentUploadResponse = Pick<DocumentResponse,"id" | "title" | "department" | "filename" | "content_type" | "file_size" | "processing_status">

export type SourceResponse = {
    chunk_id: number
    document_id: number
    chunk_index: number
    content: string
    document_title: string
    department: string
}
