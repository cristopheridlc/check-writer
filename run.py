#!/usr/bin/env python3
import os
import sys
import subprocess
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gio, Adw

# Initialize Libadwaita
Adw.init()

# Compile GResource bundle
src_dir = os.path.join(os.path.dirname(__file__), 'src')
build_dir = os.path.join(os.path.dirname(__file__), '_build')
os.makedirs(os.path.join(build_dir, 'src'), exist_ok=True)
resource_file = os.path.join(build_dir, 'src', 'check-writer.gresource')
gresource_xml = os.path.join(src_dir, 'check-writer.gresource.xml')

# Always compile resources to ensure latest UI templates are embedded
subprocess.run([
    'glib-compile-resources',
    f'--sourcedir={src_dir}',
    gresource_xml,
    f'--target={resource_file}'
], check=True)

# Register the GResource bundle (makes window.ui available)
resource = Gio.Resource.load(resource_file)
resource._register()

# Add project root to sys.path and launch the application
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.main import CheckWriterApplication

if __name__ == '__main__':
    app = CheckWriterApplication()
    sys.exit(app.run(sys.argv))
