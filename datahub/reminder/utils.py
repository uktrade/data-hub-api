from dateutil.relativedelta import relativedelta


REMINDER_DAYS_MAPPING = {
    30: lambda day: day + relativedelta(months=1),
    60: lambda day: day + relativedelta(months=2),
}


def reminder_days_to_date_filter(current_date, reminder_days):
    return [REMINDER_DAYS_MAPPING[days_left](current_date) for days_left in reminder_days]
