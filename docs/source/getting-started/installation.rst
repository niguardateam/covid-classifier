Installation instructions
=========================

Operating systems support
-------------------------

In the table below we summarize the status of *pre-compiled binaries
distributed with pypi* for the packages listed above.

+------------------+---------+
| Operating System | Support |
+==================+=========+
| Linux x86        |   Yes   |
+------------------+---------+
| MacOS >= 10.15   |   Yes   |
+------------------+---------+
| Windows          |   No    | 
+------------------+---------+

.. note::
      All packages are supported for Python >= 3.8.


Installation
--------------------

.. _installing-qibo:

Here are the instructions to install CLEARLUNG on your device.

Prerequisites
""""""""""""""

The ``dcm2niix`` package is required to convert DICOM images.
If you work on Linux can be installed with

.. code-block:: bash

      sudo apt-get install -y dcm2niix

Otherwise, if you are on Mac you can download it via `Homebrew <https://brew.sh>`:

.. code-block:: bash

      brew install dcm2niix



Installing with pip
"""""""""""""""""""

The installation using ``pip`` is not available at the moment, because we have not published
the package on PyPi yet. Once we do that, the command to install CLEARLUNG will be

.. code-block:: bash

      pip install clearlung

The ``pip`` program will download and install all the required
dependencies for CLEARLUNG.


Installing from source
""""""""""""""""""""""

The installation procedure presented in this section is useful if you have to
develop the code from source.

In order to install the package perform the following steps:

.. code-block::

      git clone https://github.com/niguardateam/covid-classifier.git
      cd covid-classifier

Then proceed with the ``clearlung`` installation in dev mode using ``pip``

.. code-block::

      sudo pip install -e .

_______________________

.. _installing-tensorflow:

tensorflow
^^^^^^^^^^

The CLEARLUNG package needs `TensorFlow <https://www.tensorflow.org>`_  to be installed, 
in order to evaluate pre-trained models.
In order to install the package, we recommend the installation using:

.. code-block:: bash

      pip install tensorflow

.. note::
      TensorFlow can be installed following its `documentation
      <https://www.tensorflow.org/install>`_.

