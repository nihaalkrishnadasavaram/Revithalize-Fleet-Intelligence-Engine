import { formatScore } from "../utils/format.js";
import { scoreTone } from "../utils/tones.js";

export default function ScoreBar({ value, inverse = false }) {
  const clamped = Math.max(0, Math.min(100, value));
  return (
    <div className="score">
      <span className="score-value">{formatScore(value)}</span>
      <div className="score-track">
        <div
          className={`score-fill fill-${scoreTone(value, inverse)}`}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
