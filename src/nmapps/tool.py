#!/usr/bin/python
# -*- coding: utf-8 -*-
"""nmapps.util module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""


import shutil

from . import __version__
from . import app
from . import fs


class UtilApp(app.CommandApp):
    def __init__(self):
        app.CommandApp.__init__(self)
        self.description = "Nmapps command line utility."
    
    def setup_args(self, parser):
        app.CommandApp.setup_args(self, parser)
        parser.add_argument("-v", "--version", action = "store_true")
    
    def cmd_version(self, cmd, cmd_args):
        """Print out nmapps package version."""
        print "nmapps %s" % (__version__, )
    
    def cmd_eggimp(self, cmd, cmd_args):
        """Copy the eggimp.py script to the current directory."""
        path = fs.Path(__file__).dir + "eggimp.py"
        shutil.copyfile(str(path.abs), str(fs.Path("eggimp.py").abs))
        

def main():
    app = UtilApp()
    return app.run()


if __name__ == "__main__":
    main()
