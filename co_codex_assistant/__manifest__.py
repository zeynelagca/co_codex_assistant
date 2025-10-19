{
    'name': 'Coflow Codex Assistant',
    'summary': 'Use a configurable LLM (Codex) to assist in Discuss and Helpdesk (reply drafting & reporting)',
    'version': '17.0.2.0.0',
    'category': 'Productivity',
    'license': 'LGPL-3',
    'author': 'Coflow Teknoloji',
    'website': 'https://coflow.com.tr',
    'live_test_url': 'https://coflow.com.tr',
    'depends': ['base', 'base_setup', 'mail', 'helpdesk'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_config_settings_rag_views.xml',
        'views/codex_document_views.xml',
        'data/cron.xml',
        'views/codex_history_views.xml',
        'views/helpdesk_views.xml',
        'views/mail_channel_views.xml',
        'wizard/codex_generate_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
        ],
    },
    'installable': True,
    'application': False,
}
