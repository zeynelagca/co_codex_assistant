# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class CardBalanceLoad(models.Model):
    _name = 'cafeteria.card.balance.load'
    _description = 'Kart Bakiye Yükleme'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'load_date desc, id desc'
    _rec_name = 'display_name'

    display_name = fields.Char(string='İsim', compute='_compute_display_name', store=True)
    card_id = fields.Many2one('cafeteria.card', string='Kart', required=True, ondelete='restrict')
    partner_id = fields.Many2one('res.partner', string='Müşteri', related='card_id.partner_id', store=True, readonly=True)
    load_type = fields.Selection([
        ('manual', 'Manuel Yükleme'),
        ('monthly', 'Aylık Otomatik'),
    ], string='Yükleme Tipi', required=True, default='manual')

    load_date = fields.Datetime(string='Yükleme Tarihi', required=True, default=fields.Datetime.now)
    amount = fields.Float(string='Yüklenen Tutar', required=True, digits=(12, 2))

    # Aylık yükleme için
    month_period = fields.Char(string='Dönem (YYYY-MM)', help='Aylık yükleme için ay dönemi')
    monthly_allocation_id = fields.Many2one('cafeteria.monthly.balance.allocation', string='Aylık Tahsis', ondelete='set null')

    # Bakiye takibi
    balance_before = fields.Float(string='Önceki Bakiye', digits=(12, 2), readonly=True)
    balance_after = fields.Float(string='Sonraki Bakiye', digits=(12, 2), readonly=True)

    # Kullanım takibi
    used_amount = fields.Float(string='Kullanılan Tutar', compute='_compute_used_amount', store=True, digits=(12, 2))
    remaining_amount = fields.Float(string='Kalan Bakiye', compute='_compute_remaining_amount', store=True, digits=(12, 2))
    transaction_count = fields.Integer(string='İşlem Sayısı', compute='_compute_transaction_stats', store=True)

    # Durum
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('confirmed', 'Onaylandı'),
        ('cancelled', 'İptal Edildi'),
    ], string='Durum', default='draft', required=True, tracking=True)

    # Açıklama
    note = fields.Text(string='Açıklama')

    # İlişkili işlemler
    transaction_ids = fields.One2many('cafeteria.transaction', 'balance_load_id', string='İşlemler')

    @api.depends('card_id', 'amount', 'load_date')
    def _compute_display_name(self):
        for rec in self:
            if rec.card_id and rec.load_date:
                date_str = fields.Datetime.context_timestamp(rec, rec.load_date).strftime('%d/%m/%Y')
                rec.display_name = f"{rec.card_id.name} - {rec.amount} TL ({date_str})"
            else:
                rec.display_name = "Yeni Bakiye Yükleme"

    @api.depends('transaction_ids', 'transaction_ids.price')
    def _compute_used_amount(self):
        for rec in self:
            if rec.transaction_ids:
                rec.used_amount = sum(rec.transaction_ids.mapped('price'))
            else:
                rec.used_amount = 0.0

    @api.depends('amount', 'used_amount')
    def _compute_remaining_amount(self):
        for rec in self:
            rec.remaining_amount = rec.amount - rec.used_amount

    @api.depends('transaction_ids')
    def _compute_transaction_stats(self):
        for rec in self:
            rec.transaction_count = len(rec.transaction_ids)

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('Yüklenen tutar sıfırdan büyük olmalıdır!'))

    def action_confirm(self):
        """Bakiye yüklemeyi onayla ve kart bakiyesini güncelle"""
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('Sadece taslak durumundaki yüklemeler onaylanabilir!'))

            # Önceki bakiyeyi kaydet
            rec.balance_before = rec.card_id.balance

            # Kart bakiyesini güncelle
            rec.card_id.balance += rec.amount

            # Sonraki bakiyeyi kaydet
            rec.balance_after = rec.card_id.balance

            # Durumu güncelle
            rec.state = 'confirmed'

    def action_cancel(self):
        """Bakiye yüklemeyi iptal et"""
        for rec in self:
            if rec.state == 'cancelled':
                raise ValidationError(_('Zaten iptal edilmiş!'))

            if rec.state == 'confirmed':
                # İlişkili işlem varsa iptal edilemez
                if rec.transaction_ids:
                    raise ValidationError(
                        _('Bu bakiye yüklemesine ait işlemler bulunmaktadır! '
                          'İptal etmek için önce işlemleri kaldırmanız gerekir.')
                    )

                # Bakiyeyi geri al
                rec.card_id.balance -= rec.amount

            rec.state = 'cancelled'

    def action_set_to_draft(self):
        """Taslağa geri al"""
        for rec in self:
            if rec.state != 'cancelled':
                raise ValidationError(_('Sadece iptal edilmiş kayıtlar taslağa alınabilir!'))
            rec.state = 'draft'

    def action_view_transactions(self):
        """İlişkili işlemleri göster"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('İşlemler'),
            'res_model': 'cafeteria.transaction',
            'view_mode': 'tree,form',
            'domain': [('balance_load_id', '=', self.id)],
            'context': {'default_balance_load_id': self.id, 'default_card_id': self.card_id.id}
        }
