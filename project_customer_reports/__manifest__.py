# -*- coding: utf-8 -*-
{
    'name': 'Project Customer Reports',
    'version': '17.0.1.0.0',
    'category': 'Project',
    'summary': 'Send Daily/Weekly Project and Timesheet Reports to Customers',
    'description': """
        This module allows you to:
        - Send daily project task reports to customers
        - Send weekly project task reports to customers
        - Send weekly timesheet reports to customers
        - Reports are generated in XLSX format
        - Automatic scheduling via cron jobs
        - Manual report generation via wizard
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'license': 'LGPL-3',
    'depends': [
        'project',
        'hr_timesheet',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template.xml',
        'data/cron_jobs.xml',
        'views/project_report_config_views.xml',
        'views/send_report_wizard_views.xml',
        'views/project_project_views.xml',

    ],
    'external_dependencies': {
        'python': ['xlsxwriter'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
