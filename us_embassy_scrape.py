"""A script to scrape the availabilities for US embasies in Canada.

First, create lots of accounts in the system using different emails. 
Use this website to enroll:
https://ais.usvisa-info.com/en-ca/niv

After enrolling an account, create an application group with applicants added
to apply your intended visa (e.g. B1, J1, O1...). You might need to fill in 
DS160 unique identifier, where you can create from here:
https://ceac.state.gov/genniv/

Then record the account, password, and the group id. You can find the group id
in your url of application page. For example, if I have a url like:
https://ais.usvisa-info.com/en-ca/niv/schedule/41520489/continue_actions
The group id is 41520489.

Ideally, you should create 8 accounts to avoid the blocking mechasnisms from
the website. Each account will usually be blocked of probing availabilities 
after 4 hours.

Then fill out the variables below.
"""


# The accounts. Write in the (email, password, group_id) in this array.
# Ideally 8 accounts will make sure the script would not be blocked.
ACCOUNTS = [
    ('kingsley@cs.toronto.edu', '', '41742555'),
]

# Cooldown mins when every account is blocked
NUM_MINS_COOLDOWN = 30

# How frequent to probe the server
NUM_MINS_PROBE = 2 # Every 2 minutes

################## Criteria ###################
# Specify the last date you want to apply for a visa. It will notify you if 
# any availibities is available before this date
ALLOWED_DATE = '2022-12-31'

# Specify the place you want to apply for a visa 
ALLOWED_PLACES = [
    'Toronto',
    'Ottawa',
    # 'Montreal',
    # 'Quebec City',
    # 'Halifax',
    # 'Calgary',
    # 'Vancouver',
]


################## Notification #####################
# I use the mynotifier to get an notification for my phone.
# You can get a free 30 notifications per month.
# Please sign up here:
# https://www.mynotifier.app/
# Then record the notifier id here. Also download the app on your phone.
API_KEY = "55390253-f731-457f-8957-c95f041b4???"



import time
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

from myutils import MONTH, minus_two_dates
from schedule import reschedule


# def to_score(date, loc):
#     return minus_two_dates("2022-08-31", date) + LOC_SCORES[loc]


# def is_date_and_loc_better(date1, loc1, date2, loc2):
#     return to_score(date1, loc1) > to_score(date2, loc2)


def get_session(email, password):
    """Login and get the session."""
    session = requests.Session() # Create new session
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
    }
    resp = session.get(
        "https://ais.usvisa-info.com/en-ca/niv/users/sign_in",
        headers=headers,
    )  # set seoprofilersession and csrftoken cookies

    soup = BeautifulSoup(resp.text, 'html.parser')
    authenticity_token = soup.find_all('input')[1].get('value') # It's brittle to use the location

    r = session.post(
        "https://ais.usvisa-info.com/en-ca/niv/users/sign_in",
        data={
            "authenticity_token": authenticity_token,
            "user[email]": email,
            "user[password]": password,
            "policy_confirmed": 1,
            "commit": "Sign In",
        },
        headers=headers,
    )  # login, sets needed cookies

    if r.status_code != 200:
        print('Login failed!')
    return session


cache_session = {}

def search_update(email, password,
                  group_id=41712813,
                  country_code='en-ca',
                  ):
    global cache_session
    if email not in cache_session:
        session = get_session(email=email, password=password)
        cache_session[email] = session
    else:
        session = cache_session[email]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36',
        "Referer": "https://ais.usvisa-info.com/%s/niv/schedule/%s/continue_actions" % (country_code, group_id),
        "Cookie": "_yatri_session=" + session.cookies['_yatri_session']
    }
    r = session.get(
        "https://ais.usvisa-info.com/%s/niv/schedule/%s/payment" % (country_code, group_id),
        headers=headers,
    )
    if r.status_code != 200:
        print(f"Error code: {r.status_code}")
        del cache_session[email]
        return None, None

    soup = BeautifulSoup(r.text, "html.parser")
    time_table = soup.find("table", {"class": "for-layout"})

    result = []
    if time_table:
        for tr in time_table.find_all("tr"):
            tds = tr.find_all("td")
            if not len(tds) == 2:
                continue
            place = tds[0].text
            date_str = tds[1].text
            s = date_str.split()
            if len(s) >= 3 and s[0] != "No":
                day_str, month_str, year_str = s[-3], s[-2].replace(",", ""), s[-1]
                year, month, day = int(year_str), MONTH[month_str], int(day_str)
                result.append(dict(place=place, year=year, month=month, day=day))
    return result, session


prev_msg = None
def send_msg(eligibles):
    """Send a message to the phone by MyNotifier app."""

    global prev_msg
    msg = ''
    for r in eligibles:
        first_date = f"{r['year']}-{r['month']}-{r['day']}"
        loc = r['place']
        msg += f"Found {loc} {first_date}; "

    if prev_msg is not None and msg == prev_msg:
        print(f'[{current_time}] Same message: {msg}')
    else:
        print('Send a notification: ', msg)
        requests.post('https://api.mynotifier.app', {
            "apiKey": API_KEY,
            "message": msg,
            "description": msg,
            "type": "success",  # info, error, warning or success
        })
        prev_msg = msg


prev_r_str = None
def process_result(result):
    global prev_r_str, CUR_DATE, CUR_LOC
    current_time = datetime.now().strftime("%m-%d %H:%M:%S")

    r_str = str(result)
    if prev_r_str is not None and r_str == prev_r_str:
        print(f'[{current_time}]: Same as previous one.')
        return

    prev_r_str = r_str

    df = pd.DataFrame(result)
    print(f'{current_time}')
    print(f'{df}')

    eligibles = []
    for r in result:
        date_str = f"{r['year']}-{'%02d' % r['month']}-{'%02d' % r['day']}"
        r['date_str'] = date_str

        if (r['place'] in ALLOWED_PLACES and date_str <= ALLOWED_DATE):
            eligibles.append(r)

    if len(eligibles) == 0:
        return

    print(f'[{current_time}]: Find {len(eligibles)} eligibles!')

    ## Send message
    send_msg(eligibles)

    ## Try to directly reschedule one
    # eligibles_sorted = sorted(eligibles, key=lambda e: to_score(e['date_str'], e['place']),
    #                           reverse=True)
    # for eligible in eligibles_sorted:
    #     print(f"Try reschedule for the {eligible['place']} {eligible['date_str']}")
    #     try:
    #         success_date = reschedule(
    #             email='zzzace2000@gmail.com',
    #             password='',
    #             place=eligible['place'],
    #             required_date=eligible['date_str'],
    #         )
    #         if success_date:
    #             # CUR_DATE = success_date
    #             # CUR_LOC = eligible['place']
    #             print(f"*********** Rescheduled to {eligible['place']} {success_date}!!! ***********")
    #             break
    #         else:
    #             print(f"Rebooked failed {eligible['date_str']}!")
    #     except Exception as e:
    #         print('Somehow rebooked failed!')
    #         print(e)


if __name__ == '__main__':
    print(f'*********** Try to find availibilities before {ALLOWED_DATE} and'
        f' in these places: {ALLOWED_PLACES} ***********')

    session = None
    account_idx = 0
    first_blocked_account_idx = None

    account_start_time = datetime.now()
    while True:
        hour_of_shift = int(np.ceil(24 / len(ACCOUNTS)))
        if (account_start_time + timedelta(hours=hour_of_shift)) < datetime.now():
            the_email = ACCOUNTS[account_idx][0]
            if the_email in cache_session:
                del cache_session[the_email]

            account_idx = (account_idx + 1) % len(ACCOUNTS)
            account_start_time = datetime.now()
            print(f'Change to next {account_idx} since {hour_of_shift} hrs have passed.')

        # Select which account to use
        email, password, group_id = ACCOUNTS[account_idx]

        result = None
        while result is None: # May login failed
            result, session = search_update(email=email, password=password, group_id=group_id)

        if len(result) == 0: # Blocked by the server
            if first_blocked_account_idx is None:
                first_blocked_account_idx = account_idx

            # Change account
            account_idx = (account_idx + 1) % len(ACCOUNTS)
            account_start_time = datetime.now()
            if email in cache_session:
                del cache_session[email] # Delete the previous session
            print(f'{email} failed. Change to next {account_idx} {ACCOUNTS[account_idx][0]}.')

            # Block to every accounts. Rest for 30 minutes
            if account_idx == first_blocked_account_idx:
                for k in cache_session.keys():
                    del cache_session[k]
                current_time = datetime.now().strftime("%m-%d %H:%M:%S")
                print(f'[{current_time}]: every account is blocked. Rest for {NUM_MINS_COOLDOWN} minutes!')
                first_blocked_account_idx = None
                time.sleep(NUM_MINS_COOLDOWN * 60)
            continue

        first_blocked_account_idx = None
        process_result(result)

        noise = np.random.randn() * 0.1
        time.sleep((NUM_MINS_PROBE + noise) * 60) # 6 minutes + noise of 0.5 minute stdev
