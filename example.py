### VideoDiff.py
### Using OpenCV To calculate the raw difference in frames
###
### Example Usage

### Copyright 2011 Timothy Marks

import sys
from optparse import OptionParser

from videodiff import Videodiff

if __name__ == "__main__":
    
    parser = OptionParser()
    parser.add_option("-g", "--grayscale", 
                  action="store_true", dest="grayscale", default=False,
                  help="compare the frames in grayscale instead of color")
    parser.add_option("-v", "--verbose",
                  action="store_true", dest="verbose", default=False,
                  help="print status messages to stdout")
    parser.add_option("-w", "--window",
                  action="store_true", dest="window", default=False,
                  help="show a window output of the original file")
    parser.add_option("-d", "--diff",
                  action="store_true", dest="diffWindow", default=False,
                  help="show a window output of the diffed frame")
    parser.add_option("-c", "--contours",
                  action="store_true", dest="contours", default=False,
                  help="show contour analysis rectangles on the output display")

    (options, args) = parser.parse_args()
    
    if len(args) != 2:
        parser.print_help()
        sys.exit(0)
    
    diff = Videodiff(args[0], args[1], options)
    diff.diffVideo()
