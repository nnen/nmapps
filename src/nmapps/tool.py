#!/usr/bin/python
# -*- coding: utf-8 -*-
"""nmapps.util module.

Author: Jan Milík <milikjan@fit.cvut.cz>
"""

import os
import sys
import tempfile
import shutil
import logging
import string
import re

from . import __version__
from . import app
from . import fs
from . import bundle
from . import injection
from . import factory


LOGGER = logging.getLogger(__name__)


class FileConfigurator(object):
    VAR_PATTERN = re.compile(r"\$\$|\$\{[^}]*\}")


class Template(object):
    HOME_DIR = ".nmapps/templates"
    PATH = []
    
    FACTORY_KEY = "nmapps.tool.TemplateFactory"
    
    def __init__(self, name, path):
        self.name = name
        self.path = fs.Path.make(path)
        self.dest = None
    
    def instantiate(self, dest, *args, **kwargs):
        raise NotImplementedError
    
    @classmethod
    def create(cls, name):
        return factory.create(cls.FACTORY_KEY, name)

# TODO: Find a better (more cross-platform) way to get the home directory.
Template.PATH.append(fs.Path.join(os.getenv("HOME"), Template.HOME_DIR))


class CopyTemplate(Template):
    VERBATIM_DIR     = "verbatim"
    STR_TEMPLATE_DIR = "templates"
    LOGIC_FILE       = "logic.py"
    
    def __getitem__(self, key):
        return self.get_var(key)
    
    def instantiate(self, dest = None):
        dest = fs.Path.make(dest)
        if dest.is_file:
            dest = dest.dir
        self.dest = dest
        
        self.logic_file = self.path + self.LOGIC_FILE
        self.verbatim_dir = self.path + self.VERBATIM_DIR
        self.template_dir = self.path + self.STR_TEMPLATE_DIR
        
        self.template_variables = {
            "template_name" : self.name,
            "dest_path"     : str(self.dest),
            "dest_dir"      : self.dest.base,
        }
        
        self.template_varfn = None
        if self.logic_file.is_file:
            variables = { "tpl": self }
            execfile(str(self.logic_file), variables)
            self.template_varfn = variables.get("get_var", None)
        
        if self.verbatim_dir.is_dir:
            fs.copy(self.verbatim_dir, "", self.dest)
        
        if self.template_dir.is_dir:
            tmpdir = tempfile.mkdtemp(prefix = "nmapps_tpl_tmp")
            try:
                self.substitute(".", tmpdir, self)
                fs.copy(tmpdir, "", self.dest)
            finally:
                shutil.rmtree(tmpdir)
    
    def get_var(self, name):
        try:
            return self.template_variables[name]
        except KeyError:
            if self.template_varfn:
                return self.template_varfn(name)
        LOGGER.error("Unknown template variable: \"%s\".", name)
        raise KeyError
    
    def substitute(self, relpath, dest, variables):
        pth = fs.Path.join(self.template_dir, relpath)
        
        if pth.is_dir:
            for name in pth.list_names():
                self.substitute(fs.Path.join(relpath, name), dest, variables)
        else:
            res_pth = fs.Path.join(dest, relpath)
            with open(str(pth), "r") as in_file:
                tpl = string.Template(in_file.read())
                with open(str(res_pth), "w") as out_file:
                    out_file.write(tpl.substitute(variables))


@injection.factory(Template.FACTORY_KEY, "default")
class TemplateFactory(factory.Factory):
    def create(self, name):
        for tpl_path in Template.PATH:
            tpl_path = fs.Path.make(tpl_path)
            if not tpl_path.exists:
                LOGGER.warning("Template path %s does not exist." % (tpl_path, ))
                continue
            
            for child in tpl_path.list_names():
                if child == name:
                    pth = fs.Path.join(tpl_path, child)
                    tpl = self.create_from_path(name, pth)
                    if tpl:
                        LOGGER.info("Template named \"%s\" found in path %s.", name, pth)
                        return tpl
        
        #raise ValueError("Template could not be constructed for name \"%s\"." % (name, ))
        raise factory.FactoryException()
    
    def create_from_path(self, name, path):
        path = fs.Path.make(path)
        if path.is_dir:
            return CopyTemplate(name, path)
        return None


class UtilApp(app.CommandApp):
    def __init__(self):
        app.CommandApp.__init__(self)
        self.description = "Nmapps command line utility."
    
    def setup_args(self, parser):
        app.CommandApp.setup_args(self, parser)
        parser.add_argument("-v", "--version", action = "store_true")
    
    def cmd_version(self, ctx, cmd_args):
        """Print out nmapps package version."""
        print "nmapps %s" % (__version__, )
    
    def cmd_which(self, ctx, cmd_args):
        """Print out the bundle the application is running from."""
        b = bundle.get_bundle(__file__)
        sys.stderr.write("Bundle: %r\n" % (b, ))
    
    def cmd_bundle(self, ctx, cmd_args):
        """
        Try to find the bundle the current directory or the specified paths
        are in.
        """
        if len(cmd_args) == 0:
            cmd_args = [os.curdir, ]
        for arg in cmd_args:
            bndl = bundle.get_bundle(arg)
            sys.stderr.write(repr(bndl) + "\n")
    
    def cmd_eggimp(self, ctx, cmd_args):
        """Copy the eggimp.py script to the current directory."""
        path = fs.Path(__file__).dir + "eggimp.py"
        shutil.copyfile(str(path.abs), str(fs.Path("eggimp.py").abs))
    
    def cmd_tpl(self, ctx, cmd_args):
        if len(cmd_args) < 1:
            sys.stderr.write("Name of a template expected.\n")
            return 1
        tpl_name = cmd_args[0]
        try:
            tpl = Template.create(tpl_name)
        except ValueError:
            sys.stderr.write("Template \"%s\" could not be found. The template path is:\n%s\n" % (tpl_name, "\n".join([str(p) for p in Template.PATH])))
            return 1
        tpl.instantiate()


@injection.factory("nmapps.tool.UtilApp.controller", None, "test", "test")
class TestCtrl(app.BasicController):
    def cmd_test(self, ctx, cmd_args):
        """A test command in the test command controller."""
        print "This is TestCtrl command controller."


def main():
    logging.basicConfig(level = logging.DEBUG)
    app = UtilApp()
    return app.run()


if __name__ == "__main__":
    main()

