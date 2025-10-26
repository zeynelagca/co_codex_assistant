from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    cafeteria_card_ids = fields.One2many(
        'cafeteria.card',
        'partner_id',
        string='Catering Kartları',
    )
