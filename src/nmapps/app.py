# src/nmapps/app.py
# -*- coding: utf-8 -*-
"""nmapps.app module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""

import sys
import os.path as path
import errno
import argparse
import logging
import inspect

import utils
import fs
import injection


LOGGER = logging.getLogger(__name__)


#####################################################################
## BASIC APPS
#####################################################################


class AbstractFile(object):
    @property
    def description(self):
        raise NotImplementedError

    def __init__(self):
        self.path = None
    
    def __str__(self):
        return self.description
    
    def get_input(self):
        raise NotImplementedError
    
    def get_output(self):
        raise NotImplementedError
    
    def get_output_file_name(self, extension = None, default_name = "output"):
        if extension:
            return default_name + "." + extension
        return default_name
    
    def get_output_file(self, extension = None, default_name = "output"):
        raise NotImplementedError


class File(AbstractFile):
    def __init__(self, path):
        AbstractFile.__init__(self)
        self.path = fs.Path.make(path)
        
        self._input = None
        self._output = None
    
    def get_input(self):
        if self._input is None:
            self._input = open(str(self.path), "r")
        return self._input
    
    def get_output(self):
        if self._output is None:
            self._output = open(str(self.path), "w")
        return self._output
    
    def get_output_file_name(self, extension = None, default_name = "output"):
        pass


def guess_app_basename(fallback = None):
    if len(sys.argv) < 1 or len(sys.argv[0]) < 1:
        return fallback
    result = path.basename(sys.argv[0])
    result = result.split(".")[0]
    return result


class AppBase(object):
    """Base class for CLI Python applications.
    """
    
    def __init__(self, basename = None):
        self.basename = (basename or
                         guess_app_basename() or
                         getattr(self, "BASENAME", type(self).__name__))
        self.description = None
        
        self.args = None
    
    def setup_args(self, parser):
        parser.add_argument("args", nargs = "*")
    
    def parse_args(self, argv):
        parser = argparse.ArgumentParser(description = self.description)
        self.setup_args(parser)
        self.args = parser.parse_args(argv)
    
    def run(self, argv = None):
        if argv is None:
            argv = sys.argv[1:]
        
        self.parse_args(argv)
        
        self._run()
    
    def _run(self):
        raise NotImplementedError()


#####################################################################
## COMMAND APPS
#####################################################################


CMD_SEP = ":"


def split_cmd(cmd):
    """Splits qualified command name into parts.
    
    Example:
    
    >>> split_cmd("some:command:name")
    ('some', 'command', 'name')
    >>> split_cmd(('other', 'command', 'name'))
    ('other', 'command', 'name')
    >>> split_cmd(['other', 'command', 'name'])
    ('other', 'command', 'name')
    >>> split_cmd(None)
    ()
    
    """
    if cmd is None:
        return tuple()
    if isinstance(cmd, basestring):
        return tuple(cmd.split(CMD_SEP))
    return tuple(cmd)


def join_cmd(cmd):
    """Joins parts of a command name back to qualified name.
    
    Example:
    
    >>> join_cmd(('some', 'command', 'name'))
    'some:command:name'
    >>> join_cmd(['some', 'command', 'name'])
    'some:command:name'
    >>> join_cmd("other:command:name")
    'other:command:name'
    """
    if isinstance(cmd, basestring):
        return cmd
    return CMD_SEP.join(cmd)


def cmd_to_str(cmd):
    value = join_cmd(cmd)
    if len(value) == 0:
        return "<none>"
    return "`%s`" % (value, )


class Command(object):
    """Represents a :class:`CommandApp` command.
    """
    
    METHOD_PREFIX = "cmd_"
    DECORATOR_ATTR = "__app_cmd__"
    
    def __init__(self, name, desc = None, callback = None):
        self.name = name
        self.description = desc
        self.callback = callback
    
    def __repr__(self):
        return utils.obj_repr(self, self.name)
    
    def execute(self, *args, **kwargs):
        self.callback(*args, **kwargs)
    
    @classmethod
    def decorate(cls, name, desc = None):
        # Decorator has been called directory on the function/method without
        # arguments.
        if hasattr(name, "im_func") or hasattr(name, "func_code"):
            setattr(name, cls.DECORATOR_ATTR, {
                "name": cls.method_name_to_cmd(name.__name__),
                "desc": name.__doc__,
            })
            return name
        
        # Decorator has been called with arguments.
        def decorator(fn):
            setattr(fn, cls.DECORATOR_ATTR, {
                "name": name,
                "desc": desc or fn.__doc__,
            })
            return fn
        return decorator
    
    @classmethod
    def method_name_to_cmd(cls, name):
        if name.startswith(cls.METHOD_PREFIX):
            return name[len(cls.METHOD_PREFIX):]
        return name
    
    @classmethod
    def from_method(cls, method):
        dec = getattr(method, cls.DECORATOR_ATTR, None)
        if dec is not None:
            return cls(dec["name"], dec["desc"], method)
        
        if not (hasattr(method, "__name__") and method.__name__.startswith(cls.METHOD_PREFIX)):
            return None
        
        cmd = method.__name__[len(cls.METHOD_PREFIX):]
        desc = getattr(method, "__doc__", None)
        return cls(cmd, desc, method)
    
    @classmethod
    def reflect(cls, obj):
        result = []
        for attr_name, attr in ((n, getattr(obj, n)) for n in dir(obj)):
            if inspect.isroutine(attr):
                cmd = cls.from_method(attr)
                if cmd is not None:
                    result.append(cmd)
        return result


appcmd = Command.decorate


class CommandApp(AppBase):
    """Base class for CLI applications that execute multiple named commands.
    
    As an example, see the :class:`DaemonControlApp` class, which takes the
    `start`, `stop`, `restart` and `status` commands to start, stop, restart
    and query status of a daemon.
    
    By default, the application supports the `help` command, which lists all
    the registered commands with a brief description.
    """
    
    def __init__(self, basename = None):
        AppBase.__init__(self, basename)
        
        #self.commands = {}
        #self.cmd_map = utils.PrefixDict()
        #self.default_command = None
        #
        #self.discover_commands()
        
        self.root_ctrl = CommandController("root", (self, ))
        self.initialize_root_controller(self.root_ctrl)
    
    #### AppBase implementation #####################################
    
    def setup_args(self, parser):
        parser.add_argument("cmd", metavar = "CMD", nargs = "?",
                            help = "command to be executed, see --help-commands for more information")
        parser.add_argument("cmd_args", metavar = "CMD_ARG", nargs = "*",
                            help = "arguments to be passed to the command")
        parser.add_argument("--help-commands", action = "store_true",
                            help = "print a list of commands and their descriptions")
    
    def _run(self):
        if self.args.help_commands:
            self.execute_command("help")
            return 0
        
        #cmd = self.args.cmd or self.default_command or "default"
        cmd = self.args.cmd
        return self.execute_command(cmd, self.args.cmd_args)
    
    #### CommandApp implementation ##################################
    
    def initialize_root_controller(self, ctrl):
        key = self.__module__ + "." + self.__class__.__name__ + ".controller"
        controllers = injection.get_all(key)
        for child in controllers:
            ctrl.add_child(child)
    
    def discover_commands(self):
        result = {}
        for attr in dir(self):
            cmd = Command.from_method(getattr(self, attr))
            if cmd is not None:
                self.add_cmd(cmd)
                result[cmd.name] = cmd
        return result
    
    def add_cmd(self, cmd):
        if cmd.name in self.commands:
            raise ValueError("Command '%s' already registered." % (cmd.name, ))
        self.commands[cmd.name] = cmd
        self.cmd_map[cmd.name] = cmd
    
    def get_commands(self):
        result = []
        for attr in dir(self):
            if attr.startswith("cmd_"):
                val = getattr(self, attr)
                doc = getattr(val, "__doc__", None) or ""
                result.append((attr[4:], doc, ))
        return result
    
    def execute_command(self, name, cmd_args = None):
        full_name = split_cmd(name)
        if cmd_args is None:
            cmd_args = []
        return self.root_ctrl.execute_command(self, full_name, (), cmd_args)
    
    def handle_ambiguous_command(self, name, args):
        alt = self.cmd_map[name]
        sys.stderr.write("Ambiguoug command: %s\n. Did you mean one of the following:\n" % (name, ))
        sys.stderr.write("\t%s\n" % (", ".join([n for n, c in alt]), ))
    
    def handle_unknown_command(self, cmd, args):
        sys.stderr.write("ERROR: Unknown command: %s %s\n\n" % (cmd, " ".join(args), ))
        self.cmd_help(cmd, args)


class CommandController(object):
    NAME = "cmd"
    
    def __init__(self, name = None, cmd_objs = None):
        self.name = name or self.NAME
        
        self.children = utils.PrefixDict()
        for child in self.initialize_children():
            self.add_child(*child)
        self.fallback_controller = None
        
        self.commands = utils.PrefixDict()
        commands = self.initialize_commands(cmd_objs)
        for cmd in commands:
            self.add_cmd(cmd)
        self.default_command_name = "help"
    
    def __repr__(self):
        return utils.obj_repr(self, self.name)
    
    def initialize_children(self):
        return []
    
    def initialize_commands(self, cmd_objs = None):
        result = []
        result += CommandHandler.reflect(self)
        if cmd_objs is not None:
            for obj in cmd_objs:
                result += CommandHandler.reflect(obj)
        return result
    
    def add_child(self, controller, name = None):
        if name is None:
            name = controller.name
        self.children[name] = controller
    
    def add_cmd(self, cmd):
        LOGGER.debug("Adding command \"%s\" to controller \"%s\"...", cmd.name, self.name)
        self.commands[cmd.name] = cmd
    
    def get_child_controller(self, name, context):
        """Returns a child controller for a given name.
        """
        try:
            alternatives = self.children[name]
        except KeyError:
            return self.get_unknown_child_controller(name, context)
        
        if len(alternatives) > 1:
            raise ValueError # TODO: Raise better exception - something like AmbiguousCommandException
        
        name, value = alternatives.pop()
        return value, (name, )
    
    def get_unknown_child_controller(self, name, context):
        #return name, self.fallback_controller or UNKNOWN_CONTROLLER
        return None, None
    
    def route_command(self, name, context = None):
        if context is None:
            context = tuple()
        
        if len(name) > 0:
            child, child_name = self.get_child_controller(name[0], context)
            if child is not None:
                return child.route_command(name[1:], context + child_name)
        
        return self, name, context
    
    def get_command(self, name, context):
        # TODO: Fix this, the rest of the name is ignored.
        assert isinstance(name, tuple)
        if isinstance(name, tuple):
            if len(name) < 1:
                name = (self.default_command_name, )
            simple_name = name[-1]
        
        try:
            alternatives = self.commands[simple_name]
        except KeyError:
            return self.get_unknown_command(name, context)
        
        if len(alternatives) > 1:
            raise ValueError # TODO: Raise better exception - something like AmbiguousCommandException
        
        cmd_name, command = alternatives.pop()
        return command, cmd_name, context + (cmd_name, )
    
    def get_unknown_command(self, name, context):
        return UNKNOWN_COMMAND_HANDLER, name, context + name
    
    def execute_command(self, app, name, context, arguments = None):
        ctrl, cmd_name, ctrl_name = self.route_command(name, context)
        command, cmd_simple_name, cmd_full_name = ctrl.get_command(cmd_name, ctrl_name)
        LOGGER.debug("Routing command %s to controller %r, command %s.", cmd_to_str(context + name), ctrl, cmd_to_str(cmd_full_name))
        #LOGGER.debug("Getting command %r from controller %r: %r.", cmd_simple_name, ctrl, command)
        
        LOGGER.info("Executing command %s...", cmd_to_str(cmd_full_name))
        return command.execute(app, ctrl, name, cmd_full_name, arguments)
    
    def cmd_help(self, app, ctrl, name, full_name, cmd_args):
        """Displays this help."""
        
        w = sys.stderr.write
        w("Commands:\n")
        
        for cmd in self.commands.itervalues():
            #if len(self.cmd_map[cmd.name[:1]]) == 1:
            #    w("\t[%s]%s\t%s\n" % (cmd.name[:1], cmd.name[1:], cmd.description, ))
            #else:
            #    w("\t%s\t%s\n" % (cmd.name, cmd.description, ))
            desc = ""
            if cmd.description is not None:
                desc = cmd.description.strip()
            w("\t%s\t%s\n" % (cmd.name, desc, ))
        
        w("\n")


class CommandHandler(object):
    """Represents a :class:`CommandApp` command handler.
    """
    
    METHOD_PREFIX = "cmd_"
    DECORATOR_ATTR = "__app_cmd__"
    
    def __init__(self, name, desc = None, callback = None):
        self.name = name
        self.description = desc
        self.callback = callback
    
    def __repr__(self):
        return utils.obj_repr(self, self.name)
    
    def execute(self, *args, **kwargs):
        self.callback(*args, **kwargs)
    
    @classmethod
    def decorate(cls, name, desc = None):
        # Decorator has been called directory on the function/method without
        # arguments.
        if hasattr(name, "im_func") or hasattr(name, "func_code"):
            setattr(name, cls.DECORATOR_ATTR, {
                "name": cls.method_name_to_cmd(name.__name__),
                "desc": name.__doc__,
            })
            return name
        
        # Decorator has been called with arguments.
        def decorator(fn):
            setattr(fn, cls.DECORATOR_ATTR, {
                "name": name,
                "desc": desc or fn.__doc__,
            })
            return fn
        return decorator
    
    @classmethod
    def method_name_to_cmd(cls, name):
        if name.startswith(cls.METHOD_PREFIX):
            return name[len(cls.METHOD_PREFIX):]
        return name
    
    @classmethod
    def from_method(cls, method):
        # Check if the method is decorated and use the decorator if it is.
        dec = getattr(method, cls.DECORATOR_ATTR, None)
        if dec is not None:
            return cls(dec["name"], dec["desc"], method)
        
        # Check if the method has magical name. If it doesn't, stop trying.
        if not (hasattr(method, "__name__") and method.__name__.startswith(cls.METHOD_PREFIX)):
            return None
        
        cmd = method.__name__[len(cls.METHOD_PREFIX):]
        desc = getattr(method, "__doc__", None)
        return cls(cmd, desc, method)
    
    @classmethod
    def reflect(cls, obj):
        result = []
        for attr_name, attr in ((n, getattr(obj, n)) for n in dir(obj)):
            if inspect.isroutine(attr):
                cmd = cls.from_method(attr)
                if cmd is not None:
                    result.append(cmd)
        return result


class UnknownCommandHandler(CommandHandler):
    def __init__(self):
        CommandHandler.__init__(self, "unknown")
    
    def execute(self, app, ctrl, name, full_name, arguments):
        if full_name[-1] == ctrl.default_command_name:
            sys.stderr.write("ERROR: Default command undefined.\n")
        else:
            sys.stderr.write("ERROR: Unknown command: %s\n" % (":".join(full_name), ))
        return 1

UNKNOWN_COMMAND_HANDLER = UnknownCommandHandler()


class UnknownController(CommandController):
    def get_child_controller(self, name, full_name):
        return name, self
    
    def get_command(self, name, full_name):
        return UnknownCommand()

UNKNOWN_CONTROLLER = UnknownController()


#####################################################################
## DAEMON APPS
#####################################################################


class DaemonControlApp(CommandApp):
    """Represents a CLI application for daemon control (starting, stopping, querying). 
    
    Can be used as-is or extended.
    """
    
    def __init__(self, daemon):
        CommandApp.__init__(self, daemon.name)
        self.daemon = daemon
    
    def cmd_start(self, cmd, args):
        pidfile = self.daemon.pidfile
        pid = pidfile.read()
        if pid is not None:
            print "Daemon is already running with PID %d. Exiting." % (pid, )
            return
        
        err = pidfile.test_write()
        if err == errno.EACCES:
            print ("Cannot write PID file \"%s\", permission denied (errno 13). "
                   "Try running the daemon as a priviledged user. Exiting.") % (
                pidfile.path, )
            return
        elif err is not None:
            print "Cannot write PID file \"%s\" because of error %d (%s). Exiting." % (
                pidfile.path, err, errno.errorcode[err], )
            return
        
        print "Starting daemon..."
        self.daemon.start()
    
    def cmd_stop(self, cmd, args):
        pid = self.daemon.pidfile.read()
        if pid is None:
            print "Daemon is not running. Exiting."
            return
        print "Stopping daemon..."
        self.daemon.stop()
    
    def cmd_restart(self, cmd, args):
        pid = self.daemon.pidfile.read()
        
        if pid is None:
            print "Daemon is not running, starting..."
        else:
            print "Daemon is running, restarting..."
            self.daemon.stop()
        
        self.daemon.start()
    
    def cmd_status(self, cmd, arg):
        pid = self.daemon.pidfile.read()
        if pid is None:
            print "Daemon is not running."
        else:
            print "Daemon is running with PID %d." % (pid, )


