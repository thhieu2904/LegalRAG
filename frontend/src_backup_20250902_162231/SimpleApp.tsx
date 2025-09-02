/**
 * 🏠 SIMPLE APP COMPONENT - ROUTING ĐƠN GIẢN
 * Quản lý routing cho 3 pages chính
 */
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ChatPage from "./pages/simple/ChatPage";
import AdminPage from "./pages/simple/AdminPage";
import OCRPage from "./pages/simple/OCRPage";
import SimpleNavigation from "./components/SimpleNavigation";

function SimpleApp() {
  return (
    <Router>
      <div className="App">
        {/* Navigation Component */}
        <SimpleNavigation />

        {/* Routes */}
        <Routes>
          {/* Chat Page - RAG Service */}
          <Route path="/" element={<ChatPage />} />
          <Route path="/chat" element={<ChatPage />} />

          {/* Admin Page - RAG Service Management */}
          <Route path="/admin" element={<AdminPage />} />

          {/* OCR Page - OCR Service */}
          <Route path="/ocr" element={<OCRPage />} />

          {/* 404 Page */}
          <Route
            path="*"
            element={
              <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                  <h1 className="text-4xl font-bold text-gray-800 mb-4">404</h1>
                  <p className="text-gray-600 mb-4">Trang không tồn tại</p>
                  <a href="/" className="text-blue-600 hover:underline">
                    Về trang chủ
                  </a>
                </div>
              </div>
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default SimpleApp;
