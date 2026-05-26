"""
SMARTFLOW — Help & About Page
System guide, metrics glossary, FAQ, and platform specifications.
"""

from dash import html
import auth
from components.header import create_header
from components.sidebar import create_sidebar
from components.common import create_section


# ─── Data ──────────────────────────────────────────────────────────

QUICK_START_STEPS = [
    {
        'title': 'Choose a Scenario',
        'icon': 'fas fa-map-location-dot',
        'desc': 'Navigate to the Scenarios tab to choose a preset intersection '
                'or configure custom traffic conditions.',
    },
    {
        'title': 'Select Control Mode',
        'icon': 'fas fa-sliders',
        'desc': 'Go to the Simulation Control panel to select either '
                'Fixed-Time or AI Agent control modes.',
    },
    {
        'title': 'Run the Simulation',
        'icon': 'fas fa-play',
        'desc': 'Click the Start button to execute the simulation in '
                'real time and observe the intersection.',
    },
    {
        'title': 'Monitor Metrics',
        'icon': 'fas fa-chart-line',
        'desc': 'Observe queue lengths, wait times, and throughput in '
                'the live telemetry grid and Performance tab.',
    },
    {
        'title': 'Export Reports',
        'icon': 'fas fa-file-export',
        'desc': 'Export comprehensive reports to PDF or Excel from the '
                'Runs & Reports history table.',
    },
]

METRICS = [
    {
        'title': 'Average Waiting Time',
        'icon': 'fas fa-hourglass-half',
        'color': 'var(--warning)',
        'desc': 'The average duration (in seconds) a vehicle spends at a '
                'complete stop in a queue before crossing the intersection.',
    },
    {
        'title': 'Average Queue Length',
        'icon': 'fas fa-car-side',
        'color': 'var(--info)',
        'desc': 'The average number of vehicles queued in a lane during '
                'a signal phase cycle.',
    },
    {
        'title': 'Maximum Queue Length',
        'icon': 'fas fa-traffic-light',
        'color': 'var(--error)',
        'desc': 'The peak count of vehicles waiting in any approach lane '
                'during a run, helpful to identify bottleneck approaches.',
    },
    {
        'title': 'Throughput',
        'icon': 'fas fa-gauge-high',
        'color': 'var(--success)',
        'desc': 'The rate of vehicles completing their journey and exiting '
                'the network per hour (veh/h).',
    },
    {
        'title': 'Emergency Clearance',
        'icon': 'fas fa-truck-medical',
        'color': 'var(--purple)',
        'desc': 'Indicates if emergency vehicles (ambulances, fire trucks) '
                'are successfully prioritized, bypassing standard cycles.',
    },
    {
        'title': 'CO₂ Emissions',
        'icon': 'fas fa-leaf',
        'color': 'var(--accent)',
        'desc': 'Estimated emissions based on vehicle wait times and '
                'stop-and-go patterns. Lower is better.',
    },
]

FAQS = [
    {
        'q': 'How is the AI reinforcement learning model trained?',
        'a': 'The AI agent uses Deep Q-Networks (DQN) to select signal phases. '
             'It receives a reward based on minimizing total cumulative waiting '
             'times and queue lengths at the intersection, learning optimal '
             'policies over successive episodes.',
    },
    {
        'q': 'Can I run multiple simulations at the same time?',
        'a': 'SMARTFLOW is designed to execute one live simulation run per '
             'session to ensure reliable performance on local engines. However, '
             'you can compare results of multiple completed runs side-by-side '
             'in the Runs & Reports tab.',
    },
    {
        'q': 'What happens if a user account is pending?',
        'a': 'Default registration puts new accounts in a "Pending Approval" '
             'state. An administrator must explicitly approve the account via '
             'the User Management panel before the user can log in.',
    },
    {
        'q': 'How does Fixed-Time control differ from AI?',
        'a': 'Fixed-Time control uses pre-programmed, static phase durations '
             'regardless of live traffic volume. The AI Agent dynamically '
             'adjusts phase durations in real-time based on the current '
             'vehicles queued at each approach.',
    },
    {
        'q': 'How do I export simulation reports?',
        'a': 'Navigate to the Runs & Reports page. Select one or more '
             'completed simulation runs, then click Export. Reports can be '
             'generated in PDF and Excel formats for further analysis.',
    },
]

SYSTEM_SPECS = [
    ('App Version',       'v1.0.0 (Build 2026.05)'),
    ('Simulation Engine', 'SUMO (Simulation of Urban MObility)'),
    ('Interface Protocol','TraCI (Traffic Control Interface)'),
    ('Database',          'SQLite3 with WAL mode'),
    ('AI Architecture',   'Deep Q-Network (PyTorch)'),
    ('Authentication',    'Werkzeug PBKDF2:sha256'),
    ('Frontend Framework','Plotly Dash Native Components'),
    ('Target Area',       'Tagum City Traffic Intersections'),
]


# ─── Section Builders ──────────────────────────────────────────────

def _build_quick_start():
    """Getting Started — numbered step cards."""
    return create_section(
        title='Getting Started',
        icon='fas fa-rocket',
        subtitle='Follow these steps to run your first simulation experiment.',
        children=[
            html.Div(
                className='help-steps-grid',
                children=[
                    html.Div(className='help-step-card', children=[
                        html.Div(str(i + 1), className='help-step-number'),
                        html.Div(className='help-step-icon', children=[
                            html.I(className=step['icon']),
                        ]),
                        html.H4(step['title'], className='help-step-title'),
                        html.P(step['desc'], className='help-step-desc'),
                    ])
                    for i, step in enumerate(QUICK_START_STEPS)
                ],
            ),
        ],
    )


def _build_glossary():
    """Traffic Metrics Glossary — icon cards in a grid."""
    return create_section(
        title='Traffic Metrics Glossary',
        icon='fas fa-book',
        subtitle='Key performance indicators used to evaluate intersection efficiency.',
        children=[
            html.Div(
                className='help-glossary-grid',
                children=[
                    html.Div(className='help-glossary-card', children=[
                        html.Div(
                            className='help-glossary-icon',
                            style={
                                'color': m['color'],
                                'background': f"color-mix(in srgb, {m['color']} 10%, transparent)",
                                'border': f"1px solid color-mix(in srgb, {m['color']} 18%, transparent)",
                            },
                            children=[html.I(className=m['icon'])],
                        ),
                        html.Div(className='help-glossary-body', children=[
                            html.H4(m['title']),
                            html.P(m['desc']),
                        ]),
                    ])
                    for m in METRICS
                ],
            ),
        ],
    )


def _build_faq():
    """FAQ — native <details> accordion, no callbacks needed."""
    return create_section(
        title='Frequently Asked Questions',
        icon='fas fa-circle-question',
        subtitle='Answers to common questions about the platform and AI operations.',
        children=[
            html.Div(
                className='help-faq-list',
                children=[
                    html.Details(className='help-faq-item', children=[
                        html.Summary(faq['q'], className='help-faq-question'),
                        html.Div(faq['a'], className='help-faq-answer'),
                    ])
                    for faq in FAQS
                ],
            ),
        ],
    )


def _build_system_info():
    """System Specifications — clean spec table + callout."""
    return create_section(
        title='System Specifications',
        icon='fas fa-microchip',
        subtitle='Technical details about the SMARTFLOW architecture.',
        children=[
            html.Div(
                className='help-specs-wrap',
                children=[
                    html.Table(className='help-specs-table', children=[
                        html.Tbody([
                            html.Tr([
                                html.Th(label),
                                html.Td(value),
                            ])
                            for label, value in SYSTEM_SPECS
                        ]),
                    ]),
                ],
            ),
            html.Div(className='help-callout', children=[
                html.I(className='fas fa-lightbulb'),
                html.Span(
                    'SMARTFLOW is designed to support AI-driven traffic '
                    'optimization research, facilitating decisions on physical '
                    'road structures and reinforcement learning algorithms.'
                ),
            ]),
        ],
    )


# ─── Page Layout ───────────────────────────────────────────────────

def layout():
    if not auth.is_authenticated():
        return html.Div()

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
                            # Page header
                            html.Div(
                                className='page-header',
                                children=[
                                    html.H1('Help & Documentation'),
                                    html.P(
                                        'Learn how to run traffic simulation '
                                        'experiments, understand key metrics, '
                                        'and explore the AI behind the scenes.'
                                    ),
                                ],
                            ),

                            # Two-column top row
                            html.Div(
                                className='help-top-row',
                                children=[
                                    _build_quick_start(),
                                    _build_system_info(),
                                ],
                            ),

                            # Full-width glossary
                            _build_glossary(),

                            # Full-width FAQ
                            _build_faq(),
                        ],
                    ),
                ],
            ),
        ],
    )
