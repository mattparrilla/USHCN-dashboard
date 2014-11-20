#!/usr/local/bin/python

from PIL import Image
import csv
import json

with open('colorbrewer.json', 'rU') as f:
    colorbrewer = json.load(f)


def make_image(f_n='btv', fill_null=True,
               unit='day', smooth_horizontal=False, smooth_vertical=False,
               palette='Set1', bins='3', x_d=2, y_d=4, continuity=0,
               recursion=0, start_idx=False, save_image=False):

    """This function generates an image from a matrix, which is then passed to
    the view as a string. All image parameters are defined here."""

    csv_f = "data/%s.csv" % f_n  # The path to the data

    # Take data and convert it into a matrix
    matrix = csv_to_matrix(csv_f, unit, fill_null, smooth_horizontal,
             smooth_vertical, recursion, start_idx)

    # Transform matrix into image
    dimensions = (int(x_d), int(y_d))  # each entry's pixel dimensions
    img = matrix_to_image(matrix, colorbrewer[palette][bins],
          continuity, dimensions)

    # TODO: use this to suggest the default filename when downloading file
    # also: improve the name, make it more useful
    continuity = str(continuity).replace('.', '_')
    name = '%s-%s-%s-%sx%s%s-%s.png' % (f_n, palette, continuity, recursion,
           'no_null' if fill_null else 'null',
           'x' if not smooth_horizontal else '',
           'y' if not smooth_vertical else '')

    return img, name


def matrix_to_image(matrix, palette, continuity, dimensions):
    """Takes a matrix and uses it to generate an image. Each entry in the
    matrix is assigned a region of defined dimensions and its color is
    determined by palette and continuity.

    dimensions: a tuple that defines the size of each data point (i.e. (2, 4)
    means each data point will be 2px wide and 4px tall in the final image.

    palette: an array of hex colors (i.e. ['000000', 'ffffff']).
    The length of the array determines the number of bins (n - 1). Entries are
    split into bins and then assigned a color from the palette.

    continuity: a float between 0 and 1.
    This number determines just how continuous the palette looks. If 1, the
    palette is perfectly continuous and a data point 50% between bin thresholds
    will get a color 50% between them. If the factor is 0, the palette is
    perfectly discrete and a point 50% between bin thresholds will be set to
    the lower threshold. If the factor is 0.4 a point 50% between bin
    thresholds will only be scaled continuously, but on only 40% (0.4) of the
    difference between the two colors, therefor it would be only 20% of the way
    from the lower threshold.
    """

    # Get matrix attributes
    width = dimensions[0] * len(matrix[0])
    height = dimensions[1] * len(matrix)
    maximum, minimum = find_max_min(matrix)

    img = Image.new('RGB', (width, height), (0, 0, 0))
    pixels = img.load()

    # define colors, bin size outside of loop
    rgb_palette = [tuple(map(ord, color.decode('hex'))) for color in palette]
    bin_width = (maximum - minimum) / (len(rgb_palette) - 1)

    for i in range(img.size[0]):
        for j in range(img.size[1]):
            temp = matrix[(j / dimensions[1])][(i / dimensions[0])]

            # TODO: figure out how to color null values or if we even should
            # (maybe more useful to fill_null?)

            # if temp is False:
            #     pixels[i, j] = (255, 0, 0)
            # else:

            color = map_colors(temp, rgb_palette, bin_width, minimum,
                    continuity)

            pixels[i, j] = color

    return img


def map_colors(value, rgb, bin_width, minimum, continuity):
    """Maps a value to a color based on the values position in the domain.
    Given a value, a palette, bin width (and number of bins from length of
    palette, the minimum value, and a continuity factor, determines the color
    of the given value"""

    # What bin is the value in, and where does it fall within the bin's domain?
    bin_idx = int((value - minimum) // bin_width)
    bin_position = ((value - minimum) % bin_width) / bin_width

    # What is color of lower (r,g,b) and upper (nr,ng,nb) thresholds?
    r, g, b = rgb[bin_idx]
    nr, ng, nb = safe_list_get(rgb, bin_idx + 1, (255, 255, 255))

    # Scale color along spectrum between two thresholds in prop. to continuity
    # bin position gives distance from lower threshold value
    # (continuity * (nr - r)) limits the palette to some percent of difference
    diff_r = bin_position * (continuity * (nr - r))
    diff_g = bin_position * (continuity * (ng - g))
    diff_b = bin_position * (continuity * (nb - b))

    color = (int(r + diff_r), int(g + diff_g), int(b + diff_b))

    return color


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


def csv_to_matrix(csv_f, unit, fill_null, smooth_horizontal, smooth_vertical,
        recursion, start_idx=False):
    """Converts a USHCN csv into a matrix with each row a unique year and each
    value a unique data point"""

    with open(csv_f, 'rU') as csv_file:
        f = csv.reader(csv_file)
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

    matrix = [[False] * length for year in years]

    # Here's what we're using below:
    # day[1] = index of day (1-366)
    # day[4] = year
    # day[5] = temperature

    last_year = values[0][year_idx]  # define first year for comparison in loop
    row_of_matrix = 0
    for value in values:
        if value[year_idx] != last_year:
            last_year = value[year_idx]  # set new year
            row_of_matrix += 1  # update row
        try:
            matrix[row_of_matrix][int(value[unit_idx]) - 1] = float(value[-1])
        except:
            pass

    #del matrix[:20]
    if start_idx:
        matrix = shift_matrix(matrix, start_idx)

    if fill_null:
        matrix = smooth_nulls(matrix)

    while recursion > 0:
        if smooth_vertical:
            matrix = five_day_averages(matrix, direction="vertical")
        if smooth_horizontal:
            matrix = five_day_averages(matrix)
        recursion -= 1

    return matrix


def shift_matrix(matrix, start_idx):
    """Shifts an matrix so a particular index is now 0"""

    dimensions = (len(matrix[0]), len(matrix))
    new_matrix = [[False] * dimensions[0] for i in range(len(matrix))]
    for i, row in enumerate(matrix):
        for j, value in enumerate(row):
            new_matrix[i][j - start_idx] = value

    return new_matrix


def smooth_nulls(matrix):
    """This function takes a matrix as an input. For any values that meet
    a condition, it averages the value at the same index in both the preceding
    and the following rows and assigns the result as its value"""

    for i, year in enumerate(matrix):
        for j, day in enumerate(year):
            if day is False:  # FIX: ideally this will be False, not zero
                try:
                    year_before = matrix[i - 1][j]
                    year_after = matrix[i + 1][j]
                    matrix[i][j] = (year_before + year_after) / 2
                except IndexError:
                    # this will throw IndexError on first and last year
                    if i == 0:
                        matrix[i][j] = matrix[i + 1][j]
                    elif i > 0:
                        matrix[i][j] = matrix[i - 1][j]

    return matrix


def five_day_averages(matrix, direction=False):
    """Takes a matrix and creates a copy of the same dimensions of the
    running average of the values for a five day period."""

    new_matrix = []
    for i, row in enumerate(matrix):
        new_matrix.append([False] * len(row))
        for j, item in enumerate(row):
            if direction is "vertical":
                # Builds an matrix of the value on this date over the surrounding five years
                five_days = [safe_list_get(matrix, i - 2, False, j),
                             safe_list_get(matrix, i - 1, False, j),
                             matrix[i][j],
                             safe_list_get(matrix, i + 1, False, j),
                             safe_list_get(matrix, i + 2, False, j)]
                if i == 0 or i + 1 == len(matrix):
                    new_matrix[i][j] = sum(five_days) / 3
                elif i == 1 or i + 2 == len(matrix):
                    new_matrix[i][j] = sum(five_days) / 4
                else:
                    new_matrix[i][j] = sum(five_days) / 5
            else:
                # Builds an matrix of the value on this surrounding five days
                five_days = [safe_list_get(row, j - 2, False),
                             safe_list_get(row, j - 1, False),
                             matrix[i][j],
                             safe_list_get(row, j + 1, False),
                             safe_list_get(row, j + 2, False)]
                new_matrix[i][j] = sum(five_days) / 5

                # TODO: Consider beginning and end of year

    return new_matrix


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
