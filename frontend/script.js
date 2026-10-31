// ---------- Settings ----------
const MAX_FILE_BYTES = 5 * 1024 * 1024; // 5 MB, same limit as the backend
const RESUME_TYPES = [".pdf", ".docx"];
const JD_TYPES = [".pdf", ".docx", ".txt"];
const MIN_JD_CHARS = 40;
const RING_LENGTH = 326.73; // circumference of the score ring (2 * PI * 52)

// ---------- Page elements ----------
const hero = document.getElementById("hero");
const formSection = document.getElementById("form-section");
const loadingSection = document.getElementById("loading");
const loadingText = document.getElementById("loading-text");
const resultsSection = document.getElementById("results");
const errorBox = document.getElementById("error-box");
const analyzeBtn = document.getElementById("analyze-btn");
const resetBtn = document.getElementById("reset-btn");

const resumeDrop = document.getElementById("resume-drop");
const resumeInput = document.getElementById("resume-input");
const resumeChip = document.getElementById("resume-file");
const resumeChipName = document.getElementById("resume-file-name");
const resumeRemove = document.getElementById("resume-remove");

const jdText = document.getElementById("jd-text");
const jdFileInput = document.getElementById("jd-file-input");
const jdChip = document.getElementById("jd-file");
const jdChipName = document.getElementById("jd-file-name");
const jdRemove = document.getElementById("jd-remove");

// ---------- State ----------
let resumeFile = null;
let jdFile = null;
let loadingTimer = null;

// ---------- Helpers ----------
function showError(message) {
  errorBox.textContent = message;
  errorBox.hidden = false;
}

function clearError() {
  errorBox.hidden = true;
  errorBox.textContent = "";
}

// Returns an error message, or "" if the file is fine.
function checkFile(file, allowedTypes, label) {
  const name = file.name.toLowerCase();
  const okType = allowedTypes.some((ext) => name.endsWith(ext));
  if (!okType) {
    return `The ${label} must be one of: ${allowedTypes.join(", ")}.`;
  }
  if (file.size > MAX_FILE_BYTES) {
    return `The ${label} is larger than 5 MB.`;
  }
  return "";
}

// ---------- Resume file ----------
function setResume(file) {
  const problem = checkFile(file, RESUME_TYPES, "resume");
  if (problem) {
    showError(problem);
    return;
  }
  clearError();
  resumeFile = file;
  resumeChipName.textContent = file.name;
  resumeChip.hidden = false;
}

function clearResume() {
  resumeFile = null;
  resumeInput.value = "";
  resumeChip.hidden = true;
}

resumeInput.addEventListener("change", () => {
  if (resumeInput.files.length > 0) setResume(resumeInput.files[0]);
});

resumeRemove.addEventListener("click", clearResume);

resumeDrop.addEventListener("dragover", (event) => {
  event.preventDefault();
  resumeDrop.classList.add("drag-active");
});

resumeDrop.addEventListener("dragleave", () => {
  resumeDrop.classList.remove("drag-active");
});

resumeDrop.addEventListener("drop", (event) => {
  event.preventDefault();
  resumeDrop.classList.remove("drag-active");
  if (event.dataTransfer.files.length > 0) setResume(event.dataTransfer.files[0]);
});

// ---------- Job description file (optional) ----------
function setJdFile(file) {
  const problem = checkFile(file, JD_TYPES, "job description file");
  if (problem) {
    showError(problem);
    return;
  }
  clearError();
  jdFile = file;
  jdChipName.textContent = file.name;
  jdChip.hidden = false;
}

function clearJdFile() {
  jdFile = null;
  jdFileInput.value = "";
  jdChip.hidden = true;
}

jdFileInput.addEventListener("change", () => {
  if (jdFileInput.files.length > 0) setJdFile(jdFileInput.files[0]);
});

jdRemove.addEventListener("click", clearJdFile);

// ---------- Loading messages ----------
// The server does everything in one request, so these messages only tell the user
// what is happening in general. They are not real-time progress.
const LOADING_MESSAGES = [
  "Reading your resume...",
  "Extracting skills and experience...",
  "Comparing with the job description...",
  "Calculating your match score...",
];

function startLoading() {
  formSection.hidden = true;
  resultsSection.hidden = true;
  loadingSection.hidden = false;

  let index = 0;
  loadingText.textContent = LOADING_MESSAGES[0];
  loadingTimer = setInterval(() => {
    index = Math.min(index + 1, LOADING_MESSAGES.length - 1);
    loadingText.textContent = LOADING_MESSAGES[index];
  }, 4000);
}

function stopLoading() {
  clearInterval(loadingTimer);
  loadingTimer = null;
  loadingSection.hidden = true;
}

// ---------- Rendering results ----------
// textContent is used everywhere (never innerHTML), so text coming from the AI
// can never inject HTML or scripts into the page.
function renderChips(container, items, chipClass, emptyMessage) {
  container.replaceChildren();
  if (!items || items.length === 0) {
    const empty = document.createElement("span");
    empty.className = "chip-empty";
    empty.textContent = emptyMessage;
    container.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const chip = document.createElement("span");
    chip.className = `chip ${chipClass}`;
    chip.textContent = item;
    container.appendChild(chip);
  });
}

function renderReasons(reasons) {
  const list = document.getElementById("reasons-list");
  list.replaceChildren();
  if (!reasons || reasons.length === 0) {
    const li = document.createElement("li");
    li.textContent = "No explanation was returned.";
    list.appendChild(li);
    return;
  }
  reasons.forEach((reason) => {
    const li = document.createElement("li");
    li.textContent = reason;
    list.appendChild(li);
  });
}

function animateScore(score) {
  const ring = document.getElementById("ring-fill");
  const valueEl = document.getElementById("score-value");

  // Reset first, then fill on the next frame so the CSS transition plays.
  ring.style.strokeDashoffset = RING_LENGTH;
  requestAnimationFrame(() => {
    ring.style.strokeDashoffset = RING_LENGTH * (1 - score / 100);
  });

  // Count the number up from 0.
  const duration = 900;
  const start = performance.now();
  function tick(now) {
    const progress = Math.min((now - start) / duration, 1);
    valueEl.textContent = Math.round(score * progress);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function renderResults(data) {
  const tier = data.match_score >= 75 ? "high" : data.match_score >= 50 ? "mid" : "low";
  resultsSection.dataset.tier = tier;

  document.getElementById("verdict").textContent = data.verdict;
  document.getElementById("candidate-name").textContent = data.candidate_name
    ? `Candidate: ${data.candidate_name}`
    : "";

  renderReasons(data.reasons);

  renderChips(
    document.getElementById("matched-list"),
    data.matched_skills,
    "chip-good",
    "No matching skills were found."
  );
  renderChips(
    document.getElementById("missing-list"),
    data.missing_skills,
    "chip-bad",
    "No missing skills. This resume covers the requirements."
  );
  renderChips(
    document.getElementById("resume-skills-list"),
    data.resume_skills,
    "chip-neutral",
    "No skills were extracted."
  );

  document.getElementById("matched-count").textContent = data.matched_skills.length;
  document.getElementById("missing-count").textContent = data.missing_skills.length;

  hero.hidden = true;
  resultsSection.hidden = false;
  animateScore(data.match_score);
  resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ---------- Calling the backend ----------
// FastAPI sends errors as { detail: "message" } or { detail: [ {msg: ...}, ... ] }.
function readErrorMessage(data) {
  if (data && typeof data.detail === "string") return data.detail;
  if (data && Array.isArray(data.detail)) {
    return data.detail.map((item) => item.msg).join(". ");
  }
  return "Something went wrong. Please try again.";
}

async function analyze() {
  clearError();

  if (!resumeFile) {
    showError("Please upload your resume (PDF or DOCX).");
    return;
  }

  const pastedJd = jdText.value.trim();
  if (!pastedJd && !jdFile) {
    showError("Please paste the job description or upload it as a file.");
    return;
  }
  if (pastedJd && pastedJd.length < MIN_JD_CHARS) {
    showError("The job description looks too short. Please paste the full text.");
    return;
  }

  const formData = new FormData();
  formData.append("resume", resumeFile);
  if (pastedJd) {
    formData.append("jd_text", pastedJd);
  } else {
    formData.append("jd_file", jdFile);
  }

  analyzeBtn.disabled = true;
  startLoading();

  try {
    const response = await fetch(`${API_BASE_URL}/api/analyze`, {
      method: "POST",
      body: formData,
    });

    let data = null;
    try {
      data = await response.json();
    } catch (parseError) {
      data = null;
    }

    if (!response.ok) {
      throw new Error(readErrorMessage(data));
    }

    stopLoading();
    renderResults(data);
  } catch (error) {
    stopLoading();
    formSection.hidden = false;
    if (error instanceof TypeError) {
      // fetch() throws a TypeError when the server cannot be reached at all.
      showError("Cannot reach the server. Make sure the backend is running.");
    } else {
      showError(error.message);
    }
  } finally {
    analyzeBtn.disabled = false;
  }
}

analyzeBtn.addEventListener("click", analyze);

resetBtn.addEventListener("click", () => {
  clearResume();
  clearJdFile();
  jdText.value = "";
  clearError();
  resultsSection.hidden = true;
  hero.hidden = false;
  formSection.hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
});
