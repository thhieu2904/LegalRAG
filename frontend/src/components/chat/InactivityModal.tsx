/**
 * 💬 INACTIVITY MODAL - QUEUE-BASED USE CASE
 * Appears after 5 minutes of inactivity to ask if user wants to start a new conversation
 * Used for kiosk/queue-based deployments where different users come to the machine
 *
 * ⚠️ IMPORTANT: Modal requires MANUAL user action (click button)
 * Why? Because users may come after 8+ seconds, so auto-dismiss would not work
 */

import React from "react";
import "../../styles/components/inactivity-modal.css";

interface InactivityModalProps {
  isOpen: boolean;
  onDismiss: () => void;
  onStartNew: () => void;
}

export const InactivityModal: React.FC<InactivityModalProps> = ({
  isOpen,
  onDismiss,
  onStartNew,
}) => {
  if (!isOpen) {
    return null;
  }

  return (
    <>
      {/* Backdrop - Semi-transparent overlay */}
      <div className="inactivity-modal-backdrop" />

      {/* Modal Container */}
      <div className="inactivity-modal-container">
        <div className="inactivity-modal-box">
          {/* Header */}
          <div className="inactivity-modal-header">
            <span className="inactivity-modal-icon">💬</span>
            <h3 className="inactivity-modal-title">Cuộc trò chuyện mới?</h3>
          </div>

          {/* Body */}
          <div className="inactivity-modal-content">
            <p className="inactivity-modal-message">
              Bạn chưa gửi câu hỏi trong một thời gian. Bạn muốn
              <strong> bắt đầu một chủ đề mới</strong> hay
              <strong> tiếp tục</strong> với chủ đề trước đó?
            </p>

            <p className="inactivity-modal-note">
              ⏰ Hãy chọn một tùy chọn bên dưới để tiếp tục
            </p>
          </div>

          {/* Footer - Buttons */}
          <div className="inactivity-modal-footer">
            <button
              onClick={onDismiss}
              className="inactivity-modal-button inactivity-modal-button--continue"
              title="Tiếp tục hỏi về chủ đề hiện tại"
            >
              <span className="inactivity-modal-button-icon">⏳</span>
              Tiếp tục
            </button>
            <button
              onClick={onStartNew}
              className="inactivity-modal-button inactivity-modal-button--new"
              title="Xóa lịch sử và bắt đầu cuộc trò chuyện mới"
            >
              <span className="inactivity-modal-button-icon">🆕</span>
              Bắt đầu mới
            </button>
          </div>

          {/* Helper text */}
          <div className="inactivity-modal-helper">
            <small>💡 Vui lòng chọn một tùy chọn để tiếp tục</small>
          </div>
        </div>
      </div>
    </>
  );
};

export default InactivityModal;
