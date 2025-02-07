Building packages
========================================================================

The packaging process involves two main phases:

 - Create archive of python virtualenv.
 - Create native package using virtualenv archive.


Phase 1 - Archive of virtual envrionment
------------------------------------------------------------------------
Create a Python virtual environment and install errbot along with the backends, plugins and their dependencies.
The virtual environment is stripped of build-time temporary files and an archive file is produced from the contents.


Phase 2 - Package from archive
------------------------------------------------------------------------

The system package is built using the archive file produced from the virtual environment.  This method ensures that
the operating system's python interpretor is used and any binary libraries that were used during linking are the
correct version.  This provides are sufficient assurances that errbot will run on the native system without missing
dependencies or version mismatches.
