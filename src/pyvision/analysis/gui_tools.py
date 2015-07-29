# PyVision License
#
# Copyright (c) 2006-2011 David S. Bolme and Stephen O'Hara
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
# notice, this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
# 
# 3. Neither name of copyright holders nor the names of its contributors
# may be used to endorse or promote products derived from this software
# without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

'''
Created on Oct 31, 2011

@author: bolme and sohara
Original version by David Bolme.
Modified 2014 by Stephen O'Hara to support additional capabilities,
and an addition of an interface to capture polygons.
'''

import pyvision as pv
import cv2.cv as cv
import PIL.Image as pil

def null_callback(*args,**kwargs):
    pass

class CaptureClicks:
    '''
    This object handles the data management and display of the capture clicks window.
    '''
    
    def __init__(self,im,default_points=[],keep_window_open = False,
                 window="PyVision Capture Points", pos=None):
        '''
        Initialize the data.
        '''
        self.window = window
        self.im = im
        self.keep_window_open = keep_window_open
        self._userquit = False
        self.pos = pos #position of window
        self.current_points = []
        self.default_points = default_points
        self._showHelp = True
        
    def _clearLastPoint(self):
        if self.current_points:
            _ = self.current_points.pop()  #remove most recent element from list and discard
        return
    
    def _drawInstructions(self, canvas):
        canvas.annotateRect(pv.Rect(2,2,300,70), fill_color="white", alpha=0.25)
        canvas.annotateLabel(pv.Point(10,10), "Click anywhere in the image to select a point.",color='yellow')
        canvas.annotateLabel(pv.Point(10,20), "Press 'r' to reset.", color='yellow')
        canvas.annotateLabel(pv.Point(10,30), "Press 'x' to delete the recent point.",color='yellow')
        canvas.annotateLabel(pv.Point(10,40), "Press the space bar when finished.",color='yellow')
        canvas.annotateLabel(pv.Point(10,50), "Press 'h' to toggle display of this help text.", color='yellow')
    
    def _updateImage(self):
        '''
        Renders the annotations on top of the current image
        '''
        canvas = self.im.copy() #won't copy annotations
        if self._showHelp: self._drawInstructions(canvas)
        for idx,pt in enumerate(self.default_points):
            canvas.annotateLabel(pt,str(idx+1),mark='below', color='yellow')
        for idx,pt in enumerate(self.current_points):
            canvas.annotateLabel(pt, str(idx+1+len(self.default_points)), mark='below', color='red')
        self.canvas = canvas
       
    def display(self):
        '''
        Display the window and run the main event loop.
        '''
        # Setup the mouse callback to handle mouse events (optional)
        cv.NamedWindow(self.window)
        if self.pos:
            cv.MoveWindow(self.window, *self.pos)
        cv.SetMouseCallback(self.window, self.mouseCallback)
        
        while True:
            self._updateImage()
            key_press = self.canvas.show(self.window,delay=100)
            key_press = key_press % 256 
            
            # Handle key press events.
            if key_press == ord(' '):
                break
            
            if key_press == ord('h'):
                self._showHelp = not self._showHelp
            
            if key_press == ord('q'):
                self._userquit = True
                break
            
            if key_press == ord('x'):
                self._clearLastPoint()
            
            if key_press == ord('r'):
                self.reset()
                
        if not self.keep_window_open:
            cv.DestroyWindow(self.window)
            
        #self._showHelp = True
        all_points = self.default_points + self.current_points
        return all_points
                
    def reset(self):
        '''
        Clear the points and start over.
        '''
        self.current_points = []
            
    def mouseCallback(self, event, x, y, flags, param):
        '''
        Call back function for mouse events.
        '''
        if event in [cv.CV_EVENT_LBUTTONDOWN]:
            point = pv.Point(x,y)
            self.current_points.append(point)
        
class CapturePolygons(CaptureClicks):
    '''
    This object handles the data management and display of the capture polygons window.
    '''
    
    def __init__(self,im,default_polygons=[],keep_window_open = False,
                 window="PyVision Capture Polygons", pos=None):
        '''
        Initialize the data.
        '''
        CaptureClicks.__init__(self, im, default_points=[], keep_window_open=keep_window_open,
                                window=window, pos=pos)
        
        self.default_polygons = default_polygons #polygons that were input and must always show
        self.current_polygons = [] #completed, closed polygons
        
    def _closePolygon(self):
        if len(self.current_points) >= 3:
            #must have 3 points to close the polygon
            new_poly = self.current_points
            self.current_polygons.append(new_poly)
            self.current_points = []
        return
    
    def _clearLastPoint(self):
        if self.current_points:
            _ = self.current_points.pop()  #remove most recent element from list and discard
        return
    
    def _drawInstructions(self, canvas):
        canvas.annotateRect(pv.Rect(2,2,300,80), fill_color="white", alpha=0.25)
        canvas.annotateLabel(pv.Point(10,10), "Click anywhere in the image to select a point.",color='yellow')
        canvas.annotateLabel(pv.Point(10,20), "Press 'r' to reset.", color='yellow')
        canvas.annotateLabel(pv.Point(10,30), "Press 'x' to delete the recent point.",color='yellow')
        canvas.annotateLabel(pv.Point(10,40), "Press 'c' to close the in-progress polygon.",color='yellow')
        canvas.annotateLabel(pv.Point(10,50), "Press the space bar when finished.",color='yellow')
        canvas.annotateLabel(pv.Point(10,60), "Press 'h' to toggle display of this help text.", color='yellow')
    
    def _updateImage(self):
        '''
        Renders the annotations on top of the current image
        '''
        canvas = self.im.copy() #won't copy annotations
        if self._showHelp: self._drawInstructions(canvas)
        for idx,p in enumerate(self.default_polygons):
            canvas.annotatePolygon(p, color='yellow', width=3, fill=None)
            canvas.annotateLabel(p[0], label=str(idx+1), color='yellow', mark='below')
        for idx,p in enumerate(self.current_polygons):
            canvas.annotatePolygon(p, color='red', width=3, fill=None)
            canvas.annotateLabel(p[0], label=str(idx+1+len(self.default_polygons)), 
                                 color='red', mark='below')
        if self.current_points:
            canvas.annotatePoints(self.current_points, color='blue')
        if len(self.current_points) > 1:
            #draw lines connecting the in-progress points of a new polygon
            for idx in range(1,len(self.current_points)):
                canvas.annotateLine(self.current_points[idx], self.current_points[idx-1],
                                      color='blue', width=2)
        self.canvas = canvas
    
    def display(self):
        '''
        Display the window and run the main event loop.
        '''
        # Setup the mouse callback to handle mouse events (optional)
        cv.NamedWindow(self.window)
        if self.pos:
            cv.MoveWindow(self.window, *self.pos)
        cv.SetMouseCallback(self.window, self.mouseCallback)
        
        while True:
            self._updateImage()
            key_press = self.canvas.show(self.window,delay=100)
            key_press = key_press % 256
            
            # Handle key press events.
            if key_press == ord(' '):
                break
            
            if key_press == ord('h'):
                self._showHelp = not self._showHelp
            
            if key_press == ord('q'):
                self._userquit = True
                break
                
            if key_press == ord('c'):
                self._closePolygon()
                
            if key_press == ord('x'):
                self._clearLastPoint()
            
            if key_press == ord('r'):
                self.reset()
                
        if not self.keep_window_open:
            cv.DestroyWindow(self.window)
            
        #self._showHelp = True
        all_polys = self.default_polygons + self.current_polygons
        return all_polys
           
    def reset(self):
        '''
        Clear the points and start over.
        '''
        self.current_points = []
        self.current_polygons = []

            
class CaptureClicksVideo:
    '''
    This object handles the data management and display of the capture clicks window.
    '''
    
    def __init__(self, video, buffer_size = 60, callback = None, 
                 keep_window_open=False, pos=None):
        '''
        Initialize the data.
        '''
        self.callback = callback
        self.video = video
        self.points = {}
        self.buffer = []
        self.frame = -1
        self.buffer_index = -1
        self.buffer_size = buffer_size
        self.keep_window_open = keep_window_open
        self.pos = pos
        self.next()
        
        
    def display(self):
        '''
        Display the window and run the main event loop.
        '''
        # Setup the mouse callback to handle mouse events (optional)
        cv.NamedWindow("PyVision Capture Points")
        if self.pos:
            cv.MoveWindow("PyVision Capture Points", *self.pos)
        # This next line creates a memory leak where 'self' is never released
        # and the window cannot be closed.
        cv.SetMouseCallback("PyVision Capture Points", self.mouseCallback)
        
        
        while True:
            key_press = self.im.show("PyVision Capture Points",delay=100)
            key_press = key_press % 256
            
            # Handle key press events.
            if key_press == ord('r'):
                self.reset()

            if key_press == ord('p'):
                self.prev()

            if key_press == ord('P'):
                for _ in range(10):
                    self.prev()
                
            if key_press == ord(' ') or key_press == ord('n'):
                self.next()

            if key_press == ord('N'):
                for _ in range(10):
                    self.next()
                
            if key_press == ord('q'):
                break
                
        # Reduce but does not eliminate the memory leak.
        del self.buffer
        
        if not self.keep_window_open:
            cv.DestroyWindow("PyVision Capture Points")
        
        return self.points
            
    def reset(self):
        if self.points.has_key(self.frame):
            del self.points[self.frame]
            self.render()
            
    def render(self):
        '''
        Clear the points and start over.
        '''
        im = self.buffer[self.buffer_index]
        w,h = im.size
        nim = pil.new('RGB',(w,h+100))
        nim.paste(im.asPIL(),(0,0))
        self.im = pv.Image(nim)
        
        if self.callback != None:
            self.callback(self.im,self.frame)
        
        self.im.annotateLabel(pv.Point(10,h+10), "Frame: %d"%self.frame,color='yellow')
        self.im.annotateLabel(pv.Point(10,h+20), "Click anywhere in the image to select a point.",color='yellow')
        self.im.annotateLabel(pv.Point(10,h+30), "Press 'r' to reset.",color='yellow')
        self.im.annotateLabel(pv.Point(10,h+40), "Press the space bar or 'n' for the next frame.",color='yellow')
        self.im.annotateLabel(pv.Point(10,h+50), "Press 'p' for the previous frame.",color='yellow')
        self.im.annotateLabel(pv.Point(10,h+60), "Press 'N' or 'P' to skip 10 frames.",color='yellow')
        self.im.annotateLabel(pv.Point(10,h+70), "Press 'q' when finished.",color='yellow')
        if self.points.has_key(self.frame):
            points = self.points[self.frame]
            for i in range(len(points)):
                pt = points[i]
                self.im.annotateLabel(pt,'%d'% i,mark='below')
        
    def next(self):
        if self.buffer_index == -1:
            try:
                self.buffer.append(self.video.next())
                self.frame += 1
            except StopIteration:
                print "End of video."
            self.buffer = self.buffer [-self.buffer_size:]
        else:
            self.buffer_index += 1
            self.frame += 1

        print self.buffer_index,self.frame,len(self.buffer),self.points
        self.render()
        
    
    def prev(self):
        if self.buffer_index == -len(self.buffer):
            print "Buffer exceed. Cannot display previous frame"
        else:
            self.buffer_index -= 1
            self.frame -= 1
        self.render()
        
            
    def mouseCallback(self, event, x, y, flags, param):
        '''
        Call back function for mouse events.
        '''
        if event in [cv.CV_EVENT_LBUTTONDOWN]:
            if not self.points.has_key(self.frame):
                self.points[self.frame] = []
            points = self.points[self.frame]
            point = pv.Point(x,y)
            self.im.annotateLabel(point,str(len(points)),mark='below')
            points.append(point)
        
def capturePointsFromMouse(im,*args,**kwargs):
    '''
    This function opens a high gui window that displays the image.  Any 
    points that are clicked will be returned after the user presses the 
    space bar.
    
    @param im: An image to display.
    @returns: a list of points that were clicked by the user.
    '''
    if isinstance(im, pv.Image):
        cap = CaptureClicks(im,*args,**kwargs)
        clicks = cap.display()
    else:
        cap = CaptureClicksVideo(im,*args,**kwargs)
        clicks = cap.display()
    return clicks


if __name__ == '__main__':
    #im = pv.Image(pv.TAZ_IMAGE)
    #pv.capturePointsFromMouse(im)
    
    video = pv.Video(pv.TAZ_VIDEO)
    ccv = capturePointsFromMouse(video)
