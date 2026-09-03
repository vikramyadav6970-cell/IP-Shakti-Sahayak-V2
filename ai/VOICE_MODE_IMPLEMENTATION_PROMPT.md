# IP-SAKTI Sahayak — Full Voice Conversation Mode

## CONTEXT

The chat input currently has a mic button that transcribes speech into the
text field (dictation only — user still reads and sends manually). This task
adds a second, separate button that enables a full hands-free voice
conversation: user speaks, the query is transcribed and answered through the
existing RAG pipeline exactly as today, and the answer is spoken back aloud
via Sarvam's Text-to-Speech API, in the same language the user spoke.

**Do not touch the existing dictation mic button or its behavior.** This is
an additive second control, not a replacement.

---

## 1. UI — New Control

Add a second icon button next to the existing mic button (distinct icon —
e.g. a waveform or headset icon, not a duplicate mic) with four visual
states:

- **Idle** — default appearance, ready to start.
- **Listening** — actively recording (e.g. pulsing ring/waveform
  animation), tapping again manually stops recording early.
- **Processing** — spinner/existing loading indicator style while
  STT → RAG → TTS runs. Reuse the app's existing "thinking" indicator
  styling rather than inventing a new one.
- **Speaking** — answer audio is playing; tapping the button during this
  state **interrupts playback immediately** (barge-in) and returns to
  Idle/Listening — do not force the user to let a long answer finish
  before they can speak again.

Auto-stop recording on ~1.5–2s of silence (standard voice-UI pattern) in
addition to manual tap-to-stop, so the user doesn't have to remember to
tap stop every time.

---

## 2. FRONTEND FLOW

1. Tap button → request mic permission (if not already granted) →
   `MediaRecorder` starts recording to a Blob (webm/opus or wav, whichever
   the existing dictation mic already uses — reuse that recording setup
   rather than building a second one).
2. On auto-stop or manual stop → send the audio Blob to a new backend
   endpoint (Section 3) as multipart/form-data, alongside the current
   conversation_id / product-context state exactly as the existing text
   chat flow already sends it.
3. While waiting for the response, show the Processing state.
4. On response: display the answer text in the chat UI exactly as a normal
   text response would (don't skip the visible transcript — voice mode
   should never be audio-only, always show the text too, for accessibility
   and so the user can re-read it). Simultaneously auto-play the returned
   audio.
5. On playback end (or barge-in interruption): return to Idle, or to
   Listening automatically if you want continuous back-and-forth without
   re-tapping each turn — **make this a user setting/toggle, not a fixed
   behavior**, since some users will want to review each answer before
   continuing and others will want a hands-free back-and-forth.
6. If TTS synthesis fails for any reason, fall back silently to
   text-only — show the answer text normally, skip audio, do not block or
   error out the whole turn. Voice is an enhancement layer, never a
   blocking dependency of getting an answer.

---

## 3. BACKEND — New/Extended Endpoint

New endpoint, e.g. `POST /api/v1/chat/voice`:

1. **Receive audio** (multipart) + existing chat context fields.
2. **STT**: transcribe via Sarvam's Speech-to-Text (or Speech-to-Text-
   Translate if you want the transcription step itself to also detect/
   handle non-English input) — reuse whatever Sarvam STT integration the
   existing dictation mic button already calls; do not build a second STT
   client.
3. **Run the transcribed text through the existing chat pipeline
   unchanged** — same intent classification, multilingual
   translate-to-English, orchestration/retrieval, grounding, synthesis,
   translate-back-to-user-language — this endpoint should not duplicate or
   fork any of that logic, only wrap it.
4. **TTS**: once the final answer text (already translated into the user's
   language by the existing multilingual pipeline) is ready, call Sarvam's
   Text-to-Speech endpoint on that text:

   ```
   POST https://api.sarvam.ai/text-to-speech
   Headers: api-subscription-key: {SARVAM_API_KEY}
   Body: {
     "text": "<final answer text, already in the user's target language>",
     "target_language_code": "<same language code used for the translate-back step>",
     "speaker": "<pick one reasonable default per supported language>",
     "model": "bulbul:v3",
     "pace": 1.0
   }
   ```

   Response is JSON with an `audios` array of base64-encoded WAV chunks
   (per Sarvam's current API). Decode/join and either:
   - stream the decoded WAV bytes back to the frontend directly as the
     response body (`audio/wav`), or
   - return it as a base64 string in the JSON response alongside the
     answer text, and let the frontend construct a data URI for playback.

   Pick whichever is simpler given the existing response-handling code in
   the frontend chat client — don't over-engineer streaming for v1.

5. **Timeout/error handling for the TTS call specifically**: wrap it in a
   try/except that, on any failure (timeout, API error, unsupported
   language/speaker combination), logs the failure and returns the answer
   **without audio** rather than failing the whole request — the text
   answer is the important part; audio is additive. Mirror the same
   resilience pattern already used for the translation service (timeout +
   short retry, then graceful fallback).

---

## 4. LANGUAGE & SPEAKER SELECTION

- Use the same language code the existing multilingual pipeline already
  detected/translated to for the answer — do not add a second language
  detection step.
- Pick one default speaker per supported language (check Sarvam's current
  `/voices` or docs for available speakers per language — don't hardcode
  a speaker that may not exist for a given language without checking).
  A single sensible default per language is enough for v1; a speaker
  picker in settings is a nice-to-have, not required now.

---

## 5. TESTING

- End-to-end: speak an English query → confirm transcription, answer text,
  and spoken answer audio all match and play correctly.
- Same for at least one non-English language already supported by the
  existing multilingual flow (e.g. Hindi) — confirm STT correctly
  transcribes Hindi speech, the answer is generated and translated back to
  Hindi as it already does today, and TTS speaks it in Hindi, not English.
- Barge-in: start playback, tap the button mid-sentence, confirm audio
  stops immediately and the UI returns to a usable state.
- Failure injection: simulate a TTS API failure (e.g. temporarily break
  the API key) and confirm the turn still completes with visible text and
  no audio, rather than erroring out the whole chat turn.
- Confirm the existing dictation-only mic button and its flow are
  completely unaffected by this change.

## DELIVERABLE

- New voice-mode button + 4-state UI in the chat input component
- `POST /api/v1/chat/voice` endpoint wrapping the existing chat pipeline
  with STT in front and TTS after
- Graceful fallback to text-only on any TTS failure
- Barge-in interruption support
- Tests covering English + one Indic language + failure fallback + barge-in
