export const MAX_HINTS      = 5;   // one-time hints (everything except close_word)
export const MAX_CLOSE_WORD = 10;  // close_word can be used up to 10 times

const HINTS = [
  { type: "category",   icon: "◈", label: "Санат",     sublabel: "Қандай топ?",   color: "#a78bfa" },
  { type: "letter",     icon: "А", label: "1-ші әріп", sublabel: "Басталуы",      color: "#34d399" },
  { type: "length",     icon: "⟷", label: "Ұзындық",   sublabel: "Неше әріп?",    color: "#60a5fa" },
  { type: "far_word",   icon: "○", label: "Алыс сөз",  sublabel: "~200–300 орын", color: "#f87171" },
  { type: "mid_word",   icon: "◎", label: "Орта сөз",  sublabel: "~50–80 орын",   color: "#fb923c" },
  { type: "close_word", icon: "●", label: "Жақын сөз", sublabel: "~20–30 орын",   color: "#4ade80" },
];

export function countRegularHints(hintStates) {
  return HINTS.filter((h) => h.type !== "close_word" && hintStates[h.type]?.result).length;
}

// Word hints have the form "… «word»".
const quotedWord = (text) => text.match(/«(.+)»/)?.[1] || text;

function CloseWordCard({ hint, state, onUse, disabled }) {
  const count   = state.count || 0;
  const results = state.results || [];
  const busy    = !!state.loading;
  const maxed   = count >= MAX_CLOSE_WORD;
  return (
    <button
      type="button"
      className={`hint-card hint-card-wide ${busy ? "hint-busy" : ""} ${maxed ? "hint-locked" : ""}`}
      style={{ "--hc": hint.color }}
      disabled={busy || maxed || disabled}
      onClick={() => onUse(hint.type)}
    >
      <span className="hc-icon" style={{ color: count > 0 ? hint.color : "#4a5568" }}>
        {maxed ? "🔒" : hint.icon}
      </span>
      <div className="hc-body">
        <div className="hc-top-row">
          <span className="hc-label">{hint.label}</span>
          <span className={`hc-counter ${maxed ? "hc-counter-maxed" : ""}`}>{count}/{MAX_CLOSE_WORD}</span>
        </div>
        {results.length === 0 ? (
          <span className="hc-sub">{busy ? "…" : hint.sublabel}</span>
        ) : (
          <div className="close-words-list">
            {results.map((r, i) => <span key={i} className="close-word-badge">{quotedWord(r)}</span>)}
            {!maxed && !busy && !disabled && <span className="close-word-more">+ тағы</span>}
          </div>
        )}
      </div>
    </button>
  );
}

export default function HintsPanel({ hintStates, onUse, disabled }) {
  const used = countRegularHints(hintStates);
  return (
    <div className="hints-panel">
      <div className="hints-used-label">
        <span>Кеңестер</span>
        <span className={used >= MAX_HINTS ? "hints-limit-reached" : ""}>{used}/{MAX_HINTS} пайдаланылды</span>
      </div>
      <div className="hints-grid">
        {HINTS.map((h) => {
          const state = hintStates[h.type] || {};
          if (h.type === "close_word") {
            return <CloseWordCard key={h.type} hint={h} state={state} onUse={onUse} disabled={disabled} />;
          }
          const busy   = !!state.loading;
          const done   = !!state.result;
          const locked = !done && used >= MAX_HINTS;
          return (
            <button
              type="button"
              key={h.type}
              className={`hint-card ${done ? "hint-used" : ""} ${busy ? "hint-busy" : ""} ${locked ? "hint-locked" : ""}`}
              style={{ "--hc": h.color }}
              disabled={!done && (busy || locked || disabled)}
              onClick={() => !done && onUse(h.type)}
            >
              <span className="hc-icon" style={{ color: done ? h.color : "#4a5568" }}>{locked ? "🔒" : h.icon}</span>
              <div className="hc-body">
                <span className="hc-label">{h.label}</span>
                <span className="hc-sub">{busy ? "…" : done ? state.result : locked ? "Лимит" : h.sublabel}</span>
              </div>
              {done && <span className="hc-tick" style={{ color: h.color }}>✓</span>}
            </button>
          );
        })}
      </div>
    </div>
  );
}
