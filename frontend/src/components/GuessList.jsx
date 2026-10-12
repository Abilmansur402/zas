function rankLabel(rank) {
  return rank === 1 ? "1" : rank.toLocaleString();
}

function barWidth(rank) {
  if (rank === 1) return 100;
  const maxRank = 200000;
  const pct = (1 - Math.log10(Math.min(rank, maxRank)) / Math.log10(maxRank)) * 100;
  return Math.max(2, Math.round(pct * 10) / 10);
}

function barClass(color) {
  return { winner: "bar-winner", hot: "bar-green", warm: "bar-orange", cold: "bar-pink" }[color] || "bar-pink";
}

function GuessRow({ guess, rank, color, isLatest }) {
  return (
    <div className={`guess-row ${isLatest ? "guess-latest" : ""}`}>
      <span className={`guess-word-label ${barClass(color)}-text`}>{guess}</span>
      <div className="guess-bar-track">
        <div className={`guess-bar-fill ${barClass(color)}`} style={{ width: `${barWidth(rank)}%` }} />
      </div>
      <span className="guess-bar-rank">{rankLabel(rank)}</span>
    </div>
  );
}

// Like Contexto: the last guess is pinned above the list, and a repeated guess
// is flashed in the list instead of being sent again.
export default function GuessList({ guesses, sortByRank, latestGuess, highlight }) {
  if (guesses.length === 0) return null;
  const last = guesses[guesses.length - 1];
  const list = sortByRank
    ? [...guesses].sort((a, b) => a.rank - b.rank)
    : [...guesses].reverse();

  return (
    <>
      {guesses.length > 1 && (
        <div className="last-guess">
          <span className="last-guess-label">Соңғы болжам</span>
          <GuessRow {...last} isLatest={last.guess === latestGuess} />
        </div>
      )}
      <div className="guess-list">
        {list.map((g) => (
          <div key={g.guess} className={g.guess === highlight ? "guess-dup" : undefined}>
            <GuessRow {...g} isLatest={guesses.length === 1 && g.guess === latestGuess} />
          </div>
        ))}
      </div>
    </>
  );
}
