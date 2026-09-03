/**
 * Civic Sense — AI Assistant Chat Controller
 */

let chatHistory = [];

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("chatForm");
  const input = document.getElementById("chatInput");
  const clearBtn = document.getElementById("clearChatBtn");
  const chips = document.querySelectorAll(".prompt-chip");

  form?.addEventListener("submit", e => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    sendMessage(text);
    input.value = "";
  });

  chips.forEach(chip => {
    chip.addEventListener("click", () => {
      const prompt = chip.dataset.prompt;
      if (prompt) sendMessage(prompt);
    });
  });

  clearBtn?.addEventListener("click", () => {
    chatHistory = [];
    const chatBody = document.getElementById("chatBody");
    if (chatBody) {
      chatBody.innerHTML = `
        <div class="chat-bubble assistant">
          Chat cleared. Hello! How can I assist you with city infrastructure or complaints today?
        </div>
      `;
    }
    toast("Chat history cleared.");
  });
});

async function sendMessage(text) {
  const chatBody = document.getElementById("chatBody");
  const sendBtn = document.getElementById("sendBtn");

  // Append user message
  appendBubble("user", text);
  chatHistory.push({ role: "user", content: text });

  // Add typing indicator
  const typingId = "typing-" + Date.now();
  const typingBubble = document.createElement("div");
  typingBubble.className = "chat-bubble assistant";
  typingBubble.id = typingId;
  typingBubble.innerHTML = `<span class="muted">CivicSense AI is thinking…</span>`;
  chatBody.appendChild(typingBubble);
  chatBody.scrollTop = chatBody.scrollHeight;

  if (sendBtn) sendBtn.disabled = true;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history: chatHistory })
    });

    const data = await res.json();
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();

    if (sendBtn) sendBtn.disabled = false;

    if (!data.success) {
      appendBubble("assistant", "⚠️ Error: " + (data.error || "Failed to receive response."));
      return;
    }

    appendBubble("assistant", data.reply);
    chatHistory.push({ role: "assistant", content: data.reply });

  } catch (err) {
    console.error("Chat error:", err);
    const typingEl = document.getElementById(typingId);
    if (typingEl) typingEl.remove();
    if (sendBtn) sendBtn.disabled = false;
    appendBubble("assistant", "⚠️ Could not connect to the chat service. Please ensure the backend server is running.");
  }
}

function appendBubble(role, content) {
  const chatBody = document.getElementById("chatBody");
  if (!chatBody) return;

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;

  // Simple formatting for bold, newlines, and lists
  let formatted = content
    .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>");

  bubble.innerHTML = formatted;
  chatBody.appendChild(bubble);
  chatBody.scrollTop = chatBody.scrollHeight;
}
