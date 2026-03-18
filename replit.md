# Cold Email Generator

## Overview
A full-stack AI-powered cold email generation web app built with Python/Flask, SQLite, and the Groq API (llama3-70b-8192).

## Features
- **Email Generator** – Generate cold emails with 4 templates (Short Pitch, Problem-Solution, Quick Intro, Partnership) and 4 tones
- **Lead Management** – CSV upload, storage, and management of leads
- **Lead Scraping** – BeautifulSoup scraper for company website context
- **AI Personalization** – Unique Groq-powered personalized intro per lead
- **Campaigns** – Create campaigns, run bulk email generation for all leads
- **Campaign Analytics** – Track opens, replies, open rate, reply rate
- **Export** – TXT, HTML, PDF export (server-side via FPDF2)
- **Admin Panel** – Customize app name, sender, model, tone, template
- **PWA** – Service worker, manifest, install prompt, offline caching

## Tech Stack
- Python 3.11, Flask
- SQLite (database.db)
- Groq API (llama3-70b-8192)
- BeautifulSoup4 for web scraping
- FPDF2 for PDF generation
- Pillow for icon generation
- Gunicorn (production)

## Project Structure
```
app.py               # Main Flask app (routes)
config.py            # Configuration constants
models/db.py         # SQLite init & get_db()
services/
  ai_service.py      # Groq API email generation
  lead_scraper.py    # BeautifulSoup web scraper
  personalization.py # Per-lead AI intro generation
  campaign_service.py# Campaign CRUD
  analytics.py       # Campaign metrics
  export_service.py  # TXT/HTML/PDF export
templates/
  base.html          # Base layout + sidebar + PWA
  index.html         # Email generator
  leads.html         # Lead management + CSV upload
  campaign.html      # Campaign list + create form
  campaign_emails.html # Per-campaign email viewer
  analytics.html     # Analytics dashboard
  admin.html         # Admin settings panel
static/
  style.css          # Dark theme responsive CSS
  manifest.json      # PWA manifest
  service-worker.js  # PWA service worker
  icons/             # 512px icons (regular + maskable)
```

## Environment Variables
- `GROQ_API_KEY` (required) – Get from console.groq.com

## Running
Development: `python app.py`
Production: `gunicorn --bind=0.0.0.0:5000 --reuse-port app:app`

## Port
- Always runs on port 5000 (host 0.0.0.0)
