from django.core.management.base import BaseCommand
from yardsearcher.models import Junkyard
from datetime import datetime
from yardsearcher.utils.known_yards import KNOWN_YARDS as KNOWN_YARDS

class Command(BaseCommand):
	help = "Updates/creates junkyards in db"

	def handle(self, *args, **options):
		""" 
			Seed known junkyards
		"""
		for yard in KNOWN_YARDS:
			self.register_yard(yard)
		

	def register_yard(self, yard):
		junkyard, registered = Junkyard.objects.update_or_create(
			address=yard['address'],
			defaults={
				'name': yard['name'],
				'city': yard['city'],
				'state': yard['state'],
				'lat': yard['lat'],
				'long': yard['long'],
				'zip_code': yard['zip_code'],
			},
		)
		print(f"\nRegistered {yard['name']}")
