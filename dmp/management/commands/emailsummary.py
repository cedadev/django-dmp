from django.core.management.base import BaseCommand
from dmp.models import *
from django.template import Context, Template, loader
from django.core.mail import send_mail, EmailMultiAlternatives

'''Produces a summary email for each user in the DMP app who have reminders.
   Gives only the expired and active reminders. Email is sent via a cronjob as a manage.py task.'''

# Produce a list of users with active reminders.

class Command(BaseCommand):
    help = 'Generates emails for each of the users with open reminders which have expired or are due in the next month.'

    def handle(self, *args, **options):

        scisupcontacts = Person.objects.filter(is_active=True).filter(project__reminder__state="Open").distinct()

        for contact in scisupcontacts:
            if contact.email:

                today = date.today()

                reminders = Reminder.objects.filter(project__sciSupContact=contact)

                # List of project reminders for which the expiry date has passed
                expired = reminders.filter(due_date__lt=today)

                # List of projects reminders which have an expiry in next 2 weeks
                active = reminders.filter(due_date__range=[today, today + relativedelta(months=1)])

                # Render Template Body
                # template = Template('/dmp/templates/weekly_email/weekly_email.html')
                template = loader.get_template('dmp/weekly_email/weekly_email.html')
                context = Context({
                    "expired": expired,
                    "active": active,
                    "contact": contact,
                })

                message_content = template.render(context)

                send_mail(
                    subject = "DMP Reminders Weekly Update",
                    message= message_content,
                    from_email= 'donotreply@ceda.ac.uk',
                    recipient_list= [contact.email],
                    html_message= message_content,
                )



