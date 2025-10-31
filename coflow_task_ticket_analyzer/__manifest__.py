{
    'name': 'CoFlow Task Ticket Analyzer',
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': 'CoFlow AI-powered task and ticket analysis with automatic complexity scoring and solution suggestions',
    'description': """
        CoFlow Task Ticket Analyzer
        ===========================

        Features:
        ---------
        * Automatic analysis of project tasks and helpdesk tickets
        * AI-powered complexity scoring using Claude MCP
        * Intelligent solution suggestions
        * GitHub integration for automatic code development
        * Historical analysis of similar tasks/tickets
        * Code complexity analysis
        * Multiple trigger methods: manual, automatic, scheduled, stage-based

        This module uses CoFlow AI services to analyze tasks and tickets, providing:
        - Complexity score (1-10)
        - Estimated time to resolve
        - Suggested solutions
        - Automatic code generation for simple tasks
        - GitHub integration for code commits
    """,
    'author': 'CoFlow, Ali Zeynel Ağca',
    'website': 'https://www.coflow.com.tr',
    'maintainer': 'Ali Zeynel Ağca',
    'depends': [
        'base',
        'project',
        'odoo_website_helpdesk',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/scheduled_actions.xml',
        'views/project_project_views.xml',
        'views/project_task_views.xml',
        'views/helpdesk_ticket_views.xml',
        'views/res_partner_views.xml',
        'views/ai_analysis_history_views.xml',
    ],
    'external_dependencies': {
        'python': ['anthropic', 'github', 'requests'],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
