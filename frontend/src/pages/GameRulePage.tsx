import './GameRulePage.css'
import {useEffect, useRef} from 'react';

function GameRulePage({ onClose}: { onClose: () => void}) {
  const boxRef = useRef<HTMLDivElement>(null);

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

    return (
        <div className="game-rule-container">
            <div className="game-rule-box" ref={boxRef}>
                    <button className="close-btn" onClick={onClose}>x</button>
                    <h1>Game Rule</h1>
            </div>
        </div>
    )
}

export default GameRulePage;
