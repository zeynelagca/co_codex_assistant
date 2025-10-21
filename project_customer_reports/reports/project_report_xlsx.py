# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime, timedelta
import io
import xlsxwriter


class ProjectReportXlsx(models.AbstractModel):
    _name = 'project.report.xlsx'
    _description = 'Project Report XLSX Generator'

    def generate_task_report(self, config, report_type='daily', date_from=None, date_to=None):
        """Generate task report in XLSX format"""
        if date_from is None or date_to is None:
            if report_type == 'daily':
                date_from = fields.Date.today()
                date_to = fields.Date.today()
            else:
                date_to = fields.Date.today()
                date_from = date_to - timedelta(days=7)

        # Build domain to get tasks created in date range OR active tasks
        domain = [
            ('project_id', '=', config.project_id.id),
            '|', '|',
            # Tasks created in the date range
            '&',
            ('create_date', '>=', fields.Datetime.to_string(
                datetime.combine(date_from, datetime.min.time())
            )),
            ('create_date', '<=', fields.Datetime.to_string(
                datetime.combine(date_to, datetime.max.time())
            )),
            # Tasks with deadline in the date range
            '&',
            ('date_deadline', '>=', date_from),
            ('date_deadline', '<=', date_to),
            # Tasks modified in the date range (updates)
            '&',
            ('write_date', '>=', fields.Datetime.to_string(
                datetime.combine(date_from, datetime.min.time())
            )),
            ('write_date', '<=', fields.Datetime.to_string(
                datetime.combine(date_to, datetime.max.time())
            )),
        ]

        tasks = self.env['project.task'].search(domain, order='stage_id, name')

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Task Report')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        cell_format = workbook.add_format({
            'border': 1,
            'valign': 'top',
            'text_wrap': True,
        })

        number_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'num_format': '0.00',
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
        })
        worksheet.merge_range('A1:G1',
            f'{report_type.capitalize()} Task Report - {config.project_id.name}',
            title_format
        )
        worksheet.merge_range('A2:G2',
            f'Period: {date_from} to {date_to}',
            workbook.add_format({'align': 'center'})
        )

        worksheet.set_column('A:A', 30)
        worksheet.set_column('B:B', 40)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 12)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 25)
        worksheet.set_column('G:G', 20)

        row = 3
        col = 0

        headers = ['Task Name']
        if config.include_description:
            headers.append('Description')
        headers.append('Stage')
        if config.include_allocated_hours:
            headers.append('Allocated Hours')
        if config.include_spent_hours:
            headers.append('Hours Spent')
        if config.include_tags:
            headers.append('Tags')
        if config.include_sprint:
            headers.append('Sprint')

        for header in headers:
            worksheet.write(row, col, header, header_format)
            col += 1

        row += 1
        for task in tasks:
            col = 0
            worksheet.write(row, col, task.name or '', cell_format)
            col += 1

            if config.include_description:
                description = task.description or ''
                if isinstance(description, str) and description.startswith('<'):
                    from html import unescape
                    import re
                    description = re.sub('<[^<]+?>', '', description)
                    description = unescape(description)
                worksheet.write(row, col, description, cell_format)
                col += 1

            worksheet.write(row, col, task.stage_id.name or '', cell_format)
            col += 1

            if config.include_allocated_hours:
                worksheet.write(row, col, task.allocated_hours or 0, number_format)
                col += 1

            if config.include_spent_hours:
                worksheet.write(row, col, task.effective_hours or 0, number_format)
                col += 1

            if config.include_tags:
                tags = ', '.join(task.tag_ids.mapped('name'))
                worksheet.write(row, col, tags, cell_format)
                col += 1

            if config.include_sprint:
                sprint = task.sprint_id.name if hasattr(task, 'sprint_id') and task.sprint_id else ''
                worksheet.write(row, col, sprint, cell_format)
                col += 1

            row += 1

        row += 1
        if config.include_allocated_hours and config.include_spent_hours:
            col = 0
            worksheet.write(row, col, 'TOTAL', header_format)

            col = 1
            if config.include_description:
                col += 1
            col += 1

            if config.include_allocated_hours:
                total_allocated = sum(tasks.mapped('allocated_hours'))
                worksheet.write(row, col, total_allocated, number_format)
                col += 1

            if config.include_spent_hours:
                total_spent = sum(tasks.mapped('effective_hours'))
                worksheet.write(row, col, total_spent, number_format)

        workbook.close()
        output.seek(0)
        return output.read()

    def generate_timesheet_report(self, config, date_from=None, date_to=None):
        """Generate timesheet report in XLSX format"""
        if date_from is None or date_to is None:
            date_to = fields.Date.today()
            date_from = date_to - timedelta(days=7)

        domain = [
            ('project_id', '=', config.project_id.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
        ]

        timesheets = self.env['account.analytic.line'].search(
            domain,
            order='date desc, task_id, employee_id'
        )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Timesheet Report')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        cell_format = workbook.add_format({
            'border': 1,
            'valign': 'top',
            'text_wrap': True,
        })

        date_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'num_format': 'dd/mm/yyyy',
        })

        number_format = workbook.add_format({
            'border': 1,
            'valign': 'vcenter',
            'num_format': '0.00',
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
        })
        worksheet.merge_range('A1:F1',
            f'Weekly Timesheet Report - {config.project_id.name}',
            title_format
        )
        worksheet.merge_range('A2:F2',
            f'Period: {date_from} to {date_to}',
            workbook.add_format({'align': 'center'})
        )

        worksheet.set_column('A:A', 12)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('D:D', 40)
        worksheet.set_column('E:E', 12)
        worksheet.set_column('F:F', 15)

        row = 3
        headers = ['Date', 'Employee', 'Task', 'Description', 'Hours Spent', 'Tags']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)

        row += 1
        for timesheet in timesheets:
            worksheet.write(row, 0, timesheet.date, date_format)
            worksheet.write(row, 1, timesheet.employee_id.name or '', cell_format)
            worksheet.write(row, 2, timesheet.task_id.name or '', cell_format)
            worksheet.write(row, 3, timesheet.name or '', cell_format)
            worksheet.write(row, 4, timesheet.unit_amount or 0, number_format)

            tags = ', '.join(timesheet.task_id.tag_ids.mapped('name')) if timesheet.task_id else ''
            worksheet.write(row, 5, tags, cell_format)

            row += 1

        row += 1
        worksheet.write(row, 3, 'TOTAL HOURS:', header_format)
        total_hours = sum(timesheets.mapped('unit_amount'))
        worksheet.write(row, 4, total_hours, number_format)

        row += 2
        worksheet.write(row, 0, 'Summary by Employee:', header_format)
        row += 1
        worksheet.write(row, 0, 'Employee', header_format)
        worksheet.write(row, 1, 'Total Hours', header_format)

        employees = {}
        for timesheet in timesheets:
            emp_name = timesheet.employee_id.name or 'Unassigned'
            if emp_name not in employees:
                employees[emp_name] = 0
            employees[emp_name] += timesheet.unit_amount

        row += 1
        for emp_name, hours in sorted(employees.items()):
            worksheet.write(row, 0, emp_name, cell_format)
            worksheet.write(row, 1, hours, number_format)
            row += 1

        workbook.close()
        output.seek(0)
        return output.read()
