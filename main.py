from datetime import datetime, date
import requests
from bs4 import BeautifulSoup
import re

MVC_LOCATION_CODES_BY_SERVICE = {
  "RENEWAL": {
    "BAKERS BASKIN": 101,
    "BAYONNE": 102,
    "CAMDEN": 104,
    "CARDIFF": 105,
    "DELANCO": 107,
    "EATONTOWN": 108,
    "EDISON": 110,
    "ELIZABETH": 261,
    "FLEMINGTON": 111,
    "FREEHOLD": 113,
    "LODI": 114,
    "MANAHAWKIN": 787,
    "NEWARK": 116,
    "NEWTON": 485,
    "NORTH BERGEN": 117,
    "OAKLAND": 119,
    "PATERSON": 120,
    "RAHWAY": 122,
    "RANDOLPH": 123,
    "RIO GRANDE": 103,
    "RUNNEMEDE": 500,
    "SALEM": 106,
    "WAYNE": 118,
    "SOUTH PLAINFIELD": 109,
    "TOMS RIVER": 112,
    "VINELAND": 115,
    "WASHINGTON": 486,
    "WEST DEPTFORD": 121
  },
  "REAL ID": {
    "OAKLAND": 141,
    "PATERSON": 142,
    "LODI": 136,
    "WAYNE": 140,
    "RANDOLPH": 145,
    "NORTH BERGEN": 139,
    "NEWARK": 138,
    "BAYONNE": 125,
    "RAHWAY": 144,
    "SOUTH PLAINFIELD": 131,
    "EDISON": 132,
    "FLEMINGTON": 133,
    "BAKERS BASIN": 124,
    "FREEHOLD": 135,
    "EATONTOWN": 130,
    "TOMS RIVER": 134,
    "DELANCO": 129,
    "CAMDEN": 127,
    "WEST DEPTFORD": 143,
    "SALEM": 128,
    "VINELAND": 137,
    "CARDIFF": 146,
    "RIO GRANDE": 126,
    "ELIZABETH": 265,
    "MANAHAWKIN": 511,
    "NEWTON": 448,
    "RUNNEMEDE": 502,
    "WASHINGTON": 451
  }
}

SERVICES = {
    "REAL ID": 12,
    "RENEWAL": 11
}

# enter your preferred mvc locations or filter based on zip code / current location within X mile range
# enter your preferred days of the week and available times on each day

# TODO:
    # check every 60 seconds and print results
    # write python script to send email when appointments available

def send_email():
    print("Implement emailing")

def get_times_and_links(date, service, location):
    result = requests.get(f'https://telegov.njportal.com/njmvc/AppointmentWizard/{service}/{location}?date={date}')
    soup = BeautifulSoup(result.text, 'html.parser')

    times = soup.select('div.AppointFlex.col a')
    appointments = []
    for t in times:
        link = t['href']
        time = t.get_text(strip=True)
        appointments.append((time, link))

    return appointments

def get_appointments(s, l, current_month, current_year):
    print(f"Finding appointments in {l} for {s}")
    num_appointments = 0
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
        print(f"Last date with available appointments: {end_year}-{end_month:02}-{end_date:02}")

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
        else:
            print(f"No dates with appointments found in {year}-{month:02}")

        month += 1
        if month > 12:
            month = 1
            year += 1

    dates = list(dates) # convert set to list of dates for indexing and ordering
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d")) # sort chronologically
    
    print(dates)
    print(f"Found {len(dates)} days with available appointments in {l} for {s}")

    for d in dates:
        appointments = get_times_and_links(d, service, location)
        num_appointments += len(appointments)

        for time, link in appointments:
            print(f"{d} at {time}: https://telegov.njportal.com{link}")

    print(f"Found {num_appointments} appointments in {l} for {s}")
    if num_appointments > 0:
        send_email()

if __name__ == "__main__":
    # modify these to your personal preferences
    # locations = ["LODI", "EDISON"]
    # services = ["REAL ID", "RENEWAL"]
    
    # renewal appointments in Freehold (for testing purposes)
    # services = ["RENEWAL"]
    # locations = ["FREEHOLD"]

    # appointment that I need :)
    services = ["REAL ID"]
    locations = ["LODI"]

    today = date.today()
    print(f"Today's date: {today}")

    # get current month and year to start checking appointments from
    current_month = int(datetime.now().strftime('%m'))
    current_year = int(datetime.now().strftime('%Y'))
    
    for s in services:
        for l in locations:
            get_appointments(s, l, current_month, current_year)