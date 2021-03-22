# ------------------------------------------------------------------------------
# Makefile for zhmccli project
#
# Basic prerequisites for running this Makefile, to be provided manually:
#   One of these OS platforms:
#     Windows with CygWin
#     Linux (any)
#     OS-X
#   These commands on all OS platforms:
#     make (GNU make)
#     bash
#     rm, mv, find, tee, which
#   These commands on all OS platforms in the active Python environment:
#     python (or python3 on OS-X)
#     pip (or pip3 on OS-X)
#     twine
#   These commands on Linux and OS-X:
#     uname
# Environment variables:
#   PYTHON_CMD: Python command to use (OS-X needs to distinguish Python 2/3)
#   PIP_CMD: Pip command to use (OS-X needs to distinguish Python 2/3)
#   PACKAGE_LEVEL: minimum/latest - Level of Python dependent packages to use
# Additional prerequisites for running this Makefile are installed by running:
#   make develop
# ------------------------------------------------------------------------------

# Python / Pip commands
ifndef PYTHON_CMD
  PYTHON_CMD := python
endif
ifndef PIP_CMD
  PIP_CMD := pip
endif

# Package level
ifndef PACKAGE_LEVEL
  PACKAGE_LEVEL := latest
endif
ifeq ($(PACKAGE_LEVEL),minimum)
  pip_level_opts := -c minimum-constraints.txt
  pip_level_opts_new :=
else
  ifeq ($(PACKAGE_LEVEL),latest)
    pip_level_opts := --upgrade
    pip_level_opts_new := --upgrade-strategy eager
  else
    $(error Error: Invalid value for PACKAGE_LEVEL variable: $(PACKAGE_LEVEL))
  endif
endif

# Determine OS platform make runs on.
ifeq ($(OS),Windows_NT)
  ifdef PWD
	  # CygWin, Msys, etc.
    PLATFORM := Windows_UNIX
  else
    PLATFORM := Windows_native
    ifdef COMSPEC
      SHELL := $(subst \,/,$(COMSPEC))
    else
      SHELL := cmd.exe
    endif
    .SHELLFLAGS := /c
  endif
else
  # Values: Linux, Darwin
  PLATFORM := $(shell uname -s)
endif

ifeq ($(PLATFORM),Windows_native)
  # Note: The substituted backslashes must be doubled.
  # Remove files (blank-separated list of wildcard path specs)
  RM_FUNC = del /f /q $(subst /,\\,$(1))
  # Remove files recursively (single wildcard path spec)
  RM_R_FUNC = del /f /q /s $(subst /,\\,$(1))
  # Remove directories (blank-separated list of wildcard path specs)
  RMDIR_FUNC = rmdir /q /s $(subst /,\\,$(1))
  # Remove directories recursively (single wildcard path spec)
  RMDIR_R_FUNC = rmdir /q /s $(subst /,\\,$(1))
  # Copy a file, preserving the modified date
  CP_FUNC = copy /y $(subst /,\\,$(1)) $(subst /,\\,$(2))
  ENV = set
  WHICH = where
else
  RM_FUNC = rm -f $(1)
  RM_R_FUNC = find . -type f -name '$(1)' -delete
  RMDIR_FUNC = rm -rf $(1)
  RMDIR_R_FUNC = find . -type d -name '$(1)' | xargs -n 1 rm -rf
  CP_FUNC = cp -r $(1) $(2)
  ENV = env | sort
  WHICH = which
endif

# Name of this Python package (top-level Python namespace + Pypi package name)
package_name := zhmccli

# Package version (full version, including any pre-release suffixes, e.g. "0.1.0.dev1")
# Note: The package version is defined in zhmcclient/_version.py.
package_version := $(shell $(PYTHON_CMD) setup.py --version)

# Python versions
python_version := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('{v[0]}.{v[1]}.{v[2]}'.format(v=sys.version_info))")
pymn := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('py{v[0]}{v[1]}'.format(v=sys.version_info))")
python_m_version := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('{v[0]}'.format(v=sys.version_info))")
python_mn_version := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('{v[0]}.{v[1]}'.format(v=sys.version_info))")

# Directory for the generated distribution files
dist_dir := dist

# Distribution archives (as built by setup.py)
bdist_file := $(dist_dir)/$(package_name)-$(package_version)-py2.py3-none-any.whl
sdist_file := $(dist_dir)/$(package_name)-$(package_version).tar.gz

# Windows installable (as built by setup.py)
win64_dist_file := $(dist_dir)/$(package_name)-$(package_version).win-amd64.exe

# dist_files := $(bdist_file) $(sdist_file) $(win64_dist_file)
dist_files := $(bdist_file) $(sdist_file)

# Source files in the package
package_py_files := \
    $(wildcard $(package_name)/*.py) \
    $(wildcard $(package_name)/*/*.py) \

# Directory for generated API documentation
doc_build_dir := build_doc

# Directory where Sphinx conf.py is located
doc_conf_dir := docs

# Documentation generator command
doc_cmd := sphinx-build
doc_opts := -v -d $(doc_build_dir)/doctrees -c $(doc_conf_dir) .

# Dependents for Sphinx documentation build
doc_dependent_files := \
    $(doc_conf_dir)/conf.py \
    $(wildcard $(doc_conf_dir)/*.rst) \
    $(package_py_files) \

# Directory with test source files
test_dir := tests

# Source files with test code
test_py_files := \
    $(wildcard $(test_dir)/*.py) \
    $(wildcard $(test_dir)/*/*.py) \
    $(wildcard $(test_dir)/*/*/*.py) \

# Determine whether py.test has the --no-print-logs option.
pytest_no_log_opt := $(shell py.test --help 2>/dev/null |grep '\--no-print-logs' >/dev/null; if [ $$? -eq 0 ]; then echo '--no-print-logs'; else echo ''; fi)

# Flake8 config file
flake8_rc_file := .flake8

# PyLint config file
pylint_rc_file := .pylintrc

# PyLint additional options
pylint_opts := --disable=fixme

# Source files for check (with PyLint and Flake8)
check_py_files := \
    setup.py \
    $(package_py_files) \
    $(test_py_files) \

ifdef TESTCASES
  pytest_opts := $(TESTOPTS) -k $(TESTCASES)
else
  pytest_opts := $(TESTOPTS)
endif

ifeq ($(pymn),py34)
  pytest_cov_opts :=
else
  pytest_cov_opts := --cov $(package_name) --cov-config .coveragerc --cov-report=html
endif

# Files to be built
ifeq ($(PLATFORM),Windows_native)
build_files := $(win64_dist_file)
else
build_files := $(bdist_file) $(sdist_file)
endif

# Files the distribution archive depends upon.
dist_dependent_files := \
    setup.py \
    README.rst \
    requirements.txt \
    $(package_py_files) \

# No built-in rules needed:
.SUFFIXES:

.PHONY: help
help:
	@echo "Makefile for $(package_name) project"
	@echo "Package version will be: $(package_version)"
	@echo ""
	@echo "Make targets:"
	@echo '  install    - Install package in active Python environment'
	@echo '  develop    - Prepare the development environment by installing prerequisites'
	@echo '  check      - Run Flake8 on sources'
	@echo '  pylint     - Run PyLint on sources'
	@echo '  test       - Run tests (and test coverage)'
	@echo '               Does not include install but depends on it, so make sure install is current.'
	@echo '               Env.var TESTCASES can be used to specify a py.test expression for its -k option'
	@echo '  build      - Build the distribution files in: $(dist_dir)'
	@echo '               On Windows, builds: $(win64_dist_file)'
	@echo '               On Linux + OSX, builds: $(bdist_file) $(sdist_file)'
	@echo '  builddoc   - Build documentation in: $(doc_build_dir)'
	@echo '  all        - Do all of the above'
	@echo '  uninstall  - Uninstall package from active Python environment'
	@echo '  upload     - Upload the distribution files to PyPI (includes uninstall+build)'
	@echo '  clean      - Remove any temporary files'
	@echo '  clobber    - Remove any build products (includes uninstall+clean)'
	@echo "  platform   - Display the information about the platform as seen by make"
	@echo "  pip_list   - Display the Python packages as seen by make"
	@echo "  env        - Display the environment as seen by make"
	@echo 'Environment variables:'
	@echo "  TESTCASES=... - Testcase filter for pytest -k"
	@echo "  TESTOPTS=... - Additional options for pytest"
	@echo "  PACKAGE_LEVEL - Package level to be used for installing dependent Python"
	@echo "      packages in 'install' and 'develop' targets:"
	@echo "        latest - Latest package versions available on Pypi"
	@echo "        minimum - A minimum version as defined in minimum-constraints.txt"
	@echo "      Optional, defaults to 'latest'."
	@echo '  PYTHON_CMD=... - Name of python command. Default: python'
	@echo '  PIP_CMD=... - Name of pip command. Default: pip'

.PHONY: platform
platform:
	@echo "Makefile: Platform information as seen by make:"
	@echo "Platform: $(PLATFORM)"
	@echo "Shell used for commands: $(SHELL)"
	@echo "Shell flags: $(.SHELLFLAGS)"
	@echo "Make version: $(MAKE_VERSION)"
	@echo "Python command name: $(PYTHON_CMD)"
	@echo "Python command location: $(shell $(WHICH) $(PYTHON_CMD))"
	@echo "Python version: $(python_version)"
	@echo "Pip command name: $(PIP_CMD)"
	@echo "Pip command location: $(shell $(WHICH) $(PIP_CMD))"
	@echo "$(package_name) package version: $(package_version)"

.PHONY: pip_list
pip_list:
	@echo "Makefile: Python packages as seen by make:"
	$(PIP_CMD) list

.PHONY: env
env:
	@echo "Makefile: Environment variables as seen by make:"
	$(ENV)

.PHONY: _check_version
_check_version:
ifeq (,$(package_version))
	$(error Package version could not be determined)
endif

base_$(pymn).done: Makefile base-requirements.txt
	-$(call RM_FUNC,$@)
	@echo "Installing/upgrading pip, setuptools and wheel with PACKAGE_LEVEL=$(PACKAGE_LEVEL)"
	$(PYTHON_CMD) -m pip install $(pip_level_opts) -r base-requirements.txt
	echo "done" >$@

.PHONY: develop
develop: develop_$(pymn).done
	@echo "Makefile: $@ done."

develop_$(pymn).done: base_$(pymn).done install_$(pymn).done dev-requirements.txt requirements.txt
	@echo 'Installing runtime and development requirements with PACKAGE_LEVEL=$(PACKAGE_LEVEL)'
	$(PIP_CMD) install $(pip_level_opts) $(pip_level_opts_new) -r dev-requirements.txt
	echo "done" >$@

.PHONY: build
build: $(build_files)
	@echo "Makefile: $@ done."

.PHONY: builddoc
builddoc: html
	@echo "Makefile: $@ done."

.PHONY: html
html: $(doc_build_dir)/html/docs/index.html
	@echo "Makefile: $@ done."

$(doc_build_dir)/html/docs/index.html: Makefile $(doc_dependent_files)
	-$(call RM_FUNC,$@)
	$(doc_cmd) -b html $(doc_opts) $(doc_build_dir)/html
	@echo "Done: Created the HTML pages with top level file: $@"

.PHONY: pdf
pdf: Makefile $(doc_dependent_files)
	-$(call RM_FUNC,$@)
	$(doc_cmd) -b latex $(doc_opts) $(doc_build_dir)/pdf
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(doc_build_dir)/pdf all-pdf
	@echo "Done: Created the PDF files in: $(doc_build_dir)/pdf/"
	@echo "Makefile: $@ done."

.PHONY: man
man: Makefile $(doc_dependent_files)
	-$(call RM_FUNC,$@)
	$(doc_cmd) -b man $(doc_opts) $(doc_build_dir)/man
	@echo "Done: Created the manual pages in: $(doc_build_dir)/man/"
	@echo "Makefile: $@ done."

.PHONY: docchanges
docchanges:
	$(doc_cmd) -b changes $(doc_opts) $(doc_build_dir)/changes
	@echo
	@echo "Done: Created the doc changes overview file in: $(doc_build_dir)/changes/"
	@echo "Makefile: $@ done."

.PHONY: doclinkcheck
doclinkcheck:
	$(doc_cmd) -b linkcheck $(doc_opts) $(doc_build_dir)/linkcheck
	@echo
	@echo "Done: Look for any errors in the above output or in: $(doc_build_dir)/linkcheck/output.txt"
	@echo "Makefile: $@ done."

.PHONY: doccoverage
doccoverage:
	$(doc_cmd) -b coverage $(doc_opts) $(doc_build_dir)/coverage
	@echo "Done: Created the doc coverage results in: $(doc_build_dir)/coverage/python.txt"
	@echo "Makefile: $@ done."

.PHONY: check
check: flake8_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: pylint
pylint: pylint_$(pymn).done
	@echo "Makefile: $@ done."

.PHONY: install
install: install_$(pymn).done
	@echo "Makefile: $@ done."

install_$(pymn).done: base_$(pymn).done requirements.txt setup.py
	@echo 'Installing $(package_name) (editable) with PACKAGE_LEVEL=$(PACKAGE_LEVEL)'
	$(PIP_CMD) install $(pip_level_opts) $(pip_level_opts_new) -r requirements.txt
	$(PIP_CMD) install -e .
	$(WHICH) zhmc
	zhmc --version
	@echo 'Done: Installed $(package_name)'
	echo "done" >$@

.PHONY: uninstall
uninstall:
	bash -c '$(PIP_CMD) show $(package_name) >/dev/null; if [ $$? -eq 0 ]; then $(PIP_CMD) uninstall -y $(package_name); fi'
	@echo "Makefile: $@ done."

.PHONY: clobber
clobber: clean
	-$(call RM_FUNC,*.done $(dist_files))
	-$(call RMDIR_FUNC,$(doc_build_dir) htmlcov .tox)
	@echo 'Done: Removed all build products to get to a fresh state.'
	@echo "Makefile: $@ done."

.PHONY: clean
clean:
	-$(call RM_R_FUNC,*.pyc)
	-$(call RM_R_FUNC,*.tmp)
	-$(call RM_R_FUNC,tmp_*)
	-$(call RMDIR_R_FUNC,__pycache__)
	-$(call RMDIR_R_FUNC,.pytest_cache)
	-$(call RM_FUNC,MANIFEST MANIFEST.in AUTHORS ChangeLog .coverage)
	-$(call RMDIR_FUNC,build .cache $(package_name).egg-info .eggs)
	@echo 'Done: Cleaned out all temporary files.'
	@echo "Makefile: $@ done."

.PHONY: all
all: install develop check pylint test build builddoc
	@echo "Makefile: $@ done."

.PHONY: upload
upload: _check_version uninstall $(dist_files)
ifeq (,$(findstring .dev,$(package_version)))
	@echo '==> This will upload $(package_name) version $(package_version) to PyPI!'
	@echo -n '==> Continue? [yN] '
	@bash -c 'read answer; if [ "$$answer" != "y" ]; then echo "Aborted."; false; fi'
	twine upload $(dist_files)
	@echo 'Done: Uploaded $(package_name) version to PyPI: $(package_version)'
	@echo "Makefile: $@ done."
else
	@echo 'Error: A development version $(package_version) of $(package_name) cannot be uploaded to PyPI!'
	@false
endif

# Distribution archives.
$(bdist_file): _check_version Makefile $(dist_dependent_files)
ifneq ($(PLATFORM),Windows_native)
	-$(call RMDIR_FUNC,build $(package_name).egg-info .eggs)
	$(PYTHON_CMD) setup.py bdist_wheel -d $(dist_dir) --universal
	@echo 'Done: Created binary distribution archive: $@'
else
	@echo 'Error: Creating binary distribution archive requires to run on Linux or OSX'
	@false
endif

$(sdist_file): _check_version Makefile $(dist_dependent_files)
ifneq ($(PLATFORM),Windows_native)
	-$(call RMDIR_FUNC,build $(package_name).egg-info .eggs)
	$(PYTHON_CMD) setup.py sdist -d $(dist_dir)
	@echo 'Done: Created source distribution archive: $@'
else
	@echo 'Error: Creating source distribution archive requires to run on Linux or OSX'
	@false
endif

$(win64_dist_file): _check_version Makefile $(dist_dependent_files)
ifeq ($(PLATFORM),Windows_native)
	-$(call RMDIR_FUNC,build $(package_name).egg-info .eggs)
	$(PYTHON_CMD) setup.py bdist_wininst -d $(dist_dir) -o -t "$(package_name) v$(package_version)"
	@echo 'Done: Created Windows installable: $@'
else
	@echo 'Error: Creating Windows installable requires to run on native Windows'
	@false
endif

# TODO: Once PyLint has no more errors, remove the dash "-"
pylint_$(pymn).done: develop_$(pymn).done Makefile $(pylint_rc_file) $(check_py_files)
ifeq ($(python_m_version),2)
	@echo "Makefile: Warning: Skipping Pylint on Python $(python_version)" >&2
else
ifeq ($(python_mn_version),3.4)
	@echo "Makefile: Warning: Skipping Pylint on Python $(python_version)" >&2
else
ifeq ($(python_mn_version),3.5)
	@echo "Makefile: Warning: Skipping Pylint on Python $(python_version)" >&2
else
	@echo "Makefile: Running Pylint"
	-$(call RM_FUNC,$@)
	pylint $(pylint_opts) --rcfile=$(pylint_rc_file) --output-format=text $(check_py_files)
	echo "done" >$@
	@echo "Makefile: Done running Pylint"
endif
endif
endif

flake8_$(pymn).done: develop_$(pymn).done Makefile $(flake8_rc_file) $(check_py_files)
	-$(call RM_FUNC,$@)
	flake8 $(check_py_files)
	echo "done" >$@

.PHONY: test
test: Makefile $(package_py_files) $(test_py_files) .coveragerc
	py.test $(pytest_no_log_opt) -s $(test_dir) $(pytest_cov_opts) $(pytest_opts)
	@echo "Makefile: $@ done."
