from app.utils import format_time, format_cost
from datetime import datetime, timedelta
from app.utils import get_button_image

class Event:
    def __init__(self, date, end_date, section, title="", time="", cost="",
                 location_name="", location_url="", description="",
                 button_text="", button_url=""):
        
        
        self.date = datetime.strptime(date, "%Y-%m-%d").date() if isinstance(date, str) else date
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d").date() if isinstance(end_date, str) else end_date
        self.section = section  # <- This links it to Featured, Kids, etc.
        self.title = title
        self.time_raw = time
        self.cost_raw = cost
        self.location_name = location_name
        self.location_url = location_url
        self.description = description
        self.button_text = button_text
        self.button_url = button_url

    def is_blank(self):
        fields = [
            self.title, self.time, self.cost, self.location_name,
            self.location_url, self.description, self.button_text, self.button_url
        ]
        return all(not f for f in fields)

    def to_dict(self):
        return self.__dict__

    def __str__(self):
        return f"{self.date} — {self.section} — {self.title}"

    @property
    def formatted_time(self):
        return format_time(self.time_raw) if self.time_raw else ""

    @property
    def formatted_cost(self):
        return format_cost(self.cost_raw) if self.cost_raw else ""

    @property
    def button_image_url(self):
        return get_button_image(self.button_text)

    @property
    def is_all_weekend(self):
        if not self.end_date or not self.date:
            return False

        weekend_days = {"Friday", "Saturday", "Sunday"}
        event_days = set()

        current = self.date
        while current <= self.end_date:
            day_name = current.strftime("%A")
            if day_name in weekend_days:
                event_days.add(day_name)
            current += timedelta(days=1)

        return len(event_days) >= 2

    @property
    def parsed_start_time(self):
        """
        Parse the start time string into a datetime.time object for proper sorting.
        If parsing fails, return a default value (e.g. 00:00).
        """
        if not self.time_raw:
            return datetime.min.time()
        try:
            # Grab the first time if it's a range or multiple times
            time_str = self.time_raw.split("–")[0].split("-")[0].strip()
            return datetime.strptime(time_str, "%I:%M %p").time()
        except Exception:
            return datetime.min.time()

    @property
    def short_time(self):
        """Return only the start time (before a dash or comma)."""
        if not self.formatted_time:
            return ""
        return self.formatted_time.split("-")[0].split(",")[0].strip()