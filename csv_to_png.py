#!/usr/local/bin/python

from PIL import Image
import csv


def dict_to_image(array):
    """Take a dict of arrays and map it to an image"""

    width = len(array[0])
    height = len(array)

    maximum, minimum = find_max_min(array)

    unit_dimensions = (1, 2)  # to increase size of each data point (w,h)

    img = Image.new('RGB',
        ((unit_dimensions[0] * width), (unit_dimensions[1] * height)), (0, 0, 0))
    pixels = img.load()

    for i in range(img.size[0]):
        for j in range(img.size[1]):
            temp = array[(j / unit_dimensions[1])][(i / unit_dimensions[0])]
            if temp is False:
                pixels[i, j] = (255, 0, 0)
            else:
                color = (temp * 205) / maximum
                pixels[i, j] = (color, color, color)

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


def csv_to_array(csv_f):
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
    # day[1] = index of day 1-366
    # day[4] = year
    # day[5] = temperature

    last_year = days[0][4]  # define first year for comparison in loop
    row_of_array = 0
    for day in days:
        if day[4] != last_year:
            last_year = day[4]  # set new year
            row_of_array += 1  # update row
        try:
            array[row_of_array][int(day[1]) - 1] = int(day[5])
        except ValueError:
            pass

    return array


def array_of_averages(array):
    for i, row in enumerate(array):
        for j, item in enumerate(row):
            try:
                five_day_sum = (array[i][j - 2] + array[i][j - 1] + array[i][j] +
                    array[i][j + 1] + array[i][j + 1])
                array[i][j] = five_day_sum / 5
            except IndexError:
                pass

    return array


def make_image(csv_f):
    array = csv_to_array(csv_f)
    averaged_array = array_of_averages(array)
    img = dict_to_image(averaged_array)
    return img

make_image('montana.csv')
