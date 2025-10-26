from odoo import models, fields, api


class CafeteriaGuestEntry(models.Model):
    _name = 'cafeteria.guest.entry'
    _description = 'Catering Misafir Girişi'
    _order = 'entry_date desc, id desc'

    partner_id = fields.Many2one(
        'res.partner',
        string='Firma',
        required=True,
        ondelete='restrict',
        help='Misafirin bağlantılı olduğu firma',
    )
    entry_date = fields.Date(
        string='Giriş Tarihi',
        required=True,
        default=fields.Date.context_today,
        help='Misafir girişinin gerçekleştiği tarih',
    )
    guest_count = fields.Integer(
        string='Misafir Sayısı',
        required=True,
        default=1,
        help='Toplam misafir adedi',
    )
    price = fields.Float(
        string='Birim Fiyat',
        digits=(12, 2),
        help='Kişi başına birim fiyat',
    )
    total_amount = fields.Float(
        string='Toplam Tutar',
        compute='_compute_total_amount',
        store=True,
        digits=(12, 2),
        help='Misafir sayısı ile birim fiyatın çarpımı',
    )
    invoiced = fields.Boolean(
        string='Faturalandı',
        default=False,
        index=True,
        help='Kayıt faturaya dahil edildi mi?',
    )
    invoice_line_id = fields.Many2one(
        'account.move.line',
        string='İlgili Fatura Kalemi',
        readonly=True,
        help='Kayıt faturaya işlendiğinde ilişkilendirilen satır',
    )
    note = fields.Text(
        string='Not',
        help='Ek açıklamalar',
    )

    @api.depends('guest_count', 'price')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.guest_count * record.price
