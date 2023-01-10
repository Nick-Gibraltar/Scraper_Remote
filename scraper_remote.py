from selenium import webdriver
#from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
#from webdriver_manager.chrome import ChromeDriverManager

import csv
import datetime
import json
import requests

class Scraper:
    """
    Downloads and stores product specifications from www.screwfix.com
    for user's chosen search term.

    Methods:
        open_url: opens the www.screwfix.com home page
        cookies_check: checks if cookies need to be accepted to proceed
        initial_search: searches for the user's specified search item
        get_sub_category_list: determine if search term yields further categories
        get_sub_category_choice: ask user to choose a sub-category if they have arisen
        get_product_links: get urls for individual products
        get_product_features_table: retrieve product specifications from product urls
        transform_product_table: generate csv summary of data using consistent field names
    """
    
    def __init__(self):
        #chrome_options = Options()
        #chrome_options.add_argument("--headless")
        print("3. Scraper __init__")
        self.url = "https://www.screwfix.com"
        #self.driver = webdriver.Chrome()
        #self.driver = webdriver.Chrome(ChromeDriverManager().install())
        #self.driver = webdriver.Chrome()
        #self.driver = webdriver.Chrome(options=chrome_options)
        
        self.driver = webdriver.Remote('http://127.0.0.1:4444/wd/hub', options=webdriver.ChromeOptions)
        
        self.sub_category_list = []
        self.product_links_list = []
        self.product_features_table = []
        self.product_features_dictionary = {}
        self.output_path = "/home/nick/Documents/AICore/Data-Collection/Scraper/raw_data/"
    
    def open_url(self):
        '''
        Open the specified url, www.screwfix.com
        '''
        self.driver.get(self.url)

        return self.driver.current_url
    
    def cookies_check(self):
        '''
        Check if the home page requires cookies to be accpepted by searching for
        the text Accept Cookies. Click the Accept Cookies button if so.

        Args:
            None

        Returns:
            Void
        '''
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//iframe')))
        iframes = self.driver.find_element(by=By.XPATH, value='//iframe')
        self.driver.switch_to.frame(iframes)
        
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, './/a[@class="call"]')))
        cookies_button=self.driver.find_element(by=By.XPATH, value='.//a[@class="call"]')
        cookies_button.send_keys("")
        cookies_button.send_keys(Keys.ENTER)

    def initial_search(self, search_item):
        '''
        Searches for the user's specified search term by finding the search box
        and entering the search term into it

        Args:
            search_item: str: the item to be searched for

        Returns:
            Void
        '''
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="keyword-search"]')))
        search_bar = self.driver.find_element(by=By.XPATH, value='//*[@id="keyword-search"]')
        search_bar.send_keys(search_item)
        search_bar.send_keys(Keys.RETURN)

        return self.driver.current_url

    def get_sub_category_list(self):
        '''
        Some search items navigate to a page showing further product categories rather
        than individual products. The page html will contain n ln__cats if this is the case.
        In this event, retrieve these category names and the urls associated with each of them.

        Args:
            None

        Returns:
            Void 
        '''
        try:
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//ul[@class="n ln__cats"]')))
            sub_category_top_webelement = self.driver.find_element(by=By.XPATH, value='//ul[@class="n ln__cats"]')
        except:
            return self.sub_category_list

        print("Sub-categories detected")
        sub_category_individual_name_webelements = sub_category_top_webelement.find_elements(By.XPATH, value='.//span[@class="ln__facet"]')
        sub_category_individual_names_list = [i.text for i in sub_category_individual_name_webelements]
        sub_category_individual_link_webelements = sub_category_top_webelement.find_elements(By.XPATH, value='.//a')
        sub_category_individual_links_list = [i.get_attribute('href') for i in sub_category_individual_link_webelements]
        self.sub_category_list = list(zip(sub_category_individual_names_list, sub_category_individual_links_list))

        return self.sub_category_list

    def get_sub_category_choice(self):
        '''
        If sub-categories were detected, then display them to the user and
        request the user's choice from them
        '''
        if not self.sub_category_list:
            return
        else:
            print("Your search term gave multiple sub-categories as a result.")
            for i in self.sub_category_list:
                print(i)
            #TODO: error checking for user's input
            sub_category_choice = input("Please select from them to continue")
            self.driver.get(self.sub_category_list[int(sub_category_choice)][1])

    def get_product_links(self):
        '''
        Having arrived at a page of products, either directly from the initial
        search or via a category page, extract urls for each individual product
        
        Args:
            None
        
        Returns:
            Void
        '''
        # Get links to individual products 
        WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//div[@class="row flex-container"]')))
        product_links_webelement = self.driver.find_element(By.XPATH, value='//div[@class="row flex-container"]')
        product_links_individual_webelements = product_links_webelement.find_elements(By.XPATH, value='.//div[@class="lii__product-details"]')
        self.product_links_list = [i.find_element(By.XPATH, value='.//a').get_attribute('href') for i in product_links_individual_webelements]

        return set(self.product_links_list)

    def get_product_features_table(self):
        '''
        Iterates through the list of individual product urls navigating to each page in turn.
        On arrival at at a specific page, select the Specifications tab which contains the
        product data displayed as a table showing the product data field names and the value
        of that field for the product in question. Extract the data into a list.
        Then donwload individual product image files.

        Args:
            None

        Returns:
            Void
        '''
    
        headers={"User-Agent":"Chrome/107.0.5304.110"}
        file_date = str(datetime.datetime.today())
        
        for i in self.product_links_list:
            self.driver.get(i)
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//a[@href="#product_additional_details_container"]')))
            specifications_tab=self.driver.find_element(By.XPATH, value='//a[@href="#product_additional_details_container"]')
            specifications_tab.send_keys("")
            specifications_tab.send_keys(Keys.ENTER)
            
            WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//h1[@id="product_description"]')))
            product_name=self.driver.find_element(By.XPATH,value='//h1[@id="product_description"]').text
            
            product_price_webelement=self.driver.find_element(By.XPATH,value='//input[contains(@id,"analytics_prodPrice_")]')
            product_features_items_webelement_list=self.driver.find_elements(By.XPATH,value='//td[contains(@id,"product_selling_attribute_name")]')
            product_features_values_webelement_list=self.driver.find_elements(By.XPATH,value='//td[contains(@id,"product_selling_attribute_value")]')

            product_features_inner_dictionary={}
            self.product_features_table.append([product_name,"Price",product_price_webelement.get_attribute('value')])
            for i, j in zip(product_features_items_webelement_list, product_features_values_webelement_list):
                self.product_features_table.append([product_name, i.text, j.text])
                product_features_inner_dictionary[i.text]=j.text

            product_features_inner_dictionary["Price"]=product_price_webelement.get_attribute('value')
            self.product_features_dictionary[product_name]=product_features_inner_dictionary

            product_image_link=self.driver.find_element(By.XPATH,value='//img[@id="product_image_0"]').get_attribute('src')
            product_code = product_name[product_name.rfind("(")+1:product_name.rfind(")")]

            response=requests.get(product_image_link,headers=headers)
            file_name=self.output_path+file_date+"_"+product_code+".jpg"
            if response.status_code==200:
                with open(file_name, "wb") as f:
                    f.write(response.content)
            else:
                print("Image download failed. Response code: "+response.status_code)
                print(product_image_link)

    def export_json(self):
        with open(self.output_path+"product-features-data.json", "w") as f:
            json.dump(self.product_features_dictionary, f)

    def transform_product_table(self):
        '''
        Takes list of product data and transforms it so as to contain consistent field names
        for each product within the list. Then outputs the list to a csv file.
        Uses set property of uniqueness to create complete set of product features
        and names without duplication. The product_features_table is first transformed into
        two sets which are then read back into the product_features_list and product_names_list 


        Args:
            None

        Returns:
            Void
        '''

        product_features_set = set()
        product_names_set = set()

        for i in self.product_features_table:
            product_features_set.add(i[1])

        for i in self.product_features_table:
            product_names_set.add(i[0])

        product_features_list = list(product_features_set)
        product_names_list=list(product_names_set)
        
        rows = []
        for i in product_names_list:
            new_row = [i]
            for j in product_features_list:
                found = False
                for k in self.product_features_table:
                    if i==k[0] and j==k[1]:
                        new_row.append(k[2])
                        found = True
                        break
                if not found:
                    new_row.append("N/A")
            rows.append(new_row)
        product_features_list.insert(0,"")

        with open(self.output_path+"scraped-data.csv", "w") as f:
            write = csv.writer(f)
            write.writerow(product_features_list)
            write.writerows(rows)
