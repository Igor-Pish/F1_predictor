async function httpJson(path) {
  const res = await fetch(path);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const err = new Error(`HTTP ${res.status} for ${path}${text ? `: ${text}` : ""}`);
    err.status = res.status;
    throw err;
  }
  return res.json();
}

export async function getYears() {
  return httpJson("/api/years");
}

export async function getRounds(year) {
  return httpJson(`/api/rounds?year=${encodeURIComponent(year)}`);
}

export async function getSession(year, round, session) {
  return httpJson(
    `/api/session?year=${encodeURIComponent(year)}&round=${encodeURIComponent(round)}&session=${encodeURIComponent(session)}`
  );
}

/**
 * Эндпоинта пока нет в твоём бэке.
 * UI будет пытаться вызвать, и если 404 — покажет “нет данных”.
 */
export async function getLatestPrediction() {
  try {
    return await httpJson("/api/predictions/latest");
  } catch (e) {
    if (e?.status === 404) return null;
    // если бэк вообще не поднят или ошибка сети — тоже вернём null, но HomePage покажет ошибку отдельно
    return null;
  }
}