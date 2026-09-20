from django.core.management.base import BaseCommand
from yardsearcher.models import Junkyard, Vehicle, Scrape

from django.db.models import Q
from yardsearcher.utils.known_yards import KNOWN_YARDS as KNOWN_YARDS
from yardsearcher.utils.extractors import *

def get_junkyard_id(yard: dict)->int:		
	if not Junkyard.objects.filter(address=yard['address']).exists():
		raise ValueError(f"Address of junkyard not found")
	return Junkyard.objects.get(address=yard['address']).pk 

class Command(BaseCommand):
	help = "Refreshes Vehicle Table"

	def handle(self, *args, **options):
		""" 
			Initializes all junkyard scrapers and upserts their results into Vehicle models 
			(Also deletes vehicles that are physically removed from the junkyard )

		"""
		
		self.stdout.write(f"\n\n Refreshing {len(KNOWN_YARDS)} inventories")
		for i,yard in enumerate(KNOWN_YARDS):
			error = ""
			status = 0
			stage = "initial"
			yard['id'] = 0
			try:
				self.stdout.write(f"\n[{i+1}/{len(KNOWN_YARDS)}] {yard['name']}'s vehicles")

				stage = "getting junkyard id"
				yard['id'] = get_junkyard_id(yard)

				stage = "setting up scraper"
				scraper = yard['class']("") if 'params' not in yard.keys() else yard['class']("", params=yard['params'])

				stage = "scraping"
				scraper.handle_queries()

				stage = "updating db"
				self.cache_scraper_results(scraper.results_as_list(), yard)

				stage = "complete"
				status = 1
				self.stdout.write(self.style.SUCCESS(f"-\tran successfully"))
			except Exception as e:
				error = str(e)
				self.stdout.write(self.style.ERROR(f"-\t trouble {stage} for {yard['name']}: {error}"))

				continue
			finally:
				self.log_scrape_event(junkyard_id=yard['id'], error=error, status=status)

				
	def cache_scraper_results(self, results, yard):
		""" 
			Upserts or deletes vehicles on Vehicle model 
		"""
		assert len(results) > 0
		vehicle_instances = []
		scraped_identifiers = [] # Ex: ['stk0192','stk1111']

		# Format results to django model instances (<Vehicle>) 
		for result in results:
			vehicle_instance = self.format_result(result, yard)
			scraped_identifiers.append(vehicle_instance.junkyard_identifier)
			vehicle_instances.append(vehicle_instance)
		self.upsert_vehicle_instances(vehicle_instances)
		self.handle_removed_results(scraped_identifiers, yard['id'])
	
	def format_result(self, result, yard):
		"""
		Turns any scraped result into a <Vehicle> instance
		"""
		try:
			# some result keys require more handling because junkyard inventory column headers differ
			return Vehicle(
       			junkyard_id=yard['id'],
          		year=result['year'],
            	make=result['make'],
            	model=result['model'],
             	available_date=extract_date(result, yard['date_format']), 
              	row=extract_row(result),
               	space=extract_space(result), 
                color=extract_color(result),
                junkyard_identifier=extract_junkyard_identifier(result),
                vin=extract_vin(result)
            )
		except ValueError as e:
			print(f"{e} appeared at this result: {result}")
			raise ValueError

	def upsert_vehicle_instances(self, vehicle_instances):
		# Upsert list of <Vehicle> instances
		Vehicle.objects.bulk_create(vehicle_instances, update_conflicts=True, unique_fields=['junkyard_identifier','junkyard'], update_fields=['year','make','model'])
		self.stdout.write(f"-\t{len(vehicle_instances)} upserted")

	def handle_removed_results(self, scraped_identifiers, junkyard_id):
		"""
			Removes vehicles from <Vehicle> model 
   			that have id of junkyard_id and are NOT in freshly scraped results 
		"""
		different_identifiers = Vehicle.objects.filter(Q(junkyard_id=junkyard_id) & ~Q(junkyard_identifier__in=scraped_identifiers) )
		if len(different_identifiers) > 0:
			self.stdout.write(f"\t{len(different_identifiers)} removed from site")
			different_identifiers.delete()
		
	def log_scrape_event(self, junkyard_id, status, error=""):
		Scrape.objects.create(junkyard_id=junkyard_id, error=error, status=status)
		