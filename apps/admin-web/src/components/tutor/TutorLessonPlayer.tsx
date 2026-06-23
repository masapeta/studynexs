"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Pause, Play, RotateCcw, SkipBack, SkipForward, Volume2 } from "lucide-react";
import TutorVisual from "./TutorVisual";
import type { TutorLesson, TutorStep } from "@/lib/student-portal";

type SpeechState = "idle" | "playing" | "paused";

export default function TutorLessonPlayer({ lesson }: { lesson: TutorLesson }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [speechState, setSpeechState] = useState<SpeechState>("idle");
  const [voiceReady, setVoiceReady] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

  const steps = lesson.steps;
  const step: TutorStep | undefined = steps[stepIndex];

  useEffect(() => {
    setVoiceReady(typeof window !== "undefined" && "speechSynthesis" in window);
    return () => {
      window.speechSynthesis?.cancel();
    };
  }, []);

  const stopSpeech = useCallback(() => {
    window.speechSynthesis?.cancel();
    setSpeechState("idle");
    utteranceRef.current = null;
  }, []);

  const speakStep = useCallback(
    (index: number) => {
      const s = steps[index];
      if (!s || !voiceReady) return;
      stopSpeech();
      const utter = new SpeechSynthesisUtterance(s.narration);
      utter.rate = 0.92;
      utter.pitch = 1;
      const voices = window.speechSynthesis.getVoices();
      const en = voices.find((v) => v.lang.startsWith("en-IN")) || voices.find((v) => v.lang.startsWith("en"));
      if (en) utter.voice = en;
      utter.onend = () => setSpeechState("idle");
      utter.onerror = () => setSpeechState("idle");
      utteranceRef.current = utter;
      window.speechSynthesis.speak(utter);
      setSpeechState("playing");
    },
    [steps, voiceReady, stopSpeech]
  );

  const handlePlay = () => {
    if (!voiceReady) return;
    if (speechState === "paused") {
      window.speechSynthesis.resume();
      setSpeechState("playing");
      return;
    }
    speakStep(stepIndex);
  };

  const handlePause = () => {
    if (speechState === "playing") {
      window.speechSynthesis.pause();
      setSpeechState("paused");
    }
  };

  const handleReplay = () => speakStep(stepIndex);

  const goStep = (next: number) => {
    stopSpeech();
    setStepIndex(next);
  };

  useEffect(() => {
    stopSpeech();
  }, [stepIndex, stopSpeech]);

  if (!step) return null;

  return (
    <div className="tutor-player">
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

      <TutorVisual kind={step.visual_kind} caption={step.caption} />

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
          <button type="button" className="btn btn-primary tutor-ctrl-main" onClick={handlePlay}>
            <Play size={22} /> {speechState === "paused" ? "Resume" : "Play voice"}
          </button>
        )}
        <button type="button" className="btn btn-ghost tutor-ctrl" onClick={handleReplay} aria-label="Replay step">
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

      <p className="tutor-voice-hint">
        <Volume2 size={14} style={{ verticalAlign: "middle", marginRight: 4 }} />
        {voiceReady
          ? "Teacher-style voice + diagram — pause or replay any step until it clicks."
          : "Voice not supported in this browser — read the steps below."}
      </p>
    </div>
  );
}
