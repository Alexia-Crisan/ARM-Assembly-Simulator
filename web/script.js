async function assembleAndRun() {
  const code = document.getElementById("codeArea").value;
  const response = await fetch("/run", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });

  const data = await response.json();

  if (data.error) {
    document.getElementById(
      "results"
    ).innerHTML = `<div class="error-box"><b>Assembler Error:</b><br>${data.error}</div>`;
  } else {
    renderResults(data);
  }
}

function resetProgram() {
  document.getElementById("codeArea").value =
    "; Write your ARM assembly here\n";
  document.getElementById("results").innerHTML = "";
}

function renderResults(data) {
  const { registers, flags, instruction_memory, data_memory, steps } = data;

  let html = `<div class='section'><h3>Registers (after ${steps} instructions)</h3><table>`;

  const sortedRegs = Object.entries(registers).sort((a, b) => {
    const na = parseInt(a[0].replace(/\D/g, "")) || 0;
    const nb = parseInt(b[0].replace(/\D/g, "")) || 0;
    return na - nb;
  });

  for (const [r, v] of sortedRegs) {
    html += `<tr><td>${r}</td><td>0x${v
      .toString(16)
      .toUpperCase()
      .padStart(8, "0")}</td></tr>`;
  }
  html += "</table></div>";

  html += "<div class='section'><h3>Flags</h3><table>";
  for (const [f, v] of Object.entries(flags)) {
    html += `<tr><td>${f}</td><td>${v}</td></tr>`;
  }
  html += "</table></div>";

  html +=
    "<div class='section'><h3>Instruction Memory</h3><div style='max-height:150px;overflow-y:auto'><table><tr>";
  instruction_memory.slice(0, 64).forEach((val, i) => {
    if (i % 8 === 0) html += "</tr><tr>";
    html += `<td>${val.toString(16).toUpperCase().padStart(8, "0")}</td>`;
  });
  html += "</tr></table></div></div>";

  html +=
    "<div class='section'><h3>Data Memory</h3><div style='max-height:150px;overflow-y:auto'><table><tr>";
  data_memory.slice(0, 64).forEach((val, i) => {
    if (i % 8 === 0) html += "</tr><tr>";
    html += `<td>${val.toString(16).toUpperCase().padStart(8, "0")}</td>`;
  });
  html += "</tr></table></div></div>";

  document.getElementById("results").innerHTML = html;
}
