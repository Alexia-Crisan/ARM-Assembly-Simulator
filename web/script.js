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
    const v = codeArea.value;
    codeArea.value = v.substring(0, s) + "    " + v.substring(codeArea.selectionEnd);
    codeArea.selectionStart = codeArea.selectionEnd = s + 4;
    updateLineNumbers();
  }
});

updateLineNumbers();

async function assembleAndRun() {
  const code = codeArea.value;
  const res  = await fetch("/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
  const data = await res.json();

  if (data.error) {
    document.getElementById("results").innerHTML =
      `<div class="error-box"><b>Error:</b><br>${escHtml(data.error)}</div>`;
  } else {
    renderResults(data);
  }
}

function resetProgram() {
  codeArea.value = "; Write your ARM assembly here\n";
  document.getElementById("results").innerHTML =
    '<p style="color:#555;font-size:13px;">Run a program to see results here.</p>';
  updateLineNumbers();
}

function goToDocs() { window.location.href = "/docs.html"; }

function renderResults({ registers, flags, instruction_memory, data_memory, steps }) {
  const aliases = { 13: "SP", 14: "LR", 15: "PC" };

  const sortedRegs = Object.entries(registers).sort((a, b) => {
    return (parseInt(a[0].slice(1)) || 0) - (parseInt(b[0].slice(1)) || 0);
  });

  let regRows = sortedRegs.map(([name, val]) => {
    const n     = parseInt(name.slice(1));
    const alias = aliases[n] ? ` <span style="color:#555">(${aliases[n]})</span>` : "";
    const hex   = "0x" + val.toString(16).toUpperCase().padStart(8, "0");
    const dec   = val.toString(10);
    return `<tr><td>${name}${alias}</td><td>${hex}</td><td style="color:#666">${dec}</td></tr>`;
  }).join("");

  let flagRows = Object.entries(flags).map(([f, v]) => {
    const color = v ? "#00ff9c" : "#555";
    return `<tr><td>${f}</td><td style="color:${color};font-weight:bold">${v}</td></tr>`;
  }).join("");

  const COLS = 8;

  function buildMemGrid(words, baseAddr, usedClass) {
    const HLT = 0xF0000000;
    let html = `<div class="mem-grid-wrap"><table class="mem-grid"><thead><tr>
      <th></th>`;
    for (let c = 0; c < COLS; c++)
      html += `<th>+${(c * 4).toString(16).padStart(2,"0").toUpperCase()}</th>`;
    html += `</tr></thead><tbody>`;

    for (let r = 0; r < Math.ceil(words.length / COLS); r++) {
      const rowAddr = baseAddr + r * COLS * 4;
      html += `<tr><td class="addr-label">${rowAddr.toString(16).toUpperCase().padStart(4,"0")}</td>`;
      for (let c = 0; c < COLS; c++) {
        const idx = r * COLS + c;
        const val = words[idx] ?? 0;
        const isUsed = val !== 0 && val !== HLT;
        const cls = isUsed ? usedClass : "cell-empty";
        const txt = val.toString(16).toUpperCase().padStart(8, "0");
        html += `<td class="${cls}">${txt}</td>`;
      }
      html += `</tr>`;
    }
    return html + `</tbody></table></div>`;
  }

  const instrWords = instruction_memory.slice(0, 64);
  const dataWords  = data_memory.slice(0, 64);
  const DATA_BASE  = instrWords.length * 4;

  document.getElementById("results").innerHTML = `
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

function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}