import { useState } from "react"
import type { FormEvent } from "react"


type LoginFormProps = {
    onLogin: (email: string,password: string) => Promise<void>
}


function LoginForm({onLogin}: LoginFormProps) {
    const [email,setEmail] = useState("")
    const [password,setPassword] = useState("")
    const [loading,setLoading] = useState(false)
    const [error,setError] = useState<string | null>(null)

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        setLoading(true)
        setError(null)

        try {
            await onLogin(email,password)
        } catch (error) {
            setError(error instanceof Error ? error.message : "Login failed")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-layout">
            <header className="auth-header">
                <span className="auth-brand">ATLAS</span>
            </header>

            <main className="auth-main">
                <section className="auth-entry" aria-labelledby="auth-title">
                    <h1 id="auth-title">Sign in</h1>
                    <form onSubmit={handleSubmit} className="login-form">
                        <div className="login-field">
                            <label htmlFor="email">Email address</label>
                            <input id="email" type="email" value={email}
                                   onChange={event => setEmail(event.target.value)}
                                   autoComplete="username" required />
                        </div>

                        <div className="login-field">
                            <label htmlFor="password">Password</label>
                            <input id="password" type="password" value={password}
                                   onChange={event => setPassword(event.target.value)}
                                   autoComplete="current-password" required />
                        </div>

                        {error && <p className="login-error" role="alert">{error}</p>}
                        <button type="submit" disabled={loading}>
                            {loading ? "Signing in..." : "Sign in"}
                        </button>
                    </form>
                </section>
            </main>
        </div>
    )
}

export default LoginForm
