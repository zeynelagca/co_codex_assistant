from odoo import models, fields, api, _
from collections import defaultdict

class CafeteriaInvoiceWizard(models.TransientModel):
    _name = 'cafeteria.invoice.wizard'
    _description = 'Generate monthly invoices for cafeteria passes'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    date_from = fields.Date(string='From', required=True)
    date_to = fields.Date(string='To', required=True)
    product_id = fields.Many2one('product.product', string='Invoice Product', required=False, help='Opsiyonel. Seçerseniz her geçiş satır yerine tek kalem x adet olarak faturalandırılır.')

    def action_generate_invoice(self):
        self.ensure_one()
        tx_model = self.env['cafeteria.transaction']
        domain = [
            ('partner_id','=',self.partner_id.id),
            ('timestamp','>=',fields.Datetime.to_datetime(self.date_from)),
            ('timestamp','<=',fields.Datetime.to_datetime(self.date_to)),
            ('invoiced','=',False),
        ]
        txs = tx_model.search(domain, order='timestamp asc')
        if not txs:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': _('No transactions'), 'message': _('No transactions found for this period.'), 'type': 'warning'}
            }

        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [],
        }

        if self.product_id:
            total_count = len(txs)
            invoice_vals['invoice_line_ids'].append((0,0,{
                'name': _('Cafeteria Passes (%s - %s)') % (self.date_from, self.date_to),
                'product_id': self.product_id.id,
                'quantity': total_count,
                'price_unit': self.product_id.list_price,
            }))
        else:
            grouped = defaultdict(lambda: {'count':0,'sum':0.0,'card':False})
            for t in txs:
                key = t.card_id.id
                grouped[key]['count'] += 1
                grouped[key]['sum'] += t.price or 0.0
                grouped[key]['card'] = t.card_id
            for g in grouped.values():
                name = _('Card %s - %s passes') % (g['card'].name, g['count'])
                invoice_vals['invoice_line_ids'].append((0,0,{
                    'name': name,
                    'quantity': 1,
                    'price_unit': g['sum'],
                }))

        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()

        for t in txs:
            t.write({'invoiced': True, 'invoice_line_id': invoice.invoice_line_ids[:1].id if invoice.invoice_line_ids else False})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }