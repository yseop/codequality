#! /usr/bin/env python3

output_lines = []
current_indent_steps = 0
indent_size = 4

def indent():
    global current_indent_steps
    current_indent_steps += 1

def unindent():
    global current_indent_steps
    current_indent_steps -= 1

def add_line(new_line: str):
    output_lines.append(current_indent_steps * "\t" + new_line)

use_env = False

if use_env:
    add_line("#! /usr/bin/env bash")
else:
    add_line("#! /bin/bash")

indent()
indent()
add_line("# test comment")

# NB: Replace not working?
print("\n".join(output_lines).replace("\t", " " * indent_size))

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
  printf "%s %s${2}\n" "$prog" "$1" "${@:3}"
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
