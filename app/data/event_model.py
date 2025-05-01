class Event:
    def __init__(self, start, section, title="", time="", cost="",
                 location_name="", location_url="", description="",
                 button_text="", button_url=""):
        self.start = start
        self.section = section  # <- This links it to Featured, Kids, etc.
        self.title = title
        self.time = time
        self.cost = cost
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
