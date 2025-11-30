export interface VoiceInputProps {
  onTranscriptChange?: (text: string) => void;
  onFinalTranscript?: (text: string) => void;
  onAutoSend?: (text: string) => Promise<void>;
  disabled?: boolean;
  autoSend?: boolean;
}
