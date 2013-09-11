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


class CmdName(object):
    def __init__(self, name = None):
        self.name = split_cmd(name)
    
    def __repr__(self):
        return utils.obj_repr(self, join_cmd(self.name))
    
    def __str__(self):
        return join_cmd(self.name)
    
    def __len__(self):
        return len(self.name)
    
    def __iter__(self):
        return iter(self.name)
    
    def __getitem__(self, key):
        if isinstance(key, slice):
            return CmdName(self.name.__getitem__(key))
        return self.name.__getitem__(key)
    
    def __add__(self, rhs):
        rhs = CmdName.make(rhs)
        return CmdName(self.name + rhs.name)
    
    @property
    def is_empty(self):
        return len(self.name) == 0
    
    @classmethod
    def make(cls, value, **kwargs):
        if isinstance(value, cls):
            return value
        return CmdName(value, **kwargs)


class CmdContext(object):
    def __init__(self, app, name):
        self.app  = app
        self.name = CmdName.make(name)
        
        self.real_name = CmdName()
        self.controller = None
    
    def __iadd__(self, rhs):
        if not isinstance(rhs, CmdContext):
            raise TypeError
        self.real_name += rhs.real_name


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
        
        self.root_ctrl = BasicController("root")
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
        ctrl.add_object(self)
        
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
        ctx  = CmdContext(self, name)
        ctrl = self.root_ctrl.route(ctx, ctx.name)
        ctx.controller = ctrl
        sys.stderr.write("Command %r routed to controller %r.\n" % (name, ctrl, ))
        sys.stderr.write("Real name: %s.\n" % (ctx.real_name, ))
        return ctrl.execute(ctx, cmd_args)
        #full_name = split_cmd(name)
        #if cmd_args is None:
        #    cmd_args = []
        #return self.root_ctrl.execute_command(self, full_name, (), cmd_args)
    
    def handle_ambiguous_command(self, name, args):
        alt = self.cmd_map[name]
        sys.stderr.write("Ambiguoug command: %s\n. Did you mean one of the following:\n" % (name, ))
        sys.stderr.write("\t%s\n" % (", ".join([n for n, c in alt]), ))
    
    def handle_unknown_command(self, cmd, args):
        sys.stderr.write("ERROR: Unknown command: %s %s\n\n" % (cmd, " ".join(args), ))
        self.cmd_help(cmd, args)


class CmdController(object):
    def __repr__(self):
        return utils.obj_repr(self)
    
    # Basic Protocol ##########################################
    
    @property
    def description(self):
        return ""
    
    def route(self, ctx, name):
        if len(name) == 0:
            return self
        ctx.real_name += name
        return UnknownController(name)
    
    def execute(self, ctx, arguments = None):
        raise NotImplementedError
    
    # Other ###################################################
    
    @classmethod
    def make(self, value):
        if isinstance(value, CmdController):
            return value
        if FunctionController.is_valid(value):
            return FunctionController(value)
        
        ctrl = BasicController()
        ctrl.add_object(value)
        return ctrl


class FunctionController(CmdController):
    NAME_PREFIX = "cmd_"
    
    def __init__(self, function, name = None):
        CmdController.__init__(self)
        self.function = function
        
        if name is None:
            name = FunctionController.reflect_name(self.function)
        self.name = name
    
    def __repr__(self):
        return utils.obj_repr(self, self.function, self.name)
    
    @property
    def description(self):
        if self.function and self.function.__doc__:
            return self.function.__doc__.strip()
        return ""
    
    def execute(self, ctx, arguments = None):
        self.function(ctx, arguments)
    
    @classmethod
    def is_valid(cls, value):
        if not inspect.isroutine(value):
            return False
        if value.__name__.startswith(cls.NAME_PREFIX):
            return True
        return False
    
    @classmethod
    def reflect_name(self, function):
        if inspect.isroutine(function):
            if function.__name__.startswith(self.NAME_PREFIX):
                return function.__name__[len(self.NAME_PREFIX):]
            return function.__name__
        raise ValueError


class BasicController(CmdController):
    def __init__(self, name = None, default_cmd = None):
        CmdController.__init__(self)
        
        self.name = name
        if isinstance(default_cmd, basestring):
            default_cmd = ProxyController(self, default_cmd)
        self.default_cmd = default_cmd
        self.children = utils.PrefixDict()
        
        self.add_object(self)
        #self.add_child(FunctionController(self.cmd_help))
    
    def __repr__(self):
        return utils.obj_repr(self, self.name)
    
    #### Basic Protocol #############################################
    
    @property
    def description(self):
        if self.default_cmd:
            return self.default_cmd.description
        return ""
    
    def route(self, ctx, name):
        if len(name) < 1:
            return self
            #return self, name
        
        try:
            child_name, child = self.children[name[0]]
        except KeyError:
            ctx.real_name += name[0]
            return UnknownController(name).route(ctx, name[1:])
        
        if child is not None:
            ctx.real_name += child_name
            return child.route(ctx, name[1:])
        
        ctx.real_name += name[0]
        return UnknownController(name)
    
    def execute(self, ctx, arguments = None):
        if self.default_cmd is not None:
            return self.default_cmd.execute(ctx, arguments)

        sys.stderr.write(("ERROR: Controller \"%s\" has no default command. Use "
                          "\"%s:help\" to see available commands.\n") %
                          (ctx.real_name, ctx.real_name, ))
        
        return 1
    
    #### BasicController Implementation #############################
    
    def add_child(self, ctrl, name = None):
        ctrl = CmdController.make(ctrl)
        name = name or ctrl.name
        self.children[name] = ctrl
    
    def add_object(self, obj):
        for name, value in ((attr, getattr(obj, attr)) for attr in dir(obj)):
            if FunctionController.is_valid(value):
                self.add_child(FunctionController(value))
    
    def cmd_help(self, ctx, arguments = None):
        """Displays this help."""
        
        w = sys.stderr.write
        w("Commands:\n")

        for name, child in self.children.iteritems():
            w("   %s\n      %s\n\n" % (name, child.description, ))
        
        #for cmd in self.commands.itervalues():
        #    #if len(self.cmd_map[cmd.name[:1]]) == 1:
        #    #    w("\t[%s]%s\t%s\n" % (cmd.name[:1], cmd.name[1:], cmd.description, ))
        #    #else:
        #    #    w("\t%s\t%s\n" % (cmd.name, cmd.description, ))
        #    desc = ""
        #    if cmd.description is not None:
        #        desc = cmd.description.strip()
        #    w("\t%s\t%s\n" % (cmd.name, desc, ))
        
        w("\n")


class UnknownController(CmdController):
    def __init__(self, name):
        CmdController.__init__(self)
        self.name = name
    
    def __repr__(self):
        return utils.obj_repr(self, self.name)
    
    def route(self, ctx, name):
        if len(name) == 0:
            return self
        
        ctx.real_name += name[0]
        return UnknownController(name[0]).route(ctx, name[1:])
    
    def execute(self, ctx, arguments = None):
        if ctx.name.is_empty:
            sys.stderr.write("ERROR: Default command undefined.\n")
        else:
            sys.stderr.write("ERROR: Unknown command: %s\n" % (ctx.real_name, ))
        return 1


class ProxyController(CmdController):
    def __init__(self, ctrl, name):
        CmdController.__init__(self)
        self.controller = ctrl
        self.name       = CmdName.make(name)
        self.context    = CmdContext(None, self.name)
        
        self._target    = None
    
    @property
    def target(self):
        if self._target is None:
            self._target = self.controller.route(self.context, self.name)
        return self._target
    
    @property
    def description(self):
        return self.target.description
    
    def route(self, ctx, name):
        ctx += self.context
        return self.target.route(ctx, name)
    
    def execute(self, ctx, arguments = None):
        return self.target.execute(ctx, arguments)


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


