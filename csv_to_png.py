#!/usr/local/bin/python

from PIL import Image
import csv

# why does the 366 item in each array remain false (red)
# while the holes in the data have been saved as zero in the array (green)?

# Consider smoothing out the holes in the data too. Maybe average the missing
# day against the year before and the year after

# My averaging is smoothing things out more than I'd like to. I need to create
# a new, separate array, not use the same one in place (since that will use
# some already averaged values


def array_to_image(array):
    """Take a dict of arrays and map it to an image"""

    width = len(array[0])
    height = len(array)

    maximum, minimum = find_max_min(array)

    unit_dimensions = (2, 4)  # to increase size of each data point (w,h)

    img = Image.new('RGB',
        ((unit_dimensions[0] * width), (unit_dimensions[1] * height)), (0, 0, 0))
    pixels = img.load()

    for i in range(img.size[0]):
        for j in range(img.size[1]):
            temp = array[(j / unit_dimensions[1])][(i / unit_dimensions[0])]
            if temp is False:
                pixels[i, j] = (255, 0, 0)
            elif temp == 0:
                pixels[i, j] = (0, 255, 0)
            else:
                color = int((temp * 205) / maximum)
                pixels[i, j] = (color / 10, color / 10, color)

    img.show()


def find_max_min(array):
    """Takes an array of arrays and finds the max and min values"""

    # start with arbitrary, but valid, first value
    maximum = array[0][0]
    minimum = array[0][0]

    for i in range(len(array)):
        for j in range(len(array[0])):
            value = array[i][j]
            if value > maximum:
                maximum = value
            elif value < minimum:
                minimum = value

    return maximum, minimum


def csv_to_array(csv_f, average_zeros=False):
    f = csv.reader(open(csv_f, 'rU'))
    days = [l for l in f]
    del days[:2]

    years = []
    #max_year = days[-1][4]
    #year = days[0][4]
    #while year >= max_year:
    #    years.append(year)
    #    year += 1

    for day in days:
        if day[4] not in years:
            years.append(day[4])

    array = []
    for year in years:
        array.append([False] * 366)

    # Here's what we're using below:
    # day[1] = index of day (1-366)
    # day[4] = year
    # day[5] = temperature

    last_year = days[0][4]  # define first year for comparison in loop
    row_of_array = 0
    for day in days:
        if day[4] != last_year:
            last_year = day[4]  # set new year
            row_of_array += 1  # update row
        try:
            array[row_of_array][int(day[1]) - 1] = float(day[5])
        except ValueError:
            pass

    # smooths out the missing data by averaging year before and after
    if average_zeros:
        array = smooth_nulls(array)

    return array


def smooth_nulls(array):
    """This function takes an matrix and for any values that meets
    a condition, it averages the value at the same index in both the preceding
    and the following rows and assigns the result as its value"""

    for i, year in enumerate(array):
        for j, day in enumerate(year):
            if day == 0:  # FIX: ideally this will be False, not zero
                try:
                    year_before = array[i - 1][j]
                    year_after = array[i + 1][j]
                    array[i][j] = (year_before + year_after) / 2
                except IndexError:
                    # this will throw IndexError on first and last year
                    if i == 0:
                        array[i][j] = array[i + 1][j]
                    elif i > 0:
                        array[i][j] = array[i - 1][j]

    return array


def five_day_averages(array):
    """Takes a matrix and calculates the average of each cells five neighbors"""
    for i, row in enumerate(array):
        for j, item in enumerate(row):

            try:
                running_sum = sum([safe_list_get(array[i], j - 2, 0),
                    safe_list_get(array[i], j - 1, 0), array[i][j],
                    safe_list_get(array[i], j + 1, 0),
                    safe_list_get(array[i], j + 2, 0)])
                array[i][j] = running_sum / 5
            except IndexError:
                # if index j+2 or j-2 don't exist
                if j + 3 == len(row) or j == 1:
                    array[i][j] = running_sum / 4
                # if index j+1 or j-1 don't exist
                elif j + 2 == len(row) or j == 0:
                    array[i][j] = running_sum / 3

    return array


def safe_list_get(l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default


def make_image(csv_f, avg_zeros=False):
    array = csv_to_array(csv_f, average_zeros=True)
    averaged_array = five_day_averages(array)
    img = array_to_image(averaged_array)
    return img

make_image('precip.csv')
