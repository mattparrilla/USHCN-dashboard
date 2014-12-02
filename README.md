#USHCN Data Visualizer

A tool that creates images out of USHCN station data.

**Example:** Daily Mean Temperature in Burlington, VT Since 1940

![Daily Mean Temperature in BTV]
(http://i.imgur.com/G7Whq9W.png)
This image shows the daily mean temperature in Burlington Vermont over the last 73 years. The top left of the image is January 1, 1940 and the bottom right is December 31, 2013. The days of the year progress from left to right and the years progress from top to bottom.

For this particular image, the data has been smoothed and the color palette is a qualitative colorbrewer palette.

##Demo

Coming Soon

##To Do

See project [issues](https://github.com/mattparrilla/csv2png/issues)

##`make_image()` Parameters
`make_image()` takes USHCN station data and turns it into an image.

- `f_n` - the name of the file containing the data (no extension)
- `fill_null` - *a boolean*, should null values be populated by averaging their neighbors?
- `unit` - 'day' or 'month'
- `smooth_horizontal` - *a boolean*, should each value be an average of it and its neighbors (from two days prior to two days after)?
- `smooth_vertical` - *a boolean*, should each value be an average of it and its neighbors (the same day from two years prior to two years after)?
- `palette` - a colorbrewer palette to use
- `bins` - the number of colors to use
- `x_d` - the x-dimension that each individual value will be represented in pixels
- `y_d` - the y-dimension that each individual value will be represented in pixels
- `continuity` - a float between 0 and 1.
This number determines just how continuous the palette looks. If `1`, the palette is perfectly continuous and a data point 50% between bin thresholds will get a color 50% between them. If the factor is `0`, the palette is perfectly discrete and a point 50% between bin thresholds will be set to the lower threshold. If the factor is `0.4` a point 50% between bin thresholds will only be scaled continuously, but on only 40% (0.4) of the difference between the two colors, therefor it would be only 20% of the way from the lower threshold.
- `start_idx` - the day in the year that the image should begin at.
i.e. if `0`, start at Jan 1. If `182` start at July 1, etc.

## Creators

- Matt Parrilla
    - [https://github.com/mattparrilla](https://github.com/mattparrilla)
    - [https://twitter.com/mattparrilla](https://twitter.com/mattparrilla)

- Joe di Stefano
    - [https://github.com/joeydi](https://github.com/joeydi)
    - [https://twitter.com/joeydi](https://twitter.com/joeydi)

## License

The MIT License (MIT)

Copyright (c) 2014 Matt Parrilla, Joe di Stefano

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
