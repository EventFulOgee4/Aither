import { useMemo } from "react";
import "./contextmeter.css";

const MAX_TOKENS = 2048;
const TOKENS_PER_MESSAGE = 85;

export default function ContextMeter({ messageCount }) {
  const usage = useMemo(() => {
    const used = Math.min(messageCount * TOKENS_PER_MESSAGE, MAX_TOKENS);
    return Math.round((used / MAX_TOKENS) * 100);
  }, [messageCount]);

  if (messageCount === 0) return null;

  const isCritical = usage >= 80;
  const isWarning = usage >= 60;

  return (
    <div className="context-meter">
      <div className="context-header">
        <span className="context-label">Context Window</span>
        <span className={"context-value" + (isCritical ? " critical" : isWarning ? " warning" : "")}>
          {usage}%
        </span>
      </div>
      <div className="context-track">
        <div
          className={"context-fill" + (isCritical ? " critical" : isWarning ? " warning" : "")}
          style={{ width: usage + "%" }}
        />
      </div>
    </div>
  );
}
