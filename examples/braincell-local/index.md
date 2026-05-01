---
layout: null
title: BrainCell Lite — Persistent Memory for GitHub Copilot
description: Zero-dependency persistent memory for GitHub Copilot. No server, no database — just local JSON files in your repo.
permalink: /
---
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{{ page.title }}</title>
  <meta name="description" content="{{ page.description }}" />
  <meta property="og:title" content="{{ page.title }}" />
  <meta property="og:description" content="{{ page.description }}" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{{ site.url }}{{ site.baseurl }}/" />
  <link rel="canonical" href="{{ site.url }}{{ site.baseurl }}/" />
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:         #0d1117;
      --surface:    #161b22;
      --border:     #30363d;
      --accent:     #3fb950;
      --accent-dim: #1e4620;
      --accent2:    #58a6ff;
      --accent2-dim:#0d2035;
      --text:       #e6edf3;
      --muted:      #8b949e;
      --code-bg:    #1f2428;
      --tag-bg:     #21262d;
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      line-height: 1.6;
      min-height: 100vh;
    }

    /* NAV */
    nav {
      border-bottom: 1px solid var(--border);
      padding: 0 calc(50% - 480px);
      height: 56px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      position: sticky;
      top: 0;
      background: var(--bg);
      z-index: 10;
    }
    .nav-brand {
      font-size: 1rem;
      font-weight: 600;
      letter-spacing: .02em;
      display: flex;
      align-items: center;
      gap: .5rem;
      text-decoration: none;
      color: var(--text);
    }
    .nav-brand .dot { width: 8px; height: 8px; background: var(--accent); border-radius: 50%; }
    .nav-links a {
      color: var(--muted);
      text-decoration: none;
      font-size: .875rem;
      margin-left: 1.5rem;
    }
    .nav-links a:hover { color: var(--text); }

    /* HERO */
    .hero {
      max-width: 960px;
      margin: 0 auto;
      padding: 80px 2rem 60px;
      text-align: center;
    }
    .badge {
      display: inline-block;
      background: var(--accent-dim);
      color: var(--accent);
      font-size: .75rem;
      font-weight: 600;
      letter-spacing: .08em;
      text-transform: uppercase;
      padding: .25rem .75rem;
      border-radius: 2rem;
      margin-bottom: 1.5rem;
      border: 1px solid var(--accent);
    }
    .hero h1 {
      font-size: clamp(2rem, 5vw, 3rem);
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: 1rem;
    }
    .hero h1 span { color: var(--accent); }
    .hero p {
      font-size: 1.125rem;
      color: var(--muted);
      max-width: 680px;
      margin: 0 auto 2rem;
    }
    .hero-actions {
      display: flex;
      gap: 1rem;
      justify-content: center;
      flex-wrap: wrap;
    }
    .btn {
      display: inline-flex;
      align-items: center;
      gap: .4rem;
      padding: .625rem 1.25rem;
      border-radius: 6px;
      font-size: .9375rem;
      font-weight: 500;
      text-decoration: none;
      cursor: pointer;
      border: none;
      transition: opacity .15s;
    }
    .btn:hover { opacity: .85; }
    .btn-primary  { background: var(--accent);  color: #000; }
    .btn-secondary { background: var(--surface); color: var(--text); border: 1px solid var(--border); }

    /* PILL ROW */
    .pill-row {
      display: flex;
      gap: .625rem;
      justify-content: center;
      flex-wrap: wrap;
      margin-top: 2.5rem;
    }
    .pill {
      background: var(--tag-bg);
      border: 1px solid var(--border);
      border-radius: 2rem;
      padding: .25rem .875rem;
      font-size: .8125rem;
      color: var(--muted);
    }
    .pill strong { color: var(--text); }

    /* SECTIONS */
    section {
      max-width: 960px;
      margin: 0 auto;
      padding: 0 2rem 64px;
    }
    h2 {
      font-size: 1.375rem;
      font-weight: 600;
      margin-bottom: 1.5rem;
      padding-bottom: .5rem;
      border-bottom: 1px solid var(--border);
    }

    /* HOW IT WORKS */
    .how-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
      align-items: stretch;
    }
    .how-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
    }
    .how-card p { flex: 1; }
    .how-card .step-num {
      font-size: .75rem;
      font-weight: 700;
      color: var(--accent);
      letter-spacing: .1em;
      text-transform: uppercase;
      margin-bottom: .5rem;
    }
    .how-card h3 { font-size: 1rem; font-weight: 600; margin-bottom: .35rem; }
    .how-card p  { font-size: .875rem; color: var(--muted); }

    /* INSTALL STEPS */
    .steps { display: flex; flex-direction: column; gap: 2rem; }
    .step  { display: flex; flex-direction: column; gap: .75rem; }
    .step-header { display: flex; align-items: center; gap: 1rem; }
    .step-circle {
      width: 2rem; height: 2rem;
      border-radius: 50%;
      background: var(--accent-dim);
      border: 1px solid var(--accent);
      color: var(--accent);
      font-size: .8125rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .step-header h3 { font-size: .9375rem; font-weight: 600; margin: 0; }
    .step-body p { font-size: .875rem; color: var(--muted); margin-bottom: .75rem; }

    /* CALLOUT */
    .callout {
      background: var(--accent2-dim);
      border: 1px solid var(--accent2);
      border-radius: 8px;
      padding: 1rem 1.25rem;
      font-size: .875rem;
      color: var(--muted);
      margin-top: .75rem;
    }
    .callout strong { color: var(--accent2); }

    /* CODE BLOCKS */
    .code-block {
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
    }
    .code-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: .5rem 1rem;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
    }
    .code-label { font-size: .75rem; color: var(--muted); font-family: monospace; }
    .copy-btn {
      background: none;
      border: 1px solid var(--border);
      color: var(--muted);
      font-size: .75rem;
      padding: .15rem .5rem;
      border-radius: 4px;
      cursor: pointer;
      font-family: monospace;
    }
    .copy-btn:hover  { color: var(--text); border-color: var(--muted); }
    .copy-btn.copied { color: var(--accent); border-color: var(--accent); }
    pre {
      padding: 1rem;
      overflow-x: auto;
      font-size: .8125rem;
      line-height: 1.7;
      font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
    }
    code { font-family: inherit; }
    .hl  { color: var(--accent); }
    .hl2 { color: var(--accent2); }
    .note { color: var(--accent); }

    /* FILE TREE */
    .file-tree {
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 1rem 1.25rem;
      font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
      font-size: .8125rem;
      line-height: 1.8;
    }
    .file-tree .dir  { color: var(--text); }
    .file-tree .file { color: var(--muted); }

    /* REQUIREMENTS */
    .req-list { display: flex; flex-direction: column; gap: .625rem; }
    .req-item {
      display: flex;
      align-items: center;
      gap: .75rem;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: .75rem 1rem;
      font-size: .9375rem;
    }
    .req-item .check { color: var(--accent); font-weight: 700; flex-shrink: 0; }
    .req-item .req-sub { font-size: .8rem; color: var(--muted); display: block; }

    /* TOPIC GRID */
    .topic-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: .75rem;
    }
    .topic-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: .875rem 1rem;
      display: flex;
      flex-direction: column;
      gap: .25rem;
    }
    .topic-card .topic-file {
      font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
      font-size: .75rem;
      color: var(--accent);
    }
    .topic-card .topic-label { font-size: .875rem; font-weight: 600; }
    .topic-card .topic-desc  { font-size: .8125rem; color: var(--muted); }

    /* EXAMPLE ENTRY */
    .example-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
    }
    .example-label { font-size: .75rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: .06em; margin-bottom: .5rem; }

    /* PRIVACY */
    .privacy-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
    }
    .privacy-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 1rem 1.25rem;
    }
    .privacy-card h3 { font-size: .9375rem; font-weight: 600; margin-bottom: .35rem; }
    .privacy-card p  { font-size: .8125rem; color: var(--muted); }

    /* FOOTER */
    footer {
      border-top: 1px solid var(--border);
      padding: 2rem;
      text-align: center;
      font-size: .8125rem;
      color: var(--muted);
    }
    footer a { color: var(--muted); text-decoration: none; }
    footer a:hover { color: var(--text); }

    @media (max-width: 1040px) { nav { padding: 0 2rem; } }
    @media (max-width: 960px) {
      .topic-grid    { grid-template-columns: repeat(2, 1fr); }
      .how-grid      { grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); }
      .example-grid  { grid-template-columns: 1fr; }
      .privacy-grid  { grid-template-columns: 1fr; }
    }
    @media (max-width: 600px) {
      .hero { padding: 48px 1.25rem 40px; }
      section { padding: 0 1.25rem 48px; }
      nav { padding: 0 1.25rem; }
      .nav-links { display: none; }
      .topic-grid { grid-template-columns: 1fr; }
      .how-grid   { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>

<!-- NAV -->
<nav>
  <a class="nav-brand" href="#">
    <span class="dot"></span>
    BrainCell Lite
  </a>
  <div class="nav-links">
    <a href="#how">How it works</a>
    <a href="#install">Install</a>
    <a href="#topics">Memory topics</a>
    <a href="https://github.com/ITlusions/ITL.BrainCell" target="_blank">GitHub ↗</a>
  </div>
</nav>

<!-- HERO -->
<div class="hero">
  <div class="badge">Open Source · MIT License</div>
  <h1>Persistent memory for<br><span>GitHub Copilot</span></h1>
  <p>BrainCell Lite gives Copilot a persistent memory across sessions — stored as plain JSON files in your repo. No server, no database, no account required.</p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="#install">Install in 30 seconds</a>
    <a class="btn btn-secondary" href="https://github.com/ITlusions/ITL.BrainCell" target="_blank">View on GitHub</a>
  </div>
  <div class="pill-row">
    <span class="pill"><strong>Zero</strong> dependencies</span>
    <span class="pill"><strong>Local</strong> JSON files</span>
    <span class="pill"><strong>Version</strong> controlled</span>
    <span class="pill"><strong>Works</strong> with any repo</span>
    <span class="pill"><strong>SessionStart</strong> hook support</span>
  </div>
</div>

<!-- HOW IT WORKS -->
<section id="how">
  <h2>How it works</h2>
  <div class="how-grid">
    <div class="how-card">
      <div class="step-num">Session start</div>
      <h3>Memory is loaded automatically</h3>
      <p>The SessionStart hook reads all <code style="color:var(--accent);font-size:.8rem">braincell-lite-*.json</code> files and injects them as context before you type your first message.</p>
    </div>
    <div class="how-card">
      <div class="step-num">During session</div>
      <h3>Copilot saves what matters</h3>
      <p>Decisions, tasks, errors, and patterns are saved to topic-scoped JSON files. Each file is a simple, readable array of entries.</p>
    </div>
    <div class="how-card">
      <div class="step-num">Next session</div>
      <h3>Context carries over</h3>
      <p>Everything saved in previous sessions is available immediately — commit the <code style="color:var(--accent2);font-size:.8rem">.braincell/</code> folder to share memory across machines and team members.</p>
    </div>
  </div>
</section>

<!-- REQUIREMENTS -->
<section id="requirements">
  <h2>Requirements</h2>
  <div class="req-list">
    <div class="req-item">
      <span class="check">✓</span>
      <div>
        <strong>GitHub Copilot</strong>
        <span class="req-sub">Any plan — Free, Pro, or Business</span>
      </div>
    </div>
    <div class="req-item">
      <span class="check">✓</span>
      <div>
        <strong>VS Code with GitHub Copilot extension</strong>
        <span class="req-sub">v1.90 or later recommended for SessionStart hook support</span>
      </div>
    </div>
    <div class="req-item">
      <span class="check">✓</span>
      <div>
        <strong>PowerShell 5.1+</strong>
        <span class="req-sub">For the installer and SessionStart hook script — pre-installed on Windows; available on Linux/macOS</span>
      </div>
    </div>
    <div class="req-item">
      <span class="check">✓</span>
      <div>
        <strong>A local Git repository</strong>
        <span class="req-sub">The <code style="font-size:.85em">.braincell/</code> folder is committed and version-controlled alongside your code</span>
      </div>
    </div>
  </div>
</section>

<!-- INSTALL -->
<section id="install">
  <h2>Install</h2>
  <div class="steps">

    <div class="step">
      <div class="step-header">
        <div class="step-circle">1</div>
        <h3>Run the installer from your repo root</h3>
      </div>
      <div class="step-body">
        <p>Open a terminal in your repository root and run one of the following commands.</p>

        <p><strong>Option A — directly from GitHub (recommended):</strong></p>
        <div class="code-block">
          <div class="code-header">
            <span class="code-label">powershell</span>
            <button class="copy-btn" onclick="copyCode(this)">copy</button>
          </div>
          <pre><code><span class="hl">irm</span> https://raw.githubusercontent.com/ITlusions/ITL.BrainCell/main/examples/braincell-local/install-braincell-lite.ps1 <span class="hl">|</span> <span class="hl">iex</span></code></pre>
        </div>

        <p style="margin-top:.875rem"><strong>Option B — download and run locally:</strong></p>
        <div class="code-block">
          <div class="code-header">
            <span class="code-label">powershell</span>
            <button class="copy-btn" onclick="copyCode(this)">copy</button>
          </div>
          <pre><code><span class="hl">.\install-braincell-lite.ps1</span></code></pre>
        </div>

        <div class="callout" style="margin-top:.875rem">
          <strong>Available options:</strong>
          <table style="margin-top:.625rem;border:none;font-size:.8125rem">
            <tr style="border:none">
              <td style="border:none;padding:.2rem .75rem .2rem 0;vertical-align:top"><code style="color:var(--accent2);background:var(--tag-bg);padding:.1rem .4rem;border-radius:4px">-TargetPath &lt;path&gt;</code></td>
              <td style="border:none;padding:.2rem 0;color:var(--muted)">Install into a different repo (default: current directory)</td>
            </tr>
            <tr style="border:none">
              <td style="border:none;padding:.2rem .75rem .2rem 0;vertical-align:top"><code style="color:var(--accent2);background:var(--tag-bg);padding:.1rem .4rem;border-radius:4px">-SkipCommit</code></td>
              <td style="border:none;padding:.2rem 0;color:var(--muted)">Skip the git commit prompt at the end</td>
            </tr>
            <tr style="border:none">
              <td style="border:none;padding:.2rem .75rem .2rem 0;vertical-align:top"><code style="color:var(--accent2);background:var(--tag-bg);padding:.1rem .4rem;border-radius:4px">-Force</code></td>
              <td style="border:none;padding:.2rem 0;color:var(--muted)">Overwrite existing <code>.braincell</code> files without asking</td>
            </tr>
          </table>
        </div>
      </div>
    </div>

    <div class="step">
      <div class="step-header">
        <div class="step-circle">2</div>
        <h3>Answer the commit prompt — you are done</h3>
      </div>
      <div class="step-body">
        <p>The installer creates all required files and offers to commit them. After committing, open a new Copilot Chat — memory is active immediately.</p>
        <p>After installation your repo will contain:</p>
        <div class="file-tree">
          <div class="dir">your-repo/</div>
          <div class="file">&nbsp;&nbsp;├── .braincell/</div>
          <div class="file">&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <span class="hl">SKILL.md</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="note">← full memory skill</span></div>
          <div class="file">&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;├── <span class="hl">braincell-lite-index.json</span>&nbsp;<span class="note">← fast-search index</span></div>
          <div class="file">&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── <span class="hl">braincell-lite-notes.json</span>&nbsp;<span class="note">← initial memory store</span></div>
          <div class="file">&nbsp;&nbsp;└── .github/</div>
          <div class="file">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── <span class="hl2">copilot-instructions.md</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="note">← activation hook</span></div>
          <div class="file">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── hooks/</div>
          <div class="file">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;└── <span class="hl2">braincell-hooks.json</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span class="note">← SessionStart config</span></div>
          <div class="file">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── scripts/</div>
          <div class="file">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── <span class="hl2">braincell-session-start.ps1</span>&nbsp;<span class="note">← loads memory at startup</span></div>
        </div>
      </div>
    </div>

  </div>
</section>

<!-- MEMORY TOPICS -->
<section id="topics">
  <h2>Memory topics</h2>
  <p style="color:var(--muted);font-size:.9rem;margin-bottom:1.25rem">Each topic is a separate JSON file. New topic files are created automatically when needed. Custom topics are allowed.</p>
  <div class="topic-grid">
    <div class="topic-card">
      <span class="topic-file">braincell-lite-notes.json</span>
      <span class="topic-label">Notes</span>
      <span class="topic-desc">General context, session summaries, diagrams</span>
    </div>
    <div class="topic-card">
      <span class="topic-file">braincell-lite-decisions.json</span>
      <span class="topic-label">Decisions</span>
      <span class="topic-desc">Architecture and approach decisions made during sessions</span>
    </div>
    <div class="topic-card">
      <span class="topic-file">braincell-lite-tasks.json</span>
      <span class="topic-label">Tasks</span>
      <span class="topic-desc">Open, done, and blocked work items</span>
    </div>
    <div class="topic-card">
      <span class="topic-file">braincell-lite-errors.json</span>
      <span class="topic-label">Errors</span>
      <span class="topic-desc">Bugs found and fixed — includes the solution</span>
    </div>
    <div class="topic-card">
      <span class="topic-file">braincell-lite-patterns.json</span>
      <span class="topic-label">Patterns</span>
      <span class="topic-desc">Working commands and reusable code solutions</span>
    </div>
    <div class="topic-card">
      <span class="topic-file">braincell-lite-facts.json</span>
      <span class="topic-label">Facts</span>
      <span class="topic-desc">Project metadata, versions, key URLs</span>
    </div>
    <div class="topic-card">
      <span class="topic-file">braincell-lite-preferences.json</span>
      <span class="topic-label">Preferences</span>
      <span class="topic-desc">Style rules, constraints, coding conventions</span>
    </div>
    <div class="topic-card">
      <span class="topic-file">braincell-lite-[custom].json</span>
      <span class="topic-label">Custom</span>
      <span class="topic-desc">Any domain-specific topic — auth, api, infra, etc.</span>
    </div>
  </div>
</section>

<!-- EXAMPLE ENTRY -->
<section id="example">
  <h2>Example memory entry</h2>
  <div class="example-grid">
    <div>
      <div class="example-label">Stored in braincell-lite-decisions.json</div>
      <div class="code-block">
        <div class="code-header"><span class="code-label">json</span></div>
        <pre><code>{
  <span class="hl2">"id"</span>:      <span class="hl">"20260427-143200-decision"</span>,
  <span class="hl2">"type"</span>:    <span class="hl">"decision"</span>,
  <span class="hl2">"title"</span>:   <span class="hl">"Use PostgreSQL over SQLite"</span>,
  <span class="hl2">"content"</span>: <span class="hl">"Chose PostgreSQL for multi-user support..."</span>,
  <span class="hl2">"tags"</span>:    [<span class="hl">"database"</span>, <span class="hl">"architecture"</span>],
  <span class="hl2">"created"</span>: <span class="hl">"2026-04-27T14:32:00Z"</span>,
  <span class="hl2">"updated"</span>: <span class="hl">"2026-04-27T14:32:00Z"</span>
}</code></pre>
      </div>
    </div>
    <div>
      <div class="example-label">Matching entry in braincell-lite-index.json</div>
      <div class="code-block">
        <div class="code-header"><span class="code-label">json</span></div>
        <pre><code>{
  <span class="hl2">"id"</span>:      <span class="hl">"20260427-143200-decision"</span>,
  <span class="hl2">"type"</span>:    <span class="hl">"decision"</span>,
  <span class="hl2">"title"</span>:   <span class="hl">"Use PostgreSQL over SQLite"</span>,
  <span class="hl2">"tags"</span>:    [<span class="hl">"database"</span>, <span class="hl">"architecture"</span>],
  <span class="hl2">"file"</span>:    <span class="hl">"braincell-lite-decisions.json"</span>,
  <span class="hl2">"updated"</span>: <span class="hl">"2026-04-27T14:32:00Z"</span>
}</code></pre>
      </div>
    </div>
  </div>
</section>

<!-- PRIVACY -->
<section id="privacy">
  <h2>Privacy</h2>
  <div class="privacy-grid">
    <div class="privacy-card">
      <h3>Stays on your machine</h3>
      <p>All memory files are plain JSON in your repo. Nothing is sent to any external service.</p>
    </div>
    <div class="privacy-card">
      <h3>You control what is saved</h3>
      <p>Copilot only saves entries when instructed. Sensitive entries can be <code style="font-size:.85em">.gitignore</code>'d.</p>
    </div>
    <div class="privacy-card">
      <h3>No account or API key</h3>
      <p>BrainCell Lite has zero external dependencies. There is no backend, no telemetry, and no registration.</p>
    </div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <p>
    BrainCell Lite is part of the
    <a href="https://github.com/ITlusions/ITL.BrainCell" target="_blank">ITL BrainCell</a>
    platform by <a href="https://github.com/ITlusions" target="_blank">ITlusions</a>.
    MIT License.
  </p>
  <p style="margin-top:.5rem">
    <a href="https://github.com/ITlusions/ITL.BrainCell" target="_blank">GitHub</a> ·
    <a href="https://github.com/ITlusions/ITL.BrainCell/issues" target="_blank">Issues</a> ·
    <a href="https://github.com/ITlusions/ITL.BrainCell/blob/main/examples/braincell-local/README.md" target="_blank">Docs</a>
  </p>
</footer>

<script>
  function copyCode(btn) {
    const code = btn.closest('.code-block').querySelector('pre code');
    const text = code ? code.innerText : '';
    if (!navigator.clipboard) return;
    navigator.clipboard.writeText(text).then(function() {
      btn.textContent = 'copied!';
      btn.classList.add('copied');
      setTimeout(function() {
        btn.textContent = 'copy';
        btn.classList.remove('copied');
      }, 2000);
    });
  }
</script>
</body>
</html>
