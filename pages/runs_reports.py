"""
SMARTFLOW — Runs & Reports Page
View simulation run history and generate reports.
Includes permission-enforced actions (delete, export) and audit logging.
"""

import json
import pandas as pd
from datetime import datetime
from dash import html, dcc, callback, Input, Output, State, no_update, ctx
from dash import dash_table
from flask import session

import auth
import database
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section, create_button


def layout():
    # If not authenticated, let app.py handle redirection
    if not auth.is_authenticated():
        return html.Div()
        
    # Get scenarios to populate filters
    scenarios = database.get_scenarios()
    scenario_options = [{'label': 'All Scenarios', 'value': 'all'}] + [
        {'label': s['name'], 'value': str(s['id'])} for s in scenarios
    ]
    
    return html.Div(
        className='app-layout',
        children=[
            create_header(),
            html.Div(
                className='app-body',
                children=[
                    create_sidebar(),
                    html.Main(
                        className='main-content',
                        children=[
                            html.Div(
                                className='page-header',
                                children=[
                                    html.H1(children='Runs & Reports'),
                                    html.P(children='View simulation history and generate reports'),
                                ]
                            ),
                            
                            html.Div(
                                id='runs-alert',
                                className='alert alert-info hidden',
                                children=''
                            ),
                            
                            html.Div(
                                className='runs-controls',
                                children=[
                                    create_section(
                                        title='Filters',
                                        icon='fas fa-filter',
                                        children=[
                                            html.Div(
                                                className='filter-row',
                                                children=[
                                                    html.Div(
                                                        className='form-group',
                                                        children=[
                                                            html.Label(children='Scenario'),
                                                            dcc.Dropdown(
                                                                id='runs-scenario-filter',
                                                                options=scenario_options,
                                                                value='all',
                                                                clearable=False
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='form-group',
                                                        children=[
                                                            html.Label(children='Control Mode'),
                                                            dcc.Dropdown(
                                                                id='runs-mode-filter',
                                                                options=[
                                                                    {'label': 'All Modes', 'value': 'all'},
                                                                    {'label': 'Fixed-Time', 'value': 'fixed-time'},
                                                                    {'label': 'AI Agent', 'value': 'rl-agent'},
                                                                ],
                                                                value='all',
                                                                clearable=False
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='form-group',
                                                        children=[
                                                            html.Label(children='Status'),
                                                            dcc.Dropdown(
                                                                id='runs-status-filter',
                                                                options=[
                                                                    {'label': 'All Status', 'value': 'all'},
                                                                    {'label': 'Completed', 'value': 'completed'},
                                                                    {'label': 'Stopped', 'value': 'stopped'},
                                                                    {'label': 'Running', 'value': 'running'},
                                                                ],
                                                                value='all',
                                                                clearable=False
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='runs-table-section',
                                children=[
                                    create_section(
                                        title='Simulation Runs',
                                        icon='fas fa-list',
                                        children=[
                                            html.Div(
                                                className='table-actions',
                                                children=[
                                                    create_button(
                                                        id='refresh-runs-btn',
                                                        text='Refresh',
                                                        icon='fas fa-sync',
                                                        className='btn btn-secondary'
                                                    ),
                                                    create_button(
                                                        id='export-csv-btn',
                                                        text='Export CSV',
                                                        icon='fas fa-file-csv',
                                                        className='btn btn-primary'
                                                    ),
                                                    create_button(
                                                        id='delete-runs-btn',
                                                        text='Delete Selected',
                                                        icon='fas fa-trash',
                                                        className='btn btn-danger'
                                                    ),
                                                ]
                                            ),
                                            
                                            dash_table.DataTable(
                                                id='runs-table',
                                                columns=[
                                                    {'name': 'ID', 'id': 'id'},
                                                    {'name': 'Timestamp', 'id': 'timestamp'},
                                                    {'name': 'Scenario', 'id': 'scenario_name'},
                                                    {'name': 'Control Mode', 'id': 'control_mode'},
                                                    {'name': 'Duration', 'id': 'duration'},
                                                    {'name': 'Status', 'id': 'status'},
                                                    {'name': 'Avg Wait (s)', 'id': 'avg_wait'},
                                                    {'name': 'Max Queue', 'id': 'max_queue'},
                                                    {'name': 'Throughput', 'id': 'throughput'},
                                                ],
                                                data=[],
                                                row_selectable='multi',
                                                selected_rows=[],
                                                sort_action='native',
                                                sort_mode='multi',
                                                filter_action='native',
                                                page_action='native',
                                                page_current=0,
                                                page_size=10,
                                                style_table={'overflowX': 'auto'},
                                                style_cell={
                                                    'textAlign': 'left',
                                                    'padding': '12px',
                                                    'fontFamily': 'Inter, sans-serif',
                                                    'fontSize': '14px',
                                                },
                                                style_header={
                                                    'backgroundColor': '#f8f9fa',
                                                    'fontWeight': '600',
                                                    'border': '1px solid #dee2e6',
                                                },
                                                style_data={
                                                    'border': '1px solid #dee2e6',
                                                },
                                                style_data_conditional=[
                                                    {
                                                        'if': {'row_index': 'odd'},
                                                        'backgroundColor': '#f8f9fa',
                                                    },
                                                    {
                                                        'if': {'filter_query': '{status} = completed'},
                                                        'color': '#00e676',
                                                        'fontWeight': '600',
                                                    },
                                                    {
                                                        'if': {'filter_query': '{status} = stopped'},
                                                        'color': '#f44336',
                                                        'fontWeight': '600',
                                                    },
                                                ],
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            
                            html.Div(
                                className='reports-section',
                                children=[
                                    create_section(
                                        title='Generate Reports',
                                        icon='fas fa-file-alt',
                                        children=[
                                            html.Div(
                                                className='report-options',
                                                children=[
                                                    html.Div(
                                                        className='report-card',
                                                        children=[
                                                            html.I(className='fas fa-file-pdf'),
                                                            html.H4(children='PDF Report'),
                                                            html.P(children='Generate comprehensive PDF report with charts and analysis'),
                                                            create_button(
                                                                id='generate-pdf-btn',
                                                                text='Generate PDF',
                                                                icon='fas fa-download',
                                                                className='btn btn-primary'
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='report-card',
                                                        children=[
                                                            html.I(className='fas fa-chart-bar'),
                                                            html.H4(children='Comparison Report'),
                                                            html.P(children='Compare multiple runs side-by-side'),
                                                            create_button(
                                                                id='generate-comparison-btn',
                                                                text='Generate Comparison',
                                                                icon='fas fa-balance-scale',
                                                                className='btn btn-primary'
                                                            ),
                                                        ]
                                                    ),
                                                    html.Div(
                                                        className='report-card',
                                                        children=[
                                                            html.I(className='fas fa-file-excel'),
                                                            html.H4(children='Excel Export'),
                                                            html.P(children='Export data to Excel for further analysis'),
                                                            create_button(
                                                                id='generate-excel-btn',
                                                                text='Export Excel',
                                                                icon='fas fa-file-excel',
                                                                className='btn btn-primary'
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            dcc.Download(id='download-runs-csv'),
                            dcc.Download(id='download-runs-excel'),
                            dcc.Download(id='download-runs-pdf'),
                        ]
                    ),
                ]
            ),
        ]
    )


# ─── Callbacks ────────────────────────────────────────────────────────

@callback(
    Output('runs-table', 'data'),
    [Input('refresh-runs-btn', 'n_clicks'),
     Input('runs-scenario-filter', 'value'),
     Input('runs-mode-filter', 'value'),
     Input('runs-status-filter', 'value')]
)
def populate_runs_table(refresh_clicks, scenario_filter, mode_filter, status_filter):
    # Fetch runs
    runs = database.get_runs()
    
    # Filter runs
    filtered_runs = []
    for r in runs:
        # Match Scenario filter
        if scenario_filter != 'all' and str(r['scenario_id']) != scenario_filter:
            continue
            
        # Match Mode filter
        if mode_filter != 'all' and r['control_mode'] != mode_filter:
            continue
            
        # Match Status filter
        if status_filter != 'all' and r['status'] != status_filter:
            continue
            
        metrics = database.get_run_metrics(r['id'])
        avg_wait = f"{metrics['avg_waiting_time']:.1f} s" if metrics else '--'
        max_queue = metrics['max_queue_length'] if metrics else '--'
        throughput = f"{metrics['throughput']} veh/h" if metrics else '--'
        
        filtered_runs.append({
            'id': r['id'],
            'timestamp': r['created_at'],
            'scenario_name': r['scenario_name'] or 'Unknown',
            'control_mode': r['control_mode'].upper(),
            'duration': f"{int(r['duration_seconds'])}s" if r['duration_seconds'] else '0s',
            'status': r['status'].upper(),
            'avg_wait': avg_wait,
            'max_queue': max_queue,
            'throughput': throughput
        })
        
    return filtered_runs


@callback(
    [Output('runs-alert', 'children'),
     Output('runs-alert', 'className'),
     Output('runs-table', 'selected_rows'),
     Output('download-runs-csv', 'data'),
     Output('download-runs-excel', 'data'),
     Output('download-runs-pdf', 'data')],
    [Input('delete-runs-btn', 'n_clicks'),
     Input('export-csv-btn', 'n_clicks'),
     Input('generate-excel-btn', 'n_clicks'),
     Input('generate-pdf-btn', 'n_clicks'),
     Input('generate-comparison-btn', 'n_clicks')],
    [State('runs-table', 'selected_rows'),
     State('runs-table', 'data')],
    prevent_initial_call=True
)
def handle_table_actions(delete_clicks, export_csv_clicks, excel_clicks, pdf_clicks, comparison_clicks, selected_indices, table_data):
    triggered_id = ctx.triggered_id
    if not triggered_id or not selected_indices:
        return 'Please select one or more runs from the table to perform this action.', 'alert alert-warning', no_update, no_update, no_update, no_update

    # Validate active session
    if not auth.validate_current_session():
        auth.clear_session()
        return 'Session expired. Please log in again.', 'alert alert-error', no_update, no_update, no_update, no_update

    current_user_id = session.get('user_id')
    current_username = session.get('username')
    
    selected_run_ids = [table_data[i]['id'] for i in selected_indices]
    
    # ─── HANDLE DELETE RUNS ───────────────────────────────────────────
    if triggered_id == 'delete-runs-btn':
        # Check permissions
        if not auth.has_permission('runs-reports', 'delete') and not auth.is_admin():
            return 'Access Denied: You do not have permission to delete simulation runs.', 'alert alert-error', no_update, no_update, no_update, no_update
            
        for r_id in selected_run_ids:
            database.delete_run(r_id)
            
        # Log audit event
        database.log_audit_event(
            user_id=current_user_id,
            action='delete_runs',
            target='simulation_runs',
            details=f"User {current_username} deleted {len(selected_run_ids)} simulation runs (IDs: {selected_run_ids})"
        )
        
        return f"Successfully deleted {len(selected_run_ids)} runs.", 'alert alert-success', [], no_update, no_update, no_update
        
    # ─── HANDLE EXPORT CSV ────────────────────────────────────────────
    elif triggered_id == 'export-csv-btn':
        # Check export permission
        if not auth.has_permission('runs-reports', 'export'):
            return 'Access Denied: You do not have permission to export reports.', 'alert alert-error', no_update, no_update, no_update, no_update
            
        selected_runs_data = [table_data[i] for i in selected_indices]
        df = pd.DataFrame(selected_runs_data)
        
        # Log audit event
        database.log_audit_event(
            user_id=current_user_id,
            action='export_csv',
            target='reports',
            details=f"User {current_username} exported {len(selected_run_ids)} runs to CSV"
        )
        
        return 'CSV Export generated.', 'alert alert-success', no_update, dcc.send_data_frame(df.to_csv, "smartflow_runs_export.csv", index=False), no_update, no_update
        
    # ─── HANDLE EXPORT EXCEL ──────────────────────────────────────────
    elif triggered_id == 'generate-excel-btn':
        if not auth.has_permission('runs-reports', 'export'):
            return 'Access Denied: You do not have permission to export reports.', 'alert alert-error', no_update, no_update, no_update, no_update
            
        selected_runs_data = [table_data[i] for i in selected_indices]
        df = pd.DataFrame(selected_runs_data)
        
        # Log audit event
        database.log_audit_event(
            user_id=current_user_id,
            action='export_excel',
            target='reports',
            details=f"User {current_username} exported {len(selected_run_ids)} runs to Excel"
        )
        
        # Return excel file download
        return 'Excel Export generated.', 'alert alert-success', no_update, no_update, dcc.send_data_frame(df.to_excel, "smartflow_runs_export.xlsx", index=False), no_update
        
    # ─── HANDLE GENERATE PDF ──────────────────────────────────────────
    elif triggered_id == 'generate-pdf-btn':
        if not auth.has_permission('runs-reports', 'export'):
            return 'Access Denied: You do not have permission to export reports.', 'alert alert-error', no_update, no_update, no_update, no_update
            
        # Mock generating a PDF file (we can send a simple text file representing the report)
        report_text = f"SMARTFLOW SIMULATION RUNS PDF REPORT\n"
        report_text += f"Generated At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report_text += f"Generated By: {current_username}\n"
        report_text += f"="*50 + "\n\n"
        
        for idx in selected_indices:
            r = table_data[idx]
            report_text += f"Run ID: {r['id']}\n"
            report_text += f"Timestamp: {r['timestamp']}\n"
            report_text += f"Scenario: {r['scenario_name']}\n"
            report_text += f"Control Mode: {r['control_mode']}\n"
            report_text += f"Duration: {r['duration']}\n"
            report_text += f"Status: {r['status']}\n"
            report_text += f"Avg Wait: {r['avg_wait']}\n"
            report_text += f"Max Queue: {r['max_queue']}\n"
            report_text += f"Throughput: {r['throughput']}\n"
            report_text += "-"*50 + "\n"
            
        # Log audit event
        database.log_audit_event(
            user_id=current_user_id,
            action='generate_pdf',
            target='reports',
            details=f"User {current_username} generated a PDF report for {len(selected_run_ids)} runs"
        )
        
        return 'PDF Report generated.', 'alert alert-success', no_update, no_update, no_update, dict(content=report_text, filename="smartflow_pdf_report.pdf")
        
    # ─── HANDLE COMPARISON REPORT ─────────────────────────────────────
    elif triggered_id == 'generate-comparison-btn':
        if not auth.has_permission('runs-reports', 'export'):
            return 'Access Denied: You do not have permission to generate comparison reports.', 'alert alert-error', no_update, no_update, no_update, no_update
            
        if len(selected_run_ids) < 2:
            return 'Please select at least 2 runs to compare.', 'alert alert-warning', no_update, no_update, no_update, no_update
            
        # Log audit event
        database.log_audit_event(
            user_id=current_user_id,
            action='generate_comparison',
            target='reports',
            details=f"User {current_username} generated a comparison report for runs {selected_run_ids}"
        )
        
        # Just download a small mock comparison file
        comp_text = f"SMARTFLOW RUNS COMPARISON REPORT\n"
        comp_text += f"Runs compared: {selected_run_ids}\n\n"
        comp_text += f"ID\tScenario\tMode\tAvg Wait\tThroughput\n"
        for idx in selected_indices:
            r = table_data[idx]
            comp_text += f"{r['id']}\t{r['scenario_name']}\t{r['control_mode']}\t{r['avg_wait']}\t{r['throughput']}\n"
            
        return 'Comparison Report generated.', 'alert alert-success', no_update, no_update, no_update, dict(content=comp_text, filename="runs_comparison.txt")
        
    return '', 'alert alert-info hidden', no_update, no_update, no_update, no_update
