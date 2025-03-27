#! /usr/bin/env python3

from textwrap import dedent

# ================================================================

class Writer:
    """
    Preferences regarding indentation and so on,
    as well as utilities to generate a file.
    """

    def __init__(self, indent_size = 4):
        """
        Create a set of configuration rules for a file writer, and initialize the writer.

        args:
            indent_size (int): Number of spaces to use.
        """
        self.output_lines = []
        self.current_indent_steps = 0
        self.indent_size = indent_size

class FileConfig:
    """Details of what to include or not within the generated file, and how."""

    def __init__(self, use_env = True, greadlink = False, logging_utils = True):
        """
        Create a set of configuration rules for a generated file.

        args:
            use_env (bool):         Shebang with env or direct Bash path.
            greadlink (bool):       Whether to include Mac compatibility trick for BASEDIR.
            logging_utils (bool):   Include a set of logging functions.
        """
        self.use_env = use_env
        self.greadlink = greadlink
        self.logging_utils = logging_utils

# ================================================================

def indent():
    writer.current_indent_steps += 1

def unindent():
    writer.current_indent_steps -= 1

def is_blank(s: str):
    return not str.strip

def add_line(new_line: str = None):
    """
    Register an automatically indented line.
    The argument is not expected to contain a newline character.
    To register a blank, unindented line, pass no argument at all.
    """
    if new_line is None or is_blank(new_line):
        # Avoid getting just a bunch of indentation spaces or whatever on the line.
        writer.output_lines.append("")
    else:
        writer.output_lines.append(writer.current_indent_steps * "\t" + new_line)

def add_lines(text: str):
    """
    Register multiple lines at once.
    Indentation in the input is expected to be done via four spaces
    and will be converted.
    For simplicity’s sake, the current implementation is a bit brutal
    in this conversion and replaces any occurrence of four consecutive spaces,
    not just those that stand at the beginning of a line.
    """
    for line in dedent(text).splitlines():
        add_line(line.replace("    ", "\t"))

def print_output_lines():
    # Merge lines.
    result = "\n".join(writer.output_lines)
    # Use the right indentation kind of width.
    result = result.replace("\t", " " * writer.indent_size)
    print(result)


# ↓ FUNCTIONS DEFINING FILE PARTS ↓

def part_shebang():
    if conf.use_env:
        add_line("#! /usr/bin/env bash")
    else:
        add_line("#! /bin/bash")

def part_basedir():
    if conf.greadlink:
        add_lines("""\
        if type greadlink &> /dev/null
        then
            BASEDIR=$(dirname "$(greadlink -f -- "$0")")
        else
            BASEDIR=$(dirname "$(readlink -f -- "$0")")
        fi""")
    add_line("readonly BASEDIR")

def part_logging_utils():
    add_lines("""\
    # For internal use via the logging functions below.
    #
    # $1    String added between the program name and the message,
    #       typically to specify the log level.
    # $2    Printf-style format string.
    # $3…n  Arguments for printf.
    _f_log() {
        local prog
        prog=$(basename "$0"):
        printf "%s %s${2}\\n" "$prog" "$1" "${@:3}"
    }

    # $1    Printf-style format string.
    # $2…n  Arguments for printf.
    log() {
        _f_log '   INFO  ' "$@"
    }

    # $1    Printf-style format string.
    # $2…n  Arguments for printf.
    warn() {
        _f_log 'WARNING  ' "$@" >&2
    }

    # $1    Printf-style format string.
    # $2…n  Arguments for printf.
    err() {
        _f_log '  ERROR  ' "$@" >&2
    }""")

# ↑ FUNCTIONS DEFINING FILE PARTS ↑

# ================================================================

if __name__ == "__main__":
    writer = Writer()
    conf = FileConfig()

    # Register all the lines of the future file.
    part_shebang()
    add_line()
    part_basedir()
    if conf.logging_utils:
        add_line()
        part_logging_utils()

    # Generate the file.
    print_output_lines()
