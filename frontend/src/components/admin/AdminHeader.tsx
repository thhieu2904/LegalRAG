import { Link } from "react-router-dom";
import { Settings } from "lucide-react";
import logoHCC from "../../assets/LOGO_HCC.jpg";

export default function AdminHeader() {
  return (
    <div className="admin-header-container">
      {/* Main header bar */}
      <div className="admin-header-layout">
        {/* Logo bên trái */}
        <div className="admin-header-logo-section">
          <img
            src={logoHCC}
            alt="Logo Trung tâm Hành chính công"
            className="admin-header-logo"
          />
        </div>

        {/* Tên trung tâm ở giữa */}
        <div className="admin-header-title-section">
          <h1 className="admin-header-title">
            TRUNG TÂM PHỤC VỤ HÀNH CHÍNH CÔNG XÃ LONG PHÚ
          </h1>
        </div>

        {/* Thông tin admin bên phải */}
        <div className="admin-header-assistant-section">
          <div className="admin-header-assistant-info">
            <div className="admin-header-assistant-text">
              <div className="admin-header-assistant-name">
                Quản trị hệ thống
              </div>
              <div className="admin-header-assistant-description">
                Admin Panel - Trợ lý Pháp luật AI
              </div>
            </div>
            <Link
              to="/"
              className="admin-header-settings-button"
              title="Quay lại Chat"
            >
              <Settings className="admin-header-settings-icon" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
