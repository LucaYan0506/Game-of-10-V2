import { useState, useRef, useEffect } from 'react';
import './LoginPage.css'
import { getToken, BACKEND_URL, isResponseOk} from './Auth';

function LoginPage({
                    onClose,
                    setUsername,
                    setAuthenticated,
                    authenticated,
                    }: {
                    onClose: () => void;
                    setUsername: (value: string) => void;
                    setAuthenticated: (value: boolean) => void;
                    authenticated: boolean;
                    }) {
    const boxRef = useRef<HTMLDivElement>(null);
    const usernameRef = useRef<HTMLInputElement>(null)
    const passwordRef = useRef<HTMLInputElement>(null)
    const errorMessageRef = useRef<HTMLParagraphElement>(null)

    // Close on outside click
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (boxRef.current && !boxRef.current.contains(event.target as Node)) {
                onClose();
            }
        }
        function handleEscape(event: KeyboardEvent) {
            if (event.key === 'Escape') onClose();
        }

        document.addEventListener('mousedown', handleClickOutside);
        document.addEventListener('keydown', handleEscape);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
            document.removeEventListener('keydown', handleEscape);
        };
    }, [onClose]);

    const login = async (e: React.FormEvent) => {
        e.preventDefault();

        if (usernameRef.current && passwordRef.current) {
            const _username = usernameRef.current.value;
            const _password = passwordRef.current.value;
            let token = "";
            if (authenticated) {
                console.log("You are already logged in");
                return;
            }
            else
                token = getToken();

            fetch(`${BACKEND_URL}/login/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": token,
                },
                credentials: "include",
                body: JSON.stringify({ username: _username, password: _password }),
            })
            .then((response) => isResponseOk(response))
            .then((data) => {
                setUsername(_username)
                setAuthenticated(true);
                onClose();
                console.log(data);
            })
            .catch((err) => {
                console.log(err);
                if (errorMessageRef.current != null && err != null)
                    errorMessageRef.current.innerHTML = err.message;
            });
        }
        else {
            console.error("Refs are not attached to input elements.");
        }
    };

    return (
        <div className="login-container">
            <div className="login-box" ref={boxRef}>
                <button className="close-btn" onClick={onClose}>x</button>
                <h1>Login</h1>
                <form className="login-form" onSubmit={login}>
                    <label>Username</label>
                    <input ref={usernameRef} type="text" placeholder="Enter your username" required />

                    <label>Password</label>
                    <input ref={passwordRef} type="password" placeholder="Enter your password" required />
                    <span role="alert" className="error-message" ref={errorMessageRef}></span>

                    <button type="submit">Sign In</button>

                    <div className="login-links">
                        <a href="#">Forgot password?</a>
                        <a href="#">Create account</a>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default LoginPage
export {BACKEND_URL}