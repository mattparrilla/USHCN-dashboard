#!/usr/local/bin/python

from PIL import Image
import csv
import json

with open('colorbrewer.json', 'rU') as f:
    colorbrewer = json.load(f)

rainbow = ['000000', 'ff0000', 'ff8800', 'ffff00', '88ff00', '00ff00', '0000ff', '8800ff', 'ff00ff']


def make_image(f_n='btv', fill_null=True,
               unit='day', smooth_horizontal=False, smooth_vertical=False,
               palette='paired', bins='4', dimensions=(2, 2), similarity=1,
               recursion=0, start_idx=False, save_image=False):

    palettes = {
        'black_white': ['000000', 'ffffff'],
        'paired': colorbrewer['Paired'],
        'red': colorbrewer['YlOrRd']
    }

    csv_f = "data/%s.csv" % f_n
    save_image = False

    array = csv_to_matrix(csv_f, unit, fill_null, smooth_horizontal,
        smooth_vertical, recursion, start_idx)
    img = array_to_image(array, palettes[palette][bins], similarity, dimensions)
    if save_image:
        img.save('img/%s-%s-%s-%s%s%s-%s.png' % (f_n, palette, fill_null,
            recursion, 'x' if smooth_horizontal else '',
            'y' if smooth_vertical else '', similarity))
    return img


def array_to_image(array, palette, similarity, dimensions):
    """Take a dict of arrays and map it to an image"""

    width, height = len(array[0]), len(array)
    maximum, minimum = find_max_min(array)

    img = Image.new('RGB',
        ((dimensions[0] * width), (dimensions[1] * height)), (0, 0, 0))
    pixels = img.load()

    # define colors, bin size outside of loop
    rgb = [tuple(map(ord, color.decode('hex'))) for color in palette]
    bin_width = (maximum - minimum) / (len(rgb) - 1)

    for i in range(img.size[0]):
        for j in range(img.size[1]):
            temp = array[(j / dimensions[1])][(i / dimensions[0])]
            # if temp is False:
            #     pixels[i, j] = (255, 0, 0)
            # else:
            color = map_colors(temp, rgb, bin_width, minimum, similarity)
            pixels[i, j] = color

    return img


def map_colors(value, rgb, bin_width, minimum, similarity):
    """Takes an array of colors and maps a value to a color. Values are
    assigned to a bin with a base color, then, based on similarity (which
    has a value of 0-1 and essentially determines how continuous/discrete to
    make the output) and a value's distance from the bin threshold, it is
    assigned a final color"""

    bin_idx = int((value - minimum) // bin_width)
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


def csv_to_matrix(csv_f, unit, fill_null, smooth_horizontal, smooth_vertical,
        recursion, start_idx=False):
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

    #del array[:20]
    if start_idx:
        array = shift_array(array, start_idx)

    if fill_null:
        array = smooth_nulls(array)

    while recursion > 0:
        if smooth_vertical:
            array = five_day_averages(array, direction="vertical")
        if smooth_horizontal:
            array = five_day_averages(array)
        recursion -= 1

    return array


def shift_array(array, start_idx):
    """Shifts an array so a particular index is now 0"""

    dimensions = (len(array[0]), len(array))
    new_array = [[False] * dimensions[0] for i in range(len(array))]
    for i, row in enumerate(array):
        for j, value in enumerate(row):
            new_array[i][j - start_idx] = value

    return new_array


def smooth_nulls(array):
    """This function takes a matrix as an input. For any values that meet
    a condition, it averages the value at the same index in both the preceding
    and the following rows and assigns the result as its value"""

    for i, year in enumerate(array):
        for j, day in enumerate(year):
            if day is False:  # FIX: ideally this will be False, not zero
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


def five_day_averages(array, direction=False):
    """Takes a matrix and creates a copy of the same dimensions of the
    running average of the values for a five day period."""

    new_array = []
    for i, row in enumerate(array):
        new_array.append([False] * len(row))
        for j, item in enumerate(row):
            if direction is "vertical":
                # Builds an array of the value on this date over the surrounding five years
                five_days = [safe_list_get(array, i - 2, False, j),
                             safe_list_get(array, i - 1, False, j),
                             array[i][j],
                             safe_list_get(array, i + 1, False, j),
                             safe_list_get(array, i + 2, False, j)]
                if i == 0 or i + 1 == len(array):
                    new_array[i][j] = sum(five_days) / 3
                elif i == 1 or i + 2 == len(array):
                    new_array[i][j] = sum(five_days) / 4
                else:
                    new_array[i][j] = sum(five_days) / 5
            else:
                # Builds an array of the value on this surrounding five days
                five_days = [safe_list_get(row, j - 2, False),
                             safe_list_get(row, j - 1, False),
                             array[i][j],
                             safe_list_get(row, j + 1, False),
                             safe_list_get(row, j + 2, False)]
                new_array[i][j] = sum(five_days) / 5

                # TODO: Consider beginning and end of year

    return new_array


def safe_list_get(l, idx, default, additional=-1):
    try:
        if idx < 0:
            return default

        if additional >= 0:
            return l[idx][int(additional)]
        else:
            return l[idx]
    except IndexError:
        return default

make_image()
