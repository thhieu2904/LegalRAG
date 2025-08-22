import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { ChatInterface } from "./components/chat";
import AdminLayout from "./layouts/AdminLayout";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminVoice from "./pages/admin/AdminVoice";
import AdminVector from "./pages/admin/AdminVector";
import AdminQuestionsRedesigned from "./pages/admin/AdminQuestionsRedesigned";
import AdminDatabase from "./pages/admin/AdminDatabase";
import AdminModels from "./pages/admin/AdminModels";
import AdminSystem from "./pages/admin/AdminSystem";
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
            <Route path="/" element={<ChatInterface />} />
            <Route path="/admin" element={<AdminLayout />}>
              <Route index element={<AdminDashboard />} />
              <Route path="voice" element={<AdminVoice />} />
              <Route path="vector" element={<AdminVector />} />
              <Route path="legal-database" element={<AdminDatabase />} />
              <Route path="questions" element={<AdminQuestionsRedesigned />} />
              <Route path="models" element={<AdminModels />} />
              <Route path="system" element={<AdminSystem />} />
            </Route>
          </Routes>
        </div>
      </Router>
    </VoiceProvider>
  );
}

export default App;
