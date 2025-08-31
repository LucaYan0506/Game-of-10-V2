import * as React from 'react';
import './GameEndModal.css';

interface GameEndModalProps {
  isVisible: boolean;
  winner: string;
  loser: string;
  currentUser: string;
  onClose: () => void;
  onRefresh: () => void;
}

const GameEndModal: React.FC<GameEndModalProps> = ({
  isVisible,
  winner,
  loser,
  currentUser,
  onClose,
  onRefresh
}) => {
  if (!isVisible) return null;

  const isWinner = currentUser === winner;

  return (
    <div className="game-end-modal-overlay">
      <div className="game-end-modal">
        <h2 className={`game-end-title ${isWinner ? 'winner' : 'loser'}`}>
          {isWinner ? '🎉 You Win! 🎉' : '😞 Game Over 😞'}
        </h2>
        <p className="game-end-message">
          {isWinner 
            ? `Congratulations! You defeated ${loser} and reached 20 points!` 
            : `${winner} reached 20 points first. Better luck next time!`
          }
        </p>
        <div className="game-end-buttons">
          <button className="refresh-button" onClick={onRefresh}>New Game</button>
          <button className="close-button" onClick={onClose}>Close</button>
        </div>
      </div>
    </div>
  );
};

export default GameEndModal;