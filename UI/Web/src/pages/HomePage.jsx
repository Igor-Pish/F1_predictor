import { useEffect, useMemo, useState } from "react";
import { getLatestPrediction, getRounds, getSession, getYears } from "../api/f1Api.js";
import RaceSelector from "../components/RaceSelector.jsx";
import ResultsTable from "../components/ResultsTable.jsx";
import PredictionSidebar from "../components/PredictionSidebar.jsx";

function pickDefaultYear(years) {
  if (!years || years.length === 0) return null;
  return Math.max(...years);
}

function pickDefaultRound(rounds) {
  if (!rounds || rounds.length === 0) return null;
  // rounds приходит как [{round, name}, ...]
  return Math.max(...rounds.map((r) => Number(r.round)));
}

export default function HomePage() {
  const [years, setYears] = useState([]);
  const [rounds, setRounds] = useState([]);
  const [year, setYear] = useState(null);
  const [round, setRound] = useState(null);
  const [session, setSession] = useState("R"); // R or Q

  const [rows, setRows] = useState([]);
  const [loadingResults, setLoadingResults] = useState(false);
  const [loadingPage, setLoadingPage] = useState(true);
  const [error, setError] = useState("");

  const [prediction, setPrediction] = useState(null);
  const [loadingPrediction, setLoadingPrediction] = useState(false);

  const selectedRoundName = useMemo(() => {
    const r = rounds.find((x) => Number(x.round) === Number(round));
    return r?.name ?? "";
  }, [rounds, round]);

  async function loadRoundsAndMaybePickDefault(y) {
    const rs = await getRounds(y);
    setRounds(rs);

    const defaultRound = pickDefaultRound(rs);
    setRound(defaultRound);
    return { rounds: rs, round: defaultRound };
  }

  async function loadResults(y, r, s) {
    setLoadingResults(true);
    setError("");
    try {
      const data = await getSession(y, r, s);
      setRows(data);
    } catch (e) {
      setRows([]);
      setError(e?.message || "Ошибка загрузки результатов");
    } finally {
      setLoadingResults(false);
    }
  }

  async function bootstrap() {
    setLoadingPage(true);
    setError("");

    try {
      const ys = await getYears();
      setYears(ys);

      const defaultYear = pickDefaultYear(ys);
      setYear(defaultYear);

      const { round: defaultRound } = await loadRoundsAndMaybePickDefault(defaultYear);

      // результаты по умолчанию: последняя гонка, Race
      await loadResults(defaultYear, defaultRound, "R");

      // предсказание (опционально)
      setLoadingPrediction(true);
      const pred = await getLatestPrediction();
      setPrediction(pred);
      setLoadingPrediction(false);
    } catch (e) {
      setError(e?.message || "Ошибка инициализации");
    } finally {
      setLoadingPage(false);
    }
  }

  useEffect(() => {
    bootstrap();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function onYearChange(nextYear) {
    setYear(nextYear);
    setError("");
    try {
      const { round: defaultRound } = await loadRoundsAndMaybePickDefault(nextYear);
      await loadResults(nextYear, defaultRound, session);
    } catch (e) {
      setError(e?.message || "Ошибка при смене года");
    }
  }

  async function onRoundChange(nextRound) {
    setRound(nextRound);
    await loadResults(year, nextRound, session);
  }

  async function onSessionChange(nextSession) {
    setSession(nextSession);
    await loadResults(year, round, nextSession);
  }

  async function onRefresh() {
    await loadResults(year, round, session);
  }

  const disableControls = loadingPage || loadingResults || year === null || round === null;

  return (
    <div className="container">
      <div className="header">
        <h1 className="h1">F1 Predictor</h1>
        <div className="subtle">
          {year && round ? (
            <>
              {year} • R{String(round).padStart(2, "0")} {selectedRoundName ? `• ${selectedRoundName}` : ""}
            </>
          ) : (
            "—"
          )}
        </div>
      </div>

      <div className="grid">
        <div className="card">
          <RaceSelector
            years={years}
            rounds={rounds}
            year={year ?? ""}
            round={round ?? ""}
            session={session}
            onYearChange={onYearChange}
            onRoundChange={onRoundChange}
            onSessionChange={onSessionChange}
            onRefresh={onRefresh}
            disabled={disableControls}
          />

          {error ? <div className="error">{error}</div> : null}

          <ResultsTable session={session} rows={rows} loading={loadingResults || loadingPage} />
        </div>

        <PredictionSidebar prediction={prediction} loading={loadingPrediction} />
      </div>
    </div>
  );
}