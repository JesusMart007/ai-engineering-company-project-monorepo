/** Error state of a data view: the readable message and a way to try again. */
export function LoadError({ message, onRetry, busy }: { message: string; onRetry: () => void; busy?: boolean }) {
  return (
    <div className="state" role="alert">
      <p className="error">{message}</p>
      <button type="button" onClick={onRetry} disabled={busy}>Reintentar</button>
    </div>
  );
}
