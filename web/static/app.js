async function getJSON(url) {
  const r = await fetch(url);
  return r.json();
}

document.querySelectorAll("nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    loadAll();
  });
});

async function loadAll() {
  const overview = await getJSON("/api/overview");
  document.getElementById("stats").innerHTML = [
    ["Prompt", overview.prompts],
    ["Job", overview.jobs],
    ["Job đã xong", overview.jobs_done],
    ["Video kết quả", overview.outputs],
    ["Ảnh nhân vật", overview.characters],
  ].map(([label, value]) => `<div class="card"><b>${value}</b>${label}</div>`).join("");

  const prompts = await getJSON("/api/prompts");
  const select = document.getElementById("prompt-select");
  select.innerHTML = prompts.map((p) => `<option value="${p.name}">${p.title}</option>`).join("");

  const jobs = await getJSON("/api/jobs");
  document.getElementById("jobs").innerHTML = jobs.length
    ? jobs.map((j) => `
      <div class="job">
        <b>${j.product}</b> — ${j.prompt} — ${j.status}
        <div>${j.details || ""}</div>
        <div>${j.notes || ""}</div>
        <pre>${j.prompt_text || ""}</pre>
        <button onclick="copyPrompt(${j.id})">Copy prompt</button>
        <button onclick="markDone(${j.id})">Đã xong</button>
      </div>`).join("")
    : "<p>Chưa có job nào.</p>";
  window._jobs = jobs;

  const characters = await getJSON("/api/character");
  document.getElementById("characters").innerHTML = characters.length
    ? characters.map((c) => `<div>${c.name} — ${c.size} bytes</div>`).join("")
    : "<p>Chưa có ảnh nhân vật trong character-reference/.</p>";

  const outputs = await getJSON("/api/outputs");
  document.getElementById("outputs").innerHTML = outputs.length
    ? outputs.map((o) => `
      <div class="job">
        <b>${o.name}</b>
        <video controls src="/output/${encodeURIComponent(o.name)}"></video>
        <a href="/output/${encodeURIComponent(o.name)}" download>Tải video</a>
      </div>`).join("")
    : "<p>Chưa có video nào trong output/.</p>";
}

window.copyPrompt = async (id) => {
  const job = (window._jobs || []).find((j) => String(j.id) === String(id));
  if (!job) return;
  await navigator.clipboard.writeText(
    `Sản phẩm: ${job.product}\nChi tiết: ${job.details}\nGhi chú: ${job.notes}\n\n${job.prompt_text || ""}`
  );
  alert("Đã copy prompt của job.");
};

window.markDone = async (id) => {
  await fetch(`/api/jobs/${id}/done`, { method: "POST" });
  loadAll();
};

document.getElementById("job-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const data = Object.fromEntries(new FormData(e.target).entries());
  const r = await fetch("/api/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!r.ok) {
    alert("Tạo job chưa được, kiểm tra lại tên sản phẩm và prompt.");
    return;
  }
  e.target.reset();
  loadAll();
});

loadAll();
