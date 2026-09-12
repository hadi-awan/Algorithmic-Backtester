// Validated categorical/sequential palette (see the project's dataviz
// skill reference) -- these hex values are the reference instance and
// should not be re-ordered or swapped ad hoc; see references/palette.md
// if this project ever needs to target a different brand palette.
export const palette = {
  light: {
    surface: "#fcfcfb",
    textPrimary: "#0b0b0b",
    textSecondary: "#52514e",
    muted: "#898781",
    gridline: "#e1e0d9",
    baseline: "#c3c2b7",
    series: {
      ruleBased: "#2a78d6", // categorical slot 1 (blue)
      ml: "#eb6834", // categorical slot 2 (orange)
      buyAndHold: "#1baf7a", // categorical slot 3 (aqua)
    },
    sequential: "#2a78d6",
  },
  dark: {
    surface: "#1a1a19",
    textPrimary: "#ffffff",
    textSecondary: "#c3c2b7",
    muted: "#898781",
    gridline: "#2c2c2a",
    baseline: "#383835",
    series: {
      ruleBased: "#3987e5",
      ml: "#d95926",
      buyAndHold: "#199e70",
    },
    sequential: "#3987e5",
  },
} as const;

export type PaletteMode = keyof typeof palette;
