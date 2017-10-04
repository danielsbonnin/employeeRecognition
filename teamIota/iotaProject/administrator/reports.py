""" administrator/reports.py """

import json
from datetime import date
from calendar import monthrange
from django.db.models import Count
from teamiota.models import NormalUser, AwardEvent, Award, Department, Location

# pylint: disable=too-few-public-methods
class Summary():
    """ Summary data row for objects not in model """

    def __init__(self, category, num_awards):
        self.category = category
        self.num_awards = num_awards

    def __str__(self):
        return self.category

class Report():
    """ Data about award events

    Constructor takes report Id and sets all instance variables:

        template:       template used to render report data
        title:          title displayed on report
        report_data:    data for details table
        summary_data:   data for summary table
        chart_data:     json array for Google Chart
        sort_col:       index for column to be initially sorted

        0-type, 1-date, 2-awarder, 3-awardee, 4-dept, 5-location
    """
    # pylint: disable=too-few-public-methods, too-many-locals, too-many-branches
    def __init__(self, reportId):

    # Sources for SQL queries:
    # https://docs.djangoproject.com/en/1.9/topics/db/queries/
    # https://docs.djangoproject.com/en/1.9/topics/db/aggregation/

    # 0 = Custom Report
        if reportId == '0':
            self.template = "reports/report_custom.html"
            self.title = "Awards by Custom Filter"
            self.report_data = []
            self.summary_data = []
            self.chart_data = []
            self.sort_col = 0

        # 1 = Awards by Type
        elif reportId == '1':
            self.template = "reports/report_pie.html"
            self.title = "Awards by Type"
            self.report_data = AwardEvent.objects.order_by('awardType')
            self.summary_data = (
                Award.objects.annotate(num_awards=Count('awardevent')))
            chart_array = []
            chart_array.append(['Category', 'Count'])

            for row in self.summary_data:
                chart_array.append([row.awardType, row.num_awards])
            self.chart_data = json.dumps(chart_array)
            self.sort_col = 0

    # 2 = Awards by Department
        elif reportId == '2':
            self.template = "reports/report_pie.html"
            self.title = "Awards Received by Department"
            self.report_data = (
                AwardEvent.objects.order_by('awardee__department'))
            self.summary_data = Department.objects.\
                annotate(num_awards=Count('normaluser__awardEE'))
            chart_array = []
            chart_array.append(['Category', 'Count'])
            for row in self.summary_data:
                chart_array.append([row.name, row.num_awards])
            self.chart_data = json.dumps(chart_array)
            self.sort_col = 4

        # 3 = Awards by Location
        elif reportId == '3':
            self.template = "reports/report_pie.html"
            self.title = "Awards Received by Location"
            self.report_data = AwardEvent.objects.order_by('awardee__location')
            self.summary_data = Location.objects.\
                annotate(num_awards=Count('normaluser__awardEE'))
            chart_array = []
            chart_array.append(['Category', 'Count'])
            for row in self.summary_data:
                chart_array.append([row.name, row.num_awards])
            self.chart_data = json.dumps(chart_array)
            self.sort_col = 5

        # 4 = Awards This Month
        elif reportId == '4':
            self.template = "reports/report_line.html"
            self.title = "Awards Received This Month"

            # Calculate start and end dates. Sources:
            # https://docs.python.org/2/library/datetime.html
            # pylint: disable=line-too-long
            # http://stackoverflow.com/questions/42950/get-last-day-of-the-month-in-python
            cur_date = date.today()
            cur_range = monthrange(cur_date.year, cur_date.month)

            # Start/End date = first/last day of current month in ISO format
            start_date = cur_date.replace(day=1).isoformat()
            end_date = cur_date.replace(day=cur_range[1]).isoformat()
            self.report_data = AwardEvent.objects.filter(
                dateOfAward__gte=start_date, dateOfAward__lte=end_date)

            # Summary = total awards count for month (length of report_data)
            sum_array = []
            row = Summary(
                'Awards in ' + cur_date.strftime('%B'),
                len(self.report_data))
            sum_array.append(row)
            self.summary_data = sum_array

            # Chart = numAwards each day
            chart_data = (
                AwardEvent.objects
                .filter(dateOfAward__gte=start_date, dateOfAward__lte=end_date)
                .values('dateOfAward').annotate(num_awards=Count('id'))
                .order_by('dateOfAward')
                )

            chart_array = []
            chart_array.append(['Category', 'Count'])
            if len(chart_data) > 0:
                for row in chart_data:
                    chart_array.append(
                        [row['dateOfAward'].isoformat(),
                         row['num_awards']])
            else:
                # Provide default 0 value to prevent chart error on no awards
                chart_array.append([cur_date.strftime('%B'), 0])
            self.chart_data = json.dumps(chart_array)
            self.sort_col = 1

        # 5 = Awards This Year
        elif reportId == '5':
            self.template = "reports/report_line.html"
            self.title = "Awards Received This Year"

            # Calculate start and end dates;
            # first/last day of current year in ISO format
            cur_date = date.today()
            start_date = cur_date.replace(month=1, day=1).isoformat()
            end_date = cur_date.replace(month=12, day=31).isoformat()
            self.report_data = AwardEvent.\
                               objects.\
                               filter(
                                   dateOfAward__gte=start_date,
                                   dateOfAward__lte=end_date)

            # Create summary data: count for each month
            sum_array = []
            for i in range(12):
                temp_date = cur_date.replace(month=i+1)
                temp_range = monthrange(temp_date.year, temp_date.month)
                temp_start = temp_date.replace(day=1).isoformat()
                temp_end = temp_date.replace(day=temp_range[1]).isoformat()
                count = AwardEvent.\
                        objects.\
                        filter(
                            dateOfAward__gte=temp_start,
                            dateOfAward__lte=temp_end).\
                        count()
                row = Summary(temp_date.strftime('%B'), count)
                sum_array.append(row)
            self.summary_data = sum_array

            # Create chart data from summary
            chart_array = []
            chart_array.append(['Category', 'Count'])
            for row in self.summary_data:
                chart_array.append([row.category, row.num_awards])
            self.chart_data = json.dumps(chart_array)
            self.sort_col = 1

        # 6 = Awards All Time -> default report, see else

        # 7 = Awards Given by User
        elif reportId == '7':
            self.template = "reports/report_bar.html"
            self.title = "Awards Given by User"
            self.report_data = AwardEvent.objects.order_by('awarder')
            # Create summary data: count for each awarde
            counts = (
                NormalUser.objects.filter(isAdmin=False)
                .annotate(num_awards=Count('awardER')))
            sum_array = []
            for row in counts:
                sum_array.append(Summary(row.nickname, row.num_awards))
            self.summary_data = sum_array
            # Create chart data from summary
            chart_array = []
            chart_array.append(['Category', 'Count'])
            for row in self.summary_data:
                chart_array.append([row.category, row.num_awards])
            self.chart_data = json.dumps(chart_array)
            self.sort_col = 2

        # 8 = Awards Received by User
        elif reportId == '8':
            self.template = "reports/report_bar.html"
            self.title = "Awards Received by User"
            self.report_data = AwardEvent.objects.order_by('awardee')

            # Create summary data: count for each awarde
            counts = NormalUser.objects.filter(isAdmin=False).\
                annotate(num_awards=Count('awardEE'))
            sum_array = []
            for row in counts:
                sum_array.append(Summary(row.nickname, row.num_awards))
            self.summary_data = sum_array

            # Create chart data from summary
            chart_array = []
            chart_array.append(['Category', 'Count'])
            for row in self.summary_data:
                chart_array.append([row.category, row.num_awards])
            self.chart_data = json.dumps(chart_array)
            self.sort_col = 3

        # Default report = Awards All Time
        else:
            self.template = "reports/report_line.html"
            self.title = "Awards All Time"
            self.report_data = AwardEvent.objects.all()

            # Create summary data: total lifetime awards
            sum_array = []
            row = Summary('Lifetime Awards', len(self.report_data))
            sum_array.append(row)
            self.summary_data = sum_array

            # Chart = numAwards each day
            chart_data = AwardEvent.\
                         objects.\
                         values('dateOfAward').\
                         annotate(num_awards=Count('id')).\
                         order_by('dateOfAward')
            chart_array = []
            chart_array.append(['Category', 'Count'])
            if len(chart_data) > 0:
                for row in chart_data:
                    chart_array.append([row['dateOfAward'].isoformat(),
                                        row['num_awards']])
            else:
                # Provide default 0 value to prevent chart error on no awards
                chart_array.append(['Lifetime', 0])
            self.chart_data = json.dumps(chart_array)
            self.sort_col = 1

    # pylint: disable=unused-variable
    def apply_filters(self, filters):
        """ Query database based on User-specified filters """

        # Refine query filter-by-filter
        result = AwardEvent.objects.all()

        # General
        if filters['award_type'] != '0':
            result = result.filter(awardType=int(filters['award_type']))
        if filters['from_date'] != None:
            result = result.filter(
                dateOfAward__gte=filters['from_date'].isoformat())
        if filters['to_date'] != None:
            result = result.filter(
                dateOfAward__lte=filters['to_date'].isoformat())

        # Awarded By (awarder)
        if filters['from_user'] != '0':
            result = result.filter(awarder=int(filters['from_user']))
        if filters['from_dept'] != '0':
            result = result.filter(
                awarder__department=int(filters['from_dept']))
        if filters['from_location'] != '0':
            result = result.filter(
                awarder__location=int(filters['from_location']))

        # Awarded To (awardee)
        if filters['to_user'] != '0':
            result = result.filter(awardee=int(filters['to_user']))
        if filters['to_dept'] != '0':
            result = result.filter(awardee__department=int(filters['to_dept']))
        if filters['to_location'] != '0':
            result = result.filter(
                awardee__location=int(filters['to_location']))

        # Replace report and summary data
        self.report_data = result
        sum_array = []
        row = Summary('Filtered Awards', len(self.report_data))
        sum_array.append(row)
        self.summary_data = sum_array
