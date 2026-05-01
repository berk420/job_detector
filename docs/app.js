let allPosts = [];

async function fetchJobs() {
  const resp = await fetch(`jobs.json?t=${Date.now()}`);
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
  return resp.json();
}

function timeAgo(ts) {
  if (!ts) return "Bilinmiyor";
  const diff = Math.floor((Date.now() / 1000) - ts);
  if (diff < 60) return `${diff} saniye önce`;
  if (diff < 3600) return `${Math.floor(diff / 60)} dakika önce`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} saat önce`;
  return `${Math.floor(diff / 86400)} gün önce`;
}

function scoreBar(score) {
  const pct = Math.min(Math.round(score), 100);
  const color = pct >= 70 ? "bg-emerald-500" : pct >= 40 ? "bg-amber-500" : "bg-gray-300";
  return `
    <div class="flex items-center gap-2 mt-2">
      <div class="flex-1 bg-gray-100 dark:bg-gray-700 rounded-full h-1.5">
        <div class="${color} h-1.5 rounded-full transition-all" style="width:${pct}%"></div>
      </div>
      <span class="text-xs font-medium text-gray-500 dark:text-gray-400">${pct}</span>
    </div>`;
}

function topCard(post) {
  const isNew = post.is_new
    ? `<span class="text-xs bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full font-medium">Yeni</span>`
    : "";

  return `
    <a href="${post.url}" target="_blank" rel="noopener"
      class="group block bg-white dark:bg-gray-800 rounded-xl p-5 shadow-sm border-2 border-linkedin/20 hover:border-linkedin dark:border-blue-500/20 dark:hover:border-blue-500 transition-all duration-200 hover:shadow-md">
      <div class="flex items-start justify-between gap-2 mb-3">
        <div class="flex-1 min-w-0">
          <p class="font-semibold text-gray-900 dark:text-white text-sm truncate group-hover:text-linkedin dark:group-hover:text-blue-400 transition-colors">
            ${escHtml(post.author_name) || "Bilinmeyen"}
          </p>
          <p class="text-xs text-gray-500 dark:text-gray-400 truncate">${escHtml(post.author_title) || ""}</p>
        </div>
        ${isNew}
      </div>
      <p class="text-sm text-gray-700 dark:text-gray-300 line-clamp-4 leading-relaxed">${escHtml(post.text)}</p>
      ${scoreBar(post.score)}
      <div class="flex items-center gap-4 mt-3 text-xs text-gray-400 dark:text-gray-500">
        <span>🕐 ${timeAgo(post.timestamp)}</span>
        <span>👍 ${post.likes}</span>
        <span>💬 ${post.comments}</span>
      </div>
    </a>`;
}

function listRow(post) {
  const isNew = post.is_new
    ? `<span class="shrink-0 text-xs bg-emerald-100 dark:bg-emerald-900 text-emerald-700 dark:text-emerald-300 px-2 py-0.5 rounded-full">Yeni</span>`
    : "";

  return `
    <a href="${post.url}" target="_blank" rel="noopener"
      class="group flex gap-4 bg-white dark:bg-gray-800 rounded-xl p-4 shadow-sm border border-gray-100 dark:border-gray-700 hover:border-linkedin dark:hover:border-blue-500 transition-all duration-200 hover:shadow-md">
      <div class="shrink-0 w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-lg font-bold text-linkedin dark:text-blue-400">
        ${(post.author_name || "?")[0].toUpperCase()}
      </div>
      <div class="flex-1 min-w-0">
        <div class="flex items-center gap-2 mb-1">
          <p class="font-semibold text-sm text-gray-900 dark:text-white group-hover:text-linkedin dark:group-hover:text-blue-400 transition-colors truncate">
            ${escHtml(post.author_name) || "Bilinmeyen"}
          </p>
          ${isNew}
        </div>
        <p class="text-xs text-gray-500 dark:text-gray-400 mb-2 truncate">${escHtml(post.author_title) || ""}</p>
        <p class="text-sm text-gray-700 dark:text-gray-300 line-clamp-2">${escHtml(post.text)}</p>
        <div class="flex items-center gap-4 mt-2 text-xs text-gray-400 dark:text-gray-500">
          <span>🕐 ${timeAgo(post.timestamp)}</span>
          <span>👍 ${post.likes}</span>
          <span>💬 ${post.comments}</span>
        </div>
      </div>
      <div class="shrink-0 self-center text-right">
        <div class="text-xs font-bold text-gray-500 dark:text-gray-400 mb-1">Skor</div>
        <div class="text-lg font-bold ${post.score >= 70 ? 'text-emerald-600 dark:text-emerald-400' : post.score >= 40 ? 'text-amber-600 dark:text-amber-400' : 'text-gray-400'}">${Math.round(post.score)}</div>
      </div>
    </a>`;
}

function escHtml(str) {
  return (str || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function applySortFilter() {
  const sort = document.getElementById("sort-select").value;
  let sorted = [...allPosts];
  if (sort === "time") sorted.sort((a, b) => b.timestamp - a.timestamp);
  else if (sort === "likes") sorted.sort((a, b) => b.likes - a.likes);
  else sorted.sort((a, b) => b.score - a.score);

  const container = document.getElementById("all-results");
  if (sorted.length === 0) {
    container.innerHTML = `<div class="text-center text-gray-400 dark:text-gray-500 py-12">Henüz ilan bulunamadı</div>`;
    return;
  }
  container.innerHTML = sorted.map(listRow).join("");
}

async function refresh() {
  const btn = document.getElementById("refresh-btn");
  btn.disabled = true;
  btn.textContent = "Yükleniyor…";

  try {
    const data = await fetchJobs();
    allPosts = data.all_results || [];

    // Stats
    document.getElementById("stat-total").textContent = data.stats?.total ?? 0;
    document.getElementById("stat-today").textContent = data.stats?.new_today ?? 0;
    document.getElementById("stat-run").textContent = data.stats?.new_this_run ?? 0;

    // Query
    document.getElementById("search-query").textContent = data.query || "—";

    // Last updated
    if (data.last_updated) {
      const d = new Date(data.last_updated);
      document.getElementById("last-updated").textContent =
        `Son güncelleme: ${d.toLocaleString("tr-TR")}`;
    } else {
      document.getElementById("last-updated").textContent = "Henüz çalışmadı";
    }

    // Top results
    const topEl = document.getElementById("top-results");
    const top = data.top_results || [];
    if (top.length === 0) {
      topEl.innerHTML = `<div class="col-span-full text-center text-gray-400 dark:text-gray-500 py-12">Henüz ilan bulunamadı</div>`;
    } else {
      topEl.innerHTML = top.map(topCard).join("");
    }

    // All results
    applySortFilter();

  } catch (err) {
    console.error(err);
    document.getElementById("top-results").innerHTML =
      `<div class="col-span-full text-center text-red-400 py-10">Veriler yüklenemedi: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = "Yenile";
  }
}

function toggleDark() {
  document.documentElement.classList.toggle("dark");
  localStorage.setItem("dark", document.documentElement.classList.contains("dark") ? "1" : "0");
}

// Init
if (localStorage.getItem("dark") === "1") {
  document.documentElement.classList.add("dark");
}
refresh();
