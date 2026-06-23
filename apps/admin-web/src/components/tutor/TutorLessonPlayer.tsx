"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Pause, Play, RotateCcw, SkipBack, SkipForward, Volume2 } from "lucide-react";
import TutorVisual from "./TutorVisual";
import { API_URL, TENANT_SLUG, api, getAccessToken } from "@/lib/api";
import type { TutorLesson, TutorStep } from "@/lib/student-portal";

type SpeechState = "idle" | "playing" | "paused";

// Prefer a soft female Indian-English voice (e.g. Windows "Heera", Azure "Neerja",
// Chrome "English (India)"). Avoid the male Indian voices ("Ravi" etc.).
const FEMALE_INDIAN = /(heera|neerja|aarohi|ananya|kalpana|swara|asha|veena|priya|isha|female)/i;
const MALE_HINT = /(ravi|prabhat|madhur|hemant|valluvar|\bmale\b)/i;

function pickTeacherVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (!voices.length) return null;
  const en = voices.filter((v) => (v.lang || "").toLowerCase().startsWith("en"));
  const indian = en.filter(
    (v) => (v.lang || "").toLowerCase() === "en-in" || /india/i.test(v.name)
  );
  return (
    indian.find((v) => FEMALE_INDIAN.test(v.name) && !MALE_HINT.test(v.name)) ||
    indian.find((v) => !MALE_HINT.test(v.name)) ||
    indian[0] ||
    en.find((v) => FEMALE_INDIAN.test(v.name) && !MALE_HINT.test(v.name)) ||
    en[0] ||
    null
  );
}

export default function TutorLessonPlayer({ lesson }: { lesson: TutorLesson }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [speechState, setSpeechState] = useState<SpeechState>("idle");
  const [voiceReady, setVoiceReady] = useState(false);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const voiceRef = useRef<SpeechSynthesisVoice | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objUrlRef = useRef<string | null>(null);
  const cloudRef = useRef(false); // cloud Neural TTS available?
  const modeRef = useRef<"cloud" | "web">("web"); // active playback path
  const [cloudReady, setCloudReady] = useState(false);

  const steps = lesson.steps;
  const step: TutorStep | undefined = steps[stepIndex];

  useEffect(() => {
    const supported = typeof window !== "undefined" && "speechSynthesis" in window;
    setVoiceReady(supported);
    // getVoices() is often empty on first call — voices arrive async via "voiceschanged".
    const load = () => {
      voiceRef.current = pickTeacherVoice(window.speechSynthesis.getVoices());
    };
    if (supported) {
      load();
      window.speechSynthesis.addEventListener?.("voiceschanged", load);
    }
    // Cloud Neural TTS (soft female Indian voice) when configured; else Web Speech.
    const audio = new Audio();
    audio.onended = () => setSpeechState("idle");
    audio.onerror = () => setSpeechState("idle");
    audioRef.current = audio;
    api("/api/v1/tutor/tts/status")
      .then((r: any) => {
        cloudRef.current = !!r?.data?.enabled;
        setCloudReady(cloudRef.current);
      })
      .catch(() => {});
    return () => {
      if (supported) window.speechSynthesis.removeEventListener?.("voiceschanged", load);
      window.speechSynthesis?.cancel();
      audio.pause();
      if (objUrlRef.current) URL.revokeObjectURL(objUrlRef.current);
    };
  }, []);

  const stopSpeech = useCallback(() => {
    window.speechSynthesis?.cancel();
    const a = audioRef.current;
    if (a) {
      a.pause();
      a.currentTime = 0;
    }
    if (objUrlRef.current) {
      URL.revokeObjectURL(objUrlRef.current);
      objUrlRef.current = null;
    }
    utteranceRef.current = null;
    setSpeechState("idle");
  }, []);

  const playWeb = useCallback(
    (index: number) => {
      const s = steps[index];
      if (!s || !voiceReady) return;
      const utter = new SpeechSynthesisUtterance(s.narration);
      utter.rate = 0.88; // a touch slower — calmer, clearer for a young learner
      utter.pitch = 1.08; // gently higher — softer, warmer
      const voice = voiceRef.current ?? pickTeacherVoice(window.speechSynthesis.getVoices());
      if (voice) utter.voice = voice;
      utter.lang = voice?.lang || "en-IN"; // bias to Indian English even on a default voice
      utter.onend = () => setSpeechState("idle");
      utter.onerror = () => setSpeechState("idle");
      utteranceRef.current = utter;
      modeRef.current = "web";
      window.speechSynthesis.speak(utter);
      setSpeechState("playing");
    },
    [steps, voiceReady]
  );

  const speakStep = useCallback(
    async (index: number) => {
      const s = steps[index];
      if (!s) return;
      stopSpeech();
      if (!cloudRef.current) {
        playWeb(index);
        return;
      }
      // Cloud Neural TTS — soft female Indian voice; fall back to Web Speech on any error.
      try {
        const res = await fetch(`${API_URL}/api/v1/tutor/tts`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${getAccessToken()}`,
            "X-Tenant-Slug": TENANT_SLUG,
          },
          body: JSON.stringify({ text: s.narration }),
          credentials: "include",
        });
        if (!res.ok) throw new Error("tts");
        const url = URL.createObjectURL(await res.blob());
        objUrlRef.current = url;
        const a = audioRef.current;
        if (!a) throw new Error("audio");
        a.src = url;
        modeRef.current = "cloud";
        await a.play();
        setSpeechState("playing");
      } catch {
        cloudRef.current = false; // give up on cloud for the rest of the session
        playWeb(index);
      }
    },
    [steps, stopSpeech, playWeb]
  );

  const handlePlay = () => {
    if (speechState === "paused") {
      if (modeRef.current === "cloud") audioRef.current?.play();
      else window.speechSynthesis.resume();
      setSpeechState("playing");
      return;
    }
    speakStep(stepIndex);
  };

  const handlePause = () => {
    if (speechState !== "playing") return;
    if (modeRef.current === "cloud") audioRef.current?.pause();
    else window.speechSynthesis.pause();
    setSpeechState("paused");
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
        {voiceReady || cloudReady
          ? cloudReady
            ? "Soft Indian teacher voice + diagram — pause or replay any step until it clicks."
            : "Teacher-style voice + diagram — pause or replay any step until it clicks."
          : "Voice not supported in this browser — read the steps below."}
      </p>
    </div>
  );
}
