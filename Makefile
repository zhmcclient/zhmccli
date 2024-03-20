# ------------------------------------------------------------------------------
# Makefile for zhmccli project
#
# Basic prerequisites for running this Makefile, to be provided manually:
#   One of these OS platforms:
#     Windows with CygWin
#     Linux (any)
#     macOS (OS-X)
#   These commands on all OS platforms:
#     make (GNU make)
#     bash
#     rm, mv, find, tee, which
#   These commands on all OS platforms in the active Python environment:
#     python
#     pip
#     twine
#   These commands on Linux and macOS:
#     uname
# Environment variables:
#   PYTHON_CMD: Python command to use
#   PIP_CMD: Pip command to use
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

# Run type (normal, scheduled, release)
ifndef RUN_TYPE
  RUN_TYPE := normal
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

# Default path names of HMC inventory and vault files used for end2end tests.
# Keep in sync with zhmcclient/testutils/_hmc_definitions.py
default_testinventory := $HOME/.zhmc_inventory.yaml
default_testvault := $HOME/.zhmc_vault.yaml

# Default group name or HMC nickname in HMC inventory file to test against.
# Keep in sync with zhmcclient/testutils/_hmc_definitions.py
default_testhmc := default

# Name of this Python package (top-level Python namespace + Pypi package name)
package_name := zhmccli

# Package version (full version, including any pre-release suffixes, e.g. "0.1.0.dev1")
# Note: The package version is defined in zhmcclient/_version.py.
package_version := $(shell $(PYTHON_CMD) setup.py --version)

# Python versions
python_version := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('{v[0]}.{v[1]}.{v[2]}'.format(v=sys.version_info))")
python_mn_version := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('{v[0]}.{v[1]}'.format(v=sys.version_info))")
pymn := $(shell $(PYTHON_CMD) -c "import sys; sys.stdout.write('py{v[0]}{v[1]}'.format(v=sys.version_info))")

# Directory for the generated distribution files
dist_dir := dist

# Distribution archives (as built by 'build' tool)
bdist_file := $(dist_dir)/$(package_name)-$(package_version)-py2.py3-none-any.whl
sdist_file := $(dist_dir)/$(package_name)-$(package_version).tar.gz

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

# Source files with unit test code
test_unit_py_files := \
    $(wildcard $(test_dir)/unit/*.py) \
    $(wildcard $(test_dir)/unit/*/*.py) \
    $(wildcard $(test_dir)/unit/*/*/*.py) \

# Source files with function test code
test_function_py_files := \
    $(wildcard $(test_dir)/function/*.py) \
    $(wildcard $(test_dir)/function/*/*.py) \
    $(wildcard $(test_dir)/function/*/*/*.py) \

# Source files with end2end test code
test_end2end_py_files := \
    $(wildcard $(test_dir)/end2end/*.py) \
    $(wildcard $(test_dir)/end2end/*/*.py) \
    $(wildcard $(test_dir)/end2end/*/*/*.py) \

# Directory for .done files
done_dir := done

# Determine whether py.test has the --no-print-logs option.
pytest_no_log_opt := $(shell py.test --help 2>/dev/null |grep '\--no-print-logs' >/dev/null; if [ $$? -eq 0 ]; then echo '--no-print-logs'; else echo ''; fi)

# Flake8 config file
flake8_rc_file := .flake8

# PyLint config file
pylint_rc_file := .pylintrc

# PyLint additional options
pylint_opts := --disable=fixme

#Safety policy file (for packages needed for installation)
safety_install_policy_file := .safety-policy-install.yml
safety_all_policy_file := .safety-policy-all.yml

# Source files for check (with PyLint and Flake8)
check_py_files := \
    setup.py \
    $(package_py_files) \
    $(test_unit_py_files) \
		$(test_function_py_files) \
    $(test_end2end_py_files) \

# Packages whose dependencies are checked using pip-missing-reqs
ifeq ($(python_mn_version),3.6)
  check_reqs_packages := pip_check_reqs virtualenv tox pipdeptree build pytest coverage coveralls flake8 pylint twine
else
ifeq ($(python_mn_version),3.7)
  check_reqs_packages := pip_check_reqs virtualenv tox pipdeptree build pytest coverage coveralls flake8 pylint twine safety
else
  check_reqs_packages := pip_check_reqs virtualenv tox pipdeptree build pytest coverage coveralls flake8 pylint twine safety sphinx
endif
endif

ifdef TESTCASES
  pytest_opts := $(TESTOPTS) -k "$(TESTCASES)"
else
  pytest_opts := $(TESTOPTS)
endif

pytest_cov_opts := --cov $(package_name) --cov-config .coveragerc --cov-append --cov-report=html
pytest_cov_files := .coveragerc

# Files the distribution archive depends upon.
# This is also used for 'include' statements in MANIFEST.in.
# Wildcards can be used directly (i.e. without wildcard function).
dist_included_files := \
    setup.py \
    LICENSE \
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
	@echo "  check_reqs - Perform missing dependency checks"
	@echo '  check      - Run Flake8 on sources'
	@echo '  pylint     - Run PyLint on sources'
	@echo '  safety     - Run safety on sources'
	@echo '  test       - Run function tests (adds to coverage results)'
	@echo '               Does not include install but depends on it, so make sure install is current.'
	@echo '               Env.var TESTCASES can be used to specify a py.test expression for its -k option'
	@echo '  build      - Build the distribution files in $(dist_dir): $(dist_files)'
	@echo '  builddoc   - Build documentation in: $(doc_build_dir)'
	@echo '  all        - Do all of the above'
	@echo "  end2end    - Run end2end tests (adds to coverage results)"
	@echo "  end2end_show - Show HMCs defined for end2end tests"
	@echo '  authors    - Generate AUTHORS.md file from git log'
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
	@echo "  TESTHMC=... - HMC group or host name in HMC inventory file to be used in end2end tests. Default: $(default_testhmc)"
	@echo "  TESTINVENTORY=... - Path name of HMC inventory file used in end2end tests. Default: $(default_testinventory)"
	@echo "  TESTVAULT=... - Path name of HMC vault file used in end2end tests. Default: $(default_testvault)"
	@echo "  TESTRESOURCES=... - The resources to test with in end2end tests, as follows:"
	@echo "      random - one random choice from the complete list of resources (default)"
	@echo "      all - the complete list of resources"
	@echo "      <pattern> - the resources with names matching the regexp pattern"
	@echo "  TESTLOG=1 - Enable logging for end2end tests"
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

$(done_dir)/base_$(pymn)_$(PACKAGE_LEVEL).done: Makefile base-requirements.txt minimum-constraints.txt minimum-constraints-install.txt
	-$(call RM_FUNC,$@)
	@echo "Installing/upgrading pip, setuptools and wheel with PACKAGE_LEVEL=$(PACKAGE_LEVEL)"
	$(PYTHON_CMD) -m pip install $(pip_level_opts) -r base-requirements.txt
	echo "done" >$@

.PHONY: develop
develop: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

$(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/base_$(pymn)_$(PACKAGE_LEVEL).done $(done_dir)/install_$(pymn)_$(PACKAGE_LEVEL).done dev-requirements.txt requirements.txt minimum-constraints.txt minimum-constraints-install.txt
	@echo 'Installing runtime and development requirements with PACKAGE_LEVEL=$(PACKAGE_LEVEL)'
	$(PYTHON_CMD) -m pip install $(pip_level_opts) $(pip_level_opts_new) -r dev-requirements.txt
	echo "done" >$@

.PHONY: build
build: $(dist_files)
	@echo "Makefile: $@ done."

.PHONY: builddoc
builddoc: html
	@echo "Makefile: $@ done."

.PHONY: html
html: $(doc_build_dir)/html/docs/index.html
	@echo "Makefile: $@ done."

# Boolean variable indicating that Sphinx should be run
# We run Sphinx only on Python>=3.8 because lower Python versions require too old Sphinx versions
run_sphinx := $(shell $(PYTHON_CMD) -c "import sys; py=sys.version_info[0:2]; sys.stdout.write('true' if py>=(3,8) else 'false')")

$(doc_build_dir)/html/docs/index.html: Makefile $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done  $(doc_dependent_files)
ifeq ($(run_sphinx),true)
	@echo "Running Sphinx to create HTML pages"
	-$(call RM_FUNC,$@)
	$(doc_cmd) -b html $(doc_opts) $(doc_build_dir)/html
	@echo "Done: Created the HTML pages with top level file: $@"
else
	@echo "Skipping Sphinx to create HTML pages on Python version $(python_version)"
endif

.PHONY: pdf
pdf: Makefile $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(doc_dependent_files)
ifeq ($(run_sphinx),true)
	@echo "Running Sphinx to create PDF files"
	-$(call RM_FUNC,$@)
	$(doc_cmd) -b latex $(doc_opts) $(doc_build_dir)/pdf
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(doc_build_dir)/pdf all-pdf
	@echo "Done: Created the PDF files in: $(doc_build_dir)/pdf/"
else
	@echo "Skipping Sphinx to create PDF files on Python version $(python_version)"
endif
	@echo "Makefile: $@ done."

.PHONY: man
man: Makefile $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(doc_dependent_files)
ifeq ($(run_sphinx),true)
	@echo "Running Sphinx to create manual pages"
	-$(call RM_FUNC,$@)
	$(doc_cmd) -b man $(doc_opts) $(doc_build_dir)/man
	@echo "Done: Created the manual pages in: $(doc_build_dir)/man/"
else
	@echo "Skipping Sphinx to create manual pages on Python version $(python_version)"
endif
	@echo "Makefile: $@ done."

.PHONY: docchanges
docchanges:
ifeq ($(run_sphinx),true)
	@echo "Running Sphinx to create doc changes overview file"
	$(doc_cmd) -b changes $(doc_opts) $(doc_build_dir)/changes
	@echo
	@echo "Done: Created the doc changes overview file in: $(doc_build_dir)/changes/"
else
	@echo "Skipping Sphinx to create doc changes overview file on Python version $(python_version)"
endif
	@echo "Makefile: $@ done."

.PHONY: doclinkcheck
doclinkcheck:
ifeq ($(run_sphinx),true)
	@echo "Running Sphinx to check doc links"
	$(doc_cmd) -b linkcheck $(doc_opts) $(doc_build_dir)/linkcheck
	@echo
	@echo "Done: Look for any errors in the above output or in: $(doc_build_dir)/linkcheck/output.txt"
else
	@echo "Skipping Sphinx to check doc links on Python version $(python_version)"
endif
	@echo "Makefile: $@ done."

.PHONY: doccoverage
doccoverage:
ifeq ($(run_sphinx),true)
	@echo "Running Sphinx to create doc coverage results"
	$(doc_cmd) -b coverage $(doc_opts) $(doc_build_dir)/coverage
	@echo "Done: Created the doc coverage results in: $(doc_build_dir)/coverage/python.txt"
else
	@echo "Skipping Sphinx to create doc coverage results on Python version $(python_version)"
endif
	@echo "Makefile: $@ done."

.PHONY: check
check: $(done_dir)/flake8_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

.PHONY: pylint
pylint: $(done_dir)/pylint_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

.PHONY: safety
safety: $(done_dir)/safety_all_$(pymn)_$(PACKAGE_LEVEL).done $(done_dir)/safety_install_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

.PHONY: install
install: $(done_dir)/install_$(pymn)_$(PACKAGE_LEVEL).done
	@echo "Makefile: $@ done."

$(done_dir)/install_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/base_$(pymn)_$(PACKAGE_LEVEL).done requirements.txt minimum-constraints.txt minimum-constraints-install.txt setup.py
	@echo 'Installing $(package_name) (editable) with PACKAGE_LEVEL=$(PACKAGE_LEVEL)'
	$(PYTHON_CMD) -m pip install $(pip_level_opts) $(pip_level_opts_new) -e .
	$(WHICH) zhmc
	zhmc --version
	@echo 'Done: Installed $(package_name)'
	echo "done" >$@

.PHONY: authors
authors: _check_version
	echo "# Authors of this project" >AUTHORS.md
	echo "" >>AUTHORS.md
	echo "Sorted list of authors derived from git commit history:" >>AUTHORS.md
	echo '```' >>AUTHORS.md
	git shortlog --summary --email | cut -f 2 | sort >>AUTHORS.md
	echo '```' >>AUTHORS.md
	@echo '$@ done.'

.PHONY: uninstall
uninstall:
	bash -c '$(PIP_CMD) show $(package_name) >/dev/null; if [ $$? -eq 0 ]; then $(PIP_CMD) uninstall -y $(package_name); fi'
	@echo "Makefile: $@ done."

.PHONY: clobber
clobber: clean
	-$(call RM_FUNC,$(dist_files))
	-$(call RM_R_FUNC,*.done)
	-$(call RMDIR_FUNC,$(doc_build_dir) htmlcov htmlcov.end2end s.tox)
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
all: install develop check_reqs check pylint test build builddoc
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

# Note: distutils depends on the right files specified in MANIFEST.in, even when
# they are already specified e.g. in 'package_data' in setup.py.
# We generate the MANIFEST.in file automatically, to have a single point of
# control (this Makefile) for what gets into the distribution archive.
MANIFEST.in: Makefile $(dist_included_files)
	@echo "Makefile: Creating the manifest input file"
	echo "# MANIFEST.in file generated by Makefile - DO NOT EDIT!!" >$@
ifeq ($(PLATFORM),Windows_native)
	for %%f in ($(dist_included_files)) do (echo include %%f >>$@)
else
	echo "$(dist_included_files)" | xargs -n 1 echo include >>$@
endif
	@echo "Makefile: Done creating the manifest input file: $@"

# Distribution archives.
# Note: Deleting MANIFEST causes distutils (setup.py) to read MANIFEST.in and to
# regenerate MANIFEST. Otherwise, changes in MANIFEST.in will not be used.
# Note: Deleting build is a safeguard against picking up partial build products
# which can lead to incorrect hashbangs in scripts in wheel archives.
$(bdist_file) $(sdist_file): _check_version Makefile MANIFEST.in $(dist_included_files)
	-$(call RM_FUNC,MANIFEST)
	-$(call RMDIR_FUNC,build $(package_name).egg-info .eggs)
	$(PYTHON_CMD) -m build --outdir $(dist_dir)
	@echo 'Done: Created distribution archives: $@'

# TODO: Once PyLint has no more errors, remove the dash "-"
$(done_dir)/pylint_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done Makefile $(pylint_rc_file) $(check_py_files)
	@echo "Makefile: Running Pylint"
	-$(call RM_FUNC,$@)
	pylint $(pylint_opts) --rcfile=$(pylint_rc_file) --output-format=text $(check_py_files)
	echo "done" >$@
	@echo "Makefile: Done running Pylint"

$(done_dir)/safety_all_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done Makefile $(safety_all_policy_file) minimum-constraints.txt minimum-constraints-install.txt
ifeq ($(python_m_version),2)
	@echo "Makefile: Warning: Skipping Safety for install packages on Python $(python_version)" >&2
else
ifeq ($(python_mn_version),3.5)
	@echo "Makefile: Warning: Skipping Safety for install packages on Python $(python_version)" >&2
else
ifeq ($(python_mn_version),3.6)
	@echo "Makefile: Warning: Skipping Safety for all packages on Python $(python_version)" >&2
else
	@echo "Makefile: Running Safety"
	-$(call RM_FUNC,$@)
	bash -c "safety check --policy-file $(safety_all_policy_file) -r minimum-constraints.txt --full-report || test '$(RUN_TYPE)' != 'release' || exit 1"
	echo "done" >$@
	@echo "Makefile: Done running Safety"
endif
endif
endif

$(done_dir)/safety_install_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done Makefile $(safety_install_policy_file) minimum-constraints-install.txt
ifeq ($(python_m_version),2)
	@echo "Makefile: Warning: Skipping Safety for install packages on Python $(python_version)" >&2
else
ifeq ($(python_mn_version),3.5)
	@echo "Makefile: Warning: Skipping Safety for install packages on Python $(python_version)" >&2
else
ifeq ($(python_mn_version),3.6)
	@echo "Makefile: Warning: Skipping Safety for install packages on Python $(python_version)" >&2
else
	@echo "Makefile: Running Safety for install packages"
	-$(call RM_FUNC,$@)
	safety check --policy-file $(safety_install_policy_file) -r minimum-constraints-install.txt --full-report
	echo "done" >$@
	@echo "Makefile: Done running Safety for install packages"
endif
endif
endif

$(done_dir)/flake8_$(pymn)_$(PACKAGE_LEVEL).done: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done Makefile $(flake8_rc_file) $(check_py_files)
	-$(call RM_FUNC,$@)
	flake8 $(check_py_files)
	echo "done" >$@

.PHONY: check_reqs
check_reqs: $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done minimum-constraints.txt minimum-constraints-install.txt requirements.txt
	@echo "Makefile: Checking missing dependencies of this package"
	pip-missing-reqs $(package_name) --requirements-file=requirements.txt
	pip-missing-reqs $(package_name) --requirements-file=minimum-constraints-install.txt
	@echo "Makefile: Done checking missing dependencies of this package"
ifeq ($(PLATFORM),Windows_native)
# Reason for skipping on Windows is https://github.com/r1chardj0n3s/pip-check-reqs/issues/67
	@echo "Makefile: Warning: Skipping the checking of missing dependencies of site-packages directory on native Windows" >&2
else
	@echo "Makefile: Checking missing dependencies of some development packages in our minimum versions"
	@rc=0; for pkg in $(check_reqs_packages); do dir=$$($(PYTHON_CMD) -c "import $${pkg} as m,os; dm=os.path.dirname(m.__file__); d=dm if not dm.endswith('site-packages') else m.__file__; print(d)"); cmd="pip-missing-reqs $${dir} --requirements-file=minimum-constraints.txt"; echo $${cmd}; $${cmd}; rc=$$(expr $${rc} + $${?}); done; exit $${rc}
	@echo "Makefile: Done checking missing dependencies of some development packages in our minimum versions"
endif
	@echo "Makefile: $@ done."

.PHONY: test
test: Makefile $(package_py_files) $(test_unit_py_files) $(test_function_py_files) $(pytest_cov_files)
	py.test $(pytest_no_log_opt) -s $(test_dir) $(pytest_cov_opts) $(pytest_opts)
	@echo "Makefile: $@ done."

.PHONY:	end2end
end2end: Makefile $(done_dir)/develop_$(pymn)_$(PACKAGE_LEVEL).done $(package_py_files) $(test_end2end_py_files) $(pytest_cov_files)
	-$(call RMDIR_R_FUNC,htmlcov.end2end)
	bash -c "TESTEND2END_LOAD=true py.test --color=yes $(pytest_no_log_opt) -v -s $(test_dir)/end2end $(pytest_cov_opts) $(pytest_opts)"
	@echo "Makefile: $@ done."

.PHONY:	end2end_show
end2end_show:
	bash -c "TESTEND2END_LOAD=true $(PYTHON_CMD) -c 'from zhmcclient.testutils import print_hmc_definitions; print_hmc_definitions()'"
