import { Avatar, AvatarImage, AvatarFallback } from "../ui/avatar";
import SpeechControlsSimple from "../SpeechControlsSimple";
import logoHCC from "../../assets/LOGO_HCC.jpg";
import { User } from "lucide-react";
import type {
  ClarificationData,
  ClarificationOption,
} from "../../services/chatService";
import { ClarificationOptions } from "./ClarificationOptions";

interface ChatMessageProps {
  message: string;
  isBot: boolean;
  timestamp: string;
  clarification?: ClarificationData;
  processingTime?: number;
  sourceDocuments?: string[];
  onClarificationSelect?: (option: ClarificationOption) => void;
}

export function ChatMessage({
  message,
  isBot,
  timestamp,
  clarification,
  processingTime,
  sourceDocuments,
  onClarificationSelect,
}: ChatMessageProps) {
  const formatFileName = (filePath: string): string => {
    const fileName =
      filePath.split("\\").pop()?.replace(".json", "") || filePath;
    return fileName;
  };

  return (
    <div
      className={`px-2 py-4 hover:bg-gray-50/50 transition-colors border-b border-gray-50 last:border-b-0 ${
        isBot ? "" : "bg-blue-50/20"
      }`}
    >
      <div className="w-full">
        {isBot ? (
          // Bot message - căn trái
          <div className="flex gap-3 pr-8">
            <Avatar className="w-10 h-10 flex-shrink-0 ring-2 ring-white shadow-sm">
              <AvatarImage src={logoHCC} />
              <AvatarFallback className="bg-blue-500 text-white">
                AI
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <span className="font-medium text-blue-700">Trợ lý AI</span>
                <span className="text-xs text-gray-500">{timestamp}</span>
                {processingTime && (
                  <span className="text-xs text-gray-400">
                    ({processingTime.toFixed(2)}s)
                  </span>
                )}
              </div>

              <div className="rounded-xl p-4 bg-white border border-blue-100 shadow-sm">
                <div className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {message}
                </div>

                {/* Clarification Options */}
                {clarification && onClarificationSelect && (
                  <ClarificationOptions
                    clarification={clarification}
                    onOptionSelect={onClarificationSelect}
                  />
                )}
              </div>

              {/* Source Documents */}
              {sourceDocuments && sourceDocuments.length > 0 && (
                <div className="mt-3">
                  <div className="text-xs text-gray-500 mb-2">
                    📄 Nguồn tài liệu tham khảo:
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {sourceDocuments.map((doc, index) => (
                      <div
                        key={index}
                        className="px-2 py-1 bg-blue-100 rounded text-xs text-blue-700"
                      >
                        {formatFileName(doc)}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Text-to-Speech Controls */}
              {isBot && (
                <div className="mt-3">
                  <SpeechControlsSimple text={message} />
                </div>
              )}
            </div>
          </div>
        ) : (
          // User message - căn phải
          <div className="flex gap-3 justify-end pl-8">
            <div className="flex-1 space-y-2 flex flex-col items-end">
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">{timestamp}</span>
                <span className="font-medium text-gray-800">Bạn</span>
              </div>

              <div className="rounded-xl p-4 bg-gradient-to-br from-blue-500 to-blue-600 text-white shadow-md max-w-4xl">
                <div className="leading-relaxed whitespace-pre-wrap">
                  {message}
                </div>
              </div>
            </div>
            <Avatar className="w-10 h-10 flex-shrink-0 ring-2 ring-white shadow-sm">
              <AvatarFallback className="bg-gradient-to-br from-gray-600 to-gray-700 text-white">
                <User className="w-5 h-5" />
              </AvatarFallback>
            </Avatar>
          </div>
        )}
      </div>
    </div>
  );
}
