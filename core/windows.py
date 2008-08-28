
"""
The ui module contains functions which are used to create ui elements, as well as their class counterparts.

Pymel UIs
=========

pymel adds more readability to ui building while also maintaining backward compatibility.  Every ui command in maya.cmds
is a class in pymel, which can behave like a command or like a class. More documentation on this to come, but for now
check out pipeGen.py in examples directory

Command Callbacks
-----------------

one common point of confusion is command callbacks with ui elements. There are several different ways to handle 
command callbacks on user interface widgets:  
                        
Function Name as String
~~~~~~~~~~~~~~~~~~~~~~~

maya will try to execute this as a python command, but unless you know the namespace it will
be imported into, the function will not be recognized. notice how the namespace must be hardwired
into the command:

    >>> button( c="myCommand" )

or

    >>> button( c="myModule.myCommand" )

this method is not recommended.

Function Object
~~~~~~~~~~~~~~~  

When using this method, you pass an actual function object (without the parentheses). The callback function
has to be defined before it is referenced by the command flag.  also, keep in mind many ui widgets such as radioButtonGrp
pass args to the function (to mimic the "myCommand #1" functionality in mel), which your function must accommodate. The
tricky part is that different ui elements pass differing numbers of args to their callbacks, and some pass none at all.
This is why it is best for your command to use the *args syntax to accept any quantity of args, and then deal with them
in the function.

    >>> def myCommand( *args ): print args # this definition must come first

    >>> button( c=myCommand )
                
Lambda Functions
~~~~~~~~~~~~~~~~
In my experience this is the best way to handle most command callbacks.  You can choose exactly which args you want
to pass along to your function and order of definition does not matter.

    >>> button( c= lambda *args: myCommand(args[0]) )

    >>> def myCommand( arg ): print "running", arg 


"""



import pmtypes.pmcmds as cmds
#import maya.cmds as cmds


import pymel.util as util
import pmtypes.factories as _factories
from factories import MetaMayaNodeWrapper as metaNode
from system import Path

#-----------------------------------------------
#  Enhanced UI Commands
#-----------------------------------------------

def lsUI( **kwargs ):
    long = kwargs.pop( 'long', kwargs.pop( 'l', False ) )
    head = kwargs.pop( 'head', kwargs.pop( 'hd', None ) )
    tail = kwargs.pop( 'tail', kwargs.pop( 'tl', None) )
    
    if not kwargs:
        kwargs = { 
            'windows': 1, 'panels' : 1, 'editors' : 1, 'controls' : 1, 'controlLayouts' : 1,
            'collection' : 1, 'radioMenuItemCollections' : 1, 'menus' : 1, 'menuItems' : 1, 'contexts' : 1, 'cmdTemplates' : 1 }
    kwargs['long'] = long
    if head is not None: kwargs['head'] = head
    if tail is not None: kwargs['tail'] = tail
    return map( PyUI, util.listForNone( cmds.lsUI( **kwargs ) ) )
   
scriptTableCmds = {}

def scriptTable(*args, **kwargs):
    """
Maya Bug Fix:
    - fixed getCellCmd to work with python functions, previously only worked with mel callbacks
        IMPORTANT: you cannot use the print statement within the getCellCmd callback function or your values will not be returned to the table
    """
    cb = kwargs.pop('getCellCmd', kwargs.pop('gcc',False) )
    if cb:
        if hasattr(cb, '__call__'):        
            uiName = cmds.scriptTable( *args, **kwargs )
            procName = 'getCellMel%d' % len(scriptTableCmds.keys())
            procCmd = "global proc string %s( int $row, int $column ){return python(\"pymel.scriptTableCmds['%s'](\" + $row + \",\" + $column + \")\");}" %  (procName,uiName) 
            #print procCmd
            mm.eval( procCmd )            
            scriptTableCmds[uiName] = cb
            
            # create a scriptJob to clean up the dictionary of functions
            popCmd = "python(\"scriptTableCmds.pop('%s',None)\")" % uiName 
            #print popCmd
            cmds.scriptJob( uiDeleted=(uiName, "python(\"pymel.scriptTableCmds.pop('%s',None)\")" % uiName ) )

            return cmds.scriptTable( uiName, e=1, getCellCmd=procName )
        else:
            kwargs['getCellCmd'] = cb    
    
    cmds.scriptTable( *args, **kwargs )
    
def getPanel(*args, **kwargs):
    return util.listForNone( cmds.getPanel(*args, **kwargs ) )



_thisModule = __import__(__name__, globals(), locals(), ['']) # last input must included for sub-modules to be imported correctly



class UI(unicode):
    def __new__(cls, name=None, create=False, *args, **kwargs):
        """
        Provides the ability to create the UI Element when creating a class
        
            >>> n = pm.Window("myWindow",create=True)
            >>> n.__repr__()
            # Result: Window('myWindow')
        """
        def exists():
            try: return cls.__melcmd__(name, ex=1)
            except: pass
        
        # create a new node when any of these conditions occur:
        #    name is None
        #    create is True
        #    parent flag is set
        parent = kwargs.get( 'parent', kwargs.get('p', None))
        if name is None or create or parent:
            name = cls.__melcmd__(name, *args, **kwargs)
        return unicode.__new__(cls,name)
    
    def __repr__(self):
        return u"%s('%s')" % (self.__class__.__name__, self)
    def getChildren(self, **kwargs):
        kwargs['long'] = True
        return filter( lambda x: x.startswith(self) and not x == self, lsUI(**kwargs))
    def getParent(self):
        return UI( '|'.join( self.split('|')[:-1] ) )
    def type(self):
        return objectTypeUI(self)
    def shortName(self):
        return self.split('|')[-1]
    delete = _factories.functionFactory( 'deleteUI', _thisModule, rename='delete' )
    rename = _factories.functionFactory( 'renameUI', _thisModule, rename='rename' )
    type = _factories.functionFactory( 'objectTypeUI', _thisModule, rename='type' )
     
# customized ui classes                            
class Window(UI):
    """pymel window class"""
    __metaclass__ = metaNode                        
    def show(self):
        cmds.showWindow(self)
    def delete(self):
        cmds.deleteUI(self, window=True)
                
class FormLayout(UI):
    __metaclass__ = metaNode
    def attachForm(self, *args):
        kwargs = {'edit':True}
        #if isinstance(list, args[0]):
        #    kwargs['attachForm'] = args
        #    return self.applyArgs(**kwargs)
            
        kwargs['attachForm'] = [args]
        cmds.formLayout(self,**kwargs)
        
    def attachControl(self, *args):
        kwargs = {'edit':True}
        kwargs['attachControl'] = [args]
        cmds.formLayout(self,**kwargs)        
        
    def attachNone(self, *args):
        kwargs = {'edit':True}
        kwargs['attachNone'] = [args]
        cmds.formLayout(self,**kwargs)    
        
    def attachPosition(self, *args):
        kwargs = {'edit':True}
        kwargs['attachPosition'] = [args]
        cmds.formLayout(self,**kwargs)
        
class TextScrollList(UI):
    __metaclass__ = metaNode
    def extend( self, appendList ):
        """ append a list of strings"""
        
        for x in appendList:
            self.append(x)
            
    def selectIndexedItems( self, selectList ):
        """select a list of indices"""
        for x in selectList:
            self.selectIndexedItem(x)

    def removeIndexedItems( self, removeList ):
        """remove a list of indices"""
        for x in removeList:
            self.removeIndexedItem(x)
                
    def selectAll(self):
        """select all items"""
        numberOfItems = self.getNumberOfItems()
        self.getSelectIndexedItem(range(1,numberOfItems+1))

    
#===============================================================================
# Provides classes and functions to facilitate UI creation in Maya
#===============================================================================

class Callback(object):
    """
    Enables deferred function evaluation with 'baked' arguments.
    Useful where lambdas won't work...
    Example: 
    
    .. python::
    
        import pymel as pm
        def addRigger(rigger, **kwargs):
            print "adding rigger", rigger
           
        for rigger in riggers:
            pm.menuItem(
                label = "Add " + str(rigger),
                c = Callback(addRigger,rigger,p=1))   # will run: addRigger(rigger,p=1)
    """

    def __init__(self,func,*args,**kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
    def __call__(self,*args):
        return self.func(*self.args,**self.kwargs)
    
class AutoLayout(FormLayout):
    """ 
    Automatically distributes child controls in either a
    horizontal or vertical layout. Call 'redistribute' once done
    adding child controls.
    """
    HORIZONTAL, VERTICAL = range(2)
    sides = [["top","bottom"],["left","right"]]

    
    #def __new__(cls,  *args, **kwargs):
    #    kwargs.pop("orientation",None)
    #    kwargs.pop("spacing",None)
    #    kwargs.pop("reversed",None)
    #    kwargs.pop("ratios",None)
    #    return FormLayout.__new__(cls, *args, **kwargs)
    
        
    def __init__(self, name=None, orientation=VERTICAL, spacing=2, reversed=False, ratios=None):
        """ 
        spacing - absolute space between controls
        orientation - the orientation of the layout [ AutoLayout.HORIZONTAL | AutoLayout.VERTICAL ]
        """
        self.spacing = spacing
        self.ori = orientation
        self.reversed = reversed
        self.ratios = ratios and list(ratios) or []
    
    def flip(self):
        """Flip the orientation of the layout """
        self.ori = 1-self.ori
        self.redistribute(*self.ratios)
    
    def reverse(self):
        """Reverse the children order """
        self.reversed = not self.reversed
        self.ratios.reverse()
        self.redistribute(*self.ratios)
        
    def reset(self):
        self.ratios = []
        self.reversed = False
        self.redistribute()
        
    def redistribute(self,*ratios):
        """ Redistribute the child controls based on the given ratios.
            If not ratios are given (or not enough), 1 will be used 
            win=Window(create=1)
            win.show()
            al=AutoLayout(create=1,parent=win)
            [pm.Button(create=1,l=i,parent=al) for i in "yes no cancel".split()] # create 3 buttons
            al.redistribute(2,2) # First two buttons will be twice as big as the 3rd button
        """
        
        children = self.getChildArray()
        if not children:
            return
        if self.reversed: children.reverse()
        
        ratios = list(ratios) or self.ratios or []
        ratios += [1]*(len(children)-len(ratios))
        self.ratios = ratios
        total = sum(ratios)        
        for i in range(len(children)):
            child = children[i]
            for side in self.sides[self.ori]:
                self.attachForm(child,side,self.spacing)

            if i==0:
                self.attachForm(child,
                    self.sides[1-self.ori][0],
                    self.spacing)
            else:
                self.attachControl(child,
                    self.sides[1-self.ori][0],
                    self.spacing,
                    children[i-1])
            
            if ratios[i]:
                self.attachPosition(children[i],
                    self.sides[1-self.ori][1],
                    self.spacing,
                    float(sum(ratios[:i+1]))/float(total)*100)
            else:
                self.attachNone(children[i],
                    self.sides[1-self.ori][1])


def autoLayout(*args, **kwargs):
    kw = {}
    for k in kwargs.keys():
        if k in ["orientation", "spacing", "reversed", "ratios"]:
            v = kwargs.pop(k,None)
            if v is not None:
                kw[k] = v
    
    return AutoLayout(formLayout(*args, **kwargs),**kw)

def horizontalLayout(*args, **kwargs):
    kwargs["orientation"] = AutoLayout.HORIZONTAL
    return autoLayout(*args, **kwargs)

def verticalLayout(*args, **kwargs):
    kwargs["orientation"] = AutoLayout.VERTICAL
    return autoLayout(*args, **kwargs)



class SmartLayoutCreator:
    """
    Create a set of layouts and controls using a nested data structure.
    Example (just try it...):
    .. python::
    
        SLC = pm.SmartLayoutCreator
        
        class SLCExample:
          
            def __init__(self):
                  slc = SLC(name   = "win",                                 # name for the ui element
                            uiFunc = pm.Window,                             # callable that will create the ui element
                            kwargs = {"create":True, "title":"SLC Example"}, # keyword arguments for uiFunc
                            postFunc = pm.Window.show,                      # a callable to invoke after creating the element and its children
                            childCreators = [                               # nested ui elements, defined as further SLC objects 
                                # (non-verbose SLC declaration:)
                                SLC("layout", pm.VerticalLayout, dict(ratios=[1,1.5,2,2.5,3,3.5]), pm.VerticalLayout.redistribute,
                                    # create buttons using list comprehension:
                                    childCreators = [
                                        SLC("lbl" + str.capitalize(), pm.text, dict(al="center",l=str,bgc=[i/3.0,i/4.0,1])) 
                                            for (i,str) in enumerate("this is a dead parrot".split())
                                        ] + 
                                        [SLC("btn", pm.button, dict(l="Click Me!", c=lambda *x: self.layout.flip()))]
                                    )
                                ]
                            )
                  # create the layout, and place the named ui elements as new values in the 'creation' dictionary
                  slc.create(creation = self.__dict__)
                    
                  # now we can access ui elements via their name as designated in the SLC:  
                  self.lblYes.backgroundColor([.8,1,.8])
        
        slcEx = SLCExample()
                            
    """
    def __init__(self, name=None, uiFunc=None, kwargs=None, postFunc=None, childCreators=None):
        assert (uiFunc is None) or callable(uiFunc), uiFunc
        assert kwargs is None or isinstance(kwargs,dict), kwargs
        assert postFunc is None or callable(postFunc), postFunc
        assert childCreators is None or isinstance(childCreators,list), childCreators
        self.__dict__.update(vars())
        
    def create(self, creation=None, parent=None):
        """ 
        Create the ui elements defined in this SLC. 
        Named elements will be inserted into the 'creation' dictionary, which is also the return value of this function.
        The top ui element can be explicitly placed under 'parent', or implicitly under the current ui parent.
        """  
        
        if creation is None:
            creation = {}
        childCreators = self.childCreators or []
        if parent and self.uiFunc: self.kwargs["parent"] = parent
        self.me = self.uiFunc and self.uiFunc(**self.kwargs) or parent
        
        if self.name:
            creation[self.name] = self.me
        [child.create(creation=creation,parent=self.me) for child in childCreators]
        if self.postFunc: self.postFunc(self.me)
        return creation

SLC = SmartLayoutCreator
        
def labeledControl(label, uiFunc, kwargs, align="left", parent=None, ratios=None):
    dict = SLC("layout", horizontalLayout, {"ratios":ratios}, AutoLayout.redistribute,  [
                SLC("label", text, {"l":label,"al":align}),
                SLC("control", uiFunc, kwargs)
            ]).create(parent=parent)
    control = dict["control"]
    if not isinstance(control,UI):
        control = UI(control)
    control.label = dict["label"] 
    control.layout = dict["layout"]
    return control

def promptBox(title, message, okText, cancelText, **kwargs):
    """ Prompt for a value. Returns the string value or None if cancelled """
    ret = promptDialog(t=title, m=message, b=[okText,cancelText], db=okText, cb=cancelText,**kwargs)
    if ret==okText:
        return promptDialog(q=1,tx=1)
    
def promptBoxGenerator(*args, **kwargs):
    """ Keep prompting for values until cancelled """
    while 1:
        ret = promptBox(*args, **kwargs)
        if not ret: return
        yield ret    
    
def confirmBox(title, message, yes="Yes", no="No", defaultToYes=True):
    """ Prompt for confirmation. Returns True/False """
    ret = confirmDialog(t=title,    m=message,     b=[yes,no], 
                           db=(defaultToYes and yes or no), 
                           ma="center", cb="No", ds="No")
    return (ret==yes)
                        
def _createClassesAndFunctions():
    for funcName in _factories.uiClassList:
        classname = util.capitalize(funcName)
        #classname = funcName[0].upper() + funcName[1:]
        if not hasattr( _thisModule, classname ):
            cls = metaNode(classname, (UI,), {})
            cls.__module__ = __name__
            setattr( _thisModule, classname, cls )
        else:
            cls = getattr( _thisModule, classname )
    
        #funcName = util.uncapitalize( classname )
        func = _factories.functionFactory( funcName, cls, _thisModule, uiWidget=True )
        if func:
            func.__module__ = __name__
            #cls.__melcmd__ = func
            setattr( _thisModule, funcName, func )
        else:
            print "ui command not created", funcName
            
    moduleShortName = __name__.split('.')[-1]
    for funcName in _factories.moduleCmds[ moduleShortName ] :
        if funcName not in _factories.uiClassList:
            #print "bad stuff", funcName
            #func = None
            func = _factories.functionFactory( funcName, returnFunc=None, module=_thisModule )
            if func:
                func.__module__ = __name__
                setattr( _thisModule, funcName, func )
            
_createClassesAndFunctions()

def promptForFolder():
    """ Prompt the user for a folder path """
    
    # a little trick that allows us to change the top-level 'folder' variable from 
    # the nested function ('getfolder') - use a single-element list, and change its content
    folder = [None]
    def getfolder(*args):
        folder[0] = args[0]
    ret = cmds.fileBrowserDialog(m=4, fc=getfolder, an="Get Folder")
    folder = Path(folder[0])
    if folder.exists():
        return folder

def promptForPath():
    """ Prompt the user for a folder path """
    
    if cmds.about(linux=1):
        return fileDialog(mode=0)
    
    else:
        # a little trick that allows us to change the top-level 'folder' variable from 
        # the nested function ('getfolder') - use a single-element list, and change its content
        
        folder = [None]
        def getfolder(*args):
            folder[0] = args[0]
        ret = cmds.fileBrowserDialog(m=0, fc=getfolder, an="Get File")
        folder = Path(folder[0])
        if folder.exists():
            return folder
    
def fileDialog(*args, **kwargs):
    ret = cmds.fileDialog(*args, **kwargs )
    if ret:
        return Path( ret )


def pathButtonGrp( name=None, *args, **kwargs ):
    if name is None or not cmds.textFieldButtonGrp( name, ex=1 ):
        create = True
    else:
        create = False
        
    return PathButtonGrp( name=name, create=create, *args, **kwargs ) 

class PathButtonGrp( TextFieldButtonGrp ):
    def __new__(cls, name=None, create=False, *args, **kwargs):
        
        if create:
            kwargs.pop('bl', None)
            kwargs['buttonLabel'] = 'Browse'
            kwargs.pop('bl', None)
            kwargs['buttonLabel'] = 'Browse'
            kwargs.pop('bc', None)
            kwargs.pop('buttonCommand', None)

            name = cmds.textFieldButtonGrp( name, *args, **kwargs)
            
            def setPathCB(name):
                f = promptForPath()
                if f:
                    cmds.textFieldButtonGrp( name, e=1, text=f)
            
            cb = Callback( setPathCB, name ) 
            cmds.textFieldButtonGrp( name, e=1, buttonCommand=cb )
            
        return TextFieldButtonGrp.__new__( cls, name, create=False, *args, **kwargs )
        
     
    def getPath(self):
        return Path( self.getText() )
    
def vectorFieldGrp( *args, **kwargs ):
    return VectorFieldGrp( *args, **kwargs ) 
 
class VectorFieldGrp( FloatFieldGrp ):
    def __new__(cls, name=None, create=False, *args, **kwargs):
        if create:
            kwargs.pop('nf', None)
            kwargs['numberOfFields'] = 3
            name = cmds.floatFieldGrp( name, *args, **kwargs)

        return FloatFieldGrp.__new__( cls, name, create=False, *args, **kwargs )
        
    def getVector(self):
        x = floatFieldGrp( self, q=1, v1=True )
        y = floatFieldGrp( self, q=1, v2=True )
        z = floatFieldGrp( self, q=1, v3=True )
        return Vector( [x,y,z] )
    
    def setVector(self, vec):
        floatFieldGrp( self, e=1, v1=vec[0], v2=vec[1], v3=vec[2] )
        
        return Vector( [x,y,z] )


def PyUI(strObj, type=None):
    try:
        if not type:
            type = objectTypeUI(strObj)
        return getattr(_thisModule, util.capitalize(type) )(strObj)
    except AttributeError:
        return UI(strObj)
    
    

                        
                        
                                