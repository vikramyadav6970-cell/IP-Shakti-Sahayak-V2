/**
 * frontend/src/components/chat/VoiceInputButton.tsx
 *
 * Voice Speech-to-Text Button using the Web Speech API.
 * Transcribes spoken voice into the input field in real-time,
 * detects the spoken language script, and updates language selection.
 */

import React, { useState, useEffect, useRef } from "react";
import { Mic, MicOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/store/useChatStore";

interface VoiceInputButtonProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
  className?: string;
}

// Unicode script detector for Indic languages
function detectScriptLanguage(text: string): string | null {
  if (!text) return null;
  if (/[\u0900-\u097F]/.test(text)) return "hi-IN"; // Devanagari (Hindi/Marathi)
  if (/[\u0980-\u09FF]/.test(text)) return "bn-IN"; // Bengali
  if (/[\u0A80-\u0AFF]/.test(text)) return "gu-IN"; // Gujarati
  if (/[\u0A00-\u0A7F]/.test(text)) return "pa-IN"; // Punjabi
  if (/[\u0B00-\u0B7F]/.test(text)) return "or-IN"; // Odia
  if (/[\u0B80-\u0BFF]/.test(text)) return "ta-IN"; // Tamil
  if (/[\u0C00-\u0C7F]/.test(text)) return "te-IN"; // Telugu
  if (/[\u0C80-\u0CFF]/.test(text)) return "kn-IN"; // Kannada
  if (/[\u0D00-\u0D7F]/.test(text)) return "ml-IN"; // Malayalam
  return null;
}

export const VoiceInputButton: React.FC<VoiceInputButtonProps> = ({
  onTranscript,
  disabled = false,
  className = "",
}) => {
  const { selectedLanguage, setSelectedLanguage } = useChatStore();
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const silenceTimerRef = useRef<any>(null);

  useEffect(() => {
    // Check Web Speech API availability
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
    }
  }, []);

  const startListening = () => {
    setErrorMessage(null);
    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSupported(false);
      setErrorMessage("Speech recognition not supported in this browser. Please use Chrome or Edge.");
      return;
    }

    try {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;

      // Select speech recognition language
      if (selectedLanguage && selectedLanguage !== "auto") {
        recognition.lang = selectedLanguage;
      } else {
        // Default to Indian English / Hindi multilingual context
        recognition.lang = "hi-IN";
      }

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        let finalTranscript = "";
        let interimTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript;
          } else {
            interimTranscript += transcript;
          }
        }

        const combinedText = (finalTranscript || interimTranscript).trim();
        if (combinedText) {
          onTranscript(combinedText);

          // Detect script and sync language if auto-detect is enabled
          const detectedLang = detectScriptLanguage(combinedText);
          if (detectedLang && selectedLanguage === "auto") {
            setSelectedLanguage(detectedLang);
          }
        }

        // Reset silence timeout
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
        silenceTimerRef.current = setTimeout(() => {
          stopListening();
        }, 3000);
      };

      recognition.onerror = (event: any) => {
        console.warn("[SpeechRecognition] Error:", event.error);
        if (event.error === "not-allowed") {
          setErrorMessage("Microphone access was denied. Please allow microphone permissions.");
        } else if (event.error === "no-speech") {
          // Normal timeout on silence
        } else {
          setErrorMessage(`Voice recognition error: ${event.error}`);
        }
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      console.error("[SpeechRecognition] Failed to start:", err);
      setErrorMessage("Could not start microphone.");
      setIsListening(false);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (err) {
        // Ignore if already stopped
      }
    }
    setIsListening(false);
    if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
  };

  const toggleListening = (e: React.MouseEvent) => {
    e.preventDefault();
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  if (!isSupported) {
    return (
      <Button
        type="button"
        variant="ghost"
        size="icon"
        disabled
        title="Voice recognition is not supported in this browser (Use Chrome/Edge)"
        className={`h-11 w-11 rounded-xl text-slate-300 dark:text-slate-600 ${className}`}
      >
        <MicOff className="w-4 h-4" />
      </Button>
    );
  }

  return (
    <div className="relative inline-flex items-center">
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={toggleListening}
        disabled={disabled}
        title={
          isListening
            ? "Listening... Click to stop recording"
            : `Voice Dictation (${selectedLanguage === "auto" ? "Auto / Hindi" : selectedLanguage})`
        }
        className={`h-10 w-10 rounded-full transition-all relative ${
          isListening
            ? "bg-rose-500 text-white shadow-md shadow-rose-500/30 animate-pulse ring-4 ring-rose-500/20"
            : "text-[#5C6B62] hover:text-[#047857] hover:bg-emerald-500/10"
        } ${className}`}
      >
        {isListening ? (
          <div className="flex items-center justify-center">
            <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
            </span>
            <Mic className="w-4 h-4 text-white animate-bounce" />
          </div>
        ) : (
          <Mic className="w-4 h-4" />
        )}
      </Button>

      {/* Floating active speech status banner */}
      {isListening && (
        <div className="absolute -top-9 left-1/2 -translate-x-1/2 bg-slate-900/90 text-white text-[11px] font-medium px-2.5 py-1 rounded-full shadow-lg border border-slate-700 whitespace-nowrap flex items-center gap-1.5 z-30 animate-in fade-in-0 duration-150">
          <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
          <span>Listening... Speak now</span>
        </div>
      )}

      {errorMessage && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-rose-950/90 text-rose-200 text-[10px] font-medium px-2.5 py-1 rounded-md shadow-lg border border-rose-800 whitespace-nowrap z-30">
          {errorMessage}
        </div>
      )}
    </div>
  );
};
