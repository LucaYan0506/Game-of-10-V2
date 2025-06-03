import { useState, useEffect } from 'react';
import LoginPage, { BACKEND_URL } from './LoginPage';
import "./HomePage.css"

function LoginButton({ openLoginPage }: { openLoginPage: () => void }) {
  return (
    <div className="card">
      <div onClick={() => openLoginPage()} className="card-face login-button">
        Login
      </div>
      <button onClick={() => openLoginPage()} className="card-back">
        Welcome!
      </button>
    </div>
  )
}

function LogoutButton() {
  function logout() {
    fetch(`${BACKEND_URL}/logout/`, {
      credentials: "include",
    })
      .then(response => response.json())
      .then(data => {
        console.log(data)
      })
      .catch((err) => {
        console.log(err);
      });
  }
  return (
    <button onClick={() => logout}>Logout</button>
  )
}

function HomePage() {
  const [showLogin, setShowLogin] = useState(false);
  const [Username, setUsername] = useState('');
  const [authenticated, setAuthenticated] = useState(false);
  
  //check if user is logged in, when the page is rendered for the first time
  useEffect(() => {
    fetch(`${BACKEND_URL}/session/`, {
      credentials: "include", //get csrf token
    })
      .then((res) => res.json())
      .then((data) => {
        setAuthenticated(data.isAuthenticated);
      })
      .catch((err) => {
        console.log(err);
      });
    console.log("test")
  }, []);

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
          {!authenticated && <LoginButton openLoginPage={() => setShowLogin(true)} />}
          {authenticated && <LogoutButton />}
        </div>
      </div>
      {showLogin && <LoginPage onClose={() => setShowLogin(false)} setUsername={setUsername} setAuthenticated={setAuthenticated} authenticated={authenticated} />}
    </div>
  );
}

export default HomePage;
