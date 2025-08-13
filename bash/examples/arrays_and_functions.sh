#! /usr/bin/env bash

# ================================================================
# Examples about manipulation and declaration of function-external arrays
# (both indexed and associative) from within functions.
# This can be used to emulate the ability to “return” arrays from functions,
# and therefore return object-like or tuple-like data instead of only relying
# on the function’s standard output stream and parsing.
# This also allows to avoid dirty and dangerous “eval” calls.
#
# The “edit_…” versions have the advantage of allowing the array
# to remain non-global, when called from within another function.
# For example, in the following code, “t” does not exist outside of “f()”:
#
#   f() {
#     local -a t=(a b c d e)
#     edit_external_indexed_array t
#   }
# ================================================================

# Put “EDITED” in index 2 of an array.
#
# $1  Name of externally declared indexed array.
edit_external_indexed_array() {
  : "${1:?No array name given.}"

  # Avoid circular reference if by chance the name given
  # as parameter is the one we wanted to use locally.
  if [[ $1 != __ref ]]
  then
    # Declare a local “__ref” variable that serves as a “handle”
    # toward the variable (declared outside of this function)
    # whose name corresponds to the content of $1.
    local -n __ref=$1
  fi

  # Modify the external array through the “handle”.
  __ref[2]='EDITED'
}

# Add or set an “EDITED” value for a “KEY” key in an associative array.
#
# $1  Name of externally declared associative array.
edit_external_associative_array() {
  : "${1:?No array name given.}"

  # Avoid circular reference if by chance the name given
  # as parameter is the one we wanted to use locally.
  if [[ $1 != __ref ]]
  then
    # Declare a local “__ref” variable that serves as a “handle”
    # toward the variable (declared outside of this function)
    # whose name corresponds to the content of $1.
    local -n __ref=$1
  fi

  # Modify the external array through the “handle”.
  __ref[KEY]='EDITED'
}

# Declare a global indexed array containing a given number of random numbers.
# Overwrite it if it already exists.
#
# $1              Name of global indexed array to declare.
# $2  (Optional)  Wanted number of items in the array.
#                 Default: 3
declare_global_indexed_array() {
  : "${1:?No array name given.}"

  # Erase potentially existing array.
  unset -v "$1"
  # Often overkill, but explicit at least (both for scope and type).
  declare -ga "$1"

  # Avoid circular reference if by chance the name given
  # as parameter is the one we wanted to use locally.
  if [[ $1 != __ref ]]
  then
    # Declare a local “__ref” variable that serves as a “handle”
    # toward the variable (declared outside of this function)
    # whose name corresponds to the content of $1.
    local -n __ref=$1
  fi

  local -i k
  for ((k = 0; k < ${2:-3}; k++))
  do
    __ref+=("$RANDOM")
  done
}

# Declare a global associative array containing:
#   • The date in a “date” entry.
#   • The kernel release (output of “uname -r”) in a “kernel” entry.
# Overwrite the array if it already exists.
#
# $1              Name of global associative array to declare.
declare_global_associative_array() {
  : "${1:?No array name given.}"

  # Erase potentially existing array.
  unset -v "$1"
  # Create the empty, global, associative array.
  declare -gA "$1"

  # Avoid circular reference if by chance the name given
  # as parameter is the one we wanted to use locally.
  if [[ $1 != __ref ]]
  then
    # Declare a local “__ref” variable that serves as a “handle”
    # toward the variable (declared outside of this function)
    # whose name corresponds to the content of $1.
    local -n __ref=$1
  fi

  # Or “__ref[…]=$(…)” twice.
  __ref+=(
    [date]=$(date)
    [kernel]=$(uname -r)
  )
}

# ================================================================

# Edit an external array from within a function:

## Indexed:

t=(a b c d e)
edit_external_indexed_array t
# Print the new state.
declare -p t
# Output: declare -a t=([0]="a" [1]="b" [2]="EDITED" [3]="d" [4]="e")


## Associative:

declare -A t_a=(
  [foo]=yo
  [bar]=yeah
)
edit_external_associative_array t_a
# Print the new state.
declare -p t_a
# Output: declare -A t_a=([foo]="yo" [bar]="yeah" [KEY]="EDITED" )


# Create a global array from within a function:

## Indexed:

declare_global_indexed_array t 4
# Print the state of the newly defined array.
declare -p t
# Output: declare -a t=([0]="31259" [1]="25846" [2]="21750" [3]="7335")


## Associative:

declare_global_associative_array t_a
# Print the state of the newly defined array.
declare -p t_a
# Output: declare -A t_a=([kernel]="6.14.0-27-generic" [date]="Wed Aug 13 12:28:55 PM CEST 2025" )
