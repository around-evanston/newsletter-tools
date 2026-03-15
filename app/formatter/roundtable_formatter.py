import os
import re
from datetime import datetime, date


def _meridiem(dt: datetime) -> str:
    # "AM"/"PM" -> "a.m."/"p.m."
    return dt.strftime('%p').lower().replace('am', 'a.m.').replace('pm', 'p.m.')

def _format_single_time(dt: datetime) -> str:
    # "7:00 PM" -> "7 p.m." ; "7:30 PM" -> "7:30 p.m."
    hour = dt.strftime('%I').lstrip('0') or '0'
    minute = dt.strftime('%M')
    if minute == '00':
        return f"{hour} {_meridiem(dt)}"
    return f"{hour}:{minute} {_meridiem(dt)}"

def _format_time_range(start: datetime, end: datetime) -> str:
    # 7:00 PM - 9:00 PM -> 7 to 9 p.m.
    # 7:30 PM - 9:00 PM -> 7:30 to 9 p.m.
    # 11:30 AM - 1:00 PM -> 11:30 a.m. to 1 p.m.
    same_mer = start.strftime('%p') == end.strftime('%p')
    start_hour = start.strftime('%I').lstrip('0') or '0'
    start_min = start.strftime('%M')
    if start_min == '00':
        start_str = start_hour
    else:
        start_str = f"{start_hour}:{start_min}"

    end_str = _format_single_time(end)

    if same_mer:
        # drop meridiem from the start when both are AM or both PM
        return f"{start_str} to {end_str}"
    else:
        # include meridiem on both when they differ
        return f"{_format_single_time(start)} to {end_str}"

def _first_attr(obj, names: list[str]):
    """Return first non-None attribute value found on obj from names."""
    for n in names:
        if hasattr(obj, n):
            v = getattr(obj, n)
            if v is not None:
                return v
    return None

def format_time_display(event) -> str:
    """
    Prefer parsed datetimes if present. Falls back to event.formatted_time or event.time_raw,
    but normalizes common separators via _normalize_time_text.
    Accepts multiple possible attr names for robustness.
    """
    start = _first_attr(event, [
        'parsed_start_time', 'start_time', 'parsed_start', 'start', 'start_dt'
    ])
    end = _first_attr(event, [
        'parsed_end_time', 'end_time', 'parsed_end', 'end', 'end_dt'
    ])

    # Handle all-day or missing times entirely
    if getattr(event, 'all_day', False) or (start is None and end is None):
        return ""

    # If we have both, show the range (this is what ensures END TIMES show)
    if isinstance(start, datetime) and isinstance(end, datetime):
        return _format_time_range(start, end)

    # Start only
    if isinstance(start, datetime):
        return _format_single_time(start)

    # Fallback: use any provided raw/formatted time string and normalize it
    raw = getattr(event, 'formatted_time', None) or getattr(event, 'time_raw', None) or ""
    # Normalize things like "1-3 PM" -> "1 to 3 p.m.", ":00" removal, a.m./p.m. style, etc.
    return _normalize_time_text(raw)

def is_all_month(start: date, end: date) -> bool:
    """Return True if the event spans at least 15 days starting within a single month."""
    if not start or not end:
        return False
    event_span = (end - start).days + 1
    return event_span >= 15

def _norm_mer(mer: str | None) -> str | None:
    if not mer:
        return None
    mer = mer.strip().lower().replace('.', '')
    if mer in ('am', 'a', 'a.m', 'a.m.'):
        return 'a.m.'
    if mer in ('pm', 'p', 'p.m', 'p.m.'):
        return 'p.m.'
    return None

def _fmt_hm(hour: str, minute: str | None, mer: str | None, include_mer: bool = True) -> str:
    # strip leading zero on hour
    h = str(int(hour))  # '07' -> '7'
    # keep minutes only if not '00'
    body = h if not minute or minute == '00' else f"{h}:{minute}"
    return f"{body} {mer}" if (include_mer and mer) else body

def _normalize_time_text(text: str) -> str:
    """
    Normalize time expressions in free text to RoundTable style:
      - a.m./p.m. lowercase with periods
      - drop :00
      - use ' to ' for ranges, show meridiem once if same
    Operates ONLY on detected time patterns; other hyphenated ranges are untouched.
    """
    if not text:
        return text

    # 1) RANGES with meridiem on the END (common: '12–1:00 PM', '1-3 PM', '11:30–1 p.m.')
    range_end_mer = re.compile(
        r'\b'
        r'(?P<h1>\d{1,2})(?::(?P<m1>\d{2}))?\s*(?P<mer1>a\.?m\.?|p\.?m\.?|AM|PM)?'
        r'\s*[–—-]\s*'
        r'(?P<h2>\d{1,2})(?::(?P<m2>\d{2}))?\s*(?P<mer2>a\.?m\.?|p\.?m\.?|AM|PM)'
        r'\b'
    )

    def _sub_range_end(match: re.Match) -> str:
        h1, m1, mer1 = match.group('h1', 'm1', 'mer1')
        h2, m2, mer2 = match.group('h2', 'm2', 'mer2')
        mer1n, mer2n = _norm_mer(mer1), _norm_mer(mer2)

        # same meridiem (or start missing): show mer once at the end
        if (mer1n is None) or (mer1n == mer2n):
            left = _fmt_hm(h1, m1, None, include_mer=False)
            right = _fmt_hm(h2, m2, mer2n, include_mer=True)
            return f"{left} to {right}"
        else:
            # differing meridiems: include both
            left = _fmt_hm(h1, m1, mer1n, include_mer=True)
            right = _fmt_hm(h2, m2, mer2n, include_mer=True)
            return f"{left} to {right}"

    text = range_end_mer.sub(_sub_range_end, text)

    # 2) RANGES with meridiem on BOTH ends (e.g., '9 AM–11 AM', '11:30 a.m.-1 p.m.')
    range_both_mer = re.compile(
        r'\b'
        r'(?P<h1>\d{1,2})(?::(?P<m1>\d{2}))?\s*(?P<mer1>a\.?m\.?|p\.?m\.?|AM|PM)'
        r'\s*[–—-]\s*'
        r'(?P<h2>\d{1,2})(?::(?P<m2>\d{2}))?\s*(?P<mer2>a\.?m\.?|p\.?m\.?|AM|PM)'
        r'\b'
    )

    def _sub_range_both(match: re.Match) -> str:
        h1, m1, mer1 = match.group('h1', 'm1', 'mer1')
        h2, m2, mer2 = match.group('h2', 'm2', 'mer2')
        mer1n, mer2n = _norm_mer(mer1), _norm_mer(mer2)
        if mer1n == mer2n:
            # same meridiem: drop from left
            left = _fmt_hm(h1, m1, None, include_mer=False)
            right = _fmt_hm(h2, m2, mer2n, include_mer=True)
            return f"{left} to {right}"
        else:
            left = _fmt_hm(h1, m1, mer1n, include_mer=True)
            right = _fmt_hm(h2, m2, mer2n, include_mer=True)
            return f"{left} to {right}"

    text = range_both_mer.sub(_sub_range_both, text)

    # 3) STANDALONE times (e.g., '7:00 PM', '10am', '6 p.m.')
    standalone = re.compile(
        r'\b(?P<h>\d{1,2})(?::(?P<m>\d{2}))?\s*(?P<mer>a\.?m\.?|p\.?m\.?|AM|PM)\b'
    )

    def _sub_standalone(match: re.Match) -> str:
        h, m, mer = match.group('h', 'm', 'mer')
        return _fmt_hm(h, m, _norm_mer(mer), include_mer=True)

    text = standalone.sub(_sub_standalone, text)
    # --- fix accidental extra periods after meridiem ---
    # e.g., 'p.m...' or 'p.m..' -> 'p.m.'
    text = re.sub(r'\b(a\.m\.|p\.m\.)\.{2,3}(?!\.)', r'\1.', text)
    text = re.sub(r'\b(a\.m\.|p\.m\.)\.(?!\.)', r'\1', text)

    return text

def generate_roundtable_html(events, newsletter_date):
    """Generate HTML for Evanston RoundTable event list format with clickable bolded/underlined titles."""

    all_month_events = []
    dated_events = []

    for event in events:
        if is_all_month(event.date, event.end_date):
            all_month_events.append(event)
        else:
            dated_events.append(event)

    html = ""

    # 🟠 All Month section
    if all_month_events:
        html += "<p><strong>All Month</strong></p>\n"
        for event in all_month_events:
            linked_title = (
                f'<a href="{event.button_url}" target="_blank" tabindex="-1" style="color: #666666;">'
                f'<strong><u>{event.title}</u></strong></a>'
                if event.button_url else f'<strong><u>{event.title}</u></strong>'
            )

            location_part = (
                f'<a href="{event.location_url}" tabindex="-1" style="color: #666666;">{event.location_name}</a>'
                if event.location_url else event.location_name
            )

            time_display = format_time_display(event)

            header_line = f"{linked_title}, {time_display}, {location_part}.".strip(", ")
            sanitized_desc = _normalize_time_text(event.description)
            html += f"<p>&bull; {header_line} {sanitized_desc}</p>\n"
        html += "<br>"

    # 📅 Dated Events section
    # Keep existing sort; if some events lack parsed_start_time, getattr returns None
    sorted_events = sorted(dated_events, key=lambda e: (e.date, getattr(e, 'parsed_start_time', None)))
    last_date = None

    for event in sorted_events:
        current_date = event.date.strftime("%A, %B %-d")

        if current_date != last_date:
            if last_date is not None:
                html += "<br>"
            html += f"<p><strong>{current_date}</strong></p>\n"
            last_date = current_date

        linked_title = (
            f'<a href="{event.button_url}" target="_blank" tabindex="-1" style="color: #666666;">'
            f'<strong><u>{event.title}</u></strong></a>'
            if event.button_url else f'<strong><u>{event.title}</u></strong>'
        )

        location_part = (
            f'<a href="{event.location_url}" tabindex="-1" style="color: #666666;">{event.location_name}</a>'
            if event.location_url else event.location_name
        )

        time_display = format_time_display(event)

        header_line = f"{linked_title}, {time_display}, {location_part}.".strip(", ")
        sanitized_desc = _normalize_time_text(event.description)
        html += f"<p>&bull; {header_line} {sanitized_desc}</p>\n"

    return html

def save_roundtable_html(events, newsletter_date):
    """Generate and save RoundTable-style HTML."""
    html = generate_roundtable_html(events, newsletter_date)

    os.makedirs("output", exist_ok=True)
    filename = f"output/{newsletter_date}-roundtable.html"

    with open(filename, "w") as f:
        f.write(html)

    print(f"✅ Saved RoundTable HTML to {filename}")
