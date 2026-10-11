export type LoginResponse = {
    access_token: string
    token_type: string
}

export type CurrentUser = {
    id: number
    email: string
    role: string
    is_active: boolean
}