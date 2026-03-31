import React from "react";
import "./orblogo.css";
import { TONES } from "../ToneSelector/ToneSelector";

export default function OrbLogo({ sending = false, compact = false, toneGradient }) {
  return (
    <div className={`orb-wrap${compact ? " compact" : ""}`}>
      <div className={`orb${sending ? " orb-sending" : ""}`}>
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
