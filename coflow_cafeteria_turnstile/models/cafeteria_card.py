from odoo import models, fields

class CafeteriaCard(models.Model):
    _name = 'cafeteria.card'
    _description = 'Turnike Kart (Turnike Kart)'
    _rec_name = 'name'

    name = fields.Char(string='Card UID / Number', required=True, index=True)
    partner_id = fields.Many2one('res.partner', string='Customer / Owner', ondelete='set null')
    card_type = fields.Selection([('prepaid','Ön Ödemeli'),('postpaid','Sonradan Ödemeli')], default='prepaid')
    balance = fields.Float(string='Balance', digits=(12,2), default=0.0)
    active = fields.Boolean(default=True)
    note = fields.Text()
    transaction_count = fields.Integer(string='Pass Count', compute='_compute_transaction_count')

    # Bakiye yükleme ilişkileri
    balance_load_ids = fields.One2many('cafeteria.card.balance.load', 'card_id', string='Bakiye Yüklemeleri')
    balance_load_count = fields.Integer(string='Yükleme Sayısı', compute='_compute_balance_load_count')
    monthly_allocation_ids = fields.One2many('cafeteria.monthly.balance.allocation', 'card_id', string='Aylık Tahsisler')
    monthly_allocation_count = fields.Integer(string='Aylık Tahsis Sayısı', compute='_compute_monthly_allocation_count')

    def _compute_transaction_count(self):
        tx_env = self.env['cafeteria.transaction']
        for rec in self:
            rec.transaction_count = tx_env.search_count([('card_id','=',rec.id)])

    def _compute_balance_load_count(self):
        for rec in self:
            rec.balance_load_count = len(rec.balance_load_ids)

    def _compute_monthly_allocation_count(self):
        for rec in self:
            rec.monthly_allocation_count = len(rec.monthly_allocation_ids)

    def action_view_balance_loads(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bakiye Yüklemeleri',
            'res_model': 'cafeteria.card.balance.load',
            'view_mode': 'tree,form',
            'domain': [('card_id', '=', self.id)],
            'context': {'default_card_id': self.id}
        }

    def action_view_monthly_allocations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Aylık Tahsisler',
            'res_model': 'cafeteria.monthly.balance.allocation',
            'view_mode': 'tree,form',
            'domain': [('card_id', '=', self.id)],
            'context': {'default_card_id': self.id}
        }