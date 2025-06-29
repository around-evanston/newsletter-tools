import os
from datetime import datetime

def generate_roundtable_html(events, newsletter_date):
    """Generate HTML for Evanston RoundTable event list format with clickable bolded/underlined titles."""
    sorted_events = sorted(events, key=lambda e: (e.date, e.parsed_start_time))

    last_date = None
    html = ""

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

        header_line = f'{linked_title}, {event.formatted_time}, {location_part}.'
        html += f"<p>&bull; {header_line} {event.description}</p>\n"

    return html

def save_roundtable_html(events, newsletter_date):
    """Generate and save RoundTable-style HTML."""
    html = generate_roundtable_html(events, newsletter_date)

    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    filename = f"output/{newsletter_date}-roundtable.html"

    with open(filename, "w") as f:
        f.write(html)

    print(f"✅ Saved RoundTable HTML to {filename}")
