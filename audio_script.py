#!/user/bin/python3
# -*- coding: utf-8 -*-

"""
    Selenium Facebook Scraper.
    author:
    author: Soumick Barua


"""

import sys
import time
import json
import csv
import re
import argparse
import getpass

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def opt_parser():
    """Parse command-line options."""
    parser = argparse.ArgumentParser(description="Use Selenium & Firefox to automate Facebook login and scrape user's friend list.",
                                     formatter_class=lambda prog: argparse.RawTextHelpFormatter(prog, width=99))
    parser.add_argument("-v", "--verbose", help="Increase verbosity level.", action="store_true", default=False, dest="verbose")
    parser.add_argument("-b", "--headless", help="Activate headless mode, run firefox in the background.", action="store_true", default=False, dest="headless")
    parser.add_argument("-t", "--timeout", help="Time to wait for elements to load on webpages before giving up. (30s)", type=int, default=30, dest="timeout")
    parser.add_argument("-j", "--json", help="Export user's friend list in JSON format. (default)", default=True, action="store_true", dest="json")
    parser.add_argument("-c", "--csv", help="Export user's friend list in CSV format.", default=False, action="store_true", dest="csv")
    parser.add_argument("-s", "--html", help="Export the source html page.", default=False, action="store_true", dest="html")
    parser.add_argument("-i", "--import-html", help="Import data from source html page.", default=None, dest="htmlpage")
    parser.add_argument("-l", "--login-data", help="Read login data from file.", default=None, dest="loginfile")
    return parser.parse_args()

def check_page_loaded(driver):
    """Check whether the page is loaded or not. """
    try:
        existing = False
        elements = driver.find_elements_by_class_name("uiHeaderTitle")

        for element in elements:
            if (element.get_attribute('innerHTML') == "More About You"):
                existing = True

        return existing

    except:
        return False

def sec_to_hms(sec):
    """ Convert seconds to hh:mm:ss format. """
    h = sec // 3600
    sec %= 3600

    m = sec // 60
    sec %= 60

    return '{:02}:{:02}:{:02}'.format(int(h), int(m), int(sec))

def export_data(data, filename):
    """Export data to a file."""
    with open(filename, "w", encoding="utf-8") as file:
        file.write(json.dumps(data, indent=4))

def get_login_data_from_file(filename):
    """Read login data from file."""
    with open(filename, "r", encoding="utf-8") as login_file:
        user = login_file.readline().strip()
        password = login_file.readline().strip()

    return user, password

def get_login_data_from_stdin():
    """ Get login data from stdin. """
    print("Facebook Login:- ")
    user = input("Enter e-mail address or phone number: ")
    password = getpass.getpass("Enter password: ")

    return user, password

def automate(driver, user, password, timeout=30, verbose=False):
    """ Automate user interaction using selenium and return html source page."""
    wait = WebDriverWait(driver, timeout)
    facebook_url = "https://www.facebook.com/login.php"
    
    if verbose:
        print("GET", facebook_url)
    
    driver.get(facebook_url)

    elem = wait.until(EC.presence_of_element_located((By.ID, "email")))
    
    if verbose:
        print("Entering email... ")
    
    elem.send_keys(user)

    elem =  wait.until(EC.presence_of_element_located((By.ID, "pass")))

    if verbose:
        print("Entering password... ")
        print("Sending data... ")

    elem.send_keys(password)
    elem.send_keys(Keys.RETURN)

    if verbose:
        print("Waiting for elements to load... timeout={0}".format(timeout))

    wait.until(EC.element_to_be_clickable((By.XPATH, "//*[name()='path' and contains(@class,'xe3v8dz')]")))
    if verbose:
        print("GET https://www.facebook.com/profile.php")

    driver.get("https://www.facebook.com/profile.php")

    while (driver.current_url == "https://www.facebook.com/profile.php"):
        time.sleep(0.02)

    url = (driver.current_url[0:-2] if "#_" == driver.current_url[-2:] else driver.current_url) + "&sk=friends"
    if verbose:
        print("GET", url)

    driver.get(url)
    if verbose:
        print("Scrolling down... ")

    start_time = time.time()
    scroll_time = 120  # Stop scrolling after 60 seconds
    
    all_data = []  # To store all text and links encountered during scrolling
    
    while time.time() - start_time < scroll_time:
        # Execute JavaScript code to get all text and links on the current page
        page_data = driver.execute_script("""
            var elements = document.evaluate("//*[not(self::script)]", document, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
            var data = [];
            for (var i = 0; i < elements.snapshotLength; i++) {
                var element = elements.snapshotItem(i);
                var text = element.textContent.trim();
                var link = element.getAttribute('href') || '';
                data.push({text: text, link: link});
            }
            return data;
        """)
        all_data.extend(page_data)
        
        # Scroll down
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Wait for some time to load more content
        time.sleep(1)
        
        if check_page_loaded(driver):
            break

    # Now that scrolling has stopped, let's save the data
    driver.quit()  # Close the driver after getting the data
    return all_data


def get_source_htmlpage(options):
    """Start the program and handle command line options"""

    if options.loginfile:
        try:
            user, password = get_login_data_from_file(options.loginfile)
        except Exception as Error:
            print(Error)

            if 'y' in input("Do you want to get login data from stdout?(y/n) ").lower():
                user, password = get_login_data_from_stdin()

            else:
                sys.exit(0)
    else:
        user, password = get_login_data_from_stdin()

    if options.verbose:
        start_time = time.time()
        print("Running Chrome... ")

    chrome_options = webdriver.ChromeOptions()
    if options.headless:
        chrome_options.add_argument("--headless")

    prefs = {"profile.default_content_setting_values.notifications": 2}
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(options=chrome_options)

    data = automate(driver, user, password, verbose=options.verbose, timeout=options.timeout)

    driver.quit()

    if options.verbose:
        print("Done downloading!.. ({0})\n".format(sec_to_hms(time.time() - start_time)))

    return data

def import_from_htmlfile(path_to_htmlfile):
    """Import friend list from htmlfile downloaded from a web browser. """
    with open(path_to_htmlfile, "r", encoding="utf-8") as htmlfile:
        htmlpage = htmlfile.read()

    return htmlpage

def process_and_save_data(data):
    # Load the JSON data
    with open('facebook_friends_data.json', 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)

    # Words to remove from links
    remove_list = ["mutual", "marketplace", "app_tab", "about", "friends", "photos", "videos", "map", 
                "friends_all", "friends_recent", "friends_with_upcoming_birthdays", "following", "create", 
                "photo", "groups", "bookmarks", "notifications"]

    # Define the regular expression pattern
    pattern = r'^\s*{\s*"link":\s*"(https://www\.facebook\.com/[^"]*)",\s*"text":\s*".+"\s*}\s*$'

    # Filter out entries with links containing specified words
    filtered_data = [entry for entry in data if not any(word in entry["link"] for word in remove_list)]

    # Extract the data matching the pattern and remove entries with an empty "text" field
    filtered_data = [entry for entry in filtered_data if re.match(pattern, json.dumps(entry, indent=None, separators=(',', ':')), flags=re.MULTILINE) and entry["text"] != ""]

    # Convert the list to a set to remove duplicates and then back to a list
    unique_filtered_data = list(set(json.dumps(entry, indent=None, separators=(',', ':')) for entry in filtered_data))

    # Write the unique filtered data to a new file
    with open('unique_filtered_data.json', 'w', encoding='utf-8') as new_file:
        new_file.write("[\n")
        new_file.write(",\n".join(unique_filtered_data))
        new_file.write("\n]")

def main():
    # verbose, headless, json, csv, html, htmlpage, loginfile, timeout
    options = opt_parser()

    if options.htmlpage:
        try:
            data = import_from_htmlfile(options.htmlpage)

        except Exception as error:
            print(error)

            if 'y' in input("Do you want to scrape data online?(y/n) ").lower():
                data = get_source_htmlpage(options)

            else:
                return 0

    else:
        data = get_source_htmlpage(options)

    if options.verbose:
        print("Processing data... ")

    filename = 'facebook_friends_data.json'
    export_data(data, filename)

    if options.verbose:
        print("Data saved to:", filename)

    # Process and save the data
    process_and_save_data(data)

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("Keyboard Interruption! exiting... ")

    sys.exit(0)

