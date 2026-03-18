import requests
from services.settings_service import get_api_key, get_model


def generate_personalized_intro(lead_name: str, company: str, context: str) -> str:
    """
    Use Groq to generate a unique personalized intro line for a lead.
    Falls back to a generic intro if the API call fails.
    """
    api_key = get_api_key()
    if not api_key:
        return _fallback_intro(lead_name, company)

    name_hint = lead_name or 'there'
    company_hint = company or 'your company'
    context_hint = f' Based on their website: "{context[:300]}"' if context else ''

    prompt = (
        f'Write ONE personalized opening sentence for a cold email to {name_hint} at {company_hint}.'
        f'{context_hint} '
        f'Make it specific, warm, and under 25 words. No salutation, just the sentence.'
    )

    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': get_model(),
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.8,
            'max_tokens': 80,
        }
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers=headers,
            json=payload,
            timeout=15
        )
        if not resp.ok:
            raise ValueError(f'Groq API error {resp.status_code}')
        intro = resp.json()['choices'][0]['message']['content'].strip().strip('"')
        return intro
    except Exception:
        return _fallback_intro(lead_name, company)


def _fallback_intro(name: str, company: str) -> str:
    name = name or 'there'
    company = company or 'your company'
    return f'Hi {name} — I came across {company} and was impressed by your work.'
