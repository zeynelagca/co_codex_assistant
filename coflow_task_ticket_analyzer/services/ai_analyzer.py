import logging
from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AIAnalyzerService(models.AbstractModel):
    _name = 'ai.analyzer.service'
    _description = 'Main AI Analysis Service'

    @api.model
    def analyze_task(self, task):
        """
        Perform complete AI analysis on a task

        Args:
            task: project.task record

        Returns:
            dict with analysis results
        """
        _logger.info(f"Starting AI analysis for task {task.id}: {task.name}")

        try:
            # Step 1: Gather context using complexity analyzer
            complexity_analyzer = self.env['complexity.analyzer']
            context_data = complexity_analyzer.analyze_task(task)

            # Step 2: Prepare text for analysis
            analysis_text = self._prepare_task_text(task)

            # Step 3: Call Claude AI for analysis
            claude_service = self.env['claude.mcp.service']
            ai_result = claude_service.analyze_text(
                text=analysis_text,
                context_data=context_data,
                project=task.project_id,
                partner=task.partner_id,
                analysis_type='task'
            )

            # Step 4: Enhance results with our analysis
            result = self._enhance_analysis_results(ai_result, context_data)

            # Step 5: Update similar tasks count
            if context_data.get('similar_tasks_count'):
                task.write({'similar_tasks_count': context_data['similar_tasks_count']})

            _logger.info(f"AI analysis completed for task {task.id}. Complexity: {result.get('complexity_score')}")

            return result

        except Exception as e:
            _logger.error(f"AI analysis failed for task {task.id}: {str(e)}")
            raise

    @api.model
    def analyze_ticket(self, ticket):
        """
        Perform complete AI analysis on a helpdesk ticket

        Args:
            ticket: ticket.helpdesk record

        Returns:
            dict with analysis results
        """
        _logger.info(f"Starting AI analysis for ticket {ticket.id}: {ticket.name}")

        try:
            # Step 1: Gather context using complexity analyzer
            complexity_analyzer = self.env['complexity.analyzer']
            context_data = complexity_analyzer.analyze_ticket(ticket)

            # Step 2: Prepare text for analysis
            analysis_text = self._prepare_ticket_text(ticket)

            # Step 3: Call Claude AI for analysis
            claude_service = self.env['claude.mcp.service']
            ai_result = claude_service.analyze_text(
                text=analysis_text,
                context_data=context_data,
                project=None,
                partner=ticket.partner_id,
                analysis_type='ticket'
            )

            # Step 4: Enhance results with our analysis
            result = self._enhance_analysis_results(ai_result, context_data)

            # Step 5: Update similar tickets count
            if context_data.get('similar_tickets_count'):
                ticket.write({'similar_tickets_count': context_data['similar_tickets_count']})

            _logger.info(f"AI analysis completed for ticket {ticket.id}. Complexity: {result.get('complexity_score')}")

            return result

        except Exception as e:
            _logger.error(f"AI analysis failed for ticket {ticket.id}: {str(e)}")
            raise

    def _prepare_task_text(self, task):
        """Prepare comprehensive text from task for AI analysis"""
        text_parts = []

        # Task name
        text_parts.append(f"TASK: {task.name}")

        # Description
        if task.description:
            text_parts.append(f"\nDESCRIPTION:\n{task.description}")

        # Stage
        if task.stage_id:
            text_parts.append(f"\nCURRENT STAGE: {task.stage_id.name}")

        # Priority
        if hasattr(task, 'priority') and task.priority:
            text_parts.append(f"PRIORITY: {task.priority}")

        # Tags
        if hasattr(task, 'tag_ids') and task.tag_ids:
            tags = ', '.join(task.tag_ids.mapped('name'))
            text_parts.append(f"TAGS: {tags}")

        # Assigned users
        if hasattr(task, 'user_ids') and task.user_ids:
            users = ', '.join(task.user_ids.mapped('name'))
            text_parts.append(f"ASSIGNED TO: {users}")

        # Planned hours
        if hasattr(task, 'planned_hours') and task.planned_hours:
            text_parts.append(f"PLANNED HOURS: {task.planned_hours}")

        return '\n'.join(text_parts)

    def _prepare_ticket_text(self, ticket):
        """Prepare comprehensive text from ticket for AI analysis"""
        text_parts = []

        # Ticket name/subject
        text_parts.append(f"TICKET: {ticket.name}")

        # Description
        if ticket.description:
            text_parts.append(f"\nDESCRIPTION:\n{ticket.description}")

        # Stage
        if ticket.stage_id:
            text_parts.append(f"\nCURRENT STAGE: {ticket.stage_id.name}")

        # Priority
        if hasattr(ticket, 'priority') and ticket.priority:
            priority_labels = {'0': 'Low', '1': 'Normal', '2': 'High', '3': 'Urgent'}
            text_parts.append(f"PRIORITY: {priority_labels.get(ticket.priority, ticket.priority)}")

        # Ticket type
        if hasattr(ticket, 'ticket_type_id') and ticket.ticket_type_id:
            text_parts.append(f"TYPE: {ticket.ticket_type_id.name}")

        # Category
        if hasattr(ticket, 'category_id') and ticket.category_id:
            text_parts.append(f"CATEGORY: {ticket.category_id.name}")

        # Tags
        if hasattr(ticket, 'tag_ids') and ticket.tag_ids:
            tags = ', '.join(ticket.tag_ids.mapped('name'))
            text_parts.append(f"TAGS: {tags}")

        # Assigned user
        if hasattr(ticket, 'user_id') and ticket.user_id:
            text_parts.append(f"ASSIGNED TO: {ticket.user_id.name}")

        # Team
        if hasattr(ticket, 'team_id') and ticket.team_id:
            text_parts.append(f"TEAM: {ticket.team_id.name}")

        return '\n'.join(text_parts)

    def _enhance_analysis_results(self, ai_result, context_data):
        """Enhance AI results with our own analysis data"""

        # Add context data to results
        ai_result['similar_records_count'] = context_data.get('similar_tasks_count', 0) or context_data.get('similar_tickets_count', 0)

        # Format solution suggestion as HTML if it's not already
        if ai_result.get('solution_suggestion') and not ai_result['solution_suggestion'].startswith('<'):
            ai_result['solution_suggestion'] = f"<p>{ai_result['solution_suggestion']}</p>"

        # Add structured details
        details = {
            'description_length': context_data.get('description_length', 0),
            'related_count': context_data.get('related_count', 0),
            'similar_records_found': context_data.get('similar_tasks_count', 0) or context_data.get('similar_tickets_count', 0),
            'has_code_context': bool(context_data.get('code_context')),
            'complexity_reasoning': ai_result.get('complexity_reasoning', ''),
            'key_challenges': ai_result.get('key_challenges', []),
            'recommended_approach': ai_result.get('recommended_approach', ''),
            'technologies_involved': ai_result.get('technologies_involved', []),
        }

        ai_result['details'] = str(details)

        return ai_result

    @api.model
    def analyze_multiple_tasks(self, tasks):
        """
        Analyze multiple tasks in batch

        Args:
            tasks: project.task recordset

        Returns:
            dict: {task_id: result}
        """
        results = {}

        for task in tasks:
            try:
                result = self.analyze_task(task)
                results[task.id] = {
                    'success': True,
                    'result': result
                }

                # Update task immediately
                task.write({
                    'ai_complexity_score': result.get('complexity_score', 0),
                    'ai_estimated_hours': result.get('estimated_hours', 0),
                    'ai_solution_suggestion': result.get('solution_suggestion', ''),
                    'ai_code_suggestion': result.get('code_suggestion', ''),
                    'ai_analysis_status': 'completed',
                })

            except Exception as e:
                _logger.error(f"Failed to analyze task {task.id}: {str(e)}")
                results[task.id] = {
                    'success': False,
                    'error': str(e)
                }

                task.write({
                    'ai_analysis_status': 'error',
                    'ai_error_message': str(e),
                })

        return results

    @api.model
    def analyze_multiple_tickets(self, tickets):
        """
        Analyze multiple tickets in batch

        Args:
            tickets: ticket.helpdesk recordset

        Returns:
            dict: {ticket_id: result}
        """
        results = {}

        for ticket in tickets:
            try:
                result = self.analyze_ticket(ticket)
                results[ticket.id] = {
                    'success': True,
                    'result': result
                }

                # Update ticket immediately
                ticket.write({
                    'ai_complexity_score': result.get('complexity_score', 0),
                    'ai_estimated_hours': result.get('estimated_hours', 0),
                    'ai_solution_suggestion': result.get('solution_suggestion', ''),
                    'ai_code_suggestion': result.get('code_suggestion', ''),
                    'ai_analysis_status': 'completed',
                })

            except Exception as e:
                _logger.error(f"Failed to analyze ticket {ticket.id}: {str(e)}")
                results[ticket.id] = {
                    'success': False,
                    'error': str(e)
                }

                ticket.write({
                    'ai_analysis_status': 'error',
                    'ai_error_message': str(e),
                })

        return results

    @api.model
    def scheduled_analyze_pending_records(self):
        """
        Scheduled action to analyze pending tasks and tickets
        This can be called by a cron job
        """
        _logger.info("Starting scheduled AI analysis for pending records")

        # Analyze pending tasks
        pending_tasks = self.env['project.task'].search([
            ('ai_analysis_status', 'in', ['pending', 'error']),
            ('project_id.enable_ai_analysis', '=', True),
        ], limit=50)  # Limit to avoid timeout

        if pending_tasks:
            _logger.info(f"Found {len(pending_tasks)} pending tasks to analyze")
            self.analyze_multiple_tasks(pending_tasks)

        # Analyze pending tickets
        pending_tickets = self.env['ticket.helpdesk'].search([
            ('ai_analysis_status', 'in', ['pending', 'error']),
            ('enable_ai_analysis', '=', True),
        ], limit=50)

        if pending_tickets:
            _logger.info(f"Found {len(pending_tickets)} pending tickets to analyze")
            self.analyze_multiple_tickets(pending_tickets)

        _logger.info("Scheduled AI analysis completed")

        return True
