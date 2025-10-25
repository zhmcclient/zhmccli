Changed the hidden ``--pdb`` option to be public. So far, it just brought up
the pdb debugger before the command within zhmc is called. Now, in addition
it enables post-mortem debugging for unhandled exceptions, so that the pdb
debugger comes up at the location where the exception is raised.
