import { Link } from "react-router-dom";
import { Settings } from "lucide-react";
import logoHCC from "../../assets/LOGO_HCC.jpg";

export function ChatHeader() {
  return (
    <div className="chat-header-container">
      {/* Main header bar */}
      <div className="chat-header-layout">
        {/* Logo bên trái */}
        <div className="chat-header-logo-section">
          <img
            src={logoHCC}
            alt="Logo Trung tâm Hành chính công"
            className="chat-header-logo"
          />
        </div>

        {/* Tên trung tâm ở giữa */}
        <div className="chat-header-title-section">
          <h1 className="chat-header-title">
            TRUNG TÂM PHỤC VỤ HÀNH CHÍNH CÔNG XÃ LONG PHÚ
          </h1>
        </div>

        {/* Thông tin trợ lý AI bên phải */}
        <div className="chat-header-assistant-section">
          <div className="chat-header-assistant-info">
            <div className="chat-header-assistant-text">
              <div className="chat-header-assistant-name">
                Trợ lý Pháp luật AI
              </div>
              <div className="chat-header-assistant-description">
                Hệ thống hỗ trợ thông tin thủ tục hành chính
              </div>
            </div>
            <Link
              to="/admin"
              className="chat-header-settings-button"
              title="Quản trị hệ thống"
            >
              <Settings className="chat-header-settings-icon" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
