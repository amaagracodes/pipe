// Live demo wiring for the landing page. Exercises both response styles:
// a buffered JSON call (echo) and an incremental data stream (echo/stream).
//
// URLs are RELATIVE to the page's directory so the demo works both at the
// domain root and behind a reverse-proxy prefix (e.g. /proxy/8787/).

const $ = (id) => document.getElementById(id);
const input = $("input");
const chunk = $("chunk");
const out = $("output");

// Base = current directory of this page (keeps proxy prefixes intact).
const BASE = new URL(".", window.location.href);
const api = (path) => new URL(path, BASE).toString();

function setOutput(text, isError = false) {
  out.textContent = text;
  out.classList.toggle("error", isError);
}

async function runBuffered() {
  const data = input.value;
  setOutput("… requesting /echo");
  try {
    const res = await fetch(api(`echo?data=${encodeURIComponent(data)}`));
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    setOutput(`GET /echo  →  ${JSON.stringify(json, null, 2)}`);
  } catch (err) {
    setOutput(`error: ${err.message}`, true);
  }
}

async function runStream() {
  const data = input.value;
  const size = Math.max(1, parseInt(chunk.value, 10) || 4);
  setOutput("");
  try {
    const res = await fetch(
      api(`echo/stream?data=${encodeURIComponent(data)}&chunk_size=${size}`)
    );
    if (!res.ok || !res.body) throw new Error(`HTTP ${res.status}`);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let acc = "";
    let chunks = 0;
    // Read the stream chunk-by-chunk so you can see it arrive incrementally.
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks += 1;
      acc += decoder.decode(value, { stream: true });
      setOutput(`streaming (${chunks} chunk${chunks === 1 ? "" : "s"}) →\n${acc}`);
    }
    setOutput(`done — ${chunks} chunk(s) streamed →\n${acc}`);
  } catch (err) {
    setOutput(`error: ${err.message}`, true);
  }
}

$("btn-buffered").addEventListener("click", runBuffered);
$("btn-stream").addEventListener("click", runStream);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter") runBuffered();
});
