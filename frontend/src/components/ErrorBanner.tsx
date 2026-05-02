import type { ApiError } from "../api/client";

type Props = {
  error: ApiError | null;
  onDismiss: () => void;
};

export function ErrorBanner({ error, onDismiss }: Props) {
  if (!error) return null;
  return (
    <div
      role="alert"
      style={{
        marginBottom: "0.75rem",
        padding: "0.75rem 1rem",
        borderRadius: 12,
        border: "1px solid rgba(251, 113, 133, 0.45)",
        background: "rgba(251, 113, 133, 0.12)",
        display: "flex",
        gap: "0.75rem",
        alignItems: "flex-start",
        justifyContent: "space-between",
      }}
    >
      <div>
        <strong style={{ display: "block", marginBottom: 4 }}>{error.code}</strong>
        <span style={{ opacity: 0.92 }}>{error.message}</span>
        {error.status ? (
          <div className="mono" style={{ marginTop: 6, fontSize: 12, opacity: 0.65 }}>
            HTTP {error.status}
          </div>
        ) : null}
      </div>
      <button
        type="button"
        onClick={onDismiss}
        style={{
          border: "1px solid rgba(255,255,255,0.15)",
          background: "transparent",
          color: "inherit",
          borderRadius: 8,
          padding: "0.25rem 0.5rem",
          cursor: "pointer",
        }}
      >
        Dismiss
      </button>
    </div>
  );
}
