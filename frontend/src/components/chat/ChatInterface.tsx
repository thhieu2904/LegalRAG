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

  // Auto speak bot messages when voice is enabled
  useEffect(() => {
    if (isVoiceEnabled && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.isBot && lastMessage.content && !isLoading) {
        // Delay speaking a bit to ensure message is fully rendered
        setTimeout(() => {
          speakText(lastMessage.content);
        }, 500);
      }
    }
  }, [messages, isVoiceEnabled, isLoading, speakText]);

  const handleSendMessage = async (content: string) => {
    await sendMessage(content);
  };

  return (
    <div className="chat-interface h-screen flex flex-col bg-gray-50">
      {/* HEADER */}
      <ChatHeader />

      {/* CONTENT - Chat messages and input seamless */}
      <div className="flex-1 flex flex-col min-h-0">
        <div className="flex-1 flex flex-col bg-white overflow-hidden">
          {/* Chat messages area - full width */}
          <ScrollArea ref={scrollAreaRef} className="flex-1 bg-white">
            <div className="w-full">
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
                <div className="px-2 py-4 hover:bg-gray-50/50 transition-colors border-b border-gray-50 last:border-b-0">
                  <div className="w-full">
                    <div className="flex gap-3 pr-8">
                      <img
                        src={logoHCC}
                        alt="Trợ lý AI"
                        className="w-10 h-10 flex-shrink-0 ring-2 ring-white shadow-sm rounded-full object-cover"
                      />
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-blue-700">
                            Trợ lý AI
                          </span>
                          <span className="text-xs text-gray-500">
                            đang trả lời...
                          </span>
                        </div>
                        <div className="rounded-xl p-4 bg-white border border-blue-100 shadow-sm">
                          <div className="flex gap-2">
                            <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                            <div
                              className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                              style={{ animationDelay: "0.1s" }}
                            ></div>
                            <div
                              className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                              style={{ animationDelay: "0.2s" }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </ScrollArea>

          {/* Chat input area - seamless connection */}
          <div className="border-t border-gray-100 bg-white">
            <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
          </div>
        </div>
      </div>

      {/* FOOTER */}
      <ChatFooter />
    </div>
  );
}
