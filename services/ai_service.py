import requests
from services.settings_service import get_api_key, get_model

# Built-in email templates with personalization variables
TEMPLATES = {
    'short_pitch': (
        "You are writing a concise cold email.\n"
        "Template style: Short Pitch — keep it under 150 words.\n"
        "Introduce {{product}}, identify {{pain_point}}, and end with a call to action."
    ),
    'problem_solution': (
        "You are writing a cold email using the Problem-Solution framework.\n"
        "State the problem {{pain_point}} the prospect faces, then present {{product}} as the solution."
    ),
    'quick_intro': (
        "You are writing a quick intro cold email.\n"
        "Briefly introduce yourself ({{sender}}) and {{product}} to {{name}} at {{company}}."
    ),
    'partnership': (
        "You are writing a partnership proposal email.\n"
        "Suggest a mutually beneficial partnership between the sender and {{company}} around {{product}}."
    ),
}


def build_prompt(product, audience, pain_point, tone, template_type,
                 lead_name='', lead_company='', sender='', personalized_intro=''):
    """Build the Groq prompt for email generation."""
    template_instructions = TEMPLATES.get(template_type, TEMPLATES['short_pitch'])

    # Fill simple variables into the instruction hint
    template_instructions = (
        template_instructions
        .replace('{{product}}', product)
        .replace('{{pain_point}}', pain_point)
        .replace('{{name}}', lead_name or 'the prospect')
        .replace('{{company}}', lead_company or 'their company')
        .replace('{{sender}}', sender or 'the sender')
    )

    intro_hint = f"\nStart with this personalized opener: {personalized_intro}" if personalized_intro else ""

    prompt = f"""
You are an expert cold email copywriter.
{template_instructions}

Details:
- Product: {product}
- Target audience: {audience}
- Pain point addressed: {pain_point}
- Tone: {tone}
- Lead name: {lead_name or 'N/A'}
- Lead company: {lead_company or 'N/A'}
- Sender: {sender or 'N/A'}
{intro_hint}

Write a cold email. Return ONLY the following format with no extra text:
SUBJECT: <subject line>
BODY:
<email body>
""".strip()

    return prompt


def generate_email(product, audience, pain_point, tone, template_type,
                   lead_name='', lead_company='', sender='', personalized_intro=''):
    """Call Groq API to generate a cold email. Returns dict with subject and body."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError('Groq API key is not set. Please add it in the Admin panel.')

    prompt = build_prompt(product, audience, pain_point, tone, template_type,
                          lead_name, lead_company, sender, personalized_intro)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': get_model(),
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7,
        'max_tokens': 600,
    }

    response = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers=headers,
        json=payload,
        timeout=30
    )

    if not response.ok:
        # Extract Groq's error message for clear user feedback
        try:
            err = response.json()
            msg = err.get('error', {}).get('message', response.text)
        except Exception:
            msg = response.text
        raise ValueError(f'Groq API error ({response.status_code}): {msg}')

    text = response.json()['choices'][0]['message']['content'].strip()

    # Parse subject and body from the response
    subject = ''
    body = text
    lines = text.split('\n')
    body_lines = []
    in_body = False
    for line in lines:
        if line.upper().startswith('SUBJECT:'):
            subject = line[8:].strip()
        elif line.upper().startswith('BODY:'):
            in_body = True
        elif in_body:
            body_lines.append(line)

    if body_lines:
        body = '\n'.join(body_lines).strip()

    if not subject:
        subject = f'A quick note about {product}'

    return {'subject': subject, 'body': body}
