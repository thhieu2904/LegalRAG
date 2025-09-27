/**
 * 🔧 ADMIN PAGE - TRANG QUẢN TRỊ THỐNG NHẤT
 * Sử dụng internal navigation để chuyển đổi giữa các admin components
 * Thay vì nhiều pages riêng lẻ, chỉ cần 1 page với components thay đổi
 */
import { useState } from "react";
import Dashboard from "../components/admin/Dashboard";
import Voice from "../components/voice/Voice";
import Database from "../components/admin/Database";
import QuestionsManager from "../components/admin/questions/QuestionsManager";
import System from "../components/admin/System";
import "./AdminPage.css";

type AdminSection = "dashboard" | "voice" | "database" | "questions" | "system";

const AdminPage = () => {
  const [activeSection, setActiveSection] = useState<AdminSection>("dashboard");

  const navigationItems = [
    { key: "dashboard" as AdminSection, label: "📊 Dashboard", icon: "📊" },
    { key: "voice" as AdminSection, label: "🎤 Voice", icon: "🎤" },
    { key: "database" as AdminSection, label: "💾 Database", icon: "💾" },
    { key: "questions" as AdminSection, label: "❓ Questions", icon: "❓" },
    { key: "system" as AdminSection, label: "⚙️ System", icon: "⚙️" },
  ];

  const renderActiveComponent = () => {
    switch (activeSection) {
      case "dashboard":
        return <Dashboard />;
      case "voice":
        return <Voice />;
      case "database":
        return <Database />;
      case "questions":
        return <QuestionsManager />;
      case "system":
        return <System />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="admin-page">
      {/* Header */}
      <div className="admin-header">
        <h1>🔧 Admin Panel</h1>
        <p>Quản trị hệ thống Legal RAG</p>
      </div>

      <div className="admin-container">
        {/* Navigation Sidebar */}
        <div className="admin-navigation">
          <nav className="admin-nav">
            {navigationItems.map((item) => (
              <button
                key={item.key}
                className={`admin-nav-item ${
                  activeSection === item.key ? "active" : ""
                }`}
                onClick={() => setActiveSection(item.key)}
              >
                <span className="nav-icon">{item.icon}</span>
                <span className="nav-label">{item.label}</span>
              </button>
            ))}
          </nav>
        </div>

        {/* Content Area */}
        <div className="admin-content">
          <div className="admin-content-header">
            <h2>
              {
                navigationItems.find((item) => item.key === activeSection)
                  ?.label
              }
            </h2>
          </div>
          <div className="admin-content-body">{renderActiveComponent()}</div>
        </div>
      </div>
    </div>
  );
};

export default AdminPage;
