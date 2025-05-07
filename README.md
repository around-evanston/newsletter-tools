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
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure `.env`
Create a `.env` file with the following variables:
```ini
FEATURED_CAL_ID=your_featured_calendar_id
KIDS_CAL_ID=your_kids_calendar_id
MAIN_CALENDAR_ID=your_main_calendar_id
CREDENTIALS_PATH=credentials.json
TOKEN_PATH=token.json
```

### 4. Authenticate Google Calendar
When you run the script for the first time, it will open a browser window to authorize access to your Google Calendar and save a token locally.

### 5. Run the tool
```bash
python main.py
```
The script will fetch and format events for a given newsletter date and save the output in the /output folder.  Currently the newsletter date is hard coded into main.py.

## Output
Full-format HTML: One file per section (e.g. `2025-05-09-featured-events.html`)

Short-format HTML: Used for Live Music and other roundup sections (e.g. `2025-05-09-live-music.html`)

## Folder Structure
```bash
app/
├── calendar/           # Google Calendar integration
├── data/               # Event model and parser
├── formatter/          # HTML formatters for full and short layouts
├── utils.py            # Shared formatting and link helpers
output/                 # Generated HTML files
main.py                 # Main execution script
```

## Future Plans
- Add optional preview UI

- Support for selecting sections and dates via CLI

- Mailchimp API integration for pushing drafts directly