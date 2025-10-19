# Coflow Codex Assistant (Odoo 17)

Use a configurable LLM ("Codex") inside Odoo Discuss and Helpdesk to:  
- Draft replies for Helpdesk tickets  
- Summarize Discuss channels or create short reports  
- Keep an internal history of prompts/responses

## Configure
Settings → General Settings → Codex Assistant:
- **LLM API Base URL**: e.g. `https://api.openai.com/v1` or your proxy
- **LLM Model**: e.g. `gpt-4o-mini` (or provider-specific)
- **LLM API Key**
- Optional: temperature, max tokens, timeout

This addon supports OpenAI-compatible endpoints. It tries `/v1/chat/completions` first, then falls back to `/v1/responses`.

## Use
- **Helpdesk Ticket** form: click **Ask Codex** to open the wizard with ticket chatter context. Generate a **Reply Draft** then **Use in Composer**.
- **Discuss Channel** form: click **Codex Summary** to open the wizard. It will load recent messages for context; generate **Summary** or **Report**.

## Security
- History is visible to internal users. API key is stored as a system parameter restricted to Settings (Technical) users.

## Notes
- No vendor lock-in: you can point to any OpenAI-compatible gateway.  
- You can extend the wizard to fetch broader context or attach files.
