import os
from datetime import datetime, timedelta

MONTH = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}


def add_day_to_date_str(date_str: str, day_shift: int):
    """Add number of day to a date string.

    For example, if I want to add a day to the date "2022-08-31", it should return "2022-09-01".
    Args:
        date_str (str): the date string formatted as "%Y-%m-%d".
        day_shift (int): the number of days to shift. Could be negative.

    Returns:
        shifted_day_str (str): the shifted day string in format "%Y-%m-%d".
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    shifted_day = date + timedelta(days=day_shift)
    shifted_day_str = datetime.strftime(shifted_day, "%Y-%m-%d")
    return shifted_day_str


def minus_two_dates(date_str1: str, date_str2: str):
    """Minus two dates.

    Args:
        date_str1 (str): the date string formatted as "%Y-%m-%d".
        date_str2 (str): the number of days to shift. Could be negative.

    Returns:
        days (int): the days between two dates
    """
    date1 = datetime.strptime(date_str1, "%Y-%m-%d")
    date2 = datetime.strptime(date_str2, "%Y-%m-%d")
    return (date1 - date2).days


def output_csv(the_path, data_dict, order=None, delimiter=','):
    """Output a csv file from a python dictionary.

    If the csv file exists, it outputs another row under this csv file.

    Args:
        the_path: the filename of the csv file.
        data_dict: the data dictionary.
        order: if specified, the columns of the csv follow the specified order. Default: None.
        delimiter: the seperated delimiter. Defulat: ','.
    """
    if the_path.endswith('.tsv'):
        delimiter = '\t'

    is_file_exists = os.path.exists(the_path)
    with open(the_path, 'a+') as op:
        keys = list(data_dict.keys())
        if order is not None:
            keys = order + [k for k in keys if k not in order]

        col_title = delimiter.join([str(k) for k in keys])
        if not is_file_exists:
            print(col_title, file=op)
        else:
            old_col_title = open(the_path, 'r').readline().strip()
            if col_title != old_col_title:
                old_order = old_col_title.split(delimiter)

                no_key = [k for k in old_order if k not in keys]
                if len(no_key) > 0:
                    print('The data_dict does not have the '
                          'following old keys: %s' % str(no_key))

                additional_keys = [k for k in keys if k not in old_order]
                if len(additional_keys) > 0:
                    print('WARNING! The data_dict has following additional '
                          'keys %s.' % (str(additional_keys)))
                    col_title = delimiter.join([
                        str(k) for k in old_order + additional_keys])
                    print(col_title, file=op)

                keys = old_order + additional_keys

        vals = []
        for k in keys:
            val = data_dict.get(k, -999)
            vals.append(str(val))

        print(delimiter.join(vals), file=op)
