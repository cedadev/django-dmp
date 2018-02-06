"""
Script to scrape the value of grants from Grants on the Web and input it to the database ready for collating.
"""

from django.core.management.base import BaseCommand
from dmp.models import Grant
import requests
import re


class Command(BaseCommand):
    help = 'Scrapes grant values from Grants on the Web (gotw.nerc.ac.uk) by grant number and injects it into the database'

    def handle(self, *args, **options):

        pattern = re.compile('&pound;([0-9,]*)')

        grants = Grant.objects.all()
        for i,grant in enumerate(grants):
            url = 'http://gotw.nerc.ac.uk/list_full.asp?pcode={}'.format(grant.number)
            response = requests.get(url).text
            match = re.search(pattern,response)
            grant_value = int(match.group(1).replace(',',''))

            grant.grant_value = grant_value
            grant.save()

            self.stdout.write('{}'.format(i))

