import { apiRequest } from "./client"
import type { DocumentResponse,DocumentUploadResponse,SourceResponse } from "../types/document"

type DocumentList = {items: DocumentResponse[];total: number;offset: number;limit: number}

export async function listDocuments(token: string,signal?: AbortSignal): Promise<DocumentResponse[]> {
    const items: DocumentResponse[] = []
    for (let offset = 0; ; offset += 100) {
        const page = await apiRequest<DocumentList>(`/documents/?offset=${offset}&limit=100`,token,{signal})
        items.push(...page.items)
        if (items.length >= page.total || page.items.length === 0) return items
    }
}

export function getDocument(documentId: number,token: string,signal?: AbortSignal) {
    return apiRequest<DocumentResponse>(`/documents/${documentId}`,token,{signal})
}

export function getSource(documentId: number,chunkId: number,token: string,signal?: AbortSignal) {
    return apiRequest<SourceResponse>(`/documents/${documentId}/chunks/${chunkId}`,token,{signal})
}

export function uploadDocument(token: string,title: string,department: string,file: File) {
    const body = new FormData()
    body.append("title",title.trim())
    body.append("department",department.trim())
    body.append("file",file)
    return apiRequest<DocumentUploadResponse>("/documents/upload",token,{method:"POST",body})
}

export function updateDocument(documentId: number,token: string,title: string,department: string) {
    return apiRequest<DocumentResponse>(`/documents/${documentId}`,token,{
        method:"PATCH",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({title:title.trim(),department:department.trim()}),
    })
}

export function deleteDocument(documentId: number,token: string) {
    return apiRequest<{message: string}>(`/documents/${documentId}`,token,{method:"DELETE"})
}
