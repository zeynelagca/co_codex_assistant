from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # GitHub Configuration for Customer
    github_repo_url = fields.Char(
        string='GitHub Repository URL',
        help='GitHub repository URL for this customer (e.g., https://github.com/username/repo)'
    )
    github_token = fields.Char(
        string='GitHub Personal Access Token',
        help='Personal Access Token for GitHub API access for this customer'
    )
    github_branch = fields.Char(
        string='Default Branch',
        default='main',
        help='Default branch for commits'
    )

    # AI Configuration for Customer
    enable_ai_analysis = fields.Boolean(
        string='Enable AI Analysis',
        default=True,
        help='Enable automatic AI analysis for tickets/tasks related to this customer'
    )
    ai_auto_trigger = fields.Boolean(
        string='Auto Trigger on Create',
        default=False,
        help='Automatically analyze tickets/tasks when created'
    )
    ai_trigger_on_stage_change = fields.Boolean(
        string='Trigger on Stage Change',
        default=True,
        help='Analyze tickets/tasks when stage changes'
    )

    # Claude API Configuration (can be customer-specific)
    claude_api_key = fields.Char(
        string='Claude API Key',
        help='Customer-specific Anthropic Claude API key (optional, uses project default if not set)'
    )

    # Auto Development Settings
    enable_auto_development = fields.Boolean(
        string='Enable Auto Development',
        default=False,
        help='Allow AI to automatically create code and push to GitHub for simple tickets'
    )
    auto_dev_max_complexity = fields.Integer(
        string='Max Complexity for Auto Dev',
        default=4,
        help='Only auto-develop tickets with complexity <= this value'
    )

    # Statistics
    ai_analyzed_tickets_count = fields.Integer(
        string='AI Analyzed Tickets',
        compute='_compute_ai_statistics',
        help='Number of tickets analyzed with AI'
    )
    ai_analyzed_tasks_count = fields.Integer(
        string='AI Analyzed Tasks',
        compute='_compute_ai_statistics',
        help='Number of tasks analyzed with AI'
    )
    github_prs_count = fields.Integer(
        string='GitHub PRs Created',
        compute='_compute_github_statistics',
        help='Number of GitHub PRs created automatically'
    )

    @api.depends('ticket_ids.ai_analysis_status')
    def _compute_ai_statistics(self):
        for partner in self:
            # Count tickets
            if hasattr(self.env['helpdesk.ticket'], 'ai_analysis_status'):
                tickets = self.env['helpdesk.ticket'].search([
                    ('partner_id', '=', partner.id),
                    ('ai_analysis_status', '=', 'completed')
                ])
                partner.ai_analyzed_tickets_count = len(tickets)
            else:
                partner.ai_analyzed_tickets_count = 0

            # Count tasks
            if hasattr(self.env['project.task'], 'ai_analysis_status'):
                tasks = self.env['project.task'].search([
                    ('partner_id', '=', partner.id),
                    ('ai_analysis_status', '=', 'completed')
                ])
                partner.ai_analyzed_tasks_count = len(tasks)
            else:
                partner.ai_analyzed_tasks_count = 0

    def _compute_github_statistics(self):
        for partner in self:
            # Count GitHub PRs from tickets
            ticket_prs = 0
            if hasattr(self.env['helpdesk.ticket'], 'github_pr_url'):
                tickets = self.env['helpdesk.ticket'].search([
                    ('partner_id', '=', partner.id),
                    ('github_pr_url', '!=', False)
                ])
                ticket_prs = len(tickets)

            # Count GitHub PRs from tasks
            task_prs = 0
            if hasattr(self.env['project.task'], 'github_pr_url'):
                tasks = self.env['project.task'].search([
                    ('partner_id', '=', partner.id),
                    ('github_pr_url', '!=', False)
                ])
                task_prs = len(tasks)

            partner.github_prs_count = ticket_prs + task_prs

    def action_view_ai_analyzed_tickets(self):
        """View AI analyzed tickets for this customer"""
        self.ensure_one()
        return {
            'name': _('AI Analyzed Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.id),
                ('ai_analysis_status', '=', 'completed')
            ],
        }

    def action_view_github_prs(self):
        """View all GitHub PRs created for this customer"""
        self.ensure_one()
        # This would open a custom view showing both ticket and task PRs
        # For now, just show tickets
        return {
            'name': _('GitHub Pull Requests'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.id),
                ('github_pr_url', '!=', False)
            ],
        }
