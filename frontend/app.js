/* ============================================================
   AI Resume Generator — app.js
   Multi-step form logic, CrewAI API integration, dynamic UI
   ============================================================ */

// ── State ──────────────────────────────────────────────────────────────────
let currentStep = 0;  // 0 = hero
const TOTAL_STEPS = 4;

const state = {
  skills: ["Communication"],
  certifications: [],
  experiences: [],
  educations: [],
  generatedResume: "",
};

let expCounter = 0;
let eduCounter = 0;
const loadingMessages = [
  { title: "Agents initializing…",   subtitle: "Setting up CrewAI environment" },
  { title: "Writer Agent active…",   subtitle: "Analyzing your career data" },
  { title: "Drafting your resume…",  subtitle: "Crafting compelling bullet points" },
  { title: "Critic Agent reviewing…",subtitle: "Polishing and optimizing content" },
  { title: "Almost there…",          subtitle: "Formatting the final output" },
];

// ── Init ───────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Initialise with one experience and one education card
  addExperience();
  addEducation();

  // Objective char counter
  const objectiveTA = document.getElementById("objective");
  const objectiveCount = document.getElementById("objective-count");
  objectiveTA.addEventListener("input", () => {
    objectiveCount.textContent = objectiveTA.value.length;
  });

  // Skill input - Enter or comma
  setupTagInput("skill-input", "skill-tags", state.skills);
  setupTagInput("cert-input",  "cert-tags",  state.certifications);

  // Render initial skill tag
  const skillTagsEl = document.getElementById("skill-tags");
  state.skills.forEach(skill => {
    const tag = document.createElement("span");
    tag.className = "skill-tag";
    tag.innerHTML = `${escapeHtml(skill)}<button class="tag-remove" title="Remove">×</button>`;
    tag.querySelector(".tag-remove").addEventListener("click", () => {
      const i = state.skills.indexOf(skill);
      if (i > -1) state.skills.splice(i, 1);
      tag.style.animation = "none";
      tag.style.transform = "scale(0)";
      tag.style.opacity = "0";
      tag.style.transition = "0.15s ease";
      setTimeout(() => tag.remove(), 150);
    });
    skillTagsEl.appendChild(tag);
  });

  // Style picker radio sync
  document.querySelectorAll('input[name="template-style"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      document.querySelectorAll(".style-card").forEach((c) => c.classList.remove("active"));
      radio.closest(".style-card").classList.add("active");
    });
  });
});

// ── Navigation ─────────────────────────────────────────────────────────────
function goToHero() {
  document.getElementById("form-container").classList.add("hidden");
  document.getElementById("hero-section").style.display = "";
  currentStep = 0;
  updateProgress(0);
}

document.getElementById("start-btn").addEventListener("click", () => {
  document.getElementById("hero-section").style.display = "none";
  const fc = document.getElementById("form-container");
  fc.classList.remove("hidden");
  showStep(1);
});

function nextStep(from) {
  if (!validateStep(from)) return;
  showStep(from + 1);
}

function prevStep(from) {
  showStep(from - 1);
}

function showStep(n) {
  // Hide all panels
  document.querySelectorAll(".step-panel").forEach((p) => {
    p.classList.remove("active");
  });
  // Show target
  const target = document.getElementById(`step-${n}`);
  target.classList.add("active");
  currentStep = n;
  updateProgress(n);
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function updateProgress(step) {
  const pct = step === 0 ? 0 : ((step - 1) / (TOTAL_STEPS - 1)) * 100;
  document.getElementById("progress-fill").style.width = `${pct}%`;

  document.querySelectorAll(".step-dot").forEach((dot) => {
    const s = parseInt(dot.dataset.step);
    dot.classList.remove("active", "completed");
    if (s === step)       dot.classList.add("active");
    if (s < step)         dot.classList.add("completed");
  });

  document.querySelectorAll(".step-line").forEach((line, i) => {
    line.classList.remove("active", "completed");
    if (i + 1 < step)  line.classList.add("completed");
    if (i + 1 === step - 1) line.classList.add("active");
  });
}

// ── Validation ─────────────────────────────────────────────────────────────
function validateStep(step) {
  if (step === 1) {
    const fields = ["full-name", "email", "phone", "location", "objective"];
    for (const id of fields) {
      const el = document.getElementById(id);
      if (!el.value.trim()) {
        shakeField(el);
        showToast(`Please fill in: ${el.previousElementSibling.textContent.replace(" *", "")}`, "error");
        return false;
      }
    }
  }
  if (step === 4) {
    if (state.skills.length === 0) {
      showToast("Please add at least one skill.", "error");
      return false;
    }
  }
  return true;
}

function shakeField(el) {
  el.style.animation = "none";
  el.style.borderColor = "var(--danger)";
  el.style.boxShadow = "0 0 0 3px rgba(239,68,68,0.2)";
  setTimeout(() => {
    el.style.borderColor = "";
    el.style.boxShadow = "";
  }, 1500);
}

// ── Dynamic Work Experience ────────────────────────────────────────────────
function addExperience() {
  expCounter++;
  const idx = expCounter;
  state.experiences.push({ id: idx });
  const list = document.getElementById("experience-list");
  const card = document.createElement("div");
  card.className = "entry-card";
  card.id = `exp-card-${idx}`;
  card.innerHTML = `
    <div class="entry-card-header">
      <span class="entry-card-title">Experience #${idx}</span>
      <button class="btn-remove" onclick="removeExperience(${idx})" title="Remove">×</button>
    </div>
    <div class="entry-grid">
      <div class="field-group">
        <label>Company Name *</label>
        <input type="text" id="exp-company-${idx}" placeholder="e.g. Google" />
      </div>
      <div class="field-group">
        <label>Job Title / Role *</label>
        <input type="text" id="exp-role-${idx}" placeholder="e.g. Software Engineer" />
      </div>
      <div class="field-group">
        <label>Duration *</label>
        <input type="text" id="exp-duration-${idx}" placeholder="e.g. Jan 2022 – Dec 2023" />
      </div>
    </div>
    <div class="field-group" style="margin-top:.9rem">
      <label>Key Responsibilities & Achievements *</label>
      <textarea id="exp-desc-${idx}" rows="3"
        placeholder="Describe what you did, led, built, or improved. Include metrics where possible."></textarea>
    </div>
  `;
  list.appendChild(card);
}

function removeExperience(idx) {
  const card = document.getElementById(`exp-card-${idx}`);
  card.style.opacity = "0";
  card.style.transform = "scale(0.95)";
  card.style.transition = "0.2s ease";
  setTimeout(() => {
    card.remove();
    state.experiences = state.experiences.filter((e) => e.id !== idx);
  }, 200);
}

function collectExperiences() {
  const items = document.querySelectorAll(".entry-card[id^='exp-card-']");
  return Array.from(items).map((card) => {
    const idx = card.id.replace("exp-card-", "");
    return {
      company:     (document.getElementById(`exp-company-${idx}`)?.value || "").trim(),
      role:        (document.getElementById(`exp-role-${idx}`)?.value || "").trim(),
      duration:    (document.getElementById(`exp-duration-${idx}`)?.value || "").trim(),
      description: (document.getElementById(`exp-desc-${idx}`)?.value || "").trim(),
    };
  }).filter((e) => e.company || e.role);
}

// ── Dynamic Education ──────────────────────────────────────────────────────
function addEducation() {
  eduCounter++;
  const idx = eduCounter;
  state.educations.push({ id: idx });
  const list = document.getElementById("education-list");
  const card = document.createElement("div");
  card.className = "entry-card";
  card.id = `edu-card-${idx}`;
  card.innerHTML = `
    <div class="entry-card-header">
      <span class="entry-card-title">Education #${idx}</span>
      <button class="btn-remove" onclick="removeEducation(${idx})" title="Remove">×</button>
    </div>
    <div class="entry-grid">
      <div class="field-group">
        <label>Institution *</label>
        <input type="text" id="edu-inst-${idx}" placeholder="e.g. MIT" />
      </div>
      <div class="field-group">
        <label>Degree / Qualification *</label>
        <input type="text" id="edu-degree-${idx}" placeholder="e.g. B.Sc. Computer Science" />
      </div>
      <div class="field-group">
        <label>Year *</label>
        <input type="text" id="edu-year-${idx}" placeholder="e.g. 2018 – 2022" />
      </div>
      <div class="field-group">
        <label>GPA <span class="optional">(optional)</span></label>
        <input type="text" id="edu-gpa-${idx}" placeholder="e.g. 3.8/4.0" />
      </div>
    </div>
  `;
  list.appendChild(card);
}

function removeEducation(idx) {
  const card = document.getElementById(`edu-card-${idx}`);
  card.style.opacity = "0";
  card.style.transform = "scale(0.95)";
  card.style.transition = "0.2s ease";
  setTimeout(() => {
    card.remove();
    state.educations = state.educations.filter((e) => e.id !== idx);
  }, 200);
}

function collectEducations() {
  const items = document.querySelectorAll(".entry-card[id^='edu-card-']");
  return Array.from(items).map((card) => {
    const idx = card.id.replace("edu-card-", "");
    return {
      institution: (document.getElementById(`edu-inst-${idx}`)?.value || "").trim(),
      degree:      (document.getElementById(`edu-degree-${idx}`)?.value || "").trim(),
      year:        (document.getElementById(`edu-year-${idx}`)?.value || "").trim(),
      gpa:         (document.getElementById(`edu-gpa-${idx}`)?.value || "").trim() || null,
    };
  }).filter((e) => e.institution || e.degree);
}

// ── Tag Input (Skills / Certifications) ────────────────────────────────────
function setupTagInput(inputId, tagsId, tagsArray) {
  const input = document.getElementById(inputId);
  const tagsEl = document.getElementById(tagsId);

  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addTag(input.value.replace(",", "").trim(), tagsArray, tagsEl);
      input.value = "";
    }
  });
}

function addTag(text, array, container) {
  if (!text || array.includes(text)) return;
  array.push(text);
  const tag = document.createElement("span");
  tag.className = "skill-tag";
  tag.innerHTML = `${escapeHtml(text)}<button class="tag-remove" title="Remove">×</button>`;
  tag.querySelector(".tag-remove").addEventListener("click", () => {
    const i = array.indexOf(text);
    if (i > -1) array.splice(i, 1);
    tag.style.animation = "none";
    tag.style.transform = "scale(0)";
    tag.style.opacity = "0";
    tag.style.transition = "0.15s ease";
    setTimeout(() => tag.remove(), 150);
  });
  container.appendChild(tag);
}

// ── Generate Resume ─────────────────────────────────────────────────────────
async function generateResume() {
  if (!validateStep(4)) return;

  const payload = {
    full_name:      document.getElementById("full-name").value.trim(),
    email:          document.getElementById("email").value.trim(),
    phone:          document.getElementById("phone").value.trim(),
    location:       document.getElementById("location").value.trim(),
    linkedin:       document.getElementById("linkedin").value.trim() || null,
    portfolio:      document.getElementById("portfolio").value.trim() || null,
    objective:      document.getElementById("objective").value.trim(),
    experiences:    collectExperiences(),
    education:      collectEducations(),
    skills:         [...state.skills],
    certifications: [...state.certifications],
    template_style: document.querySelector('input[name="template-style"]:checked')?.value || "modern",
  };

  // Show loading overlay
  showLoading();

  try {
    const res = await fetch("/api/generate-resume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      let errMsg = `HTTP ${res.status}`;
      try {
        const text = await res.text();
        if (text) {
          try {
            const err = JSON.parse(text);
            errMsg = err.detail || err.message || text;
          } catch (e) {
            errMsg = text;
          }
        }
      } catch (e) {
        errMsg = `HTTP ${res.status}: ${e.message}`;
      }
      throw new Error(errMsg);
    }

    const data = await res.json();
    state.generatedResume = data.generated_resume;
    hideLoading();
    renderResult(data);
  } catch (err) {
    hideLoading();
    showToast(`Error: ${err.message}`, "error");
    console.error("Generation error:", err);
  }
}

function renderResult(data) {
  showStep(5);

  // Render Markdown resume
  const preview = document.getElementById("resume-preview");
  preview.innerHTML = marked.parse(data.generated_resume || "*(No content returned)*");

  // Render tips
  const tipsSection = document.getElementById("tips-section");
  const tipsList = document.getElementById("tips-list");
  tipsList.innerHTML = "";

  if (data.tips && data.tips.length > 0) {
    tipsSection.style.display = "";
    data.tips.forEach((tip) => {
      const li = document.createElement("li");
      li.textContent = tip;
      tipsList.appendChild(li);
    });
  } else {
    tipsSection.style.display = "none";
  }

  // Word count
  const wc = document.getElementById("word-count-badge");
  wc.textContent = wc.textContent = `📄 ${data.word_count || 0} words`;

  // Animate in
  preview.style.opacity = "0";
  preview.style.transform = "translateY(20px)";
  preview.style.transition = "0.5s ease";
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      preview.style.opacity = "1";
      preview.style.transform = "translateY(0)";
    });
  });
}

// ── Copy & Download ─────────────────────────────────────────────────────────
function copyResume() {
  if (!state.generatedResume) return;
  navigator.clipboard.writeText(state.generatedResume).then(() => {
    showToast("✓ Copied to clipboard!");
    const btn = document.getElementById("copy-btn");
    btn.textContent = "✓ Copied!";
    setTimeout(() => {
      btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copy Markdown`;
    }, 2000);
  });
}

function downloadResume() {
  if (!state.generatedResume) return;
  const name = document.getElementById("full-name").value.trim().replace(/\s+/g, "_") || "resume";
  const blob = new Blob([state.generatedResume], { type: "text/plain" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${name}_resume.txt`;
  a.click();
  URL.revokeObjectURL(a.href);
  showToast("✓ Download started!");
}

function regenerate() {
  showStep(4);
}

// ── Loading Animation ─────────────────────────────────────────────────────
let loadingInterval = null;
let loadingStepIdx = 0;

function showLoading() {
  const overlay = document.getElementById("loading-overlay");
  overlay.classList.remove("hidden");

  // Reset steps
  ["ls-1","ls-2","ls-3","ls-4"].forEach((id) => {
    const el = document.getElementById(id);
    el.classList.remove("active","done");
  });

  loadingStepIdx = 0;
  activateLoadStep(0);

  // Cycle through steps
  const stepDurations = [2500, 4000, 4000, 3000];
  let elapsed = 0;
  loadingInterval = setInterval(() => {
    elapsed += 500;
    if (elapsed >= stepDurations[loadingStepIdx]) {
      elapsed = 0;
      advanceLoadStep();
    }
  }, 500);

  // Cycle title messages
  let msgIdx = 0;
  const titleEl = document.getElementById("loading-title");
  const subtitleEl = document.getElementById("loading-subtitle");
  titleEl.textContent = loadingMessages[msgIdx].title;
  subtitleEl.textContent = loadingMessages[msgIdx].subtitle;
}

function activateLoadStep(idx) {
  const ids = ["ls-1","ls-2","ls-3","ls-4"];
  if (idx < ids.length) {
    document.getElementById(ids[idx]).classList.add("active");
    const msg = loadingMessages[Math.min(idx, loadingMessages.length - 1)];
    document.getElementById("loading-title").textContent = msg.title;
    document.getElementById("loading-subtitle").textContent = msg.subtitle;
  }
}

function advanceLoadStep() {
  const ids = ["ls-1","ls-2","ls-3","ls-4"];
  if (loadingStepIdx < ids.length) {
    document.getElementById(ids[loadingStepIdx]).classList.remove("active");
    document.getElementById(ids[loadingStepIdx]).classList.add("done");
    loadingStepIdx++;
    if (loadingStepIdx < ids.length) {
      activateLoadStep(loadingStepIdx);
    }
  }
}

function hideLoading() {
  clearInterval(loadingInterval);
  const overlay = document.getElementById("loading-overlay");
  overlay.style.opacity = "0";
  overlay.style.transition = "0.4s ease";
  setTimeout(() => {
    overlay.classList.add("hidden");
    overlay.style.opacity = "";
    overlay.style.transition = "";
  }, 400);
}

// ── Toast ──────────────────────────────────────────────────────────────────
let toastTimeout = null;
function showToast(msg, type = "success") {
  const toast = document.getElementById("toast");
  toast.textContent = msg;
  toast.className = `toast ${type === "error" ? "error" : ""}`;
  void toast.offsetWidth; // reflow
  toast.classList.add("show");
  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.remove("show");
  }, 3500);
}

// ── Utilities ─────────────────────────────────────────────────────────────
function escapeHtml(str) {
  const d = document.createElement("div");
  d.textContent = str;
  return d.innerHTML;
}
