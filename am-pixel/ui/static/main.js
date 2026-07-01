/* AM Pixel UI — plain JS, no framework (SPEC §13.2). */
"use strict";

const $ = (sel) => document.querySelector(sel);
let lastResult = null;

/* ---------------- tabs ---------------- */
document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", async () => {
    document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    const panel = $(`#panel-${btn.dataset.tab}`);
    panel.classList.add("active");
    if (panel.dataset.src && !panel.dataset.loaded) {
      panel.innerHTML = await (await fetch(panel.dataset.src)).text();
      panel.dataset.loaded = "1";
      if (btn.dataset.tab === "freeform") wireFreeform();
    }
    if (btn.dataset.tab === "continuity") {
      const r = await (await fetch("/api/continuity")).json();
      $("#continuity-md").textContent = r.markdown || "(continuity manifest is empty)";
    }
  });
});

/* ---------------- status bar ---------------- */
async function refreshStatus() {
  try {
    const s = await (await fetch("/api/status")).json();
    const bar = $("#statusbar");
    bar.classList.toggle("halted", s.halted);
    bar.textContent = s.halted
      ? "EMERGENCY HALT ACTIVE — generation gated"
      : `${s.phase} · ${s.backend} (${s.device_name}) · ` +
        `${s.vram_gb ? s.vram_gb + "GB VRAM · " : ""}disk ${s.disk_free_gb}GB free · ` +
        (s.checkpoint ? "model ready" : "no checkpoint — train first");
  } catch { $("#statusbar").textContent = "status unavailable"; }
}
refreshStatus();
setInterval(refreshStatus, 15000);

/* ---------------- chat / generate ---------------- */
function log(cls, text) {
  const div = document.createElement("div");
  div.className = cls;
  div.textContent = text;
  $("#chatlog").appendChild(div);
  $("#chatlog").scrollTop = 1e9;
}

async function generate({ width, height, seed }) {
  const body = { width, height, temperature: 0.9 };
  if (seed !== "" && seed != null) body.seed = Number(seed);
  const resp = await fetch("/api/generate", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error((await resp.json()).detail || resp.statusText);
  return resp.json();
}

$("#chatform").addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = $("#prompt").value.trim();
  log("me", prompt || `generate ${$("#width").value}x${$("#height").value}`);
  $("#genbtn").disabled = true;
  log("sys", "generating…");
  try {
    const r = await generate({
      width: Number($("#width").value), height: Number($("#height").value),
      seed: $("#seed").value,
    });
    lastResult = r;
    $("#img1x").src = `data:image/png;base64,${r.png_base64}`;
    $("#img4x").src = `data:image/png;base64,${r.png_base64_4x}`;
    const lines = Object.entries(r.score_breakdown).map(([k, v]) => `${k}: ${v}`).join("\n");
    $("#scorecard").innerHTML =
      `<span class="${r.gate_passed ? "pass" : "fail"}">automated ${r.automated_score}/85 — ` +
      `gate ${r.gate_passed ? "PASSED" : "FAILED (rebuild, not shown to human in project modes)"}</span>\n${lines}`;
    log("sys", `candidate scored ${r.automated_score}/85`);
    ["#approve", "#reject", "#adjust"].forEach((s) => ($(s).disabled = false));
  } catch (err) { log("sys", `error: ${err.message}`); }
  $("#genbtn").disabled = false;
});

async function decide(action, note = "") {
  if (!lastResult) return;
  const r = await fetch("/api/decision", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action, mode: "freeform", png_base64: lastResult.png_base64,
      width: lastResult.width, height: lastResult.height, note,
      name: $("#prompt").value.trim().slice(0, 40) || "untitled",
    }),
  });
  const data = await r.json();
  log("sys", action + (data.saved ? ` → ${data.saved}` : " logged"));
}
$("#approve").addEventListener("click", () => decide("approve"));
$("#reject").addEventListener("click", () => decide("reject"));
$("#adjust").addEventListener("click", () => {
  const note = window.prompt("Adjustment request:");
  if (note) decide("adjust", note);
});

/* ---------------- freeform tab ---------------- */
function wireFreeform() {
  let ffResult = null;
  $("#freeform-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    $("#ff-status").textContent = "generating…";
    try {
      const r = await generate({
        width: Number($("#ff-width").value), height: Number($("#ff-height").value), seed: "",
      });
      ffResult = r;
      $("#ff-img1x").src = `data:image/png;base64,${r.png_base64}`;
      $("#ff-img4x").src = `data:image/png;base64,${r.png_base64_4x}`;
      $("#ff-approve").disabled = false;
      $("#ff-status").textContent = `lighter quality check: ${r.automated_score}/85 (no 95-gate in Mode 7)`;
    } catch (err) { $("#ff-status").textContent = `error: ${err.message}`; }
  });
  $("#ff-approve").addEventListener("click", async () => {
    if (!ffResult) return;
    const r = await fetch("/api/decision", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "approve", mode: "freeform", png_base64: ffResult.png_base64,
        width: ffResult.width, height: ffResult.height,
        name: $("#ff-name").value || "untitled",
      }),
    });
    const data = await r.json();
    $("#ff-status").textContent = `saved: ${data.saved}`;
  });
}
