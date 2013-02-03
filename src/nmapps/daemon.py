# -*- coding: utf8 -*-

import os, sys, time, atexit
import signal
import logging

from nmapps.utils import UserException


__all__ = ["PIDFile", "Daemon", ]


LOGGER = logging.getLogger(__name__)


class DaemonException(UserException):
    pass


class PIDFile(object):
    @property
    def exists(self):
        return os.path.exists(self.path)
    
    def __init__(self, path):
        self.path = path
        self.locked_pid = None
    
    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.path, )
    
    def lock(self):
        pid = self.read()
        if pid:
            return False
        
        self.write()
        return True
    
    def unlock(self):
        try:
            os.remove(self.path)
        except IOError:
            sys.stderr.write("Failed to remove the PID file lock.\n")
        self.locked_pid = None

    def unlock_at_exit(self):
        atexit.register(self.unlock)
    
    def write(self, pid = None):
        if not pid:
            pid = str(os.getpid())
        with file(self.path, 'w+') as f:
            f.write("%s\n" % (pid, ))
        self.locked_pid = pid
    
    def read(self):
        try:
            with file(self.path, 'r') as f:
                pid = int(f.read().strip())
            self.locked_pid = pid
            return pid
        except IOError:
            return None
    
    def test_write(self):
        try:
            self.lock()
            self.unlock()
        except IOError as e:
            return e.errno
        return None
    
    @classmethod
    def normalize(cls, value):
        if isinstance(value, cls):
            return value
        return cls(unicode(value))


class Daemon(object):
    """
    A generic daemon class.

    Source code is a modified version of an example found at
    http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/
    
    Usage: subclass the Daemon class and override the run() method
    """
    
    name = "python_daemon"
    
    def __init__(self, pidfile = None, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', logger = LOGGER):
        if pidfile is None:
            pidfile = "/var/run/%s.pid" % (self.name, )
        self.pidfile = PIDFile.normalize(pidfile)
        
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        
        self.logger = logger
    
    def setup_logging(self):
        log_file = "/var/log/%s.log" % (self.name, )
        logging.basicConfig(filename = log_file, level = logging.INFO)
    
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        # do the first fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0) 
        except OSError, e: 
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
        
        # decouple from parent environment
        os.chdir("/") 
        os.setsid() 
        os.umask(0) 
        
        # do the second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit from second parent
                sys.exit(0) 
        except OSError, e: 
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1) 
        
        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
        # write pidfile
        self.pidfile.lock()
        self.pidfile.unlock_at_exit()
    
    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        if self.pidfile.read():
            sys.stderr.write(
                "PID file %s already exists. "
                "It seems that the daemon is already "
                "running with PID %d." % (self.pidfile.path, self.pidfile.locked_pid, ))
            sys.exit(1)
        
        # Start the daemon
        self.daemonize()
        
        try:
            self.setup_logging()
        except Exception:
            self.logger.exception("Exception occured while setting up logging.")
        
        self.logger.info("Daemon started.")
        
        try:
            self.run()
            self.logger.info("Daemon stopped.")
        except Exception:
            self.logger.exception("Exception occured in the daemon's run() method.")
    
    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        pid = self.pidfile.read()
        
        if not pid:
            message = "PID file %s does not exist. " \
                "It seems the daemon is not running.\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart
        
        # Try killing the daemon process    
        try:
            while 1:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                if self.pidfile.exists:
                    self.pidfile.unlock()
            else:
                sys.stderr.write(err + "\n")
                sys.exit(1)
    
    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()
    
    def run(self):
        """
        You should override this method when you subclass Daemon. It will be called after the process has been
        daemonized by start() or restart().
        """

        counter = 0
        
        while True:
            time.sleep(5)
            sys.stdout.write(str(time.time()) + "\n")
            
            raise Exception()


class TestDaemon(Daemon):
    def __init__(self):
        self.name = "test_python_daemon"
        super(TestDaemon, self).__init__(stdout = "/home/jan/Projects/nmapps/test_daemon.stdout")
    
    def setup_logging(self):
        log_file = "/var/log/%s.log" % (self.name, )
        logging.basicConfig(filename = log_file, level = logging.DEBUG)
    
    def run(self):
        while True:
            time.sleep(5)
            sys.stdout.write(str(time.time()) + "\n")


if __name__ == "__main__":
    daemon = TestDaemon()
    
    #logging.basicConfig(filename = "/home/jan/Projects/nmapps/test_daemon.log", level = logging.DEBUG)
    
    if daemon.pidfile.read():
        print "Stopping daemon..."
        daemon.stop()
    else:
        print "Starting daemon..."
        daemon.start()


