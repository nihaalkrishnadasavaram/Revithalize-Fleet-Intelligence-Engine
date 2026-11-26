export function LoadingState({ message = "Loading data…" }) {
  return (
    <div className="state-box" role="status">
      <div className="spinner" />
      <p>{message}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="state-box state-error" role="alert">
      <p className="state-title">Something went wrong</p>
      <p>{message}</p>
      {onRetry && (
        <button type="button" className="button button-primary" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, message, children }) {
  return (
    <div className="state-box">
      <p className="state-title">{title}</p>
      {message && <p>{message}</p>}
      {children}
    </div>
  );
}
