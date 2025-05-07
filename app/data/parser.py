import re
import html
from app.data.event_model import Event
from datetime import datetime, timedelta

def strip_html_tags(text):
    """Remove simple HTML tags from a string."""
    return re.sub(r'<[^>]+>', '', text)

def clean_google_redirect_url(url):
    """If the URL is a Google redirect, extract the real URL."""
    match = re.match(r'https://www\.google\.com/url\?q=(https?[^&]+)', url)
    return match.group(1) if match else url

def parse_event(raw_event, section):
    """
    Parses a raw Google Calendar event dict into an Event object.
    """
    raw_description = html.unescape(raw_event.get("description", "")).replace('\xa0', ' ')
    raw_description = raw_description.replace('<br>', '\n')

    def extract(pattern, text, default=""):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else default

    # Improved location handling
    loc_match = re.search(
        r'Loc:\s*Link\(\s*([^,]+?),\s*(?:<a href=")?(https?[^)">]+)', raw_description
    )

    if loc_match:
        location_name = loc_match.group(1).strip()
        location_url = clean_google_redirect_url(loc_match.group(2).strip())
    else:
        fallback_match = re.search(r'Loc:\s*Link\(\s*([^,]+?),\s*<a>(https?[^<]+)</a>', raw_description)
        location_name = fallback_match.group(1).strip() if fallback_match else extract(r'Loc:\s*(.*?)\n', raw_description)
        location_url = clean_google_redirect_url(fallback_match.group(2).strip()) if fallback_match else ''

    # Extract other fields
    title = strip_html_tags(extract(r'Title:\s*(.*?)\n', raw_description))
    time = extract(r'Time:\s*(.*?)\n', raw_description)
    cost = extract(r'Cost:\s*(.*?)\n', raw_description)
    description = extract(r'Desc:\s*(.*?)(?:\n|$)', raw_description)  # Allow HTML in description

    button_match = re.search(r'Button\(([^,]+),\s*(?:<a href=")?(https?[^">]+)?', raw_description)
    button_text = button_match.group(1).strip() if button_match else ''

    raw_button_url = button_match.group(2).strip() if button_match and button_match.group(2) else ''
    button_url = clean_google_redirect_url(raw_button_url)

    # Extract and normalize end date
    raw_end = raw_event.get("end", "")
    end_str = raw_end.get("dateTime") or raw_end.get("date") or ""
    end_date = None

    if end_str:
        try:
            # Convert string to datetime.date
            end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00')).date()
            # All-day events end on the *next* day in Google Calendar, so subtract one day
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
