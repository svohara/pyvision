# PyVision License
#
# Copyright (c) 2006-2011 David S. Bolme
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

@author: bolme
'''

import pyvision as pv
import cv2.cv as cv
import PIL.Image as pil

def null_callback(*args,**kwargs):
    pass

class CaptureClicks:
    '''
    This object handles the data mangagement and display of the capture clicks window.
    '''
    
    def __init__(self,im,default_points=[],keep_window_open = False,
                 window="PyVision Capture Points", pos=None):
        '''
        Initialize the data.
        '''
        self.window = window
        self.im = im.copy()
        self.keep_window_open = keep_window_open
        self._userquit = False
        self.pos = pos #position of window
        self.reset()
        for pt in default_points:
            self.mouseCallback(cv.CV_EVENT_LBUTTONDOWN,pt.X(),pt.Y(),None,None)
            
    def display(self):
        '''
        Display the window and run the main event loop.
        '''
        # Setup the mouse callback to handle mause events (optional)
        cv.NamedWindow(self.window)
        if self.pos:
            cv.MoveWindow(self.window, *self.pos)
        cv.SetMouseCallback(self.window, self.mouseCallback)
        
        while True:
            key_press = self.im.show(self.window,delay=100)
            
            # Handle key press events.
            if key_press == ord(' '):
                break
            
            if key_press == ord('q'):
                self._userquit = True
                break
            
            if key_press == ord('r'):
                self.reset()
                
        if not self.keep_window_open:
            cv.DestroyWindow(self.window)
            
        return self.points
                
    def reset(self):
        '''
        Clear the points and start over.
        '''
        self.im = self.im.copy()
        self.im.annotateLabel(pv.Point(10,10), "Click anywhere in the image to select a point.",color='yellow')
        self.im.annotateLabel(pv.Point(10,20), "Press the 'r' to reset.",color='yellow')
        self.im.annotateLabel(pv.Point(10,30), "Press the space bar when finished.",color='yellow')
        self.points = []
        
            
    def mouseCallback(self, event, x, y, flags, param):
        '''
        Call back function for mouse events.
        '''
        if event in [cv.CV_EVENT_LBUTTONDOWN]:
            point = pv.Point(x,y)
            self.im.annotateLabel(point,str(len(self.points)),mark='below')
            self.points.append(point)
        
class CaptureClicksVideo:
    '''
    This object handles the data mangagement and display of the capture clicks window.
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
        # Setup the mouse callback to handle mause events (optional)
        cv.NamedWindow("PyVision Capture Points")
        if self.pos:
            cv.MoveWindow("PyVision Capture Points", *self.pos)
        # This next line creates a memory leak where 'self' is never released
        # and the window cannot be closed.
        cv.SetMouseCallback("PyVision Capture Points", self.mouseCallback)
        
        
        while True:
            key_press = self.im.show("PyVision Capture Points",delay=100)
            
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
