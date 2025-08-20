import { useRef, useEffect } from "react";
import { ChatHeader } from "./ChatHeader";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";
import { ChatFooter } from "./ChatFooter";
import { ScrollArea } from "../ui/scroll-area";
import { useChat } from "../../hooks/useChat";
import { useVoice } from "../../hooks/useVoice";
import logoHCC from "../../assets/LOGO_HCC.jpg";

interface ChatInterfaceProps {
  onSendMessage?: (message: string) => Promise<string> | string;
  initialMessage?: string;
  onError?: (error: Error) => void;
}

export function ChatInterface({
  initialMessage = "Xin chào! Tôi là trợ lý pháp luật AI có thể giúp bạn tra cứu thủ tục hành chính như đăng ký khai sinh, chứng thực giấy tờ hoặc nuôi con nuôi. Bạn có câu hỏi gì không?",
  onError,
}: ChatInterfaceProps) {
  const { messages, isLoading, sendMessage, handleClarificationOption } =
    useChat({
      initialMessage,
      onError,
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

  // Auto speak bot messages when voice is enabled (only after user interaction)
  useEffect(() => {
    // Only auto-speak if voice is enabled AND this is a response to user input
    if (isVoiceEnabled && messages.length > 1) {
      // Changed from > 0 to > 1
      const lastMessage = messages[messages.length - 1];
      const secondLastMessage = messages[messages.length - 2];

      // Only speak if last message is bot response to user message
      if (
        lastMessage.isBot &&
        lastMessage.content &&
        !isLoading &&
        !secondLastMessage.isBot
      ) {
        // Delay speaking a bit to ensure message is fully rendered
        setTimeout(async () => {
          try {
            await speakText(lastMessage.content);
          } catch (error) {
            // Silently handle TTS errors (like "not-allowed")
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
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  message={message.content}
                  isBot={message.isBot}
                  timestamp={message.timestamp}
                  clarification={message.clarification}
                  processingTime={message.processingTime}
                  sourceDocuments={message.sourceDocuments}
                  onClarificationSelect={handleClarificationOption}
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
}
