pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'check_writer'
gnome = import('gnome')

gnome.compile_resources('check-writer',
  'check-writer.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'check-writer.in',
  output: 'check-writer',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr--r--'
)

check_writer_sources = [
  '__init__.py',
  'main.py',
  'window.py',
]

core_sources = [
  'core/__init__.py',
  'core/models.py',
  'core/converter.py',
  'core/database.py',
  'core/printer.py',
]

ui_sources = [
  'ui/__init__.py',
  'ui/check_canvas.py',
  'ui/writer_view.py',
  'ui/register_view.py',
  'ui/payees_view.py',
  'ui/preferences_dialog.py',
]

install_data(check_writer_sources, install_dir: moduledir)
install_data(core_sources, install_dir: moduledir / 'core')
install_data(ui_sources, install_dir: moduledir / 'ui')
