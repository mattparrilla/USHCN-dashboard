#!/usr/local/bin/python

from PIL import Image


def array_to_image(array):
    """Take an array of arrays and map it to an image"""

    width = len(array[0])
    height = len(array)

    maximum, minimum = find_max_min(array)

    unit_dimensions = (30, 30)  # to increase size of each data point (w,h)

    img = Image.new('RGB',
        ((unit_dimensions[0] * width), (unit_dimensions[1] * height)), (0, 0, 0))
    pixels = img.load()

    for i in range(img.size[0]):
        for j in range(img.size[1]):
            color = array[(j / unit_dimensions[1])][(i / unit_dimensions[0])]
            pixels[i, j] = (color, color, 100)

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

array_to_image([[2, 100, 30], [50, 60, 70]])
