import json
import logging
from odoo import api, models, _

_logger = logging.getLogger(__name__)

class CodexClient(models.AbstractModel):
    _name = 'codex.client'
    _description = 'Codex HTTP Client'

    def _get_conf(self):
        ICP = self.env['ir.config_parameter'].sudo()
        return {
            'api_base': ICP.get_param('co_codex_assistant.api_base', ''),
            'api_model': ICP.get_param('co_codex_assistant.api_model', ''),
            'api_key': ICP.get_param('co_codex_assistant.api_key', ''),
            'temperature': float(ICP.get_param('co_codex_assistant.temperature', '0.3')),
            'max_tokens': int(ICP.get_param('co_codex_assistant.max_tokens', '512')),
            'timeout': int(ICP.get_param('co_codex_assistant.timeout', '60')),
        }

    def generate(self, messages, **kwargs):
        """Call the configured LLM provider.

        messages: list of dicts like [{'role': 'system'|'user'|'assistant', 'content': '...'}]
        Returns: dict with keys: text, input_tokens, output_tokens, raw
        """
        conf = self._get_conf()
        api_base = conf['api_base'].rstrip('/')
        api_key = conf['api_key']
        model = conf['api_model']
        temperature = kwargs.get('temperature', conf['temperature'])
        max_tokens = kwargs.get('max_tokens', conf['max_tokens'])
        timeout = kwargs.get('timeout', conf['timeout'])

        if not api_base or not api_key or not model:
            raise ValueError(_('Codex Assistant is not configured (API base/model/key). Please configure in Settings > General Settings > Codex.'))

        # Two common patterns are supported automatically:
        # 1) OpenAI-compatible /v1/chat/completions
        # 2) OpenAI "responses" API emulation when providers proxy it under /v1/responses
        # We try chat/completions first, then fallback to responses.
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload_chat = {
            'model': model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        payload_responses = {
            'model': model,
            'input': messages,
            'temperature': temperature,
            'max_output_tokens': max_tokens,
        }

        import requests

        # Try chat/completions
        try:
            url = f"{api_base}/chat/completions" if not api_base.endswith('/v1') else f"{api_base}/chat/completions"
            resp = requests.post(url, headers=headers, json=payload_chat, timeout=timeout)
            if resp.status_code == 200:
                data = resp.json()
                text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                usage = data.get('usage', {})
                return {
                    'text': text,
                    'input_tokens': usage.get('prompt_tokens'),
                    'output_tokens': usage.get('completion_tokens'),
                    'raw': data,
                }
            _logger.warning('chat/completions failed (%s): %s', resp.status_code, resp.text[:500])
        except Exception as e:
            _logger.exception('Error calling chat/completions: %s', e)

        # Fallback to /responses
        url2 = f"{api_base}/responses"
        resp2 = requests.post(url2, headers=headers, json=payload_responses, timeout=timeout)
        if resp2.status_code != 200:
            raise ValueError(_('Codex HTTP error %s: %s') % (resp2.status_code, resp2.text))
        data = resp2.json()
        # Try to normalize different provider formats
        text = ''
        usage = {}
        # OpenAI "responses" style
        if 'output_text' in data:
            text = data['output_text']
        elif 'content' in data and isinstance(data['content'], list) and data['content']:
            # Sometimes providers return [{"type":"output_text","text":"..."}]
            for part in data['content']:
                if isinstance(part, dict) and part.get('type') in ('output_text', 'message') and part.get('text'):
                    text += part.get('text', '')
        elif 'choices' in data:
            text = data.get('choices', [{}])[0].get('message', {}).get('content', '')
        usage = data.get('usage', usage)
        return {
            'text': text,
            'input_tokens': usage.get('prompt_tokens') or usage.get('input_tokens'),
            'output_tokens': usage.get('completion_tokens') or usage.get('output_tokens'),
            'raw': data,
        }

    def _embed(self, texts, embed_model=None, timeout=None):
        conf = self._get_conf()
        api_base = conf['api_base'].rstrip('/')
        api_key = conf['api_key']
        timeout = timeout or conf['timeout']
        if not api_base or not api_key:
            raise ValueError(_('Codex Assistant is not configured (API base/key).'))
        ICP = self.env['ir.config_parameter'].sudo()
        embed_model = embed_model or ICP.get_param('co_codex_assistant.embed_model', '')
        if not embed_model:
            raise ValueError(_('Embeddings model is not set in Settings.'))
        payload = {'model': embed_model, 'input': texts}
        headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
        import requests
        url = f"{api_base}/embeddings"
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if r.status_code != 200:
            raise ValueError(_('Embeddings HTTP error %s: %s') % (r.status_code, r.text))
        data = r.json()
        vecs = [d.get('embedding') for d in data.get('data', [])]
        return vecs

    @staticmethod
    def _cosine(a, b):
        # a, b are Python lists
        if not a or not b:
            return 0.0
        s = 0.0
        na = 0.0
        nb = 0.0
        ln = min(len(a), len(b))
        for i in range(ln):
            x = float(a[i])
            y = float(b[i])
            s += x * y
            na += x * x
            nb += y * y
        if na <= 0 or nb <= 0:
            return 0.0
        import math
        return s / (math.sqrt(na) * math.sqrt(nb))

    def rag_retrieve(self, query_text, limit=None):
        ICP = self.env['ir.config_parameter'].sudo()
        topk = int(ICP.get_param('co_codex_assistant.rag_topk', '5'))
        limit = limit or topk
        # Compute query embedding
        qv = self._embed([query_text])[0]
        # Filter by company for multi-company environments (optional)
        domain = ['|', ('company_id', '=', False), ('company_id', '=', self.env.company.id)]
        docs = self.env['codex.document'].sudo().search(domain, limit=2000)  # simple cap
        scored = []
        for d in docs:
            v = d.embedding or []
            score = self._cosine(qv, v)
            scored.append((score, d))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [d for (s, d) in scored[:limit]]

    def rag_index_now(self):
        ICP = self.env['ir.config_parameter'].sudo()
        models_csv = (ICP.get_param('co_codex_assistant.rag_models', '') or '').strip()
        fields_csv = (ICP.get_param('co_codex_assistant.rag_fields', '') or '').strip()
        chunk_size = int(ICP.get_param('co_codex_assistant.rag_chunk', '1000'))
        if not models_csv or not fields_csv:
            return 0
        models = [m.strip() for m in models_csv.split(',') if m.strip()]
        fields = [f.strip() for f in fields_csv.split(',') if f.strip()]
        created = 0
        Doc = self.env['codex.document'].sudo()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for model_name in models:
            Model = self.env[model_name]
            # Only index records readable by current user to respect ACLs
            recs = Model.search([], limit=1000, order='write_date desc')
            for rec in recs:
                # Concatenate target fields
                parts = []
                for fname in fields:
                    if fname in rec and isinstance(rec[fname], str) and rec[fname]:
                        parts.append(rec[fname])
                if not parts:
                    continue
                text = '\n'.join(parts)
                # Split into chunks
                for idx in range(0, len(text), chunk_size):
                    chunk = text[idx: idx + chunk_size]
                    vec = self._embed([chunk])[0]
                    Doc.create({
                        'title': f"{rec.display_name} (part {idx // chunk_size + 1})",
                        'model': model_name,
                        'res_id': rec.id,
                        'company_id': rec.company_id.id if 'company_id' in rec else False,
                        'body': chunk,
                        'embedding': vec,
                        'url': f"{base_url}/web#id={rec.id}&model={model_name}&view_type=form",
                    })
                    created += 1
        return created
