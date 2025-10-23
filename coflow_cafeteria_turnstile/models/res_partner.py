from odoo import models, fields, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    cafeteria_card_ids = fields.One2many('cafeteria.card', 'partner_id', string='Cafeteria Cards')