from datetime import datetime, timedelta
import logging
import re

def get_date_ranges(newsletter_date):
    """
    Given a newsletter date (YYYY-MM-DD), return a dictionary of calendar names
    and their corresponding (start, end) date ranges for fetching events.
    
    Raises ValueError if the date is not a Monday or Thursday.
    """
    if isinstance(newsletter_date, str):
        newsletter_date = datetime.strptime(newsletter_date, "%Y-%m-%d").date()

    weekday = newsletter_date.weekday()

    if weekday == 0:  # Monday
        featured_range = (newsletter_date, newsletter_date + timedelta(days=3))  # Mon–Thu
        music_range = (newsletter_date, newsletter_date + timedelta(days=6))     # Mon–Sun
        save_the_date_range = (newsletter_date, newsletter_date + timedelta(days=35))
    elif weekday == 3:  # Thursday
        featured_range = (newsletter_date, newsletter_date + timedelta(days=3))  # Thu–Sun
        music_range = (newsletter_date, newsletter_date + timedelta(days=6))     # Thu–Wed (next week)
        save_the_date_range = (newsletter_date, newsletter_date + timedelta(days=35))
    else:
        raise ValueError("Newsletter date must be a Monday or Thursday.")

    return {
        "Featured Events": featured_range,
        "Kids and Family": featured_range,
        "Live Music": music_range,
        "Trivia": featured_range,
        "Save the Date": save_the_date_range
    }

import logging

def get_button_image(button_text):
    """Always return the 'More Info' button image, regardless of original label."""
    if not button_text:
        logging.warning("No button text provided.")
        return ''
    
    return 'https://mcusercontent.com/5d7191785ee79531ada025107/images/636e5c2b-90e4-cfb3-be68-9f6a4966c9f1.png'




def format_time(time_str: str) -> str:
    """
    Format time strings to 'H:MM AM/PM' format, including ranges like '10:00 - 12:00'.
    Also normalizes all dash types to short hyphens with spaces.
    """
    # Normalize dash types (em dash, en dash, figure dash, etc.) to " - "
    time_str = re.sub(r'\s*[\u2012\u2013\u2014\u2015\u2212\-]\s*', ' - ', time_str)

    def format_match(m):
        hour, minute, period = m.groups()
        hour = int(hour)
        minute = minute or "00"
        period = period.upper() if period else ('AM' if hour < 12 else 'PM')
        return f"{hour}:{minute} {period}"

    time_pattern = re.compile(r'(\d{1,2}):?(\d{2})?\s*(AM|PM)?', re.IGNORECASE)
    return time_pattern.sub(format_match, time_str)

def format_cost(cost_str: str) -> str:
    """
    Normalize dollar values in cost string. '$5' becomes '$5.00'.

    Only formats numbers prefixed with '$'. Leaves non-numeric cost info unchanged.
    """
    def normalize_cost(m):
        amount = m.group(1)
        if '.' not in amount:
            amount += '.00'
        return amount

    pattern = re.compile(r'(\$\d+(?:\.\d{1,2})?)')
    return pattern.sub(normalize_cost, cost_str)


def format_times_in_description(text: str) -> str:
    """
    Parses and reformats time ranges using datetime,
    only changing separators between time expressions.
    Leaves non-time text (like 'Evanston' or 'Chicago-Calumet') untouched.
    """

    # Step 1: Normalize AM/PM casing and remove periods
    text = re.sub(r'\b(a\.?m\.?|p\.?m\.?)\b', lambda m: m.group(0).replace('.', '').upper(), text, flags=re.IGNORECASE)

    # Step 2: Replace time ranges with normalized " - " and reformatted time
    time_range_pattern = re.compile(
        r'\b(\d{1,2})(?::(\d{2}))?\s*(AM|PM)\s*(to|–|—|−|-)\s*(\d{1,2})(?::(\d{2}))?\s*(AM|PM)\b',
        flags=re.IGNORECASE
    )

    def replace_range(match):
        h1, m1, mer1, sep, h2, m2, mer2 = match.groups()
        m1 = int(m1) if m1 else 0
        m2 = int(m2) if m2 else 0
        t1 = datetime.strptime(f"{int(h1)}:{m1:02d} {mer1.upper()}", "%I:%M %p")
        t2 = datetime.strptime(f"{int(h2)}:{m2:02d} {mer2.upper()}", "%I:%M %p")
        return f"{t1.strftime('%-I:%M %p')} - {t2.strftime('%-I:%M %p')}"

    text = time_range_pattern.sub(replace_range, text)

    # Step 3: Handle standalone times (not part of ranges)
    time_pattern = re.compile(r'\b(\d{1,2})(?::(\d{2}))?\s*(AM|PM)\b', re.IGNORECASE)

    def replace_single(match):
        h, m, mer = match.groups()
        m = int(m) if m else 0
        t = datetime.strptime(f"{int(h)}:{m:02d} {mer.upper()}", "%I:%M %p")
        return t.strftime("%-I:%M %p")

    text = time_pattern.sub(replace_single, text)

    return text