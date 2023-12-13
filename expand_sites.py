# expand_sites.py
# [Developer] Xinpeng Liu (xinpengl)
# [How to run] Drag this script to any IDE like Spyder, and run the current script.
# 
# [Description] When running this py file, he program will read a piracy websites.xlsx sheet
# from the same folder (An example file is attached). Next, the program will open a browser
# to visit SimilarWeb and login. Then, for each website url, the program will search for it
# on SimilarWeb and find similar sites for it. The newly discovered similar sites which belongs
# to the streaming industry will be kept. Eventually, all newly found websites will be converted
# to a dataframe and output as a xlsx file named "final_agg_sites.xlsx". After that, the program
# will open another Selenium browser to check if all recorded websites are accessible. Lastly,
# it will output a "final_checked_agg_sites.xlsx" with label indicates accessible or not.
#

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import pandas as pd

gecko_driver_path = "/usr/local/bin/geckodriver"
similar_web_username = "markcao@nexa4ai.com"
similar_web_password = "cxt1996915"

# Constants
data_path = "piracy websites.xlsx"
sites_tab_name = "Piracy Sites"
filters_tab_name = "Filter Sites"
final_output_path = "final_agg_sites.xlsx"
final_checked_output_path = "final_checked_agg_sites.xlsx"

input_website_col_name = "website"
input_filter_col_name = "not website"

wait_time = 10
sleep_time = 5
quality_check_wait_time = 10

# Prepare the parameter for initializing the selenium web driver
s = Service(gecko_driver_path)


# Function creates a browser for crawling. The use can specify is showing browser or not
def create_browser(show_browser=True):
    options = Options()
    # For starting the browser in the background
    options.headless = not show_browser
    browser = webdriver.Firefox(service=s, options=options)
    return browser


# Function reads the piracy sites and filter sites
def read_sites_and_filters_data(data_path):
    # Get sites and filters
    sites_df = pd.read_excel(data_path, sheet_name=sites_tab_name)
    filters_df = pd.read_excel(data_path, sheet_name=filters_tab_name)
    return sites_df, filters_df


def data_df_to_list(sites_df, filters_df):
    # Get sites and filters as list
    sites = sites_df[input_website_col_name].tolist()
    filters = filters_df[input_filter_col_name].tolist()
    print(sites)
    print(filters)
    return sites, filters


# Function expands the sites find their similar sites on SimilarWeb's similar sites page
# Store the result to new_webs
def find_similar_webs(input_sites, filter_sites, new_webs):
    # Some constants
    login_url = "https://secure.similarweb.com/account/login"
    similar_sites_page_base_url = 'https://pro.similarweb.com/#/digitalsuite/websiteanalysis/overview/competitive-landscape/*/999/3m?key='

    # Start a browser
    browser = create_browser(show_browser=True)
    browser.get(login_url)

    # Find email and password box
    input_email = WebDriverWait(browser, wait_time).until(
        EC.presence_of_element_located((By.ID, 'input-email')))
    input_password = WebDriverWait(browser, wait_time).until(
        EC.presence_of_element_located((By.ID, 'input-password')))

    # Send username and password to the login page
    input_email.send_keys(similar_web_username)
    input_password.send_keys(similar_web_password)

    # Submit the form
    login_button = WebDriverWait(browser, wait_time).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'button.sc-bcXHqe.iMwoDS.accessible')))
    login_button.click()

    # Go over all the sites to collect their similar sites
    total_sites_num = len(input_sites)
    print("Total {} sites to expand".format(total_sites_num))
    for idx in range(total_sites_num):
        try:
            # Create the specific url
            url = similar_sites_page_base_url + input_sites[idx]

            # Go to the specific similar site page
            browser.get(url)

            # Wait for the elements in a section are really fully loaded
            time.sleep(sleep_time)

            # Wait for up to 10 seconds for the element to be located
            web_elements = WebDriverWait(browser, wait_time).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.cell-clickable')))
            industry_elements = WebDriverWait(browser, wait_time).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'a.category-filter-cell')))

            # Collect the web_elements which is the object which holds information about similar sites
            for i in range(len(web_elements)):
                print(str(idx) + ", " + str(i))
                web_url = web_elements[i].text
                industry_element = industry_elements[i].text

                # The sites must be streaming sites, not in the original sites list, not already collected, and not in the filter list
                if (industry_element == "Arts and Entertainment > TV Movies and Streaming"
                        and web_url not in new_webs
                        and web_url not in input_sites
                        and web_url not in filter_sites):
                    new_webs.append(web_url)
            print(new_webs)
        except:
            continue

    # # Eventually, quit the browser
    # browser.quit()


# The top level driver function for expanding the sites
def expansion_driver_func():
    # Read from xlsx to dataframe
    sites_df, filter_df = read_sites_and_filters_data(data_path)

    # Convert dataframe to list
    input_sites, filter_sites = data_df_to_list(sites_df, filter_df)

    # Get the length of input sites
    input_sites_len = len(input_sites)

    # For recording the collected new webpages
    new_webs = []

    # Call the function to collect new_web for all sites available
    find_similar_webs(input_sites, filter_sites, new_webs)
    print("Found {} new sites".format(len(new_webs)))

    # Final aggregated all sites
    final_agg_sites = input_sites + new_webs
    print(final_agg_sites)

    # Prepare dataframe for final aggregated sites to xlsx
    final_agg_sites_df = pd.DataFrame(final_agg_sites, columns=[input_website_col_name])
    # Add a column to dataframe to identify old sites and new sites
    final_agg_sites_df["status"] = ["existing"] * input_sites_len + [""] * len(new_webs)
    final_agg_sites_df.to_excel(final_output_path, index=False)


# Function reads the websites from final_agg_sites.xlsx
def read_final_agg_sites():
    final_agg_sites_df = pd.read_excel(final_output_path)
    return final_agg_sites_df


# Function checks if the website is accessible using selenium web-driver
def web_quality_checker(final_agg_sites_df):
    # URL base
    url_base = "https://"

    # Add a column to dataframe to identify accessible sites and not accessible sites
    final_agg_sites_df["accessible"] = [""] * len(final_agg_sites_df)

    # Start a browser
    browser = create_browser(show_browser=True)

    # # Set the page load timeout to 10 seconds
    # browser.set_page_load_timeout(quality_check_wait_time)

    # Loop through the data frame row-by-row to check the quality of the websites
    print("Total {} sites to check".format(len(final_agg_sites_df)))

    # Iterate by index
    for index in range(len(final_agg_sites_df)):
    # for index in range(10):
        # Get the row
        row = final_agg_sites_df.iloc[index]

        print("{}. Checking website {}...".format(index, row[input_website_col_name]))

        # Get the website
        website = url_base + row[input_website_col_name]

        # Wait for up to 10 seconds for the element to be located
        try:
            # Assumption: A good website should be able to load "body" within X seconds

            # Get a website
            browser.get(website)

            # Wait for up to X seconds for the element to be located
            WebDriverWait(browser, quality_check_wait_time).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'body')))

            final_agg_sites_df["accessible"][index] = "y"
            print("Website {} accessible: Y".format(website))
        except:
            final_agg_sites_df["accessible"][index] = "n"
            print("Website {} accessible: N".format(website))

    # Eventually, quit the browser
    # browser.quit()


# Function checks the quality of the websites, like if they can be opened
def quality_checking_driver_func():
    # Get the dataframe of final aggregated sites
    final_agg_sites_df = read_final_agg_sites()

    # Check the quality of the websites
    web_quality_checker(final_agg_sites_df)
    print(final_agg_sites_df)

    # Save the dataframe to xlsx
    final_agg_sites_df.to_excel(final_checked_output_path, index=False)


if __name__ == "__main__":
    # Try to expand the websites
    expansion_driver_func()

    # Try to filter out low quality sites that we collected, or can't be opened websites
    quality_checking_driver_func()
