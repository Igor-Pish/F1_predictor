export default function PredictionSidebar({ prediction, loading }) {
  return (
    <div className="card">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <div style={{ fontWeight: 800, fontSize: 16 }}>Последнее предсказание</div>
        <span className="badge">Top-3</span>
      </div>

      <div style={{ height: 10 }} />

      {loading ? (
        <div className="muted">Загрузка…</div>
      ) : !prediction ? (
        <div className="muted">
          Пока нет данных о предсказаниях.
          <div className="subtle" style={{ marginTop: 6 }}>
            (В бэке ещё нет /api/predictions/latest — добавим, когда появится ML.)
          </div>
        </div>
      ) : (
        <>
          <div className="kpi">
            {prediction.top3?.map((p, i) => (
              <div className="kpiRow" key={`${p.driver}-${i}`}>
                <div className="kpiLeft">
                  <div className="kpiTitle">
                    {i + 1}) {p.driver}
                  </div>
                  <div className="kpiSmall">
                    {prediction.year} R{String(prediction.round).padStart(2, "0")}
                  </div>
                </div>
                <div className="kpiProb">{(Number(p.prob) * 100).toFixed(1)}%</div>
              </div>
            ))}
          </div>

          <div style={{ height: 12 }} />

          <div className="subtle">
            <div>Модель: {prediction.model_version ?? "-"}</div>
            <div>Train: {prediction.train_range ?? "-"}</div>
            <div>Создано: {prediction.created_at ?? "-"}</div>
          </div>
        </>
      )}
    </div>
  );
}