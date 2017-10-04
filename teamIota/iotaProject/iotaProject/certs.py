""" certs.py """

import os
import re
import logging
import shutil
from subprocess import Popen, PIPE
from tempfile import mkstemp
from django.core.files.storage import default_storage as storage
from django.core.files import File
from django.core.mail.message import EmailMessage
from django.template.loader import render_to_string
from teamiota.models import AwardEvent
from wand.image import Image

# pylint: disable=too-many-instance-attributes
class Certificate():
    """ A certificate (pdf, thumbnail png, or large png) """

    # Constructor takes award Id and pulls info from database to setup instance variables
    def __init__(self, awardId):
        event = AwardEvent.objects.get(id=awardId)
        self.to_name = event.awardee.nickname
        self.to_email = event.awardee.user.email
        self.from_name = event.awarder.nickname
        self.from_signature = None
        self.award_type = event.awardType.awardType
        self.award_template = event.awardType.awardTemplate

        # Make a local copy of the signature image
        with storage.open(event.awarder.signatureImage.name, 'rb+') as src:
            with open('signature.png', 'wb+') as dest:
                shutil.copyfileobj(src, dest)
                self.from_signature = File(dest)

        # Extract date info
        award_date = event.dateOfAward

        # Day with st, nd, rd, th appended
        day = award_date.day
        if day == 1 or day == 21 or day == 31:
            self.day = str(day) + "st"
        elif day == 2 or day == 22:
            self.day = str(day) + "nd"
        elif day == 3 or day == 23:
            self.day = str(day) + "rd"
        else:
            self.day = str(day) + "th"

        # Month by name
        self.month = award_date.strftime("%B")
        self.year = str(award_date.year)

    # Helper method for populating latex template and converting to PDF
    def __generate_pdf(self):
        # pdflatex code based on two references:
        # https://blog.sevenbyte.org/2014/09/23/generating-pdfs-with-django-and-latex.html
        # http://robvdl.co.nz/blog/post/latex-and-django/

        # Separate signatureImage into path and filename and modify for tex requirements
        # Get path and add trailing /

        sig_path, sig_file = os.path.split(self.from_signature.name)

        # Special handling for Windows test environments
        if os.name == 'nt':
            sig_path = sig_path.replace('\\', '/')

        sig_path += '/'
        # Get filaname without extension
        sig_name, ext = os.path.splitext(sig_file)

        # Render latex award using template and instance data
        context = {
            'toName' : self.to_name,
            'fromName' : self.from_name,
            'signaturePath' : sig_path,
            'signature' : sig_name,
            'awardType' : self.award_type,
            'awardColor' : self.award_template,
            'awardDay' : self.day,
            'awardMonth' : self.month,
            'awardYear' : self.year,
        }
        latex = render_to_string('award.tex', context)

        # Remove spaces caused by django templating.
        # Based on example from: http://stackoverflow.com/questions/35085077/\
        # how-to-properly-set-variables-in-a-latex-template-for-django
        latex = re.sub(r'\{REPLACE', '{', latex)
        latex = re.sub(r'REPLACE\}', '}', latex)
        latex = latex.encode('utf-8')

        # Setup temp file
        temp_file, path = mkstemp(prefix="award_", suffix=".pdf")

        # Special handling for Windows test environments
        if os.name == 'nt':
            path = path.replace('\\', '/')

        # split path into folder and filename
        folder, filename = os.path.split(path)
        # split filename into name and extension (pdflatex uses jobname)
        job_name, ext = os.path.splitext(filename)

        # Run pdflatex to generate PDF tempfile, run twice to place border
        # correctly
        for _ in range(2):
            process = Popen(
                ["pdflatex", "-output-directory", folder, "-jobname", job_name],
                stdin=PIPE,
                stdout=PIPE
            )
            process.communicate(latex)

        # Clean-up temp files
        for ext in (".aux", ".log", ".toc", ".lof", ".lot", ".synctex.gz"):
            try:
                os.remove(os.path.join(folder, job_name) + ext)
            except OSError:
                pass

        # Special handling for Windows test environments
        if os.name == 'nt':
            # Copy texput.pdf to correct path
            try:
                with open(folder + "/texput.pdf", "rb") as src, \
                     os.fdopen(temp_file, "wb") as dest:
                    shutil.copyfileobj(src, dest)

            except Exception as exception:
                print('{0}'.format(exception))

            try:
                os.remove(folder + "/texput.pdf")

            except Exception as exception:
                print('{0}'.format(exception))

            # Clean-up temp files
            for ext in (".aux", ".log", ".toc", ".lof", ".lot", ".synctex.gz"):
                try:
                    os.remove(os.path.join(folder + "/texput") + ext)
                except Exception as exception:
                    pass

        # Return generated PDF as path
        return path

    # Emails certificate to award recipient at their registered email address
    def email(self):
        """ Send email to award recipient User email """

        # Setup logger for debugging
        logger = logging.getLogger(__name__)

        # Create email fields
        this_subject = "You've received an award"
        email_body = 'Congratulations {0}! {1} has awarded you with {2}. ' +\
                     'Your award certificate is attached.'
        email_body = email_body.format(
            self.to_name,
            self.from_name,
            self.award_type
        )

        # Generate PDF
        path = self.__generate_pdf()
        filename = os.path.split(path)[1]

        # Open file and read contents into variable
        try:
            pdf = open(path, mode='rb')
            pdf_content = pdf.read()
            pdf.close()

        except OSError as exception:
            logger.error('OS error: %s ', exception)

        # Create email with pdf attached
        email = EmailMessage(
            subject=this_subject,
            body=email_body,
            from_email='teamosuiota@gmail.com',
            to=[self.to_email],
            headers={'Reply-To': 'teamosuiota@gmail.com'}
            )
        try:
            email.attach(filename, pdf_content, 'application/pdf')
            email.send()

        except:
            logger.error('Failed to send email')

        # Clean-up temp file
        try:
            os.remove(path)

        except OSError:
            pass

    def get_pdf(self):
        """ Return PDF version of certificate """

        # Generate PDF and return path
        return self.__generate_pdf()

    def get_image(self):
        """ Return full-sized PNG of certificate """

        # Generate PDF
        pdf_path = self.__generate_pdf()

        # Get path for new image
        folder, pdf_filename = os.path.split(pdf_path)

        filename = os.path.splitext(pdf_filename)[0]
        filename += '.png'
        path = os.path.join(folder, filename)

        # Convert to PNG
        # pylint: disable=line-too-long
        # Sources:  http://mikelynchgames.com/software-development/using-wand-to-extract-pngs-from-pdfs/
        #           http://stackoverflow.com/questions/27826854/python-wand-convert-pdf-to-png-disable-transparent-alpha-channel
        with Image(filename=pdf_path, resolution=300) as img:
            with img.convert('png') as converted:
                converted.alpha_channel = False
                converted.save(filename=path)

        # Clean-up temp file
        try:
            os.remove(pdf_path)
        except OSError as err:
            print('{0}'.format(err))

        # Return image path

        # Special handling for Windows test environments
        if os.name == 'nt':
            path = path.replace('\\', '/')

        return path

    def get_thumb(self):
        """ Return thumbnail-sized PNG of certificate """

        # Generate PDF
        pdf_path = self.__generate_pdf()

        # Get path for new image
        folder, pdf_filename = os.path.split(pdf_path)
        filename = os.path.splitext(pdf_filename)[0]
        filename += '.png'
        path = os.path.join(folder, filename)

        # Convert to PNG
        # pylint: disable=line-too-long
        # Sources:  http://mikelynchgames.com/software-development/using-wand-to-extract-pngs-from-pdfs/
        # pylint: disable=line-too-long
        #           http://stackoverflow.com/questions/27826854/python-wand-convert-pdf-to-png-disable-transparent-alpha-channel
        with Image(filename=pdf_path, resolution=300) as img:
            with img.convert('png') as converted:
                converted.alpha_channel = False
                converted.resize(165, 125)
                converted.save(filename=path)

        # Clean-up temp file
        try:
            os.remove(pdf_path)
        except OSError:
            pass

        # Special handling for Windows test environments
        if os.name == 'nt':
            path = path.replace('\\', '/')

        return path
