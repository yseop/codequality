#! /usr/bin/env python3

def init_writer():
    global output_lines
    output_lines = []
    global current_indent_steps
    current_indent_steps = 0
    global indent_size
    indent_size = 4

def indent():
    global current_indent_steps
    current_indent_steps += 1

def unindent():
    global current_indent_steps
    current_indent_steps -= 1

def add_line(new_line: str):
    output_lines.append(current_indent_steps * "\t" + new_line)

def print_output_lines():
    # Merge lines.
    result = "\n".join(output_lines)
    # Use the right indentation kind of width.
    result = result.replace("\t", " " * indent_size)
    print(result)

if __name__ == "__main__":
    init_writer()

    # Dummy-ish config. To be improved.
    use_env = False
    # End of dummy config.

    if use_env:
        add_line("#! /usr/bin/env bash")
    else:
        add_line("#! /bin/bash")

    print("""
    if type greadlink &> /dev/null
    then
      BASEDIR=$(dirname "$(greadlink -f -- "$0")")
    else
      BASEDIR=$(dirname "$(readlink -f -- "$0")")
    fi
    readonly BASEDIR

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
    }

    log 'Hello.'
    """)
