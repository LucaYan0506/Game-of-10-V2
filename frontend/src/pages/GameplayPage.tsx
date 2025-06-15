import './GamePlayPage.css'
import { useEffect, useState } from 'react';

type GridType = (number | null)[][];
const ROWS = 13;
const COLS = 13;
const createInitialGrid = (): GridType => {
  console.log("Creating initial grid..."); 
  return Array.from({ length: ROWS }, () => 
    new Array(COLS).fill(null)
  );
};

type CardType = {
  val:number,
  placed:boolean,
}

function GamePlayPage() {
  // State to control the "Draw Phase" overlay.
  const [isDrawPhase, setIsDrawPhase] = useState(false);
  // State to trigger the card draw animation from the center deck.
  const [isDrawing, setIsDrawing] = useState(false);
  const [myScore, setMyScore] = useState(12);
  const [enemyScore, setEnemyScore] = useState(10);
  // State to manage the visibility of the action buttons on mobile
  const [isActionMenuOpen, setIsActionMenuOpen] = useState(false);
  const [selectedCardId, setSelectedCardId] = useState(-1);
  const [cards, setCards] = useState<Array<CardType>>([
      { val: 1, placed: false },
      { val: 2, placed: false },
      { val: 3, placed: false },
      { val: 4, placed: false },
      { val: 5, placed: false },
      { val: 6, placed: false },
      { val: 7, placed: false },
      { val: 8, placed: false },
      { val: 9, placed: false },
      { val: 10, placed: false },
    ]);
  const [grid, setGrid] = useState<GridType>(createInitialGrid);
  let originGrid = createInitialGrid;

  useEffect(() => {
    document.body.classList.add('gameplay');
    return () => {
      document.body.classList.remove('gameplay');
    };
  }, []);

  const handleClearButton = () => {
    setGrid(originGrid);
    setSelectedCardId(-1);
      const defaultCard = cards.map((c, i) => {
        return {val:c.val, placed: false};
    });
    setCards(defaultCard);
  }

  // Handler for drawing a card from the center deck
  const handleDrawFromCenter = () => {
    if (isDrawing) return; // Prevent re-triggering animation
    setIsDrawing(true); // Start the animation

    setTimeout(() => {
      setIsDrawPhase(false);
      setIsDrawing(false); // Reset animation state
    }, 1200);
  };

  const handleCardClicked = (cardId:number) => {
      if (selectedCardId == cardId)
        setSelectedCardId(-1);
      else
        setSelectedCardId(cardId);
  };

  const handleCellUpdate = (rowIndex: number, colIndex: number) => {
    if (selectedCardId == -1)
        return;
    
    const newGrid = grid.map((row, rIndex) => {
      if (rIndex !== rowIndex) {
        return row;
      }

      const newRow = [...row];
      newRow[colIndex] = cards[selectedCardId].val; 
      return newRow;
    });

    setGrid(newGrid);

    const newCards = cards.map((curr,i) => {
        if (i !== selectedCardId) {
          return curr;
        }
      
        return {...curr,placed: true};
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

        {/* --- MAIN GAME UI --- */}
        <h1 className='turn-indicator'>Your Turn</h1>

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
            <button className="game-button submit">END <span className="button-label">Turn</span></button>
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
