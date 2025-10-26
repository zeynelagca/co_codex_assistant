from collections import defaultdict

from odoo import models, fields, api, _


class CafeteriaInvoiceWizard(models.TransientModel):
    _name = 'cafeteria.invoice.wizard'
    _description = 'Catering geçişleri için aylık fatura oluşturma sihirbazı'

    partner_id = fields.Many2one('res.partner', string='Müşteri', required=True)
    date_from = fields.Date(string='Başlangıç Tarihi', required=True)
    date_to = fields.Date(string='Bitiş Tarihi', required=True)
    product_id = fields.Many2one(
        'product.product',
        string='Fatura Ürünü',
        help='Opsiyonel. Seçilirse bütün geçişler tek satır ve adet olarak faturalandırılır.',
    )

    include_guest_entries = fields.Boolean(
        string='Misafir Girişlerini Dahil Et',
        default=True,
        help='Misafir giriş kayıtlarını faturaya ekle.',
    )
    guest_product_id = fields.Many2one(
        'product.product',
        string='Misafir Ürünü',
        help='Misafir girişleri için kullanılacak ürün.',
    )

    transaction_count = fields.Integer(
        string='Kart Geçiş Sayısı',
        compute='_compute_statistics',
    )
    transaction_total = fields.Float(
        string='Kart Geçiş Toplamı',
        compute='_compute_statistics',
        digits=(12, 2),
    )
    guest_entry_count = fields.Integer(
        string='Misafir Giriş Sayısı',
        compute='_compute_statistics',
    )
    guest_total = fields.Float(
        string='Misafir Toplamı',
        compute='_compute_statistics',
        digits=(12, 2),
    )
    grand_total = fields.Float(
        string='Genel Toplam',
        compute='_compute_statistics',
        digits=(12, 2),
    )

    @api.depends('partner_id', 'date_from', 'date_to', 'include_guest_entries')
    def _compute_statistics(self):
        for wizard in self:
            if not wizard.partner_id or not wizard.date_from or not wizard.date_to:
                wizard.transaction_count = 0
                wizard.transaction_total = 0.0
                wizard.guest_entry_count = 0
                wizard.guest_total = 0.0
                wizard.grand_total = 0.0
                continue

            tx_model = self.env['cafeteria.transaction']
            tx_domain = [
                ('partner_id', '=', wizard.partner_id.id),
                ('timestamp', '>=', fields.Datetime.to_datetime(wizard.date_from)),
                ('timestamp', '<=', fields.Datetime.to_datetime(wizard.date_to)),
                ('invoiced', '=', False),
            ]
            txs = tx_model.search(tx_domain)
            wizard.transaction_count = len(txs)
            wizard.transaction_total = sum(txs.mapped('price'))

            if wizard.include_guest_entries:
                guest_model = self.env['cafeteria.guest.entry']
                guest_domain = [
                    ('partner_id', '=', wizard.partner_id.id),
                    ('entry_date', '>=', wizard.date_from),
                    ('entry_date', '<=', wizard.date_to),
                    ('invoiced', '=', False),
                ]
                guests = guest_model.search(guest_domain)
                wizard.guest_entry_count = sum(guests.mapped('guest_count'))
                wizard.guest_total = sum(guests.mapped('total_amount'))
            else:
                wizard.guest_entry_count = 0
                wizard.guest_total = 0.0

            wizard.grand_total = wizard.transaction_total + wizard.guest_total

    def action_generate_invoice(self):
        self.ensure_one()

        tx_model = self.env['cafeteria.transaction']
        tx_domain = [
            ('partner_id', '=', self.partner_id.id),
            ('timestamp', '>=', fields.Datetime.to_datetime(self.date_from)),
            ('timestamp', '<=', fields.Datetime.to_datetime(self.date_to)),
            ('invoiced', '=', False),
        ]
        txs = tx_model.search(tx_domain, order='timestamp asc')

        guest_model = self.env['cafeteria.guest.entry']
        guests = guest_model.browse()
        if self.include_guest_entries:
            guest_domain = [
                ('partner_id', '=', self.partner_id.id),
                ('entry_date', '>=', self.date_from),
                ('entry_date', '<=', self.date_to),
                ('invoiced', '=', False),
            ]
            guests = guest_model.search(guest_domain, order='entry_date asc')

        if not txs and not guests:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Kayıt bulunamadı'),
                    'message': _('Bu dönem için faturalanmamış kart geçişi veya misafir girişi bulunamadı.'),
                    'type': 'warning',
                },
            }

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [],
        }

        if txs:
            if self.product_id:
                total_count = len(txs)
                invoice_vals['invoice_line_ids'].append((0, 0, {
                    'name': _('Kart Geçişleri (%s - %s)') % (self.date_from, self.date_to),
                    'product_id': self.product_id.id,
                    'quantity': total_count,
                    'price_unit': self.product_id.list_price,
                }))
            else:
                grouped = defaultdict(lambda: {'count': 0, 'sum': 0.0, 'card': False})
                for t in txs:
                    key = t.card_id.id
                    grouped[key]['count'] += 1
                    grouped[key]['sum'] += t.price or 0.0
                    grouped[key]['card'] = t.card_id

                for group in grouped.values():
                    name = _('Kart: %s - %s geçiş') % (group['card'].name, group['count'])
                    invoice_vals['invoice_line_ids'].append((0, 0, {
                        'name': name,
                        'quantity': 1,
                        'price_unit': group['sum'],
                    }))

        if guests:
            if self.guest_product_id:
                total_guest_count = sum(guests.mapped('guest_count'))
                total_guest_amount = sum(guests.mapped('total_amount'))
                price_unit = total_guest_amount / total_guest_count if total_guest_count else 0
                invoice_vals['invoice_line_ids'].append((0, 0, {
                    'name': _('Misafir Girişleri (%s - %s)') % (self.date_from, self.date_to),
                    'product_id': self.guest_product_id.id,
                    'quantity': total_guest_count,
                    'price_unit': price_unit,
                }))
            else:
                guest_grouped = defaultdict(lambda: {'count': 0, 'sum': 0.0})
                for guest in guests:
                    date_key = guest.entry_date.strftime('%Y-%m-%d')
                    guest_grouped[date_key]['count'] += guest.guest_count
                    guest_grouped[date_key]['sum'] += guest.total_amount

                for date_key, data in guest_grouped.items():
                    name = _('Misafir Girişi (%s) - %s kişi') % (date_key, data['count'])
                    invoice_vals['invoice_line_ids'].append((0, 0, {
                        'name': name,
                        'quantity': 1,
                        'price_unit': data['sum'],
                    }))

        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()

        invoice_line_id = invoice.invoice_line_ids[0].id if invoice.invoice_line_ids else False

        if txs:
            txs.write({
                'invoiced': True,
                'invoice_line_id': invoice_line_id,
            })

        if guests:
            guests.write({
                'invoiced': True,
                'invoice_line_id': invoice_line_id,
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
