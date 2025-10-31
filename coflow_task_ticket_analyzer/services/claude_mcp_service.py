import logging
import time
import json
from odoo import models, api, _
from odoo.exceptions import UserError

try:
    import anthropic
except ImportError:
    anthropic = None

_logger = logging.getLogger(__name__)


class ClaudeMCPService(models.AbstractModel):
    _name = 'claude.mcp.service'
    _description = 'Claude MCP Service for AI Analysis'

    @api.model
    def get_api_key(self, project=None, partner=None):
        """
        Get Claude API key with priority:
        1. Partner-specific key
        2. Project-specific key
        3. System parameter (global)
        """
        if partner and partner.claude_api_key:
            return partner.claude_api_key
        if project and project.claude_api_key:
            return project.claude_api_key

        # Fallback to system parameter
        api_key = self.env['ir.config_parameter'].sudo().get_param('coflow.claude_api_key')
        if not api_key:
            raise UserError(_('Claude API key is not configured. Please configure it in Settings or Project/Partner settings.'))
        return api_key

    @api.model
    def get_model(self, project=None):
        """Get Claude model to use"""
        if project and project.claude_model:
            return project.claude_model
        return 'claude-3-5-sonnet-20241022'  # Default to latest Sonnet

    @api.model
    def analyze_text(self, text, context_data=None, project=None, partner=None, analysis_type='task'):
        """
        Analyze text using Claude AI with MCP

        Args:
            text: Main text to analyze (task/ticket description)
            context_data: Additional context (dict with messages, related records, etc.)
            project: project.project record
            partner: res.partner record
            analysis_type: 'task' or 'ticket'

        Returns:
            dict with analysis results
        """
        if not anthropic:
            raise UserError(_('Anthropic Python package is not installed. Please install it: pip install anthropic'))

        start_time = time.time()

        try:
            api_key = self.get_api_key(project=project, partner=partner)
            model = self.get_model(project=project)

            client = anthropic.Anthropic(api_key=api_key)

            # Build the prompt
            prompt = self._build_analysis_prompt(text, context_data, analysis_type)

            _logger.info(f"Sending analysis request to Claude model: {model}")

            # Make the API call
            message = client.messages.create(
                model=model,
                max_tokens=4096,
                temperature=0.2,  # Lower temperature for more consistent analysis
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse response
            response_text = message.content[0].text if message.content else ""
            result = self._parse_analysis_response(response_text)

            analysis_duration = time.time() - start_time
            result['analysis_duration'] = analysis_duration
            result['ai_model_used'] = model

            _logger.info(f"Claude analysis completed in {analysis_duration:.2f} seconds")

            return result

        except anthropic.APIError as e:
            _logger.error(f"Claude API error: {str(e)}")
            raise UserError(_('Claude API Error: %s') % str(e))
        except Exception as e:
            _logger.error(f"Error during Claude analysis: {str(e)}")
            raise UserError(_('Analysis failed: %s') % str(e))

    def _build_analysis_prompt(self, text, context_data, analysis_type):
        """Build comprehensive prompt for Claude"""

        prompt = f"""You are an expert software development analyst. Analyze the following {analysis_type} and provide a detailed assessment.

**{analysis_type.upper()} DESCRIPTION:**
{text}

"""

        # Add context if available
        if context_data:
            if context_data.get('project_name'):
                prompt += f"\n**PROJECT:** {context_data['project_name']}"

            if context_data.get('customer_name'):
                prompt += f"\n**CUSTOMER:** {context_data['customer_name']}"

            if context_data.get('messages'):
                prompt += f"\n\n**COMMUNICATION HISTORY:**\n{context_data['messages']}"

            if context_data.get('attachments'):
                prompt += f"\n\n**ATTACHMENTS:** {context_data['attachments']}"

            if context_data.get('related_tasks'):
                prompt += f"\n\n**RELATED TASKS:**\n{context_data['related_tasks']}"

            if context_data.get('similar_records'):
                prompt += f"\n\n**SIMILAR HISTORICAL RECORDS:**\n{context_data['similar_records']}"

            if context_data.get('code_context'):
                prompt += f"\n\n**CODE CONTEXT:**\n{context_data['code_context']}"

        prompt += """

**ANALYSIS REQUIRED:**

Please provide a comprehensive analysis in the following JSON format:

{
    "complexity_score": <float between 0-10>,
    "complexity_reasoning": "<explanation of complexity score>",
    "estimated_hours": <float>,
    "estimation_reasoning": "<explanation of time estimate>",
    "solution_suggestion": "<detailed HTML-formatted solution suggestion>",
    "code_suggestion": "<actual code if applicable, or empty string>",
    "key_challenges": ["<challenge 1>", "<challenge 2>", ...],
    "recommended_approach": "<step-by-step approach>",
    "technologies_involved": ["<tech 1>", "<tech 2>", ...],
    "requires_code_changes": <true/false>,
    "auto_developable": <true/false - can this be auto-developed?>,
    "confidence_level": "<low/medium/high>"
}

**COMPLEXITY SCORING GUIDE:**
- 0-2: Trivial (simple config, data entry, minor text changes)
- 3-4: Simple (straightforward features, clear requirements, well-documented)
- 5-6: Moderate (requires some design, multiple components, moderate complexity)
- 7-8: Complex (significant architecture changes, multiple systems, unclear requirements)
- 9-10: Critical (major refactoring, high risk, extensive testing needed, system-wide impact)

**IMPORTANT:**
- Be realistic with time estimates
- Consider testing and documentation time
- Mark as auto_developable ONLY if it's a simple, well-defined code change
- Provide actual working code in code_suggestion if the task is simple enough
- Use HTML formatting in solution_suggestion for better readability

Return ONLY the JSON object, no additional text.
"""

        return prompt

    def _parse_analysis_response(self, response_text):
        """Parse Claude's JSON response"""
        try:
            # Try to extract JSON from response
            response_text = response_text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1])

            result = json.loads(response_text)

            # Validate required fields
            required_fields = ['complexity_score', 'estimated_hours', 'solution_suggestion']
            for field in required_fields:
                if field not in result:
                    _logger.warning(f"Missing field in Claude response: {field}")
                    result[field] = 0 if 'score' in field or 'hours' in field else ''

            # Ensure complexity score is in valid range
            result['complexity_score'] = max(0, min(10, float(result.get('complexity_score', 5))))

            return result

        except json.JSONDecodeError as e:
            _logger.error(f"Failed to parse Claude response as JSON: {str(e)}")
            _logger.error(f"Response text: {response_text}")

            # Fallback: create basic result
            return {
                'complexity_score': 5.0,
                'estimated_hours': 4.0,
                'solution_suggestion': f'<p>AI Response (raw):</p><pre>{response_text}</pre>',
                'code_suggestion': '',
                'complexity_reasoning': 'Failed to parse structured response',
                'auto_developable': False,
            }

    @api.model
    def analyze_code_from_github(self, github_url, file_paths=None, partner=None, project=None):
        """
        Analyze code complexity from GitHub repository

        Args:
            github_url: GitHub repository URL
            file_paths: List of specific file paths to analyze
            partner: res.partner record
            project: project.project record

        Returns:
            dict with code analysis results
        """
        # This will integrate with GitHub service to fetch code
        # and analyze it with Claude

        try:
            # Fetch code from GitHub
            github_service = self.env['github.service']
            code_content = github_service.fetch_code(github_url, file_paths, partner=partner, project=project)

            if not code_content:
                return {'error': 'Failed to fetch code from GitHub'}

            # Analyze with Claude
            api_key = self.get_api_key(project=project, partner=partner)
            model = self.get_model(project=project)

            client = anthropic.Anthropic(api_key=api_key)

            prompt = f"""Analyze the following code for complexity, potential issues, and improvement suggestions.

**CODE:**
{code_content}

Provide analysis in JSON format:
{{
    "complexity_score": <0-10>,
    "code_quality_score": <0-10>,
    "potential_issues": ["<issue 1>", ...],
    "improvement_suggestions": ["<suggestion 1>", ...],
    "summary": "<overall summary>"
}}
"""

            message = client.messages.create(
                model=model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text if message.content else "{}"
            return self._parse_analysis_response(response_text)

        except Exception as e:
            _logger.error(f"Code analysis failed: {str(e)}")
            return {'error': str(e)}
