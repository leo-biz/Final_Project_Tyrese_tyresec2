import json
from django.shortcuts import render, redirect
from django.http.response import HttpResponse, JsonResponse
from yardsearcher.utils.jup import *
from yardsearcher.utils.lkq import *
from django.views.generic.base import TemplateView
from yardsearcher.utils.queries import *
from django.db.models import Q, Count
from django.db.models.functions import Lower
from django.forms.models import model_to_dict
from yardsearcher.models import (
	Vehicle,
	Junkyard,
	Review,
)
from yardsearcher.forms import ReviewForm

# For API Use
VALID_FIELDS = ['year', 'make', 'model', 'vin', 'row','color', 'space', 'available_date']
VALID_ORDERS = ("","-")

def get_avg(li):
	dividend = len(li) if len(li) > 0 else 1
	return sum(li) / dividend

def get_query_results(queries):
	"""
	Returns vehicles matching searched queries
	"""
	
	constructed_query = construct_db_query(queries)
	print(f"generated query: {constructed_query}")
	return Vehicle.objects.filter(constructed_query)


def construct_db_query(queries):
	""" 
	Constructs a single Q object from list of query dicts
	"""
	constructed_query = Q()
	for vehicle_dict in queries:
		print(f"constructing Q value of {vehicle_dict}")
		condition = Q()
		# If a range of years are present
		if 'minYear' in vehicle_dict and 'maxYear' in vehicle_dict:
			condition &= Q(year__gte=vehicle_dict['minYear'], year__lte=vehicle_dict['maxYear'] )
		if 'year' in vehicle_dict: 
			condition &= Q(year=vehicle_dict['year'])
		if 'make' in vehicle_dict:
			condition &= Q(make__icontains=vehicle_dict['make']) | Q(model__icontains=vehicle_dict['make'])
		if 'model' in vehicle_dict:
			condition &= Q(model__icontains=vehicle_dict['model']) | Q(make__icontains=vehicle_dict['model'])
		constructed_query |= condition

	return constructed_query

def format_results(results, t0):
	lats = []
	longs = []
	formatted_results = []
	unique_yards = Junkyard.objects.all()
	for junkyard in unique_yards:
		lats.append(junkyard.lat)
		longs.append(junkyard.long)
		formatted_result = {
			'results': results.filter(junkyard_id=junkyard.pk),
			'time_elapsed': time.time() - t0,
			'meta': model_to_dict(junkyard),
		}
		formatted_result['meta']['lat'] = junkyard.lat
		formatted_result['meta']['long'] = junkyard.long
		formatted_result['num_results'] = len(formatted_result['results'])
		if formatted_result['num_results']>0:
			formatted_results.append(formatted_result)
	return (formatted_results, get_avg(lats), get_avg(longs))

def serialize_results(formatted_results):
	serializable_results = []
	#serialize_results['results'] = [instance_to_dict(junkyard) for junkyard in formatted_results]
	for yard_result in formatted_results:
		qs = yard_result['results']
		yard_result['results'] = [ instance_to_dict(vehicle) for vehicle in qs]
		serializable_results.append(yard_result)
  
	return serializable_results

def results_view(request):
	"""
		renders fetched junkyard results to results.html template
	"""
	context = {}
	if request.method == "GET":
		
		query = request.GET.get('q')
		t0 = time.time()
		queries = get_query_conditionals(query)
		results = get_query_results(queries)
		formatted_results, avg_lat, avg_long = format_results(results, t0)
		context = {
			'fetched_yard_data': formatted_results,
			'query': query,
			'total_yards': Junkyard.objects.all().count,
			'total_vehicles': Vehicle.objects.all().count,
			'yard_data_json':{
       			"avg_lat": avg_lat,
				"avg_long": avg_long,
          		"yard_data": serialize_results(formatted_results),
			}
		}
		return render(request, 'yardsearcher/results.html', context)

def instance_to_dict(instance)->dict:
    """
    Returns a dict of data from the instance (including the output of this instance's `get_duration()` magic method)
    """
    return {
		"year": instance.year,
		"make": instance.make,
		"model": instance.model,
		"vin": instance.vin,
		"color": instance.color,
		"space": instance.space,
		"row": instance.row,
		"available_date": instance.get_duration(),
	}
    
def api_test_json_response(request):
    return JsonResponse({"ok":True}, safe=True)

def api_sort_table(request):
	"""
	Supplies results page with sorted table as json
	(w/ support for q, yardId, sortBy, orderBy params )
	"""
	if request.method == "GET":
  
		try:
			# Capturing URL parameters
			query = request.GET.get('q')
			order = request.GET.get('order')
			yardId = request.GET.get('yardId')
			sortBy = request.GET.get('sortBy')
   
			# Validate them
			assert query and yardId and sortBy in VALID_FIELDS and order in VALID_ORDERS
			
			# Construct the database query fom them
			query_conditionals = get_query_conditionals(query)
			db_query = construct_db_query(query_conditionals)
			db_query &= Q(junkyard_id=yardId)
   
			# Query and sort the data 
			unordered_vehicle_qs = Vehicle.objects.filter(db_query) 
			sorted_vehicle_qs = unordered_vehicle_qs.order_by(f'{order}{sortBy}')
			
			# Queries in Django return querysets (list of model instances)
			# Help JSON serialize those model instances
			sorted_vehicles = [instance_to_dict(vehicle) for vehicle in sorted_vehicle_qs]
			return (JsonResponse(
				{	"ok": True,
					"query": query,
					"order": order,
					"yardId": yardId,
					"sortBy": sortBy,
					"vehicles": sorted_vehicles,
				},
                	safe=False
                )
          	)
		except AssertionError as e:
			return JsonResponse({"ok": False, "msg":"Sort Table API needs valid q, order, sortBy, and yardId URL parameters "}, safe=False)
		
class ReviewView(TemplateView):
    template_name = "yardsearcher/feedback.html"
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['form'] = ReviewForm
        return context
    
    def post(self, *args, **kwargs):
        form = ReviewForm(self.request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            Review.objects.create(
				feedback=cleaned_data['feedback'],
				email=cleaned_data['email'],
				rating=cleaned_data['rating'],
			)
            return redirect('home_urlpattern')

        return render(self.request, self.template_name, {'form': form})
