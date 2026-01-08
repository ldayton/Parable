# Bash Grammar Reference

Reference material for implementing a recursive descent bash parser.

## Grammar Hierarchy

```
inputunit (top-level)
  └── list
        └── and_or
              └── pipeline_command ([!] [time] ...)
                    └── pipeline
                          └── command [| command ...]
                                ├── simple_command
                                ├── shell_command (compound)
                                ├── function_definition
                                └── coproc
```

## 1. Lists and Pipelines

```
list             : and_or ((';' | '&' | '\n') and_or)* [';' | '&' | '\n']
and_or           : pipeline_command (('&&' | '||') newlines pipeline_command)*
pipeline_command : pipeline
                 | '!' pipeline_command
                 | timespec pipeline_command
                 | timespec                    # time with null command
                 | '!'                         # ! with null command (equals 'false')
pipeline         : command ('|' newlines command)*
                 | command ('|&' newlines command)*
timespec         : 'time' ['-p'] ['--']
```

**Note:** `!` and `time` modify `pipeline_command`, not individual commands.
They can be combined: `! time cmd` or `time ! cmd` (though the latter is unusual).

### Operators
- `;`  - Sequential execution
- `&`  - Background execution
- `&&` - AND list (short-circuit)
- `||` - OR list (short-circuit)
- `|`  - Pipe stdout
- `|&` - Pipe stdout and stderr (equivalent to `2>&1 |`)

## 2. Commands

```
command        : simple_command
               | shell_command [redirections]
               | function_definition
               | coproc

simple_command : cmd_element+
cmd_element    : WORD              # command name or argument
               | ASSIGNMENT_WORD   # VAR=value
               | redirection
```

**Note:** In a simple_command, elements can technically appear in any order
syntactically, but semantically:
- Assignments before the command name are exported to that command only
- Assignments after the command name are just arguments
- The first non-assignment WORD is the command name

### Simple Command Examples
```bash
VAR=value                    # assignment only (executed in current shell)
VAR=value cmd arg1 arg2      # assignment + command (VAR exported to cmd)
cmd arg1 arg2 > file         # command + redirection
> file                       # redirection only (valid!)
cmd >out arg <in             # redirections can be interspersed with args
```

## 3. Compound Commands (shell_command)

```
shell_command : brace_group        # { list; }
              | subshell           # ( list )
              | for_command
              | arith_for_command  # for (( ; ; ))
              | select_command
              | case_command
              | if_command
              | while_command
              | until_command
              | arith_command      # (( expr ))
              | cond_command       # [[ expr ]]
```

Note: `coproc` is a separate command type, not a shell_command (see section 3.8).

### 3.1 Brace Group and Subshell
```bash
{ list; }      # execute in current shell (space after { required!)
( list )       # execute in subshell
```

### 3.2 For Loops
```bash
# All valid forms (from parse.y):
for name do list done                              # no 'in', uses "$@"
for name; do list done                             # semicolon after name
for name in word ... ; do list done                # standard form
for name in ; do list done                         # empty word list

# Brace groups can replace do/done:
for name in word ... ; { list; }
for name { list; }

# C-style arithmetic form:
for (( expr1 ; expr2 ; expr3 )) ; do list ; done
for (( expr1 ; expr2 ; expr3 )) { list; }
```

### 3.3 Select
```bash
# Same variations as for loops:
select name do list done
select name; do list done
select name in word ... ; do list done
select name in ; do list done
select name in word ... ; { list; }
```

### 3.4 Case
```bash
case word in
    [(] pattern [ | pattern ] ... ) list ;;    # standard terminator
    [(] pattern [ | pattern ] ... ) list ;&    # fallthrough
    [(] pattern [ | pattern ] ... ) list ;;&   # continue testing
esac
```

The leading `(` before the pattern is optional. Each clause can have an empty
command list (just terminates with `;;` etc. after `)`). The last clause
before `esac` doesn't require a terminator.

### 3.5 If/While/Until
```bash
if list; then list; [ elif list; then list; ] ... [ else list; ] fi
while list; do list; done
until list; do list; done
```

### 3.6 Arithmetic Command
```bash
(( expression ))   # returns 0 if expression is non-zero, 1 otherwise
```

### 3.7 Conditional Command
```bash
[[ expression ]]   # conditional expression with special parsing rules
```

### 3.8 Coproc (Coprocess)
```bash
coproc shell_command [redirections]        # name defaults to COPROC
coproc NAME shell_command [redirections]   # named coprocess
coproc simple_command                      # simple command form
```

Creates a coprocess: the command runs asynchronously in a subshell with a
two-way pipe to the parent shell. File descriptors stored in array:
`${NAME[0]}` (read from coprocess) and `${NAME[1]}` (write to coprocess).
The PID is in `$NAME_PID`.

## 4. Function Definition

```bash
# From parse.y (4 forms):
name () [newlines] function_body              # POSIX form
function name () [newlines] function_body     # function keyword + parens
function name function_body                   # no parens, no newline
function name \n [newlines] function_body     # no parens, with newline(s)

function_body : shell_command [redirections]
```

When using `function` keyword without `()`, the body must either:
- Immediately follow the name (e.g., `function f { echo; }`), OR
- Be separated by newline(s) (e.g., `function f\n{ echo; }`)

Redirections after the body are attached to the function.

## 5. Redirections

```
redirection    : [n] '<'  word           # input from file
               | [n] '>'  word           # output to file (truncate)
               | [n] '>>' word           # output to file (append)
               | [n] '>|' word           # output (clobber, ignore noclobber)
               | [n] '<>' word           # open read/write
               | [n] '<<' word           # heredoc
               | [n] '<<-' word          # heredoc (strip leading tabs)
               | [n] '<<<' word          # herestring
               | [n] '<&' word           # duplicate input fd
               | [n] '>&' word           # duplicate output fd
               | '&>' word               # redirect stdout+stderr to file
               | '&>>' word              # append stdout+stderr to file

# Variable name as fd (bash extension):
               | {varname} '<'  word     # fd stored in $varname
               | {varname} '>'  word
               | {varname} '>>' word
               # ... etc for all redirection operators
```

### File Descriptor Rules
- `n` is an optional file descriptor number
- If `n` omitted before `<`: defaults to stdin (0)
- If `n` omitted before `>`: defaults to stdout (1)
- `word` can be a number for fd duplication: `2>&1`
- `word` can be `-` to close fd: `2>&-`
- `{varname}` allocates a new fd (>=10) and stores the number in varname

## 6. Word Expansions

Words can contain these expansions, which need to be parsed as nested structures:

### 6.1 Parameter Expansion `${...}`

```
${parameter}              # simple expansion
${!parameter}             # indirect expansion

# Default values (with : tests for null, without only tests unset)
${parameter:-word}        # use default if unset/null
${parameter:=word}        # assign default if unset/null
${parameter:?word}        # error if unset/null
${parameter:+word}        # use alternate if set/non-null

# Substring
${parameter:offset}       # substring from offset
${parameter:offset:length}# substring with length

# Length
${#parameter}             # string length

# Pattern removal
${parameter#pattern}      # remove shortest prefix
${parameter##pattern}     # remove longest prefix
${parameter%pattern}      # remove shortest suffix
${parameter%%pattern}     # remove longest suffix

# Substitution
${parameter/pattern/string}   # replace first match
${parameter//pattern/string}  # replace all matches
${parameter/#pattern/string}  # replace prefix
${parameter/%pattern/string}  # replace suffix

# Case modification (Bash 4.0+)
${parameter^pattern}      # uppercase first char matching pattern
${parameter^^pattern}     # uppercase all matching pattern
${parameter,pattern}      # lowercase first char matching pattern
${parameter,,pattern}     # lowercase all matching pattern

# Transformation (Bash 4.4+)
${parameter@operator}     # transform value
# Operators: U (uppercase), u (capitalize), L (lowercase),
#            Q (quoted), E (expand escapes), P (prompt expand),
#            A (assignment form), K (quoted keys), a (attributes)

# Array operations
${!prefix*}, ${!prefix@}  # names starting with prefix
${!name[@]}, ${!name[*]}  # array indices
${parameter[@]}           # all array elements
${parameter[*]}           # all array elements (as single word)
```

### 6.2 Command Substitution
```bash
$(command)    # preferred form
`command`     # legacy form (harder to nest)
```

### 6.3 Arithmetic Expansion
```bash
$((expression))   # evaluate and substitute result
$[expression]     # deprecated form
```

### 6.4 Process Substitution
```bash
<(command)    # substitute with filename of pipe from command output
>(command)    # substitute with filename of pipe to command input
```

### 6.5 Other Expansions (not nested structures)
These are expanded but don't create nested parse structures:
```bash
~            # tilde expansion (home directory)
~user        # home directory of user
{a,b,c}      # brace expansion (generates: a b c)
{1..10}      # sequence expansion (generates: 1 2 3 ... 10)
*.txt        # filename expansion / globbing
```

## 7. Arithmetic Expressions

Used in `$((...))`, `((...))`, `let`, `declare -i`, array subscripts.

### Operators (highest to lowest precedence)

| Precedence | Operators                                                | Description                  |
| ---------- | -------------------------------------------------------- | ---------------------------- |
| 1          | `id++` `id--`                                            | post-increment/decrement     |
| 2          | `++id` `--id`                                            | pre-increment/decrement      |
| 3          | `-` `+`                                                  | unary minus/plus             |
| 4          | `!` `~`                                                  | logical NOT, bitwise NOT     |
| 5          | `**`                                                     | exponentiation (right-assoc) |
| 6          | `*` `/` `%`                                              | multiply, divide, remainder  |
| 7          | `+` `-`                                                  | add, subtract                |
| 8          | `<<` `>>`                                                | bitwise shifts               |
| 9          | `<=` `>=` `<` `>`                                        | comparison                   |
| 10         | `==` `!=`                                                | equality                     |
| 11         | `&`                                                      | bitwise AND                  |
| 12         | `^`                                                      | bitwise XOR                  |
| 13         | `\|`                                                     | bitwise OR                   |
| 14         | `&&`                                                     | logical AND                  |
| 15         | `\|\|`                                                   | logical OR                   |
| 16         | `?:`                                                     | ternary conditional          |
| 17         | `=` `*=` `/=` `%=` `+=` `-=` `<<=` `>>=` `&=` `^=` `\|=` | assignment                   |
| 18         | `,`                                                      | comma                        |

### Number Formats
- `123` - decimal
- `0777` - octal (leading 0)
- `0xFF` - hexadecimal (0x or 0X)
- `2#1010` - arbitrary base (base#number, base 2-64)

### Variables in Arithmetic
- Variables referenced by name without `$`: `((x + y))`
- Unset/null variables evaluate to 0
- Arrays: `arr[0]`, `arr[i+1]`

## 8. Quoting

```
'...'         # single quotes: literal, no expansion
"..."         # double quotes: $, `, and \ are special
              # \ only special before: $ ` " \ newline
              # ! triggers history expansion (interactive)
$'...'        # ANSI-C quoting: \n, \t, \xHH, \uHHHH, etc.
$"..."        # locale translation (gettext)
\c            # escape next character (outside quotes)
```

### Special Characters That Need Quoting
```
| & ; ( ) < > space tab newline
* ? [ ] # ~ = %
$ ` " ' \
{ } !
```

## 9. Reserved Words

Only reserved when unquoted and first word of a command (or after `;;`, etc.):
```
! { } [[ ]] case coproc do done elif else esac fi for
function if in select then time until while
```

**Note:** `{` and `}` require whitespace separation to be recognized as reserved words.
`[[` and `]]` start/end conditional expressions. `!` negates pipeline exit status.
`time` is only recognized at the start of a pipeline.

Recognition is context-sensitive:
- `in` is only reserved after `for`, `case`, or `select`
- `do` is only reserved after `for`/`while`/`until`/`select` condition list
- `then` is only reserved after `if`/`elif` condition list

## 10. Tokens/Operators

### Control Operators
```
|| && ;; ;& ;;& ( ) | |& ; & \n
```

### Redirection Operators
```
< > << >> <& >& <<- <<< <> >| &> &>>
```

## 11. Context-Sensitive Parsing Notes

### Keywords Are Contextual
```bash
for=1         # 'for' is a variable name here
echo for      # 'for' is a regular word here
for x in a b  # 'for' is a keyword here
```

### `{` and `}` Are Reserved Words
```bash
{ echo hi; }  # brace group (space after { required!)
{echo hi}     # NOT a brace group, it's the word "{echo" + "hi}"
```

### `[[` Has Special Parsing
Inside `[[ ... ]]`:
- Word splitting disabled
- `<` and `>` are string comparison, not redirection
- `=~` does regex matching
- Glob patterns not expanded on right side of `==`

### Heredoc Parsing
```bash
cat <<EOF && echo "continues on same logical line"
heredoc content
EOF
```
The heredoc delimiter (`<<EOF`) appears in the command, but the heredoc body
comes after the line containing the delimiter. The rest of the line after `<<EOF`
is still part of the same command. This requires special handling in the parser:
1. When `<<DELIM` is seen, register that a heredoc is pending
2. Continue parsing the rest of the command line normally
3. After the line is complete, read heredoc content until `DELIM` is found
4. Multiple heredocs can be pending: `cat <<A <<B` reads body A then body B

### Assignment vs. Command
```bash
foo=bar           # assignment (foo becomes a variable)
foo =bar          # command 'foo' with argument '=bar'
foo= bar          # assignment 'foo=' then command 'bar'
foo=bar baz       # assignment 'foo=bar' exported to command 'baz'
```

### Process Substitution vs. Comparison
```bash
cat <(cmd)        # process substitution
[[ a < b ]]       # string comparison (inside [[)
[ a \< b ]        # string comparison (escaped in [)
cmd < file        # redirection
```

---

## Source Files

Reference materials (not included in repo, download separately to `reference/`):

- `bash-parse.y` - Official GNU Bash YACC grammar
- `posix-shell.html` - POSIX shell specification
- `bash-manpage.txt` - Complete bash man page
