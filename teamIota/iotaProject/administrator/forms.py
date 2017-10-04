""" administrator/forms.py """

from django import forms
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.models import User
from teamiota.models import NormalUser, Award, Location, Department


class AddUserForm(forms.ModelForm):
    """ Form to enter a User's data """

    def __init__(self, *args, **kwargs):
        super(AddUserForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['location'].required = True
        self.fields['department'].required = True
        self.fields['first_name'].required = False
        self.fields['first_name'].help_text = '*optional'
        self.fields['last_name'].required = False
        self.fields['last_name'].help_text = '*optional'

    dept_choices = [(None, "-- Select a Department --")]
    loc_choices = [(None, "-- Select a Location --")]
    try:
        for department in Department.objects.all().order_by('name'):
            dept_choices.append((department.id, department.name))
        for location in Location.objects.all().order_by('name'):
            loc_choices.append((location.id, location.name))
    except:
        pass
    location = forms.ChoiceField(label='location', choices=loc_choices)
    department = forms.ChoiceField(label='department', choices=dept_choices)
    is_admin = forms.BooleanField(label='User is an Admin', required=False)

    class Meta:
        """ Restrict form to username, password, and email fields """

        model = User
        fields = ['username', 'password', 'email', 'first_name', 'last_name',]
        widgets = {
            'password': forms.PasswordInput(),
            }

    def is_valid(self):
        """ Override validation to enforce unique emails """

        is_valid = super(AddUserForm, self).is_valid()
        
        # Basic validation failed
        if not is_valid:
            return False

        this_email = self.cleaned_data['email']
        this_email_already_exists = False
        try:
            if User.objects.get(email=this_email):
                self.add_error('email', ('{0} is already in use. '
                    'Please choose another email. ').format(this_email))
                this_email_already_exists = True
        except User.DoesNotExist:
            pass

        # return False if email already exists 
        return not this_email_already_exists
        
class EditUserForm(forms.ModelForm):
    """ Edit a teamiota.models.NormalUser """

    def __init__(self, initial_location, initial_department, is_admin, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.fields['location'].required = True
        self.fields['location'].initial = initial_location
        self.fields['department'].required = True
        self.fields['department'].initial = initial_department
        self.fields['first_name'].required = False
        self.fields['first_name'].help_text = '*optional'
        self.fields['last_name'].required = False
        self.fields['last_name'].help_text = '*optional'
        self.fields['is_admin'].initial = is_admin

    dept_choices = [(None, "-- Select a Department --")]
    loc_choices = [(None, "-- Select a Location --")]
    try:
        for department in Department.objects.all().order_by('name'):
            dept_choices.append((department.id, department.name))
        for location in Location.objects.all().order_by('name'):
            loc_choices.append((location.id, location.name))
    except:
        pass
    location = forms.ChoiceField(label='location', choices=loc_choices)
    department = forms.ChoiceField(label='department', choices=dept_choices)
    is_admin = forms.BooleanField(label='User is an Admin', required=False)
    
    class Meta:
        """ Restrict form to exclude auth fields """

        model = User
        fields = ['username', 'first_name', 'last_name',]

class ReportFilterForm(forms.Form):
    """ Get user options for custom reports """

    # Initialize choice arrays for drop-down menus
    type_choices = [(0, "-- All --")]
    dept_choices = [(0, "-- All --")]
    loc_choices = [(0, "-- All --")]
    user_choices = [(0, "-- All --")]

    # Pull choices for drop-downs from model
    # Try/except block required to fix new database migration issue:
    # migrate attempts to run queries before database tables are created
    try:
        for award in Award.objects.all().order_by('awardType'):
            type_choices.append((award.id, award.awardType))

        for department in Department.objects.all().order_by('name'):
            dept_choices.append((department.id, department.name))

        for location in Location.objects.all().order_by('name'):
            loc_choices.append((location.id, location.name))

        for normal_user in NormalUser.objects.filter(isAdmin=False)\
            .order_by('nickname'):
            user_choices.append((normal_user.id, normal_user.nickname))
    except:
        pass

    # Form fields
    award_type = forms.ChoiceField(label='Award Type', choices=type_choices)
    from_user = forms.ChoiceField(label='User', choices=user_choices)
    from_dept = forms.ChoiceField(label='Department', choices=dept_choices)
    from_location = forms.ChoiceField(label='Location', choices=loc_choices)
    to_user = forms.ChoiceField(label='User', choices=user_choices)
    to_dept = forms.ChoiceField(label='Department', choices=dept_choices)
    to_location = forms.ChoiceField(label='Location', choices=loc_choices)
    from_date = forms.DateField(label='Awarded Between', required=False)
    to_date = forms.DateField(label='and', required=False)