# Access Control & Permissions Matrix Redesign

Date: 2026-05-24

## Summary
Redesign the Admin > Role & Access Control page into a Phoenix-inspired, premium permission management dashboard. The page keeps the existing SQLite-backed permissions model but presents a cleaner, more visual, and enterprise-grade interface with a KPI summary row, a grouped permission matrix, compact controls, and a role details panel.

## Goals
- Provide a polished, modern, dark-theme permission matrix that is easy to scan.
- Preserve side-by-side role comparison while reducing the spreadsheet feel.
- Add clear visual hierarchy: header, KPI row, toolbar, matrix, and details panel.
- Maintain existing backend bindings (SQLite permissions storage).
- Keep editing safe with explicit Save/Reset and confirmation for protected actions.
- Ensure responsive layout for narrower screens.

## Non-Goals
- No change to authentication logic or routing rules.
- No new permissions or roles beyond existing database data.
- No advanced workflow (approvals, bulk import/export, or audit analytics).
- No replacement of the SQLite permissions storage.

## Layout Structure
1. **Page Header**
   - Title: "Access Control & Permissions Matrix"
   - Subtitle: Role-based access governance for the SMARTFLOW admin platform.

2. **Summary KPI Row (4 cards)**
   - Total Roles
   - Total Permissions
   - Enabled Admin Permissions
   - Restricted Actions (for selected role)
   - Each card uses an icon chip and compact text.

3. **Main Content Grid (Desktop)**
   - Left: Permission matrix card with toolbar and legend.
   - Right: Role details card showing key facts and guidance.
   - On narrow screens, the role details card stacks below the matrix.

4. **Toolbar Row (above matrix)**
   - Search permissions input.
   - Role selector dropdown.
   - Save Changes (primary action).
   - Reset to Defaults (secondary action).

5. **Permission Matrix Card**
   - Sticky header for role columns.
   - Permission groups with labeled separators.
   - Compact, modern checkbox/toggle indicators per role.

6. **Role Details Card**
   - Role name and badge.
   - Description and intended usage.
   - Granted permissions count.
   - Protected actions list.
   - Notes (who should use the role, risk level).

7. **Legend (below toolbar or below matrix header)**
   - Enabled, Disabled, Locked, Protected indicators.

## Permission Grouping
Groups map to existing permission keys (no new keys):

- **Dashboard access**: dashboard:view
- **Simulation control**: simulation:view, simulation:run
- **Scenario management**: scenarios:view, scenarios:create, scenarios:edit, scenarios:delete
- **Live traffic monitoring**: live-traffic:view
- **Performance reports**: performance:view
- **AI Agent RL panel**: ai-agent:view
- **Runs & Reports export**: runs-reports:view, runs-reports:export
- **User management**: admin-users:view
- **Role access control**: admin-roles:view


- **Audit logs**: admin-audit:view
- **Backup & restore**: admin-backups:view

Group rows act as visual separators and improve scanning.

## Visual System
- **Theme**: Phoenix-inspired dark dashboard with soft borders and subtle gradients.
- **Cards**: rounded corners, gentle border, minimal shadows.
- **Matrix**: muted grid lines, sticky headers, compact spacing.
- **States**:
  - Enabled: green accent indicator.
  - Disabled: muted indicator with low opacity.
  - Locked: gray/disabled indicator with lock icon.
  - Protected: warning accent and confirmation requirement.
- **Typography**: existing font system, with small caps for labels and strong weight for values.

## Interactions and Safety
- **Role selection**:
  - Dropdown selects the active role for editing and details panel.
  - Selected role column is subtly highlighted (column glow and header emphasis).
- **Editing**:
  - Admin column remains locked (always enabled).
  - Researcher role editable by default.
  - Other roles can remain locked unless explicitly enabled in future iterations.
- **Pending changes**:
  - Changes update a local pending state.
  - Save writes to SQLite (existing update function).
  - Reset reloads the saved state from the database.
- **Protected actions**:
  - For admin-critical permissions (user management, role access, audit, backups, scenario library), show a confirmation before adding to pending changes.

## Data and Metrics
- **Total Roles**: count of roles in database.
- **Total Permissions**: length of defined permissions list.
- **Enabled Admin Permissions**: equals total permissions (admin locked to enabled).
- **Restricted Actions**: count of permissions disabled for selected role.

## Accessibility
- Inputs include visible labels or aria labels.
- Keyboard navigation supported for search, role selector, toggles, and buttons.
- Focus states use accent color outline.

## Responsiveness
- Main content switches to single-column stack below 960px.
- Toolbar wraps into two rows with search first, actions aligned right.
- Matrix remains scrollable with sticky header for readability.

## Implementation Notes (Non-Binding)
- Reuse existing KPI card styles from the admin users page to keep consistency.
- Add new CSS classes scoped to the role access page for matrix groups, column highlight, and toggles.
- Keep changes limited to layout and styling, preserving existing database calls.

## Open Questions
- None.
