async function getJSON(url) {
  const r = await fetch(url);
  return r.json();
}

function readFileAsDataURL(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function uploadFiles(kind, files) {
  for (const file of files) {
    const data = await readFileAsDataURL(file);
    const r = await fetch("/api/uploads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind, name: file.name, data }),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      alert(`Tải "${file.name}" chưa được: ${err.error || "lỗi không rõ"}`);
    }
  }
  loadAll();
}

function wireUpload(inputId, kind) {
  const input = document.getElementById(inputId);
  const zone = input.closest(".dropzone");
  input.addEventListener("change", async () => {
    if (input.files.length) await uploadFiles(kind, input.files);
    input.value = "";
  });
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", async (e) => {
    e.preventDefault();
    zone.classList.remove("dragover");
    if (e.dataTransfer.files.length) await uploadFiles(kind, e.dataTransfer.files);
  });
}

wireUpload("product-upload", "product");
wireUpload("character-upload", "character");

document.querySelectorAll("nav button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("nav button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    loadAll();
  });
});

function galleryHTML(items, prefix, selected, onSelect) {
  if (!items.length) return "<p class=\"hint\">Chưa có ảnh nào. Tải ảnh lên bằng khung phía trên.</p>";
  return items.map((it) => `
    <div class="thumb ${selected === it.name ? "selected" : ""}">
      <img src="/${prefix}/${encodeURIComponent(it.name)}" alt="${it.name}" onclick="${onSelect}('${it.name.replace(/'/g, "\\'")}')">
      <span>${it.name}</span>
      <button class="del" title="Xoá ảnh" onclick="deleteImage('${prefix === "input" ? "products" : "characters"}', '${it.name.replace(/'/g, "\\'")}')">×</button>
    </div>`).join("");
}

window.selectProduct = (name) => {
  document.getElementById("product-select").value = name;
  document.getElementById("product-selected").textContent = `Đã chọn ảnh sản phẩm: ${name}`;
  loadAll(true);
};

window.deleteImage = async (kind, name) => {
  if (!confirm(`Xoá ảnh "${name}"?`)) return;
  await fetch(`/api/${kind}/${encodeURIComponent(name)}`, { method: "DELETE" });
  loadAll();
};

async function loadAll(keepSelection) {
  const overview = await getJSON("/api/overview");
  document.getElementById("stats").innerHTML = [
    ["Prompt", overview.prompts],
    ["Ảnh sản phẩm", overview.products || 0],
    ["Ảnh nhân vật", overview.characters],
    ["Job", overview.jobs],
    ["Job đã xong", overview.jobs_done],
    ["Video kết quả", overview.outputs],
  ].map(([label, value]) => `<div class="card"><b>${value}</b>${label}</div>`).join("");

  const prompts = await getJSON("/api/prompts");
  document.getElementById("prompt-select").innerHTML =
    prompts.map((p) => `<option value="${p.name}">${p.title}</option>`).join("");

  const products = await getJSON("/api/products");
  const productSelect = document.getElementById("product-select");
  const prevProduct = keepSelection ? productSelect.value : "";
  productSelect.innerHTML = `<option value="">— Chưa chọn —</option>` +
    products.map((p) => `<option value="${p.name}">${p.name}</option>`).join("");
  if (prevProduct) productSelect.value = prevProduct;
  document.getElementById("product-gallery").innerHTML =
    galleryHTML(products, "input", productSelect.value, "selectProduct");

  const characters = await getJSON("/api/character");
  document.getElementById("character-select").innerHTML =
    `<option value="">— Không dùng nhân vật / chọn sau —</option>` +
    characters.map((c) => `<option value="${c.name}">${c.name}</option>`).join("");
  document.getElementById("characters").innerHTML =
    galleryHTML(characters, "character", "", "selectCharacter");

  const jobs = await getJSON("/api/jobs");
  document.getElementById("jobs").innerHTML = jobs.length
    ? jobs.map((j) => `
      <div class="job">
        <b>${j.product}</b> — ${j.prompt} — ${j.status}
        <div>${j.product_image ? `Ảnh sản phẩm: ${j.product_image}` : ""} ${j.character_image ? `· Nhân vật: ${j.character_image}` : ""}</div>
        <div>${j.details || ""}</div>
        <div>${j.notes || ""}</div>
        <pre>${j.prompt_text || ""}</pre>
        <button onclick="copyPrompt(${j.id})">Copy prompt</button>
        <button onclick="markDone(${j.id})">Đã xong</button>
      </div>`).join("")
    : "<p>Chưa có job nào.</p>";
  window._jobs = jobs;

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

window.selectCharacter = (name) => {
  document.getElementById("character-select").value = name;
  document.querySelector('[data-tab="create"]').click();
};

window.copyPrompt = async (id) => {
  const job = (window._jobs || []).find((j) => String(j.id) === String(id));
  if (!job) return;
  await navigator.clipboard.writeText(
    `Sản phẩm: ${job.product}\nChi tiết: ${job.details}\nẢnh sản phẩm: ${job.product_image || ""}\nẢnh nhân vật: ${job.character_image || ""}\nGhi chú: ${job.notes}\n\n${job.prompt_text || ""}`
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
