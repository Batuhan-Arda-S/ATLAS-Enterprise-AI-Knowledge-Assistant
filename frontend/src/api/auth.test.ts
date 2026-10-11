import { afterEach,expect,test,vi } from "vitest"
import { login,getCurrentUser } from "./auth"


afterEach(() => {
    vi.unstubAllGlobals()
})


test("login sends credentials and returns a token",async () => {
    const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({access_token:"test-token",token_type:"bearer"})
    })

    vi.stubGlobal("fetch",fetchMock)

    const result = await login("test@example.com","password123")

    expect(result.access_token).toBe("test-token")

    expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/users/login"),
        expect.objectContaining({
            method: "POST",
            body: JSON.stringify({email:"test@example.com",password:"password123"})
        })
    )
})


test("getCurrentUser sends the bearer token",async () => {
    const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({id:1,email:"test@example.com",role:"employee",is_active:true})
    })

    vi.stubGlobal("fetch",fetchMock)

    const user = await getCurrentUser("test-token")

    expect(user.id).toBe(1)

    expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/users/me"),
        expect.objectContaining({
            headers: {"Authorization":"Bearer test-token"}
        })
    )
})


test("getCurrentUser rejects an invalid session",async () => {
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue({
        ok: false,
        status: 401
    }))

    await expect(getCurrentUser("invalid-token")).rejects.toMatchObject({
        status: 401
    })
})