import React, { useState, useEffect, useRef } from 'react';
import './GameSettingPage.css';
import { getToken, BACKEND_URL, isResponseOk } from './Auth';
import { useNavigate } from 'react-router';

const gameTypes = ['Standard', 'Game of x', 'Hard'] as const;
const gameModes = ['PvP', 'PvAi'] as const;
const AiModels = ['RL', 'MCTS', 'Hard coded'] as const;

type GameType = typeof gameTypes[number];
type GameMode = typeof gameModes[number];
type AiModel = typeof AiModels[number]
type PvpChoice = 'create' | 'join';

function PvPOptionSection({ pvpChoice, setPvpChoice, gameID, setGameID, readOnly }: { pvpChoice: PvpChoice, setPvpChoice: (val: PvpChoice) => void, gameID: string, setGameID: (val: string) => void, readOnly: boolean }) {
  return (
    <>
      <div className="form-section">
        <label>PvP Options:</label>
        <div className="checkbox-group">
          <div
            key="create"
            className={`checkbox-option ${pvpChoice === 'create' ? 'selected' : ''}`}
            onClick={() => {
              if (readOnly)
                  return; 
              setPvpChoice('create');
            }}
          >
            Create Game
          </div>
          <div
            key="join"
            className={`checkbox-option ${pvpChoice === 'join' ? 'selected' : ''}`}
            onClick={() => {
              if (readOnly)
                  return;
              setPvpChoice('join');
              }
            }
          >
            Join Game
          </div>
        </div>
        {pvpChoice === 'create' && !readOnly &&(
          <p style={{ color: "#2e2a47", fontWeight: "600" }}>Note: A new game will be created. Share the Game ID with your friend after creation.</p>
        )}
        {pvpChoice === 'create' && readOnly &&(
          <p style={{ color: "#2e2a47", fontWeight: "600" }}>Game ID: {gameID}</p>
        )}
      </div>
      {pvpChoice === 'join' && (
        <div className="form-section">
          <label htmlFor="gameIDInput" className="input-label">Game ID:</label>
          <input
            type="text"
            id="gameIDInput"
            value={gameID}
            onChange={(e) => setGameID(e.target.value)}
            placeholder="Enter Game ID"
            className="text-input"
            required
          />
        </div>
      )}

    </>
  );
}

function PvAiOptionSection({ setAiModel, aiModel, readOnly }: { setAiModel: (val: AiModel) => void, aiModel : AiModel, readOnly: boolean }) {
  return (
    <div className="form-section">
      <label>Choose Game Type:</label>
      <div className="checkbox-group">
        {AiModels.map(model => (
          <div
            key={model}
            className={`checkbox-option ${aiModel === model ? 'selected' : ''}`}
            onClick={() => {
              if (readOnly)
                  return;
              setAiModel(model);
            }}
          >
            {model}
          </div>
        ))}
      </div>
    </div>
  );
}


function GameSettingPage({ onClose, readOnly = false}: { onClose: () => void; readOnly?: boolean}) {
  const boxRef = useRef<HTMLDivElement>(null);
  const errorMessageRef = useRef<HTMLSpanElement>(null)

  const [selectedType, setSelectedType] = useState<GameType>('Standard');
  const [selectedMode, setSelectedMode] = useState<GameMode>('PvP');
  const navigate = useNavigate();

  // New state for PvP options
  const [pvpChoice, setPvpChoice] = useState<PvpChoice>('create');
  const [gameID, setGameID] = useState<string>('');

  // New state for PvAi options
  const [aiModel, setAiModel] = useState<AiModel>('RL');

  // Get game info when it's readOnly
  if (readOnly){
      fetch(`${BACKEND_URL}/gameInfo/`, {
      method: 'GET',
      credentials: 'include', //include session id, to verify if the user is logged in
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((res) => res.json())
      .then((data) => {
        console.log(data);
      })
      .catch((err) => {
        console.log(err);
        if (errorMessageRef.current != null)
          errorMessageRef.current.innerHTML = err;
      });
  }

  useEffect(() => {
    setGameID('');
    setAiModel('RL');
    if (errorMessageRef.current != null)
      errorMessageRef.current.innerHTML = '';

  },[selectedMode,pvpChoice])

  useEffect(() => {
    setPvpChoice('create');
  },[selectedMode])

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


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (readOnly)
        return;
    const body = { gameType: selectedType, gameMode: selectedMode, pvpChoice: pvpChoice, gameID: gameID, aiModel: aiModel };

    console.log('Game started:', body);

    let token = getToken();

    fetch(`${BACKEND_URL}/newGame/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": token,
      },
      credentials: "include",
      body: JSON.stringify(body),
    })
    .then((response) => isResponseOk(response))
    .then((data) => {
      console.log(data);
      navigate('/match');
    })
    .catch((err) => {
      console.log(err.message);
      if (errorMessageRef.current != null && err != null)
        errorMessageRef.current.innerHTML = err.message;
    });

  };

  return (
    <div className="game-setting-container">
      <div className="game-setting-box" ref={boxRef}>
        <button className="close-btn" onClick={onClose}>x</button>
        {readOnly 
          ? <h1>Game Settings</h1>
          : <h1>Choose Game Settings</h1>
        }
        <form onSubmit={handleSubmit} className={readOnly ? 'read-only' : ''}>
          <div className="form-section">
            <label>Choose Game Type:</label>
            <div className="checkbox-group">
              {gameTypes.map(type => (
                <div
                  key={type}
                  className={`checkbox-option ${selectedType === type ? 'selected' : ''}`}
                  onClick={() => {
                    if (readOnly)
                        return;
                    setSelectedType(type);
                  }}
                >
                  {type}
                </div>
              ))}
            </div>
          </div>
          <div className="form-section">
            <label>Choose Game Mode:</label>
            <div className="checkbox-group">
              {gameModes.map(mode => (
                <div
                  key={mode}
                  className={`checkbox-option ${selectedMode === mode ? 'selected' : ''}`}
                  onClick={() => {
                    if (readOnly)
                      return;
                    setSelectedMode(mode);
                  }}
                >
                  {mode}
                </div>
              ))}
            </div>
          </div>
          {selectedMode === 'PvP' && <PvPOptionSection pvpChoice={pvpChoice} setPvpChoice={setPvpChoice} gameID={gameID} setGameID={setGameID} readOnly={readOnly} />}
          {selectedMode === 'PvAi' && <PvAiOptionSection setAiModel={setAiModel} aiModel={aiModel} readOnly={readOnly}/>}
          
          <span role="alert" className="error-message" ref={errorMessageRef}></span>
          {!readOnly && <button className="continue-button" type="submit">Continue</button>}
          
        </form>
      </div>
    </div>
  );
}


export default GameSettingPage;
