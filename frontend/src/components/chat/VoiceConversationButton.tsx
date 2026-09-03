/**
 * frontend/src/components/chat/VoiceConversationButton.tsx
 *
 * Full Hands-Free Voice Conversation Mode for IP-SAKTI Sahayak.
 * 
 * 4 Visual States:
 * - Idle: Default state, ready to start voice dialogue.
 * - Listening: Recording user audio with pulsing animation & automatic silence detection (~1.8s silence).
 * - Processing: Spinner / thinking indicator while STT -> RAG -> TTS pipeline executes.
 * - Speaking: Audio playback of synthesized spoken answer. Tapping immediately triggers barge-in interruption.
 *
 * Audio is recorded and encoded directly to 16kHz mono WAV for maximum fidelity and Sarvam STT compatibility.
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import {
  Headphones,
  Square,
  Loader2,
  Settings2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/store/useChatStore";

interface VoiceConversationButtonProps {
  jurisdiction?: string;
  intent?: string;
  disabled?: boolean;
  className?: string;
}

type VoiceState = "idle" | "listening" | "processing" | "speaking";

// Helper to encode Float32Array PCM samples into standard 16-bit 16kHz mono WAV Blob
function encodeWAV(samples: Float32Array, sampleRate: number = 16000): Blob {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  const writeString = (offset: number, str: string) => {
    for (let i = 0; i < str.length; i++) {
      view.setUint8(offset + i, str.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true); // PCM format
  view.setUint16(22, 1, true); // 1 channel (mono)
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true); // ByteRate
  view.setUint16(32, 2, true); // BlockAlign
  view.setUint16(34, 16, true); // BitsPerSample
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (let i = 0; i < samples.length; i++, offset += 2) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
  }

  return new Blob([view], { type: "audio/wav" });
}

export const VoiceConversationButton: React.FC<VoiceConversationButtonProps> = ({
  jurisdiction = "INDIA",
  intent,
  disabled = false,
  className = "",
}) => {
  const { isVoiceContinuous, setIsVoiceContinuous, sendVoiceMessage, isSending } = useChatStore();

  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);

  // Audio Recording & Analysis refs
  const pcmChunksRef = useRef<Float32Array[]>([]);
  const isRecordingRef = useRef<boolean>(false);
  const streamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const hasSpokenRef = useRef<boolean>(false);
  const silenceStartTimestampRef = useRef<number | null>(null);
  const recordingStartTimestampRef = useRef<number>(0);
  const animationFrameRef = useRef<number | null>(null);

  // Audio Playback ref (for barge-in interruption)
  const activeAudioRef = useRef<HTMLAudioElement | null>(null);

  // Constants for Speech and Silence Thresholds (RMS Volume Scale)
  const SPEECH_RMS_THRESHOLD = 0.018; // Detects natural speech above ambient room floor
  const SILENCE_RMS_THRESHOLD = 0.012; // Level below which audio is counted as silence
  const SILENCE_DURATION_MS = 1800; // Auto-stop after 1.8s of sustained silence after speaking
  const MAX_RECORDING_DURATION_MS = 30000; // 30s safety timeout

  // Clean up streams & audio on unmount
  useEffect(() => {
    return () => {
      stopMediaStream();
      stopPlayback();
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, []);

  const stopMediaStream = useCallback(() => {
    isRecordingRef.current = false;
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (processorRef.current) {
      processorRef.current.disconnect();
      processorRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== "closed") {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
  }, []);

  const stopPlayback = useCallback(() => {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current.currentTime = 0;
      activeAudioRef.current = null;
    }
  }, []);

  // Stop Recording and trigger STT processing
  const stopRecordingAndProcess = useCallback(async () => {
    if (!isRecordingRef.current) return;
    isRecordingRef.current = false;

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    const chunks = [...pcmChunksRef.current];
    stopMediaStream();

    let totalLength = 0;
    for (const chunk of chunks) {
      totalLength += chunk.length;
    }

    if (totalLength < 4000) {
      // Less than 0.25s of audio recorded
      setVoiceState("idle");
      return;
    }

    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    const wavBlob = encodeWAV(merged, 16000);
    await handleProcessVoice(wavBlob);
  }, []);

  const stopRecordingAndProcessRef = useRef(stopRecordingAndProcess);
  useEffect(() => {
    stopRecordingAndProcessRef.current = stopRecordingAndProcess;
  }, [stopRecordingAndProcess]);

  // Silence Detection Loop using Real-Time Time-Domain RMS Energy
  const monitorAudioVolume = useCallback(() => {
    if (!analyserRef.current || !isRecordingRef.current) return;

    const bufferLength = analyserRef.current.fftSize;
    const timeData = new Float32Array(bufferLength);
    analyserRef.current.getFloatTimeDomainData(timeData);

    // Calculate root-mean-square (RMS) volume from waveform
    let sumSquares = 0;
    for (let i = 0; i < bufferLength; i++) {
      sumSquares += timeData[i] * timeData[i];
    }
    const rms = Math.sqrt(sumSquares / bufferLength);
    const now = performance.now();

    // 1. Detect if speech has occurred
    if (rms >= SPEECH_RMS_THRESHOLD) {
      hasSpokenRef.current = true;
      silenceStartTimestampRef.current = null; // Reset silence counter while speaking
    } else if (hasSpokenRef.current) {
      // 2. User spoke and is now quiet: track silence accumulation
      if (rms <= SILENCE_RMS_THRESHOLD) {
        if (!silenceStartTimestampRef.current) {
          silenceStartTimestampRef.current = now;
        } else if (now - silenceStartTimestampRef.current >= SILENCE_DURATION_MS) {
          // 1.8s silence reached -> auto-stop recording & send query
          stopRecordingAndProcessRef.current();
          return;
        }
      } else {
        // Marginal noise level: only reset if noise is close to speech volume
        if (rms > (SPEECH_RMS_THRESHOLD + SILENCE_RMS_THRESHOLD) / 2) {
          silenceStartTimestampRef.current = null;
        }
      }
    }

    // Safety timeout: auto-stop after 30s max
    if (now - recordingStartTimestampRef.current > MAX_RECORDING_DURATION_MS) {
      stopRecordingAndProcessRef.current();
      return;
    }

    if (isRecordingRef.current) {
      animationFrameRef.current = requestAnimationFrame(monitorAudioVolume);
    }
  }, []);

  // Start Recording
  const startRecording = async () => {
    setErrorMessage(null);
    stopPlayback();
    hasSpokenRef.current = false;
    silenceStartTimestampRef.current = null;
    recordingStartTimestampRef.current = performance.now();
    pcmChunksRef.current = [];

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioCtx({ sampleRate: 16000 });
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 512;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Real-time PCM capture processor
      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;
      isRecordingRef.current = true;

      processor.onaudioprocess = (e) => {
        if (!isRecordingRef.current) return;
        const inputData = e.inputBuffer.getChannelData(0);
        pcmChunksRef.current.push(new Float32Array(inputData));
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);

      setVoiceState("listening");

      // Start continuous volume monitor loop
      animationFrameRef.current = requestAnimationFrame(monitorAudioVolume);
    } catch (err: any) {
      console.error("Microphone access error:", err);
      setErrorMessage("Microphone access denied or unavailable.");
      setVoiceState("idle");
    }
  };

  // Process Voice Query: Send to Backend STT -> RAG -> TTS
  const handleProcessVoice = async (audioBlob: Blob) => {
    setVoiceState("processing");
    try {
      const res = await sendVoiceMessage(audioBlob, jurisdiction, intent);

      // If synthesized audio received, play it aloud with barge-in support
      if (res && res.audio_base64) {
        playSynthesizedAudio(res.audio_base64, res.audio_format || "audio/wav");
      } else {
        // Fallback: No audio returned or TTS skipped -> return to idle (or auto-resume)
        if (isVoiceContinuous) {
          setTimeout(() => startRecording(), 1000);
        } else {
          setVoiceState("idle");
        }
      }
    } catch (err: any) {
      console.error("Voice processing error:", err);
      setVoiceState("idle");
    }
  };

  // Play audio and handle barge-in
  const playSynthesizedAudio = (base64Audio: string, format: string) => {
    stopPlayback();
    setVoiceState("speaking");

    try {
      const audioUrl = `data:${format};base64,${base64Audio}`;
      const audio = new Audio(audioUrl);
      activeAudioRef.current = audio;

      audio.onended = () => {
        activeAudioRef.current = null;
        if (isVoiceContinuous) {
          // Continuous back-and-forth: immediately start listening for next turn
          setTimeout(() => startRecording(), 600);
        } else {
          setVoiceState("idle");
        }
      };

      audio.onerror = (e) => {
        console.warn("Audio playback error:", e);
        activeAudioRef.current = null;
        setVoiceState("idle");
      };

      audio.play().catch((playErr) => {
        console.warn("Audio autoplay prevented by browser:", playErr);
        activeAudioRef.current = null;
        setVoiceState("idle");
      });
    } catch (err) {
      console.error("Audio initialization error:", err);
      setVoiceState("idle");
    }
  };

  // Main Button Click Handler
  const handleButtonClick = () => {
    if (voiceState === "idle") {
      startRecording();
    } else if (voiceState === "listening") {
      // Manually stop recording early
      stopRecordingAndProcess();
    } else if (voiceState === "speaking") {
      // Barge-in: immediately cancel audio playback and stop turn
      stopPlayback();
      if (isVoiceContinuous) {
        startRecording();
      } else {
        setVoiceState("idle");
      }
    }
  };

  return (
    <div className="relative inline-flex items-center">
      {/* Voice Mode Toggle Button */}
      <Button
        type="button"
        variant="ghost"
        size="icon"
        onClick={handleButtonClick}
        disabled={disabled || (voiceState === "processing" && isSending)}
        className={`h-10 w-10 rounded-full transition-all relative shrink-0 shadow-sm ${
          voiceState === "listening"
            ? "bg-emerald-50/90 border border-[#059669] text-[#059669] ring-4 ring-[#10B981]/30 animate-pulse"
            : voiceState === "processing"
            ? "bg-emerald-50/90 border border-[#059669] text-[#059669]"
            : voiceState === "speaking"
            ? "bg-emerald-50/90 border border-[#059669] text-[#059669] shadow-md"
            : "bg-emerald-50/90 hover:bg-emerald-100/90 border border-[#059669] text-[#059669]"
        } ${className}`}
        style={{
          background: "rgba(236, 253, 245, 0.9)",
          borderColor: "var(--accent-600, #059669)",
          color: "var(--accent-600, #059669)",
        }}
        title={
          voiceState === "listening"
            ? "Listening... Tap to stop recording."
            : voiceState === "processing"
            ? "Processing voice consultation..."
            : voiceState === "speaking"
            ? "Speaking answer. Tap anytime to interrupt (Barge-in)."
            : "Hands-Free Voice Conversation Mode"
        }
      >
        {voiceState === "idle" && <Headphones className="w-4 h-4 text-[#059669]" />}

        {voiceState === "listening" && (
          <div className="relative flex items-center justify-center">
            <span className="absolute w-7 h-7 rounded-full bg-[#10B981]/30 animate-ping" />
            <Square className="w-3.5 h-3.5 fill-[#059669] text-[#059669]" />
          </div>
        )}

        {voiceState === "processing" && <Loader2 className="w-4 h-4 animate-spin text-[#059669]" />}

        {voiceState === "speaking" && (
          <div className="flex items-center justify-center gap-0.5">
            <span className="w-0.5 h-2.5 bg-[#059669] rounded-full animate-bounce [animation-delay:-0.3s]" />
            <span className="w-0.5 h-4 bg-[#059669] rounded-full animate-bounce [animation-delay:-0.15s]" />
            <span className="w-0.5 h-2.5 bg-[#059669] rounded-full animate-bounce" />
          </div>
        )}
      </Button>

      {/* Voice Continuous Mode Toggle & Quick Settings Button */}
      <button
        type="button"
        onClick={() => setShowSettings(!showSettings)}
        className="absolute -top-1.5 -right-1.5 p-0.5 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700 text-[10px]"
        title="Voice Conversation Settings"
      >
        <Settings2 className="w-3 h-3" />
      </button>

      {/* Settings Dropdown Popover */}
      {showSettings && (
        <div className="absolute bottom-14 right-0 z-50 w-64 p-3 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xl text-xs space-y-2.5">
          <div className="flex items-center justify-between font-semibold text-slate-800 dark:text-slate-200">
            <span>Voice Mode Settings</span>
            <button
              onClick={() => setShowSettings(false)}
              className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-sm"
            >
              &times;
            </button>
          </div>

          <label className="flex items-center justify-between cursor-pointer pt-1 border-t border-slate-100 dark:border-slate-800">
            <span className="text-slate-600 dark:text-slate-300">Continuous Back-and-Forth</span>
            <input
              type="checkbox"
              checked={isVoiceContinuous}
              onChange={(e) => setIsVoiceContinuous(e.target.checked)}
              className="rounded text-emerald-600 focus:ring-emerald-500 h-4 w-4"
            />
          </label>
          <p className="text-[11px] text-slate-400 dark:text-slate-500 leading-tight">
            When enabled, the assistant automatically listens for your next response after speaking.
          </p>
        </div>
      )}

      {/* Error Tooltip / Toast */}
      {errorMessage && (
        <div className="absolute bottom-14 left-1/2 -translate-x-1/2 z-50 whitespace-nowrap px-3 py-1.5 rounded-lg bg-rose-600 text-white text-xs shadow-lg">
          {errorMessage}
        </div>
      )}
    </div>
  );
};
