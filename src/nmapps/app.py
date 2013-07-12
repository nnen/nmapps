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


LOGGER = logging.getLogger(__name__)


def guess_app_basename(fallback = None):
    if len(sys.argv) < 1 or len(sys.argv[0]) < 1:
        return fallback
    result = path.basename(sys.argv[0])
    result = result.split(".")[0]
    return result


class AppBase(object):
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


class CommandApp(AppBase):
    def __init__(self, basename = None):
        AppBase.__init__(self, basename)
        self.default_command = None
    
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
        
        cmd = self.args.cmd or "default"
        return self.execute_command(cmd, self.args.cmd_args)
    
    def get_commands(self):
        result = []
        for attr in dir(self):
            if attr.startswith("cmd_"):
                val = getattr(self, attr)
                doc = getattr(val, "__doc__", None) or ""
                result.append((attr[4:], doc, ))
        return result
    
    def execute_command(self, cmd, cmd_args = []):
        if isinstance(cmd, basestring):
            cmd = cmd.lower().replace("-", "_")
            handler = getattr(self, "cmd_" + cmd, self.handle_unknown_command)
        else:
            handler = cmd
        LOGGER.info("Executing command %r...", cmd)
        return handler(cmd, cmd_args)
    
    def cmd_help(self, cmd, cmd_args):
        """Displays this help."""
        
        print "Known Commands" 
        print "==============" 
        print
        
        for cmd, doc in self.get_commands():
            print "\t%s\t%s" % (cmd, doc, )
        
        print
    
    def handle_unknown_command(self, cmd, args):
        # TODO: Implement a better handler for unknown commands.
        print "Unknown command: %s %s" % (cmd, " ".join(args), )


class DaemonControlApp(CommandApp):
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


