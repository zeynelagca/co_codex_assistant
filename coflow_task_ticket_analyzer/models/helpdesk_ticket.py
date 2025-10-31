from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = 'ticket.helpdesk'

    # AI Analysis Fields
    ai_complexity_score = fields.Float(
        string='AI Complexity Score',
        readonly=True,
        help='AI-calculated complexity score (0-10)'
    )
    ai_complexity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], string='Complexity Level', compute='_compute_complexity_level', store=True)

    ai_estimated_hours = fields.Float(
        string='AI Estimated Hours',
        readonly=True,
        help='AI-estimated time to resolve this ticket'
    )
    ai_solution_suggestion = fields.Html(
        string='AI Solution Suggestion',
        readonly=True,
        help='AI-generated solution suggestion'
    )
    ai_code_suggestion = fields.Text(
        string='AI Code Suggestion',
        readonly=True,
        help='AI-generated code suggestion if ticket requires code changes'
    )
    ai_analysis_date = fields.Datetime(
        string='Last AI Analysis',
        readonly=True,
        help='Date of last AI analysis'
    )
    ai_analysis_status = fields.Selection([
        ('pending', 'Pending Analysis'),
        ('analyzing', 'Analyzing...'),
        ('completed', 'Analysis Completed'),
        ('error', 'Analysis Error'),
    ], string='AI Status', default='pending')

    ai_error_message = fields.Text(
        string='AI Error Message',
        readonly=True
    )

    # GitHub Integration
    github_issue_url = fields.Char(
        string='GitHub Issue',
        readonly=True,
        help='Link to related GitHub issue'
    )
    github_pr_url = fields.Char(
        string='GitHub Pull Request',
        readonly=True,
        help='Link to automatically created pull request'
    )
    github_commit_sha = fields.Char(
        string='GitHub Commit SHA',
        readonly=True
    )

    # Historical Analysis
    similar_tickets_count = fields.Integer(
        string='Similar Tickets Found',
        compute='_compute_similar_tickets',
        help='Number of similar tickets found in history'
    )
    ai_analysis_history_ids = fields.One2many(
        'ai.analysis.history',
        'ticket_id',
        string='Analysis History'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='customer_id',
        store=True,
        readonly=False,
        help='Customer linked to the ticket (alias of customer_id for compatibility)'
    )

    # Enable AI for this ticket
    enable_ai_analysis = fields.Boolean(
        string='Enable AI Analysis',
        default=True,
        help='Enable AI analysis for this ticket'
    )

    @api.depends('ai_complexity_score')
    def _compute_complexity_level(self):
        for ticket in self:
            if not ticket.ai_complexity_score:
                ticket.ai_complexity_level = False
            elif ticket.ai_complexity_score <= 3:
                ticket.ai_complexity_level = 'low'
            elif ticket.ai_complexity_score >= 7:
                if ticket.ai_complexity_score >= 9:
                    ticket.ai_complexity_level = 'critical'
                else:
                    ticket.ai_complexity_level = 'high'
            else:
                ticket.ai_complexity_level = 'medium'

    def _compute_similar_tickets(self):
        for ticket in self:
            # This will be implemented in complexity_analyzer service
            ticket.similar_tickets_count = 0

    @api.model
    def create(self, vals):
        ticket = super(HelpdeskTicket, self).create(vals)
        # Auto-trigger AI analysis if enabled
        if ticket.enable_ai_analysis:
            # Check if partner or team has auto-trigger enabled
            auto_trigger = False
            if ticket.partner_id and ticket.partner_id.ai_auto_trigger:
                auto_trigger = True
            if ticket.team_id and hasattr(ticket.team_id, 'ai_auto_trigger') and ticket.team_id.ai_auto_trigger:
                auto_trigger = True

            if auto_trigger:
                ticket._trigger_ai_analysis()
        return ticket

    def write(self, vals):
        result = super(HelpdeskTicket, self).write(vals)
        # Trigger on stage change if enabled
        if 'stage_id' in vals:
            for ticket in self:
                if ticket.enable_ai_analysis:
                    # Check if partner or team has stage trigger enabled
                    stage_trigger = False
                    if ticket.partner_id and ticket.partner_id.ai_trigger_on_stage_change:
                        stage_trigger = True
                    if ticket.team_id and hasattr(ticket.team_id, 'ai_trigger_on_stage_change') and ticket.team_id.ai_trigger_on_stage_change:
                        stage_trigger = True

                    if stage_trigger:
                        ticket._trigger_ai_analysis()
        return result

    def action_analyze_with_ai(self):
        """Manual trigger for AI analysis"""
        self.ensure_one()
        return self._trigger_ai_analysis()

    def _trigger_ai_analysis(self):
        """Trigger AI analysis for this ticket"""
        self.ensure_one()

        if not self.enable_ai_analysis:
            raise UserError(_('AI analysis is not enabled for this ticket.'))

        # Update status
        self.ai_analysis_status = 'analyzing'

        try:
            # Call AI analyzer service
            ai_analyzer = self.env['ai.analyzer.service']
            result = ai_analyzer.analyze_ticket(self)

            # Update ticket with results
            self.write({
                'ai_complexity_score': result.get('complexity_score', 0),
                'ai_estimated_hours': result.get('estimated_hours', 0),
                'ai_solution_suggestion': result.get('solution_suggestion', ''),
                'ai_code_suggestion': result.get('code_suggestion', ''),
                'ai_analysis_date': fields.Datetime.now(),
                'ai_analysis_status': 'completed',
                'ai_error_message': False,
            })

            # Create analysis history record
            self.env['ai.analysis.history'].create({
                'ticket_id': self.id,
                'complexity_score': result.get('complexity_score', 0),
                'solution_suggestion': result.get('solution_suggestion', ''),
                'analysis_details': result.get('details', ''),
            })

            # If complexity is low and auto-dev is enabled, trigger auto development
            if (self.partner_id and self.partner_id.enable_auto_development and
                self.ai_complexity_score <= (self.partner_id.auto_dev_max_complexity or 4) and
                result.get('code_suggestion')):
                self._trigger_auto_development(result)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('AI Analysis Completed'),
                    'message': _('Complexity Score: %.1f - %s') % (
                        self.ai_complexity_score,
                        dict(self._fields['ai_complexity_level'].selection).get(self.ai_complexity_level)
                    ),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except Exception as e:
            _logger.error(f"AI analysis failed for ticket {self.id}: {str(e)}")
            self.write({
                'ai_analysis_status': 'error',
                'ai_error_message': str(e),
            })
            raise UserError(_('AI Analysis failed: %s') % str(e))

    def _trigger_auto_development(self, analysis_result):
        """Trigger automatic code development and GitHub push"""
        self.ensure_one()

        try:
            github_service = self.env['github.service']
            result = github_service.create_and_push_code(
                ticket=self,
                code_suggestion=analysis_result.get('code_suggestion', ''),
                solution_description=analysis_result.get('solution_suggestion', '')
            )

            if result.get('success'):
                self.write({
                    'github_commit_sha': result.get('commit_sha'),
                    'github_pr_url': result.get('pr_url'),
                })

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Auto Development Completed'),
                        'message': _('Code has been generated and pushed to GitHub!'),
                        'type': 'success',
                        'sticky': True,
                    }
                }
        except Exception as e:
            _logger.error(f"Auto development failed for ticket {self.id}: {str(e)}")
            # Don't fail the whole analysis if auto-dev fails
            pass

    def action_view_github_pr(self):
        """Open GitHub PR in browser"""
        self.ensure_one()
        if not self.github_pr_url:
            raise UserError(_('No GitHub PR available for this ticket.'))

        return {
            'type': 'ir.actions.act_url',
            'url': self.github_pr_url,
            'target': 'new',
        }

    def action_view_analysis_history(self):
        """View analysis history"""
        self.ensure_one()
        return {
            'name': _('AI Analysis History'),
            'type': 'ir.actions.act_window',
            'res_model': 'ai.analysis.history',
            'view_mode': 'tree,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }
