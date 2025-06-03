import { useState, useEffect, useRef } from 'react';
import './NotFoundPage.css'

function LoginModal({ onClose }: { onClose: () => void }) {
  const modalRef = useRef<HTMLDivElement>(null);

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

  return (
    <div className="login-container">
      <div className="login-box" ref={modalRef}>
          <button className="close-btn" onClick={onClose}>x</button>
          <h1>Login</h1>
          <form className="login-form">
            <label>Email</label>
            <input type="email" placeholder="Enter your email" required />

            <label>Password</label>
            <input type="password" placeholder="Enter your password" required />

            <button type="submit">Sign In</button>

            <div className="login-links">
              <a href="#">Forgot password?</a>
              <a href="#">Create account</a>
            </div>
          </form>
      </div>
      {/* <div className="modal" ref={modalRef}>
        <h2>Login</h2>
        <p>This is the login window.</p>
        <button onClick={onClose}>Close</button>
      </div> */}
    </div>
  );
}

function HomePage() {
  const [showLogin, setShowLogin] = useState(false);

  return (
    <div className="container">
      <div className="content">
        <img src="src/assets/icon5.png" alt="Game Icon" className="icon" />
        <p className="description">Place cards to reach power tens</p>
        <div className="button-group">
          <div className="card">
            <div className="card-face play-button">Play</div>
            <button className="card-back">Let’s Go!</button>
          </div>
          <div className="card">
            <div onClick={() => setShowLogin(true)} className="card-face login-button">
              Login
            </div>
            <button onClick={() => setShowLogin(true)} className="card-back">
              Welcome!
            </button>
          </div>
        </div>
      </div>
        {showLogin && <LoginModal onClose={() => setShowLogin(false)} />}
    </div>
  );
}

export default HomePage;
