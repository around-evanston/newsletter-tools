from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from app.calendar.calendar_api import (
    authenticate_google_calendar,
    fetch_events,
    fetch_event_colors
)
from app.data.parser import parse_all_events
from app.utils import get_date_ranges

load_dotenv()

# Load calendar IDs from .env
CALENDAR_IDS = {
    "Featured Events": os.getenv("FEATURED_CAL_ID"),
    "Kids and Family": os.getenv("KIDS_CAL_ID"),
}
MAIN_CALENDAR_ID = os.getenv("MAIN_CALENDAR_ID")
MUSIC_COLOR_HEX = '#5484ed'  # The color used to identify music events

def to_iso_z(date_obj):
    return datetime.combine(date_obj, datetime.min.time()).isoformat() + "Z"

if __name__ == "__main__":
    newsletter_date = "2025-05-08"  # Change to desired Monday or Thursday

    try:
        section_ranges = get_date_ranges(newsletter_date)
    except ValueError as e:
        print(f"❌ Error: {e}")
        exit(1)

    service = authenticate_google_calendar()
    event_colors = fetch_event_colors(service)

    all_events = []

    for section, (start_date, end_date) in section_ranges.items():
        print(f"\n📅 Fetching {section} from {start_date} to {end_date}")

        time_min = to_iso_z(start_date)
        time_max = to_iso_z(end_date + timedelta(days=1))  # inclusive

        # Special case for Live Music (comes from main calendar + color filter)
        if section == "Live Music":
            raw_music_events = fetch_events(service, MAIN_CALENDAR_ID, time_min, time_max, event_colors)

            filtered_music = []
            for event in raw_music_events:
                color_id = event.get('colorId')
                if color_id:
                    hex_code = event_colors.get(color_id, {}).get('background')
                    if hex_code == MUSIC_COLOR_HEX:
                        filtered_music.append(event)

            parsed = parse_all_events(filtered_music, section)

        else:
            calendar_id = CALENDAR_IDS.get(section)
            if not calendar_id:
                print(f"⚠️ No calendar ID found for {section}")
                continue

            raw_events = fetch_events(service, calendar_id, time_min, time_max, event_colors)
            parsed = parse_all_events(raw_events, section)

        all_events.extend(parsed)

    print(f"\n✅ Total events pulled: {len(all_events)}")
for event in all_events:
    print(f"\n{event.date} — {event.section}")

    print(f"  Title: {event.title}")
    print(f"  Start Date: {event.date}")
    print(f"  End Date: {event.end_date}")
    print(f"  All Weekend: {event.is_all_weekend}")
    print(f"  Time: {event.time_raw}")
    print(f"  Time Formatted: {event.formatted_time}")
    print(f"  Cost: {event.cost_raw}")
    print(f"  Cost Formatted: {event.formatted_cost}")

    if event.section == "Live Music":
        print(f"  Location: {event.location_name}")
        print(f"  Button URL: {event.button_url}")
    else:
        print(f"  Location: {event.location_name} → {event.location_url}")
        print(f"  Description: {event.description}")
        print(f"  Button: {event.button_text} → {event.button_url}")

from app.formatter.html_formatter import format_and_save_sections

# After all_events is populated
format_and_save_sections(all_events, newsletter_date)

from app.formatter import short_formatter

# Filter events for the short-format section, e.g. "Live Music"
short_section = "Live Music"
short_events = [e for e in all_events if e.section == short_section]

# Only generate the file if there are matching events
if short_events:
    short_formatter.save_short_html(short_events, newsletter_date, short_section)