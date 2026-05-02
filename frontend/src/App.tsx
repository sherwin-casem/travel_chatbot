import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiError, fetchHealth, postChat } from "./api/client";
import type { ChatResponse } from "./api/types";
import { ErrorBanner } from "./components/ErrorBanner";

const SESSION_KEY = "travel_chatbot_session_id";

function renderLiteMarkdown(text: string): string {
  const esc = (s: string) =>
    s
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  let t = esc(text);
  t = t.replaceAll(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  t = t.replaceAll(
    /\[(.+?)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>',
  );
  return t.split("\n").join("<br />");
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(() => sessionStorage.getItem(SESSION_KEY));
  const [messages, setMessages] = useState<{ role: "user" | "assistant"; html: string; meta?: ChatResponse }[]>(
    [],
  );
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [health, setHealth] = useState<{
    status: string;
    kb: number;
    hint?: string | null;
  } | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [bannerError, setBannerError] = useState<ApiError | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  const sessionLabel = useMemo(
    () => (sessionId ? `Session ${sessionId.slice(0, 8)}…` : "New conversation"),
    [sessionId],
  );

  const scrollToEnd = useCallback(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToEnd();
  }, [messages, scrollToEnd]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const h = await fetchHealth();
        if (!cancelled) {
          setHealth({ status: h.status, kb: h.kb_chunks, hint: h.hint });
          setHealthError(null);
        }
      } catch (e) {
        if (cancelled) return;
        if (e instanceof ApiError) {
          setHealthError(`${e.code}: ${e.message}`);
        } else if (e instanceof Error) {
          setHealthError(e.message);
        } else {
          setHealthError("Could not reach the API.");
        }
        setHealth(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBannerError(null);
    setMessages((m) => [...m, { role: "user", html: renderLiteMarkdown(text) }]);
    setBusy(true);
    try {
      const data = await postChat(text, sessionId);
      if (!sessionId) {
        sessionStorage.setItem(SESSION_KEY, data.session_id);
        setSessionId(data.session_id);
      }
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          html: renderLiteMarkdown(data.answer),
          meta: data,
        },
      ]);
    } catch (err) {
      if (err instanceof ApiError) {
        setBannerError(err);
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            html: renderLiteMarkdown(
              `**Could not complete request**\n\n${err.message}\n\n_Code: ${err.code}_`,
            ),
          },
        ]);
      } else if (err instanceof Error) {
        setMessages((m) => [
          ...m,
          {
            role: "assistant",
            html: renderLiteMarkdown(`**Unexpected error**\n\n${err.message}`),
          },
        ]);
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div
        aria-hidden
        style={{
          position: "fixed",
          inset: 0,
          zIndex: -1,
          background:
            "radial-gradient(900px 500px at 10% -10%, rgba(94, 234, 212, 0.14), transparent 55%), radial-gradient(700px 480px at 95% 10%, rgba(167, 139, 250, 0.16), transparent 50%), linear-gradient(180deg, #070a12, #0d1220)",
        }}
      />
      <header
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "1.1rem 1.5rem",
          borderBottom: "1px solid rgba(255,255,255,0.08)",
          backdropFilter: "blur(12px)",
          background: "rgba(13, 18, 32, 0.72)",
          position: "sticky",
          top: 0,
          zIndex: 2,
        }}
      >
        <div style={{ display: "flex", gap: "0.85rem", alignItems: "center" }}>
          <span
            style={{
              width: 40,
              height: 40,
              borderRadius: 12,
              background: "linear-gradient(135deg, #5eead4, #a78bfa)",
              boxShadow: "0 8px 30px rgba(94, 234, 212, 0.25)",
            }}
          />
          <div>
            <p style={{ margin: 0, fontWeight: 700, letterSpacing: "-0.02em" }}>Atlas Travel</p>
            <p style={{ margin: 0, fontSize: "0.85rem", opacity: 0.62 }}>Concierge · React + FastAPI</p>
          </div>
        </div>
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", flexWrap: "wrap", justifyContent: "flex-end" }}>
          <span className="mono" style={{ fontSize: 12, opacity: 0.6, maxWidth: 480, textAlign: "right" }}>
            {health
              ? `${health.status} · KB chunks ${health.kb}${health.hint ? ` — ${health.hint}` : ""}`
              : healthError
                ? `API: ${healthError}`
                : "Checking API…"}
          </span>
          <span
            className="mono"
            style={{
              fontSize: "0.78rem",
              padding: "0.35rem 0.65rem",
              borderRadius: 999,
              border: "1px solid rgba(255,255,255,0.08)",
              opacity: 0.72,
            }}
          >
            {sessionLabel}
          </span>
        </div>
      </header>

      <main
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(220px, 300px) 1fr",
          minHeight: "calc(100vh - 72px)",
          maxWidth: 1200,
          margin: "0 auto",
        }}
      >
        <aside
          style={{
            padding: "1.25rem 1.5rem",
            borderRight: "1px solid rgba(255,255,255,0.08)",
            background: "rgba(10, 14, 25, 0.35)",
          }}
        >
          <h2 style={{ margin: "0 0 0.75rem", fontSize: "1rem", fontWeight: 600 }}>How we help</h2>
          <ul style={{ margin: 0, paddingLeft: "1.1rem", opacity: 0.62, fontSize: "0.92rem" }}>
            <li style={{ marginBottom: "0.5rem" }}>Answers grounded in internal docs (RAG)</li>
            <li style={{ marginBottom: "0.5rem" }}>Structured replies + booking links</li>
            <li style={{ marginBottom: "0.5rem" }}>Clear API + UI error handling</li>
          </ul>
          <p style={{ marginTop: "1.5rem", paddingTop: "1rem", borderTop: "1px solid rgba(255,255,255,0.08)", fontSize: "0.82rem", opacity: 0.55 }}>
            Backend: <code>backend/</code> · Frontend: <code>frontend/</code>
          </p>
        </aside>

        <section style={{ display: "flex", flexDirection: "column", minHeight: 0 }}>
          <div style={{ flex: 1, overflowY: "auto", padding: "1.25rem 1.5rem 1rem", display: "flex", flexDirection: "column", gap: "0.85rem" }}>
            <ErrorBanner error={bannerError} onDismiss={() => setBannerError(null)} />
            {messages.map((m, i) => (
              <div
                key={i}
                style={{
                  alignSelf: m.role === "user" ? "flex-end" : "flex-start",
                  maxWidth: "min(720px, 100%)",
                  animation: "rise 0.35s ease",
                }}
              >
                <div
                  style={{
                    padding: "0.85rem 1rem",
                    borderRadius: "var(--radius)",
                    border: "1px solid rgba(255,255,255,0.08)",
                    boxShadow: "0 20px 60px rgba(0,0,0,0.55)",
                    background:
                      m.role === "user"
                        ? "linear-gradient(135deg, rgba(94, 234, 212, 0.18), rgba(167, 139, 250, 0.14))"
                        : "var(--bg-2)",
                  }}
                  dangerouslySetInnerHTML={{ __html: m.html }}
                />
                {m.meta ? (
                  <div className="mono" style={{ marginTop: 6, fontSize: 12, opacity: 0.55, display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {m.meta.retrieval_confidence != null ? (
                      <span style={{ padding: "0.15rem 0.45rem", borderRadius: 999, border: "1px solid rgba(255,255,255,0.1)" }}>
                        match {Math.round(m.meta.retrieval_confidence * 100)}%
                      </span>
                    ) : null}
                    {m.meta.escalated ? (
                      <span style={{ padding: "0.15rem 0.45rem", borderRadius: 999, border: "1px solid rgba(251,113,133,0.45)", color: "#fecdd3" }}>
                        human support
                      </span>
                    ) : null}
                    {m.meta.booking_link ? (
                      <a href={m.meta.booking_link} target="_blank" rel="noreferrer" style={{ fontSize: 12 }}>
                        booking
                      </a>
                    ) : null}
                  </div>
                ) : null}
                {m.meta?.related_services?.length ? (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
                    {m.meta.related_services.map((s) => (
                      <div
                        key={s.name}
                        style={{
                          flex: "1 1 140px",
                          padding: "0.6rem 0.7rem",
                          borderRadius: 12,
                          background: "rgba(255,255,255,0.04)",
                          border: "1px solid rgba(255,255,255,0.08)",
                          fontSize: "0.85rem",
                        }}
                      >
                        <strong style={{ display: "block", marginBottom: 4 }}>{s.name}</strong>
                        <span style={{ opacity: 0.65 }}>{s.reason}</span>
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ))}
            {busy ? (
              <div className="mono" style={{ opacity: 0.55, fontSize: 13 }} aria-live="polite">
                Assistant is thinking…
              </div>
            ) : null}
            <div ref={endRef} />
          </div>

          <form
            onSubmit={onSubmit}
            style={{
              display: "flex",
              gap: "0.65rem",
              padding: "1rem 1.5rem 1.25rem",
              borderTop: "1px solid rgba(255,255,255,0.08)",
              background: "rgba(13, 18, 32, 0.92)",
              backdropFilter: "blur(10px)",
            }}
          >
            <label htmlFor="msg" className="sr-only">
              Message
            </label>
            <textarea
              id="msg"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              rows={2}
              required
              disabled={busy}
              placeholder="Ask about bookings, cancellations, destinations, or policies…"
              style={{
                flex: 1,
                resize: "none" as const,
                minHeight: 48,
                padding: "0.75rem 0.85rem",
                borderRadius: 12,
                border: "1px solid rgba(255,255,255,0.08)",
                background: "var(--bg-2)",
                color: "var(--text)",
                font: "inherit",
              }}
            />
            <button
              type="submit"
              disabled={busy}
              style={{
                border: "none",
                borderRadius: 12,
                padding: "0 1.15rem",
                fontWeight: 600,
                cursor: busy ? "wait" : "pointer",
                color: "#042f2e",
                background: "linear-gradient(135deg, var(--accent), #2dd4bf)",
                opacity: busy ? 0.6 : 1,
              }}
            >
              Send
            </button>
          </form>
        </section>
      </main>
      <style>{`
        @keyframes rise { from { opacity: 0; transform: translateY(8px);} to { opacity: 1; transform: none; } }
        .sr-only { position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0; }
        @media (max-width: 840px) {
          main { grid-template-columns: 1fr !important; }
          aside { border-right: none !important; border-bottom: 1px solid rgba(255,255,255,0.08); }
        }
      `}</style>
    </>
  );
}
