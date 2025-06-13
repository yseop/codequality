#! /usr/bin/env bash

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

# Print a command before running it.
# (This function takes care of running it).
#
# $@    The words making up the command to run.
log_and_run() {
    log 'Running: %s' "${*@Q}"
    "$@"
}
