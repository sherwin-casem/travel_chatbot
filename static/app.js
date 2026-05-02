const messagesEl = document.getElementById("messages");
const form = document.getElementById("composer");
const input = document.getElementById("msg");
const sendBtn = document.getElementById("send");
const sessionPill = document.getElementById("session-pill");

let sessionId = sessionStorage.getItem("travel_session_id") || null;

function setSession(id) {
  sessionId = id;
  sessionStorage.setItem("travel_session_id", id);
  sessionPill.textContent = `Session ${id.slice(0, 8)}…`;
}

function tpl(id) {
  const t = document.getElementById(id);
  return t.content.firstElementChild.cloneNode(true);
}

function appendUser(text) {
  const node = tpl("bubble-user");
  node.querySelector(".msg-inner").textContent = text;
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(s) {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

/** Very small markdown subset: **bold**, [text](url), newlines */
function liteMarkdown(s) {
  let t = escapeHtml(s);
  t = t.replaceAll(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  t = t.replaceAll(/\[(.+?)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  return t.split("\n").join("<br>");
}

function appendBot(payload) {
  const node = tpl("bubble-bot");
  const inner = node.querySelector(".msg-inner");
  inner.innerHTML = liteMarkdown(payload.answer);

  const meta = node.querySelector(".msg-meta");
  const bits = [];
  if (payload.retrieval_confidence != null) {
    bits.push(
      `<span class="tag">match ${(payload.retrieval_confidence * 100).toFixed(0)}%</span>`,
    );
  }
  if (payload.escalated) {
    bits.push(`<span class="tag warn">human support</span>`);
  }
  if (payload.booking_link) {
    bits.push(
      `<span class="tag"><a href="${payload.booking_link}" target="_blank" rel="noopener noreferrer">booking</a></span>`,
    );
  }
  meta.innerHTML = bits.join("");

  if (payload.related_services?.length) {
    const row = document.createElement("div");
    row.className = "card-row";
    for (const svc of payload.related_services) {
      const card = document.createElement("div");
      card.className = "mini-card";
      card.innerHTML = `<strong>${escapeHtml(svc.name)}</strong><span class="muted">${escapeHtml(
        svc.reason,
      )}</span>`;
      row.appendChild(card);
    }
    inner.appendChild(row);
  }

  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function showTyping() {
  const wrap = document.createElement("div");
  wrap.className = "msg msg-bot typing-msg";
  wrap.innerHTML =
    '<div class="typing" aria-label="Assistant is typing"><span></span><span></span><span></span></div>';
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

async function sendMessage(text) {
  sendBtn.disabled = true;
  const typing = showTyping();
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || res.statusText);
    }
    const data = await res.json();
    if (!sessionId) setSession(data.session_id);
    typing.remove();
    appendBot(data);
  } catch (e) {
    typing.remove();
    appendBot({
      answer: `**Something went wrong**\n\n${e.message}`,
      related_services: [],
      retrieval_confidence: null,
      escalated: false,
      booking_link: null,
    });
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (ev) => {
  ev.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  appendUser(text);
  input.value = "";
  input.style.height = "auto";
  void sendMessage(text);
});

input.addEventListener("input", () => {
  input.style.height = "auto";
  input.style.height = `${Math.min(input.scrollHeight, 160)}px`;
});

if (sessionId) {
  setSession(sessionId);
}
