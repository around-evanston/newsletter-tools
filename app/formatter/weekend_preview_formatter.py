import os

def generate_weekend_preview_html(events, newsletter_date):
    """Group events by day of the week and output as simple title links under weekday headings."""
    from collections import defaultdict

    grouped = defaultdict(list)
    for e in events:
        day = e.date.strftime("%A")
        grouped[day].append(e)

    html = ""
    for day in ["Friday", "Saturday", "Sunday"]:
        if day in grouped:
            html += f"<p><strong>{day}</strong></p>\n<ul>\n"
            for e in grouped[day]:
                html += f'<li><a href="{e.button_url}" target="_blank" style="color: #E54F25; text-decoration: underline;">{e.title}</a></li>\n'
            html += "</ul>\n"

    return html

def save_weekend_preview_html(events, newsletter_date):
    html = generate_weekend_preview_html(events, newsletter_date)

    os.makedirs("output", exist_ok=True)
    filename = f"output/{newsletter_date}-weekend-preview.html"
    with open(filename, "w") as f:
        f.write(html)

    print(f"✅ Saved Weekend Preview HTML to {filename}")
