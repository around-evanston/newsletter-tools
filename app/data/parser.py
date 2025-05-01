import re
import html
from app.data.event_model import Event

def strip_html_tags(text):
    """Remove simple HTML tags from a string."""
    return re.sub(r'<[^>]+>', '', text)

def parse_event(raw_event, section):
    """
    Parses a raw Google Calendar event dict into an Event object.
    """
    raw_description = html.unescape(raw_event.get("description", "")).replace('\xa0', ' ')
    raw_description = raw_description.replace('<br>', '\n')

    def extract(pattern, text, default=""):
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        return match.group(1).strip() if match else default

    title = strip_html_tags(extract(r'Title:\s*(.*?)\n', raw_description))
    time = extract(r'Time:\s*(.*?)\n', raw_description)
    cost = extract(r'Cost:\s*(.*?)\n', raw_description)

    loc_match = re.search(r'Loc:\s*Link\(([^,]+),\s*(?:<a href=")?(https?[^">]+)', raw_description)
    location_name = loc_match.group(1).strip() if loc_match else extract(r'Loc:\s*(.*?)\n', raw_description)
    location_url = loc_match.group(2).strip() if loc_match else ''

    description = strip_html_tags(extract(r'Desc:\s*(.*?)(?:\n|$)', raw_description))

    button_match = re.search(r'Button\(([^,]+),\s*(?:<a href=")?(https?[^">]+)?', raw_description)
    button_text = button_match.group(1).strip() if button_match else ''
    button_url = button_match.group(2).strip() if button_match and button_match.group(2) else ''

    return Event(
        start=raw_event.get("start"),
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
