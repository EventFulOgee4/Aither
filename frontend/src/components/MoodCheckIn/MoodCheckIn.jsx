import React, { useState } from "react";
import "./moodcheckin.css";

const MOODS = [
  { emoji: "😔", label: "Sad",       value: "sad",       intensity: 2 },
  { emoji: "😟", label: "Anxious",   value: "anxious",   intensity: 3 },
  { emoji: "😐", label: "Neutral",   value: "neutral",   intensity: 5 },
  { emoji: "🙂", label: "Okay",      value: "okay",      intensity: 6 },
  { emoji: "😊", label: "Good",      value: "good",      intensity: 8 },
  { emoji: "😄", label: "Great",     value: "great",     intensity: 10 },
];

export default function MoodCheckIn({ onLog, onDismiss }) {
  const [selected, setSelected] = useState(null);
  const [submitted, setSubmitted] = useState(false);

  async function handleSelect(mood) {
    setSelected(mood.value);
    setSubmitted(true);
    try {
      await onLog?.(mood.value, mood.intensity);
    } catch (e) {
      console.error("Mood log failed:", e);
    }
    // Auto-dismiss after a short delay
    setTimeout(() => onDismiss?.(), 1800);
  }

  return (
    <div className="mood-checkin">
      {!submitted ? (
        <>
          <div className="mood-checkin-label">How are you feeling right now?</div>
          <div className="mood-checkin-options">
            {MOODS.map((m) => (
              <button
                key={m.value}
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
            {MOODS.find((m) => m.value === selected)?.emoji}
          </span>
          <span>Thanks for sharing — I'll keep that in mind.</span>
        </div>
      )}
    </div>
  );
}