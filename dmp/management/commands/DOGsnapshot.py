from django.core.management.base import BaseCommand
from dmp.models import Grant, DOGstats
import datetime

class Command(BaseCommand):
    help = 'Takes a snapshot of the grants for the DOG report. Used to take a regular image and upload to database to allow historical queries.'

    def handle(self, *args, **options):
        todays_date = datetime.datetime.date(datetime.datetime.now())
        todays_datetime = datetime.datetime.now()

        # filter queries to collect data for new grant DOG report
        new_grant_query = [
            {'project__status': 'Active'},  # Grant active
            {'project__initial_contact__isnull': False},  # Contacted
            {'project__dmp_agreed__isnull': False},  # DMPs Accepted
            {'project__status': 'NoData'},  # No Data Grants
            {'project__status': 'Complete'},  # Complete Grants
            {'project__status': 'EndedWithDataToCome'},  # Ended with data to come grants
            {}]

        # filter queries to collect data for legacy grant DOG
        legacy_grant_query = [
            {'project__status': 'Active'},  # Grant active
            {'project__status': 'NoData'},  # No Data Grants
            {'project__status': 'Complete'},  # Complete Grants
            {'project__status': 'EndedWithDataToCome'},  # Ended with data to come grants
            {}
        ]

        new_grant_dates = [datetime.date(2014, 0o4, 0o1), todays_date]
        legacy_grant_dates = [datetime.date(2010, 0o1, 0o1), datetime.date(2014, 0o3, 31)]

        def grant_summary_counter(timerange, statistic):
            total = 0
            start = timerange[0]
            end = timerange[1]

            total += Grant.objects.filter(project__startdate__range=[start, end]).filter(**statistic).count()
            return total

        # loop stats and append info
        new_grant_summary = [todays_datetime,'new_grants']
        for stat in new_grant_query:
            new_grant_summary.append(grant_summary_counter(new_grant_dates, stat))

        # loop stats and append info
        legacy_grant_summary = [todays_datetime,'legacy_grants']
        for stat in legacy_grant_query:
            legacy_grant_summary.append(grant_summary_counter(legacy_grant_dates, stat))

        # put data in database
        DOGstats(
            date= new_grant_summary[0],
            stat_type=new_grant_summary[1],
            active_grants=new_grant_summary[2],
            contacted_grants=new_grant_summary[3],
            dmps_accepted=new_grant_summary[4],
            no_data=new_grant_summary[5],
            complete_grants=new_grant_summary[6],
            ended_with_outstanding_data=new_grant_summary[7],
            total_grants=new_grant_summary[8]
        ).save()

        DOGstats(
            date=legacy_grant_summary[0],
            stat_type=legacy_grant_summary[1],
            active_grants=legacy_grant_summary[2],
            no_data=legacy_grant_summary[3],
            complete_grants=legacy_grant_summary[4],
            ended_with_outstanding_data=legacy_grant_summary[5],
            total_grants=legacy_grant_summary[6]
        ).save()


