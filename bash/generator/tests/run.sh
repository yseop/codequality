#! /usr/bin/env bash

BASEDIR=$(dirname "$(readlink -f -- "$0")")
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
    rm -rf -- "$_temp_dir"
}

print_help() {
    local prog
    prog=$(printf '%q' "$0")
    cat << _HELP_

  Test the script generator against sample outputs.

  Usage:
    ${prog} [OPTIONS]... [SPECIFIC_TESTS]...

  Arguments:
    SPECIFIC_TESTS  (Optional) Run those instead of all tests.

  Options:
    --uv                Wrap Python calls with “uv run” to auto-select
                        the Python version.
    -h, --help          Print this message and exit.

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
            --uv)
                opt_uv=1
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
    arg_specific_tests=("$@")
}

# ================================

parse_command "$@"

unset -v starting_points
starting_points=(
    "${arg_specific_tests[@]:-${BASEDIR}/configs/}"
)

readarray -t -d '' to_be_run < <(
    find "${starting_points[@]}" -type f -name '*.json' -print0
)

if ((${#to_be_run[@]} == 0))
then
    err 'Found no tests under %s.' "${starting_points[*]@Q}"
    exit 1
fi

log 'Found %d tests under %s.' "${#to_be_run[@]}" "${starting_points[*]@Q}"

unset -v _temp_dir
trap exit_trap EXIT
_temp_dir=$(mktemp --directory) || exit

unset -v maybe_uv
if [[ $opt_uv ]]
then
    log 'Using “uv run”.'
    maybe_uv=(uv run)
else
    log 'Using Python %s.' "$(python3 --version | sed 's/^\s*python\s*//i')"
    maybe_uv=()
fi
echo

unset -v failed
failed=()

for config in "${to_be_run[@]}"
do
    # Same name but .sh instead of .json, and in “expectations/” instead of “configs/”.
    expectation=$(
        dirname "$(dirname "$config")"
    )/expectations/$(
        basename "$config" '.json'
    ).sh

    output=${_temp_dir:?}/output.sh
    rm -f -- "$output"

    if
        logs=$(
            {
                log_and_run "${maybe_uv[@]}" "$BASEDIR"/../create-bash-script.py \
                        --load-config "$config" \
                        --output "$output" &&
                diff "$expectation" "$output"
            } 2>&1
        )
    then
        log '[OK]     %q' "${config#"${BASEDIR}/"}"
    else
        err '[Failed] %q' "${config#"${BASEDIR}/"}"
        printf '%s\n' "$logs"
        failed+=("$config")
    fi
    echo
done

# Final, ad-hoc test, for the “utils in separate file” case.
config=${BASEDIR}/split
if
    logs=$(
        {
            log_and_run "${maybe_uv[@]}" "$BASEDIR"/../create-bash-script.py \
                    --load-config '{ "utils": 1 }' \
                    --output "${_temp_dir:?}/main.sh" &&
            diff "${BASEDIR}/split/main.sh" "${_temp_dir:?}/main.sh" &&
            diff "${BASEDIR}/split/common.sh" "${_temp_dir:?}/common.sh"
        } 2>&1
    )
then
    log '[OK]     %q' "${config#"${BASEDIR}/"}"
else
    err '[Failed] %q' "${config#"${BASEDIR}/"}"
    printf '%s\n' "$logs"
    failed+=("$config")
fi
echo

if ((${#failed[@]} > 0))
then
    err 'There were test failures:'
    printf '  • %q\n' "${failed[@]}"
    exit 1
else
    log 'All clear.'
    exit 0
fi
