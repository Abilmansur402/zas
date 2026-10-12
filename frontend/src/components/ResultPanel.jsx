function tierClass(i) {
  return i < 8 ? "sim-gold" : i < 20 ? "sim-green" : i < 40 ? "sim-yellow" : "sim-gray";
}

export default function ResultPanel({ won, secret, guesses, similarWords, loadingSimilar, onShare, onNewGame }) {
  const guessed = new Set(guesses.map((g) => g.guess));
  return (
    <>
      <div className={`win-banner ${won ? "" : "lose-banner"}`}>
        <span className="win-icon">{won ? "🏆" : "🏳️"}</span>
        <div>
          <div className="win-title">
            {won ? "Керемет!" : <>Жасырын сөз: <span className="secret-word">{secret}</span></>}
          </div>
          <div className="win-sub">
            {won ? `${guesses.length} болжаммен таптыңыз!` : `${guesses.length} болжамнан кейін берілдіңіз.`}
          </div>
        </div>
        <div className="win-actions">
          <button className="btn-new-game" onClick={onShare}>📤 Бөлісу</button>
          <button className="btn-new-game" onClick={onNewGame}>Жаңа ойын</button>
        </div>
      </div>

      <div className="similar-section">
        <div className="similar-header">
          <span className="similar-title">Жасырын сөзге жақын топ-60</span>
          {loadingSimilar && <span className="similar-loading">жүктелуде…</span>}
        </div>
        {similarWords.length > 0 && (
          <div className="similar-list">
            {similarWords.slice(0, 60).map((item, i) => (
              <div key={item.word} className={`similar-item ${tierClass(i)} ${guessed.has(item.word) ? "sim-guessed" : ""}`}>
                <span className="sim-rank">#{item.rank}</span>
                <span className="sim-word">{item.word}</span>
                {guessed.has(item.word) && <span className="sim-tag">✓</span>}
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
