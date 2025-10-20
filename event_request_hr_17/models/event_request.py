# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class EventType(models.Model):
    _name = "event.request.type"
    _description = "Event Type"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()

class AttendanceStatus(models.Model):
    _name = "event.request.attendance.status"
    _description = "Attendance Status"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()

class AccessOption(models.Model):
    _name = "event.request.access.option"
    _description = "Access Option"
    _order = "name"

    name = fields.Char(required=True)
    code = fields.Char()

class EventRequest(models.Model):
    _name = "event.request"
    _description = "Etkinlik Talebi"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "event_name"
    _order = "event_date desc, id desc"

    # Basic Info
    employee_id = fields.Many2one('hr.employee', string='Personel', tracking=True)
    event_name = fields.Char('Etkinlik Adı', required=True, tracking=True)
    event_date = fields.Date('Etkinlik Tarihi', required=True, tracking=True)
    event_location = fields.Char('Etkinlik Yeri', tracking=True)

    # Types (checkbox-like via M2M)
    event_type_ids = fields.Many2many('event.request.type', string='Etkinlik Türü', tracking=True)
    event_type_other = fields.Char('Diğer Tür (açıklama)')

    # Attendance multi
    attendance_status_ids = fields.Many2many('event.request.attendance.status', string='Katılım Durumu', tracking=True)
    attendance_status_other = fields.Char('Diğer Katılım (açıklama)')

    # Notes / Wishes
    notes = fields.Text('Dilek/İstekler')

    # Access
    access_option_ids = fields.Many2many('event.request.access.option', string='Erişim Seçenekleri', tracking=True)
    access_option_other = fields.Char('Diğer Erişim (açıklama)')

    # State machine
    state = fields.Selection([
        ('draft', 'Taslak'),
        ('submitted', 'Gönderildi'),
        ('approved', 'Onaylandı'),
        ('done', 'Tamamlandı'),
        ('cancel', 'İptal')
    ], string='Durum', default='draft', tracking=True, copy=False)

    def action_submit(self):
        for rec in self:
            rec.state = 'submitted'

    def action_approve(self):
        for rec in self:
            rec.state = 'approved'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    def action_reset_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'

    def name_get(self):
        result = []
        for rec in self:
            name = rec.event_name or _("Etkinlik Talebi")
            if rec.event_date:
                name = f"{name} ({rec.event_date})"
            if rec.employee_id:
                name = f"{rec.employee_id.name} - {name}"
            result.append((rec.id, name))
        return result