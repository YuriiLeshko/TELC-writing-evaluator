export default function LoadingState({ message = "Laden…" }) {
  return (
    <div className="loading" role="status">
      <div className="loading__spinner" aria-hidden />
      <span>{message}</span>
    </div>
  );
}
