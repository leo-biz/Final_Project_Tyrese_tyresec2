from django.shortcuts import render

from yardsearcher.models import Junkyard, Scrape, Vehicle

def root_view(request):
    latest_scrape = Scrape.objects.order_by("-scraped_at").first()
    context = {
        "total_yards": Junkyard.objects.count(),
        "total_vehicles": Vehicle.objects.count(),
        "latest_scrape": latest_scrape,
    }
    return render(request, "yardsearcher/home.html", context)
