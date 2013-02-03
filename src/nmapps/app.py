# src/nmapps/app.py

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
        
        self.args = None
    
    def setup_args(self, parser):
        parser.add_argument("args", nargs = "*")
    
    def parse_args(self, argv):
        parser = argparse.ArgumentParser()
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
    def setup_args(self, parser):
        parser.add_argument("cmd", nargs = "?")
        parser.add_argument("cmd_args", nargs = "*")
    
    def _run(self):
        command = self.args.cmd.lower()
        command = command.replace("-", "_")
        handler = getattr(self, "cmd_" + command, self.handle_unknown_command)
        handler(command, self.args.cmd_args)
    
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


