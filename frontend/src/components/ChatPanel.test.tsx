// @vitest-environment jsdom

import { afterEach,expect,test,vi } from "vitest"
import { cleanup,fireEvent,render,screen } from "@testing-library/react"
import ChatPanel from "./ChatPanel"

const document = {id:1,title:"Policy",department:"HR",content:"Policy text",processing_status:"processed" as const}
afterEach(cleanup)

test("blocks blank questions and submits trimmed text",() => {
    const onSend = vi.fn().mockResolvedValue(undefined)
    render(<ChatPanel document={document} messages={[]} loading={false} error={null}
        sending={false} onSend={onSend} onSourceSelect={vi.fn()} />)
    const input = screen.getByLabelText("Ask about this document")
    fireEvent.change(input,{target:{value:"   "}})
    expect(screen.getByRole("button",{name:"Send message"}).hasAttribute("disabled")).toBe(true)
    fireEvent.change(input,{target:{value:"  What is the policy?  "}})
    fireEvent.keyDown(input,{key:"Enter",shiftKey:true})
    expect(onSend).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole("button",{name:"Send message"}))
    expect(onSend).toHaveBeenCalledWith("What is the policy?")
})

test("keeps provisional text unlinked until completion and shows failure",() => {
    const onSourceSelect = vi.fn()
    const message = {id:1,role:"assistant" as const,content:"Answer [[chunk:7]]",
        answer_status:null,cited_chunk_ids:null,pending:true}
    const {rerender} = render(<ChatPanel document={document} messages={[message]} loading={false}
        error={null} sending={true} onSend={vi.fn()} onSourceSelect={onSourceSelect} />)
    expect(screen.queryByRole("button",{name:"Open source #7"})).toBeNull()
    rerender(<ChatPanel document={document} messages={[{...message,pending:false,failed:true}]} loading={false}
        error={null} sending={false} onSend={vi.fn()} onSourceSelect={onSourceSelect} />)
    expect(screen.getByText(/partial text is unverified/)).toBeTruthy()
    expect(screen.queryByRole("button",{name:"Open source #7"})).toBeNull()
})

test("shows verified sources as quiet preview links",() => {
    const onSourceSelect = vi.fn()
    render(<ChatPanel document={document} messages={[{
        id:2,role:"assistant",content:"Approval is required [[chunk:7]].",
        answer_status:"answered",cited_chunk_ids:[7],
    }]} loading={false} error={null} sending={false} onSend={vi.fn()} onSourceSelect={onSourceSelect} />)
    const link = screen.getByRole("button",{name:"Open source #7"})
    expect(link.textContent).toContain("Source preview · Policy")
    fireEvent.click(link)
    expect(onSourceSelect).toHaveBeenCalledWith(7)
})

test("shows distinct abstention states",() => {
    render(<ChatPanel document={document} messages={[
        {id:1,role:"assistant",content:null,answer_status:"no_candidates",cited_chunk_ids:[]},
        {id:2,role:"assistant",content:null,answer_status:"insufficient_evidence",cited_chunk_ids:[]},
    ]} loading={false} error={null} sending={false} onSend={vi.fn()} onSourceSelect={vi.fn()} />)
    expect(screen.getByText(/No relevant passages/)).toBeTruthy()
    expect(screen.getByText(/do not support an answer/)).toBeTruthy()
})
