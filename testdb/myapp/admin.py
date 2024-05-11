from .models import UserProfile
from .models import Student
from django.contrib import admin

# Register your models here.
from .models import Certificate

admin.site.register(Certificate)

# admin.py

admin.site.register(Student)

# admin.py
admin.site.register(UserProfile)
