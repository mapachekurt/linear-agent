# Linear Product Management Agent – Specification

Version: 0.3  
Owner: Kurt / Mapache  
Runtime: Vertex AI Agent Builder (ADK) on Vertex AI Agent Engine  
Primary Integrations: Linear MCP & API, GitHub MCP & API, Slack bot  
Ecosystem: All Google Cloud + GitHub

---

## 1. Purpose

The **Linear Product Management Agent** (“Linear Agent”) is the product/backlog brain for Mapache.

It:

- Keeps Linear projects/issues **lean and up to date** (no code-level bloat).
- Reflects the **Mapache business model**:
  - `mapache.solutions` = GUI-first, AI-native micro-SaaS apps.
  - `mapache.app` = conversational OS that reuses those GUIs via **MCP-GUI**.
- Orchestrates **execution routing** to GitHub Copilot (agent vs chat).
- Acts as the glue between:
  - You (Kurt) in Slack.
  - Opportunity Agent (idea generator).
  - Linear (backlog).
  - GitHub + Copilot (implementation).

The agent does **not** write code itself; it shapes work and routes it to the right coding tools.

---

## 2. Business context: Mapache.solutions & Mapache.app

### 2.1 mapache.solutions

- Traditional web apps with:
  - A clear GUI (forms, tables, dashboards).
  - AI baked in from day one (not an add-on).
- Most apps are **spawned by the Opportunity Agent** as experiments:
  - Validate specific pain points.
  - Explore workflows.
  - Acquire users.
- These apps are **not the final destination**; they are:
  - Proving grounds.
  - Sources of **re-usable GUI flows** for mapache.app.

### 2.2 mapache.app

- The **conversational business OS** for SMBs.
- Core surface:
  - Chat interface.
  - In-line GUI/CRUD panels rendered via **MCP-GUI**.
- Many GUI flows originate from mapache.solutions:
  - Screens are **mirrored / repurposed** into mapache.app as MCP-GUI components.
  - Over time, the OS hosts the “canonical” version of a workflow.

### 2.3 What the agent must internalize

The Linear Agent must:

- Recognize when work:
  - Creates or evolves a `.solutions` app.
  - Extracts / repurposes `.solutions` GUIs into `.app` via MCP-GUI.
  - Only maintains a legacy `.solutions` artifact that should probably be pruned.
- Prefer projects that:
  - Turn validated `.solutions` flows into **first-class `.app` experiences**.
  - De-duplicate or retire obsolete `.solutions` projects.

---

## 3. Scope & non-goals

### In scope

- **Backlog shaping** in Linear:
  - Classify issues/projects by source and product surface.
  - Convert bloated tickets into **Lean tickets**.
  - Kill/park low-value or obsolete work.
- **Prioritization**:
  - Favor work that moves users & workflows **into mapache.app**.
  - Down-rank noise and stale experiments.
- **Execution routing**:
  - Decide between:
    - GitHub Copilot **coding agent / Agent Mode** (large work).
    - GitHub Copilot **chat** (small/medium work).
    - Kurt/manual (strategy/ambiguity).
- **Two inflows of ideas**:
  - Direct Kurt ideas (Slack / manual Linear issues).
  - Opportunity Agent-created tickets.
- **Self-improvement loop**:
  - Log misclassifications / failures into a dedicated “Linear Agent – Improvements” project.

### Out of scope

- Running CI/CD, infra, or deployments.
- Being a generic product strategist for unrelated products.
- Directly handling user/customer messages (that’s for mapache.app).

---

## 4. Operating environment

- **Cloud**: 100% Google Cloud (GCP).
- **Agent framework**: Google **Agent Development Kit (ADK)**, deployed to **Vertex AI Agent Engine**.
- **Code hosting & dev**: GitHub + GitHub Copilot (chat, coding agent, code review).
- **Backlog**: Linear.
- **Conversation surface**: Slack + custom Slack bot (Kurt proxy).

The Linear Agent is an ADK agent with tools for:

- Calling **Linear MCP**.
- Calling **Linear REST API** (for webhooks & gaps).
- Calling **GitHub MCP** (Copilot agents).
- Calling **GitHub REST/GraphQL** (metadata/PR links).

---

## 5. Workflows and actors

### 5.1 Actors

- **Kurt** – human owner, works mainly in Slack + Linear + GitHub.
- **Opportunity Agent** – ADK agent that proposes new opportunities/tiny SaaS ideas.
- **Linear Agent (this spec)** – ADK agent that:
  - Shapes the backlog.
  - Routes work.
- **GitHub Copilot** – coding agents / chat inside GitHub.
- **Slack Bot** – front-end for Kurt; calls the Linear Agent via HTTP/A2A.

### 5.2 Main flows

1. **Kurt creates idea in Linear or via Slack**
   - Ticket enters Linear as `status:candidate`, `source:user`.
   - Linear Agent triages & shapes.

2. **Opportunity Agent proposes opportunity**
   - Creates issue/project in Linear with `source:opportunity-agent`.
   - Linear Agent validates, shapes, and prioritizes.

3. **Backlog shaping**
   - Linear Agent periodically (or via webhook) scans:
     - New/changed issues.
     - New projects.
   - Cleans descriptions, classifies, sets size & route.

4. **Execution**
   - For `route:copilot-agent`:
     - Linear Agent prepares a **Copilot brief** and issues a task to GitHub via MCP.
   - For `route:copilot-chat`:
     - Linear Agent prepares a **prompt snippet** for Kurt/Copilot chat.
   - For `route:manual`:
     - Linear Agent flags it for Kurt’s decision.

5. **Slack collaboration**
   - Kurt uses slash commands or mentions (via Slack bot) to:
     - Ask for triage/suggestions.
     - Ask “what should I do next?”
     - Inspect why something was prioritized.

---

## 6. Data model (labels, fields, statuses)

Implementation detail: strings are **configurable** (via config file/env), not hard-coded.

### 6.1 Source

- `source:user` – Kurt created manually.
- `source:opportunity-agent` – created by Opportunity Agent.
- (Optional) `source:system-migration` – for bulk/legacy imports.

### 6.2 Surface / product

- `surface:solutions` – work primarily about mapache.solutions web apps.
- `surface:app` – work primarily about mapache.app OS.
- `surface:bridge` – work explicitly about moving flows from `.solutions` → `.app` (MCP-GUI, shared data models, etc).

One ticket can carry multiple surface tags if appropriate.

### 6.3 Size

Rough, used only for routing:

- `size:small`
- `size:medium`
- `size:large`

### 6.4 Routing

- `route:copilot-agent`
- `route:copilot-chat`
- `route:manual`

### 6.5 Status / lifecycle

Map these to either Linear workflow states or labels:

- `status:candidate` – new, needs triage.
- `status:shaped` – Lean format, clear outcome.
- `status:ready` – ready for execution (has route).
- `status:parked` – later / maybe never.
- `status:discarded` – intentionally dropped.

---

## 7. Lean ticket format

The agent should converge issue descriptions into a **standard Lean format**:

1. **Problem**  
   - Short, user-centered description.
2. **Desired Outcome**  
   - What changes in the user/system behavior when done.
3. **Product Surface**  
   - `mapache.solutions` / `mapache.app` / `bridge`.
4. **Context & Constraints**  
   - Links to repos, files, diagrams.
   - Hard constraints (don’t break X, must reuse Y).
   - No inline code unless absolutely necessary.
5. **Execution Route Hint**  
   - One of `copilot-agent`, `copilot-chat`, `manual`, with a one-line rationale.

The agent should strip or demote:

- Implementation details like “in file X, rename function Y to Z”.
- Large code blobs that will be stale quickly.

---

## 8. Core behaviors

### 8.1 Intake & triage

**Triggered by:**

- Linear webhooks (issue created/updated/project updated).
- Manual calls (Slack command, scheduled sweeps).

**Steps:**

1. **Fetch candidates**  
   - Issues with `status:candidate` or equivalent state.
2. **Relevance check**  
   - Is this clearly about Mapache? If not:
     - Move to `status:discarded` or a parking board.
3. **Surface classification**  
   - Decide between `surface:solutions`, `surface:app`, `surface:bridge`.
   - Use:
     - Title & description keywords.
     - Linked repos (`mapache-solutions-*` vs `mapache-app-*` etc).
4. **Leanification**  
   - Rewrite description to Lean format.
   - Remove outdated code instructions in favor of:
     - “Let Copilot plan from the current codebase.”
5. **Size estimation**  
   - Heuristic:
     - Single-file or localized → `small`.
     - Multi-component but straightforward → `medium`.
     - Cross-cutting, multiple services, or conceptual redesign → `large`.
6. **Set `status:shaped`** once Lean & classification are done.

### 8.2 Prioritization

Apply deterministic rules:

- **Bias toward bridge work**:
  - `surface:bridge` gets boosted.
  - E.g. “mirror X SaaS flow into MCP-GUI inside mapache.app”.
- Lift items that:
  - Simplify the funnel `.solutions → .app`.
  - Consolidate duplicated functionality across multiple `.solutions` apps.
- Push down:
  - Maintenance of low-signal `.solutions` experiments.
  - Purely speculative ideas with no clear user or funnel fit.

Output:

- Update Linear priority field (P1–P4 or equivalent).
- Optionally set target cycle/milestone.
- Add short “Agent rationale” comment for non-obvious changes.

### 8.3 Routing to GitHub Copilot

For issues with `status:shaped`:

1. **Decide route**:
   - `route:copilot-agent` when:
     - `size:large`, or
     - Multi-repo/multi-module work, or
     - Ideal for a long-running Copilot coding agent session.
   - `route:copilot-chat` when:
     - `size:small` or `size:medium`.
     - The work is natural to do in one or a few focused Copilot Chat sessions.
   - `route:manual` when:
     - Strategy/architecture decisions.
     - Ambiguous scope or conflicting constraints.

2. **For `route:copilot-agent`:**
   - Prepare a **machine-readable brief**:
     - Problem, outcome, constraints, repos.
     - Suggested steps at a high level.
   - Use **GitHub MCP** tool(s) to:
     - Start a Copilot coding agent/Agent Mode session with that brief.
     - Optionally create or update a GitHub issue linked to the Linear issue.
   - Store references (session ID / PR links) as:
     - Linear comments and/or custom fields.

3. **For `route:copilot-chat`:**
   - Prepare a **prompt snippet** for Kurt to paste into Copilot Chat:
     - Include: context, problem, constraints, acceptance criteria.
   - Attach this snippet to the Linear issue (comment or description section).

### 8.4 Slack interactions (via Slack bot)

The Linear Agent exposes capabilities that the Slack bot calls over HTTP/A2A. Examples:

- `/linear-agent triage`  
  - Triage all `status:candidate` issues in selected project.
- `/linear-agent next`  
  - Return the top N recommended issues to work on now (with route & rationale).
- `/linear-agent inspect <issue-key>`  
  - Summarize the issue, surfaces, size, route, and rationale.
- `/linear-agent clean-project <project-key>`  
  - Run Leanification + prioritization for everything in a project.

The agent itself does **not** handle Slack APIs; it only exposes methods the bot can call.

### 8.5 Self-improvement

On any failure or misbehavior:

- Log an issue in a special Linear project, e.g. `Linear Agent – Improvements`:
  - What input it saw.
  - What decision it made.
  - Why it believes this was wrong (if detectable).
  - Suggested rule adjustment.
- For severe failures (e.g., misrouting a huge refactor to `copilot-chat`):
  - Notify Kurt via a Slack-facing method so the bot can surface it.

---

## 9. Integration specifics (for implementers)

### 9.1 Linear MCP

- Use the official **Linear MCP server** as a remote tool.
- Wrap MCP calls behind an interface:

  - `list_candidates()`
  - `get_issue(issue_id)`
  - `update_issue(issue_id, fields)`
  - `comment_issue(issue_id, body)`
  - `list_projects()`
  - `update_project(project_id, fields)`

### 9.2 Linear REST API + webhooks

- Use webhooks to trigger the agent on:
  - `issue.created`
  - `issue.updated`
  - `project.updated` (if available)
- REST is fallback when MCP doesn’t cover some operation:
  - E.g., certain project metadata, advanced filters.

### 9.3 GitHub MCP

- Treat GitHub MCP as the interface to:
  - Start/monitor Copilot coding agent sessions.
  - Possibly request code analysis/summarization.

### 9.4 GitHub REST/GraphQL

- Used for:
  - Repo discovery (which repo is associated with which issue).
  - Linking Linear issues to GitHub issues/PRs.
  - Reading labels/branches when helpful.

---

## 10. Implementation notes (for ADK / repo structure)

**Language:** Python with Google ADK.

Suggested repo structure (under this GitHub repo):

- `agents/linear_agent/`
  - `app.py` – ADK app / entrypoint for Vertex AI Agent Engine.
  - `core.py` – pure logic:
    - classification
    - Leanification
    - prioritization
    - routing
  - `linear_client.py` – MCP + REST wrapper.
  - `github_client.py` – MCP + REST wrapper.
  - `models.py` – dataclasses for tickets, routes, surfaces.
  - `config.py` – labels/status mappings, env vars.
- `tests/test_core.py` – unit tests for:
  - Bloated issue cleanup.
  - Large cross-cutting refactor → `route:copilot-agent`.
  - Opportunity Agent suggestion → prioritized correctly.
  - Irrelevant/low-value idea → `status:discarded`/parked.

Constraints:

- **No secrets** in code; use environment variables or GCP Secret Manager.
- All label names, project IDs, states must come from `config.py`.
- Logging must be structured and compatible with Vertex logging/monitoring.

---

## 11. Example scenarios (for tests)

1. **Bloated `.solutions` ticket**  
   - Description full of implementation notes & stale code paths.  
   - Expected:
     - Converted to Lean format.
     - `surface:solutions`.
     - `size:medium`.
     - `route:copilot-chat`.

2. **Bridge project (promote GUI to MCP-GUI)**  
   - “Mirror the customer onboarding flow from X solutions app into mapache.app via MCP-GUI.”  
   - Expected:
     - `surface:bridge` (+ `surface:solutions` + `surface:app`).
     - Higher priority.
     - `size:large`.
     - `route:copilot-agent`.
     - Prepared Copilot brief referencing relevant repos.

3. **High-signal Opportunity Agent idea**  
   - New issue with `source:opportunity-agent`, describing a clear pain that fits Mapache’s OS vision.  
   - Expected:
     - Classified to correct surface.
     - Leanified + `status:shaped`.
     - Priority boosted vs generic ideas.

4. **Low-signal or off-topic idea**  
   - “Random experiment” not tied to `.solutions` or `.app`.  
   - Expected:
     - Marked `status:discarded` or moved to parking.
     - Short comment explaining why.

5. **Misrouted large work** (for self-improvement)  
   - Test that when a large, cross-cutting refactor is accidentally given `route:copilot-chat`, a correction path exists and a self-improvement ticket is logged.

---
