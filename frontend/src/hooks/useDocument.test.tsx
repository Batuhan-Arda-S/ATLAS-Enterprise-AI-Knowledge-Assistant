// @vitest-environment jsdom

import { afterEach,expect,test,vi } from "vitest"
import { cleanup,renderHook,waitFor } from "@testing-library/react"

import { useDocument } from "./useDocument"
import { getDocument } from "../api/documents"


vi.mock("../api/documents",() => ({
    getDocument: vi.fn()
}))


afterEach(() => {
    cleanup()
    vi.resetAllMocks()
})


test("loads a document successfully",async () => {
    vi.mocked(getDocument).mockResolvedValue({
        id:12,title:"Remote Work Policy",department:"HR",content:"Remote work rules"
    })

    const {result} = renderHook(() => useDocument(12,"test-token"))

    await waitFor(() => {
        expect(result.current.status).toBe("success")
    })

    expect(result.current.document?.id).toBe(12)
    expect(result.current.error).toBeNull()
})


test("handles document loading failure",async () => {
    vi.mocked(getDocument).mockRejectedValue(new Error("Document request failed (404)"))

    const {result} = renderHook(() => useDocument(999,"test-token"))

    await waitFor(() => {
        expect(result.current.status).toBe("error")
    })

    expect(result.current.error).toBe("Document request failed (404)")
    expect(result.current.document).toBeNull()
})


test("does not display the previous document while loading another",async () => {
    vi.mocked(getDocument).mockImplementation(async documentId => ({
        id:documentId,title:`Document ${documentId}`,department:"HR",content:"Test content"
    }))

    const {result,rerender} = renderHook(
        ({documentId}) => useDocument(documentId,"test-token"),
        {initialProps:{documentId:12}}
    )

    await waitFor(() => {
        expect(result.current.document?.id).toBe(12)
    })

    rerender({documentId:13})

    expect(result.current.status).toBe("loading")
    expect(result.current.document).toBeNull()

    await waitFor(() => {
        expect(result.current.document?.id).toBe(13)
    })
})


test("aborts the request when the component unmounts",() => {
    let signal: AbortSignal | undefined

    vi.mocked(getDocument).mockImplementation((_documentId,_token,requestSignal) => {
        signal = requestSignal
        return new Promise(() => {})
    })

    const {unmount} = renderHook(() => useDocument(12,"test-token"))

    unmount()

    expect(signal?.aborted).toBe(true)
})
