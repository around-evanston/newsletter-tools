import os
from datetime import datetime
from app.utils import get_button_image

def generate_event_html(event):
    """Generate HTML block for a single Event object."""
    location_html = f'<em>Time: {event.formatted_time}<br>Cost: {event.formatted_cost}<br>'
    if event.location_url:
        location_html += f'Location: <a href="{event.location_url}" tabindex="-1">{event.location_name}</a></em>'
    else:
        location_html += f'Location: {event.location_name}</em>'

    event_html = f"""
    <h4>{event.title}</h4>
    <p>{location_html}<br><br>{event.description}</p>
    """

    if event.button_text and event.button_url and event.button_image_url:
        height = 45  # All buttons use the same image now
        event_html += f"""
        <p style="text-align: center;">
            <a href="{event.button_url}" target="_blank" tabindex="-1" style="display: inline-block; padding: 30px 0px;">
                <img src="{event.button_image_url}" alt="Rounded orange button with 'More Info' text" style="height:{height}px !important;width:auto !important;max-height:{height}px !important;border-radius:0;display:block" width="auto" height="{height}" class="mceImage">
            </a>
        </p>
        """


    return event_html

def generate_section_html(events, section_name):
    sorted_events = sorted(events, key=lambda e: (e.date, e.parsed_start_time))

    # Split into All Weekend and others
    all_weekend_events = [e for e in sorted_events if e.is_all_weekend]
    regular_events = [e for e in sorted_events if not e.is_all_weekend]

    html_content = ""

    if all_weekend_events:
        html_content += '<h3 style="padding-top: 20px; padding-bottom: 20px;">All Weekend</h3>'
        for event in all_weekend_events:
            html_content += generate_event_html(event)
        html_content += """
        <table width="100%" border="0" cellspacing="0" cellpadding="0">
            <tbody><tr><td style="padding-top: 20px;">
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                    <tbody><tr><td style="border-top: 2px solid #e54f25;"><p></p></td></tr></tbody>
                </table>
            </td></tr></tbody>
        </table>
        """

    last_date = None
    for event in regular_events:
        current_date = event.date.strftime("%A, %B %-d")

        if current_date != last_date:
            if last_date is not None:
                html_content += """
                <table width="100%" border="0" cellspacing="0" cellpadding="0">
                    <tbody><tr><td style="padding-top: 20px;">
                        <table width="100%" border="0" cellspacing="0" cellpadding="0">
                            <tbody><tr><td style="border-top: 2px solid #e54f25;"><p></p></td></tr></tbody>
                        </table>
                    </td></tr></tbody>
                </table>
                """
            html_content += f'<h3 style="padding-top: 20px; padding-bottom: 20px;">{current_date}</h3>'
            last_date = current_date

        html_content += generate_event_html(event)

    return html_content


def save_html_to_file(html, section_name, newsletter_date):
    """Save the generated HTML to a file in /output."""
    os.makedirs("output", exist_ok=True)
    filename = f"output/{newsletter_date}-{section_name.lower().replace(' ', '-')}.html"
    with open(filename, "w") as f:
        f.write(html)
    print(f"✅ Saved {section_name} HTML to {filename}")

def format_and_save_sections(events, newsletter_date):
    """Group events by section and save HTML output for each."""
    from collections import defaultdict

    sections = defaultdict(list)
    for event in events:
        if event.section != "Live Music":  # Skip music for now
            sections[event.section].append(event)

    for section_name, section_events in sections.items():
        html = generate_section_html(section_events, section_name)
        save_html_to_file(html, section_name, newsletter_date)
