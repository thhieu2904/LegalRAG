import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import MainChatPage from "./pages/MainChatPage";
import AdminPage from "./pages/AdminPage";
import QRScanPage from "./pages/QRScanPage";
import { VoiceProvider } from "./contexts/VoiceContext";
import "./styles/main.css";

function App() {
  return (
    <VoiceProvider>
      <Router
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <div className="App">
          <Routes>
            <Route path="/" element={<MainChatPage />} />
            <Route path="/qr" element={<QRScanPage />} />
            <Route path="/scan" element={<QRScanPage />} />
            <Route path="/admin" element={<AdminPage />} />
          </Routes>
        </div>
      </Router>
    </VoiceProvider>
  );
}

export default App;
