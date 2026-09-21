from datetime import datetime

def extract_row(result):
	"""
	Returns the 'Row' value from a junkyard scraper's results attr
	"""

	row = 0
	try:
		# Junkyards may name the 'row' attrtibute differently
		if 'row' in result.keys() and len(result['row']) > 0:
			row = int(result['row'])  # Pyp, Pnp
		elif 'vehicle row' in result.keys() and len(result['vehicle row']) > 0:
			row = int(result['vehicle row']) # Jup
	except ValueError:
		# Chicago South junkyard had a vehicle with 'A' for a row value
		row = 0
	finally:
		return row

def extract_junkyard_identifier(result):
	junkyard_identifier = ""
	if 'stock#' in result.keys():
		junkyard_identifier = result['stock#']
	elif 'stock #' in result.keys():
		junkyard_identifier = result['stock #']
	elif 'barCodeNumber' in result.keys():
		junkyard_identifier = result['barCodeNumber'] # Pnp
	return str(junkyard_identifier).strip()

def extract_color(result):
	color = ""
	if 'color' in result.keys():
		color = result['color']
	return color

def extract_space(result):
	space = result.get('space', '')
	try:
		return int(space) if space not in ('', None) else 0
	except (TypeError, ValueError):
		return 0

def extract_date(result, date_format):
	date = ''
	if 'date set in yard' in result.keys():
		date = result['date set in yard']
	elif 'available' in result.keys():
		date = result['available'] 
	elif 'dateAdded' in result.keys():
		date = result['dateAdded']
	return datetime.strptime(date, date_format)

def extract_vin(result):
	vin = str(result.get('vin', '') or '').strip()
	if len(vin) > 17:
		return ""
	return vin
