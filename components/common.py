"""
SMARTFLOW — Common UI Components
Reusable utility functions for creating consistent UI elements.
"""

from dash import html, dcc


def create_card(children, className='', **kwargs):
    return html.Div(
        className=f'card {className}'.strip(),
        children=children,
        **kwargs
    )


def create_kpi_card(icon, title, value, color='#00e676', id=None):
    return html.Div(
        className='kpi-card',
        id=id,
        children=[
            html.Div(
                className='kpi-icon',
                style={'color': color},
                children=[html.I(className=icon)]
            ),
            html.Div(
                className='kpi-content',
                children=[
                    html.Div(className='kpi-title', children=title),
                    html.Div(className='kpi-value', children=value),
                ]
            )
        ]
    )


def create_section(title, children, icon=None, subtitle=None, className=''):
    header_children = []
    if icon:
        header_children.append(html.I(className=icon))
    
    title_children = title
    if subtitle:
        title_children = [
            html.Span(title, className='section-title-text'),
            html.Small(subtitle, className='section-subtitle')
        ]
    
    header_children.append(html.H3(className='section-title', children=title_children))
    
    return html.Div(
        className=f'section {className}'.strip(),
        children=[
            html.Div(className='section-header', children=header_children),
            html.Div(className='section-content', children=children),
        ]
    )


def create_button(text, id=None, className='btn', icon=None, disabled=False):
    children = []
    if icon:
        children.append(html.I(className=icon))
    children.append(html.Span(children=text))

    props = {'className': className, 'disabled': disabled}
    if id is not None:
        props['id'] = id
    if not children:
        children = text

    return html.Button(children=children, **props)


def create_input(id, type='text', placeholder='', value='', className='input-field'):
    return dcc.Input(
        id=id,
        type=type,
        placeholder=placeholder,
        value=value,
        className=className,
        debounce=True
    )


def create_dropdown(id, options, value=None, placeholder='Select...', className='dropdown'):
    return dcc.Dropdown(
        id=id,
        options=options,
        value=value,
        placeholder=placeholder,
        className=className,
        clearable=False
    )


def create_status_badge(status, label=None):
    status_map = {
        'active': ('status-active', 'Active'),
        'inactive': ('status-inactive', 'Inactive'),
        'pending': ('status-pending', 'Pending'),
        'running': ('status-running', 'Running'),
        'paused': ('status-paused', 'Paused'),
        'stopped': ('status-stopped', 'Stopped'),
        'completed': ('status-completed', 'Completed'),
        'error': ('status-error', 'Error'),
    }
    
    css_class, default_label = status_map.get(status, ('', status))
    display_label = label or default_label
    
    return html.Span(
        className=f'status-badge {css_class}',
        children=display_label
    )


def create_alert(message, type='info', id=None):
    alert_types = {
        'info': 'alert-info',
        'success': 'alert-success',
        'warning': 'alert-warning',
        'error': 'alert-error',
    }
    
    return html.Div(
        id=id,
        className=f'alert {alert_types.get(type, "alert-info")}',
        children=message
    )


def create_modal(id, title, children, is_open=False):
    return html.Div(
        id=id,
        className='modal-overlay' if is_open else 'modal-overlay hidden',
        children=[
            html.Div(
                className='modal',
                children=[
                    html.Div(
                        className='modal-header',
                        children=[
                            html.H2(children=title),
                            html.Button(
                                className='modal-close',
                                children='×',
                                id=f'{id}-close'
                            )
                        ]
                    ),
                    html.Div(className='modal-body', children=children)
                ]
            )
        ]
    )


def create_table(headers, rows, id=None, className='data-table'):
    header_row = html.Thead(
        children=[
            html.Tr(
                children=[html.Th(children=h) for h in headers]
            )
        ]
    )
    
    body_rows = [
        html.Tr(
            children=[html.Td(children=cell) for cell in row]
        )
        for row in rows
    ]
    
    return html.Table(
        id=id,
        className=className,
        children=[
            header_row,
            html.Tbody(children=body_rows)
        ]
    )


def create_tabs(tabs_data, active_tab=None):
    tabs = []
    for tab_id, tab_label in tabs_data.items():
        is_active = (tab_id == active_tab) if active_tab else False
        tabs.append(
            html.Button(
                id=f'tab-{tab_id}',
                className=f'tab-btn {"active" if is_active else ""}',
                children=tab_label
            )
        )
    
    return html.Div(className='tabs-container', children=tabs)


def create_progress_bar(value, max_value=100, color='#00e676', id=None):
    percentage = (value / max_value * 100) if max_value > 0 else 0
    return html.Div(
        id=id,
        className='progress-bar-container',
        children=[
            html.Div(
                className='progress-bar-fill',
                style={
                    'width': f'{percentage}%',
                    'backgroundColor': color
                }
            )
        ]
    )


def create_loading_spinner():
    return html.Div(
        className='loading-spinner',
        children=[
            html.Div(className='spinner'),
            html.Span(children='Loading...')
        ]
    )


def create_empty_state(message, icon='fas fa-inbox'):
    return html.Div(
        className='empty-state',
        children=[
            html.I(className=icon),
            html.P(children=message)
        ]
    )


def create_mini_stat(label, value, icon=None, color='var(--accent)', id=None):
    """Compact stat chip for admin KPI summary rows."""
    props = {'className': 'mini-stat'}
    if id is not None:
        props['id'] = id
    return html.Div(
        **props,
        children=[
            html.Div(className='mini-stat-icon', style={'color': color},
                     children=[html.I(className=icon)] if icon else []),
            html.Div(className='mini-stat-content', children=[
                html.Span(value, className='mini-stat-value'),
                html.Span(label, className='mini-stat-label'),
            ]),
        ]
    )
