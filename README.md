# newsletter_tools

# newsletter-tools

A set of tools for generating HTML newsletters from Google Calendar event data. Designed for semi-automated production of the *Around Evanston* email newsletter.

## Features

- Pulls and parses events from Google Calendar
- Categorizes events by section (Featured, Kids and Family, Live Music, etc.)
- Formats event data into clean, styled HTML for newsletter use
- Supports both full-format and short-format outputs
- Detects and handles multi-day events (including "All Weekend")
- Filters and cleans button URLs (removes Google redirects)

## Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/your-username/newsletter-tools.git
cd newsletter-tools
```

### 2. Set up the virtual environment

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

