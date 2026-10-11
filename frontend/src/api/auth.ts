import type { LoginResponse, CurrentUser } from "../types/auth"


const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"


export class ApiError extends Error {
    status: number

    constructor(message: string,status: number) {
        super(message)
        this.name = "ApiError"
        this.status = status
    }
}


export async function login(email: string,password: string): Promise<LoginResponse> {
    const response = await fetch(`${API_URL}/users/login`,{
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: JSON.stringify({email,password})
    })

    if (response.status === 401) {
        throw new ApiError("Invalid email or password",401)
    }

    if (!response.ok) {throw new ApiError(`Login failed (${response.status})`,response.status)}

    return await response.json()
}


export async function getCurrentUser(token: string): Promise<CurrentUser> {
    const response = await fetch(`${API_URL}/users/me`,{
        headers: {"Authorization":`Bearer ${token}`}
    })

    if (response.status === 401) {throw new ApiError("Session is invalid or expired",401)}

    if (response.status === 403) {throw new ApiError("Access forbidden",403)}

    if (!response.ok) {throw new ApiError(`User request failed (${response.status})`,response.status)}

    return await response.json()
}