from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CodexGenerateWizard(models.TransientModel):
    _name = 'codex.generate.wizard'
    _description = 'Generate with Codex'

    purpose = fields.Selection([
        ('reply', 'Reply Draft'),
        ('summary', 'Summary'),
        ('report', 'Report'),
    ], default='reply', required=True)
    language = fields.Selection([
        ('auto', 'Auto'),
        ('en', 'English'),
        ('tr', 'Turkish'),
    ], default='auto', required=True)
    tone = fields.Selection([
        ('neutral', 'Neutral/Professional'),
        ('friendly', 'Friendly'),
        ('formal', 'Formal'),
    ], default='neutral', required=True)
    context_text = fields.Text('Context', readonly=True)
    prompt = fields.Text('Extra Instructions')
    result = fields.Text('Result', readonly=True)

    ticket_id = fields.Many2one('helpdesk.ticket', string='Helpdesk Ticket', readonly=True)
    channel_id = fields.Many2one('discuss.channel', string='Discuss Channel', readonly=True)

    def _build_messages(self):
        system = 'You are a helpful assistant for Odoo. Always produce concise, actionable text. If purpose is report, structure with headings and bullet points.'
        if self.language and self.language != 'auto':
            system += f' Write the output in {self.language.upper()}.'
        if self.tone == 'friendly':
            system += ' Maintain a friendly, helpful tone.'
        elif self.tone == 'formal':
            system += ' Maintain a formal, concise tone.'

        user_parts = []
        if self.purpose == 'reply':
            user_parts.append('Draft a reply given the context.')
        elif self.purpose == 'summary':
            user_parts.append('Summarize the context for quick understanding.')
        else:
            user_parts.append('Create a brief report from the context with key sections and recommendations.')
        if self.prompt:
            user_parts.append(self.prompt)
        if self.context_text:
            user_parts.append('Context:\n' + self.context_text)

        messages = [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': '\n\n'.join(user_parts)},
        ]
        return messages

    def action_generate(self):
        client = self.env['codex.client']
        messages = self._build_messages()
        out = client.generate(messages)
        text = out.get('text') or ''
        self.write({'result': text})
        self.env['codex.history'].create({
            'user_id': self.env.user.id,
            'ticket_id': self.ticket_id.id if self.ticket_id else False,
            'channel_id': self.channel_id.id if self.channel_id else False,
            'purpose': self.purpose,
            'prompt': self.prompt,
            'context': self.context_text,
            'response': text,
            'input_tokens': out.get('input_tokens') or 0,
            'output_tokens': out.get('output_tokens') or 0,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'codex.generate.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_use_in_composer(self):
        # Insert result into the chatter composer on helpdesk ticket if present
        self.ensure_one()
        if not self.result:
            raise UserError(_('Nothing to insert. Please generate first.'))
        if self.ticket_id:
            self.ticket_id.message_post(body=self.result)
            return {'type': 'ir.actions.act_window_close'}
        # For Discuss channel, send a message
        if self.channel_id:
            self.channel_id.message_post(body=self.result)
            return {'type': 'ir.actions.act_window_close'}
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        ticket_id = self.env.context.get('default_ticket_id')
        channel_id = self.env.context.get('default_channel_id')
        ctx_text = ''
        if ticket_id:
            ticket = self.env['helpdesk.ticket'].browse(ticket_id)
            # collect last 20 messages (excluding internal notes if needed later)
            msgs = self.env['mail.message'].search([('model','=','helpdesk.ticket'),('res_id','=',ticket.id)], order='date desc', limit=20)
            lines = []
            for m in reversed(msgs):
                author = m.author_id.name or 'System'
                body = (m.body or '').replace('<p>','').replace('</p>','').replace('<br/>','\n')
                lines.append(f"{author}: {body}")
            ctx_text = '\n'.join(lines).strip()
            res['context_text'] = ctx_text
        elif channel_id:
            channel = self.env['discuss.channel'].browse(channel_id)
            msgs = self.env['mail.message'].search(
                [('model', '=', 'discuss.channel'), ('res_id', '=', channel.id)],
                order='date desc', limit=30,
            )
            if not msgs:
                msgs = self.env['mail.message'].search(
                    [('model', '=', 'mail.channel'), ('res_id', '=', channel.id)],
                    order='date desc', limit=30,
                )
            lines = []
            for m in reversed(msgs):
                author = m.author_id.name or 'System'
                body = (m.body or '').replace('<p>','').replace('</p>','').replace('<br/>','\n')
                lines.append(f"{author}: {body}")
            ctx_text = '\n'.join(lines).strip()
            res['context_text'] = ctx_text
        try:
            retriever = self.env['codex.client']
            query = (res.get('context_text') or '')[:1000] or (self.env.user.company_id.name or '')
            docs = retriever.rag_retrieve(query)
            if docs:
                rag_lines = []
                for d in docs:
                    rag_lines.append(f"[RAG:{d.model}#{d.res_id}] {d.title}\n{d.body}\n---")
                rag_block = '\n'.join(rag_lines)
                existing = res.get('context_text') or ''
                res['context_text'] = (rag_block + '\n' + existing).strip()
        except Exception:
            # fail open; do not block if RAG retrieval fails
            pass
        return res
