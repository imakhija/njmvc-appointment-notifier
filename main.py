from datetime import datetime, date
import requests
from bs4 import BeautifulSoup
import re

MVC_LOCATION_CODES = {
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
    "RIO GRANDE": 126
}

SERVICES = {
    "REAL ID": 12,
    "RENEWAL": 11
}

# enter your preferred mvc locations or filter based on zip code / current location within X mile range
# enter your preferred days of the week and available times on each day

if __name__ == "__main__":
    location = MVC_LOCATION_CODES["LODI"]
    service = SERVICES["REAL ID"]
    # service = 11
    # location = 113
    
    # real_id = requests.get('https://telegov.njportal.com/njmvc/AppointmentWizard/12/{location}')
    url = requests.get('https://telegov.njportal.com/njmvc/AppointmentWizard/{service}/{location}')
    
    today = date.today()
    print(f"Today's date: {today}")

    current_month = int(datetime.now().strftime('%m')) # check month we're currently in
    current_year = int(datetime.now().strftime('%Y'))
    print(f"Current month: {current_month}")
    print(f"Current year: {current_year}")
    
    end_month = min(int(current_month) + 3, 12) # by default, look 3 months ahead
    end_year = current_year
    match = re.search(r'var\s+maxDate\s*=\s*new\s+Date\("(\d{4})-(\d{2})-\d{2}"\)', url.text)
    if match:
        end_month = int(match.group(2)) # check last month with appointments still available
        end_year = int(match.group(1))
        print(f"Last month with available appointments: {end_month}")
        print(f"Last year with available appointments: {end_year}")

    dates = set()
    # iterate from current month-year to month-year with last available appointment date
    month, year = current_month, current_year
    while (year < end_year) or (year == end_year and month <= end_month):
        url = f'https://telegov.njportal.com/njmvc/AppointmentWizard/{service}/{location}?date={year}-{month:02}-01'
        
        response = requests.get(url)
        pattern = r'addAvailableDates\([^,]+,\s*\[(.*?)\]\)'
        match = re.search(pattern, response.text)

        if match:
            raw_dates = match.group(1)
            found_dates = re.findall(r'\d{4}-\d{2}-\d{2}', raw_dates)
            dates.update(found_dates)
        else:
            print(f"No dates found in {year}-{month:02}")

        month += 1
        if month > 12:
            month = 1
            year += 1

    dates = list(dates)
    dates.sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))
    print(dates)
    print(f"Found {len(dates)} days with available appointments")