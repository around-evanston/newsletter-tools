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
    elif weekday == 3:  # Thursday
        featured_range = (newsletter_date, newsletter_date + timedelta(days=3))  # Thu–Sun
        music_range = (newsletter_date, newsletter_date + timedelta(days=6))     # Thu–Wed (next week)
    else:
        raise ValueError("Newsletter date must be a Monday or Thursday.")

    return {
        "Featured Events": featured_range,
        "Kids and Family": featured_range,
        "Live Music": music_range
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

    Examples:
    '9:30' → '9:30 AM'
    '10:00 - 12:00' → '10:00 AM - 12:00 PM'
    """
    def format_match(m):
        hour, minute, period = m.groups()
        hour = int(hour)
        minute = minute or "00"
        period = period.upper() if period else ('AM' if hour < 12 else 'PM')
        return f"{hour}:{minute} {period}"

    # Matches: 9:00, 9:00am, 09:00 AM, etc.
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
