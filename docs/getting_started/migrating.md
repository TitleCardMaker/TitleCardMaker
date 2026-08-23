---
title: Migration Guide
description: >
    Migrate to the TitleCardMaker Web UI.
---


# Migrating Guide

The following interactive migration guide will help you migrate into using
TitleCardMaker version 2.

<div id="migration-flowchart" class="fc-widget"></div>

<style>
/* ---- Color tokens: light by default, dark via OS pref or MkDocs Material's
   slate scheme (html[data-md-color-scheme="slate"]) --------------------- */
.fc-widget {
  --fc-bg: #ffffff;
  --fc-bg-subtle: #f6f8fb;
  --fc-border: #e2e5ea;
  --fc-text: #1a1d23;
  --fc-text-muted: #6b7280;
  --fc-accent: #6366f1;
  --fc-accent-text: #ffffff;
  --fc-result-bg: #ecfdf5;
  --fc-result-border: #10b981;
  --fc-result-text: #065f46;
  --fc-shadow: 0 1px 3px rgba(16, 24, 40, 0.06), 0 1px 2px rgba(16, 24, 40, 0.04);
}
@media (prefers-color-scheme: dark) {
  .fc-widget {
    --fc-bg: #1e2129;
    --fc-bg-subtle: #262a34;
    --fc-border: #363b47;
    --fc-text: #e8e9ec;
    --fc-text-muted: #9aa0ac;
    --fc-accent: #818cf8;
    --fc-accent-text: #14161b;
    --fc-result-bg: #0f2e24;
    --fc-result-border: #34d399;
    --fc-result-text: #a7f3d0;
    --fc-shadow: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.24);
  }
}
html[data-md-color-scheme="slate"] .fc-widget {
  --fc-bg: #1e2129;
  --fc-bg-subtle: #262a34;
  --fc-border: #363b47;
  --fc-text: #e8e9ec;
  --fc-text-muted: #9aa0ac;
  --fc-accent: #818cf8;
  --fc-accent-text: #14161b;
  --fc-result-bg: #0f2e24;
  --fc-result-border: #34d399;
  --fc-result-text: #a7f3d0;
  --fc-shadow: 0 1px 3px rgba(0, 0, 0, 0.3), 0 1px 2px rgba(0, 0, 0, 0.24);
}

.fc-widget {
  max-width: 560px;
  font-family: inherit;
  background: var(--fc-bg);
  border: 1px solid var(--fc-border);
  border-radius: 14px;
  padding: 22px 22px 18px;
  margin: 1.5em 0;
  box-shadow: var(--fc-shadow);
  color: var(--fc-text);
  transition: background 0.2s ease, border-color 0.2s ease;
}
.fc-trail {
  display: flex; flex-wrap: wrap; gap: 6px;
  font-size: 0.75em; color: var(--fc-text-muted);
  margin-bottom: 14px; min-height: 1.4em;
}
.fc-crumb {
  background: var(--fc-bg-subtle);
  border: 1px solid var(--fc-border);
  border-radius: 999px;
  padding: 3px 10px;
  white-space: nowrap;
}
.fc-question {
  font-size: 1.08em; font-weight: 600; margin-bottom: 16px;
  line-height: 1.45; letter-spacing: -0.01em;
}
.fc-result {
  font-size: 1.02em; line-height: 1.55;
  padding: 14px 16px;
  background: var(--fc-result-bg);
  border-left: 3px solid var(--fc-result-border);
  border-radius: 8px;
  color: var(--fc-result-text);
}
.fc-options { display: flex; flex-direction: column; gap: 8px; }
.fc-btn {
  display: flex; align-items: center; justify-content: space-between;
  padding: 11px 16px;
  border: 1px solid var(--fc-border);
  border-radius: 10px;
  background: var(--fc-bg-subtle);
  color: var(--fc-text);
  cursor: pointer;
  text-align: left;
  font-size: 0.95em;
  font-family: inherit;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
}
.fc-btn:hover { border-color: var(--fc-accent); background: var(--fc-bg); }
.fc-btn:active { transform: scale(0.99); }
.fc-btn .fc-chevron { color: var(--fc-text-muted); margin-left: 12px; }
.fc-btn .fc-check {
  color: var(--fc-result-border);
  margin-right: 4px;
  font-weight: 700;
  flex-shrink: 0;
}
.fc-controls { margin-top: 18px; display: flex; gap: 8px; }
.fc-controls button {
  font-size: 0.8em; padding: 6px 12px; border-radius: 8px;
  border: 1px solid var(--fc-border);
  background: transparent;
  color: var(--fc-text-muted);
  font-family: inherit;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
}
.fc-controls button:hover:not(:disabled) { color: var(--fc-text); border-color: var(--fc-accent); }
.fc-controls button:disabled { opacity: 0.35; cursor: default; }

.fc-step { animation: fc-fade 0.18s ease; }
@keyframes fc-fade {
  from { opacity: 0; transform: translateY(3px); }
  to   { opacity: 1; transform: translateY(0); }
}
</style>

<script>
(function () {
  // ---- 1. DEFINE YOUR FLOW HERE ----------------------------------------
  // Each key is a step id. A step is either:
  //   a question:  { text, options: [{ label, next }, ...] }
  //   an end node: { text, result: true }
  const FLOW = {
    start: {
      text: "Have you used TitleCardMaker before?",
      options: [
        { label: "No", next: "start_new_user" },
        { label: "Yes, Version 1 only", next: "start_v1"},
        { label: "Yes, Version 2", next: "current_sponsor"},
      ],
    },

    start_new_user: {
      text: 'Follow the <a href="../index.html">Getting Started Guide</a>.',
      result: true,
    },

    start_v1: {
      text: 'Follow the <a href="../index.html">Getting Started Guide</a> in a <b>new</b> install folder',
      options: [
        { label: "Finished", next: "copy_old_config_folder", check: true },
      ],
    },

    copy_old_config_folder: {
      text: "Move the <code>config</code> folder from your v1 install into your new install folder",
      options: [
        { label: "Finished", next: "preserve_old_configs", check: true },
      ],
    },

    preserve_old_configs: {
      text: "Do you want to preserve your existing Title Card configs? (This will take more effort)",
      options: [
        { label: "No", next: "preserve_old_configs_no" },
        { label: "Yes", next: "start_v1_preserve_st1" },
      ],
    },

    preserve_old_configs_no: {
      text: "Your setup is completed - enjoy TitleCardMaker!",
      result: true,
    },

    start_v1_preserve_st1: {
      text: "Copy your <code>preferences.yml</code> settings into the matching settings within the UI",
      options: [
        { label: "Finished", next: "start_v1_preserve_st2", check: true },
      ],
    },

    start_v1_preserve_st2: {
      text: "Sync your Series into TitleCardMaker - this may take a while depending on the size of your server",
      options: [
        { label: "Finished", next: "start_v1_preserve_st3_0", check: true },
        { label: "I did not create any Syncs", next: "start_v1_preserve_st3_1" },
      ],
    },

    start_v1_preserve_st3_0: {
      text: "Manually copy the YAML configuration for each Series into it's matching setting with in the UI.",
      result: true,
    },

    start_v1_preserve_st3_1: {
      text: "Create a Sync within the UI or manually add the Series you want to migrate.",
      options: [
        { label: "Finished", next: "start_v1_preserve_st3_0", check: true },
      ],
    },

    current_sponsor: {
      text: "Are you a current project sponsor, or have you contributed at least $15?",
      options: [
        { label: "Yes", next: "no_action" },
        { label: "No", next: "previous_sponsor" },
      ],
    },

    previous_sponsor: {
      text: "How did you install TitleCardMaker?",
      options: [
        { label: "Docker Compose", next: "prior_sponsor_docker" },
        { label: "Docker", next: "prior_sponsor_docker" },
        { label: "Non-Docker (Python)", next: "prior_sponsor_non_docker" },
        { label: "Unraid", next: "prior_sponsor_docker" },
      ],
    },

    prior_sponsor_docker: {
      text: "Change your Docker image URL from <code>ghcr.io/titlecardmaker/titlecardmaker-webui</code> to <code>ghcr.io/titlecardmaker/titlecardmaker</code>.",
      options: [
        { label: "Finished", next: "start_v1_preserve_st3_0", check: true },
      ],
    },

    prior_sponsor_docker_branch_check: {
      text: "Did you use the <code>:develop</code> Docker tag?",
      options: [
        { label: "Yes", next: "prior_sponsor_docker_branch_check_yesdevelop" },
        { label: "No", next: "prior_sponsor_docker_branch_check_nodevelop" },
      ],
    },

    prior_sponsor_docker_branch_check_yesdevelop: {
      text: "Change <code>:develop</code> in your Docker image URL to <code>:latest</code>.",
      result: true,
    },

    prior_sponsor_docker_branch_check_nodevelop: {
      text: "You do not need to take any further action.",
      result: true,
    },

    prior_sponsor_non_docker: {
      text: 'Follow the "Downloading the Code" section of the <a href="../index.html">Getting Started Guide</a> in a new directory, and then move your <code>config</code> folder over to this new directory.',
      result: true,
    },

    no_action: {
      text: "You do not need to take any action - your setup will continue to work as-is.",
      result: true,
    },

  };
  const START_STEP = "start";
  // -----------------------------------------------------------------------

  const root = document.getElementById("migration-flowchart");
  let history = [START_STEP];

  function stripHtml(html) {
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || "";
  }


  function render() {
    const stepId = history[history.length - 1];
    const step = FLOW[stepId];

    const trail = history
      .slice(0, -1)
      .map(id => `<span class="fc-crumb">${stripHtml(FLOW[id].text).slice(0, 10)}…</span>`)
      .join("");

    let html = `<div class="fc-trail">${history.length > 1 ? trail : ""}</div>`;

    if (step.result) {
      html += `<div class="fc-result">${step.text}</div>`;
    } else {
      html += `<div class="fc-question">${step.text}</div>`;
      html += `<div class="fc-options">`;
      step.options.forEach(opt => {
        html += `<button class="fc-btn" data-next="${opt.next}">
          <span class="fc-label">${opt.check ? '<span class="fc-check">✓</span>' : ''}${opt.label}</span>
          <span class="fc-chevron">›</span>
        </button>`;
      });
      html += `</div>`;
    }

    html += `<div class="fc-controls">
      <button data-action="back" ${history.length <= 1 ? "disabled" : ""}>← Back</button>
      <button data-action="restart">Restart</button>
    </div>`;

    root.innerHTML = html;

    root.querySelectorAll("[data-next]").forEach(btn => {
      btn.addEventListener("click", () => {
        history.push(btn.getAttribute("data-next"));
        render();
      });
    });
    root.querySelector('[data-action="back"]').addEventListener("click", () => {
      if (history.length > 1) { history.pop(); render(); }
    });
    root.querySelector('[data-action="restart"]').addEventListener("click", () => {
      history = [START_STEP]; render();
    });
  }

  render();
})();
</script>

Please reach out on [Discord](https://discord.gg/bJ3bHtw8wH) if you have any
issues or questions.
