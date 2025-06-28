import React from 'react';
import './ConfirmModal.css'; 

interface ConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  children: React.ReactNode; 
}

const ConfirmModal = ({ isOpen, onClose, onConfirm, title, children }: ConfirmModalProps) => {
  // If the modal is not open, render nothing.
  if (!isOpen) {
    return null;
  }

  // Prevent clicks inside the modal from closing it
  const handleModalContentClick = (e: React.MouseEvent) => {
    e.stopPropagation();
  };

  return (
    // The modal overlay that covers the entire screen
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={handleModalContentClick}>
        <h2 className="modal-title">{title}</h2>
        <div className="modal-body">
          {children}
        </div>
        <div className="modal-actions">
          <button className="modal-button cancel" onClick={onClose}>
            Cancel
          </button>
          {/* Use the delete-button style for the confirm action */}
          <button className="modal-button surrender-button" onClick={onConfirm}>
            Surrender
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmModal;