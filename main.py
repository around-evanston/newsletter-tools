from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

from app.calendar.calendar_api import (
    authenticate_google_calendar,
    fetch_events
)

from app.data.parser import parse_all_events
from app.utils import get_date_ranges
from app.formatter.html_formatter import format_and_save_sections
from app.formatter import short_formatter
from app.formatter.roundtable_formatter import save_roundtable_html
from app.formatter.weekend_preview_formatter import save_weekend_preview_html


load_dotenv()

# Load calendar IDs from .env
# Load calendar IDs from .env
CALENDAR_IDS = {
    "Featured Events": os.getenv("FEATURED_CAL_ID"),
    "Kids and Family": os.getenv("KIDS_CAL_ID"),
    "Trivia": os.getenv("TRIVIA_CAL_ID"),
    "Save the Date": os.getenv("SAVE_THE_DATE_CAL_ID"),
    "RoundTable": os.getenv("ROUNDTABLE_CAL_ID"),
    "Live Music": os.getenv("MUSIC_CAL_ID"),
    "Weekend Preview": os.getenv("WEEKEND_PREVIEW_CAL_ID")
}


def to_iso_z(date_obj):
    return datetime.combine(date_obj, datetime.min.time()).isoformat() + "Z"

if __name__ == "__main__":
    newsletter_date = "2026-03-12"  # Change to desired Monday or Thursday
    newsletter_date_obj = datetime.strptime(newsletter_date, "%Y-%m-%d").date()

    try:
        section_ranges = get_date_ranges(newsletter_date)
    except ValueError as e:
        print(f"❌ Error: {e}")
        exit(1)

    service = authenticate_google_calendar()

    all_events = []

    for section, (start_date, end_date) in section_ranges.items():
        print(f"\n📅 Fetching {section} from {start_date} to {end_date}")

        time_min = to_iso_z(start_date)
        time_max = to_iso_z(end_date + timedelta(days=1))  # inclusive

        if section == "Live Music":
            raw_music_events = fetch_events(service, CALENDAR_IDS["Live Music"], time_min, time_max)
            parsed = parse_all_events(raw_music_events, section)

        elif section == "Trivia":
            raw_trivia_events = fetch_events(service, CALENDAR_IDS["Trivia"], time_min, time_max)
            parsed = parse_all_events(raw_trivia_events, section)

        else:
            calendar_id = CALENDAR_IDS.get(section)
            if not calendar_id:
                print(f"⚠️ No calendar ID found for {section}")
                continue

            raw_events = fetch_events(service, calendar_id, time_min, time_max)
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

    # 🟠 RoundTable Events (only on Monday newsletters)
    rt_start = newsletter_date_obj + timedelta(days=3)  # Thursday
    rt_end = rt_start + timedelta(days=6)               # through next Wednesday
    rt_time_min = to_iso_z(rt_start)
    rt_time_max = to_iso_z(rt_end + timedelta(days=1))  # inclusive

    print(f"\n📅 Fetching RoundTable events from {rt_start} to {rt_end}")
    roundtable_raw = fetch_events(service, CALENDAR_IDS["RoundTable"], rt_time_min, rt_time_max)
    kids_rt_raw = fetch_events(service, CALENDAR_IDS["Kids and Family"], rt_time_min, rt_time_max)

    roundtable_parsed = parse_all_events(roundtable_raw, "RoundTable")
    kids_parsed = parse_all_events(kids_rt_raw, "Kids and Family")

    combined_rt_events = roundtable_parsed + kids_parsed

    if combined_rt_events:
        save_roundtable_html(combined_rt_events, newsletter_date)
    else:
        print("⚠️ No RoundTable or Kids events found for RoundTable-style section.")

    # 📰 Standard newsletter formatting
    format_and_save_sections(all_events, newsletter_date)

    # 📄 Short-format sections
    for short_section in ["Live Music", "Trivia", "Save the Date"]:
        short_events = [e for e in all_events if e.section == short_section]
        if not short_events:
            continue

        # Avoid filename collision with the normal Save the Date output
        if short_section == "Save the Date":
            short_formatter.save_short_html(short_events, newsletter_date, "Save the Date Short")
        else:
            short_formatter.save_short_html(short_events, newsletter_date, short_section)


    # 🟢 Weekend Preview section (only on Monday newsletters)
    if newsletter_date_obj.weekday() == 0:  # Monday
        wp_start = newsletter_date_obj + timedelta(days=4)  # Friday
        wp_end = wp_start + timedelta(days=2)  # through Sunday
        wp_time_min = to_iso_z(wp_start)
        wp_time_max = to_iso_z(wp_end + timedelta(days=1))  # inclusive

        print(f"\n📅 Fetching Weekend Preview events from {wp_start} to {wp_end}")
        wp_raw = fetch_events(service, CALENDAR_IDS["Weekend Preview"], wp_time_min, wp_time_max)
        wp_parsed = parse_all_events(wp_raw, "Weekend Preview")

        if wp_parsed:
            save_weekend_preview_html(wp_parsed, newsletter_date)
        else:
            print("⚠️ No Weekend Preview events found.")

   