/**
 * 💬 MAIN CHAT PAGE - TRANG CHÍNH CỦA APP
 * Parent component quản lý state và truyền props xuống dump components
 * Cấu trúc: Header + Content + Footer
 */
import { useRef, useEffect } from "react";
import { ChatHeader } from "../components/chat/ChatHeader";
import { ChatMessage } from "../components/chat/ChatMessage";
import { ClarificationOptions } from "../components/chat/ClarificationOptions"; // 🔧 Fix: Add ClarificationOptions import
import { ChatInput } from "../components/chat/ChatInput";
import { ChatFooter } from "../components/chat/ChatFooter";
import { ScrollArea } from "../components/ui/scroll-area";
import { useChat } from "../hooks/useChat";
import { useVoice } from "../hooks/useVoice";
import logoHCC from "../assets/LOGO_HCC.jpg";

const MainChatPage = () => {
  const initialMessage =
    "Xin chào! Tôi là trợ lý pháp luật AI có thể giúp bạn tra cứu thủ tục hành chính như đăng ký khai sinh, chứng thực giấy tờ hoặc nuôi con nuôi. Bạn có câu hỏi gì không?";

  // State management - MainChatPage làm parent quản lý
  const {
    messages,
    isLoading,
    sendMessage,
    handleClarificationOption,
    currentClarification, // 🔧 Fix: Add currentClarification to destructure
  } = useChat({
    initialMessage,
    onError: (error) => console.error("Chat error:", error),
  });

  const { isVoiceEnabled, speakText } = useVoice();
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new messages are added
  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollElement =
        scrollAreaRef.current.querySelector(".overflow-auto");
      if (scrollElement) {
        scrollElement.scrollTop = scrollElement.scrollHeight;
      }
    }
  }, [messages]);

  // Auto speak bot messages when voice is enabled
  useEffect(() => {
    if (isVoiceEnabled && messages.length > 1) {
      const lastMessage = messages[messages.length - 1];
      const secondLastMessage = messages[messages.length - 2];

      if (
        lastMessage.isBot &&
        lastMessage.content &&
        !isLoading &&
        !secondLastMessage.isBot
      ) {
        setTimeout(async () => {
          try {
            await speakText(lastMessage.content);
          } catch (error) {
            console.log(
              "TTS not available:",
              error instanceof Error ? error.message : "Unknown error"
            );
          }
        }, 500);
      }
    }
  }, [messages, isVoiceEnabled, isLoading, speakText]);

  const handleSendMessage = async (content: string) => {
    await sendMessage(content);
  };

  return (
    <div className="chat-interface-container">
      {/* HEADER */}
      <ChatHeader />

      {/* CONTENT - Chat messages and input seamless */}
      <div className="chat-content-wrapper">
        <div className="chat-main-container">
          {/* Chat messages area - full width */}
          <ScrollArea ref={scrollAreaRef} className="chat-messages-area">
            <div className="chat-messages-container">
              {messages.map((message, index) => (
                <ChatMessage
                  key={index}
                  message={message}
                  onClarificationClick={handleClarificationOption}
                  logoSrc={logoHCC}
                />
              ))}

              {/* Loading indicator */}
              {isLoading && (
                <div className="loading-indicator-wrapper">
                  <div className="loading-indicator-layout">
                    <img
                      src={logoHCC}
                      alt="Trợ lý AI"
                      className="loading-indicator-avatar"
                    />
                    <div className="loading-indicator-content">
                      <div className="loading-indicator-header">
                        <span className="loading-indicator-name">
                          Trợ lý AI
                        </span>
                        <span className="loading-indicator-status">
                          đang trả lời...
                        </span>
                      </div>
                      <div className="loading-indicator-bubble">
                        <div className="loading-dots-container">
                          <div className="loading-dot loading-dot-1"></div>
                          <div className="loading-dot loading-dot-2"></div>
                          <div className="loading-dot loading-dot-3"></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* 🔧 Fix: Render current clarification if exists */}
              {currentClarification && (
                <div className="clarification-wrapper">
                  <div className="clarification-layout">
                    <img
                      src={logoHCC}
                      alt="Trợ lý AI"
                      className="clarification-avatar"
                    />
                    <div className="clarification-content">
                      <div className="clarification-header">
                        <span className="clarification-name">Trợ lý AI</span>
                      </div>
                      <div className="clarification-bubble">
                        <div className="clarification-message">
                          {currentClarification.clarification.message}
                        </div>
                        <ClarificationOptions
                          clarification={currentClarification.clarification}
                          onOptionSelect={handleClarificationOption}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Chat input area - seamless connection */}
          <div className="chat-input-wrapper">
            <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <ChatFooter />
    </div>
  );
};

export default MainChatPage;
