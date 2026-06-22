from django.forms import ModelForm
from yardsearcher.models import (Review)

class ReviewForm(ModelForm):
    
    class Meta:
        model = Review
        fields = ("rating","email","feedback")

    