# IMP Concerts Calendar

An auto-updating calendar of concerts from [IMP Concerts](https://www.impconcerts.com/) (9:30 Club, The Anthem, Lincoln Theatre, Merriweather Post Pavilion).

## Subscribe to the Calendar

Add this calendar to your favorite calendar app using the subscription URL:

```
https://<your-username>.github.io/imp-calendar/imp_concerts.ics
```

### Instructions by App

#### Apple Calendar (macOS/iOS)
1. Go to **File** → **New Calendar Subscription** (macOS) or **Settings** → **Calendar** → **Accounts** → **Add Account** → **Other** → **Add Subscribed Calendar** (iOS)
2. Enter the calendar URL above
3. Set refresh frequency to "Every week" or "Every day"

#### Google Calendar
1. Go to [Google Calendar Settings](https://calendar.google.com/calendar/r/settings)
2. Click **Add calendar** → **From URL**
3. Paste the calendar URL
4. Click **Add calendar**

#### Outlook
1. Go to **Calendar** → **Add calendar** → **Subscribe from web**
2. Enter the calendar URL
3. Name it "IMP Concerts" and click **Import**

## How It Works

- A GitHub Actions workflow runs on the 1st and 15th of each month
- The scraper fetches the latest concert listings from impconcerts.com
- The calendar file is automatically updated and published via GitHub Pages

## Venues Included

- 9:30 Club (815 V St NW, Washington, DC)
- The Anthem (901 Wharf St SW, Washington, DC)
- Lincoln Theatre (1215 U St NW, Washington, DC)
- Merriweather Post Pavilion (10475 Little Patuxent Pkwy, Columbia, MD)

## Manual Update

You can manually trigger an update:
1. Go to the **Actions** tab in this repository
2. Select **Update Concert Calendar**
3. Click **Run workflow**

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the scraper
python scraper.py
```

## License

This project is for personal use. Concert data belongs to IMP Concerts.
