from django.contrib.auth.models import AbstractUser
from django.db import models

class Ward(models.Model):
    ward_number = models.PositiveIntegerField(unique=True)
    ward_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Ward {self.ward_number} - {self.ward_name}"

class User(AbstractUser):
    ROLE_CHOICES = (
        ('citizen', 'Citizen'),
        ('ward_member', 'Ward Member'),
        ('field_worker', 'Field Worker'),
        ('panchayath_admin', 'Panchayath Admin'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='citizen')
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True)
    ward = models.ForeignKey(Ward, on_delete=models.SET_NULL, null=True, blank=True)
    address = models.TextField(blank=True, null=True)
    
    # Location for smart assignment (Field Workers)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    # Helper methods for your custom admin panel logic
    def is_ward_member(self):
        return self.role == 'ward_member'

    def is_field_worker(self):
        return self.role == 'field_worker'

    def is_panchayath_admin(self):
        return self.role == 'panchayath_admin'

class CitizenProfile(models.Model):
    GENDER_CHOICES = (('M', 'Male'), ('F', 'Female'), ('O', 'Other'))
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    occupation = models.CharField(max_length=100, null=True, blank=True)
    annual_income = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    aadhaar_number = models.CharField(max_length=12, unique=True, null=True, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"