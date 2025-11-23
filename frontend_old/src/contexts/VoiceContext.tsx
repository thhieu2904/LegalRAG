import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import { textToSpeechService } from "../services/textToSpeech";

interface VoiceContextType {
  isVoiceEnabled: boolean;
  setIsVoiceEnabled: (enabled: boolean) => void;
  speakText: (text: string) => Promise<void>;
  stopSpeaking: () => void;
}

const VoiceContext = createContext<VoiceContextType | undefined>(undefined);

export function VoiceProvider({ children }: { children: ReactNode }) {
  const [isVoiceEnabled, setIsVoiceEnabled] = useState(true);

  useEffect(() => {
    // Stop any current speech when disabled
    if (!isVoiceEnabled) {
      textToSpeechService.stop();
    }
  }, [isVoiceEnabled]);

  const speakText = async (text: string) => {
    if (isVoiceEnabled && textToSpeechService.isSupported()) {
      try {
        const cleanText = textToSpeechService.cleanTextForSpeech(text);
        if (cleanText.trim()) {
          await textToSpeechService.speak(cleanText);
        }
      } catch (error) {
        console.error("Error speaking text:", error);
      }
    }
  };

  const stopSpeaking = () => {
    textToSpeechService.stop();
  };

  return (
    <VoiceContext.Provider
      value={{
        isVoiceEnabled,
        setIsVoiceEnabled,
        speakText,
        stopSpeaking,
      }}
    >
      {children}
    </VoiceContext.Provider>
  );
}

export const useVoice = () => {
  const context = useContext(VoiceContext);
  if (context === undefined) {
    throw new Error("useVoice must be used within a VoiceProvider");
  }
  return context;
};
