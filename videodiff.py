### VideoDiff.py
### Using OpenCV To calculate the raw difference in frames
###
### Takes a video file of any supported format
### Outputs a CSV file with the percentage difference between each frame at the timestamp of the frame

### Copyright 2011 Timothy Marks

from cv import *
import time
import tempfile

class Videodiff:

    verbose = False
    window = False
    diffWindow = False
    grayscale = False
    contours = False

    videoFile = None
    outputFile = None
    
    videoProperties = {}
    
    # Holds the default previous frame
    lastFrame = None
    # Holds the default current frame (direct clone or copied to grayscale)
    currentFrame = None
    
    ### Raw diff
    # Holds the black and white copy of the absolute diff
    bwDiffFrame = None
    # Holds the absolute diff of the lastFrame and currentFrame
    diffFrame = None
    # Holds the output if diffWindow is enabled
    displayFrame = None
    
    def __init__(self, videoFile, outputFile):
        self.videoFile = videoFile
        self.outputFile = outputFile
    
    def __init__(self, videoFile, outputFile, options):
        self.videoFile = videoFile
        self.outputFile = outputFile
        # Parse the options to get the runtime flags
        self.verbose = options.verbose
        self.window = options.window
        self.diffWindow = options.diffWindow
        self.grayscale = options.grayscale
        self.contours = options.contours
    
    # Internal function to parse the video properties
    def parseVideoProperties(self, video):
        # Get video properties
        self.videoProperties['fps'] = GetCaptureProperty(video, CV_CAP_PROP_FPS)
        self.videoProperties['width'] = int(GetCaptureProperty(video, CV_CAP_PROP_FRAME_WIDTH))
        self.videoProperties['height'] = int(GetCaptureProperty(video, CV_CAP_PROP_FRAME_HEIGHT))
        self.videoProperties['frames'] = int(GetCaptureProperty(video, CV_CAP_PROP_FRAME_COUNT))            
        self.vLog("Video Details: fps=%d, width=%d, height=%d, totalFrames = %d" % (self.videoProperties['fps'], self.videoProperties['width'], self.videoProperties['height'], self.videoProperties['frames']))
    
    # Internal function to get the percentage difference of the diffed frame
    def rawDiff(self):
        
        AbsDiff(self.currentFrame, self.lastFrame, self.diffFrame)
            
        # We need the diff frame to be black and white
        if self.grayscale:
            # No need to convert so just take a copy
            self.bwDiffFrame = CloneImage(self.diffFrame)
        else:
            # The diff is in color so convert it to grayscale
            CvtColor(self.diffFrame, self.bwDiffFrame, CV_RGB2GRAY)
        
        # We want to measure a difference as binary (difference/no difference)
        # Therefore we need to threshold the grayscale image into only black and white
        Threshold(self.bwDiffFrame, self.bwDiffFrame, 30, 255, CV_THRESH_BINARY)

        # Need a reference to the last frame for diff comparison
        self.lastFrame = CloneImage(self.currentFrame)
        
        if self.diffWindow:
            Merge(self.bwDiffFrame, self.bwDiffFrame, self.bwDiffFrame, None, self.displayFrame)
        
        # Get the percentage of the image with motion
        # Not very smart algorithm, basically check every pixel between frames
        # A white pixel means that the pixel differed between frames
        # Black means the pixels where the exact same
        pixelsDiff = 0
        matrix = GetMat(self.bwDiffFrame)
        rows = matrix.rows
        cols = matrix.cols
        for i in xrange(0, rows):
            for j in xrange (0, cols):
                rgb = Get2D(matrix, i, j)
                if (rgb[0] == 255.0):
                    pixelsDiff += 1

        # Total motion percentage is the count of pixels changed out of the total number of pixels
        percentDiff = (float(pixelsDiff) / (matrix.rows * matrix.cols)) * 100.0
        
        return percentDiff
    
    def contourDiff(self):
    
        # Do a contour analysis of the current diff
        storage = CreateMemStorage(0);
        contours = FindContours(self.bwDiffFrame, storage,
                CV_RETR_EXTERNAL, CV_CHAIN_APPROX_SIMPLE, (0, 0))

        while contours != None and len(contours) > 0:
            bndRect = BoundingRect(contours, 0);
            (x, y, width, height) = bndRect
            if self.diffWindow:
            	# Draw contours into the diff window
                Rectangle(self.displayFrame, (x, y), (x+width, y+height), (0, 0, 255), 3)
            if self.window:
            	# Draw contours into the current default frame
                Rectangle(self.currentFrame, (x, y), (x+width, y+height), (0, 0, 255), 3)
            contours = contours.h_next()
    
    # Perform a diff on the video and output the results
    def diffVideo(self):
        try:
            video = CaptureFromFile(self.videoFile)
        except:
            print "Could not open the provided video file"
            raise
        
        # Extract the video properties to setup the frame
        self.parseVideoProperties(video)
        
        # Create the single channel bw diff frame
        self.bwDiffFrame = CreateImage( (self.videoProperties['width'], self.videoProperties['height']), IPL_DEPTH_8U, 1)
        
        if self.grayscale:
            # Grayscale requires different types of frames (single channel)
            self.lastFrame = CreateImage( (self.videoProperties['width'], self.videoProperties['height']), IPL_DEPTH_8U, 1)
            self.currentFrame = CreateImage( (self.videoProperties['width'], self.videoProperties['height']), IPL_DEPTH_8U, 1)
            self.diffFrame = CreateImage( (self.videoProperties['width'], self.videoProperties['height']), IPL_DEPTH_8U, 1)
            
        else:
            # Need 3 color channels to do a color comparison
            self.lastFrame = CreateImage( (self.videoProperties['width'], self.videoProperties['height']), IPL_DEPTH_8U, 3)
            self.currentFrame = CreateImage( (self.videoProperties['width'], self.videoProperties['height']), IPL_DEPTH_8U, 3)
            self.diffFrame = CreateImage( (self.videoProperties['width'], self.videoProperties['height']), IPL_DEPTH_8U, 3)
        
        # This frame holds the diffed display information
        self.displayFrame = CreateImage( (self.videoProperties['width'], self.videoProperties['height']), IPL_DEPTH_8U, 3)
    
        frameCount = 0
        
        if self.window:
            # Create a named window to output the original file in
            NamedWindow("Original", 0)
        
        if self.diffWindow:
            # Create a named window to output the diffed frames
            NamedWindow("Diff", 0)
        
        # Prewrite the first frame with diff 0 as the first frame can't be compared
        f = open(self.outputFile, 'w')
        f.write('0.0,0.0\r\n')
        lastPercentageProcessed = 0
        
        while True:
            
            # Loop over the entire video and get each frame
            frame = QueryFrame(video)
            
            if (frame == None):
                # Reached an invalid frame or the end of the file
                break
            
            if frameCount == 0:
                # First frame so we can't make a comparison, store for next frame
                
                # Blur to reduce camera noise
                Smooth(frame, frame, CV_BLUR, 3)
                
                if self.grayscale:
                    # Convert the frame to grayscale for comparison
                    CvtColor(frame, self.lastFrame, CV_RGB2GRAY)
                else:
                    # Keep original frame
                    self.lastFrame = CloneImage(frame)
                frameCount += 1
                continue
            
            # Blur to reduce camera noise
            Smooth(frame, frame, CV_BLUR, 3)
            
            if self.grayscale:
                # Convert the frame to grayscale for comparison
                CvtColor(frame, self.currentFrame, CV_RGB2GRAY)
            else:
                # Keep original frame
                self.currentFrame = CloneImage(frame)
            
            
            #### Do a very simple raw pixel diff analysis
            
            # Generate the diffed image
            percentDiff = self.rawDiff()
    
            # Do a contour analysis
            if self.contours:
                self.contourDiff()
    
            # Calculate the timestamp of the frame
            timeStamp = GetCaptureProperty(video, CV_CAP_PROP_POS_MSEC) / 1000.0
            
            self.vLog("%f,%f" % (timeStamp, percentDiff))
            
            # Write the percentage difference out to the csv with the timestamp of the frame
            f.write("%f,%f\r\n" % (timeStamp, percentDiff))
            frameCount += 1
            
            # Calculate the amount of video currently processed
            percentageProcessed = (frameCount / (self.videoProperties['frames'] * 1.0)) * 100.0
            percentageProcessed = int(percentageProcessed)
            if (percentageProcessed != lastPercentageProcessed):
                self.vLog("%d" %(percentageProcessed))
                lastPercentageProcessed = percentageProcessed
                
            if self.window:  
                ShowImage("Original", self.currentFrame)
            if self.diffWindow:
                ShowImage("Diff", self.displayFrame)
            
    
        # Flush and close the output file
        f.flush()
        f.close()
        
    def vLog(self, message):
        if self.verbose:
            print message
