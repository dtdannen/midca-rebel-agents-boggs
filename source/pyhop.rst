PyHop Methods and Operators
***************************

MIDCA, and thus our rebel agent code, uses PyHop, a Python-based hierarchical task network (HTN) planner, to generate plans for the goals it has. Using PyHop means giving PyHop a set of functions called "methods" and a set of functions called "operators" which allow PyHop to decompose a goal into a series of tasks. For more information on PyHop see https://bitbucket.org/dananau/pyhop. We have two separate modules for this, one for the methods and one for the operators.

World Methods
---------------

.. automodule:: world_methods
    :members:
    :undoc-members:


World Operators
-----------------

.. automodule:: world_operators
    :members:
    :undoc-members:
