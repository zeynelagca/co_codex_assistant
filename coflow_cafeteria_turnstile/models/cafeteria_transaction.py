from odoo import models, fields, api, _


class CafeteriaTransaction(models.Model):
    _name = 'cafeteria.transaction'
    _description = 'Catering Turnike İşlemi'
    _order = 'timestamp desc'

    card_id = fields.Many2one(
        'cafeteria.card',
        string='Kart',
        required=True,
        ondelete='restrict',
    )
    card_uid = fields.Char(related='card_id.name', store=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Müşteri',
        related='card_id.partner_id',
        store=True,
    )
    timestamp = fields.Datetime(
        string='Geçiş Zamanı',
        required=True,
        default=lambda self: fields.Datetime.now(),
    )
    device_ip = fields.Char(string='Cihaz IP')
    device_sn = fields.Char(string='Cihaz Seri No')
    price = fields.Float(string='Tutar', digits=(12, 2))
    invoiced = fields.Boolean(string='Faturalandı', default=False, index=True)
    invoice_line_id = fields.Many2one('account.move.line', string='Fatura Satırı', readonly=True)
    balance_load_id = fields.Many2one(
        'cafeteria.card.balance.load',
        string='Bakiye Yüklemesi',
        ondelete='set null',
    )

    def _cron_fetch_zk_transactions(self):
        """ZKTeco K70 cihazlarından turnike geçişlerini alıp kaydeder."""
        # TODO: Cihaz entegrasyonu burada gerçekleştirilecek.
        return True
