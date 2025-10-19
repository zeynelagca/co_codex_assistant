import json
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class CodexDocument(models.Model):
    _name = 'codex.document'
    _description = 'Codex RAG Document'
    _order = 'write_date desc'
    _rec_name = 'title'

    title = fields.Char(required=True)
    model = fields.Char(index=True)
    res_id = fields.Integer(index=True)
    company_id = fields.Many2one('res.company', index=True)
    body = fields.Text(help='Indexed text content')
    embedding = fields.Json(help='Vector embedding as list[float]')
    url = fields.Char(help='Smart URL to the record')
    tags = fields.Char(help='Comma separated tags')
    language = fields.Char(help='Detected language or set language')
    active = fields.Boolean(default=True)

    def name_get(self):
        return [(r.id, f"{r.title} [{r.model},{r.res_id}]") for r in self]

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    codex_embed_model = fields.Char(
        string='Embeddings Model',
        help='Model name for embeddings (e.g., text-embedding-3-small).')
    codex_rag_models = fields.Char(
        string='Models to Index (CSV)',
        help='Comma-separated list of model names to index, e.g.: helpdesk.ticket,mail.message')
    codex_rag_fields = fields.Char(
        string='Fields to Index (CSV)',
        help='Comma-separated list of text fields to index, e.g.: name,description,body')
    codex_rag_topk = fields.Integer(
        string='Retrieve Top-K', default=5,
        help='How many chunks to retrieve as context.')
    codex_rag_chunk = fields.Integer(
        string='Chunk Size (chars)', default=1000,
        help='Split long texts into chunks of this size.')

    def set_values(self):
        super().set_values()
        p = self.env['ir.config_parameter'].sudo()
        p.set_param('co_codex_assistant.embed_model', self.codex_embed_model or '')
        p.set_param('co_codex_assistant.rag_models', self.codex_rag_models or '')
        p.set_param('co_codex_assistant.rag_fields', self.codex_rag_fields or '')
        p.set_param('co_codex_assistant.rag_topk', str(self.codex_rag_topk or 5))
        p.set_param('co_codex_assistant.rag_chunk', str(self.codex_rag_chunk or 1000))

    @api.model
    def get_values(self):
        res = super().get_values()
        p = self.env['ir.config_parameter'].sudo()
        res.update(
            codex_embed_model=p.get_param('co_codex_assistant.embed_model', default=''),
            codex_rag_models=p.get_param('co_codex_assistant.rag_models', default='helpdesk.ticket,mail.message'),
            codex_rag_fields=p.get_param('co_codex_assistant.rag_fields', default='name,description,body'),
            codex_rag_topk=int(p.get_param('co_codex_assistant.rag_topk', default='5')),
            codex_rag_chunk=int(p.get_param('co_codex_assistant.rag_chunk', default='1000')),
        )
        return res
