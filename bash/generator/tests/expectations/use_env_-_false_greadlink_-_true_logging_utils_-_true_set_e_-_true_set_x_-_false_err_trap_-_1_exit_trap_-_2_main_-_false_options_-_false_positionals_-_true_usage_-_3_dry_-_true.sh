#! /bin/bash

set -e

if type greadlink &> /dev/null
then
    BASEDIR=$(dirname "$(greadlink -f -- "$0")")
else
    BASEDIR=$(dirname "$(readlink -f -- "$0")")
fi
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
    prog=$(basename "$0"):${DRY:+ [DRY RUN]}
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

# Returns with 0 status if and only if
# the dry run mode is currently activated.
is_dry_run() {
    [[ $DRY ]]
}

# Only run a command if dry run mode is not activated.
# In dry run mode, log the command instead to show what
# would have been run in a normal context.
#
# $@    The words making up the command to potentially run.
run_if_not_dry() {
    if is_dry_run
    then
        log 'Would have run: %s' "${*@Q}"
    else
        "$@"
    fi
}

# Executed when a command fails, with the same exceptions as for “set -e”.
# See “trap” documentation in “man bash” for details.
err_trap() {
    err 'An error occurred.'
}

# Executed upon exit, regardless of the cause.
exit_trap() {
    rm -rf -- "$_temp_dir"
}

print_help() {
    local prog
    prog=$(printf '%q' "$0")
    cat << _HELP_

  Perform blah blah on a blah blah.

  Usage:
    ${prog} FOO [BAR]

  Arguments:
    FOO     The foo to process.
    BAR     (Optional) A bar in which to write the plop.
            This allows to blah blah.
            Default: “${DEFAULT_BAR}”

  Environment variables:
    GIT_USER    Username for requests to GitHub.
    DRY         If not empty, turn dry mode on.
                “Important” commands will be skipped.

_HELP_
}

# Fill up global “arg_*” variables according to given arguments
# and perform basic checks on the presence of mandatory info.
#
# $@    Arguments originally passed to the script itself.
parse_command() {
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

trap err_trap ERR

unset -v _temp_dir
trap exit_trap EXIT
_temp_dir=$(mktemp --directory)

parse_command "$@"
log 'Foo: %q; Bar: %q' "$arg_foo" "$arg_bar"

run_if_not_dry log 'TODO'

exit 0
