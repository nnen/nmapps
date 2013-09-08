#!/usr/bin/python
# -*- coding: utf-8 -*-
"""writers module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


import sys
import cStringIO as StringIO
import logging


LOGGER = logging.getLogger("ast")


def obj_repr(instance, *args, **kwargs):
    args_list = []
    args_list += [repr(a) for a in args]
    args_list += ["%s = %r" % (k, v) for k, v in kwargs.iteritems()]
    return "%s(%s)" % (type(instance).__name__, ", ".join(args_list), )


class Writer(object):
    def __init__(self, output = None):
        if output is None:
            output = StringIO.StringIO()
        self.output = output
        self.indent_stack = []
    
    def __str__(self):
        getvalue = getattr(self.output, None)
        if getvalue:
            return getvalue()
        return repr(self)
    
    def __getattr__(self, name):
        return getattr(self.output, name)
    
    def write_indent(self):
        if len(self.indent_stack) > 0:
            self.output.write(self.indent_stack[-1])
    
    def indent(self, value = "\t"):
        if len(self.indent_stack) > 0:
            self.indent_stack.append(self.indent_stack[-1] + value)
        else:
            self.indent_stack.append(value)
        
        class IndentGuard(object):
            def __init__(self, writer):
                self.writer = writer
            def __enter__(self):
                pass
            def __exit__(self, exc_type, exc_value, traceback):
                if exc_type is None:
                    self.writer.unindent()
        
        return IndentGuard(self)
    
    def unindent(self):
        if len(self.indent_stack) > 0:
            self.indent_stack.pop()


class HTMLWriter(Writer):
    def __init__(self, output = None):
        Writer.__init__(self, output)
        self.tag_stack = []
    
    def __str__(self):
        getvalue = getattr(self.output, None)
        if getvalue:
            return getvalue()
        return repr(self)
    
    def format_css_style(self, value):
        if isinstance(value, dict):
            result = "; ".join(["%s: %s" % (k, v, ) for k, v in value.iteritems()])
        return str(value)

    def format_tag_attrs(self, attrs):
        if "style" in attrs:
            attrs["style"] = self.format_css_style(attrs["style"])
        attributes = {}
        for k, v in attrs.iteritems():
            if k.endswith("_"):
                attributes[k[:-1]] = v
            else:
                attributes[k] = v
        return " ".join(["%s=\"%s\"" % (k, v, ) for k, v in attributes.iteritems()])
    
    def tag(self, name, value = None, **kwargs):
        self.tag_stack.append(name)
        if not isinstance(name, basestring):
            names = name
            name = names[-1]
            for t in names[:-1]:
                self.output.write("<%s>" % (t, ))
        
        if len(kwargs) > 0:
            self.output.write("<%s %s>" % (
                name,
                self.format_tag_attrs(kwargs),
            ))
            #if "style" in kwargs:
            #    kwargs["style"] = self.format_css_style(kwargs["style"])
            #attributes = {}
            #for k, v in kwargs.iteritems():
            #    if k.endswith("_"):
            #        attributes[k[:-1]] = v
            #    else:
            #        attributes[k] = v
            #self.output.write("<%s %s>" % (
            #    name,
            #    " ".join(["%s=\"%s\"" % (k, v, ) for k, v in attributes.iteritems()]),
            #))
        else:
            self.output.write("<%s>" % (name, ))
        
        if value is not None:
            self.write(value)
            self.end_tag()
            return
        
        class TagGuard(object):
            def __init__(self, writer):
                self.writer = writer
            def __enter__(self):
                pass
            def __exit__(self, exc_type, exc_value, traceback):
                if exc_type is None:
                    self.writer.end_tag()
        
        return TagGuard(self)
    
    def end_tag(self):
        tag = self.tag_stack.pop()
        if isinstance(tag, basestring):
            self.output.write("</%s>" % (tag, ))
        else:
            for t in reversed(tag):
                self.output.write("</%s>" % (t, ))
    
    def write(self, value):
        self.output.write(str(value))


class DOTWriter(object):
    def __init__(self, output = None):
        if output is None:
            output = sys.stdout
        self.output = output
    
    def write(self, value):
        self.output.write(str(value))
    
    def writeln(self, value):
        self.output.write(str(value))
        self.output.write("\n")

    def start(self, name = "UnnamedGraph", digraph = False):
        if digraph:
            self.output.write("digraph %s {\n" % (name, ))
        else:
            self.output.write("graph %s {\n" % (name, ))
    
    def end(self):
        self.output.write("}\n")
    
    def edge(self, a, b = None, **attributes):
        if b is None:
            return self.node(a, **attributes)
        if len(attributes) == 0:
            self.output.write("\t%s -> %s;\n" % (a, b, ))
            return
        self.output.write("\t%s -> %s [ %s];\n" % (
            a, b,
            "".join(["%s = %s; " % (k, v, ) for k, v in attributes.iteritems() if v is not None]),
        ))
    
    def node(self, name, **kwargs):
        self.output.write("\t%s [ %s];\n" % (
            name,
            "".join(["%s = %s; " % (k, v, ) for k, v in kwargs.iteritems() if v is not None]),
        ))
    
    def attrs(self, **kwargs):
        for k, v in kwargs.iteritems():
            self.output.write("\t%s = %s;\n" % (k, v, ))


def main():
    print __doc__


if __name__ == "__main__":
    main()

