# urls.py
from django.urls import path
from . import views
from django.contrib.auth.views import LoginView, LogoutView
from django.conf.urls.static import static
from django.conf import settings


from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', views.index, name='index'),
    path('register_student/', views.register_student,
         name='register_student'),


    path('validate_certificate/', views.validate_certificate,
         name='validate_certificate'),

    path('admin/', admin.site.urls),  # This line includes the admin URLs
    path('registration_success/', views.registration_success,
         name='registration_success'),
   # path('login/', LoginView.as_view(template_name='login.html'), name='login'),

   path('logout/', views.custom_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    path('vc_login/', views.vc_login, name='vc_login'),
   
    path('pending_requests/', views.pending_requests, name='pending_requests'),
    path('employer_register/', views.employer_register, name='employer_register'),
    path('employer_login/', views.employer_login, name='employer_login'),
    path('employer_dashboard/', views.employer_dashboard,
         name='employer_dashboard'),
    path('student_register/', views.student_register, name='student_register'),
    path('student_login/', views.student_login, name='student_login'),
    path('student_dashboard/', views.student_dashboard, name='student_dashboard'),
    path('download_certificate/<int:student_id>/',
         views.download_certificate, name='download_certificate'),
   path('custom_logout/', views.custom_logout, name='custom_logout'),
    path('view_annual_report',views.view_annual_report, name='view_annual_report'),
    path('pending_registrar_approval', views.pending_registrar_approval, name='pending_registrar_approval'),
    path('registrar_login', views.registrar_login, name='registrar_login'),
    path('register_student_in_graduation_list', views.register_student_in_graduation_list, name='register_student_in_graduation_list'),
    path('registration_failed', views.registration_failed, name='registration_failed'),
    path('examination_login', views.examination_login, name='examination_login'),
   
    path('success_page', views.success_page, name='success_page'),
    path('otp_verification_examination/', views.otp_verification_examination, name='otp_verification_examination'),
    path('otp_verification_registrar/', views.otp_verification_registrar, name='otp_verification_registrar'),
    path('otp_verification_vc/', views.otp_verification_vc, name='otp_verification_vc'),
    path('otp_verification_student/', views.otp_verification_student, name='otp_verification_student'),
    path('otp_verification_dean/', views.otp_verification_dean, name='otp_verification_dean'),
    path('otp_verification_employer/', views.otp_verification_employer, name='otp_verification_employer'),
     path('dean_login/', views.dean_login, name='dean_login'),
     path('main/', views.main, name='main'),
     path('download_report_as_pdf/', views.download_report_as_pdf, name='download_report_as_pdf'),
    
]