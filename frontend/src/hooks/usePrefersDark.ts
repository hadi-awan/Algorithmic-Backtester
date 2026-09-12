import { useEffect, useState } from "react";

/** Tracks the OS/browser `prefers-color-scheme` setting so chart
 * components can select the validated dark-mode palette rather than
 * just flipping the light one. */
export function usePrefersDark(): boolean {
  const [prefersDark, setPrefersDark] = useState<boolean>(
    () => window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false,
  );

  useEffect(() => {
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = (e: MediaQueryListEvent) => setPrefersDark(e.matches);
    mq.addEventListener("change", handler);
    return () => mq.removeEventListener("change", handler);
  }, []);

  return prefersDark;
}
