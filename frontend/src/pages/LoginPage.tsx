import { useState, useRef, useEffect } from 'react';
import Cookies from 'universal-cookie';
const BACKEND_URL = 'http://localhost:8000';
import './LoginPage.css'

const cookies = new Cookies();

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
    const modalRef = useRef<HTMLDivElement>(null);
    const usernameRef = useRef<HTMLInputElement>(null)
    const passwordRef = useRef<HTMLInputElement>(null)
    const errorMessageRef = useRef<HTMLParagraphElement>(null)

    // Close on outside click
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
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


    function isAuthenticated() {
        fetch(`${BACKEND_URL}/session/`, {
            credentials: "include", //get csrf token
        })
            .then((res) => res.json())
            .then((data) => {
                setAuthenticated(data.isAuthenticated);
                return data.isAuthenticated;
            })
            .catch((err) => {
                console.log(err);
            });

        return false;
    }

    function getToken() {
        // if (!cookies.get("csrftoken"))
            // isAuthenticated();
        return cookies.get("csrftoken");
    }

    const login = async (e: React.FormEvent) => {
        e.preventDefault();

        function isResponseOk(response: Response) {
            if (response.status >= 200 && response.status <= 299) {
                return response.json();
            } else {
                throw Error(response.statusText);
            }
        }

        if (usernameRef.current && passwordRef.current) {
            const _username = usernameRef.current.value;
            const _password = passwordRef.current.value;
            let token = "";
            if (authenticated) {
                console.log("You are already logged in");
                return;
            }
            else
                token = getToken()

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
                setAuthenticated(true)
                console.log(data);
            })
            .catch((err) => {
                console.log(err);
                if (errorMessageRef.current != null)
                    errorMessageRef.current.innerHTML = err.msg;
            });
        }
        else {
            console.error("Refs are not attached to input elements.");
        }
    };

    return (
        <div className="login-container">
            <div className="login-box" ref={modalRef}>
                <button className="close-btn" onClick={onClose}>x</button>
                <h1>Login</h1>
                <form className="login-form" onSubmit={login}>
                    <label>Email</label>
                    <input ref={usernameRef} type="email" placeholder="Enter your email" required />

                    <label>Password</label>
                    <input ref={passwordRef} type="password" placeholder="Enter your password" required />
                    <p className="error-message" style={{ color: '#cc0000' }} ref={errorMessageRef}></p>

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