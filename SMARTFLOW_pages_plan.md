# SMARTFLOW Page Build Plan

## Purpose
This document defines the necessary pages, role-based navigation, authentication flow, and build checklist for SMARTFLOW, a local simulation-based traffic analysis and decision-support dashboard using Dash, SQLite, simulation control, live monitoring, reports, and RL-vs-fixed-time evaluation. The project scope already includes local authentication, scenario configuration, simulation control, live monitoring, performance evaluation, reporting, and stored experiment records, so the page structure below is designed to support that full workflow.

---

## Roles

### 1) Admin
**Purpose:** Full platform control.

**Can access:**
- All researcher pages
- User Management
- Role & Access Control
- Scenario Library Management
- System Configuration
- Database / Backup Tools
- Audit Logs

### 2) Researcher
**Purpose:** Run experiments, monitor simulations, compare results, and export reports.

**Can access:**
- Dashboard
- Simulation Control
- Scenarios
- Live Traffic
- Performance
- AI Agent (RL)
- Runs & Reports
- Profile / Settings
- Help / About

---

## Navigation Design

### Shared Top Header
Necessary items:
- SMARTFLOW logo / project title
- Current selected scenario
- Current simulation status (Idle / Running / Paused / Stopped / Completed)
- Simulation timer
- Logged-in user name and role badge
- Notifications / alerts icon
- Profile menu
- Logout button

### Researcher Sidebar
Necessary pages:
1. Dashboard
2. Simulation Control
3. Scenarios
4. Live Traffic
5. Performance
6. AI Agent (RL)
7. Runs & Reports
8. Profile / Settings
9. Help / About

### Admin Sidebar
Necessary pages:
1. Dashboard
2. Simulation Control
3. Scenarios
4. Live Traffic
5. Performance
6. AI Agent (RL)
7. Runs & Reports
8. User Management
9. Role & Access Control
10. Scenario Library Admin
11. System Configuration
12. Audit Logs
13. Backup & Restore
14. Profile / Settings
15. Help / About

---

## Authentication Pages

## Login Page
Necessary items:
- Project branding and short description
- Username or email input
- Password input
- Show / hide password toggle
- Remember me checkbox
- Login button
- Link to Register page
- Forgot password flow (local reset by admin or security question flow)
- Login validation messages
- Disabled state while submitting
- Security note that the system is for authorized users only

Necessary backend logic:
- Validate credentials against SQLite users table
- Hash passwords, never store plain text
- Check account status (active, disabled, locked)
- Create authenticated session
- Redirect by role after login
- Record login time and audit entry

## Register Page
Necessary items:
- Full name
- Username
- Email
- Password
- Confirm password
- Institution / department
- Role request note (default researcher request or restricted signup)
- Register button
- Link back to Login
- Terms / project-use acknowledgement
- Validation messages

Recommended role rule:
- Public self-registration should create a pending researcher request or inactive account
- Only admin should approve, activate, or assign admin access

Necessary backend logic:
- Unique username and email validation
- Password strength check
- Save new account to SQLite
- Default role = researcher_pending or researcher_inactive
- Audit registration event

## First Admin Account
Necessary setup:
- Seed one default admin account during first app initialization
- Force password change on first login
- Prevent deletion of the last active admin account
- Store creation timestamp and creator metadata

---

## Page-by-Page Build Checklist

## 1) Dashboard
**Goal:** Main command center and quick overview.

Necessary sections:
- Live simulation preview panel
- Current scenario summary
- Current controller mode (Fixed-Time or RL)
- KPI cards: average waiting time, average queue length, maximum queue length, throughput, pedestrian delay, emergency clearance status
- Current signal phase and phase timer
- Recent events / alerts panel
- Quick actions: Start, Pause, Stop, Reset
- Quick scenario selector
- Latest completed run summary
- System health card: simulation engine, RL engine, visualization, database, session

Nice-to-have:
- Quick compare last RL run vs last fixed-time run
- Alert severity colors

## 2) Simulation Control
**Goal:** Full run execution and runtime control.

Necessary sections:
- Start / Pause / Stop / Reset controls
- Simulation speed control
- Run duration settings
- Warm-up settings
- Random seed or repeatability option
- Controller mode selection (Fixed-Time vs RL)
- Manual phase override area (admin only or protected mode)
- Live run state log
- Current phase timeline
- Engine status and connection state

Necessary validations:
- Prevent start if scenario config is incomplete
- Prevent duplicate run launch
- Confirm destructive reset if a run is active

## 3) Scenarios
**Goal:** Configure experiment inputs and disruption conditions.

Necessary sections:
- Scenario preset selector
- Traffic density settings
- Pedestrian density settings
- Emergency vehicle settings
- Lane closure toggle / configuration
- Road construction toggle / configuration
- Accident / blockage toggle / configuration
- Flooding / disruption toggle / configuration
- Saved scenario presets list
- Save preset, duplicate preset, delete preset
- Scenario notes / description

Necessary logic:
- Store scenario presets in SQLite
- Allow loading previously saved presets
- Link selected scenario to each run record

## 4) Live Traffic
**Goal:** Detailed live monitoring page.

Necessary sections:
- Large 3D / map simulation panel
- Approach-by-approach queue counts
- Vehicle counts by direction
- Pedestrian waiting counts by crossing
- Active signal state visualization
- Emergency vehicle detection status
- Incident / disruption state panel
- Real-time event stream
- Snapshot capture button

Nice-to-have:
- Lane-level occupancy view
- Color-coded congestion map

## 5) Performance
**Goal:** Evaluate current and completed runs.

Necessary sections:
- Average waiting time chart
- Average queue length chart
- Maximum queue length chart
- Throughput chart
- Pedestrian delay chart
- Emergency clearance time chart
- Signal phase efficiency chart
- Congestion severity indicator
- Scenario filters
- Time range filters
- Export chart / export data buttons

Necessary comparison tools:
- Compare RL vs Fixed-Time
- Compare run A vs run B
- Compare same scenario across multiple repetitions

## 6) AI Agent (RL)
**Goal:** Expose RL-specific diagnostics and decisions.

Necessary sections:
- Agent status (idle, training, evaluating, running)
- Model type (DQN / Double DQN etc.)
- Current observation summary
- Current chosen action
- Reward trend
- Episode count
- Epsilon / exploration value
- Loss value
- Checkpoint / model version info
- Last action timestamp
- Agent notes / explanation panel

Nice-to-have:
- Observation vector breakdown
- Reward component breakdown
- Training progress history

## 7) Runs & Reports
**Goal:** Store, review, compare, and export experiment outputs.

Necessary sections:
- Runs table with filters
- Run details drawer/page
- Scenario used
- Controller used
- Date and time
- Duration
- Created by user
- Result summary metrics
- Export PDF / CSV / image
- Compare selected runs
- Mark run as baseline / favorite
- Notes and interpretation field

Necessary storage fields per run:
- run_id
- user_id
- scenario_id
- control_mode
- start_time
- end_time
- status
- summary metrics
- output file paths

## 8) Profile / Settings
**Goal:** User preferences and local app behavior.

Necessary sections:
- Profile info
- Change password
- Theme / density preference
- Default landing page
- Default scenario selection
- Auto-refresh interval
- Notification preferences
- Export preferences
- Session info

Admin-only settings should not be mixed here; put them in System Configuration.

## 9) Help / About
**Goal:** Explain the system and reduce user confusion.

Necessary sections:
- What SMARTFLOW does
- Scope and limitations
- How to run a simulation
- Meaning of each metric
- RL vs Fixed-Time explanation
- Scenario/disruption definitions
- FAQ
- Contact / project team info
- Version info

---

## Admin-Only Pages

## 10) User Management
**Goal:** Manage all local accounts.

Necessary sections:
- Users table
- Search and filter by role/status
- Create user
- Edit user
- Activate / deactivate user
- Reset password
- Lock / unlock account
- Delete user (with safeguards)
- View last login
- View created runs count
- Bulk actions for selected users

Necessary safeguards:
- Cannot delete the last active admin
- Cannot demote own account if it is the last admin
- Audit every admin action

## 11) Role & Access Control
**Goal:** Control permissions cleanly.

Necessary sections:
- Roles list
- Permission matrix by page and action
- View-only vs edit permissions
- Simulation execution permission
- Scenario management permission
- Report export permission
- User-management permission
- Admin-only protected actions list

Recommended base roles:
- admin
- researcher
- researcher_pending
- disabled

## 12) Scenario Library Admin
**Goal:** Govern official presets and disruption templates.

Necessary sections:
- Approved scenario presets
- Official baseline scenarios
- Default training/evaluation scenarios
- Constraint templates
- Publish / unpublish scenario
- Archive old presets
- Preset ownership and version history

## 13) System Configuration
**Goal:** Central admin settings for the platform.

Necessary sections:
- SQLite database path/config info
- Simulation engine paths
- SUMO / TraCI configuration fields
- Model/checkpoint directories
- Export directories
- Default run settings
- Session timeout
- Registration mode (open, approval-only, closed)
- Password policy settings
- Logging level
- Maintenance mode toggle

## 14) Audit Logs
**Goal:** Trace sensitive actions.

Necessary sections:
- Login history
- Failed login attempts
- User creation/edit/deletion events
- Scenario creation/edit/deletion events
- Run start/stop/reset events
- Export/download events
- Role change events
- Password reset events
- Timestamp, actor, action, target, details

## 15) Backup & Restore
**Goal:** Protect local project data.

Necessary sections:
- Manual backup button
- Backup history list
- Restore backup action
- Export SQLite database
- Export scenarios only
- Export runs/reports only
- Warning / confirmation dialogs

---

## Suggested Database Tables

Necessary tables:
- users
- roles
- permissions
- user_sessions
- audit_logs
- scenarios
- scenario_constraints
- simulation_runs
- run_metrics
- rl_models
- rl_checkpoints
- notifications
- system_settings
- backups

### users
Recommended fields:
- id
- full_name
- username
- email
- password_hash
- role_id
- status
- must_change_password
- created_at
- updated_at
- last_login_at

### scenarios
Recommended fields:
- id
- name
- description
- traffic_density
- pedestrian_density
- emergency_mode
- lane_closure_config
- construction_config
- accident_config
- flooding_config
- created_by
- created_at
- updated_at
- is_official
- is_archived

### simulation_runs
Recommended fields:
- id
- scenario_id
- user_id
- control_mode
- rl_model_id
- status
- start_time
- end_time
- duration_seconds
- seed
- notes
- created_at

### run_metrics
Recommended fields:
- id
- run_id
- avg_waiting_time
- avg_queue_length
- max_queue_length
- throughput
- avg_pedestrian_delay
- emergency_clearance_time
- signal_phase_efficiency
- congestion_severity
- raw_metrics_json

---

## Access Matrix

| Page | Researcher | Admin |
|---|---|---|
| Login | Yes | Yes |
| Register | Yes | Yes |
| Dashboard | Yes | Yes |
| Simulation Control | Yes | Yes |
| Scenarios | Yes | Yes |
| Live Traffic | Yes | Yes |
| Performance | Yes | Yes |
| AI Agent (RL) | Yes | Yes |
| Runs & Reports | Yes | Yes |
| Profile / Settings | Yes | Yes |
| Help / About | Yes | Yes |
| User Management | No | Yes |
| Role & Access Control | No | Yes |
| Scenario Library Admin | No | Yes |
| System Configuration | No | Yes |
| Audit Logs | No | Yes |
| Backup & Restore | No | Yes |

---

## Build Priority

### Phase 1 - Core Access
- Login page
- Register page
- Session handling
- Admin seed account
- Role-based route protection

### Phase 2 - Researcher Core Workflow
- Dashboard
- Simulation Control
- Scenarios
- Live Traffic
- Performance
- Runs & Reports

### Phase 3 - RL and Comparison
- AI Agent (RL)
- RL vs Fixed-Time comparison views
- Run comparison tools

### Phase 4 - Admin Features
- User Management
- Role & Access Control
- Scenario Library Admin
- Audit Logs
- System Configuration
- Backup & Restore

### Phase 5 - Polish
- Notifications
- Better exports
- Rich filters
- UI refinements
- Help / About documentation

---

## Final Recommended Navigation

### Researcher Final Navbar
- Dashboard
- Simulation Control
- Scenarios
- Live Traffic
- Performance
- AI Agent (RL)
- Runs & Reports
- Profile / Settings
- Help / About

### Admin Final Navbar
- Dashboard
- Simulation Control
- Scenarios
- Live Traffic
- Performance
- AI Agent (RL)
- Runs & Reports
- User Management
- Role & Access Control
- Scenario Library Admin
- System Configuration
- Audit Logs
- Backup & Restore
- Profile / Settings
- Help / About

---

## Implementation Notes
- Keep authentication local and SQLite-based.
- Require login before exposing simulation controls, configuration, reports, and stored results.
- Keep admin-only actions clearly separated from researcher workflow.
- Preserve the dashboard as a research and decision-support system, not a generic corporate admin panel.
- Prioritize complete end-to-end experiment flow before adding advanced polish.
