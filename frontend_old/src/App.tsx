import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import MainChatPage from "./pages/MainChatPage";
import AdminPage from "./pages/AdminPage";
import IntegratedFormPage from "./pages/IntegratedFormPage";
import DocumentPreviewPage from "./pages/DocumentPreviewPage";
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

            <Route path="/admin" element={<AdminPage />} />

            {/* Document Preview Routes */}
            <Route
              path="/admin/documents/:collection/:docId/preview/:type"
              element={<DocumentPreviewPage />}
            />

            <Route path="/forms" element={<IntegratedFormPage />} />
            <Route
              path="/forms/:collectionId/:docId/:formFilename"
              element={<IntegratedFormPage />}
            />
          </Routes>
        </div>
      </Router>
    </VoiceProvider>
  );
}

export default App;
