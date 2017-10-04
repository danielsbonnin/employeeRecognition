""" teamiota/forms.py """

from django import forms
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate
from django.db.models import Q
from teamiota.models import User, NormalUser, AwardEvent

class SignatureWidget(forms.widgets.ClearableFileInput):
    """ Add correct URLs to ClearableFileInput template """

    template_with_initial = (
        '%(initial_text)s: <a href="%(initial_url)s"><img src="%(initial_url)s"></a> '
        '%(clear_template)s<br />%(input_text)s: %(input)s'
    )

class NormalUserLoginForm(forms.Form):
    """ Login Form for Normal Users Portal """

    email = forms.EmailField(label='Email:', max_length=50)
    password = forms.CharField(
        label='Password:',
        max_length=50,
        widget=forms.PasswordInput)

    def get_user(self):
        """ Return valid User """

        this_user = User.objects.get(Q(email=self.email))
        username = this_user.get_username()
        return authenticate(username=username, password=self.password)

    def is_valid(self):
        """
        Override default form validation to check user email/pass
        @return None or User object
        """

        # src chriskief.com/2012/12/16/override-django-form-is-valid
        # run default form validation
        is_valid = super(NormalUserLoginForm, self).is_valid()

        # Basic input problems
        if not is_valid:
            return False

        self.email = self.cleaned_data['email']
        self.password = self.cleaned_data['password']

        # Retrieve User from db
        try:
            this_user = User.objects.get(
                Q(email=self.email)
            )

        # Email not in DB
        except User.DoesNotExist:
            self.add_error('email', 'User does not exist')
            return False

        # Password is incorrect for existing email
        if not check_password(self.password, this_user.password):
            self.add_error('password', 'Password is invalid')
            return False

        return True

class NormalUserEditForm(forms.ModelForm):
    """ Edit Form for Normal User """
    
    def __init__(self, *args, **kwargs):
        super(NormalUserEditForm, self).__init__(*args, **kwargs)
        self.fields['nickname'].required = True
    
    class Meta:
        """ Modify form to include only nickname and signatureImage """
        
        model = NormalUser
        fields = ['nickname', 'signatureImage']
        widgets = {
            'signatureImage': SignatureWidget()
        }

class NewAwardForm(forms.ModelForm):
    """ Form for creating a new award """

    def __init__(self, *args, **kwargs):
        super(NewAwardForm, self).__init__(*args, **kwargs)
        self.fields['awardee'].queryset = NormalUser.objects.filter(isAdmin=False)
        self.fields['awardee'].required = True
        self.fields['awardType'].required = True

    class Meta:
        """ Modify form to include only awarder, awardee, awardType and date """

        model = AwardEvent
        fields = ['awarder', 'awardee', 'awardType', 'dateOfAward']

        widgets = {
            'awarder': forms.HiddenInput(),
            'dateOfAward': forms.TextInput(attrs={'class': 'form-control'}),
        }
