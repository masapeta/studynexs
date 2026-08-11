"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Pause, Play, RotateCcw, SkipBack, SkipForward, Volume2 } from "lucide-react";
import TutorVisual from "./TutorVisual";
import { fetchTtsStatus, fetchTutorSpeechBlob } from "@/lib/api";
import type { TutorLesson, TutorStep } from "@/lib/student-portal";

/** Microsoft Neural Neerja — must match API TUTOR_TTS_VOICE. */
const NEERJA_VOICE = "en-IN-NeerjaExpressiveNeural";

type SpeechState = "idle" | "playing" | "paused";

export default function TutorLessonPlayer({ lesson }: { lesson: TutorLesson }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [speechState, setSpeechState] = useState<SpeechState>("idle");
  const [ttsStatusLoaded, setTtsStatusLoaded] = useState(false);
  const [cloudEnabled, setCloudEnabled] = useState(false);
  const [voiceError, setVoiceError] = useState("");
  const [activeVoiceLabel, setActiveVoiceLabel] = useState("Neerja");

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objUrlRef = useRef<string | null>(null);
  const cloudEnabledRef = useRef(false);
  const cloudVoiceRef = useRef(NEERJA_VOICE);
  const cloudBackendRef = useRef("edge");

  const steps = lesson.steps;
  const step: TutorStep | undefined = steps[stepIndex];

  useEffect(() => {
    const audio = new Audio();
    audio.onended = () => setSpeechState("idle");
    audio.onerror = () => {
      setSpeechState("idle");
      setVoiceError("Could not play Neerja voice. Try Play again.");
    };
    audioRef.current = audio;

    fetchTtsStatus()
      .then((data) => {
        const enabled = !!data.enabled;
        cloudEnabledRef.current = enabled;
        setCloudEnabled(enabled);
        const v = data.voice || "";
        cloudVoiceRef.current = v.includes("Neerja") ? v : NEERJA_VOICE;
        cloudBackendRef.current = data.backend || "off";
        setActiveVoiceLabel(data.voice_display || "Neerja");
        if (!enabled) {
          setVoiceError(
            "Teacher voice is temporarily unavailable. You can still read the lesson steps below."
          );
        }
      })
      .catch(() => {
        cloudEnabledRef.current = false;
        setCloudEnabled(false);
        setVoiceError(
          "Teacher voice is temporarily unavailable. You can still read the lesson steps below."
        );
      })
      .finally(() => setTtsStatusLoaded(true));

    return () => {
      audio.pause();
      if (objUrlRef.current) URL.revokeObjectURL(objUrlRef.current);
    };
  }, []);

  const stopSpeech = useCallback(() => {
    const a = audioRef.current;
    if (a) {
      a.pause();
      a.currentTime = 0;
    }
    if (objUrlRef.current) {
      URL.revokeObjectURL(objUrlRef.current);
      objUrlRef.current = null;
    }
    setSpeechState("idle");
  }, []);

  const speakStep = useCallback(
    async (index: number) => {
      const s = steps[index];
      if (!s) return;
      stopSpeech();
      setVoiceError("");

      if (!cloudEnabledRef.current) {
        return;
      }

      const voice = cloudVoiceRef.current.includes("Neerja")
        ? cloudVoiceRef.current
        : NEERJA_VOICE;

      for (let attempt = 0; attempt < 2; attempt++) {
        try {
          const { blob, voice: used, voiceDisplay, backend } = await fetchTutorSpeechBlob(
            s.narration,
            voice,
            s.title
          );
          if (!used.includes("Neerja")) {
            throw new Error("wrong voice");
          }
          setActiveVoiceLabel(voiceDisplay);
          cloudBackendRef.current = backend;
          const url = URL.createObjectURL(blob);
          if (objUrlRef.current) URL.revokeObjectURL(objUrlRef.current);
          objUrlRef.current = url;
          const a = audioRef.current;
          if (!a) throw new Error("audio");
          a.src = url;
          await a.play();
          setSpeechState("playing");
          return;
        } catch {
          if (attempt === 1) {
            setVoiceError(
              "Teacher voice is temporarily unavailable. You can still read the lesson steps below."
            );
          }
        }
      }
    },
    [steps, stopSpeech]
  );

  const handlePlay = () => {
    if (!ttsStatusLoaded) return;
    if (speechState === "paused") {
      audioRef.current?.play();
      setSpeechState("playing");
      return;
    }
    void speakStep(stepIndex);
  };

  const handlePause = () => {
    if (speechState !== "playing") return;
    audioRef.current?.pause();
    setSpeechState("paused");
  };

  const handleReplay = () => {
    if (!ttsStatusLoaded) return;
    void speakStep(stepIndex);
  };

  const goStep = (next: number) => {
    stopSpeech();
    setStepIndex(next);
  };

  useEffect(() => {
    stopSpeech();
  }, [stepIndex, stopSpeech]);

  if (!step) return null;

  const voiceHint = cloudEnabled
    ? `${activeVoiceLabel} · English (India) teacher voice`
    : "Teacher voice is off — you can still read the lesson steps below.";

  return (
    <div className="tutor-player tutor-player--split">
      {/* Left column — lesson narrative and controls */}
      <div className="tutor-player__lesson">
      <div className="tutor-player-meta">
        <span className="tutor-badge">{lesson.subject_name}</span>
        {lesson.mastery_pct != null && (
          <span className="tutor-badge muted">{lesson.mastery_pct.toFixed(0)}% mastery</span>
        )}
      </div>
      <h2 className="tutor-lesson-title">{lesson.topic}</h2>
      {lesson.mistake_summary && (
        <p className="tutor-mistake-hint">From your exam: {lesson.mistake_summary}</p>
      )}

      <div className="tutor-step-dots">
        {steps.map((s, i) => (
          <button
            key={s.id}
            type="button"
            className={`tutor-dot${i === stepIndex ? " active" : ""}`}
            onClick={() => goStep(i)}
            aria-label={`Step ${i + 1}: ${s.title}`}
          />
        ))}
      </div>

      <div className="portal-card tutor-step-card">
        <div className="tutor-step-label">
          Step {stepIndex + 1} of {steps.length} · {step.title}
        </div>
        <p className="tutor-narration">{step.narration}</p>
      </div>

      <div className="tutor-controls">
        <button
          type="button"
          className="btn btn-ghost tutor-ctrl"
          onClick={() => goStep(Math.max(0, stepIndex - 1))}
          disabled={stepIndex === 0}
          aria-label="Previous step"
        >
          <SkipBack size={20} />
        </button>
        {speechState === "playing" ? (
          <button type="button" className="btn btn-primary tutor-ctrl-main" onClick={handlePause}>
            <Pause size={22} /> Pause
          </button>
        ) : (
          <button
            type="button"
            className="btn btn-primary tutor-ctrl-main"
            onClick={handlePlay}
            disabled={!ttsStatusLoaded}
          >
            <Play size={22} />{" "}
            {!ttsStatusLoaded ? "Loading Neerja…" : speechState === "paused" ? "Resume" : "Play voice"}
          </button>
        )}
        <button
          type="button"
          className="btn btn-ghost tutor-ctrl"
          onClick={handleReplay}
          disabled={!ttsStatusLoaded}
          aria-label="Replay step"
        >
          <RotateCcw size={20} />
        </button>
        <button
          type="button"
          className="btn btn-ghost tutor-ctrl"
          onClick={() => goStep(Math.min(steps.length - 1, stepIndex + 1))}
          disabled={stepIndex >= steps.length - 1}
          aria-label="Next step"
        >
          <SkipForward size={20} />
        </button>
      </div>

      {voiceError ? <p className="tutor-voice-hint tutor-voice-hint--warn">{voiceError}</p> : null}

      <p className="tutor-voice-hint">
        <Volume2 size={14} style={{ verticalAlign: "middle", marginRight: 4 }} />
        {voiceHint}
      </p>
      </div>

      {/* Right column — the visual explanation stage (reference: figure panel) */}
      <aside className="tutor-player__stage" aria-label="Visual explanation">
        <div className="tutor-stage-card">
          <div className="tutor-stage-head">
            <span className="tutor-stage-kicker">Visual explanation</span>
            <span className="tutor-stage-step">
              Step {stepIndex + 1}/{steps.length}
            </span>
          </div>
          <TutorVisual kind={step.visual_kind} caption={step.caption} />
          {lesson.mastery_pct != null && (
            <div className="tutor-stage-mastery">
              <span className="tutor-stage-mastery__label">Your mastery on this topic</span>
              <div className="tutor-stage-mastery__bar">
                <span
                  className="tutor-stage-mastery__fill"
                  style={{ width: `${Math.max(2, Math.min(100, lesson.mastery_pct))}%` }}
                />
              </div>
              <span className="tutor-stage-mastery__pct">{lesson.mastery_pct.toFixed(0)}%</span>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
