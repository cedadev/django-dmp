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
