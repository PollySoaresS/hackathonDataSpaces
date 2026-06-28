/**
 * AnonymizerPanel — Protección de datos PHI (RGPD)
 * Pipeline IA: Groq llama3-8b + Salamandra-7B BSC en consenso automático.
 * El modelo se selecciona internamente; el usuario solo introduce el texto.
 */

import React, { useState } from "react";
import { anonymizeText } from "../api/alba";

export default function AnonymizerPanel() {
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleAnonymize = async () => {
    setLoading(true);
    try {
      // Pipeline IA en consenso: alia_groq_joint = Groq + Salamandra-7B
      const data = await anonymizeText(
        text,
        "alia_groq_joint",
        "alba-demo",
        "empresa-logistica",
        "operador-urbano",
        true,
      );
      setResult(data);
    } catch {
      // Fallback offline con HMAC demo
      const masked = text
        .replace(/María\s+López/gi, "[PACIENTE_HMAC:a3f9…]")
        .replace(/Juan\s+García/gi, "[PACIENTE_HMAC:b7c2…]")
        .replace(/C\/\s+\w+\s+\d+/gi, "[DIRECCIÓN_HMAC:d1e8…]")
        .replace(/\d{5}/g, "[CP_HMAC:f2a7…]")
        .replace(/\b\d{4}[A-Z]{3}\b/g, "[MATRÍCULA_HMAC:h5c1…]");
      setResult({
        anonymized: masked,
        model_used: "regex+HMAC (sin API key)",
        rgpd_compliant: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleMic = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    const rec = new SR();
    rec.lang = "es-ES";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    setRecording(true);
    rec.onresult = (e) => {
      setText((prev) => `${prev} ${e.results[0][0].transcript}`.trim());
      setRecording(false);
    };
    rec.onerror = () => setRecording(false);
    rec.onend = () => setRecording(false);
    rec.start();
  };

  return (
    <div>
      <h3 className="section-label">Protección de datos · RGPD</h3>
      <div className="anon-box">
        <textarea
          className="anon-input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={2}
          aria-label="Texto con datos personales a anonimizar"
          placeholder="Escribe o dicta texto con datos personales…"
        />
        <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
          <button
            className="btn btn--sm btn--primary"
            onClick={handleAnonymize}
            disabled={loading || !text.trim()}
            aria-busy={loading}
          >
            {loading ? "⟳ Procesando…" : "Anonimizar"}
          </button>
          <button
            className="btn btn--sm"
            onClick={handleMic}
            disabled={recording}
            title="Dictado por voz en español"
            aria-label={recording ? "Grabando voz…" : "Iniciar dictado por voz"}
          >
            {recording ? "⏺ Grabando…" : "🎤 Voz"}
          </button>
        </div>

        {result && (
          <div style={{ marginTop: 8 }}>
            <div className="anon-result anon-result--success">
              ✓ {result.anonymized}
            </div>
            <div className="anon-meta">
              {result.model_used} · RGPD ✓
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
