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


def financial_year(value,start,end):

    data={}
    # for i in xrange(start.year-1, end.year + 1):
    #     data[i]=0
    diff = relativedelta(end, start)

    # +1 because counting the first and last month in the calculation
    months = (diff.years * 12) + diff.months + 1

    # If the end day < start day, will lose an extra month in the diff calc which needs to be added back in unless
    # both dates are at the end of the month where one months finishes on the 30th and the other on the 31st. In
    # this instance, we don't need to add an extra month.
    if end.day < start.day and not \
            (end_of_month(start) and end_of_month(end)):
        months += 1

    # Set up intervening years list
    intervening_years = range(start.year, end.year)

    # Cash per month
    month_cash = float(value)/months

    # Add start year
    if start.month < 4:
        # Start date is before 1 April of the start year
        data[start.year - 1] = (4 - start.month) * month_cash
    else:
        # Start date is after 1 April of the start year
        data[start.year] = (12-(start.month - 4)) * month_cash
        # First financial year taken care of, remove from intervening years list
        if intervening_years:
            del intervening_years[0]

    # Add end year
    if end.month < 4:
        # End date is before 1 April of the end year
        data[end.year -1] = (9+end.month) * month_cash
        # Last financial year taken care of, remove from intervening years list
        if intervening_years:
            del intervening_years[-1]
    else:
        # End date is after 1 April of the end year
        data[end.year] = (end.month - 3) * month_cash

    # Add data to intervening years
    for year in intervening_years:
        data[year] = 12 * month_cash

    return data