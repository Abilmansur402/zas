// Custom games are shared as ?c=<token>.
export function readCustomTokenFromUrl() {
  try { return new URLSearchParams(window.location.search).get("c"); } catch { return null; }
}

export function setCustomTokenInUrl(token) {
  try {
    const url = new URL(window.location.href);
    if (token) url.searchParams.set("c", token); else url.searchParams.delete("c");
    window.history.replaceState(null, "", url);
  } catch {}
}

export function customGameLink(token) {
  return `${window.location.origin}${window.location.pathname}?c=${encodeURIComponent(token)}`;
}

export async function shareOrCopy(text) {
  if (navigator.share) {
    try { await navigator.share({ text }); return "shared"; } catch {}
  }
  try { await navigator.clipboard.writeText(text); return "copied"; } catch { return "failed"; }
}

export function buildResultText({ gameMode, gameId, guesses, hintsUsed, gaveUp }) {
  const count = (c) => guesses.filter((g) => g.color === c).length;
  const title = gameMode === "daily" ? `Жасырын Сөз #${gameId}`
              : gameMode === "custom" ? "Жасырын Сөз · досымның сөзі"
              : "Жасырын Сөз · кездейсоқ";
  const outcome = gaveUp
    ? `🏳️ ${guesses.length} болжамнан кейін берілдім`
    : `${guesses.length} болжаммен таптым!`;
  return [
    title,
    `${outcome}${hintsUsed ? ` 💡${hintsUsed}` : ""}`,
    `🟩 ${count("hot")}  🟧 ${count("warm")}  🟥 ${count("cold")}`,
    window.location.origin,
  ].join("\n");
}
