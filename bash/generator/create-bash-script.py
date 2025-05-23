#! /usr/bin/env python3

from textwrap import dedent
import argparse
import re
import logging
import enum
import dataclasses

# ================================================================

class Writer:
    """
    Preferences regarding indentation and so on,
    as well as utilities to generate a file.
    """

    def __init__(self, indent_size):
        """
        Create a set of configuration rules for a file writer, and initialize the writer.

        args:
            indent_size (int): Number of spaces to use.
        """
        self.output_lines = []
        self.current_indent_steps = 0
        self.indent_size = indent_size

@dataclasses.dataclass
class FileConfig:
    """Details of what to include or not within the generated file, and how.

    args:
        use_env (bool):         Shebang with env or direct Bash path.
        greadlink (bool):       Whether to include Mac compatibility trick for BASEDIR.
        logging_utils (bool):   Include a set of logging functions.
    """
    use_env: bool = True
    greadlink: bool = False
    logging_utils: bool = True
    set_e: bool = False
    set_x: bool = False
    err_trap: int = 0
    exit_trap: int = 0
    main: bool = False
    options: bool = True
    positionals: bool = True
    usage: int = 1

@enum.verify(enum.UNIQUE)
class LevelOfDetails(enum.Enum):
    BATCH = "batch"
    DEFAULT = "default"
    ADVANCED = "advanced"
    FULL = "full"

# ================================================================

def init_logging():
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="create-bash-script.py",
        description="Provide a starting point for Bash script",
    )

    parser.add_argument(
        "--indent-size",
        type=int,
        default=4,
        help="Number of spaces used to indent the generated script template.",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Print script template to a file instead of standard output.",
    )
    parser.add_argument(
        "-l", "--level",
        choices=[v.value for v in LevelOfDetails],
        default="default",
        help="""\
        Level of details of the questions that the program will ask. \
        Use "batch" for non-interactive generation.""",
    )

    args = parser.parse_args()
    # Convert string to proper enum value.
    args.level = LevelOfDetails(args.level)
    return args

def ask_choice(question: str, options: list[str]) -> int:
    print()
    print(question)
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    while True:
        try:
            choice = int(input("Enter the number of your choice: "))
            if 1 <= choice <= len(options):
                return choice - 1
        except ValueError:
            pass
        logging.error(f"Invalid input. Please enter a number in 1–{len(options)}.")

def ask_yes_or_no(question: str, default: bool = None) -> bool:
    print()
    match default:
        case None:
            instructions = "[y/n]"
        case True:
            instructions = "[Y/n]"
        case False:
            instructions = "[y/N]"

    print(question, instructions)
    while True:
        choice = input("Choice: ").lower()
        if "y" in choice:
            return True
        elif "n" in choice:
            return False
        elif default is not None:
            return default
        else:
            logging.error("Invalid input. Please specify either “y” or “n”.")

def indent(levels: int = 1):
    writer.current_indent_steps += levels

def unindent(levels: int = 1):
    writer.current_indent_steps -= levels

def is_blank(s: str):
    return not s.strip()

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

def add_lines(text: str, keep_indentation: bool = False):
    """
    Register multiple lines at once.
    Indentation in the input is expected to be done via four spaces
    and will be converted.
    """
    if not keep_indentation:
        text = dedent(text)
    for line in text.splitlines():
        # Replace leading groups of 4 spaces with tabs.
        converted = re.sub(r'^( {4})+', lambda m: '\t' * (len(m.group(0)) // 4), line)
        add_line(converted)

def print_output_lines():
    # Merge lines.
    result = "\n".join(writer.output_lines)
    # Use the right indentation kind of width.
    result = result.replace("\t", " " * writer.indent_size)
    if args.output:
        logging.info(f"Printing script template to “{args.output}”...")
        with open(args.output, "w") as f:
            f.write(result + "\n")
        logging.info("Done.")
    else:
        print("==== [ ↓ SCRIPT TEMPLATE START ↓ ] ====")
        print(result)
        print("==== [ ↑  SCRIPT TEMPLATE END  ↑ ] ====")


# ↓ FUNCTIONS DEFINING FILE PARTS ↓

def part_shebang():
    if conf.use_env:
        add_line("#! /usr/bin/env bash")
    else:
        add_line("#! /bin/bash")
    add_line()

def part_flags():
    flags = []
    if conf.set_e:
        flags.append("e")
    if conf.err_trap == 2:
        flags.append("E")
    if conf.set_x:
        flags.append("x")

    if flags:
        add_line(f"set -{"".join(flags)}")
        add_line()

def part_basedir():
    if conf.greadlink:
        add_lines("""\
        if type greadlink &> /dev/null
        then
            BASEDIR=$(dirname "$(greadlink -f -- "$0")")
        else
            BASEDIR=$(dirname "$(readlink -f -- "$0")")
        fi""")
    else:
        add_line('BASEDIR=$(dirname "$(readlink -f -- "$0")")')
    add_line("# Adapt or remove the ROOTDIR definition depending")
    add_line("# on the depth of this script within the project.")
    add_line('ROOTDIR=$(dirname "$BASEDIR")')
    add_line("readonly BASEDIR ROOTDIR")
    add_line()

def part_constants():
    if conf.positionals:
        add_line("readonly DEFAULT_BAR=/the/default/bar")
        add_line()

def part_logging_utils():
    if not conf.logging_utils:
        return

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
    }

    """)

def part_traps_definition():
    if conf.err_trap != 0:
        add_lines("""\
        # Executed when a command fails, with the same exceptions as for “set -e”.
        # See “trap” documentation in “man bash” for details.
        err_trap() {""")
        indent()
        if conf.logging_utils:
            add_line("err 'An error occurred.'")
        else:
            add_line("printf '%s: An error occurred.\\n' \"$(basename \"$0\")\" >&2")
        unindent()
        add_line("}")
        add_line()

    if conf.exit_trap != 0:
        add_lines("""\
        # Executed upon exit, regardless of the cause.
        exit_trap() {""")
        indent()
        match conf.exit_trap:
            case 1:
                if conf.logging_utils:
                    add_line("log 'Exiting.'")
                else:
                    add_line("printf '%s: Exiting.\\n' \"$(basename \"$0\")\"")

            case 2:
                add_line('rm -rf -- "$_temp_dir"')

            case 3:
                add_line('rm -rf -- "${_to_be_deleted[@]}"')

            case _:
                raise ValueError(f"Unknown exit_trap choice: {conf.exit_trap}")
        unindent()
        add_line("}")
        add_line()

def part_traps_activation():
    if conf.exit_trap != 0:
        add_line("trap err_trap ERR")
        add_line()

    match conf.exit_trap:
        case 0:
            pass

        case 1:
            add_line("trap exit_trap EXIT")
            add_line()

        case 2:
            add_line("unset -v _temp_dir")
            add_line("trap exit_trap EXIT")
            if conf.set_e:
                add_line("_temp_dir=$(mktemp --directory)")
            else:
                add_line("_temp_dir=$(mktemp --directory) || exit")
            add_line()

        case 3:
            add_line("unset -v _to_be_deleted")
            add_line("_to_be_deleted=()")
            add_line("trap exit_trap EXIT")
            if conf.set_e:
                add_line("_some_dir=$(mktemp --directory)")
            else:
                add_line("_some_dir=$(mktemp --directory) || exit")
            add_line('_to_be_deleted+=("$_some_dir")')
            add_line()

        case _:
            raise ValueError(f"Unknown exit_trap choice: {conf.exit_trap}")

def part_usage_function():
    if conf.usage == 0:
        return

    add_lines('''\
    print_help() {
        local prog
        prog=$(printf '%q' "$0")
        cat << _HELP_

      Perform blah blah on a blah blah.

      Usage:''')

    if conf.options:
        if conf.positionals:
            # Support for both options and positional parameters.
            add_line('    ${prog} [OPTIONS]... FOO [BAR]')
        else:
            # Options only.
            add_line('    ${prog} [OPTIONS]...')
    elif conf.positionals:
        # Positional parameters only.
        add_line('    ${prog} FOO [BAR]')
    else:
        # Nothing to parse, so no function to call.
        add_line('    <No arguments>')
    add_line()

    if conf.positionals:
        add_lines('''\
  Arguments:
    FOO     The foo to process.
    BAR     (Optional) A bar in which to write the plop.
            This allows to blah blah.
            Default: “${DEFAULT_BAR}”

''', keep_indentation=True)

    if conf.usage != 0 or conf.options:
        add_line('  Options:')

    if conf.options:
        add_lines('''\
    -y, --yo            Turn on yo mode.
    -p, --plop PLOP     Use PLOP as the plop.''',
            keep_indentation=True)

    if conf.usage == 1:
        add_line('    -h, --help          Print this message and exit.')

    if conf.usage == 1 or conf.options:
        add_line()

    add_lines('''\
    _HELP_
    }

    ''')

def subpart_parse_command_function_options_and_positionals():
    add_lines('''\
        # Fill up global “opt_*” and “arg_*” variables according to given
        # options and positional parameters, and perform basic checks
        # on the presence of mandatory info.
        #
        # $@    Arguments originally passed to the script itself.
        parse_command() {''')
    indent(1)
    subpart_print_help_if_no_arg()
    add_lines('''\
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
                    print_help >&2''')
    indent(3)
    if conf.logging_utils:
        add_line("err 'Invalid option: %q' \"$param\"")
    else:
        add_line('printf \'%s: Error: Invalid option: %q\\n\' "$(basename "$0")" "$param"')
    unindent(4)
    add_lines('''\
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
    then''', keep_indentation=True)
    indent(2)
    if conf.usage != 0:
        add_line("print_help")
    if conf.logging_utils:
        add_line("err 'Missing mandatory parameter: foo'")
    else:
        add_line("printf '%s: Error: Missing mandatory parameter: foo\\n' \"$(basename \"$0\")\"")
    add_line("exit 1")
    unindent()
    add_line("fi >&2")
    unindent()
    add_line("}")
    add_line()

def subpart_parse_command_function_options_only():
    add_lines('''\
        # Fill up global “opt_*” variables according to given options
        # and perform basic checks on the presence of mandatory info.
        #
        # $@    Arguments originally passed to the script itself.
        parse_command() {''')
    indent(1)
    subpart_print_help_if_no_arg()
    add_lines('''\
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

                -h|--help)
                    print_help
                    exit 0
                    ;;

                *)
                    print_help >&2''')
    indent(2)
    if conf.logging_utils:
        add_line("err 'Invalid option or extra parameter: %q' \"$param\"")
    else:
        add_line('printf \'%s: Error: Invalid option or extra parameter: %q\\n\' "$(basename "$0")" "$param"')
    unindent(3)
    add_lines('''\
                    exit 1
                    ;;
            esac
        done
    }''')

def subpart_parse_command_function_positionals_only():
    add_lines('''\
        # Fill up global “arg_*” variables according to given arguments
        # and perform basic checks on the presence of mandatory info.
        #
        # $@    Arguments originally passed to the script itself.
        parse_command() {''')
    indent(1)
    subpart_handle_help_request_without_fancy_option_parsing(True)
    add_lines('''\
        arg_foo=$1
        arg_bar=${2:-${DEFAULT_BAR}}

        if [[ -z $arg_foo ]]
        then''')
    indent(1)
    if conf.usage != 0:
        add_line("print_help")
    if conf.logging_utils:
        add_line("err 'Missing mandatory parameter: foo'")
    else:
        add_line("printf '%s: Error: Missing mandatory parameter: foo\\n' \"$(basename \"$0\")\"")
    add_line("exit 1")
    unindent()
    add_line("fi >&2")
    unindent()
    add_line("}")
    add_line()

def part_parse_command_function():
    if conf.options:
        if conf.positionals:
            # Support for both options and positional parameters.
            subpart_parse_command_function_options_and_positionals()
        else:
            # Options only.
            subpart_parse_command_function_options_only()
    elif conf.positionals:
        # Positional parameters only.
        subpart_parse_command_function_positionals_only
    else:
        # Nothing to parse, so no function to define.
        pass

def subpart_log_option_values():
    if conf.logging_utils:
        add_line('log \'Yo: %q; Plop: %q\' "$opt_yo" "$opt_plop"')
    else:
        add_line('printf \'%s: Yo: %q; Plop: %q\\n\' \\')
        indent(2)
        add_line('"$(basename "$0")" "$opt_yo" "$opt_plop"')
        unindent(2)

def subpart_log_parameter_values():
    if conf.logging_utils:
                add_line('log \'Foo: %q; Bar: %q\' "$arg_foo" "$arg_bar"')
    else:
        add_line('printf \'%s: Foo: %q; Bar: %q\\n\' \\')
        indent(2)
        add_line('"$(basename "$0")" "$arg_foo" "$arg_bar"')
        unindent(2)

def subpart_print_help_if_no_arg():
    if conf.usage == 2:
        add_lines('''\
            if (($# == 0))
            then
                print_help
                exit 1
            fi''')
        add_line()

def subpart_handle_help_request_without_fancy_option_parsing(with_local_vars: bool):
    if conf.usage == 1:
        if with_local_vars:
            add_line("local arg")
        add_lines('''\
            for arg
            do
                if [[ ${arg,,} = @(-h|+(-)help) ]]
                then
                    print_help
                    exit 0
                fi
            done''')
        add_line()
    subpart_print_help_if_no_arg()

def part_parse_command_call():
    the_call = 'parse_command "$@"'
    if conf.options:
        if conf.positionals:
            # Support for both options and positional parameters.
            add_line(the_call)
            add_line()
            subpart_log_option_values()
            subpart_log_parameter_values()
            add_line()
        else:
            # Options only.
            add_line(the_call)
            add_line()
            subpart_log_option_values()
            add_line()
    elif conf.positionals:
        # Positional parameters only.
        add_line(the_call)
        subpart_log_parameter_values()
        add_line()
    else:
        # Nothing to parse, so no function to call.
        # We may need to handle help requests, though.
        subpart_handle_help_request_without_fancy_option_parsing(conf.main)

def part_start_main_part():
    if conf.main:
        add_line("main() {")
        indent()
    else:
        add_line("# ================================")
        add_line()

def part_end_main_part():
    if conf.main:
        add_line("return 0")
        unindent()
        add_lines('''\
        }

        main "$@"''')
    else:
        add_line("exit 0")

def part_dummy_business_instructions():
    if conf.logging_utils:
        add_line("log 'TODO'")
    else:
        add_line("echo 'TODO'")

# ↑ FUNCTIONS DEFINING FILE PARTS ↑

# ================================================================

if __name__ == "__main__":
    init_logging()

    args = parse_args()
    writer = Writer(indent_size=args.indent_size)
    conf = FileConfig()

    # Default questions:
    if args.level != LevelOfDetails.BATCH:
        conf.logging_utils = ask_yes_or_no(
            "Add logging utils?",
            default=conf.logging_utils,
        )
        conf.options = ask_yes_or_no(
            "Support options?",
            default=conf.options,
        )
        conf.positionals = ask_yes_or_no(
            "Support positional parameters?",
            default=conf.positionals,
        )
        conf.usage = ask_choice(
            "Generate a “print_help” function?",
            [
                "No",
                "Yes, tied to “-h” and “--help” options",
                "Yes, and call it if no argument is given",
                "Yes, but let me call it the way I want later",
            ],
        )

    # Advanced questions:
    if args.level in [LevelOfDetails.ADVANCED, LevelOfDetails.FULL]:
        conf.set_e = ask_yes_or_no(
            "Add “set -e”? "
            "WARNING: Make sure to read "
            "https://github.com/yseop/codequality/blob/master/bash/README.adoc"
            "#set_e_etc "
            "before activating this.",
            default=conf.set_e,
        )
        conf.set_x = ask_yes_or_no(
            "Add “set -x”? (Log executed commands to stderr.)",
            default=conf.set_x,
        )
        conf.err_trap = ask_choice(
            "Add an error (ERR) trap? NB: Can be hard to master.",
            [
                "No",
                "Yes, root level only",
                "Yes, inherited by functions, subshells, etc. (“set -E”)",
            ],
        )
        conf.exit_trap = ask_choice(
            "Add an exit trap? (Typically for cleanup or logging purposes.)",
            [
                "No",
                "Yes, logging only",
                "Yes, with a temporary directory",
                "Yes, with a dynamic list of files or directories to delete"
            ],
        )

    # Full-mode-only questions:
    if args.level == LevelOfDetails.FULL:
        conf.use_env = ask_yes_or_no("Use env-based shebang?", default=conf.use_env)
        conf.greadlink = ask_yes_or_no("Support MacOS’ “greadlink”?", default=conf.greadlink)
        conf.main = ask_yes_or_no(
            "Use a “main” function? "
            "NB: Its local variables are still visible from within subfunctions, "
            "so main functions are of debatable usefulness.",
            default=conf.main,
        )

    # Register all the lines of the future file.
    part_shebang()
    part_flags()
    part_basedir()
    part_constants()
    part_logging_utils()
    part_traps_definition()
    part_usage_function()
    part_parse_command_function()

    part_start_main_part()
    part_traps_activation()
    part_parse_command_call()
    part_dummy_business_instructions()
    part_end_main_part()

    # Generate the file.
    print_output_lines()
