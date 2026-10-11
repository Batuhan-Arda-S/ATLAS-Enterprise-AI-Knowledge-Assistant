// @vitest-environment jsdom

import { afterEach,beforeEach,describe,expect,it,vi } from "vitest"
import { cleanup,fireEvent,render,screen,waitFor,within } from "@testing-library/react"
import App from "./App"
import { login,getCurrentUser } from "./api/auth"
import { deleteDocument,getDocument,getSource,listDocuments,updateDocument,uploadDocument } from "./api/documents"
import { createConversation,getConversation,listConversations,streamChat } from "./api/chat"
import type { DocumentResponse } from "./types/document"

vi.mock("./api/auth",() => ({login:vi.fn(),getCurrentUser:vi.fn(),
    ApiError:class ApiError extends Error {
        status: number
        constructor(message: string,status: number) {super(message);this.status = status}
    }}))
vi.mock("./api/documents",() => ({getDocument:vi.fn(),getSource:vi.fn(),listDocuments:vi.fn(),
    uploadDocument:vi.fn(),updateDocument:vi.fn(),deleteDocument:vi.fn()}))
vi.mock("./api/chat",() => ({createConversation:vi.fn(),getConversation:vi.fn(),listConversations:vi.fn(),streamChat:vi.fn()}))

const document: DocumentResponse = {id:12,title:"Remote Work Policy",department:"HR",
    content:"Employees need manager approval.",processing_status:"processed"}
const other: DocumentResponse = {id:13,title:"Security Policy",department:"IT",
    content:"Report incidents promptly.",processing_status:"processed"}
const conversation = {id:4,document_id:12,title:"Approval",created_at:"2026-01-01",updated_at:"2026-01-01"}

function submitLogin() {
    fireEvent.change(screen.getByLabelText("Email address"),{target:{value:"admin@example.com"}})
    fireEvent.change(screen.getByLabelText("Password"),{target:{value:"secret123"}})
    fireEvent.click(screen.getByRole("button",{name:"Sign in"}))
}

async function signIn() {
    submitLogin()
    await screen.findByRole("heading",{name:"Policy Assistant"})
    await screen.findByRole("button",{name:/Remote Work Policy/})
}

beforeEach(() => {
    vi.mocked(login).mockResolvedValue({access_token:"test-token",token_type:"bearer"})
    vi.mocked(getCurrentUser).mockResolvedValue({id:1,email:"admin@example.com",role:"admin",is_active:true})
    vi.mocked(listDocuments).mockResolvedValue([document,other])
    vi.mocked(getDocument).mockImplementation(async id => id === 12 ? document : other)
    vi.mocked(listConversations).mockResolvedValue([conversation])
    vi.mocked(getConversation).mockResolvedValue({...conversation,messages:[]})
    vi.mocked(createConversation).mockResolvedValue({...conversation,id:5})
    vi.mocked(streamChat).mockResolvedValue({answer:"Yes [[chunk:7]].",answer_status:"answered",
        retrieval_status:"relevant",cited_sources:[{chunk_id:7,document_id:12,chunk_index:0}]})
    vi.mocked(getSource).mockResolvedValue({chunk_id:7,document_id:12,chunk_index:0,
        content:"Employees need manager approval.",document_title:"Remote Work Policy",department:"HR"})
    vi.mocked(updateDocument).mockResolvedValue(document)
    vi.mocked(deleteDocument).mockResolvedValue({message:"deleted"})
})

afterEach(() => {cleanup();vi.restoreAllMocks();vi.resetAllMocks()})

describe("App login and workspace flow",() => {
    it("starts on login and waits for authentication",() => {
        vi.mocked(login).mockReturnValue(new Promise(() => {}))
        render(<App />)
        submitLogin()
        expect(screen.getByRole("button",{name:"Signing in..."}).hasAttribute("disabled")).toBe(true)
        expect(getCurrentUser).not.toHaveBeenCalled()
    })

    it("loads real document and conversation lists with the token",async () => {
        render(<App />)
        await signIn()
        expect(getCurrentUser).toHaveBeenCalledWith("test-token")
        expect(listDocuments).toHaveBeenCalledWith("test-token",expect.any(AbortSignal))
        await waitFor(() => expect(getDocument).toHaveBeenCalledWith(12,"test-token",expect.any(AbortSignal)))
        expect(screen.getByRole("navigation",{name:"Recent conversations"})).toBeTruthy()
    })

    it("reports rejected credentials",async () => {
        vi.mocked(login).mockRejectedValue(new Error("Invalid email or password"))
        render(<App />)
        submitLogin()
        expect((await screen.findByRole("alert")).textContent).toBe("Invalid email or password")
        expect(listDocuments).not.toHaveBeenCalled()
    })

    it("stays on login when the profile fails",async () => {
        vi.mocked(getCurrentUser).mockRejectedValue(new Error("Session is invalid or expired"))
        render(<App />)
        submitLogin()
        expect((await screen.findByRole("alert")).textContent).toBe("Session is invalid or expired")
        expect(listDocuments).not.toHaveBeenCalled()
    })

    it("filters documents by their real department and changes selection",async () => {
        render(<App />)
        await signIn()
        fireEvent.click(screen.getByRole("button",{name:"IT"}))
        const library = screen.getByLabelText("Documents")
        expect(within(library).queryByText("Remote Work Policy")).toBeNull()
        fireEvent.click(within(library).getByRole("button",{name:/Security Policy/}))
        await waitFor(() => expect(getDocument).toHaveBeenCalledWith(13,"test-token",expect.any(AbortSignal)))
    })

    it("uploads a document and selects it",async () => {
        vi.mocked(uploadDocument).mockResolvedValue({id:14,title:"New Policy",department:"HR",processing_status:"processed"})
        vi.mocked(listDocuments).mockResolvedValueOnce([document,other]).mockResolvedValueOnce([document,other,
            {id:14,title:"New Policy",department:"HR",content:"New content",processing_status:"processed"}])
        render(<App />)
        await signIn()
        fireEvent.click(screen.getByRole("button",{name:/Upload document/}))
        fireEvent.change(screen.getByLabelText("Title"),{target:{value:"New Policy"}})
        fireEvent.change(screen.getByLabelText("Department"),{target:{value:"HR"}})
        fireEvent.change(screen.getByLabelText("File"),{target:{files:[new File(["New content"],"policy.txt",{type:"text/plain"})]}})
        fireEvent.click(screen.getByRole("button",{name:"Upload"}))
        await waitFor(() => expect(uploadDocument).toHaveBeenCalled())
        await screen.findByText("Document uploaded and added to the library.")
    })

    it("keeps the upload form open and reports an upload failure",async () => {
        vi.mocked(uploadDocument).mockRejectedValue(new Error("Unsupported file type"))
        render(<App />)
        await signIn()
        fireEvent.click(screen.getByRole("button",{name:/Upload document/}))
        fireEvent.change(screen.getByLabelText("Title"),{target:{value:"Image"}})
        fireEvent.change(screen.getByLabelText("Department"),{target:{value:"HR"}})
        fireEvent.change(screen.getByLabelText("File"),{target:{files:[new File(["x"],"image.jpg",{type:"image/jpeg"})]}})
        fireEvent.click(screen.getByRole("button",{name:"Upload"}))
        expect((await screen.findByRole("alert")).textContent).toContain("Unsupported file type")
        expect(screen.getByLabelText("Title")).toBeTruthy()
    })

    it("updates metadata and confirms deletion before calling the API",async () => {
        render(<App />)
        await signIn()
        fireEvent.click(screen.getByRole("button",{name:"Edit document details"}))
        fireEvent.change(screen.getByLabelText("Document title"),{target:{value:"Revised Policy"}})
        fireEvent.click(screen.getByRole("button",{name:"Save changes"}))
        await waitFor(() => expect(updateDocument).toHaveBeenCalledWith(12,"test-token","Revised Policy","HR"))

        fireEvent.click(screen.getByRole("button",{name:"Edit document details"}))
        const confirm = vi.spyOn(window,"confirm").mockReturnValueOnce(false).mockReturnValueOnce(true)
        fireEvent.click(screen.getByRole("button",{name:"Delete document"}))
        expect(deleteDocument).not.toHaveBeenCalled()
        fireEvent.click(screen.getByRole("button",{name:"Delete document"}))
        await waitFor(() => expect(deleteDocument).toHaveBeenCalledWith(12,"test-token"))
        expect(confirm).toHaveBeenCalledTimes(2)
    })

    it("streams an answer, opens its citation, and returns to login",async () => {
        render(<App />)
        await signIn()
        await screen.findByRole("heading",{name:"Ask about this document"})
        fireEvent.change(screen.getByLabelText("Ask about this document"),{target:{value:"Is approval needed?"}})
        fireEvent.click(screen.getByRole("button",{name:"Send message"}))
        await waitFor(() => expect(createConversation).toHaveBeenCalledWith(12,"test-token","Is approval needed?",expect.any(AbortSignal)))
        expect(await screen.findByRole("button",{name:"Open source #7"})).toBeTruthy()
        fireEvent.click(screen.getByRole("button",{name:"Open source #7"}))
        expect(await screen.findByText("Employees need manager approval.")).toBeTruthy()
        fireEvent.click(screen.getByRole("button",{name:"Sign out"}))
        expect(screen.getByRole("heading",{name:"Sign in"})).toBeTruthy()
    })

    it("opens saved history and clears it for New Chat",async () => {
        vi.mocked(getConversation).mockResolvedValue({...conversation,messages:[
            {id:1,role:"user",content:"Policy?",answer_status:null,cited_chunk_ids:null},
            {id:2,role:"assistant",content:"Yes [[chunk:7]].",answer_status:"answered",cited_chunk_ids:[7]},
        ]})
        render(<App />)
        await signIn()
        fireEvent.click(screen.getByRole("button",{name:"Approval"}))
        expect(await screen.findByText("Policy?")).toBeTruthy()
        fireEvent.click(screen.getByRole("button",{name:"New chat"}))
        expect(screen.queryByText("Policy?")).toBeNull()
    })
})
