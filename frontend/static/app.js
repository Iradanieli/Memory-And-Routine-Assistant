const state = {
  currentView: "assistant",
  scheduleMonth: null,
  pendingProtectedView: null,
};

const byId = (id) => document.getElementById(id);
const CAREGIVER_PASSWORD = "1234";
const PROTECTED_VIEWS = new Set(["schedule", "caregiver"]);

function showMessage(message) {
  const panel = byId("message-panel");
  window.clearTimeout(state.messageTimer);
  byId("message-text").textContent = message;
  panel.classList.remove("hidden");
  state.messageTimer = window.setTimeout(() => panel.classList.add("hidden"), 3500);
}

function formatDate(value, options = {}) {
  const date = new Date(`${value}T00:00:00`);
  return new Intl.DateTimeFormat("en-US", options).format(date);
}

function cleanAssistantText(value) {
  return (value || "")
    .replace(/\\([*_])/g, "$1")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/__(.*?)__/g, "$1")
    .replace(/_(.*?)_/g, "$1")
    .replace(/[*∗＊﹡]/g, "")
    .replace(/:\s+([🌍🇺🇸🎭⚽📰])/gu, ":\n\n$1")
    .replace(/\s+([🌍🇺🇸🎭⚽📰][^:\n]{1,40}:)/gu, "\n\n$1")
    .replace(/\s+-\s+/g, "\n- ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function addConversationEntry(question) {
  const container = byId("conversation-list");
  const article = document.createElement("article");
  article.className = "conversation-entry";

  const questionBlock = document.createElement("div");
  questionBlock.className = "chat-message user-message";
  const questionLabel = document.createElement("strong");
  questionLabel.textContent = "You";
  const questionText = document.createElement("p");
  questionText.textContent = question;
  questionBlock.append(questionLabel, questionText);

  const answerBlock = document.createElement("div");
  answerBlock.className = "chat-message assistant-message";
  const answerLabel = document.createElement("strong");
  answerLabel.textContent = "Assistant";
  const answerText = document.createElement("p");
  answerText.className = "assistant-answer-text";
  answerText.textContent = "Thinking...";
  answerBlock.append(answerLabel, answerText);

  article.append(questionBlock, answerBlock);
  container.append(article);
  article.scrollIntoView({ behavior: "smooth", block: "end" });

  return { answerText };
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.error || "Request failed.");
  }
  return payload;
}

function showView(viewName) {
  state.currentView = viewName;
  document.querySelectorAll(".view").forEach((view) => view.classList.add("hidden"));
  byId(`${viewName}-view`).classList.remove("hidden");
  byId("assistant-hero").classList.toggle("hidden", viewName !== "assistant");

  if (viewName === "assistant") {
    loadDashboard();
  }
  if (viewName === "schedule") {
    loadSchedule(state.scheduleMonth);
  }
}

function requestProtectedView(viewName) {
  state.pendingProtectedView = viewName;
  const modal = byId("password-modal");
  const passwordInput = byId("caregiver-password");
  byId("password-form").reset();
  modal.classList.remove("hidden");
  passwordInput.focus();
}

function closePasswordModal() {
  state.pendingProtectedView = null;
  byId("password-modal").classList.add("hidden");
}

function navigateToView(viewName) {
  if (PROTECTED_VIEWS.has(viewName)) {
    requestProtectedView(viewName);
    return;
  }

  showView(viewName);
}

function submitPassword(event) {
  event.preventDefault();
  const password = byId("caregiver-password").value;

  if (password !== CAREGIVER_PASSWORD) {
    showMessage("Incorrect caregiver password.");
    byId("caregiver-password").select();
    return;
  }

  const viewName = state.pendingProtectedView;
  closePasswordModal();
  showView(viewName);
}

function renderEvents(events) {
  const container = byId("today-events");
  container.innerHTML = "";
  if (!events.length) {
    container.innerHTML = '<p class="empty">No scheduled events.</p>';
    return;
  }

  events.forEach((event) => {
    const article = document.createElement("article");
    article.className = "routine-item";
    article.innerHTML = `
      <time>${event.time}</time>
      <div>
        <strong>${event.title}</strong>
        <span>${event.location || ""}${event.related_person ? ` · ${event.related_person}` : ""}</span>
        ${event.notes ? `<p>${event.notes}</p>` : ""}
      </div>
    `;
    container.append(article);
  });
}

function renderTasks(todos) {
  const container = byId("today-tasks");
  container.innerHTML = "";
  if (!todos.length) {
    container.innerHTML = '<p class="empty">No open tasks.</p>';
    return;
  }

  todos.forEach((todo) => {
    const article = document.createElement("article");
    article.className = `routine-item task priority-${todo.priority.toLowerCase()}`;
    article.innerHTML = `
      <time>${todo.time}</time>
      <div>
        <strong>${todo.title}</strong>
        <span>${todo.priority} priority</span>
      </div>
      <button class="small-button" type="button">Done</button>
    `;
    article.querySelector("button").addEventListener("click", async () => {
      await api(`/api/tasks/${todo.task_id}/done`, { method: "POST" });
      await loadDashboard();
    });
    container.append(article);
  });
}

async function loadDashboard() {
  const data = await api("/api/dashboard");
  byId("today-label").textContent = `Today is ${formatDate(data.today, {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  })}`;

  const fallback = byId("fallback-day-message");
  fallback.textContent = data.is_fallback_day
    ? `No routine items are dated today. Showing sample routine data from ${formatDate(data.selected_day, {
        month: "long",
        day: "numeric",
        year: "numeric",
      })}.`
    : "";

  renderEvents(data.events);
  renderTasks(data.todos);
}

async function askQuestion(event) {
  event.preventDefault();
  const question = byId("question").value.trim();
  if (!question) {
    showMessage("Please type a question first.");
    return;
  }

  byId("answer-panel").classList.remove("hidden");
  const conversationEntry = addConversationEntry(question);
  byId("question").value = "";

  try {
    const result = await api("/api/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    });
    conversationEntry.answerText.textContent = cleanAssistantText(result.answer);
  } catch (error) {
    conversationEntry.answerText.textContent = error.message;
  }
}

function renderMonthEvents(events) {
  const container = byId("month-events");
  container.innerHTML = "";
  if (!events.length) {
    container.innerHTML = '<p class="empty">No events are scheduled for this month.</p>';
    return;
  }

  events.forEach((event) => {
    const article = document.createElement("article");
    article.className = "month-event";
    article.innerHTML = `
      <div class="month-date">
        <span>${event.date}</span>
        <strong>${event.time}</strong>
      </div>
      <div>
        <h3>${event.title}</h3>
        <p>${event.location || ""}${event.related_person ? ` · ${event.related_person}` : ""}</p>
        ${event.notes ? `<p>${event.notes}</p>` : ""}
      </div>
      <div class="event-actions">
        <span class="status-pill">${event.status}</span>
        <button class="remove-button" type="button">Remove</button>
      </div>
    `;
    article.querySelector(".remove-button").addEventListener("click", async () => {
      try {
        await api(`/api/events/${event.event_id}`, { method: "DELETE" });
        await loadSchedule(state.scheduleMonth);
        showMessage("Event deleted successfully.");
      } catch (error) {
        showMessage(error.message);
      }
    });
    container.append(article);
  });
}

async function loadSchedule(month) {
  const path = month ? `/api/schedule?month=${month}` : "/api/schedule";
  const data = await api(path);
  state.scheduleMonth = data.month;
  byId("schedule-month-title").textContent = data.month_label;
  byId("previous-month").dataset.month = data.previous_month;
  byId("current-month").dataset.month = data.today_month;
  byId("next-month").dataset.month = data.next_month;
  renderMonthEvents(data.events);
}

function formPayload(form) {
  return Object.fromEntries(new FormData(form).entries());
}

async function submitEvent(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    await api("/api/events", {
      method: "POST",
      body: JSON.stringify(formPayload(form)),
    });
    form.reset();
    showMessage("Event added successfully.");
    await loadDashboard();
  } catch (error) {
    showMessage(error.message);
  }
}

async function submitTask(event) {
  event.preventDefault();
  const form = event.currentTarget;
  try {
    await api("/api/tasks", {
      method: "POST",
      body: JSON.stringify(formPayload(form)),
    });
    form.reset();
    showMessage("Task added successfully.");
    await loadDashboard();
  } catch (error) {
    showMessage(error.message);
  }
}

document.querySelectorAll("[data-view-link]").forEach((link) => {
  link.addEventListener("click", (event) => {
    event.preventDefault();
    navigateToView(event.currentTarget.dataset.viewLink);
  });
});

byId("question-form").addEventListener("submit", askQuestion);
byId("event-form").addEventListener("submit", submitEvent);
byId("task-form").addEventListener("submit", submitTask);
byId("password-form").addEventListener("submit", submitPassword);
byId("password-cancel").addEventListener("click", closePasswordModal);
["previous-month", "current-month", "next-month"].forEach((id) => {
  byId(id).addEventListener("click", (event) => loadSchedule(event.currentTarget.dataset.month));
});

loadDashboard().catch((error) => showMessage(error.message));
