import re
import html
from bs4 import BeautifulSoup
from app.data.event_model import Event
from datetime import datetime, timedelta
from app.utils import format_times_in_description

def strip_html_tags(text):
    return ''.join(BeautifulSoup(text, "html.parser").stripped_strings)

def clean_google_redirect_url(url):
    match = re.match(r'https://www\.google\.com/url\?q=(https?[^&]+)', url)
    return match.group(1) if match else url

def parse_event(raw_event, section):
    raw_description = html.unescape(raw_event.get("description", "")).replace('\xa0', ' ').replace('<br>', '\n')
    soup = BeautifulSoup(raw_description, "html.parser")
    text = soup.get_text()

    def extract(pattern, default=""):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else default

    # --- Location Handling ---
    location_name = ''
    location_url = ''

    loc_match = re.search(r'Loc:\s*Link\(([^,]+?),\s*(https?[^)\n]+)', text)
    if loc_match:
        location_name = loc_match.group(1).strip()
        location_url = clean_google_redirect_url(loc_match.group(2).strip())
    else:
        location_name = extract(r'Loc:\s*(.*?)\n')
        location_url = ''

    # --- Field Extraction ---
    title = extract(r'Title:\s*(.*?)\n')
    time = extract(r'Time:\s*(.*?)\n')
    cost = extract(r'Cost:\s*(.*?)\n')
    description = extract(r'Desc:\s*(.*?)(?:\n|$)')

    # Extract description and format time strings within it
    description = format_times_in_description(description)

    # --- Button ---
    button_text = ''
    button_url = ''

    button_match = re.search(r'Button\(([^,]+),\s*(https?[^)\n]+)', text)
    if button_match:
        button_text = button_match.group(1).strip()
        button_url = clean_google_redirect_url(button_match.group(2).strip())

    # --- End Date ---
    raw_end = raw_event.get("end", "")
    end_str = raw_end.get("dateTime") or raw_end.get("date") or ""
    end_date = None

    if end_str:
        try:
            end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date()
            if 'date' in raw_end:
                end_dt = end_dt - timedelta(days=1)
            end_date = end_dt
        except Exception as e:
            print(f"⚠️ Could not parse end date: {end_str} — {e}")

    return Event(
        date=raw_event.get("start"),
        end_date=end_date,
        section=section,
        title=title,
        time=time,
        cost=cost,
        location_name=location_name,
        location_url=location_url,
        description=description,
        button_text=button_text,
        button_url=button_url
    )

def parse_all_events(event_list, section):
    return [parse_event(e, section) for e in event_list]
