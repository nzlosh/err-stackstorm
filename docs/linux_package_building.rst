Building Linux Packages
=========================================================================================================================================================
Two scripts are used to help ``err-stackstorm`` packages available on multiple operating systems.  Each script represent a phase in the package build process

``contrib/packaging/build_archive`` is a BASH script that carries out the steps to create a Python virtual environment and install errbot, various backends and err-stackstorm using a supported operating systems native Python installation.

``contrib/packaging/build`` is a Python script that depends on jinja2.  It should be setup using its own virtual environment and is executed after the err-stackstorm archive has been successfully created by ``build_archive``.  ``build`` reads the ``build.cfg`` configuration file, which is JSON format, to fill out jinja templates that are used by the operating systems package build system.  This allows for updating and build system packages in a similar manner for all supported operating systems.

Phase 1: Packaging Python
---------------------------------------------------------------------------------------------------------------------------------------------------------
Python applications are best isolated from the system.  Python virtual environments (venv) are created for this purpose, the virtual environment is created inside a single directory, various base standard libraries are copied into the venv and symlinks setup to point to the systems Python interpreter.  The venv will be created with whichever version of python was executed to create the venv.
::

    python3.8 -m venv <venv_name>
    source <venv_name>/bin/activate


Phase 2: Build System packages
---------------------------------------------------------------------------------------------------------------------------------------------------------
After the Python virtual environment has been setup, dependencies installed and pre-compiled files purged, the Python virtual environment is archived using ``tar``.  The resulting archive will be used to deploy the virtual environment inside the native OS packaging.


Building DEB based packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TO DO


Building RPM based packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TO DO

Phase 3: Repository Signing
---------------------------------------------------------------------------------------------------------------------------------------------------------

TO DO
