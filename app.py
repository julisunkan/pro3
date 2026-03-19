import os
import io
import csv
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, jsonify, send_file, make_response, g
)
from models.db import init_db, get_db
from services.ai_service import generate_email
from services.lead_scraper import scrape_website
from services.personalization import generate_personalized_intro
from services.campaign_service import create_campaign
from services.analytics import get_campaign_analytics
from services.export_service import export_email_txt, export_email_html, export_email_pdf, export_email_docx

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cold-email-secret-key-2024')

# Initialize database on startup
with app.app_context():
    init_db()


@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of each request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ─────────────────────────────────────────────
# HOME / EMAIL GENERATOR
# ─────────────────────────────────────────────

@app.route('/')
def index():
    db = get_db()
    emails = db.execute(
        'SELECT e.*, c.name as campaign_name FROM emails e '
        'LEFT JOIN campaigns c ON e.campaign_id = c.id '
        'ORDER BY e.created_at DESC LIMIT 20'
    ).fetchall()
    return render_template('index.html', emails=emails)


@app.route('/generate', methods=['POST'])
def generate():
    product = request.form.get('product', '').strip()
    audience = request.form.get('audience', '').strip()
    pain_point = request.form.get('pain_point', '').strip()
    tone = request.form.get('tone', 'friendly')
    template_type = request.form.get('template_type', 'short_pitch')
    sender = request.form.get('sender', '').strip()

    if not product or not audience or not pain_point:
        return jsonify({'success': False, 'message': 'Please fill in all required fields.'})

    try:
        result = generate_email(product, audience, pain_point, tone, template_type, sender=sender)
        db = get_db()
        cursor = db.execute(
            'INSERT INTO emails (campaign_id, lead_id, subject, body) VALUES (?, ?, ?, ?)',
            (None, None, result['subject'], result['body'])
        )
        db.commit()
        return jsonify({
            'success': True,
            'subject': result['subject'],
            'body': result['body'],
            'email_id': cursor.lastrowid
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ─────────────────────────────────────────────
# LEAD MANAGEMENT
# ─────────────────────────────────────────────

@app.route('/leads')
def leads():
    db = get_db()
    leads = db.execute('SELECT * FROM leads ORDER BY id DESC').fetchall()
    return render_template('leads.html', leads=leads)


@app.route('/leads/upload', methods=['POST'])
def upload_leads():
    if 'csv_file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided.'})

    file = request.files['csv_file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'})

    try:
        stream = io.StringIO(file.stream.read().decode('utf-8'), newline=None)
        reader = csv.DictReader(stream)
        db = get_db()
        count = 0
        for row in reader:
            name = row.get('name', '').strip()
            email = row.get('email', '').strip()
            company = row.get('company', '').strip()
            website = row.get('website', '').strip()
            if email:
                db.execute(
                    'INSERT OR IGNORE INTO leads (name, email, company, website) VALUES (?, ?, ?, ?)',
                    (name, email, company, website)
                )
                count += 1
        db.commit()
        return jsonify({'success': True, 'message': f'{count} leads imported successfully.'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error parsing CSV: {str(e)}'})


@app.route('/leads/delete/<int:lead_id>', methods=['POST'])
def delete_lead(lead_id):
    db = get_db()
    db.execute('DELETE FROM leads WHERE id = ?', (lead_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'Lead deleted.'})


# ─────────────────────────────────────────────
# CAMPAIGNS
# ─────────────────────────────────────────────

@app.route('/campaigns')
def campaigns():
    db = get_db()
    campaigns = db.execute('SELECT * FROM campaigns ORDER BY id DESC').fetchall()
    return render_template('campaign.html', campaigns=campaigns)


@app.route('/campaigns/delete/<int:campaign_id>', methods=['POST'])
def delete_campaign(campaign_id):
    db = get_db()
    db.execute('DELETE FROM emails WHERE campaign_id = ?', (campaign_id,))
    db.execute('DELETE FROM campaigns WHERE id = ?', (campaign_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'Campaign deleted.'})


@app.route('/campaigns/create', methods=['POST'])
def create_campaign_route():
    name = request.form.get('name', '').strip()
    product = request.form.get('product', '').strip()
    pain_point = request.form.get('pain_point', '').strip()
    template_type = request.form.get('template_type', 'short_pitch')
    tone = request.form.get('tone', 'friendly')
    sender = request.form.get('sender', '').strip()

    if not name or not product:
        return jsonify({'success': False, 'message': 'Campaign name and product are required.'})

    try:
        campaign_id = create_campaign(name, product, template_type, tone, sender, pain_point)
        return jsonify({'success': True, 'message': f'Campaign "{name}" created.', 'campaign_id': campaign_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/campaigns/<int:campaign_id>/run', methods=['POST'])
def run_campaign(campaign_id):
    try:
        db = get_db()
        campaign = db.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,)).fetchone()
        if not campaign:
            return jsonify({'success': False, 'message': 'Campaign not found.'})

        leads = db.execute('SELECT * FROM leads').fetchall()
        if not leads:
            return jsonify({'success': False, 'message': 'No leads found. Please upload leads first.'})

        generated = 0
        errors = []
        for lead in leads:
            try:
                # Scrape website for context if available
                context = ''
                if lead['website']:
                    context = scrape_website(lead['website'])

                # Generate personalized intro
                intro = generate_personalized_intro(
                    lead['name'], lead['company'], context
                )

                # Generate full email
                result = generate_email(
                    campaign['product'],
                    lead['company'] or 'your company',
                    campaign['pain_point'] or f'growing {lead["company"] or "their business"}',
                    campaign['tone'],
                    campaign['template_type'],
                    lead_name=lead['name'],
                    lead_company=lead['company'],
                    sender=campaign['sender'],
                    personalized_intro=intro
                )

                db.execute(
                    'INSERT INTO emails (campaign_id, lead_id, subject, body) VALUES (?, ?, ?, ?)',
                    (campaign_id, lead['id'], result['subject'], result['body'])
                )
                generated += 1
            except Exception as e:
                errors.append(f"Lead {lead['email']}: {str(e)}")

        db.commit()
        msg = f'Generated {generated} emails.'
        if errors:
            msg += f' {len(errors)} error(s) occurred.'
        return jsonify({'success': True, 'message': msg, 'count': generated})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/campaigns/<int:campaign_id>/emails')
def campaign_emails(campaign_id):
    db = get_db()
    campaign = db.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,)).fetchone()
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('campaigns'))
    emails = db.execute(
        'SELECT e.*, l.name as lead_name, l.email as lead_email, l.company '
        'FROM emails e LEFT JOIN leads l ON e.lead_id = l.id '
        'WHERE e.campaign_id = ? ORDER BY e.created_at DESC',
        (campaign_id,)
    ).fetchall()
    return render_template('campaign_emails.html', campaign=campaign, emails=emails)


# ─────────────────────────────────────────────
# ANALYTICS
# ─────────────────────────────────────────────

@app.route('/analytics')
def analytics():
    db = get_db()
    campaigns = db.execute('SELECT * FROM campaigns ORDER BY id DESC').fetchall()
    stats = []
    for c in campaigns:
        s = get_campaign_analytics(c['id'])
        s['name'] = c['name']
        s['id'] = c['id']
        stats.append(s)
    total_emails = db.execute('SELECT COUNT(*) FROM emails').fetchone()[0]
    return render_template('analytics.html', campaigns=stats, total_emails=total_emails)


@app.route('/analytics/mark-opened/<int:email_id>', methods=['POST'])
def mark_opened(email_id):
    db = get_db()
    db.execute('UPDATE emails SET opened = 1 WHERE id = ?', (email_id,))
    db.commit()
    return jsonify({'success': True})


@app.route('/analytics/mark-replied/<int:email_id>', methods=['POST'])
def mark_replied(email_id):
    db = get_db()
    db.execute('UPDATE emails SET replied = 1 WHERE id = ?', (email_id,))
    db.commit()
    return jsonify({'success': True})


# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────

@app.route('/export/<int:email_id>/<fmt>')
def export_email(email_id, fmt):
    db = get_db()
    email = db.execute('SELECT * FROM emails WHERE id = ?', (email_id,)).fetchone()
    if not email:
        flash('Email not found.', 'error')
        return redirect(url_for('index'))

    subject = email['subject']
    body = email['body']

    if fmt == 'txt':
        content, mimetype, filename = export_email_txt(subject, body)
        return send_file(
            io.BytesIO(content.encode('utf-8')),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    elif fmt == 'html':
        content, mimetype, filename = export_email_html(subject, body)
        return send_file(
            io.BytesIO(content.encode('utf-8')),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    elif fmt == 'pdf':
        pdf_bytes, mimetype, filename = export_email_pdf(subject, body)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    elif fmt == 'docx':
        docx_bytes, mimetype, filename = export_email_docx(subject, body)
        return send_file(
            io.BytesIO(docx_bytes),
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
    else:
        flash('Invalid export format.', 'error')
        return redirect(url_for('index'))


# ─────────────────────────────────────────────
# EMAIL EDIT
# ─────────────────────────────────────────────

@app.route('/email/<int:email_id>/edit', methods=['POST'])
def edit_email(email_id):
    db = get_db()
    email = db.execute('SELECT id FROM emails WHERE id = ?', (email_id,)).fetchone()
    if not email:
        return jsonify({'success': False, 'message': 'Email not found.'})
    subject = request.form.get('subject', '').strip()
    body = request.form.get('body', '').strip()
    if not subject or not body:
        return jsonify({'success': False, 'message': 'Subject and body cannot be empty.'})
    db.execute('UPDATE emails SET subject = ?, body = ? WHERE id = ?', (subject, body, email_id))
    db.commit()
    return jsonify({'success': True, 'message': 'Email saved successfully.', 'subject': subject, 'body': body})


# ─────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────

@app.route('/report/<int:email_id>', methods=['POST'])
def report_email(email_id):
    db = get_db()
    email = db.execute('SELECT id FROM emails WHERE id = ?', (email_id,)).fetchone()
    if not email:
        return jsonify({'success': False, 'message': 'Email not found.'})
    reason = request.form.get('reason', '').strip()
    db.execute(
        'INSERT INTO reports (email_id, reason) VALUES (?, ?)',
        (email_id, reason)
    )
    db.commit()
    return jsonify({'success': True, 'message': 'Report submitted. Thank you.'})


@app.route('/admin/reports/review/<int:report_id>', methods=['POST'])
def review_report(report_id):
    db = get_db()
    report = db.execute('SELECT id FROM reports WHERE id = ?', (report_id,)).fetchone()
    if not report:
        return jsonify({'success': False, 'message': 'Report not found.'})
    db.execute('UPDATE reports SET reviewed = 1 WHERE id = ?', (report_id,))
    db.commit()
    return jsonify({'success': True})


# ─────────────────────────────────────────────
# ADMIN PANEL
# ─────────────────────────────────────────────

@app.route('/admin')
def admin():
    db = get_db()
    settings = {}
    rows = db.execute('SELECT key, value FROM settings').fetchall()
    for row in rows:
        settings[row['key']] = row['value']
    reports = db.execute(
        'SELECT r.*, e.subject FROM reports r '
        'LEFT JOIN emails e ON r.email_id = e.id '
        'ORDER BY r.reported_at DESC'
    ).fetchall()
    return render_template('admin.html', settings=settings, reports=reports)


@app.route('/admin/save', methods=['POST'])
def admin_save():
    db = get_db()
    for key in request.form:
        value = request.form[key].strip()
        db.execute(
            'INSERT INTO settings (key, value) VALUES (?, ?) '
            'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
            (key, value)
        )
    db.commit()
    return jsonify({'success': True, 'message': 'Settings saved successfully.'})


# ─────────────────────────────────────────────
# PWA
# ─────────────────────────────────────────────

@app.route('/manifest.json')
def manifest():
    return send_file('static/manifest.json', mimetype='application/manifest+json')


@app.route('/service-worker.js')
def service_worker():
    response = make_response(send_file('static/service-worker.js'))
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Content-Type'] = 'application/javascript'
    return response


@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='Page not found.'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('error.html', code=500, message='An internal server error occurred.'), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
