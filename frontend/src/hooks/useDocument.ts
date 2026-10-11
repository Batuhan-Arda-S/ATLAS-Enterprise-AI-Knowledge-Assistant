import { useEffect, useState } from "react"

import { getDocument } from "../api/documents"
import type { DocumentResponse } from "../types/document"


type DocumentState =
    | { documentId: number; status: "loading"; document: null; error: null }
    | { documentId: number; status: "success"; document: DocumentResponse; error: null }
    | { documentId: number; status: "error"; document: null; error: string }


export function useDocument(documentId: number,token: string) {
    const [state,setState] = useState<DocumentState>({
        documentId, status: "loading", document: null, error: null
    })

    useEffect(() => {
        const controller = new AbortController()

        async function loadDocument() {
            try {
                const document = await getDocument(documentId,token,controller.signal)

                if (!controller.signal.aborted) {
                    setState({documentId,status:"success",document,error:null})
                }
            } catch (error) {
                if (controller.signal.aborted) return

                const message = error instanceof Error ? error.message : "Document could not be loaded"

                setState({documentId,status:"error",document:null,error:message})
            }
        }

        void loadDocument()

        return () => controller.abort()
    }, [documentId,token])

    if (state.documentId !== documentId) {
        return {status:"loading" as const,document:null,error:null}
    }

    return state
}
