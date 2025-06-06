#! /usr/bin/env bash

set -x

BASEDIR=$(dirname "$(readlink -f -- "$0")")
# Adapt or remove the ROOTDIR definition depending
# on the depth of this script within the project.
ROOTDIR=$(dirname "$BASEDIR")
readonly BASEDIR ROOTDIR

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

# Executed upon exit, regardless of the cause.
exit_trap() {
    log 'Exiting.'
}

print_help() {
    local prog
    prog=$(printf '%q' "$0")
    cat << _HELP_

  Perform blah blah on a blah blah.

  Usage:
    ${prog} [OPTIONS]...

  Options:
    -y, --yo            Turn on yo mode.
    -p, --plop PLOP     Use PLOP as the plop.

  Environment variables:
    GIT_USER    Username for requests to GitHub.

_HELP_
}

# Fill up global “opt_*” variables according to given options
# and perform basic checks on the presence of mandatory info.
#
# $@    Arguments originally passed to the script itself.
parse_command() {
    if (($# == 0))
    then
        print_help
        exit 1
    fi

    # Clear all option-related variables before parsing.
    unset -v "${!opt_@}"

    local param
    while (($# > 0))
    do
        param=$1
        shift
        case $param in
            -y|--yo)
                opt_yo=1
                ;;

            -p|--plop)
                opt_plop=${1:?Missing argument for option: ${param}}
                shift
                ;;

            *)
                print_help >&2
                err 'Invalid option or extra parameter: %q' "$param"
                exit 1
                ;;
        esac
    done
}
# ================================

trap exit_trap EXIT

parse_command "$@"

log 'Yo: %q; Plop: %q' "$opt_yo" "$opt_plop"

log 'TODO'

exit 0
