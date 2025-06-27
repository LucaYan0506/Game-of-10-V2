import { useState, useEffect } from 'react';
import LoginPage from './LoginPage';
import { BACKEND_URL } from './Auth';
import "./HomePage.css"
import GameSettingPage from './GameSettingPage';
import { useNavigate } from 'react-router';

function LoginButton({ openLoginPage }: { openLoginPage: () => void }) {
  return (
    <div className="card">
      <div onClick={openLoginPage} className="card-face login-button">
        Login
      </div>
      <button onClick={openLoginPage} className="card-back">
        Welcome!
      </button>
    </div>
  )
}

function LogoutButton({setAuthenticated} : {setAuthenticated: (val: boolean) => void}) {
  function logout() {
    fetch(`${BACKEND_URL}/logout/`, {
      credentials: "include",
    })
      .then(response => response.json())
      .then(data => {
        console.log(data)
        setAuthenticated(false);
      })
      .catch((err) => {
        console.log(err);
      });
  }
  return (
    <button onClick={logout}>Logout</button>
  )
}

function HomePage() {
  const [showLogin, setShowLogin] = useState(false);
  const [showGameSetting, setshowGameSetting] = useState(false);
  const [Username, setUsername] = useState('');
  const [authenticated, setAuthenticated] = useState(false);
  
  const navigate = useNavigate();
  
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
  }, []);

  async function playButtonHandleClick(){
    fetch(`${BACKEND_URL}/hasActiveGame/`, {
      method: 'GET',
      credentials: 'include', //include session id, to verify if the user is logged in
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.msg)
          navigate('/match');
        else
          setshowGameSetting(true);
      })
      .catch((err) => {
        console.log(err);
      });

  }


  return (
    <div className="home-container">
      <div className="content">
        <img src="src/assets/icon5.png" alt="Game Icon" className="icon" />
        <p className="description">Place cards to reach 10<sup>x</sup>!</p>
        <div className="button-group">
          <div className="card">
            <div className="card-face play-button" onClick={playButtonHandleClick}>Play</div>
            <button className="card-back" onClick={playButtonHandleClick}>Let’s Go!</button>
          </div>
          {!authenticated && <LoginButton openLoginPage={() => setShowLogin(true)} />}
          {authenticated && <LogoutButton setAuthenticated={setAuthenticated}/>}
        </div>
      </div>
      {showLogin && <LoginPage onClose={() => setShowLogin(false)} setUsername={setUsername} setAuthenticated={setAuthenticated} authenticated={authenticated} />}
      {showGameSetting && <GameSettingPage createMode={true} onClose={() => setshowGameSetting(false)} />}
    </div>
  );
}

export default HomePage;
