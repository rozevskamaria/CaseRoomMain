export interface FlagStyleEntry {
  bg: string;
  text: string;
  badge: string | null;
  badgeBg: string | null;
  badgeText: string | null;
}

export type FlagKey =
  | "crit"
  | "hi2"
  | "hi"
  | "absent"
  | "diag"
  | "lo3"
  | "lo2"
  | "lo"
  | "ok"
  | "neutral";

export const FLAG_STYLE: Record<FlagKey, FlagStyleEntry> = {
  crit: { bg: "#FFF0F0", text: "#8B0000", badge: "CRITICAL", badgeBg: "#C03030", badgeText: "#fff" },
  hi2: { bg: "#FFF4EC", text: "#8B3A00", badge: "↑↑", badgeBg: "#C05020", badgeText: "#fff" },
  hi: { bg: "#FFFBF0", text: "#7B4A00", badge: "↑", badgeBg: "#B07020", badgeText: "#fff" },
  absent: { bg: "#F5F0FF", text: "#4A1A7A", badge: "ABSENT", badgeBg: "#7040B0", badgeText: "#fff" },
  diag: { bg: "#F0FFF4", text: "#1A5E30", badge: "DIAGNOSTIC", badgeBg: "#1D7A40", badgeText: "#fff" },
  lo3: { bg: "#EEF4FF", text: "#1A3A8B", badge: "↓↓↓", badgeBg: "#2050B0", badgeText: "#fff" },
  lo2: { bg: "#F0F5FF", text: "#1A408B", badge: "↓↓", badgeBg: "#2060B0", badgeText: "#fff" },
  lo: { bg: "#F2F6FF", text: "#204890", badge: "↓", badgeBg: "#3070C0", badgeText: "#fff" },
  ok: { bg: "#F5FFF8", text: "#1A5030", badge: null, badgeBg: null, badgeText: null },
  neutral: { bg: "transparent", text: "#1A1714", badge: null, badgeBg: null, badgeText: null },
};
