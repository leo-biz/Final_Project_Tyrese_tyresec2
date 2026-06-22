# Dev Journal


## 3/1/2026

On the 22nd, I introduced Scraphounds to 3 guys @ Autozone. I asked for feedback and they asked if there was a feature to leave reviews. 

Implementing said feature would consist of: 
*   Developing `Review` model 
*   Developing a ListView binded to  `POST /reviews`
*   Developing a template 

### Objectives
#### Developing `Review` model 

a review consists of a rating, feedback, date created, email, keep_posted. Users are not considered in this version of the application. Not until someone specifically says so in the feedback. 

(it'd be cool to compile all feedback into a list for OpenAI to prioritze implentation order based on relevancy)

#### Using gear icons as review scale

I don't fancy the HTML5 provided slides or number inputs. I'd rather users click gear svgs to give a rating. 

I'll do this in Javascript by first subsituting 5 gear svgs with the rating input.
The appearance will be controlled in CSS using `.rating-icon`
These svgs will have number values (1-5) associated with them in their `data-rating` attribute
Those number values will get passed:
-   into `update_ratings(new_rating=int)` that triggers when clicked
-   into `hover_prior_ratings(new_rating=int)` that partially highlights prior ratings


##### Logic for update_ratings(new_rating)

if current_rating != new_rating
1. Turn off all ratings 
2. Illuminate up to new_rating
3. set value of hidden rating input for form 


## 2/28/26

### Objectives


#### [x] Skip over junkyards that don't successfully refresh

Implemented a try-catch on `utils/refresh_inventories.py`

#### [x] Create model to track scrape events 

I modified the Lkq scraper work with concurrency but violated the TSL/ SSL protocol. I learned that faster isn't always the most reliable long-term because I'm being blocked on a connection-level:

```
# yardsearcher/management/commands/refresh_inventories.py 
Can't scrape: HTTPSConnectionPool(host='www.pyp.com', port=443): Max retries exceeded with url: /DesktopModules/pyp_vehicleInventory/getVehicleInventory.aspx?page=1&filter=&store=1582 (Caused by SSLError(SSLEOFError(8, 'EOF occurred in violation of protocol (_ssl.c:1129)')))

```

I intend on adding this command to a scheduler. In the event that a junkyard isn't updated, I must see the status, the junkyard ID, the reason for failure, and the date. I'll also log the successful scrapes in the same model.

##### Scrape model 1.0.0
-   status: Success or Fail('1','0') 
-   error: error message is blank text
-   junkyardID: foreign key to Junkyard
-   refresh_date


## 2/25/26 

### Objectives

#### Updating lkq scraper to move faster

The refresh command synchronously calls upon every yard scraper. The LKQ Scrapers (`LKQSearch`) move slower than the other scrapers because of how I handle a junkyard's use of pagination [to display their data].

##### cProfile results

I ran a cProfile report on this scraper using blue island parameters and an empty search query (as to return the whole inventory), and the report says:

*   `9708253 function calls (9706638 primitive calls) in 136.092 seconds`
*   `1    0.000    0.000  136.092  136.092 lkq.py:44(fetch_inventory)`
*   `69    0.000    0.000  136.092    1.972 lkq.py:52(is_page_valid)`
*   `69    0.002    0.000  136.092    1.972 lkq.py:58(fetch_inventory_html)`

`fetch_inventory()` while-looped `is_page_valid()` 69 times. is_page_valid pretended to be a simple bool-returning predicate but it does network I/O, parses HTML, and mutates state of class attributes (b/c it triggers fetch_inventory_html). That while-loop essentially says  "fetch_inventory_html on this page (~2s), then fetch_inventory_html on the next page (~2s), and so on until fetch_inventory_html comes back empty. This sequential execution is responsible of the bottleneck.

##### Introducing ThreadPoolExtractor

The original implementation of LKQSearch was intentionally simple: iterate through paginated inventory pages, fetch HTML, parse vehicle cards, and append structured results into a shared list. This worked reliably but was slow — each page request blocked the entire process.

As the page count grew (≈80 pages per yard), network latency became the dominant cost.

At this stage, the primary goal was throughput, not sophistication.

I replaced the while-loop from `fetch_inventory` with the ThreadPoolExtractor code and learned that I would need to use one of two methods (provided by `Executor`):

- [`Executor.map()`](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.Executor.map)
- `Executor.submit()`

Using the first allows me to asnynchronously call a *fn* over iterables / list . The iterables will be a range of page numbers from 1-> 80 (lkq stops at 68 according to the cProfile results above). It's best to give the workers everything they need to process a page (b/c they may try many pages at once)

Since each page may have a list of results, a worker would need to make a request to the page, and extract the list of results from that request's response. For these reasons, I gave the workers:

- fetch_page_results(page_number): to request page level results and return as list of tuples [('2018', 'CHEVROLET', 'SONIC', 'Black', '1G1JD5SB1J4120381', 'GM', '48', '20', '1582-82961', '11/7/2025')]

This works for concurrency because the workers are not concerned about shared mutable states. Unforunately, this led to an SSL error because because of how the requests hit concurrently in complete disregard of *politeness*

## 2/17/26

### Objectives
#### Updating map marker buttons to trigger collapse icons 

Clicking 'See X Vehicles' on the map would expand the correct inventory but not change the collapse icon. 

Clicking the collapse icon spins it around and turns the background orange. That visual animation should **also** be triggered when clicking 'See X Vehicles'   

The `See X Vehicle` button calls the function `handleJunkyardClick()` (now `showInventory()`) It would:
*   Unhide an inventory  
*   Scroll browser to the inventory

The line of code that unhides the inventory code is duplicated in the `toggleTable()` function. So I'll simply reuse that function in `showInventory()` because it already: 
*   Unhides an inventory
*   Triggers the collapse icon animation 


#### Move map building js to external sheet

    Django processes templates on the server, but Javascript exists in the browser.

Because I pass results data to the `results.html` template, I can access it in JS if it exists in the same sheet. When I move the JS code to another sheet (for readability purposes), I lost the connection to the results data. 

That method was not secure. A [more secure way](https://adamj.eu/tech/2020/02/18/safely-including-data-for-javascript-in-a-django-template/) involved using the `json_script` template tag to output the data to the external JS (HTML injection proof)

The data being passed was not JSON serializable. I used `model_to_dict` to serialize the querysets or model instances when needed and altered the corresponding variables used in `results.html` 

With the data serializable, I can refactor the external map building JS .

##### refactor the external map building JS 

Much of the Leaflet map building JS code relied on data passed from Django template tags ({{}}). Now that I'm passing data to an external JS file, I have to refactor the old JS code. 

#### Update map UI to expand icons onclick

The code I had gotten from that AI had a feature that would expand the map marker icon when clicked. The map felt dull, so I went back to the commit with the original features looking for inspiration.

The original JS for that feature would refresh the map every time a marker got clicked. I reproduced that code by introducing:
*   `selected_junkyard`: Captures junkyard data for last clicked marker
*   `isSelected: bool that determines the size of a marker icon
*   `removeMarkers()`: clears `markers` list and removes icons from map
*   `handleMarkerClick(*yard*)`: sets `selected_junkyard`, refreshes map, opens popup, and pans to marker. 
*   `markers`: list of Leaflet markers 

## 2/16/26

### Objective
-   ~~Enable sorting inventory data by columns (Year, make, date, etc).~~ 
    - ~~Updating sorting carets to appear muted when not in use~~
    - ~~Change API to provide dates from the `Vehicle.get_duration()` magic method~~

#### Update sort carets to appear muted when not in use 

I dislike how each sort icon appeared in use. I'll have them greyed out before they are clicked and when a different icon is clicked. To track the state, I'll add the `data-isusing` attribute on the \<th> elements holding these icons. 

`data-isusing` will be set true when a client clicks a \<th> element, and false when the page loads or a different icon is clicked. This change will take place in the JS function `toggleOrder()`

This will enable control over the colors of every sort icon that is in/not in use. Now I can turn unused sort icons grey using the CSS selector: `th[data-isusing="false"] > svg > path.sort-caret`

In JS, I can now find the </th> element that is in use and "turn it off "

#### Changed Collapse caret icon 

I've decided to switch caret icons for the collapse menus and change its 'feel' a bit. When a user clicks the collapse icon, it turns orange and rotates


#### Change sort table API to provide readable dates for the available_date key 

In v1.0.2, Every `Vehicle` instance got a magic method called `get_duration()` that returns its `available_date` as a readable format (i.e., "4 days ago"). It is used in the Django `results.html` template 

Unfortunately the API (in its current state) does not use that method when creating its JSON because I used Django's built-in `model_to_dict()` to quickly make vehicle instances serializable. Instead of letting this built-in function take care of it, I'll manually spcecify what data to use from the vehicle instances in a function called instance_to_dict

##### Building `instance_to_dict()`

Question: Does a Django model instance have access to Python's `dict.keys()` method, or something similar? 
Surveys Says: ........................... No, they aren't dictionaries.  

Given a model instance, I'll return a JSON serializable dictionary containing data from the instance (including the output of this instance's `get_duration()` magic method)

###### Snippet of Sort table API (v1.1.0)

```
 "vehicles": [
        {
            "year": 2002,
            "make": "TOYOTA",
            "model": "CAMRY",
            "vin": "4T1BF30K32U516113",
            "color": "Silver",
            "space": 15,
            "row": 22,
            "available_date": "3 months ago"
        },...
 ]
```


## 2/15/26

### Today's Objective
-   Enable sorting inventory data by columns (Year, make, date, etc). 
    - ~~Get JS function that's triggered by `<th>` elements to prepare parameters~~
    - ~~Use parameters to make request to internal API (sort table)~~
    - ~~Rebuild specific table's body based on API results~~
    - ~~Use svgs as visual state trackers for any clicked \<th> element's `data-order` attribute~~



#### Setting up the JS call to internal API for sorting inventory tables
1.place `sortby`, `order` params in \<th> elements attrs 
1. set \<th> element's `onclick` to sortInventory function
2. Develop sortInventory to prep parameters (from \<th>, & url), 
3. call API
4.rebuild *the appropiate table*

##### Curent Internal API State (v1.0.3 ->  v1.1.0)
```
{
  "ok": true,
  "query": "00",
  "order": "",
  "yardId": "17",
  "sortBy": "model",
  "vehicles": [
    {
      "year": 2000,
      "make": "mercedes-benz",
      "model": "c-class",
      "color": "",
      "row": 25,
      "space": 0,
      "vin": "",
      "available_date": "2025-12-13"
    }, {}, {}...
 ]
}
```
##### Gathering Params

*   `order`: held in data-order of \<th>
*   `sortBy`: held in data-name of \<th> elements
*   `yardId`: held in parent `<tr>` of \<th> element because it's closer in the DOM tree (than \<table>) and its static 
*   `q`: held in the q paramenter of the URL (because the input box is subject to change)

#### Rebuilding the *appropriate* table from API

Because junkyards collect different info on their vehicles, there are a different number of columns for each table. However, every vehicle dictionary provided by the API has the same number of keys and **some keys have empty values**.

To help JS determine what keys to use in the API result (& create table rows from), I collect the non-empty keys to use from any given table's \<th> elements by accessing the `data-sortby` attibutes. I call these keys `inventory_keys` or and `valid_fields`

They're passed into the create table row function where they are used to grab only the non-empty values from the API and determine what CSS classes to use for the \<td> elements. When a \<tr> element is prepped  with the \<td> elements and ready to go, it is appended to the appropriate table body element

#### Enabling toggle order 

Clicking the \<th> elements will sort the table by that element's `data-sortBy` attribute **once**. This is because that element's `data-order` attribute has not changed. 

`data-order` starts at ascending order and *should* switch when the table has been sorted. For that reason, I'll create a `toggleOrder` function that takes in the `<th>` element as a parameter. 

If `th[data-order]` is "" (ascending) then set to "-" (descending),  else set to "". This function will be executed at the end of `sortInventory`

[I Found a cool sort icon](https://fontawesome.com/icons/sort). I'll have the top caret light up when the order is originally ascending or the bottom when the order is originally descending.

##### Snippet of sort Icon SVG element

```
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Pro v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2026 Fonticons, Inc.--><path d="M130.4 268.2C135.4 280.2 147 288 160 288L480 288C492.9 288 504.6 280.2 509.6 268.2C514.6 256.2 511.8 242.5 502.7 233.3L342.7 73.3C330.2 60.8 309.9 60.8 297.4 73.3L137.4 233.3C128.2 242.5 125.5 256.2 130.5 268.2zM130.4 371.7C125.4 383.7 128.2 397.4 137.3 406.6L297.3 566.6C309.8 579.1 330.1 579.1 342.6 566.6L502.6 406.6C511.8 397.4 514.5 383.7 509.5 371.7C504.5 359.7 492.9 352 480 352L160 352C147.1 352 135.4 359.8 130.4 371.8z"/></svg>
```

Man I was hoping for two different <paths>. I'll break them apart the top and bottom carets apart in inkscape then copy/paste the SVGs in the \<th> element. Since the SVGs will be inside of the \<th> elements, I can access the right ones by simply grabbing the last child of a clicked \<th> element. 

##### Snippet of sort Icon SVG element (post Inkscape)
```
<svg
   viewBox="0 0 640 640"
   version="1.1"
   xmlns="http://www.w3.org/2000/svg">

  <!--!Font Awesome Pro v7.2.0 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license (Commercial License) Copyright 2026 Fonticons, Inc.-->
  <path
     d="m 130.4,371.7 c -5,12 -2.2,25.7 6.9,34.9 l 160,160 c 12.5,12.5 32.8,12.5 45.3,0 l 160,-160 c 9.2,-9.2 11.9,-22.9 6.9,-34.9 -5,-12 -16.6,-19.7 -29.5,-19.7 H 160 c -12.9,0 -24.6,7.8 -29.6,19.8 z"
      class="sort-caret"/>
  <path
     d="m 130.4,268.2 c 5,12 16.6,19.8 29.6,19.8 h 320 c 12.9,0 24.6,-7.8 29.6,-19.8 5,-12 2.2,-25.7 -6.9,-34.9 l -160,-160 c -12.5,-12.5 -32.8,-12.5 -45.3,0 l -160,160 c -9.2,9.2 -11.9,22.9 -6.9,34.9 z"
     class="sort-caret" />
</svg>
```
**That's better**. Now I can access either caret in CSS using something like `th[data-order=""] > svg > path.sort-caret:first-child`

## 2/14/26

### Objective
*   Enable sorting inventory data by columns (Year, make, date, etc). 
*   
#### Building the Internal API to sort inventory tables 

I do not want a refresh to occur because it may disrupt the user's experience. For this reason, JS will be used to dynamically *sort* a table( of choice ) by a column (of set{'year','make','model','entryDate','row'}) 

I'll use JS to fetch data from an internal API and repopulate the DOM instead of undergoing extensive JS work to search the DOM, capture the values, sort the values, and so on.

The former would require:

1. creating a JSONResponse view of results (w/ support for q, yardId, sortBy, orderBy params )
2. introducing JS function that gets triggered by clicking any `<th>` element. It will:
    - make a call to the internal API (**will need q, yardId, sortBy, order params**)
    - (if status ok & results exists) 
        - remove children of clicked **table.tbody**
        - map results list to table row elements 
        - append those table row nodes to clicked table.tbody
        - toggle icon


##### Keep in mind

*   Not all `<th>` elements will be sortable. 
*   `<Vehicle>` instances may have blank or default values for certain fields

##### Creating the JSONResponse View

The 4 parameters must be present for the SortTable API to work (for now). I use assert statements behind a try block and handle assertione errors if the parameters are invalid. 
With the parameters, I construct a query for the database like the one in `results_view`, The difference here is that I add onto that query to filter cars by `junkyard_id`. 

I filter the db with this newly prepped query, then sort the returned data using Django's built-in `order_by` method.  The last two parameters (order & sortBy ) will be combined into a sting and passed into order_by. 

With the newly sorted queryset, the last thing to do is format this. Here I turn the Vehicle instances into a dict for JSON to serialize (Can't serialize querysets). 

###### Expected JSON Output (Bare minimum for sort table feature)
```
{
    "query": "00-07 civic",
    "sortBy": "entryDate",
    "order": "",
    "yardId": 17,
    num_vehicles: 32,
    "vehicles": [
        {
            "year": "2007",
            "make": "Honda",
            "model": "Civic",
            "vin": "",
            "photo": "",
            "space": "",
            "entryDate": "3 months ago",
            "row":75,
        }, ...{},
    ],
}
```


## 2/13/26


Day 2 of adding Pick n Pull Summit to Scraphounds. Thankful for their api

v1.0.2 is configured to scrape data from a url when the refresh_inventories command is run. The command is not used to having JSON handed to it so easily.

Typically, a scraper subclass's `inventory_headers` tuple is set after extracting the text from the appropriate \<th> tags...  With Pnp's API, there's no need to scrape anything! 

I can manually set the `Pnp().inventory_headers` to these keys from the api:
*   barCodeNumber (unique identifier)
*   vin
*  year
*   make
*   model
*   largeImage (in case Scraphounds support vehicle images in the future)
*   dateAdded
 
 Now I can easily clean the vehicle dictionaries (that come back from this API) by extracting **ONLY** the key value pairs with keys that exist in `inventory_headers`

 Unlike other junkyard specific scraper classes, this scraper class doesn't need to use `Yardsearch.results_as_list()` the same. When the vehicle dictionaries are cleaned, they are immediately appended to the `results` attribute. 

 In `yardsearcher.utils.known_yards` I'll manually fill in details like class to use, lat, long, and request params to register Pick n Pull Summit to Scraphounds. 

 I suspect this class's `handle_queries` method to fail when called in `yardsearcher.management.commands.refresh_inventories` because there are no *queries* to pass as a parameter. (Older versions used to pass queries to return matching vehicles from websites ). To prevent this, I will override the parent `handle_queries` method to: 
 1. Fetch all inventory results 
 2. Format each result (removing irrelevant keys from API dictionary)
 3. Append to `results` attribute

 The final step is testing the `refesh_inventory` command & adjusting `yardsearcher.utils.extractors` to account for the different key names that Pick n Pull use ( Pnp uses "dateAdded" for dates; LKQ uses "date available" for dates)

## 2/12/26

I'll be adding Pick n Pull Summit to Scraphounds. ~~I originally intented to scrape their inventory data~~, then  I found their internal api that just returns it

|Properties | Values|
|:------|:------|
|~~Inventory URL~~| ~~https://www.picknpull.com/check-inventory/vehicle-search?distance=10&zip=60501~~|
|API URL| https://www.picknpull.com/api/vehicle/search?&makeId=&modelId=&year=&distance=10&zip=60501&language=english |
|Inventory Table| \<table _ngcontent-gog-c26="" class="table pnpDataTable table-striped table-hover"> |
|Inventory Tablerows  | table.pnpDataTable tbody tr |
|Inventory Tabledata  | table.pnpDataTable tbody tr td.hidden-xs|
|Results headers  | table.pnpDataTable thead tr |


#### Snippet of DOM:
<table>
<thead _ngcontent-gog-c26="" class="hidden-xs"><tr _ngcontent-gog-c26=""><th _ngcontent-gog-c26="" data-field="ThumbNail" class="photo-column hidden-xs"><div _ngcontent-gog-c26="" class="th-inner">Photo</div><div _ngcontent-gog-c26="" class="fht-cell"></div></th><th _ngcontent-gog-c26="" data-field="Year" class="hidden-xs vehicle-year"><div _ngcontent-gog-c26="" class="th-inner sortable both">Year</div><div _ngcontent-gog-c26="" class="fht-cell"></div></th><th _ngcontent-gog-c26="" data-field="Make" class="hidden-xs"><div _ngcontent-gog-c26="" class="th-inner">Make</div><div _ngcontent-gog-c26="" class="fht-cell"></div></th><th _ngcontent-gog-c26="" data-field="Model" class="hidden-xs"><div _ngcontent-gog-c26="" class="th-inner">Model</div><div _ngcontent-gog-c26="" class="fht-cell"></div></th><th _ngcontent-gog-c26="" data-field="Row" class="hidden-xs"><div _ngcontent-gog-c26="" class="th-inner sortable both">Row</div><div _ngcontent-gog-c26="" class="fht-cell"></div></th><th _ngcontent-gog-c26="" data-field="DateAdded" class="hidden-xs set-date"><div _ngcontent-gog-c26="" class="th-inner sortable both">Set Date</div><div _ngcontent-gog-c26="" class="fht-cell"></div></th></tr></thead>
<tr _ngcontent-gog-c26="" data-index="0"><td _ngcontent-gog-c26="" class="photo-column">
<img _ngcontent-gog-c26="" src="https://cdn.row52.com/images/e7af07b7-119d-443a-95c6-715aa49343fb.JPG" alt="1988 Oldsmobile Ninety Eight"></td><!----><!----><td _ngcontent-gog-c26="" class="hidden-xs vehicle-year">1988</td><td _ngcontent-gog-c26="" class="hidden-xs">Oldsmobile</td><td _ngcontent-gog-c26="" class="hidden-xs">Ninety Eight</td><td _ngcontent-gog-c26="" class="hidden-xs">15</td><td _ngcontent-gog-c26="" class="hidden-xs set-date">02/06/2026</td><td _ngcontent-gog-c26="" class="visible-xs" style="text-decoration:line-through;position:absolute"><div _ngcontent-gog-c26="" class="compactTitle" >1988 Oldsmobile Ninety Eight</div><div _ngcontent-gog-c26="">Row 15</div><div _ngcontent-gog-c26="">Set: 02/06/2026</div></td></tr>
</table>

```
<!--Snippet Code-->

<tr _ngcontent-gog-c26="" data-index="0">
    <td _ngcontent-gog-c26="" class="photo-column">
        <img _ngcontent-gog-c26="" src="https://cdn.row52.com/images/e7af07b7-119d-443a-95c6-715aa49343fb.JPG" alt="1988 Oldsmobile Ninety Eight">
    </td>
    <!---->
    <!---->
    <td _ngcontent-gog-c26="" class="hidden-xs vehicle-year">
        1988
    </td>
    <td _ngcontent-gog-c26="" class="hidden-xs">
        Oldsmobile
    </td>
    <td _ngcontent-gog-c26="" class="hidden-xs">
        Ninety Eight
    </td>
    <td _ngcontent-gog-c26="" class="hidden-xs">
        15
    </td>
    <td _ngcontent-gog-c26="" class="hidden-xs set-date">
        02/06/2026
    </td>

    <!-- Will not be needing td.visible-xs -->
    <td _ngcontent-gog-c26="" class="visible-xs">
        <div _ngcontent-gog-c26="" class="compactTitle">
            1988 Oldsmobile Ninety Eight
        </div>
        <div _ngcontent-gog-c26="">
            Row 15
        </div>
        <div _ngcontent-gog-c26="">
            Set: 02/06/2026
        </div>
    </td>
</tr>
```

#### Key Observations:
*   Table data has no identifying attributes (id, name, etc)
*   Not all vehicles have thumbnails
*   I don't need the td element with the `td.visible-xs` class.

## ??? 

I want to alter the scraping process to reduce the number of requests.  
Instead of sending several requests to junkyards everytime the search button is clicked,  I'll cache the inventory data of each junkyard into a new model from one request.  


1) ~~Building a `Vehicles` Model to store vehicle data from every junkyard~~ . 
2) Altering base scraper class to insert results into that model 
3) Building a JSONResponse view (currently @ */api/search/<str:query>* url pattern )
4) Altering `results_view`'s to fetch and handle that JSON  

## Fri Dec 26 

After watching YT Combinator videos w/ my Bro, he volunteered to do a test run of the website as a client / customer. Here are the notes I've gathered: 

- UI unclear (not knowing what to type in main search)
- "Fetch Junkyard Inventories Fast" as a hero header is ambigous  
- donor car concept not clear
- The 'company' name is too... niche. Try Junkyard Car Lookup

**Avatar(s): Mechanical Newbie vs Mechanically Inclined**

First Set of Feedback: 

- 'Assumes map shows results of places matching search query (bc of markers)'
- 'FALSE HOPE WHEN 0 RESULTS. All these fancy feats and sh*t w/ 0 results'
- 'Generations would be cool or automatically giving similar cars automatically?'
- 'Cool, "this 0.0129 secs" is useless to the client'



!!!!!!!2012 toyota corolla test case didn't work !!!!!!!!!!

- 'why show row and space?' 
(*after searching 'honda civic'*)
- Lots of civics i understand but ..... 

	- 'Why spaces in 0' 
	- 'AvailableDate?? 
	- 2025-11-10 ?????????? '

- 'Whats the address of the junkyards?' 

- 'Cool if I could see the address or get direction in my maps'

These notes were the reason I:
- removed the useless sidebar & filter junkyards buttons(for MVP)
- altered the hero text to set the tone. 
- created a dynamic placeholder for main input box to show examples of valid queries 

## Thur Dec 25

I succesfully reduced the amount of requests to junkyard websites by creating a Django command (to be run by a scheduler) that caches inventory data into the internal database ( My God was it a challenge )

Of course I saw it through! Now this application can find 1000s of vehicles in less than 0.1 seconds


## Tue Dec 23

Steps 1 & 2 are complete. Step 4 would have been clearing the models but I will be "upserting" the data.
If a vehicle exists in the db with the same identifier & junkyard_id combo, don't create a new record. 

To do so, I had to set constraints on the models.

After that, I saw an opportunity to detect changes in the vehicles from the junkyards. Junkyards scrap vehicles and remove them from their public databases (`results` in `management/commands/refresh_inventories`) 


Here's my attempt: 

```
Vehicle.objects.exclude(~Q(junkyard_id=junkyard_id) & Q(junkyard_identifier__in=scraped_identifiers))
```

This attempt did not work because I did not consider its truth table.

To determine which vehicles are removed I'll use the two premises: 
- P = Vehicle belongs to junkyard that's being scraped
- Q = Vehicle exists in scraped results

My Original Query

P | Q | ~P| (~P & Q) | ~(~P & Q)
T | T | F | F | T
T | F | F | F | T
F | T | T | T | F
F | F | T | F | T

There were alot more truth outcomes than expected. I expect P= T and Q = F to be the only case where a delete is necesary

P | Q | ? | P & ~Q
T | T | do not delete | F
T | F | delete | T
F | T | do not delete | F
F | F | do not delete | F

There you have it folks, a new query: 

```
different_identifiers = Vehicle.objects.filter(Q(junkyard_id=junkyard_id) & ~Q(junkyard_identifier__in=scraped_identifiers) )
```

## Mon Dec 22

I'm taking on the task `2)Altering the base scraper class`. My plan of attack is to build a script that'll be scheduled to execute @ 2:30 am on my buddy's server. 

Let's test some things

1. ~~Make `management/commands/refresh_inventories.py`~~
2. ~~Import models & scrapers~~
3. ~~Run each scraper w/ empty query~~
4. Clear models if results
5. ~~Loop through results and insert into Vehicles~~

## Sat Dec 20 

- geocode 2.4.1 installed

I'm giving the yard models a magic method that returns a tuple of latitude and longitude decimal values. The goal is to make these values accessible in the templates and views. [This](https://geopy.readthedocs.io/en/stable/#nominatim) is the official geopy documentation

The `results_view` starts the multi-scraping process, and compiles the results into a list of dictionaries named `fetched_yard_data`. Then the **results template** loops through that list, adding markers (w/ tooltips) to the Leafly JS map. 

**Implementing geopy would require that I set JS level variables to the returned tuple before adding the markers.** 
