import './GamePlayPage.css'
import { useEffect, useState } from 'react';

function GamePlayPage() {
  // State to control the "Draw Phase" overlay. Set to true to see it on load.
  const [isDrawPhase, setIsDrawPhase] = useState(true);
  // State to trigger the card draw animation from the center deck.
  const [isDrawing, setIsDrawing] = useState(false);

  const [myScore, setMyScore] = useState(12);
  const [enemyScore, setEnemyScore] = useState(10);
  
  useEffect(() => {
    // This adds the 'gameplay' class to the <body> tag to change the page background
    document.body.classList.add('gameplay');

    // Cleanup function runs when the component unmounts to remove the class
    return () => {
      document.body.classList.remove('gameplay');
    };
  }, []); 

  // Handler for drawing a card from the center deck
  const handleDrawFromCenter = () => {
    if (isDrawing) return; // Prevent re-triggering animation
    
    setIsDrawing(true); // Start the animation

    // After the animation finishes (1.2s), end the draw phase
    setTimeout(() => {
      setIsDrawPhase(false);
      setIsDrawing(false); // Reset animation state
      // You would also add the drawn card to the player's hand state here
    }, 1200);
  };

  return (
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
              {/* This card animates from the center deck */}
              {isDrawing && <div className="drawn-card-center"></div>}
            </div>
            <div className="draw-prompt">
              Draw
            </div>
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
      
      <div className="action-buttons">
          <button className="game-button">DISCARD<span className="button-label">Selected Card</span></button>
          <button className="game-button">CLEAR<span className="button-label">Selection</span></button>
          <button className="game-button submit">END <span className="button-label">Turn</span></button>
      </div>

      <table className='game-table'>
        <tbody>
          {Array.from({ length: 13 }, (_, row) => (
            <tr key={row}>
              {Array.from({ length: 13 }, (_, col) => (
                <td key={col}></td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="player-hand-container">
        {/* Placeholder cards for the hand */}
        <div className="hand-card"></div>
        <div className="hand-card"></div>
        <div className="hand-card"></div>
        <div className="hand-card"></div>
        <div className="hand-card"></div>
        <div className="hand-card"></div>
        <div className="hand-card"></div>
        <div className="hand-card"></div>
        <div className="hand-card"></div>
        <div className="hand-card"></div>
      </div>
    </div>
  );
}

export default GamePlayPage;
