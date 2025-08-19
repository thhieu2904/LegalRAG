import { ChatInterface } from "./components/chat";
import { ChatService } from "./services/chatService";
import "./App.css";

function App() {
  const handleSendMessage = async (message: string): Promise<string> => {
    try {
      return (await ChatService.sendMessage(message)).response;
    } catch (error) {
      console.error("Error in App:", error);
      return "Đã có lỗi xảy ra. Vui lòng thử lại sau.";
    }
  };

  const handleError = (error: Error) => {
    console.error("Chat error:", error);
  };

  return (
    <div className="App">
      <ChatInterface onSendMessage={handleSendMessage} onError={handleError} />
    </div>
  );
}

export default App;
