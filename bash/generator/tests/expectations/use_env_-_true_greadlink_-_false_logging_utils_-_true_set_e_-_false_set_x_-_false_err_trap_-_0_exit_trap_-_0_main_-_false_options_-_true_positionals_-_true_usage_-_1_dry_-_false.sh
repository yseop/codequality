#! /usr/bin/env bash

BASEDIR=$(dirname "$(readlink -f -- "$0")")
# Adapt or remove the ROOTDIR definition depending
# on the depth of this script within the project.
ROOTDIR=$(dirname "$BASEDIR")
readonly BASEDIR ROOTDIR

readonly DEFAULT_BAR=/the/default/bar

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

print_help() {
    local prog
    prog=$(printf '%q' "$0")
    cat << _HELP_

  Perform blah blah on a blah blah.

  Usage:
    ${prog} [OPTIONS]... FOO [BAR]

  Arguments:
    FOO     The foo to process.
    BAR     (Optional) A bar in which to write the plop.
            This allows to blah blah.
            Default: “${DEFAULT_BAR}”

  Options:
    -y, --yo            Turn on yo mode.
    -p, --plop PLOP     Use PLOP as the plop.
    -h, --help          Print this message and exit.

  Environment variables:
    GIT_USER    Username for requests to GitHub.

_HELP_
}

# Fill up global “opt_*” and “arg_*” variables according to given
# options and positional parameters, and perform basic checks
# on the presence of mandatory info.
#
# $@    Arguments originally passed to the script itself.
parse_command() {
    # Clear all option-related variables before parsing.
    unset -v "${!opt_@}"

    local param
    local -a positionals=()
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

            -h|--help)
                print_help
                exit 0
                ;;

            -*)
                print_help >&2
                err 'Invalid option: %q' "$param"
                exit 1
                ;;

            *)
                positionals+=("$param")
                ;;
        esac
    done

    set -- "${positionals[@]}"
    arg_foo=$1
    arg_bar=${2:-${DEFAULT_BAR}}

    if [[ -z $arg_foo ]]
    then
        print_help
        err 'Missing mandatory parameter: foo'
        exit 1
    fi >&2
}

# ================================

parse_command "$@"

log 'Yo: %q; Plop: %q' "$opt_yo" "$opt_plop"
log 'Foo: %q; Bar: %q' "$arg_foo" "$arg_bar"

log 'TODO'

exit 0
