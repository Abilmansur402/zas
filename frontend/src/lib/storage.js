// Only the daily game is persisted, so random games never overwrite it.
const STORAGE_KEY = "zhasyrynsoz_v3";
const LEGACY_KEY  = "zhasyrynsoz_v2";  // { gameId, guesses, won }

export function loadDailyState(gameId) {
  try {
    const raw = localStorage.getItem(STORAGE_KEY) || localStorage.getItem(LEGACY_KEY);
    if (!raw) return null;
    const p = JSON.parse(raw);
    return p.gameId === gameId ? p : null;
  } catch { return null; }
}

export function saveDailyState(state) {
  try {
    // Drop transient "loading" flags from hints before saving.
    const hints = Object.fromEntries(
      Object.entries(state.hints || {}).map(([k, { loading, ...rest }]) => [k, rest])
    );
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...state, hints }));
  } catch {}
}
