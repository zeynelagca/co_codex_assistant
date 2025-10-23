from odoo import models, fields, api, _
from datetime import datetime

class CafeteriaTransaction(models.Model):
    _name = 'cafeteria.transaction'
    _description = 'Cafeteria Turnstile Transaction'
    _order = 'timestamp desc'

    card_id = fields.Many2one('cafeteria.card', string='Card', required=True, ondelete='restrict')
    card_uid = fields.Char(related='card_id.name', store=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related='card_id.partner_id', store=True)
    timestamp = fields.Datetime(string='Timestamp', required=True, default=lambda self: fields.Datetime.now())
    device_ip = fields.Char(string='Device IP')
    device_sn = fields.Char(string='Device SN')
    price = fields.Float(string='Price', digits=(12,2))
    invoiced = fields.Boolean(default=False, index=True)
    invoice_line_id = fields.Many2one('account.move.line', string='Invoice Line', readonly=True)
    balance_load_id = fields.Many2one('cafeteria.card.balance.load', string='Bakiye Yüklemesi', ondelete='set null')

    def _cron_fetch_zk_transactions(self):
        # Placeholder: implement ZKTeco K70 fetch and create records here.
        # Example pseudo:
        # for device in configured_devices:
        #   for evt in zk_client.fetch(device):
        #       card = self.env['cafeteria.card'].search([('name','=',evt.uid)], limit=1)
        #       if not card:
        #           continue
        #       self.create({
        #           'card_id': card.id,
        #           'timestamp': evt.ts,
        #           'device_ip': device.ip,
        #           'price': card.card_type == 'postpaid' and device.default_price or 0.0,
        #       })
        return True