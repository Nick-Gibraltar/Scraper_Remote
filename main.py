import scraper_remote

def main(search_term):                                                                   
    print("2. Entering main")
    data_collect = scraper_remote.Scraper()
    data_collect.open_url()
    data_collect.cookies_check()
    data_collect.initial_search(search_term)
    data_collect.get_sub_category_list()
    data_collect.get_sub_category_choice()
    data_collect.get_product_links()
    data_collect.get_product_features_table()
    data_collect.export_json()
    data_collect.transform_product_table()

if __name__=='__main__':
    print("1. Name == Main")
    main("grout")