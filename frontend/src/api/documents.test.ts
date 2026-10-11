import { afterEach, describe, expect, it, vi } from "vitest"

import { getDocument } from "./documents"


afterEach(() => vi.unstubAllGlobals())

describe("getDocument", () => {
    it("requests the document with the abort signal and returns JSON", async () => {
        const document = {id: 12,title: "Policy",department: "HR",content: "Document text"}
        const fetchMock = vi.fn().mockResolvedValue({
            ok: true,
            json: vi.fn().mockResolvedValue(document)
        })
        const controller = new AbortController()
        vi.stubGlobal("fetch",fetchMock)

        await expect(getDocument(12,"test-token",controller.signal)).resolves.toEqual(document)
        expect(fetchMock).toHaveBeenCalledWith(
            "http://127.0.0.1:8000/documents/12",
            {signal: controller.signal,headers:{Authorization:"Bearer test-token"}}
        )
    })

    it.each([404,500])("reports HTTP %i", async status => {
        vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok: false,status}))

        await expect(getDocument(12,"test-token")).rejects.toThrow(`Request failed (${status})`)
    })
})
