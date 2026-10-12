import { useState } from "react";

export default function CustomForm({ onCreate }) {
  const [word, setWord]       = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState("");

  const submit = async () => {
    const w = word.trim().toLowerCase();
    if (!w || loading) return;
    setLoading(true);
    setError("");
    try {
      await onCreate(w);
      setWord("");
    } catch (err) {
      setError(err.message || "Сөз қабылданмады.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="custom-form">
      <p className="custom-title">Жасырын сөзді енгізіңіз</p>
      <div className="input-row">
        <input
          className="guess-input"
          value={word}
          onChange={(e) => setWord(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Мысалы: үй, жылқы, арман..."
          autoComplete="off" spellCheck={false} autoFocus
        />
        <button className="btn-submit" onClick={submit} disabled={loading || !word.trim()}>
          {loading ? "…" : "Бастау"}
        </button>
      </div>
      {error && <div className="error-msg">{error}</div>}
      <p className="custom-hint">Сөзді енгізіп, сілтемені досыңызға жіберіңіз!</p>
    </div>
  );
}
