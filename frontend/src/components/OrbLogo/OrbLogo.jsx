import React, { useEffect, useRef, useState } from "react";
import "./orblogo.css";
import { TONES } from "../ToneSelector/ToneSelector";

export default function OrbLogo({ sending = false, compact = false, toneGradient }) {
  const [pulsing, setPulsing] = useState(false);
  const prevToneRef = useRef(toneGradient);

  // Trigger pulse when tone changes
  useEffect(() => {
    if (prevToneRef.current !== toneGradient) {
      prevToneRef.current = toneGradient;
      setPulsing(true);
      const t = setTimeout(() => setPulsing(false), 700);
      return () => clearTimeout(t);
    }
  }, [toneGradient]);

  return (
    <div className={`orb-wrap${compact ? " compact" : ""}`}>
      <div
        className={[
          "orb",
          sending  ? "orb-sending"  : "",
          pulsing  ? "orb-tone-pulse" : "",
        ].filter(Boolean).join(" ")}
      >
        {TONES.map((t) => (
          <div
            key={t.id}
            className="orb-tone-layer"
            style={{
              background: t.gradient,
              opacity: t.gradient === toneGradient ? 1 : 0,
            }}
          />
        ))}
      </div>
    </div>
  );
}