// ── Line numbers ──────────────────────────────────────────────────────
const codeArea    = document.getElementById("codeArea");
const lineNumbers = document.getElementById("line-numbers");

function updateLineNumbers() {
  const lines = codeArea.value.split("\n").length;
  lineNumbers.innerHTML = Array.from({ length: lines }, (_, i) => i + 1).join("<br>");
  lineNumbers.scrollTop = codeArea.scrollTop;
}

codeArea.addEventListener("input",  updateLineNumbers);
codeArea.addEventListener("scroll", () => { lineNumbers.scrollTop = codeArea.scrollTop; });

codeArea.addEventListener("keydown", e => {
  if (e.key === "Tab") {
    e.preventDefault();
    const s = codeArea.selectionStart;
    codeArea.value = codeArea.value.substring(0, s) + "    " + codeArea.value.substring(codeArea.selectionEnd);
    codeArea.selectionStart = codeArea.selectionEnd = s + 4;
    updateLineNumbers();
  }
});

updateLineNumbers();

// ── Normal run ────────────────────────────────────────────────────────
async function assembleAndRun() {
  exitDebugMode();
  const res  = await fetch("/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code: codeArea.value,
      user_pseudos: collectUserPseudos(),
    }),
  });
  const data = await res.json();
  if (data.error) {
    showError(data.error);
  } else {
    renderResults(data, null);
  }
}

function resetProgram() {
  exitDebugMode();
  codeArea.value = "; Write your ARM assembly here\n";
  document.getElementById("results").innerHTML =
    '<p style="color:#555;font-size:13px;">Run a program to see results here.</p>';
  updateLineNumbers();
}

function goToDocs() { window.location.href = "/docs.html"; }

function toggleMacros() {
  const panel = document.getElementById("macros-panel");
  panel.classList.toggle("hidden");
}

function addMacroRow(name = "", params = "", body = "") {
  const tbody = document.getElementById("macros-body");
  const tr    = document.createElement("tr");
  tr.className = "macro-row";
  tr.innerHTML = `
    <td><input  class="macro-name"   type="text"     placeholder="e.g. TRIPLE"   value="${escHtml(name)}"   spellcheck="false"/></td>
    <td><input  class="macro-params" type="text"     placeholder="e.g. Rd, Rn"   value="${escHtml(params)}" spellcheck="false"/></td>
    <td><textarea class="macro-body" rows="3"        placeholder="One instruction per line&#10;e.g. MOV R12, Rn&#10;ADD Rd, R12, Rn" spellcheck="false">${escHtml(body)}</textarea></td>
    <td><button class="btn-macro-del" onclick="deleteMacroRow(this)">&#10005;</button></td>
  `;
  tbody.appendChild(tr);
}

function deleteMacroRow(btn) {
  btn.closest("tr").remove();
}

function collectUserPseudos() {
  const result = {};
  document.querySelectorAll(".macro-row").forEach(row => {
    const name   = row.querySelector(".macro-name").value.trim().toUpperCase();
    const params = row.querySelector(".macro-params").value
                      .split(",").map(p => p.trim()).filter(Boolean);
    const body   = row.querySelector(".macro-body").value
                      .split("\n").map(l => l.trim()).filter(Boolean);
    if (name && body.length > 0) {
      result[name] = { params, body };
    }
  });
  return result;
}

// ── Debugger state ────────────────────────────────────────────────────
let _sessionId   = null;
let _addrToLine  = {};   // "byte_addr_str" -> instruction_index (0-based, labels excluded)
let _instrLines  = [];   // instruction lines (labels excluded) from source
let _prevRegs    = null;
let _running     = false;
let _runInterval = null;

function _instrLinesFromSource(src) {
  return src.split("\n")
    .map(l => l.trim())
    .filter(l => {
      if (!l) return false;
      let stripped = l;
      for (const sep of [";", "//"]) {
        if (stripped.includes(sep)) stripped = stripped.split(sep)[0].trim();
      }
      if (!stripped) return false;
      if (stripped.endsWith(":")) return false;
      if (stripped.includes(":")) {
        const colonIdx = stripped.indexOf(":");
        const potLabel = stripped.slice(0, colonIdx).trim();
        if (!potLabel.includes(" ")) return false;
      }
      return true;
    });
}

// ── Debug start ───────────────────────────────────────────────────────
async function startDebug() {
  exitDebugMode();
  const code = codeArea.value;
  _instrLines = _instrLinesFromSource(code);

  const res  = await fetch("/debug/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      code,
      user_pseudos: collectUserPseudos(),
    }),
  });
  const data = await res.json();
  if (data.error) { showError(data.error); return; }

  _sessionId  = data.session_id;
  _addrToLine = data.addr_to_line || {};
  _prevRegs   = null;

  document.getElementById("btn-bar").classList.add("hidden");
  document.getElementById("debug-bar").classList.remove("hidden");
  codeArea.readOnly = true;

  renderDebugState(data);
}

// ── Debug step ────────────────────────────────────────────────────────
async function stepDebug() {
  if (!_sessionId) return;
  const res  = await fetch("/debug/step", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: _sessionId }),
  });
  const data = await res.json();
  if (data.error) { showError(data.error); stopDebug(); return; }
  renderDebugState(data);
  if (data.halted) stopRunLoop();
}

// ── Debug run (continuous) ────────────────────────────────────────────
function runDebug() {
  if (!_sessionId || _running) return;
  _running = true;
  document.querySelector(".btn-run").disabled  = true;
  document.querySelector(".btn-step").disabled = true;
  _runInterval = setInterval(async () => {
    await stepDebug();
  }, 120);
}

function stopRunLoop() {
  if (_runInterval) { clearInterval(_runInterval); _runInterval = null; }
  _running = false;
  const runBtn  = document.querySelector(".btn-run");
  const stepBtn = document.querySelector(".btn-step");
  if (runBtn)  runBtn.disabled  = false;
  if (stepBtn) stepBtn.disabled = false;
}

async function stopDebug() {
  stopRunLoop();
  if (_sessionId) {
    await fetch("/debug/reset", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: _sessionId }),
    });
  }
  exitDebugMode();
}

function exitDebugMode() {
  stopRunLoop();
  _sessionId  = null;
  _addrToLine = {};
  _instrLines = [];
  _prevRegs   = null;
  codeArea.readOnly = false;
  clearLineHighlight();
  document.getElementById("btn-bar").classList.remove("hidden");
  document.getElementById("debug-bar").classList.add("hidden");
  document.getElementById("debug-status").textContent = "";
}

// ── Render debug state ────────────────────────────────────────────────
function renderDebugState(data) {
  const { registers, flags, steps, halted, pc, changed_registers,
          instruction_memory, data_memory } = data;

  // highlight current source line
  const pcStr    = String(pc);
  const lineIdx  = _addrToLine[pcStr];
  if (lineIdx !== undefined && !halted) {
    highlightLine(lineIdx);
  } else if (halted) {
    clearLineHighlight();
  }

  // status bar
  const statusEl = document.getElementById("debug-status");
  if (halted) {
    statusEl.textContent = `Halted after ${steps} instructions`;
    statusEl.style.color = "#00ff9c";
    stopRunLoop();
  } else {
    statusEl.textContent = `Step ${steps}  |  PC = 0x${pc.toString(16).toUpperCase().padStart(8,"0")}`;
    statusEl.style.color = "#888";
  }

  // current instruction label
  const curInstrText = (!halted && lineIdx !== undefined && _instrLines[lineIdx])
    ? _instrLines[lineIdx]
    : (halted ? "— halted —" : "");

  renderResults(
    { registers, flags, instruction_memory, data_memory, steps },
    changed_registers,
    curInstrText
  );

  _prevRegs = registers;
}

// ── Line highlight in editor ──────────────────────────────────────────
let _overlayEl = null;

function highlightLine(instrIdx) {
  clearLineHighlight();

  // Find which visual line in the textarea corresponds to instrIdx
  // We need to map instruction index -> line number in the raw source
  const srcLines = codeArea.value.split("\n");
  let instrCount = 0;
  let targetLineNum = -1;

  for (let i = 0; i < srcLines.length; i++) {
    let stripped = srcLines[i].trim();
    for (const sep of [";", "//"]) {
      if (stripped.includes(sep)) stripped = stripped.split(sep)[0].trim();
    }
    if (!stripped || stripped.endsWith(":")) continue;
    // inline label: "ok: MOV R1, #1" — the instruction part counts
    if (instrCount === instrIdx) { targetLineNum = i; break; }
    instrCount++;
  }

  if (targetLineNum < 0) return;

  // Create an overlay div that sits on top of the textarea
  const wrapper  = document.getElementById("editor-wrapper");
  const lineH    = 21;   // matches CSS line-height
  const padTop   = 10;   // matches textarea padding-top
  const scrollY  = codeArea.scrollTop;

  _overlayEl = document.createElement("div");
  _overlayEl.className = "line-highlight";
  _overlayEl.style.top  = `${padTop + targetLineNum * lineH - scrollY}px`;
  _overlayEl.style.height = `${lineH}px`;
  wrapper.appendChild(_overlayEl);

  // keep overlay in sync with scroll
  codeArea._hlLine = targetLineNum;
  codeArea._hlScrollHandler = () => {
    if (_overlayEl) {
      _overlayEl.style.top = `${padTop + codeArea._hlLine * lineH - codeArea.scrollTop}px`;
    }
  };
  codeArea.addEventListener("scroll", codeArea._hlScrollHandler);
}

function clearLineHighlight() {
  if (_overlayEl) { _overlayEl.remove(); _overlayEl = null; }
  if (codeArea._hlScrollHandler) {
    codeArea.removeEventListener("scroll", codeArea._hlScrollHandler);
    codeArea._hlScrollHandler = null;
  }
}

// ── Render results (shared by normal run + debugger) ──────────────────
function renderResults({ registers, flags, instruction_memory, data_memory, steps },
                        changedRegs = null, currentInstr = null) {
  const aliases = { 13: "SP", 14: "LR", 15: "PC" };
  const HLT     = 0xF0000000;

  const sortedRegs = Object.entries(registers).sort((a, b) =>
    (parseInt(a[0].slice(1)) || 0) - (parseInt(b[0].slice(1)) || 0)
  );

  const regRows = sortedRegs.map(([name, val]) => {
    const n      = parseInt(name.slice(1));
    const alias  = aliases[n] ? ` <span style="color:#555">(${aliases[n]})</span>` : "";
    const hex    = "0x" + val.toString(16).toUpperCase().padStart(8, "0");
    const dec    = val.toString(10);
    const changed = changedRegs && changedRegs.includes(n);
    const bg     = changed ? 'style="background:#1a2e1a"' : "";
    const dot    = changed ? '<span class="changed-dot"></span>' : "";
    return `<tr ${bg}><td>${dot}${name}${alias}</td><td>${hex}</td><td style="color:#666">${dec}</td></tr>`;
  }).join("");

  const flagRows = Object.entries(flags).map(([f, v]) => {
    const color = v ? "#00ff9c" : "#555";
    return `<tr><td>${f}</td><td style="color:${color};font-weight:bold">${v}</td></tr>`;
  }).join("");

  const COLS = 8;

  function buildMemGrid(words, baseAddr, usedClass) {
    let html = `<div class="mem-grid-wrap"><table class="mem-grid"><thead><tr><th></th>`;
    for (let c = 0; c < COLS; c++)
      html += `<th>+${(c*4).toString(16).padStart(2,"0").toUpperCase()}</th>`;
    html += `</tr></thead><tbody>`;
    for (let r = 0; r < Math.ceil(words.length / COLS); r++) {
      const rowAddr = baseAddr + r * COLS * 4;
      html += `<tr><td class="addr-label">${rowAddr.toString(16).toUpperCase().padStart(4,"0")}</td>`;
      for (let c = 0; c < COLS; c++) {
        const idx = r * COLS + c;
        const val = words[idx] ?? 0;
        const isUsed = val !== 0 && val !== HLT;
        const cls  = isUsed ? usedClass : "cell-empty";
        html += `<td class="${cls}">${val.toString(16).toUpperCase().padStart(8,"0")}</td>`;
      }
      html += `</tr>`;
    }
    return html + `</tbody></table></div>`;
  }

  const instrWords = (instruction_memory || []).slice(0, 64);
  const dataWords  = (data_memory || []).slice(0, 64);
  const DATA_BASE  = instrWords.length * 4;

  const instrBanner = currentInstr
    ? `<div class="current-instr">&#9658; ${escHtml(currentInstr)}</div>` : "";

  document.getElementById("results").innerHTML = `
    ${instrBanner}
    <div class="section">
      <h3>Registers — after ${steps} instruction${steps !== 1 ? "s" : ""}</h3>
      <table>
        <thead><tr><th>Register</th><th>Hex</th><th>Decimal</th></tr></thead>
        <tbody>${regRows}</tbody>
      </table>
    </div>
    <div class="section">
      <h3>Flags</h3>
      <table>
        <thead><tr><th>Flag</th><th>Value</th></tr></thead>
        <tbody>${flagRows}</tbody>
      </table>
    </div>
    <div class="section">
      <h3>Instruction Memory &nbsp;<span style="color:#555;font-size:10px">0x0000 – 0x${(DATA_BASE-1).toString(16).toUpperCase().padStart(4,"0")}</span></h3>
      ${buildMemGrid(instrWords, 0, "cell-used-instr")}
    </div>
    <div class="section">
      <h3>Data / Stack Memory &nbsp;<span style="color:#555;font-size:10px">0x${DATA_BASE.toString(16).toUpperCase().padStart(4,"0")} – 0x${(DATA_BASE + dataWords.length*4 - 1).toString(16).toUpperCase().padStart(4,"0")}</span></h3>
      ${buildMemGrid(dataWords, DATA_BASE, "cell-used-data")}
    </div>
  `;
}

// ── Utilities ─────────────────────────────────────────────────────────
function showError(msg) {
  document.getElementById("results").innerHTML =
    `<div class="error-box"><b>Error:</b><br>${escHtml(msg)}</div>`;
}

function escHtml(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}