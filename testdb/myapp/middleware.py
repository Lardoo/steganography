# middleware.py
from .models import AdministratorActivityLog
from django.utils import timezone


class AdminActivityLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.user.is_authenticated and request.user.is_superuser:
            administrator = request.user
            timestamp = timezone.now()
            path = request.path

            if request.user.last_login and request.user.last_login < timestamp:
                # Log administrator login
                AdministratorActivityLog.objects.create(
                    administrator=administrator,
                    activity=f"{administrator.username} logged in at {timestamp} from {request.META['REMOTE_ADDR']}"
                )

            if path.startswith('/register_student/') and request.method == 'POST':
                # Extract the student registration number from the POST data
                registration_number = request.POST.get('registration_number')
                if registration_number:
                    # Log student registration by administrator if registration_number is not None
                    AdministratorActivityLog.objects.create(
                        administrator=administrator,
                        activity=f"{administrator.username} registered student with registration number {registration_number} at {timestamp}"
                    )

            # Add more conditionals to log other admin actions as needed

        return response
