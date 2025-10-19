from odoo import api, fields, models, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    codex_api_base = fields.Char(
        string='LLM API Base URL',
        help='Base URL of the LLM provider (e.g., https://api.openai.com/v1).')
    codex_api_model = fields.Char(
        string='LLM Model',
        help='Model name to use (e.g., gpt-4o-mini or another provider-specific name).')
    codex_api_key = fields.Char(
        string='LLM API Key',
        help='API Key for the LLM provider. Stored as a system parameter.')
    codex_temperature = fields.Float(
        string='LLM Temperature', default=0.3,
        help='Sampling temperature (creativity).')
    codex_max_tokens = fields.Integer(
        string='Max Output Tokens', default=512,
        help='Maximum number of tokens to generate in the response.')
    codex_timeout = fields.Integer(
        string='HTTP Timeout (sec)', default=60,
        help='Timeout in seconds for the HTTP request.')

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('co_codex_assistant.api_base', self.codex_api_base or '')
        params.set_param('co_codex_assistant.api_model', self.codex_api_model or '')
        if self.codex_api_key:
            params.set_param('co_codex_assistant.api_key', self.codex_api_key, groups=['base.group_system'])
        params.set_param('co_codex_assistant.temperature', str(self.codex_temperature or 0.0))
        params.set_param('co_codex_assistant.max_tokens', str(self.codex_max_tokens or 0))
        params.set_param('co_codex_assistant.timeout', str(self.codex_timeout or 60))

    @api.model
    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            codex_api_base=params.get_param('co_codex_assistant.api_base', default=''),
            codex_api_model=params.get_param('co_codex_assistant.api_model', default=''),
            codex_api_key=params.get_param('co_codex_assistant.api_key', default=''),
            codex_temperature=float(params.get_param('co_codex_assistant.temperature', default='0.3')),
            codex_max_tokens=int(params.get_param('co_codex_assistant.max_tokens', default='512')),
            codex_timeout=int(params.get_param('co_codex_assistant.timeout', default='60')),
        )
        return res
