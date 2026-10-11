import { ApiError } from "./auth"
import { API_URL,apiRequest } from "./client"
import type { Conversation,ConversationDetail,StreamDone } from "../types/chat"

export function listConversations(token: string,signal?: AbortSignal) {
    return apiRequest<Conversation[]>("/chat/",token,{signal})
}

export function createConversation(documentId: number,token: string,title: string,signal?: AbortSignal) {
    return apiRequest<Conversation>("/chat/",token,{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({document_id:documentId,title:title.slice(0,200)}),signal,
    })
}

export function getConversation(id: number,token: string,signal?: AbortSignal) {
    return apiRequest<ConversationDetail>(`/chat/${id}`,token,{signal})
}

export async function streamChat(id: number,question: string,token: string,
                                 onToken: (text: string) => void,signal?: AbortSignal): Promise<StreamDone> {
    const response = await fetch(`${API_URL}/chat/${id}/stream`,{
        method:"POST",headers:{Authorization:`Bearer ${token}`,"Content-Type":"application/json"},
        body:JSON.stringify({question}),signal,
    })
    if (!response.ok) throw new ApiError(`Chat request failed (${response.status})`,response.status)
    if (!response.body) throw new Error("Chat stream is unavailable")

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ""
    let done: StreamDone | null = null

    function processFrame(frame: string) {
        const lines = frame.split(/\r\n|\n|\r/)
        const event = lines.find(line => line.startsWith("event:"))?.slice(6).trim()
        const data = lines.filter(line => line.startsWith("data:"))
            .map(line => line.slice(5).trimStart()).join("\n")
        if (!event || !data) return
        let value: unknown
        try { value = JSON.parse(data) } catch { throw new Error("Invalid chat stream data") }
        if (!value || typeof value !== "object") throw new Error("Invalid chat stream data")
        const payload = value as Record<string,unknown>
        if (event === "token") {
            if (typeof payload.text !== "string") throw new Error("Invalid chat token")
            if (!done) onToken(payload.text)
        } else if (event === "error") {
            throw new Error(typeof payload.message === "string" ? payload.message : "Chat streaming failed")
        } else if (event === "done") {
            const status = payload.answer_status
            const sources = payload.cited_sources
            if (!Array.isArray(sources) ||
                !sources.every(source => source && typeof source.chunk_id === "number" &&
                    typeof source.document_id === "number" && typeof source.chunk_index === "number") ||
                !["answered","no_candidates","insufficient_evidence"].includes(String(status)) ||
                (status === "answered" && (typeof payload.answer !== "string" || sources.length === 0)) ||
                (status !== "answered" && payload.answer !== null)) {
                throw new Error("Invalid chat completion")
            }
            done = payload as StreamDone
        }
    }

    function processBuffer() {
        let boundary = /\r\n\r\n|\n\n|\r\r/.exec(buffer)
        while (boundary && boundary.index !== undefined) {
            const frame = buffer.slice(0,boundary.index)
            buffer = buffer.slice(boundary.index + boundary[0].length)
            processFrame(frame)
            boundary = /\r\n\r\n|\n\n|\r\r/.exec(buffer)
        }
    }

    try {
        while (true) {
            const chunk = await reader.read()
            if (chunk.done) break
            buffer += decoder.decode(chunk.value,{stream:true})
            processBuffer()
        }
        buffer += decoder.decode()
        processBuffer()
        if (buffer.trim()) processFrame(buffer)
        if (!done) throw new Error("Chat stream ended before completion")
        return done
    } finally {
        reader.releaseLock()
    }
}
