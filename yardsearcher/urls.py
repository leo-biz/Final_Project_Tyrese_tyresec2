"""
URL configuration for scraphounds project.

"""
from django.contrib import admin
from django.urls import path, include
from yardsearcher.views import (
    results_view,
    ReviewView,
)

urlpatterns = [
    path('results/', results_view, name="results_urlpattern"),
    path('review/add', ReviewView.as_view() , name="add_review_urlpattern"),
]
