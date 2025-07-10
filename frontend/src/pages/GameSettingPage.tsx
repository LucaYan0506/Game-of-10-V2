import React, { useState, useEffect, useRef } from 'react';
import './GameSettingPage.css';
import { getToken, BACKEND_URL, isResponseOk } from './Auth';
import { useNavigate } from 'react-router';
import ConfirmModal from '../component/ConfirmModal';

const gameTypes = ['Standard', 'Game of x', 'Hard'] as const;
const gameModes = ['PvP', 'PvAi'] as const;
const AiModels = ['RL', 'MCTS', 'Hard coded'] as const;

type GameType = typeof gameTypes[number];
type GameMode = typeof gameModes[number];
type AiModel = typeof AiModels[number]
type PvpChoice = 'create' | 'join';

function isGameType(value: any): value is GameType {
  // The 'includes' method checks if the array contains the value.
  return (gameTypes as readonly string[]).includes(value);
}

function isGameMode(value: any): value is GameMode {
  // The 'includes' method checks if the array contains the value.
  return (gameModes as readonly string[]).includes(value);
}

function isAiModel(value: any): value is AiModel {
  // The 'includes' method checks if the array contains the value.
  return (AiModels as readonly string[]).includes(value);
}

function PvPOptionSection({ pvpChoice, setPvpChoice, gameID, setGameID, createMode, opponentUsername }: { pvpChoice: PvpChoice, setPvpChoice: (val: PvpChoice) => void, gameID: string, setGameID: (val: string) => void, createMode: boolean, opponentUsername: String }) {
  const [isCopied, setIsCopied] = useState(false);

  const handleCopy = () => {
    if (isCopied) return;

    navigator.clipboard.writeText(gameID)
      .then(() => {
        setIsCopied(true);
        // Reset the button text after 2 seconds
        setTimeout(() => {
          setIsCopied(false);
        }, 2000);
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
      });
  };
  
  return (
    <>
      {createMode 
      ?(<>
        <div className="form-section">
          <label>PvP Options:</label>
          <div className="checkbox-group">
            <div
              key="create"
              className={`checkbox-option ${pvpChoice === 'create' ? 'selected' : ''}`}
              onClick={() => {
                if (!createMode)
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
                if (!createMode)
                    return;
                setPvpChoice('join');
                }
              }
            >
              Join Game
            </div>
          </div>
          {pvpChoice === 'create' &&(
            <p style={{ color: "#2e2a47", fontWeight: "600" }}>Note: A new game will be created. Share the Game ID with your friend after creation.</p>
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
      </>)
      :(<> <div className={'game-id-container'}>
          <p className={'game-id-text'}>
            <span>Game ID:</span> {gameID}
          </p>
          <button 
            className={`copy-button ${isCopied ? 'copied' : ''}`}
            onClick={handleCopy} 
            disabled={isCopied} 
          >
            {isCopied ? 'Copied!' : 'Copy'}
          </button>
        </div>

        <div className={'opponent-container'}>
          {opponentUsername != "" 
          ? (
            <p className={'opponent-text'}>
              <span>Opponent:</span> {opponentUsername}
            </p>) : (
            <p className={'opponent-text opponent-waiting'}>
              <span>Opponent:</span> Waiting for opponent...
            </p>
          )}
        </div>
        </>)
      }
    </>
  );
}

function PvAiOptionSection({ setAiModel, aiModel, createMode }: { setAiModel: (val: AiModel) => void, aiModel : AiModel, createMode: boolean }) {
  return (
    <div className="form-section">
      <label>Choose Game Type:</label>
      <div className="checkbox-group">
        {AiModels.map(model => (
          <div
            key={model}
            className={`checkbox-option ${aiModel === model ? 'selected' : ''}`}
            onClick={() => {
              if (!createMode)
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


function GameSettingPage({ onClose, createMode}: { onClose: () => void; createMode: boolean}) {
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

  const [opponentUsername, setOpponentUsername] = useState<string>('');

  const [isModalOpen, setIsModalOpen] = useState(false);

  if (!createMode){
      fetch(`${BACKEND_URL}/gameInfo/`, {
      method: 'GET',
      credentials: 'include', //include session id, to verify if the user is logged in
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((res) => res.json())
      .then((data) => {
        // console.log(data);
        setGameID(data.game.game_id);
        if (isGameType(data.game.game_type))
          setSelectedType(data.game.game_type);
        if (isGameMode(data.game.game_mode))
          setSelectedMode(data.game.game_mode);
        if (isAiModel(data.game.ai_model))
          setAiModel(data.game.ai_model);
        setOpponentUsername(data.game.opponent);
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
      if (isModalOpen)
          return;
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
  }, [onClose, isModalOpen]);


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createMode)
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

  // const handleDeleteGame = () => {
  //   if (confirm("Are you sure you want permantly delete the game? (once delete, you need to create/join a new game to play)")){

  //   }
  // };

  const handleSurrender = () => {
      const token = getToken();
      console.log("TES")
      fetch(`${BACKEND_URL}/endGame/`, {
          method: "DELETE",
          headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": token,
          },
          credentials: "include",
      })
      .then((response) => isResponseOk(response))
      .then((data) => {
          console.log(data);
          navigate('/');
      })
      .catch((err) => {
          console.log(err);
          if (errorMessageRef.current != null && err != null)
              errorMessageRef.current.innerHTML = err.message;
      });  

    setIsModalOpen(false);
  };

  // When the user clicks the main delete button, it just opens the modal
  const handleOpenConfirmation = () => {
    setIsModalOpen(true);
  };

  return (
    <div className="game-setting-container">
      <div className="game-setting-box" ref={boxRef}>
        <button className="close-btn" onClick={onClose}>x</button>
        {createMode 
          ? <h1>Choose Game Settings</h1>
          : <h1>Game Settings</h1>
        }
        <form onSubmit={handleSubmit} className={createMode ? '' : 'read-only'}>
          <div className="form-section">
            <label>Choose Game Type:</label>
            <div className="checkbox-group">
              {gameTypes.map(type => (
                <div
                  key={type}
                  className={`checkbox-option ${selectedType === type ? 'selected' : ''}`}
                  onClick={() => {
                    if (!createMode)
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
                    if (!createMode)
                      return;
                    setSelectedMode(mode);
                  }}
                >
                  {mode}
                </div>
              ))}
            </div>
          </div>
          {selectedMode === 'PvP' && <PvPOptionSection pvpChoice={pvpChoice} setPvpChoice={setPvpChoice} gameID={gameID} setGameID={setGameID} createMode={createMode} opponentUsername={opponentUsername} />}
          {selectedMode === 'PvAi' && <PvAiOptionSection setAiModel={setAiModel} aiModel={aiModel} createMode={createMode}/>}
          
          <span role="alert" className="error-message" ref={errorMessageRef}></span>
          {createMode
            ? <button className="continue-button" type="submit">Continue</button>
            : <button className="surrender-button" onClick={handleOpenConfirmation} type="submit">Surrender</button>
          }
        </form>
      </div>

      {/* --- This is the Modal Component --- */}
      <ConfirmModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleSurrender}
        title="Confirm Surrender"
      >
        <p>Are you sure you want to surrender? This will end the current game and count as a loss.</p>
        <p><strong>This action cannot be undone.</strong> Your opponent will be declared the winner.</p>
      </ConfirmModal>
    </div>
  );
}


export default GameSettingPage;
