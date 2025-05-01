from datetime import datetime, timedelta

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
