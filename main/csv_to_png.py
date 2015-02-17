#!/usr/local/bin/python

from PIL import Image
from main import ABSOLUTE_PATH
import csv
import json


def make_image(filename='btv-mean-temp', fill_null=True,
               smooth_horizontal=True, smooth_vertical=True,
               palette='RdYlBu', bins='8', data_width=2, data_height=4,
               continuity=0.4, recursion=2, start_index=0, save_image=False):

    """Take all arguments and translate station data into a matrix, apply
    various transformations, and generate an image for consumption

    See project README.md for a description of the arguments
    """

    csv_filename = "%s/static/data/%s.csv" % (ABSOLUTE_PATH, filename)

    # Convert data to matrix
    matrix = csv_to_matrix(csv_filename, fill_null, smooth_horizontal,
             smooth_vertical, recursion, start_index)

    # Load colorbrewer palettes from JSON, generate image
    with open('%s/static/colorbrewer.json' % ABSOLUTE_PATH, 'rU') as f:
        colorbrewer = json.load(f)
        try:
            img = matrix_to_image(matrix, colorbrewer[palette][bins][::-1],
                continuity, data_width, data_height)

        # Not all palettes have same number of bins
        except KeyError:

            bins = int(bins)
            while str(bins) not in colorbrewer[palette]:
                bins -= 1
                img = matrix_to_image(matrix,
                    colorbrewer[palette][str(bins)][::-1],
                    continuity, data_width, data_height)


    # Generate a unique name for image
    continuity = str(continuity).replace('.', '_')
    name = '%s-%s-%s-%sx%s%s-%s.png' % (filename, palette, continuity, recursion,
           'no_null' if fill_null else 'null',
           'x' if not smooth_horizontal else '',
           'y' if not smooth_vertical else '')

    return img, name


def csv_to_matrix(csv_filename, fill_null, smooth_horizontal, smooth_vertical,
        recursion, start_index=0):
    """Converts a USHCN csv into a matrix with each row a unique year and each
    value a unique data point"""

    with open(csv_filename, 'rU') as csv_f:
        f = csv.reader(csv_f)
        values = [l for l in f][2:]  # First two lines are headers, not data

    # Get all years in dataset
    years = []
    for value in values:
        if value[4] not in years:
            years.append(value[4])

    # Create matrix of width 366 and height years w/ False as default entry
    matrix = [[False] * 366 for year in years]

    # Here's what we're using below:
    # day[1] = index of day (1-366)
    # day[4] = year
    # day[5] = unit of interest (temp, precip, etc.)

    current_year = values[0][4]  # define first year for comparison in loop
    row_of_matrix = 0
    for value in values:
        if value[4] != current_year:
            current_year = value[4]  # set new year
            row_of_matrix += 1  # update row
        try:
            matrix[row_of_matrix][int(value[1]) - 1] = float(value[-1])
        except ValueError:
            # null values are often listed as '.' in source data, can't
            # convert '.' to float
            matrix[row_of_matrix][int(value[1]) - 1] = False

    # if start_index is given, shift matrix to new start_index
    if start_index:
        matrix = shift_matrix(matrix, start_index)

    # if fill_null, fill all null values
    if fill_null:
        matrix = smooth_nulls(matrix)

    # loops through a smoothing algorithm `recursion` times
    while recursion > 0:
        if smooth_vertical:
            matrix = five_day_averages(matrix, direction="vertical")
        if smooth_horizontal:
            matrix = five_day_averages(matrix)
        recursion -= 1

    return matrix


def matrix_to_image(matrix, palette, continuity, data_width, data_height):
    """Takes a matrix and uses it to generate an image. Each entry in the
    matrix is assigned a region of defined dimensions and its color is
    determined by palette and continuity.
    """

    image_width = data_width * len(matrix[0])
    image_height = data_height * len(matrix)
    img = Image.new('RGB', (image_width, image_height), (0, 0, 0))
    pixels = img.load()

    # define palette and max/min outside of loop
    rgb_palette = [tuple(map(ord, color.decode('hex'))) for color in palette]
    maximum, minimum = find_max_min(matrix)  # needed for color scaling

    # bin width is linear across the entire domain of the matrix
    # number of bins is 1 less than number of colors b/c 2 bins needed to
    # contain 1 bin, just as 2 curbs contain 1 road
    bin_width = (maximum - minimum) / (len(rgb_palette) - 1)

    # Loop through image, pixel by pixel and assign colors
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            value = matrix[(j / data_height)][(i / data_width)]
            color = map_colors(value, rgb_palette, bin_width, minimum,
                    continuity)
            pixels[i, j] = color

    return img


def map_colors(value, rgb, bin_width, minimum, continuity):
    """Maps a value to a color based on the values position in the domain.
    Given a value, a palette, bin width (and number of bins from length of
    palette), the minimum value, and a continuity factor, determines the color
    of the given value"""

    # Determine what bin the value belongs to and where it falls within
    # that bins domain
    bin_idx = int((value - minimum) // bin_width)
    bin_position = ((value - minimum) % bin_width) / bin_width

    # Determing color of lower bounding color (lr,lg,lb) and upper bounding
    # color (ur,ug,ub)
    lr, lg, lb = rgb[bin_idx]
    ur, ug, ub = safe_list_get(rgb, bin_idx + 1, (255, 255, 255))

    # Scale color along spectrum between two thresholds in proportion to
    # continuity. Bin position gives distance from lower threshold value and
    # (continuity * (ur - lr)) limits the palette to some percent of difference
    diff_r = bin_position * (continuity * (ur - lr))
    diff_g = bin_position * (continuity * (ug - lg))
    diff_b = bin_position * (continuity * (ub - lb))

    color = (int(lr + diff_r), int(lg + diff_g), int(lb + diff_b))

    return color


def smooth_nulls(matrix):
    """This function takes a matrix as an input. For any values that meet
    a condition, it averages the value at the same index in both the preceding
    and the following rows and assigns the result as its value"""

    for i, year in enumerate(matrix):
        for j, day in enumerate(year):
            if day is False:
                if i == 0:
                    matrix[i][j] = matrix[i + 1][j]
                elif i + 1 == len(matrix):
                    matrix[i][j] = matrix[i - 1][j]
                else:
                    year_before = matrix[i - 1][j]
                    year_after = matrix[i + 1][j]
                    matrix[i][j] = (year_before + year_after) / 2

    return matrix


def five_day_averages(matrix, direction=False):
    """Takes a matrix and creates a copy of the same dimensions of the
    running average of the values for a five day period."""

    new_matrix = []
    for i, row in enumerate(matrix):
        new_matrix.append([False] * len(row))
        for j, item in enumerate(row):

            if direction == "vertical":
                # Gets the 2 elements above and 2 elements below the value
                # if IndexError, return False
                five_days = [safe_list_get(matrix, i - 2, False, j),
                             safe_list_get(matrix, i - 1, False, j),
                             matrix[i][j],
                             safe_list_get(matrix, i + 1, False, j),
                             safe_list_get(matrix, i + 2, False, j)]

                false_count = sum([1 for v in five_days if v is False])
                new_matrix[i][j] = sum(five_days) / (5 - false_count)

            else:  # direction is horizontal

                # Gets the 2 elements to before and the 2 elements after value
                # returns False if IndexError
                five_days = [safe_list_get(row, j - 2, False),
                             safe_list_get(row, j - 1, False),
                             matrix[i][j],
                             safe_list_get(row, j + 1, False),
                             safe_list_get(row, j + 2, False)]

                false_count = sum([1 for v in five_days if v is False])
                new_matrix[i][j] = sum(five_days) / (5 - false_count)

                ## If first day of year, get values from end of previous year
                #if j == 0:
                #    if i > 0:
                #        if matrix[i - 1][-1] is False:  # True if leap year
                #            five_days.append(matrix[i - 1][-2])
                #            five_days.append(matrix[i - 1][-3])
                #        else:
                #            five_days.append(matrix[i - 1][-1])
                #            five_days.append(matrix[i - 1][-2])
                #        new_matrix[i][j] = sum(five_days) / 5

                #    else:  # if first year in dataset
                #        new_matrix[i][j] = sum(five_days) / 3

                ## If last day of year, get values from beginning of next year
                #elif j + 1 == len(row):
                #    if i + 1 == len(matrix):  # if last year in dataset
                #        new_matrix[i][j] = sum(five_days) / 3
                #    else:
                #        five_days.append(matrix[i + 1][0])
                #        five_days.append(matrix[i + 1][1])
                #        new_matrix[i][j] = sum(five_days) / 5

                ## If 2nd day in year
                #elif j == 1:
                #    if i > 0:
                #        if matrix[i - 1][-1]:
                #            five_days.append(matrix[i - 1][-1])
                #        else:
                #            five_days.append(matrix[i - 1][-2])
                #        new_matrix[i][j] = sum(five_days) / 5
                #    else:
                #        new_matrix[i][j] = sum(five_days) / 4

                ## If 2nd to last day in year
                #elif j + 2 == len(row):
                #    if i + 1 == len(matrix):  # if last year in dataset
                #        new_matrix[i][j] = sum(five_days) / 4
                #    else:
                #        five_days.append(matrix[i + 1][0])
                #        new_matrix[i][j] = sum(five_days) / 5
                #else:
                #    new_matrix[i][j] = sum(five_days) / 5

    return new_matrix


def safe_list_get(matrix, idx, default, second_dimension_idx=None):
    try:
        if second_dimension_idx is not None:
            return matrix[idx][second_dimension_idx]
        else:
            return matrix[idx]
    except IndexError:
        return default


def find_max_min(matrix):
    # start with arbitrary, but valid, first value
    maximum = matrix[0][0]
    minimum = matrix[0][0]

    for i, row in enumerate(matrix):
        for j, column in enumerate(row):
            value = matrix[i][j]
            if value > maximum:
                maximum = value
            elif value < minimum:
                minimum = value

    return maximum, minimum


def shift_matrix(matrix, start_index):
    """Shifts an matrix so a particular index is now 0"""

    new_matrix = [[False] * len(matrix[0]) for i in range(len(matrix))]
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            new_matrix[i][j - start_index] = value

    return new_matrix
