#!/usr/bin/python
# -*- coding: utf-8 -*-
"""nmapps.trace module.

Author: Jan Milik <milikjan@fit.cvut.cz>
"""


import sys


class TraceSection(object):
    def __init__(self, trace, title):
        self.trace = trace
        self.title = title
    
    def __enter__(self):
        pass
    
    def __exit__(self):
        self.trace.unwind_section(self)


class Trace(object):
    def __init__(self, name):
        self.name = name
        
        self._section_stack = []
        self._outputs = []

    def add_output(self, output):
        self._outputs.append(output)
    
    def section(self, title):
        sec = TraceSection(title)
        self._section_stack.append(sec)
        for out in self._outputs:
            out.start_section(sec)
        return sec
    
    def end_section(self):
        sec = self._section_stack.pop()
        for out in self._outputs:
            out.end_section(sec)
        return sec
    
    def unwind_section(self, sec):
        stack = self._section_stack
        while len(stack) > 0 and stack[-1] is not sec:
            self.end_section()
        
        if len(stack) > 0:
            stack.pop()
    
    def msg(self, fmt, *args, **kwargs):
        if len(args) > 0 or len(kwargs) > 0:
            msg = fmt.format(*args, **kwargs)
        else:
            msg = fmt
        for out in self._outputs:
            out.msg(msg)


class TraceOutput(object):
    def __init__(self, out = None):
        if out is None:
            out = sys.stderr
        elif isinstance(out, basestring):
            out = open(out, "w")
        self.output = out
    
    def start_section(self, sec):
        pass
    
    def end_section(self, sec):
        pass
    
    def msg(self, msg):
        self.output.write(msg)
        self.output.write("\n")


TRACE = Trace("global")
TRACE.add_output(TraceOutput(out = "trace.txt"))


def msg(fmt, *args, **kwargs):
    TRACE.msg(fmt, *args, **kwargs)


def section(title):
    TRACE.section(title)


def end_section():
    TRACE.end_section()


def main():
    print __doc__


if __name__ == "__main__":
    main()


