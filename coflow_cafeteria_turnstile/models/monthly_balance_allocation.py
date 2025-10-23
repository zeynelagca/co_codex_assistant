# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class MonthlyBalanceAllocation(models.Model):
    _name = 'cafeteria.monthly.balance.allocation'
    _description = 'Aylık Bakiye Tahsisi'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'allocation_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(string='İsim', compute='_compute_display_name', store=True)

    card_id = fields.Many2one('cafeteria.card', string='Kart', required=True, ondelete='restrict')
    partner_id = fields.Many2one('res.partner', string='Müşteri', related='card_id.partner_id', store=True, readonly=True)

    monthly_amount = fields.Float(string='Aylık Tutar', required=True, digits=(12, 2))
    allocation_day = fields.Integer(string='Ayın Günü', default=1, help='Her ayın kaçıncı günü yüklenecek (1-28)')

    start_date = fields.Date(string='Başlangıç Tarihi', required=True, default=fields.Date.today)
    end_date = fields.Date(string='Bitiş Tarihi', help='Boş bırakılırsa süresiz devam eder')

    allocation_date = fields.Date(string='Son Yükleme Tarihi', readonly=True, help='Son otomatik yükleme tarihi')
    next_allocation_date = fields.Date(string='Sonraki Yükleme', compute='_compute_next_allocation_date', store=True)

    active = fields.Boolean(string='Aktif', default=True)
    state = fields.Selection([
        ('active', 'Aktif'),
        ('suspended', 'Askıya Alındı'),
        ('completed', 'Tamamlandı'),
    ], string='Durum', default='active', required=True)

    load_ids = fields.One2many('cafeteria.card.balance.load', 'monthly_allocation_id', string='Yüklemeler')
    load_count = fields.Integer(string='Yükleme Sayısı', compute='_compute_load_count')

    note = fields.Text(string='Açıklama')

    @api.depends('card_id', 'monthly_amount', 'allocation_day')
    def _compute_display_name(self):
        for rec in self:
            if rec.card_id:
                rec.display_name = f"{rec.card_id.name} - Aylık {rec.monthly_amount} TL (Her ayın {rec.allocation_day})"
            else:
                rec.display_name = "Yeni Aylık Tahsis"

    @api.depends('allocation_date', 'start_date', 'allocation_day', 'state')
    def _compute_next_allocation_date(self):
        for rec in self:
            if rec.state != 'active':
                rec.next_allocation_date = False
                continue

            today = fields.Date.today()
            if rec.allocation_date:
                # Son yüklemeden sonraki ayı hesapla
                last_date = rec.allocation_date
                next_month = last_date + relativedelta(months=1)
            else:
                # İlk yükleme tarihi
                next_month = rec.start_date if rec.start_date > today else today

            # Ayın belirtilen gününe ayarla
            try:
                next_allocation = next_month.replace(day=rec.allocation_day)
            except ValueError:
                # Örneğin 31. gün olmayan aylarda ayın son günü
                next_allocation = next_month + relativedelta(day=31)

            # Bitiş tarihi kontrolü
            if rec.end_date and next_allocation > rec.end_date:
                rec.next_allocation_date = False
            else:
                rec.next_allocation_date = next_allocation

    @api.depends('load_ids')
    def _compute_load_count(self):
        for rec in self:
            rec.load_count = len(rec.load_ids)

    @api.constrains('allocation_day')
    def _check_allocation_day(self):
        for rec in self:
            if not (1 <= rec.allocation_day <= 28):
                raise ValidationError(_('Ayın günü 1-28 arasında olmalıdır!'))

    @api.constrains('monthly_amount')
    def _check_monthly_amount(self):
        for rec in self:
            if rec.monthly_amount <= 0:
                raise ValidationError(_('Aylık tutar sıfırdan büyük olmalıdır!'))

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.end_date and rec.start_date > rec.end_date:
                raise ValidationError(_('Bitiş tarihi başlangıç tarihinden önce olamaz!'))

    def action_suspend(self):
        """Aylık tahsisi askıya al"""
        self.write({'state': 'suspended', 'active': False})

    def action_activate(self):
        """Aylık tahsisi aktif et"""
        self.write({'state': 'active', 'active': True})

    def action_complete(self):
        """Aylık tahsisi tamamla"""
        self.write({'state': 'completed', 'active': False})

    def action_process_monthly_allocations(self):
        """Aylık tahsisleri işle (Cron job)"""
        today = fields.Date.today()

        allocations = self.search([
            ('state', '=', 'active'),
            ('next_allocation_date', '<=', today),
        ])

        load_env = self.env['cafeteria.card.balance.load']

        for allocation in allocations:
            # Aylık yükleme oluştur
            month_period = today.strftime('%Y-%m')

            load = load_env.create({
                'card_id': allocation.card_id.id,
                'load_type': 'monthly',
                'amount': allocation.monthly_amount,
                'load_date': fields.Datetime.now(),
                'month_period': month_period,
                'monthly_allocation_id': allocation.id,
                'note': f'Aylık otomatik yükleme - {month_period}',
            })

            # Otomatik onayla
            load.action_confirm()

            # Son yükleme tarihini güncelle
            allocation.allocation_date = today

            # Bitiş tarihi kontrolü
            if allocation.end_date and today >= allocation.end_date:
                allocation.action_complete()

    def action_view_loads(self):
        """İlişkili yüklemeleri göster"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bakiye Yüklemeleri'),
            'res_model': 'cafeteria.card.balance.load',
            'view_mode': 'tree,form',
            'domain': [('monthly_allocation_id', '=', self.id)],
            'context': {'default_monthly_allocation_id': self.id, 'default_card_id': self.card_id.id}
        }
