from bs4 import BeautifulSoup
import requests
import io
import re
import time
import cProfile
import random
from concurrent.futures import ThreadPoolExecutor


class YardSearch:
    """
    The base class used in every junkyard search
    
    """
    lats = []
    longs = []
    def __init__(self, query_str):
        self.searched_query = self.replace_em_dashes(query_str)
        self.queries = self.searched_query.strip().split(',')
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }
        self.results = []
        self.base_url = ''
        self.long = 0
        self.lat = 0
        self.base_params = {}
        self.inventory_headers = ()
        self.name = ''
        self.elem_id = ''
        self.time_elapsed = 0
        self.session = requests.Session()
        self.session.headers.update(self.base_headers)

    def appendLocation(self):
        print(f"{self}")
        YardSearch.lats.append(self.lat)
        YardSearch.longs.append(self.long)
        
    def set_inventory_headers(self, inventory_headers):
        self.inventory_headers = inventory_headers

    def set_url(self, new_url=""):
        self.base_url = new_url

    def add_result(self, inventory_vehicle):
        self.results.append(inventory_vehicle)

    def update_headers(self, new_headers={}):
        self.base_headers.update(new_headers)

    def update_params(self, new_params={}):
        self.base_params.update(new_params)
        print("Base params After Update:", self.base_params)

    def set_time_elapsed(self, time_elapsed):
        self.time_elapsed = time_elapsed

    def replace_em_dashes(self, query="") -> str:
        """
        Replaces em-dashes and hyphens (in query) with a default '-'
        """
        query = query if len(query.strip()) > 0 else self.searched_query
        return query.replace('–', '-').replace('—', '-')

    def is_year_present(self, query="") -> bool:
        query = query if len(query.strip()) > 0 else self.searched_query
        # Does the query contains patterns '2004 ' or '08 ' 
        return True if re.findall(r"^\d{2}\s|^\d{4}\s", query) else False

    def is_year_range_present(self, query="") -> bool:
        query = query if len(query.strip()) > 0 else self.searched_query
        # Does the query contains patterns '2004-2012 ' or '02-11'
        return True if re.findall(r"^(\d{2}-\d{2}\s)|^(\d{4}-\d{4}\s)", query) else False

    def parse_car_year(self, query="") -> str:
        """
        Strips a given query str of it's year
        parse_car_year('2004 Honda Civic') => '2004'
        """
        query = query if len(query.strip()) > 0 else self.searched_query
        assert self.is_year_present(query)

        # Find the characters of query matching patterns '02' or '2004'
        car_year = re.findall(r"^\d{2}\s|^\d{4}\s", query)[0].strip()

        # Place the current year's prefix if car year had 2 characters (e.g: '01'->'2001')  
        formatted_car_year = car_year if len(car_year) == 4 else f"20{car_year}"
        return formatted_car_year

    def parse_car_year_range(self, query="") -> tuple:
        """
        Strips a given query str of minimum and maximum years

        parse_car_year_range('2004-2008 Honda Civic') => ('2004','2008')
        """
        query = query if len(query.strip()) > 0 else self.searched_query
        assert self.is_year_range_present(query)
        range_str = re.findall(r"^\d{2}-\d{2}|^\d{4}-\d{4}", query.strip())[0]
        min_year = range_str.split('-')[0]
        max_year = range_str.split('-')[1]
        formatted_min_year = "20" + min_year if len(min_year) == 2 else min_year 
        formatted_max_year = "20" + max_year if len(max_year) == 2 else max_year 

        return (formatted_min_year,formatted_max_year)


    def extract_conditionals(self, query="") -> dict:
        conditionals = {}
        query = query if len(query.strip()) > 0 else self.searched_query
        semantics = query.strip().split(' ')

        if self.is_year_present(query):
            conditionals['year'] = self.parse_car_year(query)
            semantics.pop(0)
        elif not self.is_year_present(query) and self.is_year_range_present(query):
            conditionals['minYear'], conditionals['maxYear'] = self.parse_car_year_range(query)
            semantics.pop(0)
        
        conditionals['original_query'] = query
        conditionals['make'] = semantics[0]
        semantics.pop(0)
        conditionals['model'] = ' '.join(semantics)
        return conditionals

    def satisfies_conditionals(self, inventory_vehicle_tuple, conditionals):
        """
        Given extracted vehicle tuple, return True if the vehicle tuple passes year based conditonals
        """
        # Let's find the year of the given tuple
        try:
            # Grabbing the index of 'year' from this junkyard's inventory headers (int)
            vehicle_year_index = self.inventory_headers.index('year')
            # Locate the vehicle's year from the given tuple using that index (str)
            vehicle_year = inventory_vehicle_tuple[vehicle_year_index]
            
        except ValueError as e:
            return False

        vehicle_matches_year = ('year' in conditionals.keys() and vehicle_year == conditionals['year'])
        vehicle_in_year_range = ('minYear' in conditionals.keys() and int(vehicle_year) in range(int(conditionals['minYear']), int(conditionals['maxYear']) + 1))
        ignore_year_and_range = ('minYear' not in conditionals.keys()) and ('year' not in conditionals.keys())

        #print(f'extracted_year: {vehicle_year} \n conditionals: {conditionals} \n match_year:{vehicle_matches_year} \n vehicle_in_range:{vehicle_in_year_range} \n ignore_year_and_range: {ignore_year_and_range}')
        if(vehicle_matches_year or vehicle_in_year_range or ignore_year_and_range):
            return True
        else: 
            return False

    def handle_queries(self, queries=[]):
        queries = queries if len(queries) > 0 else self.queries
        t0 = time.time()
        for query_iteration, query in enumerate(queries):
            conditionals = self.extract_conditionals(query)
            #... grab matching vehicles from online inventory that matches the filter, and satisfies the conditional 
            self.fetch_inventory(conditionals=conditionals)
        t1 = time.time()
        self.set_time_elapsed(round(t1-t0, 2))


    def fetch_inventory(self, conditionals={}):
        """ 
        Returns prettified version of junkyard site HTML (BeautifulSoup)
        """
        time.sleep(random.uniform(1.0,2.0))
        response = self.session.get(self.base_url, headers=self.base_headers, params=self.base_params)
        soup = BeautifulSoup(response.text, "lxml")
        return soup

    def data_as_dict(self):
        return {
            "name": self.name, 
            "elem_id" : self.elem_id,
            "num_results": len(self.results),
            "time_elapsed": self.time_elapsed,
            "result_headers": self.inventory_headers,
            "results": self.results,
            "lat": self.lat,
            "long": self.long,
        }
