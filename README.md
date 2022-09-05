# Script to scrape the availabilities of US visa interviews in Canada

The idea is to create multiple accounts and scrape the most recent availabities in the payment page. Then it implements a notification function to your phone using the MyNotifier app. Once you're notified, you can login manually and book it.

I also implemented a function to automatically book the slot, but it's not well tested and sometimes it fails. You can see my commented codes for details.

Hope it helps your appointments!

If you succeed, you should find the following screenshots:
<img src="https://github.com/zzzace2000/us_scraper/blob/master/screenshot.png" width=600px>

## How to use

First, install the packages using pip
```bash
pip install -r requirements.txt
```

Then please follow the instructions in the us_embassy_scrape.py.
