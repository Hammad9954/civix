/**
 * Civic Sense — AI Assistant Chat Controller
 * Enhanced with Claude-style AI activity status indicator
 */

let chatHistory = [];

/* ── Configurable AI Status Messages ── */
const AI_STATUS_MESSAGES = [
  "Fathoming...",
  "Thinking...",
  "Analyzing...",
  "Formulating response...",
  "Finalizing..."
];
const AI_STATUS_ROTATE_MS = 2800; // milliseconds between status rotations

/* ── Activity Steps ── */
const AI_ACTIVITY_STEPS = [
  "Request received",
  "Analyzing input",
  "Generating response"
];

/* ── State Guard ── */
let isSending = false;

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


/* ── AI Status Indicator ── */

function createStatusIndicator() {
  const container = document.createElement("div");
  container.className = "ai-status";
  container.setAttribute("role", "status");
  container.setAttribute("aria-live", "polite");
  container.setAttribute("aria-busy", "true");

  // Header (collapsed view)
  const header = document.createElement("div");
  header.className = "ai-status-header";

  const sparkle = document.createElement("span");
  sparkle.className = "ai-status-sparkle";
  sparkle.textContent = "✦";
  sparkle.setAttribute("aria-hidden", "true");

  const text = document.createElement("span");
  text.className = "ai-status-text";
  text.textContent = AI_STATUS_MESSAGES[0];

  const toggle = document.createElement("span");
  toggle.className = "ai-status-toggle";
  toggle.textContent = "˅";
  toggle.setAttribute("aria-hidden", "true");

  header.appendChild(sparkle);
  header.appendChild(text);
  header.appendChild(toggle);

  // Expandable steps panel
  const steps = document.createElement("div");
  steps.className = "ai-status-steps";

  AI_ACTIVITY_STEPS.forEach((label, i) => {
    const step = document.createElement("div");
    step.className = "ai-status-step";
    step.dataset.stepIndex = i;

    const icon = document.createElement("span");
    icon.className = "step-icon";
    icon.textContent = "○";

    const name = document.createElement("span");
    name.textContent = label;

    step.appendChild(icon);
    step.appendChild(name);
    steps.appendChild(step);
  });

  // Toggle expand/collapse
  header.addEventListener("click", () => {
    const isOpen = steps.classList.toggle("open");
    toggle.classList.toggle("expanded", isOpen);
  });

  container.appendChild(header);
  container.appendChild(steps);

  return container;
}

function startStatusRotation(statusEl) {
  let index = 0;
  const textEl = statusEl.querySelector(".ai-status-text");
  if (!textEl) return null;

  const intervalId = setInterval(() => {
    index = (index + 1) % AI_STATUS_MESSAGES.length;
    textEl.textContent = AI_STATUS_MESSAGES[index];
  }, AI_STATUS_ROTATE_MS);

  return intervalId;
}

function progressStep(statusEl, stepIndex) {
  const allSteps = statusEl.querySelectorAll(".ai-status-step");

  allSteps.forEach((step, i) => {
    const icon = step.querySelector(".step-icon");
    step.classList.remove("done", "active");

    if (i < stepIndex) {
      step.classList.add("done");
      icon.textContent = "✓";
    } else if (i === stepIndex) {
      step.classList.add("active");
      icon.textContent = "→";
    } else {
      icon.textContent = "○";
    }
  });
}

function removeStatusIndicator(statusEl, rotationId) {
  if (rotationId) clearInterval(rotationId);
  if (!statusEl) return;
  statusEl.setAttribute("aria-busy", "false");
  statusEl.classList.remove("visible");
  setTimeout(() => statusEl.remove(), 400);
}


/* ── Core Chat Functions ── */

async function sendMessage(text) {
  if (isSending) return; // prevent duplicate submissions
  isSending = true;

  const chatBody = document.getElementById("chatBody");
  const sendBtn = document.getElementById("sendBtn");
  const chips = document.querySelectorAll(".prompt-chip");

  // Append user message
  appendBubble("user", text);
  chatHistory.push({ role: "user", content: text });

  // Disable controls
  if (sendBtn) sendBtn.disabled = true;
  chips.forEach(c => c.disabled = true);

  // Create and show AI status indicator
  const statusEl = createStatusIndicator();
  chatBody.appendChild(statusEl);
  chatBody.scrollTop = chatBody.scrollHeight;

  // Trigger visible state (after DOM paint)
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      statusEl.classList.add("visible");
    });
  });

  // Start rotating status messages
  const rotationId = startStatusRotation(statusEl);

  // Progress through activity steps on a schedule
  progressStep(statusEl, 0); // "Request received" immediately
  const stepTimer1 = setTimeout(() => progressStep(statusEl, 1), 900);   // "Analyzing input"
  const stepTimer2 = setTimeout(() => progressStep(statusEl, 2), 2200);  // "Generating response"

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history: chatHistory })
    });

    const data = await res.json();

    // Clean up timers and status
    clearTimeout(stepTimer1);
    clearTimeout(stepTimer2);
    removeStatusIndicator(statusEl, rotationId);

    // Re-enable controls
    if (sendBtn) sendBtn.disabled = false;
    chips.forEach(c => c.disabled = false);
    isSending = false;

    if (!data.success) {
      appendBubble("assistant", "⚠️ Error: " + (data.error || "Failed to receive response."), true);
      return;
    }

    appendBubble("assistant", data.reply);
    chatHistory.push({ role: "assistant", content: data.reply });

  } catch (err) {
    console.error("Chat error:", err);

    // Clean up timers and status
    clearTimeout(stepTimer1);
    clearTimeout(stepTimer2);
    removeStatusIndicator(statusEl, rotationId);

    // Re-enable controls
    if (sendBtn) sendBtn.disabled = false;
    chips.forEach(c => c.disabled = false);
    isSending = false;

    appendBubble("assistant", "⚠️ Could not connect to the chat service. Please ensure the backend server is running.", true);
  }
}

function appendBubble(role, content, isError) {
  const chatBody = document.getElementById("chatBody");
  if (!chatBody) return;

  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  if (isError) bubble.classList.add("error-bubble");

  // Simple formatting for bold, newlines, and lists
  let formatted = content
    .replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")
    .replace(/\n\n/g, "<br><br>")
    .replace(/\n/g, "<br>");

  bubble.innerHTML = formatted;
  chatBody.appendChild(bubble);
  chatBody.scrollTop = chatBody.scrollHeight;
}
