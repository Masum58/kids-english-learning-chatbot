const API_URL = window.TEDDY_API_URL || "http://localhost:8000";
const sessionKey = "teddy-english-session";
let sessionId = localStorage.getItem(sessionKey) || null;

const messages = document.querySelector("#messages");
const quickReplies = document.querySelector("#quick-replies");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const sendButton = document.querySelector(".send-button");
const toast = document.querySelector("#toast");

function addMessage(text, kind = "teddy") {
  const item = document.createElement("article");
  item.className = `message ${kind}-message`;
  item.textContent = text;
  messages.append(item);
  messages.scrollTop = messages.scrollHeight;
  return item;
}

function setQuickReplies(items) {
  quickReplies.replaceChildren();
  items.forEach((item) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = item;
    button.addEventListener("click", () => sendMessage(item));
    quickReplies.append(button);
  });
}

function updateProgress(progress) {
  if (!progress) return;
  document.querySelector("#level-label").textContent = `Level ${progress.level}`;
  document.querySelector("#progress-label").textContent = `${progress.correct} / ${progress.target}`;
  document.querySelector("#progress-bar").style.width = `${(progress.correct / progress.target) * 100}%`;
  document.querySelectorAll("#stars span").forEach((star, index) => star.classList.toggle("earned", index < progress.correct));
}

function showError(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 3500);
}

async function sendMessage(rawMessage) {
  const message = rawMessage.trim();
  if (!message || sendButton.disabled) return;
  input.value = "";
  addMessage(message, "user");
  sendButton.disabled = true;
  const typing = addMessage("Teddy is thinking...", "typing");
  try {
    const response = await fetch(`${API_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, message }),
    });
    if (!response.ok) throw new Error("Could not reach Teddy");
    const data = await response.json();
    sessionId = data.session_id;
    localStorage.setItem(sessionKey, sessionId);
    typing.remove();
    addMessage(data.reply, "teddy");
    setQuickReplies(data.quick_replies);
    updateProgress(data.progress);
  } catch (error) {
    typing.remove();
    showError("Teddy needs a moment. Is the server running?");
  } finally {
    sendButton.disabled = false;
    input.focus();
  }
}

form.addEventListener("submit", (event) => { event.preventDefault(); sendMessage(input.value); });
