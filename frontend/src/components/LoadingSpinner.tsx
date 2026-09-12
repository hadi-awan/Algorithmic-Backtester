export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-neutral-500 dark:text-neutral-400">
      <span
        className="h-5 w-5 animate-spin rounded-full border-2 border-neutral-300 border-t-blue-600 dark:border-neutral-700 dark:border-t-blue-500"
        aria-hidden="true"
      />
      <span className="text-sm">Running backtest...</span>
    </div>
  );
}
