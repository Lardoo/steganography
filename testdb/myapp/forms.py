# forms.py
# forms.py
from django import forms
from .models import Student
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from myapp.models import GraduationList



class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [ 'registration_number']


class CertificateValidationForm(forms.Form):
    certificate_image = forms.ImageField(
        label='Upload Certificate Image',

    )


class AcceptDeclineForm(forms.Form):
    action = forms.ChoiceField(
        choices=[('accept', 'Accept'), ('decline', 'Decline')],
        widget=forms.RadioSelect
    )


class EmployerRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2']


class CustomStudentRegistrationForm(UserCreationForm):
    registration_number = forms.CharField(max_length=20)

    class Meta:
        model = CustomUser  # Replace with your User model
        fields = ['username', 'email',
                  'registration_number', 'password1', 'password2']

    def clean_registration_number(self):
        registration_number = self.cleaned_data['registration_number']
        # Check if a Student with the provided registration number exists
        if not Student.objects.filter(registration_number=registration_number).exists():
            raise forms.ValidationError(
                "No student with this registration number exists.")
        return registration_number


class CustomUserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'password1', 'password2')


class StudentRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1',
                  'password2', 'registration_number', 'id_number']

    def __init__(self, *args, **kwargs):
        super(StudentRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['registration_number'].required = True
        self.fields['id_number'].required = True

    def save(self, commit=True):
        user = super(StudentRegistrationForm, self).save(commit=False)
        user.is_student = True  # Set the user as a student
        if commit:
            user.save()
        return user


class GraduationListForm(forms.ModelForm):
    class Meta:
        model = GraduationList
        fields = ['name', 'registration_number',
                  'id_number', 'course', 'year_of_completion']
        

        

