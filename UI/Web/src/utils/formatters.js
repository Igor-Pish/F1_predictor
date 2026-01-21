export function formatSecondsToTime(sec) {
  if (sec === null || sec === undefined) return "-";
  const s = Number(sec);
  if (!Number.isFinite(s)) return String(sec);

  const minutes = Math.floor(s / 60);
  const seconds = s - minutes * 60;

  // 1:23.456
  const secondsStr = seconds.toFixed(3).padStart(6, "0");
  return `${minutes}:${secondsStr}`;
}

export function safe(v) {
  if (v === null || v === undefined || v === "") return "-";
  return String(v);
}