from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
import datetime
# Create your models here.
class Junkyard(models.Model):
    junkyard_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, blank=False)
    address = models.CharField(max_length=100, blank=False)
    city = models.CharField(max_length=50, blank=False)
    state = models.CharField(max_length=2, blank=False)
    zip_code = models.IntegerField(blank=False)
    website = models.URLField(blank=True, max_length=255)
    lat = models.FloatField(default=0.00, editable=False)
    long = models.FloatField(default=0.00, editable=False)
    created_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        #self.lat, self.long = self.get_latlong()
        super().save(**kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('_detail', kwargs={'pk': self.pk})
    
    
class Vehicle(models.Model):
    vehicle_id = models.AutoField(primary_key=True)
    junkyard = models.ForeignKey(Junkyard, related_name='vehicles', on_delete=models.CASCADE)
    junkyard_identifier = models.CharField(max_length=30, blank=False)
    year = models.IntegerField(blank=False)
    make = models.CharField(max_length=40, blank=False)
    model = models.CharField(max_length=40, blank=False)
    color = models.CharField(max_length=20, blank=True)
    row = models.IntegerField(blank=False)
    space = models.IntegerField(blank=True)
    vin = models.CharField(max_length=17, blank=True)
    available_date = models.DateField()
    created_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [models.UniqueConstraint(fields=['junkyard', 'junkyard_identifier'], name='unique_vehicle')]
        
    def get_duration(self)-> str:
        output = ""
        today = datetime.date.today()
        time_delta = self.available_date - today
        num_days = abs(time_delta.days)
        num_months = num_days // 30
        if num_days == 0:
            return "Today"
        
        if num_months > 0:     
            output = f"{num_months} months" if num_months > 1 else f"{num_months} month" 
        else:
            output = f"{num_days} days" if num_days > 1 else f"{num_days} day"
        return output + " ago"
    
    def __str__(self):
        return f'{self.year} {self.make} {self.model}'


class UserAllowedYard(models.Model):
    user = models.ForeignKey(User, related_name='allowed_yards', on_delete=models.CASCADE)
    junkyard = models.ForeignKey(Junkyard, related_name='allowed_yards', on_delete=models.CASCADE)
    
    def __str__(self):
        return f'{self.user} allowed {self.junkyard}'

class Scrape(models.Model):
    STATUSES = (
        ('1','SUCCESS'),
        ('0','FAILED'),
    )
    junkyard = models.ForeignKey(Junkyard, related_name='scrapes', on_delete=models.CASCADE)
    status = models.CharField(max_length=1, choices=STATUSES, editable=False)
    error = models.TextField(blank=True)
    scraped_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f'[{"SUCCESS" if self.status == "1" else "FAILED"}] {self.junkyard.name} at {self.scraped_at}'

class Review(models.Model):
    email = models.EmailField(max_length=100)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now=True)
    rating = models.FloatField(
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(5.0),
        ]
    )
    
    def __str__(self):
        return f'{self.email.split("@")[0]} gave us {self.rating}/5 on {self.created_at}'
