interface Props {
  message: string;
}

export default function ErrorBanner({ message }: Props) {
  return (
    <div
      role="alert"
      className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
    >
      <span className="font-semibold">Backtest failed: </span>
      {message}
    </div>
  );
}
