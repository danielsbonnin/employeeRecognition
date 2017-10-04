""" administrator/views.py """

from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.utils import timezone
from teamiota.models import NormalUser
from .reports import Report
from .forms import *
from django.contrib.auth.decorators import user_passes_test


@login_required()
@user_passes_test(lambda u: u.normaluser.isAdmin)
def admin_account(request):
    """ The main Administrator Page """

    return render(request, 'admin_account.html')

@login_required()
@user_passes_test(lambda u: u.normaluser.isAdmin)
def edit(request):
    """ Process email address input from edit.html """

    email = request.POST.get('email', None)

    if email is None:
        return render(request, 'edit.html')
    else:
        try:
            user = User.objects.get(email=email)
            return HttpResponseRedirect(
                '/administrator/edit_user/{0}'.format(user.id))
        except:
            return render(request, 'edit.html', {'noemail': True})

@login_required()
@user_passes_test(lambda u: u.normaluser.isAdmin)
def edit_user(request, user_id):
    """ Handle the submission of the Edit User form """

    user = User.objects.get(id=user_id)
    normal_user = NormalUser.objects.get(user=user)
    user = normal_user.user
    initial_department = normal_user.department.id
    initial_location = normal_user.location.id
    is_admin = normal_user.isAdmin
    if request.method == "POST":
        edit_user_form = EditUserForm(initial_location, initial_department, 
            is_admin, request.POST, instance=user, prefix='user')
        if edit_user_form.is_valid():
            edit_user_form.save()
            new_department = Department.objects\
                .get(pk=edit_user_form.cleaned_data['department'])
            normal_user.department = new_department
            new_location = Location.objects\
                .get(pk=edit_user_form.cleaned_data['location'])
            is_admin = edit_user_form.cleaned_data['is_admin']
            normal_user.isAdmin = is_admin
            normal_user.location = new_location
            normal_user.save()
            return HttpResponseRedirect('/administrator')
    else:
        edit_user_form = EditUserForm(initial_location, initial_department, 
            is_admin, instance=user, prefix='user')

        return render(request, 'edit_user.html',
            {
              'user_to_edit': normal_user,
              'edit_user_form': edit_user_form,
            })

@login_required()
@user_passes_test(lambda u: u.normaluser.isAdmin)
def list(request):
    """ Page with a table of Users """

    users = NormalUser.objects.all()
    return render(request, 'list.html', {'users':users})

@login_required()
@user_passes_test(lambda u: u.normaluser.isAdmin)
def add_user(request):
    """ Add User Page """

    new_normal_user = None
    if request.method == 'POST':  # Admin User submitted Add User Form
    
        # Get input for both the Base User and NormalUser
        add_user_form = AddUserForm(request.POST, prefix='user')

        if add_user_form.is_valid():
        
            # pylint: disable=line-too-long
            # src for last_login: http://stackoverflow.com/questions/33075399/automatically-generating-last-login-and-date-joined-values-for-authuser
            
            # Create a django.auth.User from validated form
            username, email, password = (
                add_user_form.cleaned_data['username'],
                add_user_form.cleaned_data['email'],
                add_user_form.cleaned_data['password'])
       
            new_user = User.objects.create_user(username=username,
                email=email, password=password)
            
            new_user.last_name = add_user_form.cleaned_data['last_name']
            new_user.first_name = add_user_form.cleaned_data['first_name']
            
            # Set last_login
            new_user.last_login = timezone.now()
            new_user.save()
            
            # Modify the associated teamiota.models.NormalUser
            new_normal_user = NormalUser.objects.get(user=new_user)
            new_normal_user.isAdmin = add_user_form.cleaned_data['is_admin']
            new_normal_user.department = Department.objects.get(
                pk=add_user_form.cleaned_data['department'])
            new_normal_user.location = Location.objects.get(
                pk=add_user_form.cleaned_data['location'])
            new_normal_user.save()

    else:
        add_user_form = AddUserForm(prefix='user')

    return render(request, 'add_user.html',
                  {
                      'user_form': add_user_form,
                      'new_normal_user': new_normal_user
                  })

@login_required()
@user_passes_test(lambda u: u.normaluser.isAdmin)
def delete(request, user_id):
    """ Delete a User """

    try:
        user = User.objects.get(id=user_id)
    except:
        return render(
        request, 'list.html', {'users': NormalUser.objects.all()})
    user.delete()
    return render(request, 'list.html', {'users': NormalUser.objects.all()})

@login_required()
@user_passes_test(lambda u: u.normaluser.isAdmin)
def reports(request, report_id):
    """ Handler for all reports """

    this_report = Report(report_id)
    return render(request, this_report.template, {
        'title' : this_report.title,
        'details' : this_report.report_data,
        'summary' : this_report.summary_data,
        'chart' : this_report.chart_data,
        'sort' : this_report.sort_col
    })

@login_required()
@user_passes_test(lambda u: u.normaluser.isAdmin)
def reports_filter(request):
    """ Handler for custom reports """

    # If POST, process form data
    if request.method == 'POST':
        form = ReportFilterForm(request.POST)
        this_report = Report('0')
        if form.is_valid():
            # Create array of filters to apply
            filters = {}
            filters['award_type'] = form.cleaned_data['award_type']
            filters['from_user'] = form.cleaned_data['from_user']
            filters['from_dept'] = form.cleaned_data['from_dept']
            filters['from_location'] = form.cleaned_data['from_location']
            filters['to_user'] = form.cleaned_data['to_user']
            filters['to_dept'] = form.cleaned_data['to_dept']
            filters['to_location'] = form.cleaned_data['to_location']
            filters['from_date'] = form.cleaned_data['from_date']
            filters['to_date'] = form.cleaned_data['to_date']

            # Apply filters to report
            this_report.apply_filters(filters)

        return render(request, this_report.template, {
            'title' : this_report.title,
            'details' : this_report.report_data,
            'summary' : this_report.summary_data,
            'chart' : this_report.chart_data,
            'sort' : this_report.sort_col
        })

    # Else, display blank form
    else:
        form = ReportFilterForm()

    return render(request, 'report_filters.html', {'form' : form})

def logout_user(request):
    """ Handle a User logout request """

    logout(request)
    return HttpResponseRedirect('/administrator')
