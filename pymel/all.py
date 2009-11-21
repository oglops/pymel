import sys

import internal
import internal.plogging as plogging
import internal.factories as factories

#logger = plogging.getplogging.pymelLogger(__name__)
plogging.pymelLogger.debug( 'imported internal' )

import api
plogging.pymelLogger.debug( 'imported api' )

from core import *
plogging.pymelLogger.debug( 'imported core' )

# for wrapped math functions
from util.arrays import *

import core.datatypes as datatypes

import versions

from core import nodetypes
from core.nodetypes import *
from core.uitypes import *

# These two were imported into 'old' pymel top level module,
# so make sure they're imported here as well
import core
import tools

## some submodules do 'import pymel.core.pmcmds as cmds' -
## this ensures that when the user does 'from pymel import *',
## cmds is always maya.cmds
import maya.cmds as cmds