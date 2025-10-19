from odoo import fields, models


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'

    codex_history_ids = fields.One2many(
        'codex.history',
        'ticket_id',
        string='Codex History',
        help='LLM prompts and responses generated from this ticket.',
    )
