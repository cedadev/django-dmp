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

        grant_value_pattern = re.compile('&pound;([0-9,]*)')
        grant_programme_pattern = re.compile('list_them.asp\?them(.*)<\/a><\/span>')

        grants = Grant.objects.all()
        for i,grant in enumerate(grants):
            url = 'http://gotw.nerc.ac.uk/list_full.asp?pcode={}'.format(grant.number)
            response = requests.get(url).text
            value_match = re.search(grant_value_pattern,response)
            if value_match:
                grant_value = int(value_match.group(1).replace(',',''))

                grant.grant_value = grant_value

            programme_match = re.search(grant_programme_pattern,response)
            if programme_match:
                grant.programme = programme_match.group(1).split('>')[1]

            if value_match or programme_match:
                grant.save()

            self.stdout.write('{}'.format(i))

