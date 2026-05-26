# SMARTFLOW — Codebase Status Document

**Generated:** 2026-05-24
**Project:** SMARTFLOW — AI-Driven Agent-Based Traffic Simulation & RL Signal Optimization
**Location:** `C:\Users\jhepo\Desktop\trapik2`

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [What's Complete](#3-whats-complete)
4. [What's Partially Complete / Mock](#4-whats-partially-complete--mock)
5. [What's NOT Started / Missing](#5-whats-not-started--missing)
6. [Database Status](#6-database-status)
7. [Page-by-Page Implementation Status](#7-page-by-page-implementation-status)
8. [Measured Against SmartFlow Planning Docs](#8-measured-against-smartflow-planning-docs)
9. [Architectural Issues & Tech Debt](#9-architectural-issues--tech-debt)
10. [Recommended Next Steps](#10-recommended-next-steps)

---

## 1. Project Overview

SMARTFLOW is a local, AI-driven, agent-based traffic simulation and decision-support platform. It simulates a high-volume intersection in Tagum City, Davao del Norte, Philippines — modeling autonomous vehicles, pedestrians, and traffic signal behavior. The core research question: **can an RL-based adaptive traffic signal controller outperform fixed-time signal timing?**

The project has three planning documents:

| Document | Purpose |
|----------|---------|
| `SMARTFLOW_Project_Master_Reference.md` | Definitive project bible — objectives, architecture, agent design, RL approach |
| `SMARTFLOW_Implementation_Plan_Without_SUMO.md` | Custom Python engine strategy (no SUMO dependency), 8-phase roadmap |
| `SMARTFLOW_pages_plan.md` | Page-by-page build checklist, 15 pages, 13 DB tables, 5 build phases |

---

## 2. Technology Stack

| Layer | Technology | Status |
|-------|-----------|--------|
| Frontend Framework | Dash (Python) | ✅ Implemented |
| Visualization | Plotly | ✅ Implemented (mock data) |
| Styling | Custom CSS (dark premium theme, ~2500+ lines) | ✅ Complete |
| Database | SQLite via `sqlite3` | ✅ Full schema + CRUD |
| Authentication | Flask sessions + Werkzeug hashing | ✅ Complete |
| Icons | Font Awesome 6.5 | ✅ Complete |
| Fonts | Inter, JetBrains Mono | ✅ Complete |
| Simulation Engine | None | ❌ Not started |
| RL Library | None | ❌ Not started |
| 3D Visualization | None (Three.js planned) | ❌ Not started |

**`requirements.txt`** contains only: `dash`, `plotly`, `pandas`, `Werkzeug`. No SUMO, TraCI, PyTorch, TensorFlow, Stable-Baselines3, or any simulation/ML library.

---

## 3. What's Complete

### 3.1 Authentication & Authorization ✅

- Login with username/password (SQLite-backed)
- Password hashing via Werkzeug (`generate_password_hash` / `check_password_hash`)
- Session management with token-based expiry (1-hour timeout, extendable)
- Role-based access control: `admin`, `researcher`, `researcher_pending`, `disabled`
- Permission matrix with `page:action` granularity (`auth.has_permission()`)
- Force password change on first login (`must_change_password` flag)
- Login attempt rate limiting (5 failures → 15-minute lockout)
- Registration with admin approval flow
- Audit logging for all auth events
- User CRUD from admin panel

**Key files:** `auth.py` (174 lines), `pages/login.py`, `pages/register.py`, `pages/change_password.py`, `app.py` (route guards)

### 3.2 Database Layer ✅

**13 tables** with full DDL, indexes, and CRUD operations:

| Table | CRUD Status | Seed Data |
|-------|------------|-----------|
| `roles` | Read-only | 4 rows (admin, researcher, researcher_pending, disabled) |
| `users` | Full CRUD | 4 users (2 admins, 2 researchers) |
| `permissions` | CRUD | 14 permissions for researcher role |
| `user_sessions` | Full CRUD | None (runtime only) |
| `audit_logs` | Create + Read | 1 row (initialization event) |
| `scenarios` | Full CRUD | 4 official scenarios |
| `scenario_constraints` | Full CRUD | None |
| `simulation_runs` | Full CRUD | None (no engine to populate) |
| `run_metrics` | Create + Read | None (no engine to populate) |
| `rl_models` | **Schema-only** | None |
| `rl_checkpoints` | **Schema-only** | None |
| `notifications` | Create + Read + Update | None |
| `system_settings` | Read + Upsert | 7 rows (config defaults) |
| `backups` | Full CRUD | None |
| `login_attempts` | Create + Read | None (runtime only) |

**Key file:** `database.py` (1006 lines)

### 3.3 Dashboard UI (16 Pages) ✅

All pages built with premium dark-themed enterprise design:

| Page | Route | File | Data Source | Permission |
|------|-------|------|-------------|------------|
| Login | `/login` | `pages/login.py` | Real DB | Public |
| Register | `/register` | `pages/register.py` | Real DB | Public |
| Change Password | `/change-password` | `pages/change_password.py` | Real DB | Authenticated |
| Dashboard | `/dashboard` | `pages/dashboard.py` + `layout.py` | Mock (random) | `dashboard:view` |
| Simulation Control | `/simulation` | `pages/simulation.py` | Stub (static) | `simulation:view` |
| Scenarios | `/scenarios` | `pages/scenarios.py` | **Real DB** | `scenarios:view` |
| Live Traffic | `/live-traffic` | `pages/live_traffic.py` | Mock (hardcoded) | `live-traffic:view` |
| Performance | `/performance` | `pages/performance.py` | Stub (empty) | `performance:view` |
| AI Agent (RL) | `/ai-agent` | `pages/ai_agent.py` | Stub (empty) | `ai-agent:view` |
| Runs & Reports | `/runs-reports` | `pages/runs_reports.py` | **Real DB** | `runs-reports:view` |
| Profile / Settings | `/profile` | `pages/profile_settings.py` | Real DB | `profile:view` |
| Help / About | `/help` | `pages/help_about.py` | Static | `help:view` |
| User Management | `/admin/users` | `pages/admin_users.py` | **Real DB** | `admin-users:view` |
| Role & Access Control | `/admin/roles` | `pages/admin_roles.py` | **Real DB** | `admin-roles:view` |
| Audit Logs | `/admin/audit` | `pages/admin_audit.py` | **Real DB** | `admin-audit:view` |
| Backup & Restore | `/admin/backups` | `pages/admin_backups.py` | **Real DB** | `admin-backups:view` |

### 3.4 Reusable Components ✅

| Component | File | Lines | Status |
|-----------|------|-------|--------|
| Header (nav bar) | `components/header.py` | 151 | Complete — auth-aware user menu, scenario selector, sim timer |
| Sidebar | `components/sidebar.py` | 122 | Complete — role-based sections, active link detection, system status |
| Common Library | `components/common.py` | 254 | Complete — 14 factory functions (KPI cards, modals, tables, tabs, badges, etc.) |

### 3.5 Design System ✅

- Full CSS custom properties (6 background levels, 4 border levels, 4 text levels)
- Premium dark theme with green accent (`#00e676`)
- Consistent card, button, input, table, badge, modal, progress bar styles
- Typography: Inter (sans) + JetBrains Mono (monospace)
- `cubic-bezier(0.16, 1, 0.3, 1)` transitions at 0.2s
- Auth pages with branded radial glow styling
- Responsive considerations

**Key files:** `assets/styles.css`, `assets/auth.css`

### 3.6 Admin Tools ✅

- **User Management:** Full CRUD with search, filter, role badges, status pills, avatar initials, activity stats, last login
- **Role & Access Control:** Phoenix-inspired permission matrix, KPI summary row, grouped permissions, role comparison, pending changes tracking, save/reset
- **Audit Logs:** Timestamped event viewer with filters
- **Backup & Restore:** Database backup creation, restore, download, delete

### 3.7 Routing & Callbacks ✅

- `app.py`: Full route registration with auth gating, permission checks, admin guards, 404 handler, force password change redirect
- `callbacks.py`: 5 callbacks — live clock, sim timer (demo mode), phase timer (demo mode), control button state machine, view toggle
- All callbacks use `prevent_initial_call=True` and `ctx.triggered_id` pattern

### 3.8 Configuration ✅

`config.py` (27 lines): `SECRET_KEY`, `DB_PATH`, `SESSION_TIMEOUT`, default admin credentials, app metadata, registration mode, password requirements, logging level.

### 3.9 Testing ✅

- `tests/test_admin_roles_helpers.py`: Unit tests for `permission_key`, `flatten_permission_groups`, `apply_pending_permissions`, `compute_role_stats`

---

## 4. What's Partially Complete / Mock

### 4.1 Live Traffic Page

**File:** `pages/live_traffic.py`
**Status:** Elaborate mock — all values are hardcoded

- KPIs: `'187'` vehicles, `'12.4'`s wait, `'14'` queue, `'842'/h` throughput, `'1'` emergency
- Queue bars: `'40%'`, `'25%'`, `'60%'`, `'35%'` (hardcoded heights)
- Traffic lights: NS=red active, EW=green active (static display)
- Phase timer: hardcoded `'18'`s with static ring progress
- Direction breakdown: fixed-width bars (65%, 40%, 85%, 50%)
- Events feed: 7 hardcoded items with fake timestamps
- `dcc.Interval(id='lt-update-interval', interval=1000)` exists but no callbacks connect to it
- Bottom charts (`lt-queue-chart`, `lt-wait-chart`) are empty `dcc.Graph` with no figure data

### 4.2 Dashboard (layout.py)

**File:** `layout.py` (909 lines)
**Status:** All mock — uses `random` module with fixed seeds

- `create_traffic_flow_figure()`: `random.seed(42); random.randint(18, 35)` for 4 directions × 30 points
- `create_wait_time_figure()`: `random.seed(99); random.uniform(10, 16)` for RL vs baseline traces
- KPI cards: `'12.4'`s, `'5.2'` veh, `'842'` veh/h, `'186'`, `'1'` (all hardcoded)
- RL Agent status: `'68%'` progress, `'0.22'` epsilon, `'1,247'` episodes, `'+3,842'` reward
- Events feed: 7 hardcoded items
- Sim view: static image `/assets/traffic_intersection.png`
- No database queries for any dashboard data

### 4.3 Simulation Timer & Controls (callbacks.py)

**File:** `callbacks.py`
**Status:** Demo mode only — no real engine connection

- Timer starts at hardcoded `elapsed_seconds: 872` and counts up
- Phase timer cycles with `random.randint(15, 35)` phase durations
- Start/Pause/Stop/Reset buttons change status badge CSS only (`Idle` ↔ `Running` ↔ `Paused`)
- No simulation engine is started/stopped — purely a UI state machine

### 4.4 Runs & Reports

**File:** `pages/runs_reports.py`
**Status:** Real DB infrastructure, but no data

- Real CRUD via `database.get_runs()`, `database.delete_run()`, `database.get_run_metrics()`
- CSV and Excel exports work (use real dataframes)
- **PDF export is fake:** generates a plain `.txt` file with `.pdf` extension
- **Comparison report is fake:** generates a `.txt` file
- `simulation_runs` table is empty — no simulation engine to populate it

### 4.5 Scenarios (CRUD complete, no engine to run them)

**File:** `pages/scenarios.py`
**Status:** Full real DB CRUD, 4 seed scenarios

- All scenario CRUD operations work: create, read, update, delete, duplicate
- 4 official seed scenarios: Tagum City Main, Secondary, Emergency Vehicle, Lane Closure
- Constraints system is fully wired (`scenario_constraints` table)
- **Gap:** Scenarios define *what* to simulate, but no engine exists to *run* them

---

## 5. What's NOT Started / Missing

### 5.1 Simulation Engine ❌

No simulation engine of any kind exists. The choices from the planning docs are:
- **ORIGINAL PLAN:** SUMO + TraCI integration
- **REVISED PLAN:** Custom Python engine (`SMARTFLOW_Implementation_Plan_Without_SUMO.md`)

Neither has been started. There are:
- Zero imports of SUMO, TraCI, or any simulation library
- No `simulation/` package directory
- No vehicle agent classes
- No pedestrian agent classes
- No traffic network model
- No signal state machine
- No simulation loop

### 5.2 RL Controller ❌

No reinforcement learning implementation exists:
- Zero imports of PyTorch, TensorFlow, Stable-Baselines3, or any ML library
- No DQN/Double DQN/A2C/PPO implementation
- No observation/action/reward system
- No training loop
- AI Agent page (`pages/ai_agent.py`) is a stub with empty charts and `'--'` values
- `rl_models` and `rl_checkpoints` tables are schema-only (no CRUD functions in `database.py`)
- `requirements.txt` has no RL dependencies

### 5.3 Live 3D Visualization ❌

- No Three.js integration
- Simulation view shows a static PNG image only (`/assets/traffic_intersection.png`)
- No real-time vehicle/pedestrian rendering
- The `live_traffic.py` page has CSS-based static mock layout, not 3D

### 5.4 Real Metrics Pipeline ❌

- `run_metrics` table is empty (no simulation runs to generate metrics)
- `simulation_runs` table is empty (no engine to create runs)
- All KPI cards, charts, and event feeds use mock/random/hardcoded data
- Performance page (`pages/performance.py`) shows "Run a simulation to view detailed metrics" placeholder

### 5.5 Backend Integration ❌

- Simulation control buttons (Start/Pause/Stop/Reset) change CSS classes but don't connect to any engine
- No TraCI or custom engine loop
- No scenario-to-run pipeline
- The `rl_model_id` foreign key in `simulation_runs` is always NULL

---

## 6. Database Status

### 6.1 Tables with Real Seed Data

| Table | Row Count | Notes |
|-------|-----------|-------|
| `roles` | 4 | admin, researcher, researcher_pending, disabled |
| `users` | 4 | admin, admin2, researcher, researcher2 |
| `permissions` | 14 | Researcher role: view/run/create/edit/delete/export on each page |
| `system_settings` | 7 | registration_mode, session_timeout, min_password_length, app_name, app_version, maintenance_mode, logging_level |
| `scenarios` | 4 | Tagum City Main, Secondary Route, Emergency Vehicle, Lane Closure (all `is_official=1`) |
| `audit_logs` | 1 | DB initialization event |

### 6.2 Tables That Are Empty (No Data)

| Table | Reason |
|-------|--------|
| `simulation_runs` | No simulation engine to create runs |
| `run_metrics` | No simulation runs to generate metrics |
| `rl_models` | No RL training — table is schema-only |
| `rl_checkpoints` | No RL training — table is schema-only |
| `scenario_constraints` | Seed scenarios don't include constraints |
| `user_sessions` | Runtime only (created on login) |
| `notifications` | No notification-generating events |
| `backups` | No manual backups created yet |
| `login_attempts` | Runtime only |

### 6.3 Tables Lacking CRUD Functions

| Table | Missing Functions |
|-------|-------------------|
| `rl_models` | No `create_rl_model()`, `get_rl_models()`, `update_rl_model()`, `delete_rl_model()` |
| `rl_checkpoints` | No `save_checkpoint()`, `get_checkpoints_for_model()`, `get_latest_checkpoint()` |

These tables have DDL in `SCHEMA_SQL` but zero functions in `database.py`. They're pure scaffolding.

---

## 7. Page-by-Page Implementation Status

| # | Page | Import DB? | Real Data? | Callbacks? | Mock/Stub? | Verdict |
|---|------|-----------|------------|------------|------------|---------|
| 1 | `login.py` | ✅ | ✅ Real | ✅ Login callback | — | **Complete** |
| 2 | `register.py` | ✅ | ✅ Real | ✅ Register callback | — | **Complete** |
| 3 | `change_password.py` | ✅ | ✅ Real | ✅ Change callback | — | **Complete** |
| 4 | `dashboard.py` | — | ❌ | — (in callbacks.py) | ✅ All mock | **Mock** |
| 5 | `simulation.py` | — | ❌ | ❌ None | ✅ All static | **Stub** |
| 6 | `scenarios.py` | ✅ | ✅ Real DB | ✅ Full CRUD | — | **Complete** |
| 7 | `live_traffic.py` | — | ❌ | ❌ None | ✅ All hardcoded | **Mock** |
| 8 | `performance.py` | — | ❌ | ❌ None | ✅ Empty charts | **Stub** |
| 9 | `ai_agent.py` | — | ❌ | ❌ None | ✅ Empty, `'--'` | **Stub** |
| 10 | `runs_reports.py` | ✅ | ✅ Real DB (empty) | ✅ CRUD + export | ⚠️ PDF is fake | **Real DB** |
| 11 | `profile_settings.py` | ✅ | ✅ Real DB | ✅ Profile callbacks | — | **Complete** |
| 12 | `help_about.py` | — | — (static) | — | — | **Complete** |
| 13 | `admin_users.py` | ✅ | ✅ Real DB | ✅ Full CRUD | — | **Complete** |
| 14 | `admin_roles.py` | ✅ | ✅ Real DB | ✅ Full matrix | — | **Complete** |
| 15 | `admin_audit.py` | ✅ | ✅ Real DB | ✅ Filters | — | **Complete** |
| 16 | `admin_backups.py` | ✅ | ✅ Real DB | ✅ Backup/Restore | — | **Complete** |

**Summary:** 10 pages are complete with real DB, 3 are mocks, 3 are stubs.

---

## 8. Measured Against SmartFlow Planning Docs

### 8.1 Against `SMARTFLOW_Project_Master_Reference.md` — 7 Objectives

| # | Objective | Status |
|---|-----------|--------|
| 1 | Develop a realistic network model of a selected Tagum City intersection | ❌ Not started — no network model exists |
| 2 | Design heterogeneous autonomous vehicle & pedestrian agents | ❌ Not started — no agent classes |
| 3 | Implement configurable traffic demand & pedestrian generation | ⚠️ Scenario configs exist; no generator |
| 4 | Develop an RL-based adaptive traffic signal controller (DQN/Double DQN) | ❌ Not started |
| 5 | Create configurable disruption scenarios | ✅ Scenario definitions exist |
| 6 | Build an interactive dashboard for simulation control & monitoring | ✅ Complete (mock data) |
| 7 | Compare RL adaptive control vs. fixed-time baseline | ❌ Not started — no engine to run either |

### 8.2 Against `SMARTFLOW_Implementation_Plan_Without_SUMO.md` — 8 Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Foundation (auth, DB, UI framework, project structure) | ✅ Complete |
| 2 | Basic Simulation (network model, agent spawning, trivial movement) | ❌ Not started |
| 3 | Vehicle & Pedestrian Agent Behavior (car-following, lane-changing, pedestrian crossing) | ❌ Not started |
| 4 | Fixed-Time Signal Controller & Metrics (phase cycling, queue/wait/throughput measurement) | ❌ Not started |
| 5 | Advanced Simulation (lane closures, construction, accidents, flooding, emergency vehicles) | ❌ Not started |
| 6 | RL Controller (DQN training, checkpoint saving, hyperparameter tuning) | ❌ Not started |
| 7 | Dashboard Integration (replace all mock data with live engine state) | ⚠️ Dashboard built; engine missing |
| 8 | Testing, Validation & Polish (integration tests, performance benchmarking, capstone readiness) | ⚠️ Minimal unit tests; UI polished |

### 8.3 Against `SMARTFLOW_pages_plan.md` — 5 Build Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Core Access (auth, login, register, roles, permissions) | ✅ Complete |
| 2 | Researcher Workflow (dashboard, simulation, scenarios, live traffic, performance, AI agent, runs/reports) | ⚠️ UI complete; all data mock |
| 3 | RL / Comparison (RL training pipeline, fixed-time baseline, AB comparison) | ❌ Not started |
| 4 | Admin Features (user management, roles, audit, backups) | ✅ Complete |
| 5 | Polish (responsive design, accessibility, error states, loading, empty states) | ⚠️ UI polished; engine missing |

---

## 9. Architectural Issues & Tech Debt

### 9.1 Duplicate Header/Sidebar in `layout.py`

**Severity:** Medium
**Description:** `layout.py` (909 lines) contains duplicate implementations of `create_header()` and `create_sidebar()` that differ from the canonical versions in `components/header.py` and `components/sidebar.py`. The `layout.py` versions lack user menus and role-based admin sections. The `components/` versions are the ones used by all pages — `layout.py` is legacy starter code.

**Recommendation:** Deprecate or remove the duplicate implementations in `layout.py`. Add a comment marking it as legacy if keeping for reference.

### 9.2 `layout.py` Contains Mock Dashboard Content

**Severity:** Low
**Description:** `layout.py` is imported by `pages/dashboard.py` but contains all mock/random data generation. When the simulation engine is built, this file should be refactored to pull real data from the engine/database instead of `random.randint()`.

### 9.3 `rl_models` and `rl_checkpoints` Tables Are Schema-Only

**Severity:** Medium
**Description:** These tables have DDL in `SCHEMA_SQL` and a foreign key reference from `simulation_runs.rl_model_id`, but zero CRUD functions in `database.py`. This creates a silent failure path — any attempt to reference an RL model from a simulation run will fail.

**Recommendation:** Either add CRUD functions now, or drop the `rl_model_id` FK until the RL pipeline is implemented.

### 9.4 No Simulation Engine — Core Research Gap

**Severity:** Critical
**Description:** The project's core purpose (traffic simulation + RL signal optimization) has zero implementation. All dashboard data is mock/random/stub.

### 9.5 PDF Export Is Fake

**Severity:** Low
**Description:** `pages/runs_reports.py` generates plain `.txt` files with `.pdf` extension for both PDF export and comparison reports. Real PDF generation needs a library like `reportlab` or `weasyprint`.

### 9.6 Minor: Duplicate Import in `components/sidebar.py`

**Severity:** Trivial
**Description:** Line 8 duplicates the import from line 7: `from dash import html, dcc` appears twice.

---

## 10. Recommended Next Steps

### Immediate Priority: Simulation Engine

The project has a fully polished frontend with nothing to drive it. The simulation engine is the critical missing piece. The `SMARTFLOW_Implementation_Plan_Without_SUMO.md` provides the clearest path:

1. **Create `simulation/` package** with these modules:
   - `network.py` — Traffic network model (four-way intersection, lanes, approaches)
   - `agents.py` — Vehicle and pedestrian agent classes with heterogeneous profiles
   - `traffic_light.py` — Signal state machine (fixed-time phase cycling)
   - `engine.py` — Main simulation loop (spawn, update, metrics, step)
   - `scenarios.py` — Load scenario configs from DB and apply constraints
   - `metrics.py` — Compute wait time, queue length, throughput, pedestrian delay
   - `controllers.py` — Fixed-time and RL controller interfaces
   - `serializer.py` — Save run state and metrics to DB

2. **Wire engine to existing UI callbacks** — Connect Start/Pause/Stop/Reset to the engine, push engine state to the dashboard via `dcc.Interval`

3. **Replace mock data** — Update `layout.py`, `live_traffic.py`, `performance.py`, `ai_agent.py` to pull from engine state instead of hardcoded values

### Secondary Priority: RL Controller

4. **Add RL dependencies** to `requirements.txt` — `torch`, `numpy`, `gymnasium`
5. **Implement DQN/Double DQN** controller in `controllers.py`
6. **Add CRUD functions** for `rl_models` and `rl_checkpoints` in `database.py`
7. **Build training UI** in `pages/ai_agent.py` — wire hyperparameter inputs to training loop

### Tertiary: Polish & Cleanup

8. **Deprecate or remove** duplicate header/sidebar in `layout.py`
9. **Implement real PDF export** using `reportlab` or `weasyprint`
10. **Add real 3D visualization** (Three.js or Plotly animation)
11. **Add integration tests** for simulation engine components
12. **Fix duplicate import** in `components/sidebar.py` (line 8)

---

## Summary

| Area | Status |
|------|--------|
| **Frontend / UI** | ✅ Complete — 16 pages, premium dark theme, full component library |
| **Authentication / Auth** | ✅ Complete — login, register, sessions, RBAC, rate limiting |
| **Database** | ✅ Complete — 13 tables, full CRUD for 11 of 13, seed data |
| **Admin Tools** | ✅ Complete — user management, role matrix, audit logs, backups |
| **Scenarios** | ✅ Complete — full CRUD, 4 seed scenarios, constraint system |
| **Runs & Reports** | ⚠️ Real DB but empty — no engine to populate |
| **Live Traffic** | ❌ Mock — all hardcoded demo numbers |
| **Dashboard** | ❌ Mock — random data with fixed seeds |
| **Simulation Controls** | ❌ Mock — UI state machine only |
| **Performance / AI Agent** | ❌ Stubs — empty charts, placeholder text |
| **Simulation Engine** | ❌ Not started — no SUMO, no custom engine |
| **RL Controller** | ❌ Not started — no DQN, no PyTorch, no training loop |
| **3D Visualization** | ❌ Not started — static PNG only |
| **Real Metrics Pipeline** | ❌ Not started — zero simulation data |

**Bottom line:** The project is a fully built, production-quality **dashboard shell**. All authentication, database, UI, and admin infrastructure is complete. The **simulation engine and RL controller — the project's core research components — have not been started.** The project is at the transition point between Phases 1-2 (UI and Auth complete) and Phase 3+ (simulation engine needed).
