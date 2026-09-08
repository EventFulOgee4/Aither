import React, { useEffect, useRef, useState } from "react";
import "./moodcheckin.css";

const MOODS = [
  { emoji: "😔", label: "Sad",       value: "sad",       intensity: 2 },
  { emoji: "😟", label: "Anxious",   value: "anxious",   intensity: 3 },
  { emoji: "😐", label: "Neutral",   value: "neutral",   intensity: 5 },
  { emoji: "🙂", label: "Okay",      value: "neutral",      intensity: 6 },
  { emoji: "😊", label: "Good",      value: "happy",      intensity: 8 },
  { emoji: "😄", label: "Great",     value: "happy",     intensity: 10 },
];

export default function MoodCheckIn({ onLog, onDismiss }) {
  const [selected, setSelected] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const timer = useRef(null);
  useEffect(() => () => clearTimeout(timer.current), []);

  async function handleSelect(mood) {
    if (saving) return;
    setSaving(true);
    setError("");
    setSelected(mood.label);
    try {
      await onLog?.(mood.value, mood.intensity);
      setSubmitted(true);
      timer.current = setTimeout(() => onDismiss?.(), 4000);
    } catch (e) {
      setError("Could not save your mood. Please try again.");
      console.error("Mood log failed:", e);
    } finally {
      setSaving(false);
    }

  }

  return (
    <div className="mood-checkin">
      {error && <p role="alert">{error}</p>}
      {!submitted ? (
        <>
          <div className="mood-checkin-label">How are you feeling right now?</div>
          <div className="mood-checkin-options">
            {MOODS.map((m) => (
              <button
                key={m.label}
                disabled={saving}
                className="mood-option"
                onClick={() => handleSelect(m)}
                title={m.label}
                type="button"
              >
                <span className="mood-emoji">{m.emoji}</span>
                <span className="mood-label">{m.label}</span>
              </button>
            ))}
          </div>
        </>
      ) : (
        <div className="mood-checkin-thanks">
          <span className="mood-thanks-emoji">
            {MOODS.find((m) => m.label === selected)?.emoji}
          </span>
          <span>Thanks for sharing — I'll keep that in mind.</span>
        </div>
      )}
    </div>
  );
}
