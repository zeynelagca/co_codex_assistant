{
    "name": "Helpdesk Ticket Stage Change History",
    "summary": "Log and report how long tickets stay in each stage",
    "version": "17.0.1.0.0",
    "category": "Helpdesk",
    "website": "https://coflow.com.tr",
    "author": "Coflow Teknoloji",
    "license": "LGPL-3",
    "depends": ["helpdesk"],
    "data": [
        "security/helpdesk_stage_history_security.xml",
       # "security/ir.model.access.csv",
        "views/helpdesk_stage_history_views.xml",
        "data/server_actions.xml"
    ],
    "application": True,
    "installable": True,
    "auto_install":True
}
