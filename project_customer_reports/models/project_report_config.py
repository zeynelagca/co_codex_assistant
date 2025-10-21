# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
import re


class ProjectReportConfig(models.Model):
    _name = 'project.report.config'
    _description = 'Project Report Configuration'

    name = fields.Char('Configuration Name', required=True)
    project_id = fields.Many2one('project.project', string='Project', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)

    # Report Types
    send_daily_report = fields.Boolean('Send Daily Report', default=True)
    send_weekly_report = fields.Boolean('Send Weekly Report', default=True)
    send_timesheet_report = fields.Boolean('Send Weekly Timesheet Report', default=True)

    # Email Configuration
    email_to = fields.Char('Email To', required=True)
    email_cc = fields.Char('Email CC')

    # Report Options
    include_description = fields.Boolean('Include Task Description', default=True)
    include_allocated_hours = fields.Boolean('Include Allocated Hours', default=True)
    include_spent_hours = fields.Boolean('Include Spent Hours', default=True)
    include_tags = fields.Boolean('Include Tags', default=True)
    include_sprint = fields.Boolean('Include Sprint', default=True)

    # Scheduling
    daily_send_time = fields.Float('Daily Report Time (24h format)', default=18.0)
    weekly_day = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string='Weekly Report Day', default='4')

    active = fields.Boolean('Active', default=True)

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id and self.project_id.partner_id:
            self.partner_id = self.project_id.partner_id
            if self.project_id.partner_id.email:
                self.email_to = self.project_id.partner_id.email

    @api.constrains('email_to')
    def _check_email_to(self):
        """Validate email_to format"""
        for record in self:
            if record.email_to:
                emails = [e.strip() for e in record.email_to.split(',')]
                for email in emails:
                    if email and not self._validate_email(email):
                        raise ValidationError(_('Invalid email address: %s') % email)

    @api.constrains('email_cc')
    def _check_email_cc(self):
        """Validate email_cc format"""
        for record in self:
            if record.email_cc:
                emails = [e.strip() for e in record.email_cc.split(',')]
                for email in emails:
                    if email and not self._validate_email(email):
                        raise ValidationError(_('Invalid CC email address: %s') % email)

    def _validate_email(self, email):
        """Validate email format using regex"""
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_regex, email) is not None
