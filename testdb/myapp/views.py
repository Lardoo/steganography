from django.shortcuts import render, redirect
from .forms import StudentForm, CertificateValidationForm
from .models import Certificate, Student
from PIL import Image, ImageDraw, ImageFont
import os
from stegano import lsb
import random
import string
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login
from .models import RegistrationRequest
from django.contrib.auth import authenticate
from .models import UserProfile
from django.core.files.base import ContentFile
import io
from .forms import AcceptDeclineForm
from myapp.models import AdministratorActivityLog
from io import BytesIO
from django.core.files import File
from django.core.files.uploadedfile import InMemoryUploadedFile
from .forms import EmployerRegistrationForm
from .models import Employer
from .forms import StudentRegistrationForm
from .forms import CustomUserRegistrationForm
from myapp.models import CustomUser
from django.http import HttpResponseForbidden
from django.http import Http404
from django.http import FileResponse

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from myapp.models import Student,AnnualReport
from myapp.models import FakeCertificate
from datetime import datetime
import requests
from django.conf import settings
from myapp.models import  Student, GraduationList
from .forms import GraduationListForm
from django.core.mail import send_mail


#@login_required
def pending_requests(request):
    # For VC approval
    # Check if the user is an administrator with the ability to approve the second stage
  #  if not request.user.is_authenticated or not request.user.is_vc:
     #   return redirect('vc_login')

    # Filter students pending VC approval
    pending_requests = Student.objects.filter(certificate_status='pending', second_admin_approval=True)

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')

        if action == 'accept':
            student = get_object_or_404(Student, id=student_id)
            if student.certificate_status != 'accepted':
                student.certificate_status = 'accepted'

                # Generate a random 8-digit uppercase string
                random_string = ''.join(random.choice(string.ascii_uppercase) for _ in range(8))

                # Create a certificate for the student with the encoded text
                generate_certificate_image(student, random_string)

                student.save()
        elif action == 'decline':
            student = get_object_or_404(Student, id=student_id)
            student.certificate_status = 'declined'
            student.save()

    return render(request, 'pending_requests.html', {'pending_requests': pending_requests})


def vc_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_vc:  # Assuming is_registrar is a boolean field on the User model
                    # Generate OTP and send via email
                otp = generate_otp()
                send_otp_email(user.email, otp)
                # Store the OTP in the user's session for verification
                request.session['otp'] = otp
                request.session['user_id'] = user.id
                return redirect('otp_verification_vc')  # Redirect to OTP verification page 
            else:
                # Invalid credentials or not a registrar
                return render(request, 'vc_login.html', {'form': form, 'error': 'Invalid login credentials for Vice Chancellor.'})
    else:
        form = AuthenticationForm()
    return render(request, 'vc_login.html', {'form': form})


def otp_verification_vc(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp:
           stored_otp = request.session.get('otp')
           user_id = request.session.get('user_id')
        if entered_otp == stored_otp and user_id:
            # Match the entered OTP with the stored OTP
            user = CustomUser.objects.get(pk=user_id)
            login(request, user)
            del request.session['otp']
            del request.session['user_id']
            return redirect('pending_requests')  # Redirect to the dashboard after successful login
        else:
            error_message = 'Invalid OTP. Please try again.'
            return render(request, 'otp_verification.html', {'error': error_message})
    return render(request, 'otp_verification.html', {})







def index(request):
    return render(request, 'home_page.html')


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')


def generate_certificate_image(student, encoded_text):
    if student.certificate_status != 'accepted':
        return None

    # Load the certificate border image
    border_path = '/home/anonymous/django-postgres/testdb/media/cert.png'  # Replace with your border image path
    border_image = Image.open(border_path).convert("RGBA")

    # Load the university logo image
    logo_path = '/home/anonymous/django-postgres/testdb/media/must-logo.png'  # Replace with your university logo path
    logo_image = Image.open(logo_path).convert("RGBA")

    # Calculate center positions for the logo and text
    logo_position = ((border_image.width - logo_image.width) // 2, 20)
    text_start_position = (100, 150)  # Adjust as needed

    # Create a drawing context on the border image
    draw = ImageDraw.Draw(border_image)

    # Paste the university logo onto the certificate border image
    border_image.paste(logo_image, logo_position, logo_image)

    # Load a professional-looking font (replace with your font file path)
    font_path = '/home/anonymous/django-postgres/testdb/39335_UniversCondensed.ttf'  # Replace with your font file path
    font_size = 24
    font = ImageFont.truetype(font_path, font_size)

    # Calculate center position for the text
    text_width, text_height = draw.textsize("Name: Example Student", font=font)
    text_position = ((border_image.width - text_width) // 2, text_start_position[1])

    # Draw the student details on the certificate border image
    draw.text(text_position, f"Name: {student.name}", fill='black', font=font)
    draw.text((text_position[0], text_position[1] + 50), f"Registration Number: {student.registration_number}", fill='black', font=font)
    draw.text((text_position[0], text_position[1] + 100), f"ID Number: {student.id_number}", fill='black', font=font)
    draw.text((text_position[0], text_position[1] + 150), f"Course: {student.course}", fill='black', font=font)
    draw.text((text_position[0], text_position[1] + 200), f"Year of Completion: {student.year_of_completion}", fill='black', font=font)

    # Embed the encoded text into the certificate border image
    encoded_image = lsb.hide(border_image, encoded_text)

    # Convert the PIL Image to bytes
    img_byte_array = BytesIO()
    encoded_image.save(img_byte_array, format='PNG')
    img_byte_array = img_byte_array.getvalue()

    # Save the certificate image to the Certificate model
    certificate = Certificate(student=student, encoded_string=encoded_text)
    certificate.certificate_image.save(f'certificates/{student.name}.png', ContentFile(img_byte_array))
    certificate.save()

    # Update the AnnualReport model for generated certificates
    annual_report, created = AnnualReport.objects.get_or_create(year=certificate.created_at.year)
    annual_report.generated_certificates_count += 1
    annual_report.save()


@login_required
def register_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)
            registration_number = form.cleaned_data['registration_number']
            
            # Check if student details exist in GraduationList
            graduation_list_exists = GraduationList.objects.filter(registration_number=student.registration_number).exists()

            if not graduation_list_exists:
                # Student details not found in GraduationList, prevent registration
                messages.error(request, 'Student details not found in the graduation list.')
                return redirect('registration_failed')  # Redirect to the registration failed view

            # Associate the student with the current user (administrator)
            graduation_student = get_object_or_404(GraduationList, registration_number=registration_number)
         
            student = Student(
                name=graduation_student.name,
                registration_number=graduation_student.registration_number,
                id_number=graduation_student.id_number,
                course=graduation_student.course,
                year_of_completion=graduation_student.year_of_completion,

                # Add other fields accordingly
            )
           
            student.user = request.user
            student.certificate_status = 'pending'  # Initial status is pending

            # Save the student and log the activity
            student.save()
           # log_activity(request.user, f"Registered student: {student.registration_number}")

            # Redirect to the pending second approval for registrar's approval
            return redirect('registration_success')  # Create this view

    else:
        form = StudentForm()

    return render(request, 'register_student.html', {'form': form})

# Define the log_activity function to log administrator activities


def log_activity(administrator, activity):
    AdministratorActivityLog.objects.create(
        administrator=administrator, activity=activity)



#@login_required
def validate_certificate(request):
    if request.method == 'POST':
        form = CertificateValidationForm(request.POST, request.FILES)
        if form.is_valid():
            certificate_image = form.cleaned_data['certificate_image']
            try:
                certificate_image_data = certificate_image.read()
                hidden_text = lsb.reveal(certificate_image)
            except Exception as e:
                hidden_text = None

            if hidden_text:
                certificate = Certificate.objects.filter(encoded_string=hidden_text).first()
                if certificate:
                    student = Student.objects.get(id=certificate.student.id)
                    # Ensure the student's certificate status is 'accepted'
                    student.certificate_status = 'accepted'
                    student.save()
                    
                    # Get the current year
                    current_year = datetime.now().year
                    
                    # Update the AnnualReport model for valid certificates
                    annual_report, created = AnnualReport.objects.get_or_create(year=current_year)
                    annual_report.certificate_count += 1
                    annual_report.valid_certificates_count += 1
                    annual_report.save()
                    
                    return render(request, 'certificate_valid.html', {'certificate': hidden_text, 'student': student})
                else:
                    # Certificate is invalid
                    # Update the AnnualReport model for invalid certificates
                    current_year = datetime.now().year
                    annual_report, created = AnnualReport.objects.get_or_create(year=current_year)
                    annual_report.certificate_count += 1
                    annual_report.invalid_certificates_count += 1
                    annual_report.save()
                    
                    fake_certificate = FakeCertificate()
                    certificate_data = BytesIO(certificate_image_data)
                    fake_certificate.certificate_image = InMemoryUploadedFile(
                        certificate_data, None, 'temp.png', 'image/png', len(certificate_image_data), None)
                    fake_certificate.save()
                    return render(request, 'certificate_invalid.html')
            else:
                # No hidden text found in the image
                # Update the AnnualReport model for invalid certificates
                current_year = datetime.now().year
                annual_report, created = AnnualReport.objects.get_or_create(year=current_year)
                annual_report.certificate_count += 1
                annual_report.invalid_certificates_count += 1
                annual_report.save()
                
                fake_certificate = FakeCertificate()
                certificate_data = BytesIO(certificate_image_data)
                fake_certificate.certificate_image = InMemoryUploadedFile(
                    certificate_data, None, 'fake.png', 'image/png', len(certificate_image_data), None)
                fake_certificate.save()
                return render(request, 'no_hidden_text.html')
    else:
        form = CertificateValidationForm()
    return render(request, 'validate_certificate.html', {'form': form})

def registration_success(request):
    return render(request, 'registration_success.html')


def custom_logout(request):
    logout(request)
    return redirect('index')


def employer_register(request):
    if request.method == 'POST':
        form = EmployerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request, 'Registration successful.')
            # Redirect to the employer login
            return redirect('employer_login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")

    else:
        form = EmployerRegistrationForm()

    return render(request, 'employer_register.html', {'form': form})


def employer_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None :  # Assuming is_registrar is a boolean field on the User model
                    # Generate OTP and send via email
                otp = generate_otp()
                send_otp_email(user.email, otp)
                # Store the OTP in the user's session for verification
                request.session['otp'] = otp
                request.session['user_id'] = user.id
                return redirect('otp_verification_employer')  # Redirect to OTP verification page 
            else:
                # Invalid credentials or not a registrar
                return render(request, 'employer_login.html', {'form': form, 'error': 'Invalid login credentials for employer.'})
    else:
        form = AuthenticationForm()
    return render(request, 'employer_login.html', {'form': form})


def otp_verification_employer(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp:
           stored_otp = request.session.get('otp')
           user_id = request.session.get('user_id')
        if entered_otp == stored_otp and user_id:
            # Match the entered OTP with the stored OTP
            user = CustomUser.objects.get(pk=user_id)
            login(request, user)
            del request.session['otp']
            del request.session['user_id']
            return redirect('employer_dashboard')  # Redirect to the dashboard after successful login
        else:
            error_message = 'Invalid OTP. Please try again.'
            return render(request, 'otp_verification.html', {'error': error_message})
    return render(request, 'otp_verification.html', {})





@login_required
def employer_dashboard(request):
    user = request.user
    employer = user.employer
    return render(request, 'employer_dashboard.html', {'employer': employer})


def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            registration_number = form.cleaned_data['registration_number']
            id_number = form.cleaned_data['id_number']

            # Check if the student with the provided registration number and id number exists
            try:
                student = Student.objects.get(
                    registration_number=registration_number, id_number=id_number)
                user = form.save()
                try:
                    # Check if a certificate exists for the student
                    certificate = Certificate.objects.get(student=student)

                    # Provide a download link for the certificate
                    #return render(request, 'student_dashboard.html', {'student': student, 'certificate': certificate})
                    return  redirect('student_login')
                except Certificate.DoesNotExist:
                    # Certificate is pending
                    return render(request, 'certificate_pending.html', {'student': student})

            except Student.DoesNotExist:
                # Student details do not exist
                return render(request, 'error.html', {'error_message': "You are not authorized to have an account in this application."})

    else:
        form = StudentRegistrationForm()

    return render(request, 'student_register.html', {'form': form})


def student_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_student:  # Assuming is_student is a boolean field on the User model
                    # Generate OTP and send via email
                otp = generate_otp()
                send_otp_email(user.email, otp)
                # Store the OTP in the user's session for verification
                request.session['otp'] = otp
                request.session['user_id'] = user.id
                return redirect('otp_verification_student')  # Redirect to OTP verification page 
            else:
                # Invalid credentials or not a student
                return render(request, 'student_login.html', {'form': form, 'error': 'Invalid login credentials for student.'})
    else:
        form = AuthenticationForm()
    return render(request, 'student_login.html', {'form': form})


def otp_verification_student(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp:
           stored_otp = request.session.get('otp')
           user_id = request.session.get('user_id')
        if entered_otp == stored_otp and user_id:
            # Match the entered OTP with the stored OTP
            user = CustomUser.objects.get(pk=user_id)
            login(request, user)
            del request.session['otp']
            del request.session['user_id']
            return redirect('student_dashboard')  # Redirect to the dashboard after successful login
        else:
            error_message = 'Invalid OTP. Please try again.'
            return render(request, 'otp_verification.html', {'error': error_message})
    return render(request, 'otp_verification.html', {})



@login_required
def student_dashboard(request):
    user = request.user

    # Check if the user is a student
    if user.is_student:
        try:
            student = Student.objects.get(
                registration_number=user.registration_number, id_number=user.id_number)

            return render(request, 'student_dashboard.html', {'student': student})
        except Student.DoesNotExist:
            return render(request, 'error.html', {'error_message': "You are not authorized to access this page."})

    return render(request, 'error.html', {'error_message': "You are not authorized to access this page."})

@login_required
def download_certificate(request, student_id):
    student = get_object_or_404(Student, id=student_id)

    try:
        certificate = Certificate.objects.get(student=student)
    except Certificate.DoesNotExist:
        raise Http404("Certificate not found.")

    certificate_file = certificate.certificate_image.path
    certificate_filename = f"{student.name}.png"

    # Serve the certificate file for download
    response = FileResponse(open(certificate_file, 'rb'),
                            content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="{certificate_filename}"'

    return response

def update_annual_report(year):
    annual_report, created = AnnualReport.objects.get_or_create(year=year)
    annual_report.certificate_count = Certificate.objects.filter(
        created_at__year=year).count()
    annual_report.valid_certificates_count = Certificate.objects.filter(
        student__certificate_status='accepted',
        certificate_image__isnull=False,
        created_at__year=year
    ).count()
    annual_report.invalid_certificates_count = Certificate.objects.filter(
        student__certificate_status='declined',
        certificate_image__isnull=False,
        created_at__year=year
    ).count()
    annual_report.save()
    
@login_required
def view_annual_report(request):
    if request.method == 'POST':
        if not request.user.is_authenticated or not request.user.is_superuser:
          return redirect('login')
        # Get the selected year from the form
        selected_year = int(request.POST.get('selected_year'))
        annual_report = AnnualReport.objects.filter(year=selected_year).first()
        if annual_report:
            return render(request, 'annual_report.html', {'annual_report': annual_report})
        else:
            # Handle the case when the report for the selected year does not exist
            return render(request, 'annual_report_not_found.html')

    return render(request, 'annual_report_form.html')


def registration_failed(request):
    return render(request, 'not_in_list.html')



#@login_required
def pending_registrar_approval(request):
    # Check if the user is a registrar
   # if not request.user.is_authenticated or not request.user.is_registrar:
    #    return redirect('registrar_login')  # Redirect to the login page or access denied page
    
    # Filter students pending registrar's approval
    pending_registrar_approval_requests = Student.objects.filter(certificate_status='pending', second_admin_approval=False)

    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')

        if action == 'approve':
            student = get_object_or_404(Student, id=student_id)
            student.second_admin_approval = True
            student.save()

            # Log the registrar's approval activity
            log_activity(request.user, f"Registrar approved certificate for: {student.name}")

        elif action == 'decline':
            student = get_object_or_404(Student, id=student_id)
            student.certificate_status = 'declined'
            student.save()

            # Log the registrar's decline activity
            log_activity(request.user, f"Registrar declined certificate for: {student.name}")

    return render(request, 'pending_registrar_approval.html', {'pending_requests': pending_registrar_approval_requests})


def registrar_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_registrar:  # Assuming is_registrar is a boolean field on the User model
                    # Generate OTP and send via email
                otp = generate_otp()
                send_otp_email(user.email, otp)
                # Store the OTP in the user's session for verification
                request.session['otp'] = otp
                request.session['user_id'] = user.id
                return redirect('otp_verification_registrar')  # Redirect to OTP verification page 
            else:
                # Invalid credentials or not a registrar
                return render(request, 'registrar_login.html', {'form': form, 'error': 'Invalid login credentials for registrar.'})
    else:
        form = AuthenticationForm()
    return render(request, 'registrar_login.html', {'form': form})


def otp_verification_registrar(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp:
           stored_otp = request.session.get('otp')
           user_id = request.session.get('user_id')
        if entered_otp == stored_otp and user_id:
            # Match the entered OTP with the stored OTP
            user = CustomUser.objects.get(pk=user_id)
            login(request, user)
            del request.session['otp']
            del request.session['user_id']
            return redirect('pending_registrar_approval')  # Redirect to the dashboard after successful login
        else:
            error_message = 'Invalid OTP. Please try again.'
            return render(request, 'otp_verification.html', {'error': error_message})
    return render(request, 'otp_verification.html', {})




@login_required
def register_student_in_graduation_list(request):
     # Check if the user is a examiner
    if not request.user.is_authenticated or not request.user.is_examiner:
        return redirect('examination_login')  # Redirect to the login page or access denied page
    if request.method == 'POST':
        form = GraduationListForm(request.POST)
        if form.is_valid():
            form.save()
            # Optionally, add success messages or other redirects
            return redirect('success_page')  # Replace 'success_page' with your success URL
    else:
        form = GraduationListForm()

    return render(request, 'graduation_list_form.html', {'form': form})


def success_page(request):
    return render(request, 'success_message.html')


#def examination_login(request):
   # if request.method == 'POST':
     #   form = AuthenticationForm(data=request.POST)
     #   if form.is_valid():
      #      username = form.cleaned_data.get('username')
      #      password = form.cleaned_data.get('password')
       #     user = authenticate(username=username, password=password)
       #     if user is not None and user.is_examiner:  # Assuming is_examiner is a boolean field on the User model
       #         login(request, user)
      #          return redirect('register_student_in_graduation_list')  
       #     else:
                # Invalid credentials or not a examiner
                
     #           return render(request, 'examiner_login.html', {'form': form, 'error': 'Invalid login credentials for examination officer.'})
  #  else:
    #    form = AuthenticationForm()
  #  return render(request, 'examiner_login.html', {'form': form})




# Function to generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Function to send OTP via email
def send_otp_email(email, otp):
    subject = 'Login OTP'
    message = f"Your OTP is: {otp}"
    from_email = 'autoreply@litwebtech.com'  # Your email
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

# Login view with OTP generation and email sending
def examination_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_examiner:
                # Generate OTP and send via email
                otp = generate_otp()
                send_otp_email(user.email, otp)
                # Store the OTP in the user's session for verification
                request.session['otp'] = otp
                request.session['user_id'] = user.id
                return redirect('otp_verification_examination')  # Redirect to OTP verification page
            else:
                error_message = 'Invalid login credentials.'
        else:
            error_message = 'Invalid login credentials.'
        return render(request, 'examiner_login.html', {'form': form, 'error': error_message})
    else:
        form = AuthenticationForm()
    return render(request, 'examiner_login.html', {'form': form})

# OTP verification view
def otp_verification_examination(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp:
           stored_otp = request.session.get('otp')
           user_id = request.session.get('user_id')
        if entered_otp == stored_otp and user_id:
            # Match the entered OTP with the stored OTP
            user = CustomUser.objects.get(pk=user_id)
            login(request, user)
            del request.session['otp']
            del request.session['user_id']
            return redirect('register_student_in_graduation_list')  # Redirect to the dashboard after successful login
        else:
            error_message = 'Invalid OTP. Please try again.'
            return render(request, 'otp_verification.html', {'error': error_message})
    return render(request, 'otp_verification.html', {})


 #Login view with OTP generation and email sending for administrator/Dean
def dean_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.is_superuser:
                # Generate OTP and send via email
                otp = generate_otp()
                send_otp_email(user.email, otp)
                # Store the OTP in the user's session for verification
                request.session['otp'] = otp
                request.session['user_id'] = user.id
                return redirect('otp_verification_dean')  # Redirect to OTP verification page
            else:
                error_message = 'Invalid login credentials.'
        else:
            error_message = 'Invalid login credentials.'
        return render(request, 'dean_login.html', {'form': form, 'error': error_message})
    else:
        form = AuthenticationForm()
    return render(request, 'dean_login.html', {'form': form})

# OTP verification view

def otp_verification_dean(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        if entered_otp:
           stored_otp = request.session.get('otp')
           user_id = request.session.get('user_id')
        if entered_otp == stored_otp and user_id:
            # Match the entered OTP with the stored OTP
            user = CustomUser.objects.get(pk=user_id)
            login(request, user)
            del request.session['otp']
            del request.session['user_id']
            return redirect('dashboard')  # Redirect to the dashboard after successful login
        else:
            error_message = 'Invalid OTP. Please try again.'
            return render(request, 'otp_verification.html', {'error': error_message})
    return render(request, 'otp_verification.html', {})


def main(request):
    return render(request , 'main_dashboard.html')



@login_required
def download_report_as_pdf(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('/login')

    # Fetch data from the AnnualReport model
    annual_reports = AnnualReport.objects.all()

    # Create a PDF buffer
    buffer = io.BytesIO()

    # Create a PDF object
    pdf = canvas.Canvas(buffer, pagesize=letter)

    # Set starting position for content
    y_position = 750

    # Write report data to PDF
    pdf.drawString(100, y_position, "Annual Report Data")
    y_position -= 20  # Adjust vertical position for next line

    for report in annual_reports:
        pdf.drawString(100, y_position, f"Year: {report.year}")
        y_position -= 20  # Adjust vertical position for next line

        pdf.drawString(100, y_position, f"Generated Certificates: {report.generated_certificates_count}")
        y_position -= 20  # Adjust vertical position for next line

        pdf.drawString(100, y_position, f"Valid Certificates: {report.valid_certificates_count}")
        y_position -= 20  # Adjust vertical position for next line

        pdf.drawString(100, y_position, f"Invalid Certificates: {report.invalid_certificates_count}")
        y_position -= 30  # Adjust vertical position for next section

    # Save the PDF content
    pdf.save()

    # Set up response
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="annual_report.pdf"'

    return response