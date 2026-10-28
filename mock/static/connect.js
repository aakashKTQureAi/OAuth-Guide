// Model connection panel. The key is posted once to our server and never kept in the page.
const DEFAULT_MODEL = { anthropic: "claude-opus-5-5", portkey: "claude-opus-5-5", openai: "" };
const LABEL = { anthropic: "Anthropic", openai: "OpenAI", portkey: "Portkey" };

function showConnection(c) {
  const chip = document.getElementById("conn-chip");
  chip.textContent = c.connected ? `Model: ${LABEL[c.provider]} · ${c.model}` : "No model connected";
  chip.classList.toggle("off", !c.connected);
  document.getElementById("conn-disconnect").hidden = !c.connected;
}

async function refreshConnection() {
  const c = await fetch("/api/connection", { cache: "no-store" }).then(r => r.json());
  showConnection(c);
  return c;
}

function initConnect() {
  const form = document.getElementById("conn-form");
  const provider = form.elements.provider, model = form.elements.model, portkey = document.getElementById("conn-portkey");
  const sync = () => { model.value = DEFAULT_MODEL[provider.value]; portkey.hidden = provider.value !== "portkey"; };
  provider.addEventListener("change", sync);
  sync();
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const status = document.getElementById("conn-status");
    status.textContent = "Checking the key…";
    const body = Object.fromEntries(new FormData(form));
    form.elements.api_key.value = "";  // drop the key from the page as soon as it is sent
    const res = await fetch("/api/connect", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const out = await res.json();
    status.textContent = res.ok ? "Connected. The key lives only in server memory for this session." : out.error;
    if (res.ok) { showConnection(out); document.getElementById("conn-panel").open = false; }
  });
  document.getElementById("conn-disconnect").addEventListener("click", async () => {
    showConnection(await fetch("/api/disconnect", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }).then(r => r.json()));
  });
  refreshConnection();
}

initConnect();
