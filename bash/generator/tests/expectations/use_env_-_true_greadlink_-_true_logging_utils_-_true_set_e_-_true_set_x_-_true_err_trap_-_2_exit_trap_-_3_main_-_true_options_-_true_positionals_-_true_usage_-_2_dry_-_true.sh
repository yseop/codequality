#! /usr/bin/env bash

set -eEx

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
    rm -rf -- "${_to_be_deleted[@]}"
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
    --dry               Turn dry mode on.

  Environment variables:
    GIT_USER    Username for requests to GitHub.
    DRY         If not empty, turn dry mode on.
                “Important” commands will be skipped.

_HELP_
}

# Fill up global “opt_*” and “arg_*” variables according to given
# options and positional parameters, and perform basic checks
# on the presence of mandatory info.
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

            --dry)
                DRY=1
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

main() {
    trap err_trap ERR

    unset -v _to_be_deleted
    _to_be_deleted=()
    trap exit_trap EXIT
    _some_dir=$(mktemp --directory)
    _to_be_deleted+=("$_some_dir")

    parse_command "$@"

    log 'Yo: %q; Plop: %q' "$opt_yo" "$opt_plop"
    log 'Foo: %q; Bar: %q' "$arg_foo" "$arg_bar"

    run_if_not_dry log 'TODO'
    return 0
}

main "$@"
