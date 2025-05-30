from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from const import MVC_LOCATION_CODES_BY_SERVICE, SERVICES
from mail import sendAppointments
import os

def get_times_and_links(date, service, location, s, l):
    result = requests.get(f'https://telegov.njportal.com/njmvc/AppointmentWizard/{service}/{location}?date={date}')
    soup = BeautifulSoup(result.text, 'html.parser')

    times = soup.select('div.AppointFlex.col a')
    appointments = []
    for t in times:
        link = t['href']
        time = t.get_text(strip=True)
        appointments.append((s, l, date, time, link))

    return appointments

def get_appointments(s, l, current_month, current_year):
    print(f"Finding appointments in {l} for {s}")

    location = MVC_LOCATION_CODES_BY_SERVICE[s][l]
    service = SERVICES[s]
    
    url = requests.get(f'https://telegov.njportal.com/njmvc/AppointmentWizard/{service}/{location}')
    
    end_month = min(int(current_month) + 3, 12) # by default, look at most 3 months ahead
    end_year = current_year
    match = re.search(r'var\s+maxDate\s*=\s*new\s+Date\("(\d{4})-(\d{2})-(\d{2})"\)', url.text)
    if match:
        end_month = int(match.group(2)) # check last month with appointments still available
        end_year = int(match.group(1))
        end_date = int(match.group(3))

    dates = set()
    # iterate from current month-year to month-year with last available appointment date
    month, year = current_month, current_year
    while (year < end_year) or (year == end_year and month <= end_month):
        url = f'https://telegov.njportal.com/njmvc/AppointmentWizard/{service}/{location}?date={year}-{month:02}-01'
        
        response = requests.get(url)
        pattern = r'addAvailableDates\([^,]+,\s*\[(.*?)\]\)'
        match = re.search(pattern, response.text)

        if match:
            dates_list = match.group(1)
            dates.update(re.findall(r'\d{4}-\d{2}-\d{2}', dates_list))

        # loop around to January of next year after reaching December
        month += 1
        if month > 12:
            month = 1
            year += 1

    dates = list(dates) # convert set to list of dates for indexing and ordering
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d")) # sort chronologically

    # for each date with appointments, get their timings and URLs
    appointments = []
    for d in dates:
        appointments.extend(get_times_and_links(d, service, location, s, l))

    print(f"Found {len(appointments)} appointments in {l} for {s}")

    return appointments

def filter_appointments(appointments, dates, weekly):
    def parse_dates(range):
        start, end = range.split("-")
        return (datetime.strptime(start, "%m/%d/%Y").date(), datetime.strptime(end, "%m/%d/%Y").date())

    def parse_times(range):
        start, end = range.split("-")
        return (datetime.strptime(start, "%I:%M%p").time(), datetime.strptime(end, "%I:%M%p").time())

    date_ranges = [parse_dates(r) for r in dates]
    filtered_appts = []

    for a in appointments:
        appt_date = datetime.strptime(a[2], "%Y-%m-%d").date()
        appt_time = datetime.strptime(a[3].split()[0] + a[3].split()[1], "%I:%M%p").time()
        appt_day = appt_date.strftime("%A")

        valid_date = any(start <= appt_date <= end for start, end in date_ranges)

        range = weekly.get(appt_day)
        valid_time = False
        if range:
            start, end = parse_times(range)
            valid_time = (start <= appt_time <= end)

        if valid_date and valid_time:
            filtered_appts.append(a)
    
    return filtered_appts

if __name__ == "__main__":
    now = datetime.now() # used to record program execution time for log

    # appointment that I need (modify these to your personal preferences)
    services = ["REAL ID", "REAL ID TUESDAY"]
    locations = ["LODI"]
    
    # availability filters
    dates = ["05/29/2025-08/12/2025"] # enter each range as MM/DD/YYYY-MM/DD/YYYY
    weekly = {"Monday": "08:00AM-04:30PM", # enter each range as HH:MM(AM/PM)-HH:MM(AM/PM)
              "Tuesday": "",               # leaving empty string indicates no availability on that day
              "Wednesday": "",
              "Thursday": "",
              "Friday": "08:00AM-04:30PM",
              "Saturday": "08:00AM-03:00PM"
    }

    # get current month and year to start checking appointments from
    current_month = int(datetime.now().strftime('%m'))
    current_year = int(datetime.now().strftime('%Y'))
    
    # loop through each location for each service and pull all available appointments
    appointments = []
    for s in services:
        for l in locations:
            appointments.extend(get_appointments(s, l, current_month, current_year))

    if len(appointments) > 0:
        # filter appointments based on availability preferences
        appointments = filter_appointments(appointments, dates, weekly)
        print(f"Found {len(appointments)} total appointments for all preferred locations and services after filtering by available dates and times")

        if len(appointments) > 0:
            formatted_appointments = "\n".join(
                f"{service} at {location} on {date} at {time}: https://telegov.njportal.com{link}"
                for (service, location, date, time, link) in appointments
            )

            # read the previous appointments file if it exists
            if os.path.exists("prev.txt"):
                with open("prev.txt", "r") as f:
                    prev_appts = f.read()

            # send the new appointments only if this is the first run or the available appointments have changed
            if (not os.path.exists("prev.txt") or prev_appts != formatted_appointments):
                sendAppointments(formatted_appointments)

            with open("prev.txt", "w") as f: # store new appointments for comparison on next execution
                f.write(formatted_appointments)
    else:
        print("Found 0 total appointments for all preferred locations and services")
    
    print(f"Executed at {now.strftime('%Y-%m-%d %H:%M:%S')}\n")