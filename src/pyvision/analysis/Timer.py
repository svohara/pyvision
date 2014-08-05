import time
import pyvision as pv

class Timer:
    '''
    A simple timer class used to measure and record run times.  Each timer has a
    member variable named table which keeps a log of timing data.
    
    Usage:
    timer = pv.Timer()
    
    ... Do Some Stuff ...
    
    timer.mark("Event 1")
    
    ... Do Some Stuff ...
    
    timer.mark("Event 2")
    
    print timer
    -- or --
    ilog(timer,"TimingData")
    
    '''
    def __init__(self, compact=False, format_str=None):
        '''
        Create and setup the timer.  Also creates a mark titled "Timer Created".
        @param compact: If True, then timer will not store cpu_time, cpu_current,
        and cpu_total fields, thus making a more compact table. Else (default)
        all six time fields are stored, wall-clock and cpu-clock.
        @param format_str: For each entry in the timer's table, the relevant
        time field (e.g., cpu_current) will be formatted with this mask. All the
        fields are of type float, so use a new-style string formatting mask that takes
        exactly one float, for example format_str="{:0.3f}".
        Default is None, meaning no special formatting.
        '''
        self.table = pv.Table()
        self.started = False
        self.i = 0
        self.compact = compact
        self.format_str = format_str
        self.mark("Timer Created")
                
    def mark(self,event,notes=None):
        '''
        @param event: a short text description of the event being marked.
        @param notes: additional notes for this event.
        @returns: 6-tuple of times in seconds: Wall Clock Time, Time since last mark, Time since creation, CPU time, CPU time since last mark, CPU time since creation
        '''
        current = time.time()
        cpu = time.clock()
        if self.started == False:
            self.started = True
            self.prev = self.start = current
            self.cpu_prev = self.cpu_start = cpu
        
        #compute the 6 time fields
        rt = current
        ct = current - self.prev
        tot = current - self.start
        crt = cpu
        cct = cpu - self.cpu_prev
        ctot = cpu - self.cpu_start
        
        #Construct the table
        if self.compact:
            time_fields = { (1,"time"):rt, (2,"current"):ct, (3,"total"):tot}
        else:
            time_fields = { (1,"time"):rt, (2,"current"):ct, (3,"total"):tot, 
                           (4,"cpu_time"):crt, (5,"cpu_current"):cct, (6,"cpu_total"):ctot}
            
        self.table[self.i,"event"]   = event
        for (ix,field_name) in sorted(time_fields.keys()):
            #ix used to force sort order
            val = time_fields[(ix,field_name)]
            self.table[self.i, field_name] = self.format_str.format(val) if self.format_str else val
        self.table[self.i,"notes"] = notes
        
        #update internal fields
        self.prev = current
        self.cpu_prev = cpu
        self.i += 1
        
        return rt,ct,tot,crt,cct,ctot
        
    def __str__(self):
        '''Render the timing log to a string.'''
        
        return self.table.__str__()
    
    def save(self,filename):
        '''Save the timing log to a csv file.'''
        self.table.save(filename)
        
