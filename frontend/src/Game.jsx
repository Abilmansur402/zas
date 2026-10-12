import { useState, useEffect, useRef, useCallback } from "react";
import {
  fetchDailyGame, fetchRandomGame, createCustomGame,
  submitGuess, fetchHint, fetchSimilarWords, fetchReveal, APIError,
} from "./api";
import { saveGameToHistory } from "./Stats";
import { loadDailyState, saveDailyState } from "./lib/storage";
import {
  readCustomTokenFromUrl, setCustomTokenInUrl, customGameLink, shareOrCopy, buildResultText,
} from "./lib/share";
import GuessList from "./components/GuessList";
import HintsPanel, { MAX_HINTS, MAX_CLOSE_WORD, countRegularHints } from "./components/HintsPanel";
import ResultPanel from "./components/ResultPanel";
import CustomForm from "./components/CustomForm";

const EMPTY_GAME = { guesses: [], won: false, gaveUp: false, secret: null, hints: {} };

export default function Game() {
  const [gameId, setGameId]           = useState(null);
  const [customToken, setCustomToken] = useState(null);
  const [gameMode, setGameMode]       = useState("daily");
  const [game, setGame]               = useState(EMPTY_GAME);
  const [similarWords, setSimilarWords]     = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [input, setInput]             = useState("");
  const [loading, setLoading]         = useState(false);
  const [initFailed, setInitFailed]   = useState(false);
  const [error, setError]             = useState("");
  const [shareNote, setShareNote]     = useState("");
  const [showCustomForm, setShowCustomForm] = useState(false);
  const [showHints, setShowHints]     = useState(false);
  const [sortByRank, setSortByRank]   = useState(true);
  const [latestGuess, setLatestGuess] = useState(null);
  const [dupGuess, setDupGuess]       = useState(null);
  const inputRef = useRef(null);
  const timers   = useRef({});

  const { guesses, won, gaveUp, hints: hintStates } = game;
  const finished = won || gaveUp;
  const solution = won ? guesses.find((g) => g.rank === 1)?.guess : game.secret;
  const ready    = gameId !== null || !!customToken;

  // ── Flash messages ────────────────────────────
  const flash = useCallback((key, setter, msg, ms) => {
    clearTimeout(timers.current[key]);
    setter(msg);
    timers.current[key] = setTimeout(() => setter(""), ms);
  }, []);
  const showError = useCallback((msg, ms = 3000) => flash("error", setError, msg, ms), [flash]);
  const showNote  = useCallback((msg, ms = 2500) => flash("note", setShareNote, msg, ms), [flash]);

  // ── Game setup ────────────────────────────────
  const startGame = useCallback(({ mode, id = null, token = null, saved = null }) => {
    setGameMode(mode); setGameId(id); setCustomToken(token);
    setGame(saved ? { ...EMPTY_GAME, ...saved } : EMPTY_GAME);
    setSimilarWords([]); setShowCustomForm(false); setInput(""); setError("");
    setCustomTokenInUrl(token);
    inputRef.current?.focus();
  }, []);

  const startDaily = useCallback(async () => {
    try {
      const d = await fetchDailyGame();
      setInitFailed(false);
      startGame({ mode: "daily", id: d.game_id, saved: loadDailyState(d.game_id) });
    } catch (err) {
      setInitFailed(true);
      showError(err.message || "Серверге қосылу мүмкін болмады.", 5000);
    }
  }, [startGame, showError]);

  const startRandom = async () => {
    try {
      const d = await fetchRandomGame();
      startGame({ mode: "random", id: d.game_id });
    } catch (err) { showError(err.message); }
  };

  const handleCreateCustom = async (word) => {
    const { custom_token } = await createCustomGame(word);  // errors are shown by the form
    startGame({ mode: "custom", token: custom_token });
    const how = await shareOrCopy(`Жасырын Сөз: мен бір сөз ойладым, тауып көр! ${customGameLink(custom_token)}`);
    if (how === "copied") showNote("Сілтеме көшірілді — досыңызға жіберіңіз!", 4000);
  };

  useEffect(() => {
    const token = readCustomTokenFromUrl();
    if (token) startGame({ mode: "custom", token });
    else startDaily();
  }, [startGame, startDaily]);

  useEffect(() => {
    if (gameMode === "daily" && gameId !== null) saveDailyState({ gameId, ...game });
  }, [gameMode, gameId, game]);

  // Closest words are shown once the game is over (also after a reload).
  useEffect(() => {
    if (!finished || !solution) return;
    let cancelled = false;
    setLoadingSimilar(true);
    fetchSimilarWords(gameId, customToken, solution)
      .then((data) => { if (!cancelled) setSimilarWords(data.similar || []); })
      .catch(() => {})
      .finally(() => { if (!cancelled) setLoadingSimilar(false); });
    return () => { cancelled = true; };
  }, [finished, solution, gameId, customToken]);

  const recordResult = (didWin, secretWord, guessCount) => saveGameToHistory({
    gameId, customToken, mode: gameMode, won: didWin, guessCount, secretWord, ts: Date.now(),
  });

  // ── Guess ─────────────────────────────────────
  const handleSubmit = async () => {
    const word = input.trim().toLowerCase();
    if (!word || loading || finished || !ready) return;
    if (guesses.some((g) => g.guess === word)) {
      setInput("");
      setDupGuess(word);
      setTimeout(() => setDupGuess(null), 1200);
      showError("Бұл сөзді бұрын болжадыңыз.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const r = await submitGuess(gameId, word, customToken);
      const entry = { guess: r.guess, rank: r.rank, color: r.color, closeness_pct: r.closeness_pct };
      setGame((g) => ({ ...g, guesses: [...g.guesses, entry], won: r.found }));
      setLatestGuess(r.guess);
      setTimeout(() => setLatestGuess(null), 1500);
      setInput("");
      if (r.found) recordResult(true, r.guess, guesses.length + 1);
    } catch (err) {
      if (err instanceof APIError && err.code === "WORD_NOT_FOUND") {
        showError(`«${word}» — сөздікте жоқ.`);
      } else if (err instanceof APIError && err.status === 404 && customToken) {
        showError("Бұл сілтеме жарамсыз. Күнделікті ойынға ауысыңыз.", 5000);
      } else {
        showError(err.message || "Қате орын алды.");
      }
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  // ── Give up ───────────────────────────────────
  const handleGiveUp = async () => {
    if (finished || !ready || !window.confirm("Берілесіз бе? Жасырын сөз ашылады.")) return;
    try {
      const { secret } = await fetchReveal(gameId, customToken);
      setGame((g) => ({ ...g, gaveUp: true, secret }));
      recordResult(false, secret, guesses.length);
    } catch (err) { showError(err.message); }
  };

  // ── Hints ─────────────────────────────────────
  const setHint = (type, patch) =>
    setGame((g) => ({ ...g, hints: { ...g.hints, [type]: { ...g.hints[type], ...patch } } }));

  const handleHint = async (type) => {
    const prev = hintStates[type] || {};
    if (prev.loading || finished) return;
    const isClose = type === "close_word";
    if (isClose ? (prev.count || 0) >= MAX_CLOSE_WORD
                : prev.result || countRegularHints(hintStates) >= MAX_HINTS) return;

    setHint(type, { loading: true });
    try {
      const { hint } = await fetchHint(gameId, type, customToken, isClose ? prev.count || 0 : 0);
      setHint(type, isClose
        ? { loading: false, count: (prev.count || 0) + 1, results: [...(prev.results || []), hint] }
        : { loading: false, result: hint });
    } catch (err) {
      setHint(type, { loading: false });
      showError(err.message || "Кеңес алынбады.");
    }
  };

  const hintsUsed = countRegularHints(hintStates) + (hintStates.close_word?.count || 0);

  const handleShareResult = async () => {
    const how = await shareOrCopy(buildResultText({ gameMode, gameId, guesses, hintsUsed, gaveUp }));
    if (how === "copied") showNote("Нәтиже көшірілді!");
  };

  const handleCopyCustomLink = async () => {
    const how = await shareOrCopy(customGameLink(customToken));
    if (how === "copied") showNote("Сілтеме көшірілді!");
  };

  // ── Render ────────────────────────────────────
  const bestRank = guesses.reduce((b, g) => Math.min(b, g.rank), Infinity);

  return (
    <div className="game-wrap">
      <div className="mode-bar">
        <button className={`mode-btn ${gameMode === "daily"  ? "mode-active" : ""}`} onClick={startDaily}>Күнделікті</button>
        <button className={`mode-btn ${gameMode === "random" ? "mode-active" : ""}`} onClick={startRandom}>Кездейсоқ 🎲</button>
        <button className={`mode-btn ${gameMode === "custom" ? "mode-active" : ""}`} onClick={() => setShowCustomForm((v) => !v)}>Өз сөзім ✏️</button>
      </div>

      {showCustomForm && <CustomForm onCreate={handleCreateCustom} />}

      {gameMode === "custom" && customToken && !finished && (
        <div className="custom-active">
          <span>Досыңыздың сөзі</span>
          <button className="ctrl-btn" onClick={handleCopyCustomLink}>🔗 Сілтеме</button>
        </div>
      )}

      {shareNote && <div className="share-note">{shareNote}</div>}

      {initFailed && !ready && (
        <div className="error-msg retry-row">
          <span>Серверге қосылу мүмкін болмады.</span>
          <button className="ctrl-btn" onClick={startDaily}>↻ Қайталау</button>
        </div>
      )}

      <div className="top-bar">
        <span className="top-guesses">
          БОЛЖАМДАР: <strong>{guesses.length}</strong>
          {guesses.length > 0 && (
            <span className="top-best"> · Жақын: <strong>{bestRank === 1 ? "★" : bestRank.toLocaleString()}</strong></span>
          )}
        </span>
        <div className="top-controls">
          {guesses.length > 1 && (
            <button className="ctrl-btn" onClick={() => setSortByRank((v) => !v)}>
              {sortByRank ? "↕ Нөмір" : "↕ Уақыт"}
            </button>
          )}
          <button className={`ctrl-btn ${showHints ? "ctrl-active" : ""}`} onClick={() => setShowHints((v) => !v)}>
            Кеңес {showHints ? "▲" : "▼"}
          </button>
          {!finished && guesses.length > 0 && (
            <button className="ctrl-btn ctrl-danger" onClick={handleGiveUp}>🏳️ Берілу</button>
          )}
        </div>
      </div>

      {!finished && (
        <div className="input-row">
          <input
            ref={inputRef}
            className="guess-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            placeholder="Сөз жазыңыз..."
            disabled={loading || !ready}
            autoFocus autoComplete="off" autoCorrect="off" autoCapitalize="off" spellCheck={false}
          />
          <button className="btn-submit" onClick={handleSubmit} disabled={loading || !input.trim() || !ready}>
            {loading ? "…" : "Болжау"}
          </button>
        </div>
      )}

      {error && <div className="error-msg">{error}</div>}

      {showHints && <HintsPanel hintStates={hintStates} onUse={handleHint} disabled={finished || !ready} />}

      {finished && (
        <ResultPanel
          won={won}
          secret={solution}
          guesses={guesses}
          similarWords={similarWords}
          loadingSimilar={loadingSimilar}
          onShare={handleShareResult}
          onNewGame={startRandom}
        />
      )}

      <GuessList guesses={guesses} sortByRank={sortByRank} latestGuess={latestGuess} highlight={dupGuess} />
    </div>
  );
}
