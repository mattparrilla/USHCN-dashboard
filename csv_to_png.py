#!/usr/local/bin/python

from PIL import Image
import csv
import json

with open('colorbrewer.json', 'rU') as f:
    colorbrewer = json.load(f)

rainbow = ['ff0000', 'ff0000', 'ff8800', 'ffff00', '00ff00', '0000ff', '8800ff', 'ff00ff']


def array_to_image(array, palette, similarity, dimensions):
    """Take a dict of arrays and map it to an image"""

    width, height = len(array[0]), len(array)
    maximum, minimum = find_max_min(array)

    img = Image.new('RGB',
        ((dimensions[0] * width), (dimensions[1] * height)), (0, 0, 0))
    pixels = img.load()

    # define colors, bin size outside of loop
    rgb = [tuple(map(ord, color.decode('hex'))) for color in palette]
    bin_width = (maximum - minimum) / len(rgb)

    for i in range(img.size[0]):
        for j in range(img.size[1]):
            temp = array[(j / dimensions[1])][(i / dimensions[0])]
            if temp is False:
                pixels[i, j] = (255, 0, 0)
            elif temp == 0:
                pixels[i, j] = (0, 255, 0)
            else:
                color = map_colors(temp, rgb, bin_width, minimum, similarity)
                pixels[i, j] = color

    img.show()


def map_colors(value, rgb, bin_width, minimum, similarity):
    """Takes an array of colors and maps a value to a color. Values are
    assigned to a bin with a base color, then, based on similarity (which
    has a value of 0-1 and essentially determines how continuous/discrete to
    make the output) and a value's distance from the bin threshold, it is
    assigned a final color"""

    bin_idx = int((value - minimum) // bin_width) - 1
    bin_position = ((value - minimum) % bin_width) / bin_width

    r, g, b = rgb[bin_idx]
    nr, ng, nb = safe_list_get(rgb, bin_idx + 1, (255, 255, 255))

    diff_r = bin_position * (similarity * (nr - r))
    diff_g = bin_position * (similarity * (ng - g))
    diff_b = bin_position * (similarity * (nb - b))

    color = (int(r + diff_r), int(g + diff_g), int(b + diff_b))
    return color


def find_max_min(array):
    """Takes an array of arrays and finds the max and min values"""

    # start with arbitrary, but valid, first value
    maximum = array[0][0]
    minimum = array[0][0]

    for i, row in enumerate(array):
        for j, column in enumerate(row):
            value = array[i][j]
            if value > maximum:
                maximum = value
            elif value < minimum:
                minimum = value

    return maximum, minimum


def csv_to_matrix(csv_f, unit, fill_zeros, smooth_values):
    """Converts a USHCN csv into a matrix with each row a unique year and each
    value a unique value"""
    f = csv.reader(open(csv_f, 'rU'))
    values = [l for l in f]
    del values[:2]

    if unit is "day":
        length = 366
        unit_idx = 1
        year_idx = 4
    else:
        length = 12
        unit_idx = 2
        year_idx = 1

    years = []
    for value in values:
        if value[year_idx] not in years:
            years.append(value[year_idx])

    array = [[False] * length for year in years]

    # Here's what we're using below:
    # day[1] = index of day (1-366)
    # day[4] = year
    # day[5] = temperature

    last_year = values[0][year_idx]  # define first year for comparison in loop
    row_of_array = 0
    for value in values:
        if value[year_idx] != last_year:
            last_year = value[year_idx]  # set new year
            row_of_array += 1  # update row
        try:
            array[row_of_array][int(value[unit_idx]) - 1] = float(value[-1])
        except:
            pass

    if fill_zeros:
        array = smooth_nulls(array)

    if smooth_values:
        array = five_day_averages(array)

    return array


def smooth_nulls(array):
    """This function takes a matrix as an input. For any values that meet
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
    """Takes a matrix and creates a copy of the same dimensions of the
    running average of the values for a five day period."""

    new_array = []
    for i, row in enumerate(array):
        new_array.append([])
        for j, item in enumerate(row):
            five_days = [safe_list_get(array[i], j - 2, False),
                safe_list_get(array[i], j - 1, False), array[i][j],
                safe_list_get(array[i], j + 1, False),
                safe_list_get(array[i], j + 2, False)]
            valid_days = 5 - five_days.count(False)
            if valid_days == 0:
                new_array[i].append(False)
            else:
                new_array[i].append(sum(five_days) / valid_days)

    return new_array


def safe_list_get(l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default


def make_image():
    csv_f = "data/%s.csv" % raw_input("What file to visualize: ")
    unit = raw_input("What is unit (blank for day): ") or 'day'
    fill_zeros = raw_input("Should null values be filled? (blank = no): ")
    smooth_values = raw_input("Should the values be smoothed? (blank = no): ")
    palette = eval(raw_input("What palette to use (blank = b/w): ") or ['ffffff',
        '000000'])
    similarity = float(raw_input("How similar to the next bin should " +
        "color be? \n(On a scale 0-1, default=not similar) ")) or 0

    array = csv_to_matrix(csv_f, unit, fill_zeros, smooth_values)
    img = array_to_image(array, palette, similarity, dimensions=(2, 4))
    return img

make_image()
