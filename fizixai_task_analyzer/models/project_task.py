from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = 'project.task'

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
        help='AI-estimated time to complete this task'
    )
    ai_solution_suggestion = fields.Html(
        string='AI Solution Suggestion',
        readonly=True,
        help='AI-generated solution suggestion'
    )
    ai_code_suggestion = fields.Text(
        string='AI Code Suggestion',
        readonly=True,
        help='AI-generated code suggestion'
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
    similar_tasks_count = fields.Integer(
        string='Similar Tasks Found',
        compute='_compute_similar_tasks',
        help='Number of similar tasks found in history'
    )
    ai_analysis_history_ids = fields.One2many(
        'ai.analysis.history',
        'task_id',
        string='Analysis History'
    )

    @api.depends('ai_complexity_score', 'project_id.complexity_low_threshold',
                 'project_id.complexity_high_threshold')
    def _compute_complexity_level(self):
        for task in self:
            if not task.ai_complexity_score:
                task.ai_complexity_level = False
            elif task.ai_complexity_score <= (task.project_id.complexity_low_threshold or 3):
                task.ai_complexity_level = 'low'
            elif task.ai_complexity_score >= (task.project_id.complexity_high_threshold or 7):
                if task.ai_complexity_score >= 9:
                    task.ai_complexity_level = 'critical'
                else:
                    task.ai_complexity_level = 'high'
            else:
                task.ai_complexity_level = 'medium'

    def _compute_similar_tasks(self):
        for task in self:
            # This will be implemented in complexity_analyzer service
            task.similar_tasks_count = 0

    @api.model
    def create(self, vals):
        task = super(ProjectTask, self).create(vals)
        # Auto-trigger AI analysis if enabled
        if task.project_id.enable_ai_analysis and task.project_id.ai_auto_trigger:
            task._trigger_ai_analysis()
        return task

    def write(self, vals):
        result = super(ProjectTask, self).write(vals)
        # Trigger on stage change if enabled
        if 'stage_id' in vals:
            for task in self:
                if task.project_id.enable_ai_analysis and task.project_id.ai_trigger_on_stage_change:
                    task._trigger_ai_analysis()
        return result

    def action_analyze_with_ai(self):
        """Manual trigger for AI analysis"""
        self.ensure_one()
        return self._trigger_ai_analysis()

    def _trigger_ai_analysis(self):
        """Trigger AI analysis for this task"""
        self.ensure_one()

        if not self.project_id.enable_ai_analysis:
            raise UserError(_('AI analysis is not enabled for this project.'))

        # Update status
        self.ai_analysis_status = 'analyzing'

        try:
            # Call AI analyzer service
            ai_analyzer = self.env['ai.analyzer.service']
            result = ai_analyzer.analyze_task(self)

            # Update task with results
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
                'task_id': self.id,
                'complexity_score': result.get('complexity_score', 0),
                'solution_suggestion': result.get('solution_suggestion', ''),
                'analysis_details': result.get('details', ''),
            })

            # If complexity is low and auto-dev is enabled, trigger auto development
            if (self.project_id.enable_auto_development and
                self.ai_complexity_score <= self.project_id.auto_dev_max_complexity and
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
            _logger.error(f"AI analysis failed for task {self.id}: {str(e)}")
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
                task=self,
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
            _logger.error(f"Auto development failed for task {self.id}: {str(e)}")
            # Don't fail the whole analysis if auto-dev fails
            pass

    def action_view_github_pr(self):
        """Open GitHub PR in browser"""
        self.ensure_one()
        if not self.github_pr_url:
            raise UserError(_('No GitHub PR available for this task.'))

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
            'domain': [('task_id', '=', self.id)],
            'context': {'default_task_id': self.id},
        }
