// Empty = same origin: the Vite dev proxy and nginx both forward /api to the backend.
// On Vercel set VITE_API_URL to the backend URL (e.g. https://<space>.hf.space).
const BASE_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function apiFetch(path, options = {}) {
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new APIError("Серверге қосылу мүмкін болмады.", "NETWORK", 0);
  }
  let data = {};
  try { data = await res.json(); } catch { /* sleeping server returns HTML */ }
  if (!res.ok) {
    if (res.status === 503 || res.status === 502) {
      throw new APIError("Сервер іске қосылып жатыр, бір минуттан кейін қайталаңыз.", "STARTING", res.status);
    }
    const msg =
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.message || "Қате орын алды.";
    throw new APIError(msg, data.detail?.code || "API_ERROR", res.status);
  }
  return data;
}

export class APIError extends Error {
  constructor(message, code, status) {
    super(message);
    this.code   = code;
    this.status = status;
  }
}

export async function fetchDailyGame() {
  return apiFetch("/api/daily");
}

export async function fetchRandomGame() {
  return apiFetch("/api/random");
}

export async function createCustomGame(word) {
  return apiFetch("/api/custom", {
    method: "POST",
    body: JSON.stringify({ word }),
  });
}

export async function submitGuess(gameId, guess, customToken = null) {
  return apiFetch("/api/guess", {
    method: "POST",
    body: JSON.stringify({
      ...(customToken ? { custom_token: customToken } : { game_id: gameId }),
      guess,
    }),
  });
}

// offset only used for close_word — each call gets a different word
export async function fetchHint(gameId, hintType = "category", customToken = null, offset = 0) {
  const q = `hint_type=${hintType}&offset=${offset}`;
  if (customToken) {
    return apiFetch(`/api/hint/custom/${encodeURIComponent(customToken)}?${q}`);
  }
  return apiFetch(`/api/hint/${gameId}?${q}`);
}

/** Give up: returns { secret }. */
export async function fetchReveal(gameId, customToken = null) {
  if (customToken) {
    return apiFetch(`/api/reveal/custom/${encodeURIComponent(customToken)}`);
  }
  return apiFetch(`/api/reveal/${gameId}`);
}

/**
 * Words closest to the secret. The server only answers once `word` is the solution.
 */
export async function fetchSimilarWords(gameId, customToken = null, word = "") {
  const q = `word=${encodeURIComponent(word)}`;
  if (customToken) {
    return apiFetch(`/api/similar/custom/${encodeURIComponent(customToken)}?${q}`);
  }
  return apiFetch(`/api/similar/${gameId}?${q}`);
}
