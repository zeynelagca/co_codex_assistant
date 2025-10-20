# -*- coding: utf-8 -*-
{
    'name': 'Etkinlik Talep Modülü (HR)',
    'summary': 'Personeller için etkinlik katılım taleplerini toplayın ve yönetin.',
    'version': '17.0.99.0.0',
    'category': 'Human Resources/Employees',
    'license': 'LGPL-3',
    'author': 'Coflow Teknoloji',
    'website': 'https://coflow.com.tr',
    'depends': ['base', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/event_request_data.xml',
        'views/event_request_views.xml',
    ],
    'application': True,
    'installable': True,
}
