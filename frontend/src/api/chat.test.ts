import { afterEach,expect,test,vi } from "vitest"
import { streamChat } from "./chat"

afterEach(() => vi.unstubAllGlobals())

function responseFrom(parts: Uint8Array[]) {
    return {ok:true,body:new ReadableStream<Uint8Array>({
        start(controller) {parts.forEach(part => controller.enqueue(part));controller.close()}
    })} as Response
}

test("combines split UTF-8 tokens and multiple SSE events before done",async () => {
    const encoded = new TextEncoder().encode(
        'event: token\r\ndata: {"text":"İzin " }\r\n\r\n' +
        'event: token\r\ndata: {"text":"var"}\r\n\r\n' +
        'event: done\r\ndata: {"answer":"İzin var [[chunk:7]].","answer_status":"answered","retrieval_status":"relevant","cited_sources":[{"chunk_id":7,"document_id":12,"chunk_index":0}]}\r\n\r\n'
    )
    const utf8Boundary = encoded.indexOf(0xc4) + 1
    const crBoundary = encoded.indexOf(13) + 1
    const parts = [encoded.slice(0,crBoundary),encoded.slice(crBoundary,utf8Boundary),
        encoded.slice(utf8Boundary,47),encoded.slice(47)]
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue(responseFrom(parts)))
    const tokens: string[] = []
    const done = await streamChat(4,"Question?","token",text => tokens.push(text))
    expect(tokens).toEqual(["İzin ","var"])
    expect(done.answer_status).toBe("answered")
    expect(done.cited_sources[0].chunk_id).toBe(7)
})

test("rejects an error event after provisional tokens",async () => {
    const bytes = new TextEncoder().encode(
        'event: token\ndata: {"text":"Partial"}\n\nevent: error\ndata: {"message":"Citation check failed"}\n\n')
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue(responseFrom([bytes])))
    const tokens: string[] = []
    await expect(streamChat(4,"Question?","token",text => tokens.push(text)))
        .rejects.toThrow("Citation check failed")
    expect(tokens).toEqual(["Partial"])
})

test("rejects a truncated stream without done",async () => {
    const bytes = new TextEncoder().encode('event: token\ndata: {"text":"Partial"}\n\n')
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue(responseFrom([bytes])))
    await expect(streamChat(4,"Question?","token",() => {}))
        .rejects.toThrow("before completion")
})

test("accepts an abstention only after a done event",async () => {
    const bytes = new TextEncoder().encode(
        'event: done\ndata: {"answer":null,"answer_status":"no_candidates","retrieval_status":"no_candidates","cited_sources":[]}\n\n')
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue(responseFrom([bytes])))
    const done = await streamChat(4,"Question?","token",() => {})
    expect(done.answer_status).toBe("no_candidates")
    expect(done.answer).toBeNull()
})
