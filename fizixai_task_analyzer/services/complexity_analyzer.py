import logging
import re
from datetime import timedelta
from odoo import models, api, fields, _

_logger = logging.getLogger(__name__)


class ComplexityAnalyzer(models.AbstractModel):
    _name = 'complexity.analyzer'
    _description = 'Complexity Analysis Engine'

    @api.model
    def analyze_task(self, task):
        """
        Analyze task complexity based on multiple factors

        Returns:
            dict with analysis data
        """
        context_data = {}

        # 1. Description analysis
        description_score = self._analyze_description(task.description or task.name)
        context_data['description_length'] = len(task.description or '')

        # 2. Related records count
        related_count_score = self._analyze_related_records(task)
        context_data['related_count'] = related_count_score['count']

        # 3. Find similar historical tasks
        similar_tasks = self._find_similar_records(task, 'task')
        context_data['similar_records'] = self._format_similar_records(similar_tasks)
        context_data['similar_tasks_count'] = len(similar_tasks)

        # 4. Gather all context for AI
        context_data['project_name'] = task.project_id.name if task.project_id else ''
        context_data['customer_name'] = task.partner_id.name if task.partner_id else ''
        context_data['messages'] = self._get_messages(task)
        context_data['attachments'] = self._get_attachments_info(task)
        context_data['related_tasks'] = self._get_related_tasks_info(task)

        # 5. Code context (if GitHub is configured)
        if task.project_id and task.project_id.github_repo_url:
            context_data['code_context'] = self._get_code_context(task)

        return context_data

    @api.model
    def analyze_ticket(self, ticket):
        """
        Analyze ticket complexity based on multiple factors

        Returns:
            dict with analysis data
        """
        context_data = {}

        # 1. Description analysis
        description_score = self._analyze_description(ticket.description or ticket.name)
        context_data['description_length'] = len(ticket.description or '')

        # 2. Related records count
        related_count_score = self._analyze_related_records(ticket)
        context_data['related_count'] = related_count_score['count']

        # 3. Find similar historical tickets
        similar_tickets = self._find_similar_records(ticket, 'ticket')
        context_data['similar_records'] = self._format_similar_records(similar_tickets)
        context_data['similar_tickets_count'] = len(similar_tickets)

        # 4. Gather all context for AI
        context_data['project_name'] = ''  # Tickets don't have projects
        context_data['customer_name'] = ticket.partner_id.name if ticket.partner_id else ''
        context_data['messages'] = self._get_messages(ticket)
        context_data['attachments'] = self._get_attachments_info(ticket)
        context_data['related_tasks'] = ''  # Could link to related tasks if needed

        # 5. Code context (if customer has GitHub configured)
        if ticket.partner_id and ticket.partner_id.github_repo_url:
            context_data['code_context'] = self._get_code_context(ticket)

        return context_data

    def _analyze_description(self, description):
        """Analyze description text for complexity indicators"""
        if not description:
            return 0

        score = 0

        # Length-based scoring
        if len(description) > 1000:
            score += 2
        elif len(description) > 500:
            score += 1

        # Keyword-based scoring
        complexity_keywords = {
            'high': ['critical', 'urgent', 'complex', 'difficult', 'major', 'refactor', 'architecture'],
            'medium': ['improve', 'enhance', 'update', 'modify', 'change'],
            'low': ['fix', 'typo', 'minor', 'simple', 'quick'],
        }

        description_lower = description.lower()

        for keyword in complexity_keywords['high']:
            if keyword in description_lower:
                score += 0.5

        for keyword in complexity_keywords['medium']:
            if keyword in description_lower:
                score += 0.2

        for keyword in complexity_keywords['low']:
            if keyword in description_lower:
                score -= 0.3

        return max(0, score)

    def _analyze_related_records(self, record):
        """Count related records (messages, attachments, subtasks, etc.)"""
        count = 0

        # Count messages
        if hasattr(record, 'message_ids'):
            count += len(record.message_ids)

        # Count attachments
        if hasattr(record, 'attachment_ids'):
            count += len(record.attachment_ids)

        # Count subtasks for tasks
        if hasattr(record, 'child_ids'):
            count += len(record.child_ids)

        return {
            'count': count,
            'score': min(count / 10, 3)  # Max 3 points from related records
        }

    def _find_similar_records(self, record, record_type='task'):
        """Find similar historical records using text similarity"""
        model_name = 'project.task' if record_type == 'task' else 'helpdesk.ticket'

        # Simple keyword-based similarity
        # In production, could use more advanced NLP/embeddings

        keywords = self._extract_keywords(record.name or '')

        if not keywords:
            return []

        # Build domain
        domain = [
            ('id', '!=', record.id),
            ('ai_analysis_status', '=', 'completed'),
        ]

        # Add keyword search
        keyword_domain = ['|'] * (len(keywords) - 1) if len(keywords) > 1 else []
        for keyword in keywords:
            keyword_domain.append(('name', 'ilike', keyword))

        domain.extend(keyword_domain)

        # Search for similar records
        similar_records = self.env[model_name].search(domain, limit=5, order='create_date desc')

        return similar_records

    def _extract_keywords(self, text):
        """Extract meaningful keywords from text"""
        if not text:
            return []

        # Remove special characters
        text = re.sub(r'[^\w\s]', ' ', text.lower())

        # Split into words
        words = text.split()

        # Remove common words (simple stopwords)
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are'}
        keywords = [w for w in words if w not in stopwords and len(w) > 3]

        # Return top keywords
        return keywords[:5]

    def _format_similar_records(self, records):
        """Format similar records for AI context"""
        if not records:
            return ''

        formatted = "Found similar historical records:\n\n"

        for rec in records:
            formatted += f"- **{rec.name}**\n"
            if hasattr(rec, 'ai_complexity_score') and rec.ai_complexity_score:
                formatted += f"  Complexity: {rec.ai_complexity_score}/10\n"
            if hasattr(rec, 'ai_estimated_hours') and rec.ai_estimated_hours:
                formatted += f"  Estimated: {rec.ai_estimated_hours} hours\n"
            if hasattr(rec, 'description') and rec.description:
                # Truncate description
                desc = rec.description[:200] + '...' if len(rec.description) > 200 else rec.description
                formatted += f"  Description: {desc}\n"
            formatted += "\n"

        return formatted

    def _get_messages(self, record):
        """Get communication history"""
        if not hasattr(record, 'message_ids'):
            return ''

        messages = record.message_ids.filtered(lambda m: m.message_type in ['comment', 'email'])[:10]

        if not messages:
            return ''

        formatted = "Recent messages:\n\n"
        for msg in messages:
            author = msg.author_id.name if msg.author_id else 'Unknown'
            body = msg.body or ''
            # Strip HTML tags for cleaner context
            body_text = re.sub(r'<[^>]+>', '', body)[:200]
            formatted += f"- **{author}**: {body_text}\n"

        return formatted

    def _get_attachments_info(self, record):
        """Get attachment information"""
        if not hasattr(record, 'attachment_ids'):
            return ''

        attachments = record.attachment_ids

        if not attachments:
            return ''

        formatted = f"Attachments ({len(attachments)}):\n"
        for att in attachments:
            formatted += f"- {att.name} ({att.mimetype})\n"

        return formatted

    def _get_related_tasks_info(self, record):
        """Get related tasks information"""
        if not hasattr(record, 'child_ids'):
            return ''

        child_tasks = record.child_ids

        if not child_tasks:
            return ''

        formatted = f"Subtasks ({len(child_tasks)}):\n"
        for task in child_tasks:
            formatted += f"- {task.name} ({task.stage_id.name if task.stage_id else 'No stage'})\n"

        return formatted

    def _get_code_context(self, record):
        """Get code context from GitHub if available"""
        # This would integrate with github_service to fetch relevant code
        # For now, return empty - can be enhanced later

        try:
            if hasattr(record, 'project_id') and record.project_id and record.project_id.github_repo_url:
                return f"GitHub Repository: {record.project_id.github_repo_url}"
            elif hasattr(record, 'partner_id') and record.partner_id and record.partner_id.github_repo_url:
                return f"GitHub Repository: {record.partner_id.github_repo_url}"
        except Exception as e:
            _logger.warning(f"Could not get code context: {str(e)}")

        return ''

    @api.model
    def calculate_average_resolution_time(self, similar_records):
        """Calculate average resolution time from similar records"""
        if not similar_records:
            return 0

        total_hours = 0
        count = 0

        for rec in similar_records:
            if hasattr(rec, 'ai_estimated_hours') and rec.ai_estimated_hours:
                total_hours += rec.ai_estimated_hours
                count += 1

        if count == 0:
            return 0

        return total_hours / count
