HeaderFix
=========

HeaderFix is a tool for fixing copyright notices, header guards,
'extern "C"' declarations, and miscellaneous other issues with source
code and header files.

It is designed to operate on source code in a Git repository.  The
tool will fail if you try to run it outside a Git repository, this is
intentional.

Configuration
-------------

You can configure the tool by adding files named '.header' to your
repository.  These files will apply settings to any files in the
directory and to directories below.

Settings are configured by assignment, e.g.:

    tabsize = 8

Certain variables (like 'ignore') need no value, so they can be
specified without one:

    ignore

Longer values can be assigned using heredoc syntax, e.g.:

    copyright_notice = <<EOF
    All rights reserved.
    EOF

The available settings are:

* 'ignore': Any file with this setting is ignored.  Note that files
  that match patterns in .gitignore file will also be ignored.  The
  value and equals sign can be omitted, otherwise this is a boolean
  setting.

* 'guardname': For header files, this specifies the identifier used
  for the header guard.  For directories, this specifies the prefix
  for the header guard identifier, and the filename / directory name
  will be appended for directories and subdirectories.

* 'guards': A boolean (true or false) indicating that header guards
  should be added to headers.

* 'width': The maximum width, in characters, of lines of source code,
  not including the line break.  Lines wider than this will trigger
  warnings, but you will have to manually reformat those lines.

* 'tabsize': The width of a tab, when tabs are converted to spaces.

* 'extern_c': Whether an 'extern "C"' block is added to header files.

* 'copyright_notice': The copyright notice (or license), not including
  the actual authorship information, that is added to the top of each
  file.

* 'fix_copyright': A boolean.  If set to false, copyright notices will
  not be added or modified.

You can put settings in groups and apply them to certain files based
on glob patterns.  Groups are enclosed in braces '{' and '}', each on
a separate line.  Patterns for a group are specified by lines starting
with '+' for positive patterns or '-' for negative patterns.

Example
-------

Here is an example configuration file:

    guards = true
    guardname = MYLIB
    width = 78
    tabsize = 4
    copyright_notice = <<EOF
    All rights reserved.
    EOF

    {
        + /subdir
        ignore
    }

    {
        + /include
        {
            + *.h
            extern_c = true
        }
    }

You can try running the header script using this configuration by
running

    $ ./headerfix.sh example
