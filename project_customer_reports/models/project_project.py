# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
import base64
import io
import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    report_config_ids = fields.One2many(
        'project.report.config',
        'project_id',
        string='Report Configurations'
    )

    def action_send_daily_report(self):
        """Send daily report for this project"""
        for project in self:
            configs = project.report_config_ids.filtered(
                lambda c: c.active and c.send_daily_report
            )
            for config in configs:
                self._generate_and_send_task_report(config, 'daily')

    def action_send_weekly_report(self):
        """Send weekly report for this project"""
        for project in self:
            configs = project.report_config_ids.filtered(
                lambda c: c.active and c.send_weekly_report
            )
            for config in configs:
                self._generate_and_send_task_report(config, 'weekly')
                if config.send_timesheet_report:
                    self._generate_and_send_timesheet_report(config)

    def _generate_and_send_task_report(self, config, report_type, date_from=None, date_to=None):
        """Generate task report and send via email"""
        # Get date range
        if date_from is None or date_to is None:
            if report_type == 'daily':
                date_from = fields.Date.today()
                date_to = fields.Date.today()
            else:
                date_to = fields.Date.today()
                date_from = date_to - timedelta(days=7)

        # Generate XLSX report
        report_obj = self.env['project.report.xlsx']
        xlsx_data = report_obj.generate_task_report(config, report_type, date_from, date_to)

        # Create subject
        if report_type == 'daily':
            subject = f"Daily Task Report - {config.project_id.name} - {date_from}"
        else:
            subject = f"Weekly Task Report - {config.project_id.name} - {date_from} to {date_to}"

        # Create attachment
        filename = f"task_report_{report_type}_{config.project_id.name}_{fields.Date.today()}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Send email
        template = self.env.ref('project_customer_reports.mail_template_task_report')
        template.send_mail(
            config.id,
            email_values={
                'subject': subject,
                'email_to': config.email_to,
                'email_cc': config.email_cc,
                'attachment_ids': [(6, 0, [attachment.id])],
            },
            force_send=True
        )

    def _generate_and_send_timesheet_report(self, config, date_from=None, date_to=None):
        """Generate timesheet report and send via email"""
        # Get date range
        if date_from is None or date_to is None:
            date_to = fields.Date.today()
            date_from = date_to - timedelta(days=7)

        # Generate XLSX report
        report_obj = self.env['project.report.xlsx']
        xlsx_data = report_obj.generate_timesheet_report(config, date_from, date_to)

        subject = f"Weekly Timesheet Report - {config.project_id.name} - {date_from} to {date_to}"

        # Create attachment
        filename = f"timesheet_report_{config.project_id.name}_{fields.Date.today()}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(xlsx_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # Send email
        template = self.env.ref('project_customer_reports.mail_template_timesheet_report')
        template.send_mail(
            config.id,
            email_values={
                'subject': subject,
                'email_to': config.email_to,
                'email_cc': config.email_cc,
                'attachment_ids': [(6, 0, [attachment.id])],
            },
            force_send=True
        )

    @api.model
    def cron_send_daily_reports(self):
        """Cron job to send daily reports"""
        configs = self.env['project.report.config'].search([
            ('active', '=', True),
            ('send_daily_report', '=', True),
        ])
        for config in configs:
            try:
                config.project_id._generate_and_send_task_report(config, 'daily')
            except Exception as e:
                _logger.error(f"Error sending daily report for {config.name}: {str(e)}")

    @api.model
    def cron_send_weekly_reports(self):
        """Cron job to send weekly reports"""
        today = datetime.now().weekday()
        configs = self.env['project.report.config'].search([
            ('active', '=', True),
            ('send_weekly_report', '=', True),
            ('weekly_day', '=', str(today)),
        ])
        for config in configs:
            try:
                config.project_id._generate_and_send_task_report(config, 'weekly')
                if config.send_timesheet_report:
                    config.project_id._generate_and_send_timesheet_report(config)
            except Exception as e:
                _logger.error(f"Error sending weekly report for {config.name}: {str(e)}")
