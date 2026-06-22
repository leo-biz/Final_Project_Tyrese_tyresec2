from base import YardSearch
import cProfile
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

class LKQSearch(YardSearch):
    """
    Represents a search on the LKQ junkyard data
    
    Attributes:
        query (str): The raw search query in string form.
        results (list): Holds the inventory data.
        yard_info (dict): Metadata about the yard itself.
        base_url (str): URL holding the inventory data.
        headers (dict): Content headers for web scraping.
        params (dict):  URL parameters for requesting site data  
    """
    
    def __init__(self, query, params={}):
        """
        Initializes search instance
        
        Args: 
            querys (str): The raw search query 
        """
        super().__init__(query)
        self.name = "LKQ Blue Island"
        self.base_url = "https://www.pyp.com/DesktopModules/pyp_vehicleInventory/getVehicleInventory.aspx"
        self.base_headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Referer": f"https://www.pyp.com/inventory/{params['referer_suffix']}/",
            "X-Requested-With": "XMLHttpRequest",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9"
        }
        self.base_params = {}
        self.temp_inventory_headers = []
        self.inventory_headers = ()
        self.lat = 41.6325570
        self.long = -87.6731408
        self.elem_id = "lkq"
        self.params = params
        self.page_results = []
        super().appendLocation()
        
    def fetch_inventory(self, conditionals={}):
        with ThreadPoolExecutor(max_workers=3) as executor:
            page_results = executor.map(self.fetch_page_results, range(1,80))
            
        for page in page_results:
            self.handle_page(page)

    def fetch_page_results(self, page_number):
        params = {
            "page": page_number,
            "filter": "",
            "store": self.get_store_id()
        }
        # Request page soup
        response = self.session.get(self.base_url, headers=self.base_headers, params=params)
        soup = BeautifulSoup(response.text, "lxml")
        
        # format response results as list of tuples
        vehicles = soup.find_all(class_="pypvi_resultRow")
        page_results = [self.extract_data(vehicle) for vehicle in vehicles if vehicle.find(class_="pypvi_ymm") ]
        return page_results if len(page_results) > 0 else []
    
    def get_store_id(self):
        return str(self.params['store_id'])
    
    def handle_page(self, page):
        """ 
        Given array of parsed vehicle tuples, append to results attr
        """
        for vehicle in page:
            if not page == []:
                self.results.append(vehicle)
                
    # Turns matching vehicle card HTML and formats the content into a dictionary
    def extract_data(self,vehicle) -> tuple:
        inventory_car = {}
        year_make_model = vehicle.find(class_="pypvi_ymm").get_text(' ', strip=True)
        inventory_car['year'] = year_make_model.split(' ')[0]
        inventory_car['make'] = year_make_model.split(' ')[1]
        inventory_car['model'] = year_make_model.split(' ')[2]
        details = vehicle.find_all(class_="pypvi_detailItem")
        #loop through each detail item (color, stock, available inventory_car, etc)
        for detail in details:
            items = detail.find_all('b')
            if len(items) > 0:
                for item in items:
                    field_name = item.get_text(strip=True).replace(':','').lower().strip()
                    self.temp_inventory_headers.append(field_name)
                    if('available' in field_name):
                        item_value = detail.find('time').get_text()
                    else: 
                        item_value = item.next_sibling.strip()
                    inventory_car[field_name] = item_value

  
        return self.convert_car_to_tuple(inventory_car)

    def convert_car_to_tuple(self, inventory_car):
        self.inventory_headers = tuple(inventory_car.keys())
        return (
            inventory_car['year'], 
            inventory_car['make'],
            inventory_car['model'],
            inventory_car['color'],
            inventory_car['vin'],
            inventory_car['section'],
            inventory_car['row'],
            inventory_car['space'],
            inventory_car['stock #'],
            inventory_car['available'],
        )
        

    def display_data(self):
        if len(self.results) == 0:
            return ''

        print('\n')
        print('|',self.yard_info['name'])
        print('\n')
        print('Year, Make, Model, Row, Space, Color, VIN, Stock#, EntryDate')
        for result in self.results:
            print(f"{result['year']}, {result['make']}, {result['model']}, {result['row']}, {result['space']}, {result['color']},{result['vin']}, {result['stock #']}, {result['available']}")
    

# Example usage:
if __name__ == '__main__':
    stop = False
    while(stop != True):
        query = input('\nEnter year, make, model: ')
        if query.strip().lower() in ['stop','halt','exit']:
            stop = True

        yardSearch = LKQSearch(query,{'store_id':1582, 'referer_suffix': 'blue-island-1582'})
        cProfile.run("yardSearch.handle_queries()")
        print(len(yardSearch.results))


