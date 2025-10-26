from odoo import models, fields, api, _


class AIAnalysisHistory(models.Model):
    _name = 'ai.analysis.history'
    _description = 'AI Analysis History'
    _order = 'create_date desc'
    _rec_name = 'display_name'

    display_name = fields.Char(
        string='Name',
        compute='_compute_display_name',
        store=True
    )

    # Related Records
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        ondelete='cascade',
        index=True
    )
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        ondelete='cascade',
        index=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        compute='_compute_partner_id',
        store=True
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        related='task_id.project_id',
        store=True
    )

    # Analysis Results
    complexity_score = fields.Float(
        string='Complexity Score',
        required=True,
        help='AI-calculated complexity score (0-10)'
    )
    complexity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Complexity Level', compute='_compute_complexity_level', store=True)

    estimated_hours = fields.Float(
        string='Estimated Hours',
        help='AI-estimated time to complete'
    )
    solution_suggestion = fields.Html(
        string='Solution Suggestion',
        help='AI-generated solution suggestion'
    )
    code_suggestion = fields.Text(
        string='Code Suggestion',
        help='AI-generated code suggestion'
    )
    analysis_details = fields.Text(
        string='Analysis Details',
        help='Detailed analysis information from AI'
    )

    # AI Model Info
    ai_model_used = fields.Char(
        string='AI Model',
        help='Claude model used for this analysis'
    )
    analysis_duration = fields.Float(
        string='Analysis Duration (seconds)',
        help='Time taken for AI analysis'
    )

    # Similar Records Found
    similar_records_count = fields.Integer(
        string='Similar Records',
        help='Number of similar records found during analysis'
    )
    similar_record_ids = fields.Text(
        string='Similar Record IDs',
        help='IDs of similar records (JSON format)'
    )

    # GitHub Integration
    github_action_taken = fields.Boolean(
        string='GitHub Action Taken',
        default=False
    )
    github_commit_sha = fields.Char(
        string='Commit SHA'
    )
    github_pr_url = fields.Char(
        string='Pull Request URL'
    )

    # Status
    status = fields.Selection([
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ], string='Status', default='success', required=True)

    error_message = fields.Text(
        string='Error Message'
    )

    @api.depends('task_id', 'ticket_id', 'create_date')
    def _compute_display_name(self):
        for record in self:
            if record.task_id:
                record.display_name = f"Analysis: {record.task_id.name} ({record.create_date})"
            elif record.ticket_id:
                record.display_name = f"Analysis: {record.ticket_id.name} ({record.create_date})"
            else:
                record.display_name = f"Analysis ({record.create_date})"

    @api.depends('task_id.partner_id', 'ticket_id.partner_id')
    def _compute_partner_id(self):
        for record in self:
            if record.task_id:
                record.partner_id = record.task_id.partner_id
            elif record.ticket_id:
                record.partner_id = record.ticket_id.partner_id
            else:
                record.partner_id = False

    @api.depends('complexity_score')
    def _compute_complexity_level(self):
        for record in self:
            if not record.complexity_score:
                record.complexity_level = False
            elif record.complexity_score <= 3:
                record.complexity_level = 'low'
            elif record.complexity_score >= 7:
                if record.complexity_score >= 9:
                    record.complexity_level = 'critical'
                else:
                    record.complexity_level = 'high'
            else:
                record.complexity_level = 'medium'

    def action_view_related_record(self):
        """Open the related task or ticket"""
        self.ensure_one()
        if self.task_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'project.task',
                'res_id': self.task_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        elif self.ticket_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'helpdesk.ticket',
                'res_id': self.ticket_id.id,
                'view_mode': 'form',
                'target': 'current',
            }

    def action_view_github_pr(self):
        """Open GitHub PR"""
        self.ensure_one()
        if not self.github_pr_url:
            raise UserError(_('No GitHub PR available.'))

        return {
            'type': 'ir.actions.act_url',
            'url': self.github_pr_url,
            'target': 'new',
        }
