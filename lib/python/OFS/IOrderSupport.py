##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Order support interfaces.

$Id$
"""


# create IOrderedContainer
from Interface.bridge import createZope3Bridge
from OFS.interfaces import IOrderedContainer as z3IOrderedContainer
import IOrderSupport

createZope3Bridge(z3IOrderedContainer, IOrderSupport, 'IOrderedContainer')

del createZope3Bridge
del z3IOrderedContainer
del IOrderSupport