#!/usr/bin/env python3
"""
IMP Concerts Calendar Scraper

Scrapes concert listings from impconcerts.com and generates an .ics calendar file.
"""

import re
import hashlib
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event

# IMP Venues with their addresses (badge class name -> display name -> address)
VENUE_MAP = {
    "venue-930-club": ("9:30 Club", "815 V St NW, Washington, DC 20001"),
    "venue-lincoln-theatre": ("Lincoln Theatre", "1215 U St NW, Washington, DC 20009"),
    "venue-the-anthem": ("The Anthem", "901 Wharf St SW, Washington, DC 20024"),
    "venue-merriweather-post-pavilion": ("Merriweather Post Pavilion", "10475 Little Patuxent Pkwy, Columbia, MD 21044"),
    "venue-theatlantis": ("The Atlantis", "1814 Half St SW, Washington, DC 20024"),
}

# Timezone for DC area
DC_TZ = ZoneInfo("America/New_York")


def fetch_concerts():
    """Fetch and parse concert listings from IMP Concerts website."""
    url = "https://www.impconcerts.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    concerts = []

    # Find all event group wrappers - each contains a date and event(s)
    event_groups = soup.select(".events-group__wrapper")

    for group in event_groups:
        # Extract date from the date-banner__date element
        date_elem = group.select_one(".date-banner__date")
        if not date_elem:
            continue
        date_str = date_elem.get_text(strip=True)

        # Find all event__content elements within this group
        event_contents = group.select(".event__content")

        for event_content in event_contents:
            concert = parse_event(event_content, date_str)
            if concert:
                concerts.append(concert)

    return concerts


def parse_event(event_element, date_str):
    """Parse a single event element into a concert dictionary."""
    try:
        # Get headliner from h3 inside anchor
        headliner_elem = event_element.select_one("h3")
        if not headliner_elem:
            return None
        headliner = headliner_elem.get_text(strip=True)

        # Get event URL from the anchor containing h3
        url = None
        link = event_element.select_one("a[href]")
        if link and link.has_attr("href"):
            url = link["href"]

        # Get openers from h4
        openers = []
        opener_elem = event_element.select_one("h4")
        if opener_elem:
            opener_text = opener_elem.get_text(strip=True)
            # Split by bullet, comma, or ampersand
            openers = [o.strip() for o in re.split(r"[•,&]", opener_text) if o.strip()]

        # Get door time
        door_time = None
        doors_elem = event_element.select_one(".event__doors")
        if doors_elem:
            doors_text = doors_elem.get_text(strip=True)
            time_match = re.search(r"(\d{1,2}:\d{2})\s*(am|pm)", doors_text, re.IGNORECASE)
            if time_match:
                door_time = time_match.group(1) + " " + time_match.group(2)

        # Get venue from badge class
        venue_name = None
        venue_address = None
        venue_elem = event_element.select_one("[class*='badge venue-']")
        if venue_elem:
            classes = venue_elem.get("class", [])
            for cls in classes:
                if cls.startswith("venue-"):
                    if cls in VENUE_MAP:
                        venue_name, venue_address = VENUE_MAP[cls]
                    else:
                        # Use the text content as venue name
                        venue_name = venue_elem.get_text(strip=True).title()
                    break

        # Parse the date
        event_date = parse_date(date_str, door_time)
        if not event_date:
            return None

        return {
            "headliner": headliner,
            "date": event_date,
            "venue": venue_name,
            "venue_address": venue_address,
            "openers": openers,
            "url": url,
        }

    except Exception as e:
        print(f"Error parsing event: {e}")
        return None


def parse_date(date_str, door_time=None):
    """Parse various date formats into a datetime object."""
    date_str = date_str.strip()

    # Parse door time if provided (e.g., "6:30 pm")
    hour, minute = 20, 0  # Default 8pm
    if door_time:
        time_match = re.match(r"(\d{1,2}):(\d{2})\s*(am|pm)", door_time, re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            if time_match.group(3).lower() == "pm" and hour != 12:
                hour += 12
            elif time_match.group(3).lower() == "am" and hour == 12:
                hour = 0

    # Pattern: "Thu, Feb 5" or "Thu, Feb 05"
    match = re.search(r"(\w+),?\s+(\w+)\s+(\d{1,2})", date_str)
    if match:
        month_name = match.group(2)
        day = int(match.group(3))

        # Extract year if present, otherwise use current/next year logic
        year_match = re.search(r"(\d{4})", date_str)
        if year_match:
            year = int(year_match.group(1))
        else:
            # Assume current year, but if date is in the past, use next year
            year = datetime.now().year
            try:
                month = datetime.strptime(month_name[:3], "%b").month
                test_date = datetime(year, month, day)
                if test_date < datetime.now():
                    year += 1
            except ValueError:
                pass

        try:
            month = datetime.strptime(month_name[:3], "%b").month
            return datetime(year, month, day, hour, minute, tzinfo=DC_TZ)
        except ValueError:
            pass

    return None


def generate_uid(concert):
    """Generate a unique ID for a concert event."""
    unique_str = f"{concert['headliner']}-{concert['date'].isoformat()}-{concert.get('venue', '')}"
    return hashlib.md5(unique_str.encode()).hexdigest() + "@impconcerts"


def create_calendar(concerts):
    """Create an iCalendar from concert listings."""
    cal = Calendar()
    cal.add("prodid", "-//IMP Concerts Calendar//impconcerts.com//")
    cal.add("version", "2.0")
    cal.add("calscale", "GREGORIAN")
    cal.add("method", "PUBLISH")
    cal.add("x-wr-calname", "IMP Concerts")
    cal.add("x-wr-timezone", "America/New_York")

    for concert in concerts:
        event = Event()

        # Title with openers if present
        title = concert["headliner"]
        if concert.get("openers"):
            title += f" (with {', '.join(concert['openers'])})"

        event.add("summary", title)
        event.add("dtstart", concert["date"])
        event.add("dtend", concert["date"] + timedelta(hours=3))  # Assume 3 hour show
        event.add("dtstamp", datetime.now(DC_TZ))

        # Add venue and location
        venue = concert.get("venue", "")
        venue_address = concert.get("venue_address", "")
        if venue_address:
            event.add("location", venue_address)
        elif venue:
            event.add("location", venue)

        # Description with details
        description_parts = []
        if concert.get("openers"):
            description_parts.append(f"With: {', '.join(concert['openers'])}")
        if venue:
            description_parts.append(f"Venue: {venue}")
        if concert.get("url"):
            description_parts.append(f"Tickets: {concert['url']}")

        if description_parts:
            event.add("description", "\n".join(description_parts))

        if concert.get("url"):
            event.add("url", concert["url"])

        event.add("uid", generate_uid(concert))

        cal.add_component(event)

    return cal


def main():
    """Main function to scrape concerts and generate calendar."""
    print("Fetching concerts from IMP Concerts...")

    try:
        concerts = fetch_concerts()
        print(f"Found {len(concerts)} concerts")

        if concerts:
            cal = create_calendar(concerts)

            output_path = "imp_concerts.ics"
            with open(output_path, "wb") as f:
                f.write(cal.to_ical())

            print(f"Calendar saved to {output_path}")
        else:
            print("No concerts found. Creating empty calendar...")
            cal = Calendar()
            cal.add("prodid", "-//IMP Concerts Calendar//impconcerts.com//")
            cal.add("version", "2.0")
            cal.add("calscale", "GREGORIAN")
            cal.add("method", "PUBLISH")
            cal.add("x-wr-calname", "IMP Concerts")

            with open("imp_concerts.ics", "wb") as f:
                f.write(cal.to_ical())

    except requests.RequestException as e:
        print(f"Error fetching concerts: {e}")
        raise


if __name__ == "__main__":
    main()
