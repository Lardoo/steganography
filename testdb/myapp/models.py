# models.py

from django.db import models
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from datetime import datetime


class CustomUser(AbstractUser):
    is_registrar = models.BooleanField(default=False)  # New field indicating registrar status
    is_vc = models.BooleanField(default=False)
    is_examiner = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    employer = models.ForeignKey(
        'Employer', on_delete=models.CASCADE, null=True, blank=True, related_name='custom_users')
    email = models.EmailField(unique=True)
    registration_number = models.CharField(
        max_length=20, unique=True, blank=True, null=True)
    id_number = models.CharField(
        max_length=15, unique=True, blank=True, null=True)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        if self.is_student:
            if not self.id_number:
                raise ValueError("Students must provide an id_number.")
        super().save(*args, **kwargs)

    @classmethod
    def create_student(cls, username, registration_number, id_number, password=None, **extra_fields):
        extra_fields.setdefault('is_vc', False)
        extra_fields.setdefault('employer', None)
        extra_fields.setdefault('registration_number', registration_number)
        user = cls(username=username, id_number=id_number, **extra_fields)
        user.set_password(password)
        user.save()
        return user


class Student(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='students')
    name = models.CharField(max_length=100)
    second_admin_approval = models.BooleanField(default=False)  # New field for second admin approval
    registration_number = models.CharField(max_length=20, unique=True)
    id_number = models.CharField(max_length=15, unique=True)
    course = models.CharField(max_length=100)
    year_of_completion = models.IntegerField(
        default=2022, null=True, blank=True)
    CERTIFICATE_STATUSES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    )
    certificate_status = models.CharField(
        max_length=10, choices=CERTIFICATE_STATUSES, default='pending'
    )
    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, related_name='administered_students')


class Certificate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    # Adjust the max length as needed
    encoded_string = models.CharField(max_length=10, unique=True)

    certificate_image = models.ImageField(upload_to='certificates/')
    created_at = models.DateTimeField(default=datetime.now)


class AdministratorActivityLog(models.Model):
    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class RegistrationRequest(models.Model):
    # Define your model fields here
    student = models.ForeignKey('myapp.Student', on_delete=models.CASCADE)

    status = models.CharField(max_length=10)


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    is_vc = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    # You can add more fields relevant to the employer here


class Employer(models.Model):
    employer = models.ForeignKey(
        'Employer', on_delete=models.CASCADE, null=True, blank=True, related_name='employers')
    company_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, default=None)


class FakeCertificate(models.Model):
    certificate_image = models.ImageField(upload_to='fake_certificates/')

class AnnualReport(models.Model):
    year = models.IntegerField(unique=True)
    certificate_count = models.PositiveIntegerField(default=0)
    valid_certificates_count = models.PositiveIntegerField(default=0)
    invalid_certificates_count = models.PositiveIntegerField(default=0)
    generated_certificates_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return str(self.year)

    # Create a method to update the report based on certificate creation and validation
    def update_report(self):
        self.certificate_count = Certificate.objects.filter(created_at__year=self.year).count()
        self.valid_certificates_count = Certificate.objects.filter(
            student__certificate_status='accepted',
            certificate_image__isnull=False,
            created_at__year=self.year
        ).count()
        self.invalid_certificates_count = self.certificate_count - self.valid_certificates_count
        self.save()


class GraduationList(models.Model):
     name = models.CharField(max_length=100)
     registration_number = models.CharField(max_length=20, unique=True)
     id_number = models.CharField(max_length=15, unique=True)
     course = models.CharField(max_length=100)
     year_of_completion = models.IntegerField(
        default=2022, null=True, blank=True)
     



    

