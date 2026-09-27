// Live demo for the Overview page. Exercises both /echo response styles:
// a buffered JSON call and an incremental data stream.
//
// URLs are RELATIVE to the current page so the demo works at the domain root
// AND behind a reverse-proxy prefix. When this static site is served by the
// Pipe FastAPI app, /echo is on the same origin.
(function () {
  var input = document.getElementById("pipe-demo-input");
  if (!input) return; // only present on the overview page

  var BASE = new URL(".", window.location.href);
  var api = function (p) { return new URL(p, BASE).toString(); };
  var out = document.getElementById("pipe-demo-out");
  var chunk = document.getElementById("pipe-demo-chunk");

  function setOut(text, err) {
    out.textContent = text;
    out.style.color = err ? "#cf222e" : "";
  }

  async function runBuffered() {
    setOut("… requesting /echo");
    try {
      var res = await fetch(api("echo?data=" + encodeURIComponent(input.value)));
      if (!res.ok) throw new Error("HTTP " + res.status);
      setOut("GET /echo → " + JSON.stringify(await res.json(), null, 2));
    } catch (e) {
      setOut("error: " + e.message + " (is the Pipe API serving this page?)", true);
    }
  }

  async function runStream() {
    var size = Math.max(1, parseInt(chunk.value, 10) || 4);
    setOut("");
    try {
      var res = await fetch(api("echo/stream?data=" + encodeURIComponent(input.value) + "&chunk_size=" + size));
      if (!res.ok || !res.body) throw new Error("HTTP " + res.status);
      var reader = res.body.getReader();
      var dec = new TextDecoder();
      var acc = "", n = 0;
      for (;;) {
        var r = await reader.read();
        if (r.done) break;
        n += 1;
        acc += dec.decode(r.value, { stream: true });
        setOut("streaming (" + n + " chunk" + (n === 1 ? "" : "s") + ") →\n" + acc);
      }
      setOut("done — " + n + " chunk(s) →\n" + acc);
    } catch (e) {
      setOut("error: " + e.message + " (is the Pipe API serving this page?)", true);
    }
  }

  document.getElementById("pipe-demo-buffered").addEventListener("click", runBuffered);
  document.getElementById("pipe-demo-stream").addEventListener("click", runStream);
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") runBuffered(); });
})();
