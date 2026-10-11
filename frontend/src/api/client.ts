import { ApiError } from "./auth"

export const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000"

export async function apiRequest<T>(path: string,token: string,options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${API_URL}${path}`,{
        ...options,
        headers: {...options.headers,Authorization:`Bearer ${token}`},
    })
    if (!response.ok) {
        let detail = `Request failed (${response.status})`
        try {
            const body = await response.json()
            if (typeof body.detail === "string") detail = body.detail
        } catch { /* The response has no JSON error body. */ }
        throw new ApiError(detail,response.status)
    }
    return response.json() as Promise<T>
}
