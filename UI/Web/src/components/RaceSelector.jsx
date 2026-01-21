export default function RaceSelector({
  years,
  rounds,
  year,
  round,
  session,
  onYearChange,
  onRoundChange,
  onSessionChange,
  onRefresh,
  disabled
}) {
  return (
    <div className="controls">
      <div className="control">
        <label>Год</label>
        <select value={year ?? ""} onChange={(e) => onYearChange(Number(e.target.value))} disabled={disabled}>
          {(years ?? []).map((y) => (
            <option key={y} value={y}>
              {y}
            </option>
          ))}
        </select>
      </div>

      <div className="control" style={{ minWidth: 220 }}>
        <label>Гонка</label>
        <select value={round ?? ""} onChange={(e) => onRoundChange(Number(e.target.value))} disabled={disabled}>
          {(rounds ?? []).map((r) => (
            <option key={r.round} value={r.round}>
              R{String(r.round).padStart(2, "0")} — {r.name}
            </option>
          ))}
        </select>
      </div>

      <div className="control" style={{ minWidth: 220 }}>
        <label>Сессия</label>
        <div className="toggleRow">
          <div className="toggle">
            <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
              <input
                type="radio"
                name="session"
                checked={session === "R"}
                onChange={() => onSessionChange("R")}
                disabled={disabled}
              />
              Race
            </label>
            <label style={{ display: "inline-flex", gap: 6, alignItems: "center" }}>
              <input
                type="radio"
                name="session"
                checked={session === "Q"}
                onChange={() => onSessionChange("Q")}
                disabled={disabled}
              />
              Quali
            </label>
          </div>
        </div>
      </div>

      <div className="control" style={{ minWidth: 140 }}>
        <label>&nbsp;</label>
        <button onClick={onRefresh} disabled={disabled}>
          Обновить
        </button>
      </div>
    </div>
  );
}