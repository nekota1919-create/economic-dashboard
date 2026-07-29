const COUNTRY_LABEL = { US: "米", JP: "日", EU: "欧", UK: "英" };

function fmtJst(iso) {
  const d = new Date(iso);
  return d.toLocaleString("ja-JP", {
    timeZone: "Asia/Tokyo",
    month: "numeric",
    day: "numeric",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function dayKey(iso) {
  const d = new Date(iso);
  return d.toLocaleDateString("ja-JP", { timeZone: "Asia/Tokyo", month: "long", day: "numeric", weekday: "short" });
}

function badge(text, cls) {
  return `<span class="badge ${cls}">${text}</span>`;
}

async function fetchJson(path) {
  const res = await fetch(path, { cache: "no-store" });
  if (!res.ok) throw new Error(`fetch failed: ${path}`);
  return res.json();
}

function renderUpdatedAt(iso, el) {
  if (!iso) return;
  const d = new Date(iso);
  el.textContent = `最終更新: ${d.toLocaleString("ja-JP", { timeZone: "Asia/Tokyo" })} (JST)`;
}

function renderUpcoming(events, container) {
  if (!events.length) {
    container.innerHTML = '<div class="empty-state">今週の対象イベントはありません</div>';
    return;
  }
  let currentDay = null;
  let html = "";
  for (const ev of events) {
    const dk = dayKey(ev.datetime_utc);
    if (dk !== currentDay) {
      if (currentDay !== null) html += "</div>";
      html += `<div class="day-group"><h2>${dk}</h2>`;
      currentDay = dk;
    }
    const scenarioItems = (ev.scenario?.text_lines || []).map((l) => `<li>${l}</li>`).join("");
    html += `
      <div class="card">
        <div class="card-top">
          <span class="card-title">${ev.label}</span>
          <span>${badge(COUNTRY_LABEL[ev.country] || ev.country, "country-" + ev.country)} ${badge(ev.impact || "-", "impact-" + ev.impact)}</span>
        </div>
        <div class="meta-row">${fmtJst(ev.datetime_utc)} JST ・ ${ev.ff_title}</div>
        <div class="fc-prev">
          <div><span class="label">予想</span>${ev.forecast || "-"}</div>
          <div><span class="label">前回</span>${ev.previous || "-"}</div>
          <div><span class="label">傾向</span>${ev.scenario?.trend_label || "-"}</div>
        </div>
        <details class="scenario">
          <summary>参考シナリオを見る</summary>
          <ul>${scenarioItems}</ul>
        </details>
      </div>`;
  }
  html += "</div>";
  container.innerHTML = html;
}

function marketTable(reaction) {
  if (!reaction || Object.keys(reaction).length === 0) return "";
  const names = { usdjpy: "ドル円", nikkei225: "日経平均", sp500: "S&P500", us10y: "米10年金利" };
  let rows = "";
  for (const [key, r] of Object.entries(reaction)) {
    const cls = r.change_pct > 0 ? "change-pos" : r.change_pct < 0 ? "change-neg" : "";
    const sign = r.change_pct > 0 ? "+" : "";
    rows += `<tr><td>${names[key] || key}</td><td>${r.prev_close}</td><td>${r.post_close}</td><td class="${cls}">${sign}${r.change_pct}%</td></tr>`;
  }
  return `<table class="market-table">
    <thead><tr><th>指標</th><th>発表前終値</th><th>当日/翌営業日終値</th><th>変化率</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>`;
}

function renderResults(events, container) {
  if (!events.length) {
    container.innerHTML = '<div class="empty-state">まだ発表実績がありません。指標発表後に自動で反映されます。</div>';
    return;
  }
  let html = "";
  for (const ev of events) {
    let surpriseTag = "";
    if (ev.beat_forecast === true) surpriseTag = '<span class="surprise-tag beat">予想上振れ</span>';
    else if (ev.beat_forecast === false) surpriseTag = '<span class="surprise-tag miss">予想下振れ</span>';

    let pendingNote = "";
    if (ev.data_note) {
      pendingNote = `<div class="pending-note">${ev.data_note}</div>`;
    }

    let revisedNote = "";
    if (ev.was_revised) {
      revisedNote = `<div class="revised-note">初値から改定されています(初値: ${ev.actual_first_release} → 現在: ${ev.actual_latest})</div>`;
    }

    html += `
      <div class="card">
        <div class="card-top">
          <span class="card-title">${ev.label}${surpriseTag}</span>
          <span>${badge(COUNTRY_LABEL[ev.country] || ev.country, "country-" + ev.country)}</span>
        </div>
        <div class="meta-row">${fmtJst(ev.datetime_utc)} JST ・ ${ev.ff_title}</div>
        <div class="result-values">
          <div class="val-box"><span class="label">予想</span><span class="value">${ev.forecast || "-"}</span></div>
          <div class="val-box"><span class="label">実績(発表時)</span><span class="value">${ev.actual_first_release || "-"}</span></div>
          <div class="val-box"><span class="label">現在の改定値</span><span class="value">${ev.actual_latest || "-"}</span></div>
        </div>
        ${revisedNote}
        ${pendingNote}
        ${marketTable(ev.market_reaction)}
      </div>`;
  }
  container.innerHTML = html;
}
