from models import Reminder
from dateutil.relativedelta import relativedelta

def init_reminders(project):

    # Add basic reminders to project.
    # Initial contact reminder
    Reminder(
        project=project,
        description="Send initial email",
        reminder="custom",
        due_date= project.startdate + relativedelta(months=1),
        state="Open"
    ).save()

    # Dmp upload reminder
    Reminder(
        project=project,
        description="Make and upload DMP",
        reminder="custom",
        due_date= project.startdate + relativedelta(months=3),
        state="Open"
    ).save()

    # Project nearing end date, check for data
    Reminder(
        project=project,
        description="Project nearing end date",
        reminder="custom",
        due_date= project.enddate + relativedelta(months=-3),
        state="Open"
    ).save()

def end_of_month(date):
    """
    Takes a datetime object and returns wheather the date is at the end of the month
    :param date: Datetime object
    :return: Boolean
    """
    month_length = [0,31,28,31,30,31,30,31,31,30,31,30,31]
    return date.day == month_length[date.month]