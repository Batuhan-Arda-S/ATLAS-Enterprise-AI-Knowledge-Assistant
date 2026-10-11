// @vitest-environment jsdom

import { afterEach,beforeEach,expect,test,vi } from "vitest"
import { cleanup,fireEvent,render,screen } from "@testing-library/react"
import Workspace from "./Workspace"
import { getDocument,getSource,listDocuments } from "../api/documents"
import { getConversation,listConversations } from "../api/chat"

vi.mock("../api/documents",() => ({getDocument:vi.fn(),getSource:vi.fn(),listDocuments:vi.fn(),
    uploadDocument:vi.fn(),updateDocument:vi.fn(),deleteDocument:vi.fn()}))
vi.mock("../api/chat",() => ({createConversation:vi.fn(),getConversation:vi.fn(),listConversations:vi.fn(),streamChat:vi.fn()}))

const user = {id:1,email:"admin@example.com",role:"admin",is_active:true}
const first = {id:12,title:"HR Policy",department:"HR",content:"HR content",processing_status:"processed" as const}
const second = {id:13,title:"IT Policy",department:"IT",content:"IT content",processing_status:"processed" as const}
const conversation = {id:2,document_id:12,title:"Prior chat",created_at:"2026-01-01",updated_at:"2026-01-01"}

beforeEach(() => {
    vi.mocked(listDocuments).mockResolvedValue([first,second])
    vi.mocked(getDocument).mockImplementation(async id => id === 12 ? first : second)
    vi.mocked(listConversations).mockResolvedValue([conversation])
    vi.mocked(getConversation).mockResolvedValue({...conversation,messages:[
        {id:1,role:"user",content:"HR question",answer_status:null,cited_chunk_ids:null},
        {id:2,role:"assistant",content:"HR answer [[chunk:7]].",answer_status:"answered",cited_chunk_ids:[7]},
    ]})
    vi.mocked(getSource).mockResolvedValue({chunk_id:7,document_id:12,chunk_index:0,
        content:"HR source text",document_title:"HR Policy",department:"HR"})
})
afterEach(() => {cleanup();vi.resetAllMocks()})

test("renders three connected panels",async () => {
    render(<Workspace user={user} token="test-token" onLogout={vi.fn()} />)
    expect(screen.getByText("Documents")).toBeTruthy()
    expect(screen.getByRole("heading",{name:"Policy Assistant"})).toBeTruthy()
    expect(screen.getByRole("complementary",{name:"Evidence viewer"}).textContent).toContain("Sources")
    await screen.findByRole("button",{name:/HR Policy/})
})

test("switching documents clears previous chat and evidence",async () => {
    render(<Workspace user={user} token="test-token" onLogout={vi.fn()} />)
    fireEvent.click(await screen.findByRole("button",{name:"Prior chat"}))
    fireEvent.click(await screen.findByRole("button",{name:"Open source #7"}))
    expect(await screen.findByText("HR source text")).toBeTruthy()
    fireEvent.click(screen.getByRole("button",{name:/IT Policy/}))
    expect(screen.queryByText("HR question")).toBeNull()
    expect(screen.queryByText("HR source text")).toBeNull()
    expect(screen.getByText("No source selected")).toBeTruthy()
})

test("document loading error is visible",async () => {
    vi.mocked(listDocuments).mockRejectedValue(new Error("Network unavailable"))
    render(<Workspace user={user} token="test-token" onLogout={vi.fn()} />)
    expect((await screen.findByRole("alert")).textContent).toContain("Network unavailable")
})

test("logs out on request",async () => {
    const onLogout = vi.fn()
    render(<Workspace user={user} token="test-token" onLogout={onLogout} />)
    fireEvent.click(screen.getByRole("button",{name:"Sign out"}))
    expect(onLogout).toHaveBeenCalledOnce()
})
