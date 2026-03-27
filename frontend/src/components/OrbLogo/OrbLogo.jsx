import React from "react";
import "./orblogo.css";

export default function OrbLogo({ sending = false, compact = false }) {
  return (
    <div className={`orb-wrap${compact ? " compact" : ""}`}>
      <div className={`orb${sending ? " orb-sending" : ""}`} />
    </div>
  );
}