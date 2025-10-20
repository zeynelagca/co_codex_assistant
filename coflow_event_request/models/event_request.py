# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class EventType(models.Model):
    _name = "event.request.type"
    _description = "Event Type"
    _order = "name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Event Type Code must be unique!'),
    ]


class AttendanceStatus(models.Model):
    _name = "event.request.attendance.status"
    _description = "Attendance Status"
    _order = "name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Attendance Status Code must be unique!'),
    ]


class AccessOption(models.Model):
    _name = "event.request.access.option"
    _description = "Access Option"
    _order = "name"

    name = fields.Char(required=True, index=True)
    code = fields.Char(index=True)

    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Access Option Code must be unique!'),
    ]


class EventRequest(models.Model):
    _name = "event.request"
    _description = "Etkinlik Talebi"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = "event_name"
    _order = "event_date desc, id desc"

    # Basic Info
    employee_id = fields.Many2one(
        'hr.employee',
        string='Personel',
        tracking=True,
        ondelete='set null'
    )
    event_name = fields.Char(
        'Etkinlik Adı',
        required=True,
        tracking=True,
        index=True
    )
    event_date = fields.Date(
        'Etkinlik Tarihi',
        required=True,
        tracking=True,
        index=True
    )
    event_location = fields.Char('Etkinlik Yeri', tracking=True)

    # Types (checkbox-like via M2M)
    event_type_ids = fields.Many2many(
        'event.request.type',
        'event_request_type_rel',
        'event_request_id',
        'type_id',
        string='Etkinlik Türü',
        tracking=True
    )
    event_type_other = fields.Char('Diğer Tür (açıklama)')

    # Attendance multi
    attendance_status_ids = fields.Many2many(
        'event.request.attendance.status',
        'event_request_attendance_rel',
        'event_request_id',
        'attendance_id',
        string='Katılım Durumu',
        tracking=True
    )
    attendance_status_other = fields.Char('Diğer Katılım (açıklama)')

    # Notes / Wishes
    notes = fields.Text('Dilek/İstekler')

    # Access
    access_option_ids = fields.Many2many(
        'event.request.access.option',
        'event_request_access_rel',
        'event_request_id',
        'access_id',
        string='Erişim Seçenekleri',
        tracking=True
    )
    access_option_other = fields.Char('Diğer Erişim (açıklama)')

    # State machine
    state = fields.Selection(
        [
            ('draft', 'Taslak'),
            ('submitted', 'Gönderildi'),
            ('approved', 'Onaylandı'),
            ('done', 'Tamamlandı'),
            ('cancel', 'İptal')
        ],
        string='Durum',
        default='draft',
        tracking=True,
        copy=False,
        index=True
    )

    @api.constrains('event_date')
    def _check_event_date(self):
        """Validate event date is not in the past"""
        today = fields.Date.today()
        for rec in self:
            if rec.event_date and rec.event_date < today:
                raise ValidationError(
                    _('Event date cannot be in the past. Please select a future date.')
                )

    @api.constrains('employee_id')
    def _check_employee_id(self):
        """Validate employee is not empty"""
        for rec in self:
            if not rec.employee_id:
                raise ValidationError(
                    _('Employee field is required.')
                )

    def write(self, vals):
        """Override write to enforce state-based field readonly logic"""
        for rec in self:
            # Prevent modifying certain fields after submission
            if rec.state in ['submitted', 'approved', 'done', 'cancel']:
                restricted_fields = ['employee_id', 'event_name', 'event_date']
                if any(field in vals for field in restricted_fields):
                    raise ValidationError(
                        _('Cannot modify Employee, Event Name, or Event Date after submission.')
                    )

            # Prevent modifying fields after approval (stricter rules)
            if rec.state in ['approved', 'done', 'cancel']:
                stricter_fields = ['event_location', 'event_type_ids', 'attendance_status_ids',
                                   'access_option_ids', 'event_type_other', 'attendance_status_other',
                                   'access_option_other']
                if any(field in vals for field in stricter_fields):
                    raise ValidationError(
                        _('Cannot modify these fields after approval.')
                    )

            # Prevent modifying notes after cancellation or completion
            if rec.state in ['done', 'cancel']:
                if 'notes' in vals:
                    raise ValidationError(
                        _('Cannot modify notes after completion or cancellation.')
                    )

        return super().write(vals)

    def action_submit(self):
        """Submit the event request"""
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(
                    _('Only draft requests can be submitted.')
                )
            rec.state = 'submitted'

    def action_approve(self):
        """Approve the event request"""
        for rec in self:
            if rec.state != 'submitted':
                raise ValidationError(
                    _('Only submitted requests can be approved.')
                )
            rec.state = 'approved'

    def action_done(self):
        """Mark event request as done"""
        for rec in self:
            if rec.state != 'approved':
                raise ValidationError(
                    _('Only approved requests can be marked as done.')
                )
            rec.state = 'done'

    def action_reset_to_draft(self):
        """Reset cancelled request back to draft"""
        for rec in self:
            if rec.state != 'cancel':
                raise ValidationError(
                    _('Only cancelled requests can be reset to draft.')
                )
            rec.state = 'draft'

    def action_cancel(self):
        """Cancel the event request"""
        for rec in self:
            if rec.state in ['done']:
                raise ValidationError(
                    _('Cannot cancel a completed request.')
                )
            rec.state = 'cancel'

    def name_get(self):
        """Custom name display"""
        result = []
        for rec in self:
            name = rec.event_name or _("Etkinlik Talebi")
            if rec.event_date:
                name = f"{name} ({rec.event_date})"
            if rec.employee_id:
                name = f"{rec.employee_id.name} - {name}"
            result.append((rec.id, name))
        return result
