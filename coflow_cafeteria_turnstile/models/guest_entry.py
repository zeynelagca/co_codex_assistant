from odoo import models, fields, api, _

class CafeteriaGuestEntry(models.Model):
    _name = 'cafeteria.guest.entry'
    _description = 'Cafeteria Guest Entry'
    _order = 'entry_date desc, id desc'

    partner_id = fields.Many2one(
        'res.partner',
        string='Company',
        required=True,
        ondelete='restrict',
        help='Misafirin bağlı olduğu firma'
    )
    entry_date = fields.Date(
        string='Entry Date',
        required=True,
        default=fields.Date.context_today,
        help='Misafir giriş tarihi'
    )
    guest_count = fields.Integer(
        string='Guest Count',
        required=True,
        default=1,
        help='Misafir sayısı'
    )
    price = fields.Float(
        string='Unit Price',
        digits=(12, 2),
        help='Kişi başı birim fiyat'
    )
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_total_amount',
        store=True,
        digits=(12, 2),
        help='Toplam tutar (Misafir sayısı × Birim fiyat)'
    )
    invoiced = fields.Boolean(
        string='Invoiced',
        default=False,
        index=True,
        help='Faturalandı mı?'
    )
    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='Invoice Line',
        readonly=True,
        help='İlgili fatura kalemi'
    )
    note = fields.Text(
        string='Note',
        help='Ek notlar'
    )

    @api.depends('guest_count', 'price')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.guest_count * record.price
