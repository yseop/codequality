#! /usr/bin/env python3

# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
# // ↑ For “uv run” wrapping ↑

"""
Template generator to provide a starting point for Bash scripts.
See “-h” / “--help” for details.
"""

from textwrap import dedent
import os
from stat import S_IXUSR as OWNER_HAS_EXEC_PERM
import argparse
import re
import logging
import enum
import dataclasses
import json

# ================================================================

STDOUT_PLACEHOLDER = "-"
"""Treated as stdout if given as output file path."""

COMMON_BASENAME_WITHOUT_EXTENSION = "common"
COMMON_BASENAME_EXTENSION = ".sh"
COMMON_BASENAME = COMMON_BASENAME_WITHOUT_EXTENSION + COMMON_BASENAME_EXTENSION
"""Basename of a file that may be created to store common utility functions."""

class Writer:
    """
    Preferences regarding indentation and so on,
    with the current state in that regard.
    """

    def __init__(self, indent_size: int, file: str | None):
        """
        Create a set of configuration rules for a file writer, and initialize the writer.

        Args:
            indent_size (int):  Number of spaces to use.
            file (str | None):  Output file, or stdout if None.
        """
        self.output_lines: list[str] = []
        self.current_indent_steps = 0
        self.indent_size = indent_size
        self.file: str | None = file

    def print_output_lines(self):
        """Print the content of the Writer, either to the
        standard output or to a file depending on `self.file`.
        """
        # Merge lines.
        result = "\n".join(self.output_lines)

        # Checking that devnull exists: maybe some OSes don’t have an equivalent?
        if os.devnull and self.file == os.devnull:
            # Avoid errors due to, for example, trying to make “/dev/null” executable.
            return

        what = (
            "script template"
            if self is main_writer
            else "utils"
        )

        if self.file:
            # Output is a file.
            logging.info(f"Printing {what} to “{self.file}”...")
            with open(self.file, "w") as f:
                f.write(result + "\n")

            # No need to make a separate library executable.
            if self is not utils_writer:
                # Ensure the user can execute the script.
                try:
                    current_perms = os.stat(self.file).st_mode
                    os.chmod(self.file, current_perms | OWNER_HAS_EXEC_PERM)
                except Exception as e:
                    logging.warning(f"Failed to ensure “{self.file}” is executable: {e}")

            logging.info("Done.")
        else:
            # Output is standard output.
            print()
            print(f"==== [ ↓ {what.upper()} START ↓ ] ====")
            print(result)
            print(f"==== [ ↑  {what.upper()} END  ↑ ] ====")


@dataclasses.dataclass
class FileConfig:
    """Details of what to include or not within the generated file, and how.

    Args:
        use_env (bool):         Shebang with env or direct Bash path.
        greadlink (bool):       Whether to include Mac compatibility trick for BASEDIR.
        logging_utils (bool):   Include a set of logging functions.
        set_e (bool):           Use “set -e”.
        set_x (bool):           Use “set -x”.
        err_trap (int):         Set up an error trap.
        exit_trap (int):        Set up an exit trap.
        main (bool):            Use a “main” function.
        options (bool):         Support options.
        positionals (bool):     Support positional arguments.
        usage (int):            Generate a “print_help” function.
        dry (bool):             Implement a “dry run” mode.
        utils (int):            Where to store utility functions.
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
    dry: bool = False
    utils: int = 0


@enum.verify(enum.UNIQUE)
class LevelOfDetails(enum.Enum):
    """How much the user wants to be bothered (or not) with questions."""

    BATCH = "batch"
    """No questions asked; suitable for non-interactive
    or scripted execution.
    """

    DEFAULT = "default"
    """Only essential questions are asked, using sensible defaults
    for others.
    """

    ADVANCED = "advanced"
    """More questions are asked, allowing for finer control
    over common advanced settings.
    """

    FULL = "full"
    """All possible questions are asked, providing maximum control
    over every detail.
    """


LEVEL_OF_DETAILS_ALIASES = {
    "b": LevelOfDetails.BATCH,
    "d": LevelOfDetails.DEFAULT,
    "a": LevelOfDetails.ADVANCED,
    "f": LevelOfDetails.FULL,
}
"""Shorter ways for the caller to specify a value from `LevelOfDetails`."""

# ================================================================

def init_logging():
    logging.basicConfig()
    logging.root.setLevel(logging.INFO)


def parse_args() -> argparse.Namespace:
    """Configure and run a standard parser on the script’s arguments."""
    parser = argparse.ArgumentParser(
        description="Provide a starting point for Bash scripts.",
    )

    parser.add_argument(
        "-i", "--indent-size",
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
        choices=[v.value for v in LevelOfDetails] + list(LEVEL_OF_DETAILS_ALIASES.keys()),
        default="default",
        help=f"""\
        Level of details of the questions that the program will ask. \
        Use "batch" for non-interactive generation.
        Aliases: You can use the first letter of the level name only:
        {", ".join([f"{i[0]} → {i[1].value}" for i in LEVEL_OF_DETAILS_ALIASES.items()])}""",
    )

    # To avoid confusion, the user must choose explicitly
    # between loading a configuration as a base or
    # loading it brutally with no question asked.
    ways_to_load = parser.add_mutually_exclusive_group()
    ref_to_dump = "“-d” / “--dump-config”"
    json_explanations = (
        "JSON can also directly be given here as a string "
        "instead of providing a configuration file path."
    )
    ways_to_load.add_argument(
        "-c", "--load-config",
        type=str,
        help=f"""\
        Load a configuration JSON file previously generated
        via {ref_to_dump}, and skip all questions.
        {json_explanations}
        """,
    )
    ways_to_load.add_argument(
        "-b", "--base-config",
        type=str,
        help=f"""\
        Load a configuration JSON file previously generated
        via {ref_to_dump}, use it as a base to set default
        values, and still ask questions as usual afterward.
        {json_explanations}
        """,
    )
    parser.add_argument(
        "-d", "--dump-config",
        type=str,
        help=f"""\
        Print or save, as JSON data, the configuration resulting
        from the given answers, for later use or debugging purposes.
        Give “{STDOUT_PLACEHOLDER}” as path to print the data to the standard output.
        """,
    )

    args = parser.parse_args()
    if args.load_config is None:
        # Convert string to proper enum value.
        args.level = (
            # Resolve alias if one was used.
            LEVEL_OF_DETAILS_ALIASES[args.level]
            if args.level in LEVEL_OF_DETAILS_ALIASES
            else LevelOfDetails(args.level)
        )
    else:
        # Force batch level if forced config.
        args.level = LevelOfDetails.BATCH
        # Register the config as base config.
        args.base_config = args.load_config
    return args


def load_config(path_or_json: str):
    """Load a script-generating configuration.

    Args:
        path_or_json (str): Path to JSON file to build a `FileConfig`,
                            or raw JSON to load as-is.
    """

    # Get JSON either directly from the argument or from a file.
    if path_or_json.strip().startswith("{"):
        logging.info("Parsing the given configuration string... "
                     f"({len(path_or_json)} characters)")
        data = json.loads(path_or_json)
    else:
        logging.info(f"Loading generator configuration from “{path_or_json}”...")
        with open(path_or_json, "r") as f:
            data = json.load(f)

    # Now that we got the JSON data, let’s use it.
    try:
        result = FileConfig(**data)
    except TypeError as e:
        logging.error("Failed to convert the JSON data into a generator configuration. "
                      "Invalid keys?")
        field_names = [field.name for field in dataclasses.fields(FileConfig)]
        e.add_note("Valid keys are: " + ", ".join(field_names))
        raise
    logging.info("Done.")
    return result


def compute_utils_path():
    """Determine a suitable path to save utility functions, or None if those are embed."""

    if main_writer.file is None:
        # The main script is on stdout, so there’s no use fiddling with files
        # for the utility functions anyway. The only thing that may happen
        # is printing utils as a separate blurb after the main script.
        return None

    if conf.utils == 0:
        raise RuntimeError("We are not supposed to compute an output path for utils "
                           "if the utility functions are in the main script.")

    if os.devnull and main_writer.file == os.devnull:
        # If the main script is doomed, then so are the utility functions.
        return os.devnull

    # Whether we’ve been asked to brutally use the default utils file name
    # even if it means overwriting an existing file.
    overwrite = conf.utils == 1

    d = os.path.dirname(main_writer.file)
    path_using_default_name = os.path.join(d, COMMON_BASENAME)
    if overwrite or not os.path.exists(path_using_default_name):
        # Default name for the utils file.
        return path_using_default_name
    else:
        # Look for an alternate name for the file.
        template = f"{COMMON_BASENAME_WITHOUT_EXTENSION}-{{n}}{COMMON_BASENAME_EXTENSION}"
        n = 2
        while True:
            res = os.path.join(d, template.format(n=n))
            if os.path.exists(res):
                n = n + 1
            else:
                return res


def ask_choice(question: str, options: list[str], default: int = None) -> int:
    """\
    Ask a question to the user about how the script must be generated.
    This function is tailored for questions offering more possibilities
    than simply “Yes” or “No”.

    Args:
        question (str):             The question to display to the user.
        options (list[str]):        A list of strings representing the
                                    available choices.
        default (int, optional):    The index of the default option in
                                    the `options` list.
                                    Defaults to None, meaning no default
                                    choice (the user is forced to answer).

    Returns:
        int: The index of the selected option in the `options` list.
    """
    print()
    print(question)

    # Display the choices.
    for i, option in enumerate(options, 1):
        if default is None:
            print(f"  {i}. {option}")
        elif default == i - 1:
            print(f"  [Default] {i}. {option}")
        else:
            print(f"            {i}. {option}")

    prompt = (
        "Enter the number of your choice: "
        if default is None
        else "Enter the number of your choice (empty for default): "
    )

    # Let the user select one of the options.
    while True:
        try:
            answer = input(prompt)

            # An empty answer leads to the default choice, if any.
            if not answer and default is not None:
                return default

            # Otherwise, try to parse as an integer.
            choice = int(answer)
            if 1 <= choice <= len(options):
                return choice - 1
        except ValueError:
            pass
        logging.error(f"Invalid input. Please enter a number in 1–{len(options)}.")


def ask_yes_or_no(question: str, default: bool = None) -> bool:
    """\
    Ask a question to the user about how the script must be generated.
    This function is tailored for closed questions (“Yes” or “No”).

    Args:
        question (str):             The question to display to the user.
        default (bool, optional):   Default if empty input.
                                    Defaults to None, meaning no default
                                    choice (the user is forced to answer).

    Returns:
        bool: The user’s choice.
    """
    print()
    match default:
        case None:
            instructions = "[y/n]"
        case True:
            instructions = "[Y/n]"
        case False:
            instructions = "[y/N]"

    print(question, instructions)

    prompt = (
        "Choice: "
        if default is None
        else f"Choice (empty for default: {default}): "
    )

    while True:
        choice = input(prompt).lower()
        y = "y" in choice
        n = "n" in choice
        match y, n:
            case True, False:
                return True
            case False, True:
                return False
            case True, True:
                logging.error("Ambiguous input. Please specify either “y” or “n”.")
            case False, False:
                # Got neither “y” nor “n”.
                if default is not None:
                    return default
                else:
                    logging.error("Invalid input. Please specify either “y” or “n”.")


def indent(levels: int = 1, writer: Writer = None):
    """Increase the current indent level of the global `writer`."""
    if writer is None:
        writer = main_writer
    writer.current_indent_steps += levels


def unindent(levels: int = 1, writer: Writer = None):
    """Decrease the current indent level of the global `writer`."""
    if writer is None:
        writer = main_writer
    writer.current_indent_steps -= levels


def is_blank(s: str):
    return s is None or not s.strip()


def add_line(new_line: str = None, writer: Writer = None):
    """
    Register an automatically indented line.
    The argument is not expected to contain a newline character.
    To register a blank, unindented line, pass no argument at all.

    Args:
        new_line (str):     The text to add, without final newline included.
                            Any blank value (including None) falls back to "",
                            meaning that an empty line will be left in the
                            generated script at this point.
        writer (Writer):    The Writer in which the line should be registered.
                            The global `main_writer` by default.
                            Generally only specified when registering lines
                            for a separate utility functions library file.
    """
    if writer is None:
        writer = main_writer

    if is_blank(new_line):
        # Avoid getting just a bunch of indentation spaces or whatever on the line.
        new_line = ""
    else:
        # Automatic indentation.
        new_line = writer.current_indent_steps * writer.indent_size * " " + new_line

    # Register the resulting line.
    writer.output_lines.append(new_line)


def add_lines(text: str, keep_indentation: bool = False, writer: Writer = None):
    """
    Register multiple lines at once.
    Indentation in the input is expected to be done via four spaces
    and will be converted.

    Args:
        text (str):                 The text to add as consecutive lines.
        keep_indentation (bool):    If True, preserve whatever indentation
                                    is already present in the provided text.
                                    This is especially useful after having
                                    registered a large piece of text that opened
                                    multiple blocks and we want to add a tiny
                                    conditional piece after it.
        writer (Writer):            The Writer in which the lines should be registered.
                                    The global `main_writer` by default.
                                    Generally only specified when registering lines
                                    for a separate utility functions library file.
    """
    if writer is None:
        writer = main_writer
    if not keep_indentation:
        text = dedent(text)
    one_indentation_step = " " * writer.indent_size
    for line in text.splitlines():
        # Replace leading groups of 4 spaces with the suitable number of spaces.
        def to_be_applied(m):
            return one_indentation_step * (len(m.group(0)) // 4)

        converted = re.sub(r'^( {4})+', to_be_applied, line)
        add_line(converted, writer=writer)


def print_bash():
    """Generate the final Bash output file (or “files” if separate utils)."""
    # Generate the file.
    main_writer.print_output_lines()
    # Only generate an utils file if:
    # 1) we’ve been asked to do so, and
    # 2) there are things of interest to print there.
    if conf.utils != 0 and utils_writer.output_lines:
        # Add the shebang at the last moment, otherwise it would
        # make us believe that there always are “things of interest” to print.
        utils_writer.output_lines = (
            [get_shebang(), ""] + utils_writer.output_lines
        )
        # Remove potential trailing empty lines.
        while utils_writer.output_lines[-1] == "":
            utils_writer.output_lines.pop()
        # Print or save the utility functions.
        utils_writer.print_output_lines()


def print_config():
    output = args.dump_config

    if is_blank(output):
        return

    # Translate the configuration into something
    # that the JSON processor will be able to
    # serialize without complaining.
    conf_as_dict = dataclasses.asdict(conf)
    # How to print the JSON data.
    json_config = {
        "indent": args.indent_size,
    }

    if output == STDOUT_PLACEHOLDER:
        print()
        print("==== [ ↓ CONFIG START ↓ ] ====")
        print(json.dumps(conf_as_dict, **json_config))
        print("==== [ ↑  CONFIG END  ↑ ] ====")
    else:
        logging.info(f"Printing generator configuration to “{args.dump_config}”...")
        with open(args.dump_config, "w") as f:
            json.dump(conf_as_dict, f, **json_config)
            f.write("\n")
        logging.info("Done.")


def ask_questions_default_level():
    """Questions that are always asked, unless
    pure batch mode was selected.
    """

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
        default=conf.usage,
    )
    if args.output:
        conf.utils = ask_choice(
            "Where should utility functions be stored?",
            [
                "Within the script itself",
                f"Within a “{COMMON_BASENAME}” file alongside the script "
                        "(overwrite if it exists)",
                f"Within a “{COMMON_BASENAME}” file alongside the script "
                        "(add suffix if it exists)",
            ],
            default=conf.utils,
        )
    else:
        # Simplify the question somewhat because we’re not creating files anyway.
        embed = ask_yes_or_no(
            "Should utility functions be stored in the script itself? (vs. separately)",
            default=conf.utils == 0,
        )
        # Convert the yes/no answer into a valid multi-choice answer,
        # as if we had not simplified the question.
        conf.utils = 0 if embed else 1


def ask_questions_advanced_level():
    """Questions that are only asked if advanced or full mode
    were selected.
    """

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
        default=conf.err_trap,
    )
    conf.exit_trap = ask_choice(
        "Add an exit trap? (Typically for cleanup or logging purposes.)",
        [
            "No",
            "Yes, logging only",
            "Yes, with a temporary directory",
            "Yes, with a dynamic list of files or directories to delete",
        ],
        default=conf.exit_trap,
    )
    conf.dry = ask_yes_or_no(
        "Implement a “dry run” mode?",
        default=conf.dry,
    )


def ask_questions_full_level():
    """The most technical questions or niche features,
    only asked if the user really wanted them to be.
    """

    conf.use_env = ask_yes_or_no("Use env-based shebang?", default=conf.use_env)
    conf.greadlink = ask_yes_or_no("Support MacOS’ “greadlink”?", default=conf.greadlink)
    conf.main = ask_yes_or_no(
        "Use a “main” function? "
        "NB: Its local variables are still visible from within subfunctions, "
        "so main functions are of debatable usefulness.",
        default=conf.main,
    )


def ask_questions():
    """Parent routine to handle detail levels
    and ask the relevant questions.
    """

    if args.level != LevelOfDetails.BATCH:
        ask_questions_default_level()

    if args.level in [LevelOfDetails.ADVANCED, LevelOfDetails.FULL]:
        ask_questions_advanced_level()

    if args.level == LevelOfDetails.FULL:
        ask_questions_full_level()


# ↓ FUNCTIONS DEFINING FILE PARTS ↓

def get_shebang():
    return (
        "#! /usr/bin/env bash"
        if conf.use_env
        else "#! /bin/bash"
    )


def part_shebang():
    add_line(get_shebang())
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

    writer_config = {} if conf.utils == 0 else {"writer": utils_writer}

    add_lines("""\
    # For internal use via the logging functions below.
    #
    # $1    String added between the program name and the message,
    #       typically to specify the log level.
    # $2    Printf-style format string.
    # $3…n  Arguments for printf.
    _f_log() {
        local prog""", **writer_config)

    indent(**writer_config)
    if conf.dry:
        add_line('prog=$(basename "$0"):${DRY:+ [DRY RUN]}', **writer_config)
    else:
        add_line('prog=$(basename "$0"):', **writer_config)
    unindent(**writer_config)

    add_lines("""\
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

    # Print a command before running it.
    # (This function takes care of running it).
    #
    # $@    The words making up the command to run.
    log_and_run() {
        log 'Running: %s' "${*@Q}"
        "$@"
    }

    """, **writer_config)


def part_dry_run_utils():
    if not conf.dry:
        return

    if conf.logging_utils:
        logging_command = 'log \'Would have run: %s\' "${*@Q}"'
    else:
        logging_command = 'printf \'[DRY RUN] Would have run: %s\\n\' "${*@Q}"'

    writer_config = {} if conf.utils == 0 else {"writer": utils_writer}

    add_lines(f"""\
        # Returns with 0 status if and only if
        # the dry run mode is currently activated.
        is_dry_run() {{
            [[ $DRY ]]
        }}

        # Only run a command if dry run mode is not activated.
        # In dry run mode, log the command instead to show what
        # would have been run in a normal context.
        #
        # $@    The words making up the command to potentially run.
        run_if_not_dry() {{
            if is_dry_run
            then
                {logging_command}
            else
                "$@"
            fi
        }}

        """, **writer_config)


def part_libraries():
    if conf.utils == 0:
        return

    if utils_writer is None:
        raise RuntimeError("Utility functions writer not defined.")

    lib_basename = os.path.basename(utils_writer.file or COMMON_BASENAME)
    instruction = f'. "${{BASEDIR:?}}/{lib_basename}"'

    if not conf.set_e:
        instruction = instruction + " || exit"
    add_line(instruction)
    add_line()


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
    if conf.err_trap != 0:
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

    try:
        add_lines('''\
            print_help() {
                local prog
                prog=$(printf '%q' "$0")
                cat << _HELP_
            ''')

        # Now entering the Bash “here document” part.
        initial_indent_size = main_writer.indent_size
        # The help blurb has 2-space steps.
        main_writer.indent_size = 2
        add_line()
        indent()
        add_line('Perform blah blah on a blah blah.')
        add_line()
        add_line('Usage:')
        indent()

        if conf.options:
            if conf.positionals:
                # Support for both options and positional parameters.
                add_line('${prog} [OPTIONS]... FOO [BAR]')
            else:
                # Options only.
                add_line('${prog} [OPTIONS]...')
        elif conf.positionals:
            # Positional parameters only.
            add_line('${prog} FOO [BAR]')
        else:
            # Nothing to parse, so no function to call.
            add_line('<No arguments>')
        unindent()
        add_line()

        if conf.positionals:
            add_line('Arguments:')
            indent()
            add_line('FOO     The foo to process.')
            add_line('BAR     (Optional) A bar in which to write the plop.')
            add_line('        This allows to blah blah.')
            add_line('        Default: “${DEFAULT_BAR}”')
            unindent()
            add_line()

        if conf.usage == 1 or conf.options:
            add_line('Options:')
            indent()

        if conf.options:
            add_line('-y, --yo            Turn on yo mode.')
            add_line('-p, --plop PLOP     Use PLOP as the plop.')
            if conf.dry:
                add_line('--dry               Turn dry mode on.')

        if conf.usage == 1:
            add_line('-h, --help          Print this message and exit.')

        if conf.usage == 1 or conf.options:
            unindent()
            add_line()

        add_line('Environment variables:')
        indent()
        add_line('GIT_USER    Username for requests to GitHub.')
        if conf.dry:
            add_line('DRY         If not empty, turn dry mode on.')
            add_line('            “Important” commands will be skipped.')

        unindent(2)

        add_lines('''\

        _HELP_
        }

        ''')
    finally:
        main_writer.indent_size = initial_indent_size


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

        ''')

    if conf.dry:
        add_lines("""\
        --dry)
            DRY=1
            ;;
            """,
            keep_indentation=True)

    if conf.usage == 1:
        add_lines("""\
        -h|--help)
            print_help
            exit 0
            ;;
        """, keep_indentation=True)

    if conf.usage != 0:
        add_lines("""\
        -*)
            print_help >&2""",
            keep_indentation=True)
    else:
        add_lines("""\
        -*)""",
            keep_indentation=True)

    indent(3)
    if conf.logging_utils:
        add_line("err 'Invalid option: %q' \"$param\"")
    else:
        add_line('printf \'%s: Error: Invalid option: %q\\n\' "$(basename "$0")" "$param" >&2')
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

        ''')

    if conf.dry:
        add_lines("""\
        --dry)
            DRY=1
            ;;
            """,
            keep_indentation=True)

    if conf.usage == 1:
        add_lines("""\
        -h|--help)
            print_help
            exit 0
            ;;
        """, keep_indentation=True)

    if conf.usage != 0:
        add_lines("""\
        *)
            print_help >&2""",
            keep_indentation=True)
    else:
        add_lines("""\
        *)""",
            keep_indentation=True)

    indent(3)
    if conf.logging_utils:
        add_line("err 'Invalid option or extra parameter: %q' \"$param\"")
    else:
        add_line('printf \'%s: Error: Invalid option or extra parameter: %q\\n\' "$(basename "$0")" "$param" >&2')
    unindent(4)
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
        add_line("printf '%s: Error: Missing mandatory parameter: foo\\n' \"$(basename \"$0\")\" >&2")
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
        subpart_parse_command_function_positionals_only()
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
        add_line()
        add_line("exit 0")


def part_dummy_business_instructions():
    prefix = "run_if_not_dry " if conf.dry else ""

    if conf.logging_utils:
        add_line(prefix + "log 'TODO'")
    else:
        add_line(prefix + "echo 'TODO'")

# ↑ FUNCTIONS DEFINING FILE PARTS ↑

# ================================================================

if __name__ == "__main__":
    init_logging()

    args = parse_args()
    main_writer = Writer(
        indent_size=args.indent_size,
        file=args.output or None,
    )
    conf = (
        FileConfig()
        if args.base_config is None
        else load_config(args.base_config)
    )

    try:
        ask_questions()
    except KeyboardInterrupt:
        print()
        logging.warning("Cancelled.")
        exit(130)

    if conf.utils == 0:
        # Embedded utility functions.
        utils_writer = None
    else:
        # Utility functions will be in a separate file.
        utils_writer = Writer(
            indent_size=args.indent_size,
            file=compute_utils_path(),
        )

    # Register all the lines of the future file.
    part_shebang()
    part_flags()
    part_basedir()
    part_constants()
    part_logging_utils()
    part_dry_run_utils()
    part_libraries()
    part_traps_definition()
    part_usage_function()
    part_parse_command_function()

    part_start_main_part()
    part_traps_activation()
    part_parse_command_call()
    part_dummy_business_instructions()
    part_end_main_part()

    # Regurgitate content.
    print_bash()
    print_config()
