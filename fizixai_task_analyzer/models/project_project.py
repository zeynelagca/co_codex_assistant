from odoo import models, fields, api


class ProjectProject(models.Model):
    _inherit = 'project.project'

    # GitHub Configuration
    github_repo_url = fields.Char(
        string='GitHub Repository URL',
        help='GitHub repository URL for this project (e.g., https://github.com/username/repo)'
    )
    github_token = fields.Char(
        string='GitHub Access Token',
        help='Personal Access Token for GitHub API access'
    )
    github_branch = fields.Char(
        string='Default Branch',
        default='main',
        help='Default branch for commits'
    )

    # AI Configuration
    enable_ai_analysis = fields.Boolean(
        string='Enable AI Analysis',
        default=True,
        help='Enable automatic AI analysis for tasks in this project'
    )
    ai_auto_trigger = fields.Boolean(
        string='Auto Trigger on Create',
        default=False,
        help='Automatically analyze tasks when created'
    )
    ai_trigger_on_stage_change = fields.Boolean(
        string='Trigger on Stage Change',
        default=True,
        help='Analyze tasks when stage changes'
    )

    # Claude MCP Configuration
    claude_api_key = fields.Char(
        string='Claude API Key',
        help='Anthropic Claude API key for AI analysis'
    )
    claude_model = fields.Selection([
        ('claude-3-opus-20240229', 'Claude 3 Opus'),
        ('claude-3-sonnet-20240229', 'Claude 3 Sonnet'),
        ('claude-3-haiku-20240307', 'Claude 3 Haiku'),
        ('claude-3-5-sonnet-20241022', 'Claude 3.5 Sonnet'),
    ], string='Claude Model', default='claude-3-5-sonnet-20241022',
        help='Claude model to use for analysis'
    )

    # Complexity Thresholds
    complexity_low_threshold = fields.Integer(
        string='Low Complexity Threshold',
        default=3,
        help='Tasks with score <= this are considered low complexity'
    )
    complexity_high_threshold = fields.Integer(
        string='High Complexity Threshold',
        default=7,
        help='Tasks with score >= this are considered high complexity'
    )

    # Auto Development
    enable_auto_development = fields.Boolean(
        string='Enable Auto Development',
        default=False,
        help='Allow AI to automatically create code and push to GitHub for simple tasks'
    )
    auto_dev_max_complexity = fields.Integer(
        string='Max Complexity for Auto Dev',
        default=4,
        help='Only auto-develop tasks with complexity <= this value'
    )
