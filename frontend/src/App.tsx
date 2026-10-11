import { useState } from "react"

import LoginForm from "./components/LoginForm"
import Workspace from "./components/Workspace"

import { login,getCurrentUser } from "./api/auth"

import type { CurrentUser } from "./types/auth"

import "./App.css"


type Session = {
    token: string
    user: CurrentUser
}


function App() {
    const [session,setSession] = useState<Session | null>(null)

    async function handleLogin(email: string,password: string) {
        const result = await login(email,password)

        if (result.token_type.toLowerCase() !== "bearer" || !result.access_token) {
            throw new Error("Invalid authentication response")
        }

        const user = await getCurrentUser(result.access_token)

        if (!user.is_active) {
            throw new Error("Account is inactive")
        }

        setSession({token:result.access_token,user})
    }

    function handleLogout() {
        setSession(null)
    }

    if (!session) {
        return (
            <div className="auth-page">
                <LoginForm onLogin={handleLogin} />
            </div>
        )
    }

    return <Workspace user={session.user} token={session.token} onLogout={handleLogout} />
}

export default App
