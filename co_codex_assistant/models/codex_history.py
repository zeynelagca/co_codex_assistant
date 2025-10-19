from odoo import api, fields, models

class CodexHistory(models.Model):
    _name = 'codex.history'
    _description = 'Codex Assistant History'
    _order = 'create_date desc'

    name = fields.Char(string='Title', compute='_compute_name', store=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, index=True)
    ticket_id = fields.Many2one('helpdesk.ticket', string='Helpdesk Ticket')
    channel_id = fields.Many2one('discuss.channel', string='Discuss Channel')
    purpose = fields.Selection([
        ('reply', 'Reply Draft'),
        ('summary', 'Summary'),
        ('report', 'Report'),
    ], string='Purpose', required=True, default='reply')
    prompt = fields.Text(string='Prompt/Instruction')
    context = fields.Text(string='Context')
    response = fields.Text(string='Response')
    input_tokens = fields.Integer('Input Tokens')
    output_tokens = fields.Integer('Output Tokens')

    @api.depends('purpose', 'ticket_id', 'channel_id', 'create_date')
    def _compute_name(self):
        for rec in self:
            base = dict(self._fields['purpose'].selection).get(rec.purpose or '', 'Assistant')
            target = rec.ticket_id.display_name if rec.ticket_id else (rec.channel_id.display_name if rec.channel_id else 'General')
            rec.name = f"{base} -> {target}"

