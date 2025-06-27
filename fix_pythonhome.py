# fix_pythonhome.py
import sys
import os
import logging

# Set up logging to debug hook execution
logging.basicConfig(filename='C:\\Users\\lovei\\SCD_SALES\\swiftsaleapp\\hook.log', level=logging.DEBUG)
logging.debug("Running fix_pythonhome.py")

# Add Lib directory to sys.path
temp_dir = os.path.dirname(sys.executable)
lib_dir = os.path.join(temp_dir, 'Lib')
if os.path.isdir(lib_dir) and lib_dir not in sys.path:
    sys.path.insert(0, lib_dir)
    logging.debug(f"Added {lib_dir} to sys.path")

# Ensure base_library.zip is in sys.path
base_zip = os.path.join(temp_dir, 'base_library.zip')
if os.path.isfile(base_zip) and base_zip not in sys.path:
    sys.path.insert(0, base_zip)
    logging.debug(f"Added {base_zip} to sys.path")

# Set PYTHONHOME
os.environ['PYTHONHOME'] = temp_dir
logging.debug(f"Set PYTHONHOME to {temp_dir}")

# Log sys.path for debugging
logging.debug(f"sys.path: {sys.path}")