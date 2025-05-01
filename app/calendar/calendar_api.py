import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = os.getenv("TOKEN_PATH", "token.json")

def authenticate_google_calendar():
    """
    Authenticates with Google Calendar API and returns a service object.
    Handles token caching and refresh.
    """
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w") as token_file:
            token_file.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

def fetch_event_colors(service):
    """Fetch the event color hex codes."""
    colors = service.colors().get().execute()
    return colors['event']

def fetch_events(service, calendar_id, time_min, time_max, event_colors=None):
    """
    Fetch events from a calendar between time_min and time_max.
    Adds color_label to each event if event_colors is provided.
    Returns full event dictionaries with standardized 'start' and optional 'color_label'.
    """
    events_result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime',
        maxResults=250
    ).execute()

    events = events_result.get('items', [])
    event_data = []

    for event in events:
        # Normalize start date to YYYY-MM-DD format
        start_str = event['start'].get('dateTime', event['start'].get('date'))
        event['start'] = start_str[:10]

        # Add color hex if available
        color_id = event.get('colorId')
        color_hex = event_colors.get(color_id, {}).get('background') if event_colors and color_id else None
        event['color_label'] = color_hex

        event_data.append(event)

    return event_data
