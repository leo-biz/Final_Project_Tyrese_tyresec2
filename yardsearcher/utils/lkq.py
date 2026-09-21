from .base import YardSearch
import cProfile

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
            "Accept-Language": "en-US,en;q=0.9"
        }
        self.base_params = {}
        self.temp_inventory_headers = []
        self.inventory_headers = ()
        self.lat = 41.6325570
        self.long = -87.6731408
        self.elem_id = "lkq"
        self.params = params
        super().appendLocation()

    def fetch_inventory(self, conditionals={}):
        page_number = 1
        #While valid page exists 
        while(self.is_page_valid(page_number, conditionals)):
            page_number += 1
        return self.results


    def is_page_valid(self, page_number, conditionals={}) -> bool:
        # Grabs all divs HTML 
        vehicle_cards = self.fetch_inventory_html(page_number, conditionals)
        return len(vehicle_cards) > 0


    def fetch_inventory_html(self, page_number, conditionals={}) -> list:
        self.base_params = {
            "page": page_number,
            "filter": conditionals['original_query'],
            "store": str(self.params['store_id'])
        }
        soup = super().fetch_inventory(conditionals)
        vehicle_cards = soup.find_all(class_="pypvi_resultRow")
        if len(vehicle_cards) > 1:
            self.handle_vehicle_cards_html(vehicle_cards, conditionals)
        return vehicle_cards


    def handle_vehicle_cards_html(self, vehicle_cards=[], conditionals={}):
        for card in vehicle_cards:
            vehicle_data = self.extract_card_html(card)
            if super().satisfies_conditionals(vehicle_data, conditionals):
                self.results.append(vehicle_data)


    # Turns matching vehicle card HTML and formats the content into a dictionary
    def extract_card_html(self,card_html) -> dict:
        inventory_car = {}
        year_make_model = card_html.find(class_="pypvi_ymm").get_text(' ', strip=True)
        inventory_car['year'] = year_make_model.split(' ')[0]
        inventory_car['make'] = year_make_model.split(' ')[1]
        inventory_car['model'] = year_make_model.split(' ')[2]

        stock = card_html.find(class_="pypvi_stock")
        if stock:
            color_stock = stock.get_text(" ", strip=True).split("·")
            inventory_car["color"] = color_stock[0].strip()
            if len(color_stock) > 1:
                inventory_car["stock #"] = color_stock[1].strip()

        for location_cell in card_html.select("table.locate td"):
            label = location_cell.find("span")
            value = location_cell.find("b")
            if label and value:
                inventory_car[label.get_text(strip=True).lower()] = value.get_text(strip=True)

        details = card_html.find_all(class_="pypvi_detailItem")
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
            else:
                detail_text = detail.get_text(" ", strip=True)
                if detail_text.startswith("VIN "):
                    inventory_car["vin"] = detail_text.replace("VIN ", "", 1).strip()
                elif "Available" in detail_text:
                    time_elem = detail.find("time")
                    inventory_car["available"] = time_elem.get_text(strip=True) if time_elem else detail_text.replace("Available", "", 1).strip()

  
        return self.convert_car_to_tuple(inventory_car)

    def convert_car_to_tuple(self, inventory_car):
        self.inventory_headers = (
            'year',
            'make',
            'model',
            'color',
            'section',
            'row',
            'space',
            'stock #',
            'vin',
            'available',
        )
        return (
            inventory_car.get('year', ''),
            inventory_car.get('make', ''),
            inventory_car.get('model', ''),
            inventory_car.get('color', ''),
            inventory_car.get('section', ''),
            inventory_car.get('row', ''),
            inventory_car.get('space', ''),
            inventory_car.get('stock #', ''),
            inventory_car.get('vin', ''),
            inventory_car.get('available', ''),
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
        yardSearch.display_data()
