import { formatSecondsToTime, safe } from "../utils/formatters.js";

function pickColumns(session) {
  // Race
  if (session === "R") {
    return [
      { key: "position", label: "Pos" },
      { key: "driver", label: "Driver" },
      { key: "team", label: "Team" },
      { key: "best_lap", label: "Best lap" },
      { key: "laps", label: "Laps" },
      { key: "main_compound", label: "Compound" },
      { key: "status", label: "Status" }
    ];
  }
  // Quali
  return [
    { key: "position", label: "Pos" },
    { key: "driver", label: "Driver" },
    { key: "team", label: "Team" },
    { key: "q1", label: "Q1" },
    { key: "q2", label: "Q2" },
    { key: "q3", label: "Q3" },
    { key: "best_lap", label: "Best lap" },
    { key: "status", label: "Status" }
  ];
}

function renderCell(colKey, value) {
  if (colKey === "best_lap" || colKey === "q1" || colKey === "q2" || colKey === "q3") {
    // в твоей БД это, судя по загрузчику, секунды (float) или null
    return formatSecondsToTime(value);
  }
  return safe(value);
}

export default function ResultsTable({ session, rows, loading }) {
  const cols = pickColumns(session);

  if (loading) {
    return <div className="muted">Загрузка результатов…</div>;
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="muted">
        Нет данных в БД для этой сессии. (Сейчас UI просто читает /api/session; автозагрузку из FastF1 можно добавить позже.)
      </div>
    );
  }

  return (
    <div className="tableWrap">
      <table>
        <thead>
          <tr>
            {cols.map((c) => (
              <th key={c.key}>{c.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, idx) => (
            <tr key={`${r.driver ?? "row"}-${idx}`}>
              {cols.map((c) => (
                <td key={c.key}>{renderCell(c.key, r[c.key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}