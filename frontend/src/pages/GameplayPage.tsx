import './GamePlayPage.css'
import { useEffect, useState } from 'react';
import { BACKEND_URL, getToken, isResponseOk } from './Auth';
import { useNavigate } from 'react-router';
import GameSettingPage from './GameSettingPage';

type GridType = (string | null)[][];
const ROWS = 13;
const COLS = 13;
const createInitialGrid = (): GridType => {
  return Array.from({ length: ROWS }, () => 
    new Array(COLS).fill(null)
  );
};

type CardType = {
  id:number,
  val:string,
  placed:boolean,
  i:Number,
  j:Number,
}

function GamePlayPage() {
  // State to control the "Draw Phase" overlay.
  const [isDrawPhase, setIsDrawPhase] = useState(false);
  // State to trigger the card draw animation from the center deck.
  const [isDrawing, setIsDrawing] = useState(false);
  const [myScore, setMyScore] = useState(0);
  const [enemyScore, setEnemyScore] = useState(0);
  const [isMyTurn, setIsMyTurn] = useState(true);
  // State to manage the visibility of the action buttons on mobile
  const [isActionMenuOpen, setIsActionMenuOpen] = useState(false);
  const [selectedCardId, setSelectedCardId] = useState(-1);
  const [cards, setCards] = useState<Array<CardType>>([]);
  const [grid, setGrid] = useState<GridType>(createInitialGrid);
  const [originGrid, setOriginGrid] = useState<GridType>(createInitialGrid);
  // State to control the info button
  const [showGameSetting, setShowGameSetting] = useState(false);
  const navigate = useNavigate();

  const updateGameState = () => {
    fetch(`${BACKEND_URL}/hasActiveGame/`, {
      method: 'GET',
      credentials: 'include', //include session id, to verify if the user is logged in
      headers: {
        'Content-Type': 'application/json',
      },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.msg){
          const game = data.game;
          let board = JSON.parse(game.board);
          for(let i = 0; i < board.length; i++)
            for(let j = 0; j < board[i].length; j++)
              board[i][j] = String(board[i][j]);

          setOriginGrid(board);
          setGrid(board);
          let newCards = Array<CardType>(10); 
          const getCards = JSON.parse(game.my_cards)
          for(let i = 0; i < getCards.length; i++)
            newCards[i] = {id:i, val: getCards[i], placed:false, i:-1, j:-1};
          setCards(newCards);
          setMyScore(game.my_score);
          setEnemyScore(game.enemy_score);
          setIsMyTurn(game.is_my_turn)
        }
        else
          navigate('/');
      })
      .catch((err) => {
        console.log(err);
      });
  }

  useEffect(() => {
    updateGameState();
  }, [isDrawPhase])

  useEffect(() => {
    document.body.classList.add('gameplay');
    updateGameState();

    return () => {
      document.body.classList.remove('gameplay');
    };
  }, []);

  // Handler for drawing a card from the center deck
  const handleDrawFromCenter = () => {
    if (isDrawing) return; // Prevent re-triggering animation
    setIsDrawing(true); // Start the animation

    setTimeout(() => {
      setIsDrawPhase(false);
      setIsDrawing(false); // Reset animation state
    }, 1200);
  };

  const handleClearButton = () => {
    setGrid(originGrid);
    setSelectedCardId(-1);
      const defaultCard = cards.map((c, i) => {
        return {...c,val:c.val, placed: false, i:-1, j:-1};
    });
    setCards(defaultCard);
  }

  const handleCardClicked = (cardId:number) => {
      if (selectedCardId == cardId)
        setSelectedCardId(-1);
      else
        setSelectedCardId(cardId);
  };

  const handleSubmitButton = () => {
    let cardPlaced = cards.filter((card) => card.placed);
    console.log(cardPlaced);
    const token = getToken();
    fetch(`${BACKEND_URL}/placeCard/`, {
      method: 'POST',
      credentials: 'include', //include session id, to verify if the user is logged in
      headers: {
        'Content-Type': 'application/json',
        "X-CSRFToken": token,
      },
      body: JSON.stringify({ cardPlaced: JSON.stringify(cardPlaced)}),
    })
    .then((response) => isResponseOk(response))
    .then((data) => {
        console.log(data);
        setIsDrawPhase(true);
    })
    .catch((err) => {
        console.log(err);
    });
  }

  const handleCellUpdate = (rowIndex: number, colIndex: number) => {
    if (selectedCardId == -1)
        return;
    let i = -1,j = -1;
    const newGrid = grid.map((row, rIndex) => {
      if (rIndex !== rowIndex) {
        return row;
      }

      const newRow = [...row];
      newRow[colIndex] = String(cards[selectedCardId].val); 
      i = rIndex;
      j = colIndex;
      return newRow;
    });
    console.log(newGrid)

    setGrid(newGrid);
    const newCards = cards.map((curr,id) => {
        if (id !== selectedCardId) {
          return curr;
        }
      
        return {...curr,placed: true, i:i, j:j};
      });

    setCards(newCards);
    
    setSelectedCardId(-1);
  };

  return (
    <>
      <div className="game-play-container">
        {/* --- DRAW PHASE OVERLAY --- */}
        {isDrawPhase && (
          <div className="draw-phase-overlay">
            <div className="center-deck-container">
              <div
                className="card-deck large"
                onClick={handleDrawFromCenter}
                title="Click to draw a card"
              >
                {isDrawing && <div className="drawn-card-center"></div>}
              </div>
              <div className="draw-prompt">Draw</div>
            </div>
          </div>
        )}

        {showGameSetting && <GameSettingPage createMode={false} onClose={() => setShowGameSetting(false)} />}
        

        {/* --- MAIN GAME UI --- */}
        <div className="info-button" title="Game Info" onClick={() => setShowGameSetting(true)}>
          <span className="info-button-icon">i</span>
        </div>

        <h1 className='turn-indicator'>{isMyTurn ? 'Your Turn' : 'Enemy Turn'}</h1>

        <div className="score-container">
          <div className="score-item my-score">
            <span>YOU</span>
            <p>{myScore}</p>
          </div>
          <div className="score-divider">:</div>
          <div className="score-item enemy-score">
            <span>OPPONENT</span>
            <p>{enemyScore}</p>
          </div>
        </div>
        
        <div className={`action-buttons ${isActionMenuOpen ? 'open' : ''}`}>
          <div className="actions-menu">
            <button className="game-button">DISCARD<span className="button-label">Selected Card</span></button>
            <button className="game-button" onClick={handleClearButton}>CLEAR<span className="button-label">Selection</span></button>
            <button className="game-button submit" onClick={handleSubmitButton}>Submit <span className="button-label">Action</span></button>
          </div>
          <button className="game-button actions-toggle" onClick={() => setIsActionMenuOpen(!isActionMenuOpen)}>
            ACTIONS
          </button>
        </div>

        <table className='game-table'>
          <tbody>
            {Array.from({ length: 13 }, (_, i) => (
              <tr key={i}>
                {Array.from({ length: 13 }, (_, j) => (
                  <td key={j} onClick={() => handleCellUpdate(i,j)} >{grid[i][j] ? grid[i][j] : ''}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>

        <div className="player-hand-container">
          {/* Placeholder cards */}
          {cards.map((card, i) => <div key={i} className={`hand-card ${i === selectedCardId ? 'selected' : ''} ${card.placed ? 'placed' : ''}`} onClick={() => handleCardClicked(i)}>
            <span className="card-number">{card.val}</span>
            </div>)}
        </div>
      </div>
    </>
  );
}

export default GamePlayPage;
