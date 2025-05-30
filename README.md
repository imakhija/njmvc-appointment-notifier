# NJMVC REAL ID Appointment Notifier 🚗

Need an appointment to upgrade your license to a REAL ID but don't want to keep refreshing the NJMVC website all day?

## Features

- Scrapes NJMVC appointment availability for specific locations and service types
- Sends email notifications when new appointments are found
- Prevents duplicate emails if appointments haven't changed
- Filter appointments based on availability by specifying date ranges and timings for days of the week

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/imakhija/njmvc-appointment-notifier.git
```

### 2. Install Required Packages
```bash
pip install -r requirements.txt
```

### 3. SMTP Server Configuration
An SMTP server is required for the script to send out appointment email notifications.

One option is to use a Google account that is secured with 2FA. The links below will allow you to set up an app password
- https://support.google.com/accounts/answer/185833?hl=en
- https://myaccount.google.com/apppasswords

There are always other alternatives for local or external SMTP servers that you can feel free to use!

### 4. Environment Variables
Create a .env file in the root directory with the following contents, replacing the placeholders:
```bash
GMAIL_ADDRESS=[SMTP server email]
GMAIL_APP_PASSWORD=[SMTP server password]
DELIVERY_ADDRESS=[email address to notify when new appointments open]
```

### 5. Preferences
Update the script with your preferred MVC locations and services

Currently, the only offered services are "REAL ID", "REAL ID TUESDAY", and "RENEWAL"

```python
services = []
locations = []
```

## Email Format
Appointment notification emails will look like the following, but the formatting can always be modified:
```
REAL ID at LODI on 2025-08-26 at 1:15 PM EDT: https://telegov.njportal.com/njmvc/AppointmentWizard/12/136/2025-08-26/1315
REAL ID at LODI on 2025-08-26 at 1:35 PM EDT: https://telegov.njportal.com/njmvc/AppointmentWizard/12/136/2025-08-26/1335
REAL ID at LODI on 2025-08-26 at 1:55 PM EDT: https://telegov.njportal.com/njmvc/AppointmentWizard/12/136/2025-08-26/1355
REAL ID at LODI on 2025-08-26 at 2:15 PM EDT: https://telegov.njportal.com/njmvc/AppointmentWizard/12/136/2025-08-26/1415
REAL ID at LODI on 2025-08-26 at 2:35 PM EDT: https://telegov.njportal.com/njmvc/AppointmentWizard/12/136/2025-08-26/1435
```

## Running the Script
### 1. Run once
This will check for appointments exactly once at the time of execution
```bash
python main.py
```
### 2. Infinite execution
You can let main.py continuously execute in the background, but this may be computationally intensive compared to the alternatives below.

Add a while loop and a call to the sleep function in the imported time library with the number of seconds you'd like between executions (ex. time.sleep(60) indicates that new appointments will be checked once a minute).
```python
while True:
  # loop through each location for each service and pull all available appointments
  appointments = []
  for s in services:
      for l in locations:
          appointments.extend(get_appointments(s, l, current_month, current_year))
  
  if len(appointments) > 0:
      print(f"Found {len(appointments)} total appointments for all preferred locations and services")
  
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
  time.sleep(60)
```
### 3. Run as cron job
Use a cron job to have your compute automatically run the program in the background every minute or some other set time interval
1. CD into local repository
2. Make main.py executable
```bash
chmod +x main.py
```
3. Get the path to your Python installation
```bash
which python3
```
4. Open the crontab editor
```bash
crontab -e
```
5. Add this line to the editor to run main.py every minute, replacing placeholders with your local paths:
```
* * * * * [PATH TO PYTHON INSTALLATION] [PATH TO MAIN.PY] >> [PATH TO REPO]/cron.log 2>&1
```
6. Confirm the cron job
```bash
crontab -l
```
7. Check output log
```bash
cat [PATH TO REPO]/cron.log
```

### 4. Host on serverless architecture
Deploy this program on AWS Lambda, GCP Functions, or similar serverless FaaS architectures for true 24/7 availability.
