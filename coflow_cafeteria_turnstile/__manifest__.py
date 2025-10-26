{
    "name": "Restaurant Turnike (ZKTeco K70)Entegrasyonu",
    "version": "17.0.10.0.0",
    "summary": "Yemekhane turnike kartları, geçiş kayıtları ve müşteri bazlı faturalama",
    "description": "ZKTeco K70 ile entegrasyon; kart yönetimi; aylık fatura; partner sekmesi ve raporlar.",
    "category": "Operations/Attendance",
    "author": "Coflow Teknoloji",
    "website": "https://coflow.com.tr",
    "license": "LGPL-3",
    "depends": ["base", "account", "product", "mail"],
    "data": [
        "views/wizard_views.xml",
        "views/card_views.xml",
        "views/transaction_views.xml",
        "views/partner_views.xml",
        "views/guest_entry_views.xml",
        "views/balance_load_views.xml",
        "security/ir.model.access.csv",
        "views/menu.xml",
        "data/cron_jobs.xml"
    ],
    "installable": True,
    "application": True,
    "auto_install":True
}