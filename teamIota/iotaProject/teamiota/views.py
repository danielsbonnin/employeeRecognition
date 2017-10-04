""" teamiota.views.py """

import os
import shutil
from django.shortcuts import render
from django.contrib.auth import login, logout
from django.http import HttpResponseRedirect
from django.views.generic import View
from django.views.generic.detail import DetailView
from django.core.urlresolvers import reverse
from django.core.files import File
from django.core.files.storage import default_storage as storage
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from teamiota.models import NormalUser, AwardEvent
import administrator
from iotaProject.certs import Certificate
from iotaProject import settings
from .forms import NormalUserLoginForm, NormalUserEditForm, NewAwardForm

def index(request):
    """ /teamiota/ """

    title_text = 'Employee Recognition'
    context = {'titleText': title_text}
    return render(request, 'teamiota/normalUser/basePage.html', context)

class NormalUsersPortal(LoginRequiredMixin, UserPassesTestMixin, View):
    """ /teamiota/NormalUsersPortal/ """

    login_url = '/teamiota/login/'
    redirect_field_name = 'normalUsersPortal'
    titleText = 'Employee Recognition'
    context = {'titleText' : titleText, }

    def test_func(self):
        """ Test for UserPassesTestMixin """
        
        return not self.request.user.normaluser.isAdmin

    def get(self, request):
        """ Handles GET requests to Normal Users Portal """

        this_normal_user = NormalUser.objects.get(user=request.user)
        self.context['NormalUser'] = this_normal_user
        self.context['awardList'] = AwardEvent.objects.\
                                    filter(awardee=this_normal_user).\
                                    order_by('awardType')
        self.context['newAwardForm'] = \
                                    NewAwardForm(
                                        initial={'awarder':this_normal_user}
                                    )
        self.context['editForm'] = NormalUserEditForm(instance=this_normal_user)
        if this_normal_user.signatureImage:
            self.context['hasSig'] = 'true'
        else:
            self.context['hasSig'] = 'false'
        return render(request, 'teamiota/normalUser/home.html', self.context)

    def post(self, request, *args, **kwargs):
        """ Handles POST requests to Norma Users Portal """

        this_normal_user = NormalUser.objects.get(user=request.user)
        if this_normal_user.signatureImage:
            self.context['hasSig'] = 'true'
        else:
            self.context['hasSig'] = 'false'
        self.context['showEdit'] = 'false'
        self.context['showAwardForm'] = 'false' 
        if 'editForm' in request.POST:
            edit_form = NormalUserEditForm(
                request.POST,
                request.FILES,
                instance=this_normal_user
            )
            if edit_form.is_valid():
                edit_form.save()
                # Update signature check after form save
                updated_normal_user = NormalUser.objects.get(user=request.user)
                if updated_normal_user.signatureImage:
                    self.context['hasSig'] = 'true'
                else:
                    self.context['hasSig'] = 'false'
                edit_form = NormalUserEditForm(instance=this_normal_user)
            else:
                edit_form = NormalUserEditForm(request.POST)
                self.context['showEdit'] = 'true'
        else:
            edit_form = NormalUserEditForm(instance=this_normal_user)
           
        if 'newAwardForm' in request.POST:
            self.context['showAwardForm'] = 'false'
            new_award_form = NewAwardForm(request.POST)
            if new_award_form.is_valid():
                this_award_event = new_award_form.save()

                # Make a certificate from the newly created AwardEvent
                this_cert = Certificate(this_award_event.id)
                thumb_path = this_cert.get_thumb()

                # Save thumbnail to AwardEvent instance
                with open(thumb_path, 'rb+') as thumb:
                    this_award_event.certThumbnail = File(thumb)
                    this_award_event.save()

                # Delete generated file
                try:
                    os.remove(thumb_path)
                except Exception as exception:
                    print('{0}'.format(exception))

                # Send congratulatory email
                this_cert.email()

            else:
                self.context['showAwardForm'] = 'true'
        else:
            new_award_form = NewAwardForm(initial={'awarder':this_normal_user})

        self.context['NormalUser'] = this_normal_user
        self.context['awardList'] = AwardEvent.objects.\
                                    filter(awardee=this_normal_user).\
                                    order_by('awardType')
        self.context['newAwardForm'] = new_award_form
        self.context['editForm'] = edit_form

        return render(request, 'teamiota/normalUser/home.html', self.context)

class LoginView(View):
    """ /teamiota/login/ """
    template_name = 'teamiota/normalUser/loginDialog.html'

    def get(self, request):
        """ Handles GET requests for Normal User Login Form """

        form = NormalUserLoginForm(auto_id=True)
        context = {'form':form}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """ Handles POST requests for Normal User Login Form """
        form = NormalUserLoginForm(request.POST, auto_id=True)
        this_user = None
        if form.is_valid():
            this_user = form.get_user()
            login(request, this_user)
        if this_user is not None:
            this_normal_user = NormalUser.objects.get(user=this_user)
            if this_normal_user.isAdmin:
                return HttpResponseRedirect(
                    reverse(
                        administrator.views.admin_account
                        )
                    )
            else:
                return HttpResponseRedirect(reverse('normalUsersPortal'))

        return render(request, self.template_name, {'form':form})

class LogoutView(View):
    """ /teamiota/logout/ """

    def get(self, request):
        """ Handles GET requests for Normal User Logout View """

        logout(request)
        return HttpResponseRedirect(reverse('normalUserLogin'))

class RevokeView(View):
    """ /teamiota/revoke/ """

    def get(self, request):
        """ Handles GET requests for Normal User Revoke View """

        this_normal_user = NormalUser.objects.get(user=request.user)
        to_delete = AwardEvent.objects.filter(awarder=this_normal_user)
        to_delete.delete()
        return HttpResponseRedirect(reverse('normalUsersPortal'))

class DrawnSigSubmitted(View):
    """ /teamiota/drawsig/ """

    template_name = 'teamiota/normalUser/drawSignatureSuccess.html'

    def post(self, request, *args, **kwargs):
        """ Handles POST requests for the Normal Users Sig Submission view """

        this_normal_user = NormalUser.objects.get(user=request.user)
        pic = self.request.POST['imgOutput'].split('data:image/png;base64,')[1]
        from base64 import b64decode
        from django.core.files.base import ContentFile
        image_data = b64decode(pic)
        this_normal_user.signatureImage = ContentFile(image_data, 'sig.png')
        this_normal_user.save()
        return render(request, self.template_name)

class AwardView(DetailView):
    """ /teamitoa/awardEvent """

    model = AwardEvent
    template_name = 'teamiota/normalUser/awardEvent.html'

    def get_context_data(self, **kwargs):
        """ Append to the context_data of AwardEvent """
        this_cert = Certificate(self.object.id)

        # Generate full-sized certificate image for display
        src_img_path = this_cert.get_image()
        src_pdf_path = this_cert.get_pdf()

        # Copy full-sized image to /media/<AwardEvent.id>.png
        dest_img_path = settings.MEDIA_ROOT + '/' + str(self.object.id) + '.png'
        dest_pdf_path = settings.MEDIA_ROOT + '/' + str(self.object.id) + '.pdf'

        dest_img_path = str(self.object.id) + '.png'
        dest_pdf_path = str(self.object.id) + '.pdf'

        # Special handling for Windows test environments
        if os.name == 'nt':
            dest_img_path = dest_img_path.replace('\\', '/')
            dest_pdf_path = dest_pdf_path.replace('\\', '/')

        with open(src_img_path, 'rb+') as src, \
             storage.open(dest_img_path, 'wb+') as dest:
            try:
                shutil.copyfileobj(src, dest)
            except Exception as exception:
                print('{0}'.format(exception))

        # Remove generated image
        os.remove(src_img_path)

        with open(src_pdf_path, 'rb+') as src, \
             storage.open(dest_pdf_path, 'wb+') as dest:
            try:
                shutil.copyfileobj(src, dest)
            except Exception as exception:
                print('{0}'.format(exception))

        # Remove generated pdf
        os.remove(src_pdf_path)

        context = super(AwardView, self).get_context_data(**kwargs)

        # Add image url to template context
        context['certImg'] = settings.MEDIA_URL + str(self.object.id) + '.png'
        context['certPDF'] = settings.MEDIA_URL + str(self.object.id) + '.pdf'
        return context
