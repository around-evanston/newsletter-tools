import os
from datetime import datetime
from collections import defaultdict

def generate_short_event_html(event):
    """Generate a one-line HTML snippet for a single event."""
    # Build link with title
    if event.button_url:
        title_html = (
            f'<a href="{event.button_url}" target="_blank" tabindex="-1" style="color: #E54F25;">'
            f'<span style="color:rgb(229, 79, 37);">{event.title}</span></a>'
        )
    else:
        title_html = f'<span style="color:rgb(229, 79, 37);">{event.title}</span>'

    # Add parenthetical part back if needed
    if "(" in event.title and ")" in event.title:
        parenthetical = event.title[event.title.find("("):event.title.find(")") + 1]
        if parenthetical not in title_html:
            title_html += f" {parenthetical}"

    # Build full sentence
    pieces = [title_html]
    if event.location_name:
        pieces.append(f'at {event.location_name}')
    if event.short_time:
        pieces.append(f'{event.short_time}')
    if event.formatted_cost:
        pieces.append(f'{event.formatted_cost}')

    return f'<li><p>{", ".join(pieces)}</p></li>'

def generate_short_html(events, newsletter_date):
    """Group events by date and generate HTML output."""
    grouped = defaultdict(list)
    for event in events:
        grouped[event.date.strftime("%A, %B %-d")].append(event)

    html_output = '<p style="padding: 10px 0;"><em>Click the included links for info and tickets!</em></p><p></p>'

    for display_date in sorted(grouped.keys(), key=lambda d: datetime.strptime(d, "%A, %B %d")):
        html_output += f'<p><strong>{display_date}</strong></p><ul>'
        for event in sorted(grouped[display_date], key=lambda e: e.parsed_start_time):
            html_output += generate_short_event_html(event)
        html_output += '</ul><p></p>'

    return html_output

def save_short_html(events, newsletter_date, section_name):
    """Save the short HTML output to a file."""
    os.makedirs("output", exist_ok=True)
    html = generate_short_html(events, newsletter_date)
    filename = f"output/{newsletter_date}-{section_name.lower().replace(' ', '-')}.html"
    with open(filename, "w") as f:
        f.write(html)
    print(f"✅ Saved short-format HTML for {section_name} to {filename}")

