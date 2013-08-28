'''
Created on Oct 21, 2011

@author: bolme
'''

import time
from collections import defaultdict
import cProfile

#############################################################################
# Video tasks are opperations to be run on a frame.
#############################################################################
class VideoTask(object):
    '''
    This provides an interface and support functions for a video processing 
    task.  Typically a subclass will overide the constructor which will 
    be used as a task factory and will create the task and specify the 
    arguments.
    '''
    
    # TODO: optional args should also be added which are included if avalible but will not delay execution if they are not avalible. 
    def __init__(self,frame_id,args=[]):
        '''
        @param frame_id: the frame_id associated with this task.
        @param args: specification of the data that is required to execute the task.
        '''
        self.frame_id = frame_id
        self.args = args
    
    def getFrameId(self):
        '''
        @returns: the frame_id associated with this task.
        '''
        return self.frame_id
    
    def required(self):
        '''
        @returns: the list of required data.
        '''
        return self.args
        
    def execute(self, *args, **kwargs):
        '''
        This is an abstract method that needs to be implemented in subclasses.
        One argument is suppled for each item in the required arguments. This
        method should return a list of new data items.  If no data is 
        generated by this method an empty list should be returned.
        '''
        raise NotImplementedError("Abstract Method")


class _VideoDataItem(object):
    '''
    This class keeps track of data items and when they are used.
    '''
    def __init__(self,data_tuple):
        self._data_type = data_tuple[0] 
        self._frame_id = data_tuple[1]
        self._data = data_tuple[2]
        self._touched = 0
    
    def getType(self):
        ''' Get the item type. '''
        return self._data_type
    
    def getFrameId(self):
        ''' Get the frame id. '''
        return self._frame_id
    
    def getData(self):
        ''' Get the actual data. '''
        return self._data
    
    def getKey(self):
        ''' Get the key. '''
        return (self._data_type,self._frame_id)
    
    def touch(self):
        ''' Count the number of times this data was touched. '''
        self._touched += 1
        
    def getTouched(self):
        ''' Return the number of times the data was touched. '''
        return self._touched


#############################################################################
# This class manages the workflow for video items.
#############################################################################
# TODO: Should we keep this name?
class VideoTaskManager(object):
    '''
    The framework provide by this class will allow complex video processing 
    systems to be constructed from simple tasks.  Often video processing 
    loops can be complicated because data needs to persist across many frame
    and many operations or tasks need to be completed to solve a video analysis
    problem.  This class allows for many small and simple tasks to be managed 
    in a way that can produce a complex and powerful system. #
        
    Tasks request only the data they need, which keeps the complexity of tasks 
    as simple as possible.  This also reduces the coupling between tasks and 
    eliminates complex video processing loops. The video task manager handles 
    much of the complexity of the video processing system like data buffering, 
    and insures that each task gets its required data. #

    This class manages tasks that are run on video frames.  The video task 
    manager maintains a list of data objects and task objects.  Each task is 
    a listener for data objects.  When the data objects are avalible required 
    to execute a task the tasks execute method will be called and the required 
    data items will be passed as arguments. #
    
    New frames are added using the addFrame method.  When a frame is added 
    it creates a data item that includes a frame_id, a data type of "FRAME",
    and a pv.Image that contains the frame data.  Tasks can register to 
    receive that frame data or any data products of other tasks and when
    that data becomes available the task will be executed.
    '''
    
    def __init__(self,debug_level=0, buffer_size=10, show = False):
        '''
        Create a task manager.
        
        @param debug_level: 0=quiet, 1=errors, 2=warnings, 3=info, 4=verbose
        @type debug_level: int
        @param buffer_size: the size of the frame and data buffer.
        @type buffer_size: int
        '''
        self.debug_level = debug_level
        
        # Initialize data.
        self.frame_id = 0
        self.task_list = []
        self.task_factories = []
        self.data_cache = {}
        self.buffer_size = buffer_size
        
        self.frame_list = []
        self.show = show
        
        # Initialize information for flow analysis.
        self.flow = defaultdict(set)
        self.task_set = set()
        self.data_set = set()
        self.task_data = defaultdict(dict)
        
        if self.debug_level >= 3:
            print "TaskManager[INFO]: Initialized"
            

    def addTaskFactory(self,task_factory,*args,**kwargs):
        '''
        This function add a task factory function to the video task manager.
        The function is called once for every frame processed by the 
        VideoTaskManager.  This function should take one argument which
        is the frame_id of that frame.  The task factory should return an
        instance of the VideoTask class that will perform processing on this
        frame.  There are three options for implementing a task factory. #
         - A class object for a VideoTask which has a constructor that takes 
           a frame_id as an argument.  When called the constructor for that 
           class and will create a task.
         - A function that takes a frame id argument.  The function can 
           create and return a task.
         - Any other object that implements the __call__ method which 
           returns a task instance.
         
        Any additional arguments or keyword arguments passed to this 
        to this function will be pased after the frame_id argument
        to the task factory. #
        
        @param task_factory: a function or callible object that returns a task.
        @type  task_factory: callable 
        @param profile: Keyword argument.  If true, profile data will be 
                        generated for each call to this task.
        @type profile: True | False
        '''
        profile = False
        if kwargs.has_key('profile'):
            profile = kwargs['profile']
            del kwargs['profile']
        self.task_factories.append((task_factory,args,kwargs,profile))
        
        
    def addFrame(self,frame,ilog=None):
        '''
        Adds a new frame to the task manager and then start processing.
        
        @param frame: the next frame of video.
        @type  frame: pv.Image 
        '''
        # Add the frame to the data manager
        start = time.time()
        
        frame_data = _VideoDataItem(("FRAME",self.frame_id,frame))
        self.data_cache[frame_data.getKey()] = frame_data
        self._createTasksForFrame(self.frame_id)
        self.frame_list.append(frame_data)
        
        # Run any tasks that can be completed with the current data.
        self._runTasks()
        
        # Delete old data
        self._cleanUp()

        
        stop = time.time()
        
        # Set up for the next frame and display the results.
        self.frame_id += 1

        self.showFrames(ilog=ilog)
        
        if self.debug_level >= 3:
            print "TaskManager[INFO]: Frame Processing Time=%0.3fms"%(1000*(stop-start),)

        
    def _createTasksForFrame(self,frame_id):
        '''
        This calls the task factories to create tasks for the current frame. 
        '''
        start = time.time()
        count = 0
        for factory,args,kwargs,profile in self.task_factories:
            task = factory(frame_id,*args,**kwargs)
            task.profile=profile
            count += 1
            self.task_list += [task]
        stop = time.time() - start
        if self.debug_level >= 3:
            print "TaskManager[INFO]: Created %d new tasks for frame %s. Total Tasks=%d.  Time=%0.2fms"%(count,frame_id,len(self.task_list),stop*1000)

        
    def _runTasks(self):
        '''
        Run any tasks that have all data available.
        '''
        if self.debug_level >= 3: print "TaskManager[INFO]: Running Tasks..."
        while True:
            start_count = len(self.task_list)
            remaining_tasks = []
            for task in self.task_list:
                if self._evaluateTask(task):
                    remaining_tasks.append(task)
            self.task_list = remaining_tasks
            if start_count == len(self.task_list):
                break

            
    def _evaluateTask(self,task):
        '''
        Attempts to run a task.  This is intended to be run within a filter operation.
        
        @returns: false if task should be deleted and true otherwise.
        '''
        self.task_set.add(task.__class__.__name__)
        #print "task check = ",self.frame_id - task.getFrameId(),self.buffer_size
        if self.frame_id - task.getFrameId() > self.buffer_size:
            if self.debug_level >= 2: 
                print "TaskManager[WARNING]: Task %s for frame %d was not executed."%(task,task.getFrameId())
            
            # If the task is beyond the buffer, then delete it.
            return False
        
        # Attempt to fetch the data needed by this task.
        try:
            data_request = task.required()
            # data_items = [self.data_cache[key] for key in data_request]
            data_items = []
            for key in data_request:
                if self.data_cache.has_key(key[:2]):
                    data_items.append(self.data_cache[key[:2]])
                elif len(key) > 2:
                    # Use the default value
                    data_items.append(_VideoDataItem(key))
                else:
                    # Data is not yet available
                    return True
                
            # Create an argument list
            args = [each.getData() for each in data_items]
            
            # Compute the dataflow
            for each in data_items:
                self.flow[(each.getKey()[0],task.__class__.__name__)].add(each.getKey()[1]-task.getFrameId())
                self.data_set.add(each.getKey()[0])

            # Mark these items as touched
            for each in data_items: each.touch()
        except KeyError:
            # Data could not be found so delay execution
            return True
        except:
            # Unexpected exception
            raise
        
        # Run the task.
        start = time.time()
        
        # Start the profiler
        if task.profile:
            prof = cProfile.Profile()
            prof.enable()
            
        # RUN THE TASK
        result = task.execute(*args)
        
        # Stop the profiler and show that information.
        if task.profile:
            prof.disable()
            print
            print "Profiled task:",task.__class__.__name__
            prof.print_stats('time')
            print
            
        # Record the dataflow information.
        for each in result:
            self.flow[(task.__class__.__name__,each[0])].add(0)
            self.data_set.add(each[0])
                
        # Check that the task did return a list.
        try:
            len(result)
        except:
            raise Exception("Task did not return a valid list of data.\n    Task: %s\n    Data:%s"%(task,result))
                            
        # Add the data to the cache.
        for data_item in result:
            if len(data_item) != 3:
                raise Exception("Task returned a data item that does not have 3 elements.\n    Task: %s\n    Data: %s"%(task,data_item))
            key = data_item[:2]
            self.data_cache[key] = _VideoDataItem(data_item)
        stop = time.time() - start
        if self.debug_level >= 3:
            print "TaskManager[INFO]: Evalutate task %s for frame %d. Time=%0.2fms"%(task,task.getFrameId(),stop*1000)
        
        # Compute task statistics
        if not self.task_data[task.__class__.__name__].has_key('time_sum'):
            self.task_data[task.__class__.__name__]['time_sum'] = 0.0
            self.task_data[task.__class__.__name__]['call_count'] = 0
        self.task_data[task.__class__.__name__]['time_sum'] += stop
        self.task_data[task.__class__.__name__]['call_count'] += 1
        
        # Return false so that the task is deleted.
        return False
    
    
    def _remainingTasksForFrame(self,frame_id):
        '''
        @returns: the number of tasks that need to be run for this frame.
        '''
        count = 0
        for task in self.task_list:
            if task.getFrameId() == frame_id:
                count += 1
        return count
    
    def _cleanUp(self):
        '''
        This function deletes old data from the task processor.
        '''
        data_keys = self.data_cache.keys()
        for key in data_keys:
            data_item = self.data_cache[key]
            frame_id = data_item.getFrameId()
            if frame_id < self.frame_id - self.buffer_size:
                # check for unused data items
                if self.debug_level >= 2 and data_item.getTouched() == 0:
                    print "TaskManager[WARNING]: Data item %s for frame %d was created but never used."%(data_item.getType(),data_item.getFrameId())
                
                # delete old data
                del self.data_cache[key]

    # TODO: I don't really like how show frames works.  I would like display of frames to be optional or maybe handled outside of this class.  How should this work.
    def showFrames(self,ilog=None):
        '''
        Show any frames with no remaining tasks.
        '''
        while len(self.frame_list) > 0:
            frame_data = self.frame_list[0]
            frame_id = frame_data.getFrameId()
            frame = frame_data.getData()
            task_count = self._remainingTasksForFrame(frame_id)
            # If the frame is complete then show it.
            if task_count == 0:
                if self.show:
                    frame.show(delay=1)
                if ilog != None:
                    ilog(frame,ext='jpg')
                del self.frame_list[0]
            else:
                break
    
    def asGraph(self,as_image=False):
        '''
        This uses runtime analysis to create a dataflow graph for this VTM.
        '''
        import pydot
        import pyvision as pv
        import PIL.Image
        from cStringIO import StringIO
        
        def formatNum(n):
            '''
            This formats frame offsets correctly: -1,0,+1
            '''
            if n == 0:
                return '0'
            else:
                return "%+d"%n
            
        def record_strings(my_list):
            return '{''}'
            
        # Create the graph.
        graph = pydot.Dot(graph_type='digraph')
        graph.add_node(pydot.Node("Video Input",shape='invhouse',style='filled',fillcolor='#ffCC99'))
        graph.add_edge(pydot.Edge("Video Input","FRAME"))

        # Add task nodes        
        for each in self.task_set:
            call_count = self.task_data[each]['call_count']
            mean_time = self.task_data[each]['time_sum']/call_count
            node_label = "{" + " | ".join([each,
                                       "Time=%0.2fms"%(mean_time*1000.0,),
                                       "Calls=%d"%(call_count,),
                                       ]) + "}"
            graph.add_node(pydot.Node(each,label=node_label,shape='record',style='filled',fillcolor='#99CC99'))

        # Add Data Nodes
        for each in self.data_set:
            graph.add_node(pydot.Node(each,shape='box',style='rounded, filled',fillcolor='#9999ff'))
            
        # Add edges.
        for each,offsets in self.flow.iteritems():
            offsets = list(offsets)
            if len(offsets) == 1 and list(offsets)[0] == 0:
                graph.add_edge(pydot.Edge(each[0],each[1]))
            else:
                offsets.sort()
                offsets = [formatNum(tmp) for tmp in offsets]
                offsets = " ("+",".join(offsets) + ")"
                graph.add_edge(pydot.Edge(each[0],each[1],label=offsets,label_scheme=2,labeldistance=2,labelfloat=False))

        # Create a pv.Image containing the graph.                
        if as_image:
            data = graph.create_png()
            f = StringIO(data)
            im = pv.Image(PIL.Image.open(f))
            return im
        return graph



