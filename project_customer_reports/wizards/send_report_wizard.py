# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class SendReportWizard(models.TransientModel):
    _name = 'send.report.wizard'
    _description = 'Send Report Wizard'

    project_id = fields.Many2one('project.project', string='Project', required=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    email_to = fields.Char('Email To', required=True)
    email_cc = fields.Char('Email CC')

    report_type = fields.Selection([
        ('daily', 'Daily Task Report'),
        ('weekly', 'Weekly Task Report'),
        ('timesheet', 'Weekly Timesheet Report'),
    ], string='Report Type', required=True, default='daily')

    date_from = fields.Date('Date From', required=True, default=fields.Date.today)
    date_to = fields.Date('Date To', required=True, default=fields.Date.today)

    @api.onchange('project_id')
    def _onchange_project_id(self):
        if self.project_id and self.project_id.partner_id:
            self.partner_id = self.project_id.partner_id
            if self.project_id.partner_id.email:
                self.email_to = self.project_id.partner_id.email

    @api.onchange('report_type')
    def _onchange_report_type(self):
        if self.report_type in ['weekly', 'timesheet']:
            self.date_to = fields.Date.today()
            self.date_from = self.date_to - timedelta(days=7)
        else:
            self.date_from = fields.Date.today()
            self.date_to = fields.Date.today()

    def action_send_report(self):
        """Send the selected report"""
        self.ensure_one()

        # Create temporary config
        config_vals = {
            'name': f'Manual Report - {self.project_id.name}',
            'project_id': self.project_id.id,
            'partner_id': self.partner_id.id if self.partner_id else False,
            'email_to': self.email_to,
            'email_cc': self.email_cc,
            'send_daily_report': True,
            'send_weekly_report': True,
            'send_timesheet_report': True,
            'include_description': True,
            'include_allocated_hours': True,
            'include_spent_hours': True,
            'include_tags': True,
            'include_sprint': True,
            'active': False,
        }
        temp_config = self.env['project.report.config'].create(config_vals)

        try:
            if self.report_type in ['daily', 'weekly']:
                self.project_id._generate_and_send_task_report(
                    temp_config,
                    self.report_type
                )
            elif self.report_type == 'timesheet':
                self.project_id._generate_and_send_timesheet_report(temp_config)

            temp_config.unlink()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Report sent successfully!'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            temp_config.unlink()
            raise UserError(_(f'Error sending report: {str(e)}'))
