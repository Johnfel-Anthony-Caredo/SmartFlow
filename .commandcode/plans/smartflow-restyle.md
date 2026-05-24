# SMARTFLOW Dashboard Restyle Plan
Quick reference — see full plan in chat context.

## Files to Modify
1. `components/sidebar.py` — Add brand area + section headers (MAIN/INTELLIGENCE/SYSTEM/ADMIN)
2. `layout.py` — Remove `.speed-control` block from `create_control_panel()`
3. `pages/simulation.py` — Remove speed slider, swap buttons to `ctrl-btn` pattern
4. `callbacks.py` — Remove `update_speed_display` callback
5. `assets/styles.css` — New sidebar-brand styles, enhanced ctrl-btn colors, remove speed-control CSS blocks
