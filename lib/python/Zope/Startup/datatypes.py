##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Datatypes for the Zope schema for use with ZConfig."""

import os
from ZODB.config import ZODBDatabase
from ZODB.config import FileStorage

# generic datatypes

def security_policy_implementation(value):
    value = value.upper()
    ok = ('PYTHON', 'C')
    if value not in ok:
        raise ValueError, (
            "security_policy_implementation must be one of %s" % ok
            )
    return value

def cgi_environment(section):
    return section.environ

# Datatype for the access and trace logs
# (the loghandler datatypes come from the zLOG package)

class LoggerFactory:
    """
    A factory used to create loggers while delaying actual logger
    instance construction.  We need to do this because we may want to
    reference a logger before actually instantiating it (for example,
    to allow the app time to set an effective user).  An instance of
    this wrapper is a callable which, when called, returns a logger
    object.
    """
    def __init__(self, section):
        self.name = section.getSectionName()
        self.level = section.level
        self.handler_factories = section.handlers
        self.resolved = None

    def __call__(self):
        if self.resolved is None:
            # set the logger up
            import logging
            logger = logging.getLogger(self.name)
            logger.handlers = []
            logger.propagate = 0
            logger.setLevel(self.level)
            for handler_factory in self.handler_factories:
                handler = handler_factory()
                logger.addHandler(handler)
            self.resolved = logger
        return self.resolved

# DNS resolver

def dns_resolver(hostname):
    from ZServer.medusa import resolver
    return resolver.caching_resolver(hostname)

# mount-point definition

def mount_point(value):
    if not value:
        raise ValueError, 'mount-point must not be empty'
    if not value.startswith('/'):
        raise ValueError, ("mount-point '%s' is invalid: mount points must "
                           "begin with a slash" % value)
    return value

# A datatype that converts a Python dotted-path-name to an object

def importable_name(name):
    try:
        components = name.split('.')
        start = components[0]
        g = globals()
        package = __import__(start, g, g)
        modulenames = [start]
        for component in components[1:]:
            modulenames.append(component)
            try:
                package = getattr(package, component)
            except AttributeError:
                n = '.'.join(modulenames)
                package = __import__(n, g, g, component)
        return package
    except ImportError:
        raise ValueError, (
            'The object named by "%s" could not be imported' %  name )

# Datatype for the root configuration object
# (adds the softwarehome and zopehome fields; default values for some
#  computed paths)

def root_config(section):
    from ZConfig import ConfigurationError
    here = os.path.dirname(os.path.abspath(__file__))
    swhome = os.path.dirname(os.path.dirname(here))
    section.softwarehome = swhome
    section.zopehome = os.path.dirname(os.path.dirname(swhome))
    if section.cgi_environment is None:
        section.cgi_environment = {}
    if section.clienthome is None:
        section.clienthome = os.path.join(section.instancehome, "var")
    # set up defaults for pid_filename and lock_filename if they're
    # not in the config
    if section.pid_filename is None:
        section.pid_filename = os.path.join(section.clienthome, 'Z2.pid')
    if section.lock_filename is None:
        section.lock_filename = os.path.join(section.clienthome, 'Z2.lock')

    if not section.databases:
        section.databases = [getDefaultDatabaseFactory(section)]

    section.db_mount_tab = db_mount_tab = {}
    section.db_name_tab =  db_name_tab = {}
    dup_err = ('Invalid configuration: ZODB databases named "%s" and "%s" are '
               'both configured to use the same mount point, named "%s"')

    for database in section.databases:
        mount_points = database.config.mount_points
        name = database.config.getSectionName()
        db_name_tab[name] = database
        for point in mount_points:
            if db_mount_tab.has_key(point):
                raise ConfigurationError(dup_err % (db_mount_tab[point], name,
                                         point))
            db_mount_tab[point] = name

    return section

class ZopeDatabase(ZODBDatabase):
    """ A ZODB database datatype that can handle an extended set of
    attributes """
    def open(self):
        DB = ZODBDatabase.open(self)
        # set the connection class
        DB.klass = self.config.connection_class
        return DB
    
def getDefaultDatabaseFactory(context):
    # default to a filestorage named 'Data.fs' in clienthome
    class dummy:
        def __init__(self, name):
            self.name = name
        def getSectionName(self):
            return self.name

    from ZODB.Connection import Connection

    path = os.path.join(context.clienthome, 'Data.fs')
    fs_ns = dummy('default filestorage at %s' % path)
    fs_ns.path = path
    fs_ns.create = None
    fs_ns.read_only = None
    fs_ns.quota = None
    storage = FileStorage(fs_ns)
    db_ns = dummy('default zodb database using filestorage at %s' % path)
    db_ns.storage = storage
    db_ns.cache_size = 5000
    db_ns.pool_size = 7
    db_ns.version_pool_size=3
    db_ns.version_cache_size = 100
    db_ns.mount_points = ['/']
    db_ns.connection_class = Connection
    return ZopeDatabase(db_ns)

