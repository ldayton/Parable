class ParseError extends Error {
    constructor(message, pos, line) {
        super();
        this.message = message;
        this.pos = pos;
        this.line = line;
    }
    
    FormatMessage() {
        if (((this.line != null) && (this.pos != null))) {
            return ((((("Parse error at line " + String(this.line)) + ", position ") + String(this.pos)) + ": ") + this.message);
        } else if ((this.pos != null)) {
            return ((("Parse error at position " + String(this.pos)) + ": ") + this.message);
        }
        return ("Parse error: " + this.message);
    }
    
}

function IsHexDigit(c) {
    return (((c >= "0") && (c <= "9")) || ((c >= "a") && (c <= "f")) || ((c >= "A") && (c <= "F")));
}

function IsOctalDigit(c) {
    return ((c >= "0") && (c <= "7"));
}

// ANSI-C escape sequence byte values
var ANSI_C_ESCAPES = {"a": 7, "b": 8, "e": 27, "E": 27, "f": 12, "n": 10, "r": 13, "t": 9, "v": 11, "\\": 92, "\"": 34, "?": 63};
function GetAnsiEscape(c) {
    if ((c === "a")) {
        return 7;
    }
    if ((c === "b")) {
        return 8;
    }
    if (((c === "e") || (c === "E"))) {
        return 27;
    }
    if ((c === "f")) {
        return 12;
    }
    if ((c === "n")) {
        return 10;
    }
    if ((c === "r")) {
        return 13;
    }
    if ((c === "t")) {
        return 9;
    }
    if ((c === "v")) {
        return 11;
    }
    if ((c === "\\")) {
        return 92;
    }
    if ((c === "\"")) {
        return 34;
    }
    if ((c === "?")) {
        return 63;
    }
    return -1;
}

function IsWhitespace(c) {
    return ((c === " ") || (c === "\t") || (c === "\n"));
}

function IsWhitespaceNoNewline(c) {
    return ((c === " ") || (c === "\t"));
}

function StartsWithAt(s, pos, prefix) {
    return s.startsWith(prefix, pos);
}

class Node {
    toSexp() {
        throw new Error("Not implemented");
    }
    
}

class Word extends Node {
    constructor(value, parts) {
        super();
        this.kind = "word";
        this.value = value;
        if ((parts == null)) {
            parts = [];
        }
        this.parts = parts;
    }
    
    toSexp() {
        var value = this.value;
        // Expand ALL $'...' ANSI-C quotes (handles escapes and strips $)
        value = this.ExpandAllAnsiCQuotes(value);
        // Strip $ from locale strings $"..." (quote-aware)
        value = this.StripLocaleStringDollars(value);
        // Normalize whitespace in array assignments: name=(a  b\tc) -> name=(a b c)
        value = this.NormalizeArrayWhitespace(value);
        // Format command substitutions with bash-oracle pretty-printing (before escaping)
        value = this.FormatCommandSubstitutions(value);
        // Strip line continuations (backslash-newline) from arithmetic expressions
        value = this.StripArithLineContinuations(value);
        // Double CTLESC (0x01) bytes - bash-oracle uses this for quoting control chars
        // Exception: don't double when preceded by odd number of backslashes (escaped)
        value = this.DoubleCtlescSmart(value);
        // Prefix DEL (0x7f) with CTLESC - bash-oracle quotes this control char
        value = value.replaceAll("", "");
        // Escape backslashes for s-expression output
        value = value.replaceAll("\\", "\\\\");
        // Escape double quotes, newlines, and tabs
        var escaped = value.replaceAll("\"", "\\\"").replaceAll("\n", "\\n").replaceAll("\t", "\\t");
        return (("(word \"" + escaped) + "\")");
    }
    
    AppendWithCtlesc(result, byte_val) {
        result.push(byte_val);
    }
    
    DoubleCtlescSmart(value) {
        var result = [];
        var in_single = false;
        var in_double = false;
        for (let c of value) {
            // Track quote state
            if (((c === "'") && !in_double)) {
                in_single = !in_single;
            } else if (((c === "\"") && !in_single)) {
                in_double = !in_double;
            }
            result.push(c);
            if ((c === "")) {
                // Only count backslashes in double-quoted context (where they escape)
                // In single quotes, backslashes are literal, so always double CTLESC
                if (in_double) {
                    var bs_count = 0;
                    for (let j = (result.length - 2); j > -1; j--) {
                        if ((result[j] === "\\")) {
                            bs_count += 1;
                        } else {
                            break;
                        }
                    }
                    if (((bs_count % 2) === 0)) {
                        result.push("");
                    }
                } else {
                    // Outside double quotes (including single quotes): always double
                    result.push("");
                }
            }
        }
        return result.join("");
    }
    
    ExpandAnsiCEscapes(value) {
        if (!(value.startsWith("'") && value.endsWith("'"))) {
            return value;
        }
        var inner = value.slice(1, (value.length - 1));
        var result = [];
        var i = 0;
        while ((i < inner.length)) {
            if (((inner[i] === "\\") && ((i + 1) < inner.length))) {
                var c = inner[(i + 1)];
                // Check simple escapes first
                var simple = GetAnsiEscape(c);
                if ((simple >= 0)) {
                    result.push(simple);
                    i += 2;
                } else if ((c === "'")) {
                    // bash-oracle outputs \' as '\'' (shell quoting trick)
                    result.push(...[39, 92, 39, 39]);
                    i += 2;
                } else if ((c === "x")) {
                    // Check for \x{...} brace syntax (bash 5.3+)
                    if ((((i + 2) < inner.length) && (inner[(i + 2)] === "{"))) {
                        // Find closing brace or end of hex digits
                        var j = (i + 3);
                        while (((j < inner.length) && IsHexDigit(inner[j]))) {
                            j += 1;
                        }
                        var hex_str = inner.slice((i + 3), j);
                        if (((j < inner.length) && (inner[j] === "}"))) {
                            j += 1;
                        }
                        // If no hex digits, treat as NUL (truncates)
                        if (!hex_str) {
                            return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
                        }
                        var byte_val = (parseInt(hex_str, 16) & 255);
                        if ((byte_val === 0)) {
                            return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
                        }
                        this.AppendWithCtlesc(result, byte_val);
                        i = j;
                    } else {
                        // Hex escape \xHH (1-2 hex digits) - raw byte
                        j = (i + 2);
                        while (((j < inner.length) && (j < (i + 4)) && IsHexDigit(inner[j]))) {
                            j += 1;
                        }
                        if ((j > (i + 2))) {
                            byte_val = parseInt(inner.slice((i + 2), j), 16);
                            if ((byte_val === 0)) {
                                // NUL truncates string
                                return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
                            }
                            this.AppendWithCtlesc(result, byte_val);
                            i = j;
                        } else {
                            result.push(inner[i].charCodeAt(0));
                            i += 1;
                        }
                    }
                } else if ((c === "u")) {
                    // Unicode escape \uHHHH (1-4 hex digits) - encode as UTF-8
                    j = (i + 2);
                    while (((j < inner.length) && (j < (i + 6)) && IsHexDigit(inner[j]))) {
                        j += 1;
                    }
                    if ((j > (i + 2))) {
                        var codepoint = parseInt(inner.slice((i + 2), j), 16);
                        if ((codepoint === 0)) {
                            // NUL truncates string
                            return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
                        }
                        result.push(...Array.from(new TextEncoder().encode(String.fromCodePoint(codepoint))));
                        i = j;
                    } else {
                        result.push(inner[i].charCodeAt(0));
                        i += 1;
                    }
                } else if ((c === "U")) {
                    // Unicode escape \UHHHHHHHH (1-8 hex digits) - encode as UTF-8
                    j = (i + 2);
                    while (((j < inner.length) && (j < (i + 10)) && IsHexDigit(inner[j]))) {
                        j += 1;
                    }
                    if ((j > (i + 2))) {
                        codepoint = parseInt(inner.slice((i + 2), j), 16);
                        if ((codepoint === 0)) {
                            // NUL truncates string
                            return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
                        }
                        result.push(...Array.from(new TextEncoder().encode(String.fromCodePoint(codepoint))));
                        i = j;
                    } else {
                        result.push(inner[i].charCodeAt(0));
                        i += 1;
                    }
                } else if ((c === "c")) {
                    // Control character \cX - mask with 0x1f
                    if (((i + 3) <= inner.length)) {
                        var ctrl_char = inner[(i + 2)];
                        var ctrl_val = (ctrl_char.charCodeAt(0) & 31);
                        if ((ctrl_val === 0)) {
                            // NUL truncates string
                            return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
                        }
                        this.AppendWithCtlesc(result, ctrl_val);
                        i += 3;
                    } else {
                        result.push(inner[i].charCodeAt(0));
                        i += 1;
                    }
                } else if ((c === "0")) {
                    // Nul or octal \0 or \0NNN
                    j = (i + 2);
                    while (((j < inner.length) && (j < (i + 5)) && IsOctalDigit(inner[j]))) {
                        j += 1;
                    }
                    if ((j > (i + 2))) {
                        byte_val = parseInt(inner.slice((i + 1), j), 8);
                        if ((byte_val === 0)) {
                            // NUL truncates string
                            return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
                        }
                        this.AppendWithCtlesc(result, byte_val);
                        i = j;
                    } else {
                        // Just \0 - NUL truncates string
                        return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
                    }
                } else if (((c >= "1") && (c <= "7"))) {
                    // Octal escape \NNN (1-3 digits) - raw byte
                    j = (i + 1);
                    while (((j < inner.length) && (j < (i + 4)) && IsOctalDigit(inner[j]))) {
                        j += 1;
                    }
                    byte_val = parseInt(inner.slice((i + 1), j), 8);
                    if ((byte_val === 0)) {
                        // NUL truncates string
                        return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
                    }
                    this.AppendWithCtlesc(result, byte_val);
                    i = j;
                } else {
                    // Unknown escape - preserve as-is
                    result.push(92);
                    result.push(c.charCodeAt(0));
                    i += 2;
                }
            } else {
                result.push(...Array.from(new TextEncoder().encode(inner[i])));
                i += 1;
            }
        }
        // Decode as UTF-8, replacing invalid sequences with U+FFFD
        return (("'" + new TextDecoder().decode(new Uint8Array(result))) + "'");
    }
    
    ExpandAllAnsiCQuotes(value) {
        var result = [];
        var i = 0;
        var in_single_quote = false;
        var in_double_quote = false;
        var brace_depth = 0;
        while ((i < value.length)) {
            var ch = value[i];
            // Track brace depth for parameter expansions
            if (!in_single_quote) {
                if (StartsWithAt(value, i, "${")) {
                    brace_depth += 1;
                    result.push("${");
                    i += 2;
                    continue;
                } else if (((ch === "}") && (brace_depth > 0))) {
                    brace_depth -= 1;
                    result.push(ch);
                    i += 1;
                    continue;
                }
            }
            // Inside ${...}, we can expand $'...' even if originally in double quotes
            var effective_in_dquote = (in_double_quote && (brace_depth === 0));
            // Track quote state to avoid matching $' inside regular quotes
            if (((ch === "'") && !effective_in_dquote)) {
                // Check if this is start of $'...' ANSI-C string
                if ((!in_single_quote && (i > 0) && (value[(i - 1)] === "$"))) {
                    // This is handled below when we see $'
                    result.push(ch);
                    i += 1;
                } else if (in_single_quote) {
                    // End of single-quoted string
                    in_single_quote = false;
                    result.push(ch);
                    i += 1;
                } else {
                    // Start of regular single-quoted string
                    in_single_quote = true;
                    result.push(ch);
                    i += 1;
                }
            } else if (((ch === "\"") && !in_single_quote)) {
                in_double_quote = !in_double_quote;
                result.push(ch);
                i += 1;
            } else if (((ch === "\\") && ((i + 1) < value.length) && !in_single_quote)) {
                // Backslash escape - skip both chars to avoid misinterpreting \" or \'
                result.push(ch);
                result.push(value[(i + 1)]);
                i += 2;
            } else if ((StartsWithAt(value, i, "$'") && !in_single_quote && !effective_in_dquote)) {
                // ANSI-C quoted string - find matching closing quote
                var j = (i + 2);
                while ((j < value.length)) {
                    if (((value[j] === "\\") && ((j + 1) < value.length))) {
                        j += 2;
                    } else if ((value[j] === "'")) {
                        j += 1;
                        break;
                    } else {
                        j += 1;
                    }
                }
                // Extract and expand the $'...' sequence
                var ansi_str = value.slice(i, j);
                // Strip the $ and expand escapes
                var expanded = this.ExpandAnsiCEscapes(ansi_str.slice(1, ansi_str.length));
                // Inside ${...}, strip quotes for default/alternate value operators
                // but keep them for pattern replacement operators
                if (((brace_depth > 0) && expanded.startsWith("'") && expanded.endsWith("'"))) {
                    var inner = expanded.slice(1, (expanded.length - 1));
                    // Only strip if non-empty, no CTLESC, and after a default value operator
                    if ((inner && (inner.indexOf("") === -1))) {
                        // Check what precedes - default value ops: :- := :+ :? - = + ?
                        if ((result.length >= 2)) {
                            var prev = result.slice((result.length - 2), result.length).join("");
                        } else {
                            prev = "";
                        }
                        if ((prev.endsWith(":-") || prev.endsWith(":=") || prev.endsWith(":+") || prev.endsWith(":?"))) {
                            expanded = inner;
                        } else if ((result.length >= 1)) {
                            var last = result[(result.length - 1)];
                            // Single char operators (not after :), but not /
                            if ((((last === "-") || (last === "=") || (last === "+") || (last === "?")) && ((result.length < 2) || (result[(result.length - 2)] !== ":")))) {
                                expanded = inner;
                            }
                        }
                    }
                }
                result.push(expanded);
                i = j;
            } else {
                result.push(ch);
                i += 1;
            }
        }
        return result.join("");
    }
    
    StripLocaleStringDollars(value) {
        var result = [];
        var i = 0;
        var in_single_quote = false;
        var in_double_quote = false;
        while ((i < value.length)) {
            var ch = value[i];
            if (((ch === "'") && !in_double_quote)) {
                in_single_quote = !in_single_quote;
                result.push(ch);
                i += 1;
            } else if (((ch === "\"") && !in_single_quote)) {
                in_double_quote = !in_double_quote;
                result.push(ch);
                i += 1;
            } else if (((ch === "\\") && ((i + 1) < value.length))) {
                // Escape - copy both chars
                result.push(ch);
                result.push(value[(i + 1)]);
                i += 2;
            } else if ((StartsWithAt(value, i, "$\"") && !in_single_quote && !in_double_quote)) {
                // Locale string $"..." outside quotes - strip the $ and enter double quote
                result.push("\"");
                in_double_quote = true;
                i += 2;
            } else {
                result.push(ch);
                i += 1;
            }
        }
        return result.join("");
    }
    
    NormalizeArrayWhitespace(value) {
        // Match array assignment pattern: name=( or name+=(
        if (!value.endsWith(")")) {
            return value;
        }
        // Parse identifier: starts with letter/underscore, then alnum/underscore
        var i = 0;
        if (!((i < value.length) && (/^[a-zA-Z]$/.test(value[i]) || (value[i] === "_")))) {
            return value;
        }
        i += 1;
        while (((i < value.length) && (/^[a-zA-Z0-9]$/.test(value[i]) || (value[i] === "_")))) {
            i += 1;
        }
        // Optional + for +=
        if (((i < value.length) && (value[i] === "+"))) {
            i += 1;
        }
        // Must have =(
        if (!(((i + 1) < value.length) && (value[i] === "=") && (value[(i + 1)] === "("))) {
            return value;
        }
        var prefix = value.slice(0, (i + 1));
        // Extract content inside parentheses
        var inner = value.slice((prefix.length + 1), (value.length - 1));
        // Normalize whitespace while respecting quotes
        var normalized = [];
        i = 0;
        var in_whitespace = true;
        while ((i < inner.length)) {
            var ch = inner[i];
            if (IsWhitespace(ch)) {
                if ((!in_whitespace && normalized)) {
                    normalized.push(" ");
                    in_whitespace = true;
                }
                i += 1;
            } else if ((ch === "'")) {
                // Single-quoted string - preserve as-is
                in_whitespace = false;
                var j = (i + 1);
                while (((j < inner.length) && (inner[j] !== "'"))) {
                    j += 1;
                }
                normalized.push(inner.slice(i, (j + 1)));
                i = (j + 1);
            } else if ((ch === "\"")) {
                // Double-quoted string - preserve as-is
                in_whitespace = false;
                j = (i + 1);
                while ((j < inner.length)) {
                    if (((inner[j] === "\\") && ((j + 1) < inner.length))) {
                        j += 2;
                    } else if ((inner[j] === "\"")) {
                        break;
                    } else {
                        j += 1;
                    }
                }
                normalized.push(inner.slice(i, (j + 1)));
                i = (j + 1);
            } else if (((ch === "\\") && ((i + 1) < inner.length))) {
                // Escape sequence
                in_whitespace = false;
                normalized.push(inner.slice(i, (i + 2)));
                i += 2;
            } else {
                in_whitespace = false;
                normalized.push(ch);
                i += 1;
            }
        }
        // Strip trailing space
        var result = normalized.join("").replace(/[ ]+$/, "");
        return (((prefix + "(") + result) + ")");
    }
    
    StripArithLineContinuations(value) {
        var result = [];
        var i = 0;
        while ((i < value.length)) {
            // Check for $(( arithmetic expression
            if (StartsWithAt(value, i, "$((")) {
                // Find matching ))
                var start = i;
                i += 3;
                var depth = 1;
                var arith_content = [];
                while (((i < value.length) && (depth > 0))) {
                    if (StartsWithAt(value, i, "((")) {
                        arith_content.push("((");
                        depth += 1;
                        i += 2;
                    } else if (StartsWithAt(value, i, "))")) {
                        depth -= 1;
                        if ((depth > 0)) {
                            arith_content.push("))");
                        }
                        i += 2;
                    } else if (((value[i] === "\\") && ((i + 1) < value.length) && (value[(i + 1)] === "\n"))) {
                        // Skip backslash-newline (line continuation)
                        i += 2;
                    } else {
                        arith_content.push(value[i]);
                        i += 1;
                    }
                }
                if ((depth === 0)) {
                    // Found proper )) closing - this is arithmetic
                    result.push((("$((" + arith_content.join("")) + "))"));
                } else {
                    // Didn't find )) - not arithmetic (likely $( + ( subshell), pass through
                    result.push(value.slice(start, i));
                }
            } else {
                result.push(value[i]);
                i += 1;
            }
        }
        return result.join("");
    }
    
    CollectCmdsubs(node) {
        var result = [];
        var node_kind = (node.kind ?? null);
        if ((node_kind === "cmdsub")) {
            result.push(node);
        } else {
            var expr = (node.expression ?? null);
            if ((expr != null)) {
                // ArithmeticExpansion, ArithBinaryOp, etc.
                result.push(...this.CollectCmdsubs(expr));
            }
        }
        var left = (node.left ?? null);
        if ((left != null)) {
            result.push(...this.CollectCmdsubs(left));
        }
        var right = (node.right ?? null);
        if ((right != null)) {
            result.push(...this.CollectCmdsubs(right));
        }
        var operand = (node.operand ?? null);
        if ((operand != null)) {
            result.push(...this.CollectCmdsubs(operand));
        }
        var condition = (node.condition ?? null);
        if ((condition != null)) {
            result.push(...this.CollectCmdsubs(condition));
        }
        var true_value = (node.true_value ?? null);
        if ((true_value != null)) {
            result.push(...this.CollectCmdsubs(true_value));
        }
        var false_value = (node.false_value ?? null);
        if ((false_value != null)) {
            result.push(...this.CollectCmdsubs(false_value));
        }
        return result;
    }
    
    FormatCommandSubstitutions(value) {
        // Collect command substitutions from all parts, including nested ones
        var cmdsub_parts = [];
        var procsub_parts = [];
        for (let p of this.parts) {
            if ((p.kind === "cmdsub")) {
                cmdsub_parts.push(p);
            } else if ((p.kind === "procsub")) {
                procsub_parts.push(p);
            } else {
                cmdsub_parts.push(...this.CollectCmdsubs(p));
            }
        }
        // Check if we have ${ or ${| brace command substitutions to format
        var has_brace_cmdsub = ((value.indexOf("${ ") !== -1) || (value.indexOf("${|") !== -1));
        if ((cmdsub_parts.length === 0 && procsub_parts.length === 0 && !has_brace_cmdsub)) {
            return value;
        }
        var result = [];
        var i = 0;
        var cmdsub_idx = 0;
        var procsub_idx = 0;
        while ((i < value.length)) {
            // Check for $( command substitution (but not $(( arithmetic)
            if ((StartsWithAt(value, i, "$(") && !StartsWithAt(value, i, "$((") && (cmdsub_idx < cmdsub_parts.length))) {
                // Find matching close paren using bash-aware matching
                var j = FindCmdsubEnd(value, (i + 2));
                // Format this command substitution
                var node = cmdsub_parts[cmdsub_idx];
                var formatted = FormatCmdsubNode(node.command);
                // Add space after $( if content starts with ( to avoid $((
                if (formatted.startsWith("(")) {
                    result.push((("$( " + formatted) + ")"));
                } else {
                    result.push((("$(" + formatted) + ")"));
                }
                cmdsub_idx += 1;
                i = j;
            } else if (((value[i] === "`") && (cmdsub_idx < cmdsub_parts.length))) {
                // Check for backtick command substitution
                // Find matching backtick
                j = (i + 1);
                while ((j < value.length)) {
                    if (((value[j] === "\\") && ((j + 1) < value.length))) {
                        j += 2;
                        continue;
                    }
                    if ((value[j] === "`")) {
                        j += 1;
                        break;
                    }
                    j += 1;
                }
                // Keep backtick substitutions as-is (bash-oracle doesn't reformat them)
                result.push(value.slice(i, j));
                cmdsub_idx += 1;
                i = j;
            } else if (((StartsWithAt(value, i, ">(") || StartsWithAt(value, i, "<(")) && (procsub_idx < procsub_parts.length))) {
                // Check for >( or <( process substitution
                var direction = value[i];
                // Find matching close paren
                j = FindCmdsubEnd(value, (i + 2));
                // Format this process substitution (with in_procsub=True for no-space subshells)
                node = procsub_parts[procsub_idx];
                formatted = FormatCmdsubNode(node.command, 0, true);
                result.push((((direction + "(") + formatted) + ")"));
                procsub_idx += 1;
                i = j;
            } else if ((StartsWithAt(value, i, "${ ") || StartsWithAt(value, i, "${|"))) {
                // Check for ${ (space) or ${| brace command substitution
                var prefix = value.slice(i, (i + 3));
                // Find matching close brace
                j = (i + 3);
                var depth = 1;
                while (((j < value.length) && (depth > 0))) {
                    if ((value[j] === "{")) {
                        depth += 1;
                    } else if ((value[j] === "}")) {
                        depth -= 1;
                    }
                    j += 1;
                }
                // Parse and format the inner content
                var inner = value.slice((i + 2), (j - 1));
                // Check if content is all whitespace - normalize to single space
                if ((inner.trim() === "")) {
                    result.push("${ }");
                } else {
                    try {
                        var parser = new Parser(inner.replace(/^[ |]+/, ""));
                        var parsed = parser.parseList();
                        if (parsed) {
                            formatted = FormatCmdsubNode(parsed);
                            result.push(((prefix + formatted) + "; }"));
                        } else {
                            result.push("${ }");
                        }
                    } catch (_) {
                        result.push(value.slice(i, j));
                    }
                }
                i = j;
            } else {
                result.push(value[i]);
                i += 1;
            }
        }
        return result.join("");
    }
    
    getCondFormattedValue() {
        // Expand ANSI-C quotes
        var value = this.ExpandAllAnsiCQuotes(this.value);
        // Format command substitutions
        value = this.FormatCommandSubstitutions(value);
        // Bash doubles CTLESC (\x01) characters in output
        value = value.replaceAll("", "");
        return value.replace(/[\n]+$/, "");
    }
    
}

class Command extends Node {
    constructor(words, redirects) {
        super();
        this.kind = "command";
        this.words = words;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
    }
    
    toSexp() {
        var parts = [];
        for (let w of this.words) {
            parts.push(w.toSexp());
        }
        for (let r of this.redirects) {
            parts.push(r.toSexp());
        }
        var inner = parts.join(" ");
        if (!inner) {
            return "(command)";
        }
        return (("(command " + inner) + ")");
    }
    
}

class Pipeline extends Node {
    constructor(commands) {
        super();
        this.kind = "pipeline";
        this.commands = commands;
    }
    
    toSexp() {
        if ((this.commands.length === 1)) {
            return this.commands[0].toSexp();
        }
        // Build list of (cmd, needs_pipe_both_redirect) filtering out PipeBoth markers
        var cmds = [];
        var i = 0;
        while ((i < this.commands.length)) {
            var cmd = this.commands[i];
            if ((cmd.kind === "pipe-both")) {
                i += 1;
                continue;
            }
            // Check if next element is PipeBoth
            var needs_redirect = (((i + 1) < this.commands.length) && (this.commands[(i + 1)].kind === "pipe-both"));
            cmds.push([cmd, needs_redirect]);
            i += 1;
        }
        if ((cmds.length === 1)) {
            var pair = cmds[0];
            cmd = pair[0];
            var needs = pair[1];
            return this.CmdSexp(cmd, needs);
        }
        // Nest right-associatively: (pipe a (pipe b c))
        var last_pair = cmds[(cmds.length - 1)];
        var last_cmd = last_pair[0];
        var last_needs = last_pair[1];
        var result = this.CmdSexp(last_cmd, last_needs);
        var j = (cmds.length - 2);
        while ((j >= 0)) {
            pair = cmds[j];
            cmd = pair[0];
            needs = pair[1];
            if ((needs && (cmd.kind !== "command"))) {
                // Compound command: redirect as sibling in pipe
                result = (((("(pipe " + cmd.toSexp()) + " (redirect \">&\" 1) ") + result) + ")");
            } else {
                result = (((("(pipe " + this.CmdSexp(cmd, needs)) + " ") + result) + ")");
            }
            j -= 1;
        }
        return result;
    }
    
    CmdSexp(cmd, needs_redirect) {
        if (!needs_redirect) {
            return cmd.toSexp();
        }
        if ((cmd.kind === "command")) {
            // Inject redirect inside command
            var parts = [];
            for (let w of cmd.words) {
                parts.push(w.toSexp());
            }
            for (let r of cmd.redirects) {
                parts.push(r.toSexp());
            }
            parts.push("(redirect \">&\" 1)");
            return (("(command " + parts.join(" ")) + ")");
        }
        // Compound command handled by caller
        return cmd.toSexp();
    }
    
}

class List extends Node {
    constructor(parts) {
        super();
        this.kind = "list";
        this.parts = parts;
    }
    
    toSexp() {
        // parts = [cmd, op, cmd, op, cmd, ...]
        // Bash precedence: && and || bind tighter than ; and &
        var parts = Array.from(this.parts);
        var op_names = {"&&": "and", "||": "or", ";": "semi", "\n": "semi", "&": "background"};
        // Strip trailing ; or \n (bash ignores it)
        while (((parts.length > 1) && (parts[(parts.length - 1)].kind === "operator") && ((parts[(parts.length - 1)].op === ";") || (parts[(parts.length - 1)].op === "\n")))) {
            parts = parts.slice(0, (parts.length - 1));
        }
        if ((parts.length === 1)) {
            return parts[0].toSexp();
        }
        // Handle trailing & as unary background operator
        // & only applies to the immediately preceding pipeline, not the whole list
        if (((parts[(parts.length - 1)].kind === "operator") && (parts[(parts.length - 1)].op === "&"))) {
            // Find rightmost ; or \n to split there
            for (let i = (parts.length - 3); i > 0; i--) {
                if (((parts[i].kind === "operator") && ((parts[i].op === ";") || (parts[i].op === "\n")))) {
                    var left = parts.slice(0, i);
                    var right = parts.slice((i + 1), (parts.length - 1));
                    if ((left.length > 1)) {
                        var left_sexp = new List(left).toSexp();
                    } else {
                        left_sexp = left[0].toSexp();
                    }
                    if ((right.length > 1)) {
                        var right_sexp = new List(right).toSexp();
                    } else {
                        right_sexp = right[0].toSexp();
                    }
                    return (((("(semi " + left_sexp) + " (background ") + right_sexp) + "))");
                }
            }
            // No ; or \n found, background the whole list (minus trailing &)
            var inner_parts = parts.slice(0, (parts.length - 1));
            if ((inner_parts.length === 1)) {
                return (("(background " + inner_parts[0].toSexp()) + ")");
            }
            var inner_list = new List(inner_parts);
            return (("(background " + inner_list.toSexp()) + ")");
        }
        // Process by precedence: first split on ; and &, then on && and ||
        return this.ToSexpWithPrecedence(parts, op_names);
    }
    
    ToSexpWithPrecedence(parts, op_names) {
        // Process operators by precedence: ; (lowest), then &, then && and ||
        // Split on ; or \n first (rightmost for left-associativity)
        for (let i = (parts.length - 2); i > 0; i--) {
            if (((parts[i].kind === "operator") && ((parts[i].op === ";") || (parts[i].op === "\n")))) {
                var left = parts.slice(0, i);
                var right = parts.slice((i + 1), parts.length);
                if ((left.length > 1)) {
                    var left_sexp = new List(left).toSexp();
                } else {
                    left_sexp = left[0].toSexp();
                }
                if ((right.length > 1)) {
                    var right_sexp = new List(right).toSexp();
                } else {
                    right_sexp = right[0].toSexp();
                }
                return (((("(semi " + left_sexp) + " ") + right_sexp) + ")");
            }
        }
        // Then split on & (rightmost for left-associativity)
        for (let i = (parts.length - 2); i > 0; i--) {
            if (((parts[i].kind === "operator") && (parts[i].op === "&"))) {
                left = parts.slice(0, i);
                right = parts.slice((i + 1), parts.length);
                if ((left.length > 1)) {
                    left_sexp = new List(left).toSexp();
                } else {
                    left_sexp = left[0].toSexp();
                }
                if ((right.length > 1)) {
                    right_sexp = new List(right).toSexp();
                } else {
                    right_sexp = right[0].toSexp();
                }
                return (((("(background " + left_sexp) + " ") + right_sexp) + ")");
            }
        }
        // No ; or &, process high-prec ops (&&, ||) left-associatively
        var result = parts[0].toSexp();
        for (let i = 1; i < (parts.length - 1); i += 2) {
            var op = parts[i];
            var cmd = parts[(i + 1)];
            var op_name = (op_names[op.op] ?? op.op);
            result = (((((("(" + op_name) + " ") + result) + " ") + cmd.toSexp()) + ")");
        }
        return result;
    }
    
}

class Operator extends Node {
    constructor(op) {
        super();
        this.kind = "operator";
        this.op = op;
    }
    
    toSexp() {
        var names = {"&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe"};
        return (("(" + (names[this.op] ?? this.op)) + ")");
    }
    
}

class PipeBoth extends Node {
    constructor() {
        super();
        this.kind = "pipe-both";
    }
    
    toSexp() {
        return "(pipe-both)";
    }
    
}

class Empty extends Node {
    constructor() {
        super();
        this.kind = "empty";
    }
    
    toSexp() {
        return "";
    }
    
}

class Comment extends Node {
    constructor(text) {
        super();
        this.kind = "comment";
        this.text = text;
    }
    
    toSexp() {
        // bash-oracle doesn't output comments
        return "";
    }
    
}

class Redirect extends Node {
    constructor(op, target, fd) {
        super();
        this.kind = "redirect";
        this.op = op;
        this.target = target;
        this.fd = fd;
    }
    
    toSexp() {
        // Strip fd prefix from operator (e.g., "2>" -> ">", "{fd}>" -> ">")
        var op = this.op.replace(/^[0123456789]+/, "");
        // Strip {varname} prefix if present
        if (op.startsWith("{")) {
            var j = 1;
            if (((j < op.length) && (/^[a-zA-Z]$/.test(op[j]) || (op[j] === "_")))) {
                j += 1;
                while (((j < op.length) && (/^[a-zA-Z0-9]$/.test(op[j]) || (op[j] === "_")))) {
                    j += 1;
                }
                if (((j < op.length) && (op[j] === "}"))) {
                    op = op.slice((j + 1), op.length);
                }
            }
        }
        var target_val = this.target.value;
        // Expand ANSI-C $'...' quotes (converts escapes like \n to actual newline)
        target_val = new Word(target_val).ExpandAllAnsiCQuotes(target_val);
        // Strip $ from locale strings $"..."
        target_val = target_val.replaceAll("$\"", "\"");
        // For fd duplication, target starts with & (e.g., "&1", "&2", "&-")
        if (target_val.startsWith("&")) {
            // Determine the real operator
            if ((op === ">")) {
                op = ">&";
            } else if ((op === "<")) {
                op = "<&";
            }
            var fd_target = target_val.slice(1, target_val.length).replace(/[\-]+$/, "");
            if (/^[0-9]+$/.test(fd_target)) {
                return (((("(redirect \"" + op) + "\" ") + fd_target) + ")");
            } else if ((target_val === "&-")) {
                return "(redirect \">&-\" 0)";
            } else {
                // Variable fd dup like >&$fd or >&$fd- (move) - strip the & and trailing -
                return (((("(redirect \"" + op) + "\" \"") + fd_target) + "\")");
            }
        }
        // Handle case where op is already >& or <&
        if (((op === ">&") || (op === "<&"))) {
            if (/^[0-9]+$/.test(target_val)) {
                return (((("(redirect \"" + op) + "\" ") + target_val) + ")");
            }
            // Variable fd dup with move indicator (trailing -)
            target_val = target_val.replace(/[\-]+$/, "");
            return (((("(redirect \"" + op) + "\" \"") + target_val) + "\")");
        }
        return (((("(redirect \"" + op) + "\" \"") + target_val) + "\")");
    }
    
}

class HereDoc extends Node {
    constructor(delimiter, content, strip_tabs, quoted, fd) {
        super();
        if (strip_tabs == null) { strip_tabs = false; }
        if (quoted == null) { quoted = false; }
        this.kind = "heredoc";
        this.delimiter = delimiter;
        this.content = content;
        this.strip_tabs = strip_tabs;
        this.quoted = quoted;
        this.fd = fd;
    }
    
    toSexp() {
        if (this.strip_tabs) {
            var op = "<<-";
        } else {
            op = "<<";
        }
        return (((("(redirect \"" + op) + "\" \"") + this.content) + "\")");
    }
    
}

class Subshell extends Node {
    constructor(body, redirects) {
        super();
        this.kind = "subshell";
        this.body = body;
        this.redirects = redirects;
    }
    
    toSexp() {
        var base = (("(subshell " + this.body.toSexp()) + ")");
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            return ((base + " ") + redirect_parts.join(" "));
        }
        return base;
    }
    
}

class BraceGroup extends Node {
    constructor(body, redirects) {
        super();
        this.kind = "brace-group";
        this.body = body;
        this.redirects = redirects;
    }
    
    toSexp() {
        var base = (("(brace-group " + this.body.toSexp()) + ")");
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            return ((base + " ") + redirect_parts.join(" "));
        }
        return base;
    }
    
}

class If extends Node {
    constructor(condition, then_body, else_body, redirects) {
        super();
        this.kind = "if";
        this.condition = condition;
        this.then_body = then_body;
        this.else_body = else_body;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
    }
    
    toSexp() {
        var result = ((("(if " + this.condition.toSexp()) + " ") + this.then_body.toSexp());
        if (this.else_body) {
            result = ((result + " ") + this.else_body.toSexp());
        }
        result = (result + ")");
        for (let r of this.redirects) {
            result = ((result + " ") + r.toSexp());
        }
        return result;
    }
    
}

class While extends Node {
    constructor(condition, body, redirects) {
        super();
        this.kind = "while";
        this.condition = condition;
        this.body = body;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
    }
    
    toSexp() {
        var base = (((("(while " + this.condition.toSexp()) + " ") + this.body.toSexp()) + ")");
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            return ((base + " ") + redirect_parts.join(" "));
        }
        return base;
    }
    
}

class Until extends Node {
    constructor(condition, body, redirects) {
        super();
        this.kind = "until";
        this.condition = condition;
        this.body = body;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
    }
    
    toSexp() {
        var base = (((("(until " + this.condition.toSexp()) + " ") + this.body.toSexp()) + ")");
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            return ((base + " ") + redirect_parts.join(" "));
        }
        return base;
    }
    
}

class For extends Node {
    constructor(variable, words, body, redirects) {
        super();
        this.kind = "for";
        this.variable = variable;
        this.words = words;
        this.body = body;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
    }
    
    toSexp() {
        // bash-oracle format: (for (word "var") (in (word "a") ...) body)
        var suffix = "";
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            suffix = (" " + redirect_parts.join(" "));
        }
        var var_escaped = this.variable.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
        if ((this.words == null)) {
            // No 'in' clause - bash-oracle implies (in (word "\"$@\""))
            return ((((("(for (word \"" + var_escaped) + "\") (in (word \"\\\"$@\\\"\")) ") + this.body.toSexp()) + ")") + suffix);
        } else if ((this.words.length === 0)) {
            // Empty 'in' clause - bash-oracle outputs (in)
            return ((((("(for (word \"" + var_escaped) + "\") (in) ") + this.body.toSexp()) + ")") + suffix);
        } else {
            var word_parts = [];
            for (let w of this.words) {
                word_parts.push(w.toSexp());
            }
            var word_strs = word_parts.join(" ");
            return ((((((("(for (word \"" + var_escaped) + "\") (in ") + word_strs) + ") ") + this.body.toSexp()) + ")") + suffix);
        }
    }
    
}

class ForArith extends Node {
    constructor(init, cond, incr, body, redirects) {
        super();
        this.kind = "for-arith";
        this.init = init;
        this.cond = cond;
        this.incr = incr;
        this.body = body;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
    }
    
    toSexp() {
        // bash-oracle format: (arith-for (init (word "x")) (test (word "y")) (step (word "z")) body)
        function formatArithVal(s) {
            // Use Word's methods to expand ANSI-C quotes and strip locale $
            var w = new Word(s, []);
            var val = w.ExpandAllAnsiCQuotes(s);
            val = w.StripLocaleStringDollars(val);
            val = val.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
            return val;
        }
        
        var suffix = "";
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            suffix = (" " + redirect_parts.join(" "));
        }
        if (this.init) {
            var init_val = this.init;
        } else {
            init_val = "1";
        }
        if (this.cond) {
            var cond_val = NormalizeFdRedirects(this.cond);
        } else {
            cond_val = "1";
        }
        if (this.incr) {
            var incr_val = this.incr;
        } else {
            incr_val = "1";
        }
        return ((((((((((("(arith-for (init (word \"" + formatArithVal(init_val)) + "\")) ") + "(test (word \"") + formatArithVal(cond_val)) + "\")) ") + "(step (word \"") + formatArithVal(incr_val)) + "\")) ") + this.body.toSexp()) + ")") + suffix);
    }
    
}

class Select extends Node {
    constructor(variable, words, body, redirects) {
        super();
        this.kind = "select";
        this.variable = variable;
        this.words = words;
        this.body = body;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
    }
    
    toSexp() {
        // bash-oracle format: (select (word "var") (in (word "a") ...) body)
        var suffix = "";
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            suffix = (" " + redirect_parts.join(" "));
        }
        var var_escaped = this.variable.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
        if ((this.words != null)) {
            var word_parts = [];
            for (let w of this.words) {
                word_parts.push(w.toSexp());
            }
            var word_strs = word_parts.join(" ");
            if (this.words && this.words.length) {
                var in_clause = (("(in " + word_strs) + ")");
            } else {
                in_clause = "(in)";
            }
        } else {
            // No 'in' clause means implicit "$@"
            in_clause = "(in (word \"\\\"$@\\\"\"))";
        }
        return ((((((("(select (word \"" + var_escaped) + "\") ") + in_clause) + " ") + this.body.toSexp()) + ")") + suffix);
    }
    
}

class Case extends Node {
    constructor(word, patterns, redirects) {
        super();
        this.kind = "case";
        this.word = word;
        this.patterns = patterns;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
    }
    
    toSexp() {
        var parts = [];
        parts.push(("(case " + this.word.toSexp()));
        for (let p of this.patterns) {
            parts.push(p.toSexp());
        }
        var base = (parts.join(" ") + ")");
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            return ((base + " ") + redirect_parts.join(" "));
        }
        return base;
    }
    
}

function ConsumeSingleQuote(s, start) {
    var chars = ["'"];
    var i = (start + 1);
    while (((i < s.length) && (s[i] !== "'"))) {
        chars.push(s[i]);
        i += 1;
    }
    if ((i < s.length)) {
        chars.push(s[i]);
        i += 1;
    }
    return [i, chars];
}

function ConsumeDoubleQuote(s, start) {
    var chars = ["\""];
    var i = (start + 1);
    while (((i < s.length) && (s[i] !== "\""))) {
        if (((s[i] === "\\") && ((i + 1) < s.length))) {
            chars.push(s[i]);
            i += 1;
        }
        chars.push(s[i]);
        i += 1;
    }
    if ((i < s.length)) {
        chars.push(s[i]);
        i += 1;
    }
    return [i, chars];
}

function HasBracketClose(s, start, depth) {
    var i = start;
    while ((i < s.length)) {
        if ((s[i] === "]")) {
            return true;
        }
        if ((((s[i] === "|") || (s[i] === ")")) && (depth === 0))) {
            return false;
        }
        i += 1;
    }
    return false;
}

function ConsumeBracketClass(s, start, depth) {
    // First scan to see if this is a valid bracket expression
    var scan_pos = (start + 1);
    // Skip [! or [^ at start
    if (((scan_pos < s.length) && ((s[scan_pos] === "!") || (s[scan_pos] === "^")))) {
        scan_pos += 1;
    }
    // Handle ] as first char
    if (((scan_pos < s.length) && (s[scan_pos] === "]"))) {
        if (HasBracketClose(s, (scan_pos + 1), depth)) {
            scan_pos += 1;
        }
    }
    // Scan for closing ]
    var is_bracket = false;
    while ((scan_pos < s.length)) {
        if ((s[scan_pos] === "]")) {
            is_bracket = true;
            break;
        }
        if (((s[scan_pos] === ")") && (depth === 0))) {
            break;
        }
        scan_pos += 1;
    }
    if (!is_bracket) {
        return [(start + 1), ["["], false];
    }
    // Valid bracket - consume it
    var chars = ["["];
    var i = (start + 1);
    // Handle [! or [^
    if (((i < s.length) && ((s[i] === "!") || (s[i] === "^")))) {
        chars.push(s[i]);
        i += 1;
    }
    // Handle ] as first char
    if (((i < s.length) && (s[i] === "]"))) {
        if (HasBracketClose(s, (i + 1), depth)) {
            chars.push(s[i]);
            i += 1;
        }
    }
    // Consume until ]
    while (((i < s.length) && (s[i] !== "]"))) {
        chars.push(s[i]);
        i += 1;
    }
    if ((i < s.length)) {
        chars.push(s[i]);
        i += 1;
    }
    return [i, chars, true];
}

class CasePattern extends Node {
    constructor(pattern, body, terminator) {
        super();
        if (terminator == null) { terminator = ";;"; }
        this.kind = "pattern";
        this.pattern = pattern;
        this.body = body;
        this.terminator = terminator;
    }
    
    toSexp() {
        // bash-oracle format: (pattern ((word "a") (word "b")) body)
        // Split pattern by | respecting escapes, extglobs, quotes, and brackets
        var alternatives = [];
        var current = [];
        var i = 0;
        var depth = 0;
        while ((i < this.pattern.length)) {
            var ch = this.pattern[i];
            if (((ch === "\\") && ((i + 1) < this.pattern.length))) {
                current.push(this.pattern.slice(i, (i + 2)));
                i += 2;
            } else if ((((ch === "@") || (ch === "?") || (ch === "*") || (ch === "+") || (ch === "!")) && ((i + 1) < this.pattern.length) && (this.pattern[(i + 1)] === "("))) {
                // Start of extglob: @(, ?(, *(, +(, !(
                current.push(ch);
                current.push("(");
                depth += 1;
                i += 2;
            } else if (((ch === "$") && ((i + 1) < this.pattern.length) && (this.pattern[(i + 1)] === "("))) {
                // $( command sub or $(( arithmetic - track depth
                current.push(ch);
                current.push("(");
                depth += 1;
                i += 2;
            } else if (((ch === "(") && (depth > 0))) {
                current.push(ch);
                depth += 1;
                i += 1;
            } else if (((ch === ")") && (depth > 0))) {
                current.push(ch);
                depth -= 1;
                i += 1;
            } else if ((ch === "[")) {
                var result = ConsumeBracketClass(this.pattern, i, depth);
                i = result[0];
                current.push(...result[1]);
            } else if (((ch === "'") && (depth === 0))) {
                result = ConsumeSingleQuote(this.pattern, i);
                i = result[0];
                current.push(...result[1]);
            } else if (((ch === "\"") && (depth === 0))) {
                result = ConsumeDoubleQuote(this.pattern, i);
                i = result[0];
                current.push(...result[1]);
            } else if (((ch === "|") && (depth === 0))) {
                alternatives.push(current.join(""));
                current = [];
                i += 1;
            } else {
                current.push(ch);
                i += 1;
            }
        }
        alternatives.push(current.join(""));
        var word_list = [];
        for (let alt of alternatives) {
            // Use Word.to_sexp() to properly expand ANSI-C quotes and escape
            word_list.push(new Word(alt).toSexp());
        }
        var pattern_str = word_list.join(" ");
        var parts = [(("(pattern (" + pattern_str) + ")")];
        if (this.body) {
            parts.push((" " + this.body.toSexp()));
        } else {
            parts.push(" ()");
        }
        // bash-oracle doesn't output fallthrough/falltest markers
        parts.push(")");
        return parts.join("");
    }
    
}

class Function extends Node {
    constructor(name, body) {
        super();
        this.kind = "function";
        this.name = name;
        this.body = body;
    }
    
    toSexp() {
        return (((("(function \"" + this.name) + "\" ") + this.body.toSexp()) + ")");
    }
    
}

class ParamExpansion extends Node {
    constructor(param, op, arg) {
        super();
        this.kind = "param";
        this.param = param;
        this.op = op;
        this.arg = arg;
    }
    
    toSexp() {
        var escaped_param = this.param.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
        if ((this.op != null)) {
            var escaped_op = this.op.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
            if ((this.arg != null)) {
                var arg_val = this.arg;
            } else {
                arg_val = "";
            }
            var escaped_arg = arg_val.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
            return (((((("(param \"" + escaped_param) + "\" \"") + escaped_op) + "\" \"") + escaped_arg) + "\")");
        }
        return (("(param \"" + escaped_param) + "\")");
    }
    
}

class ParamLength extends Node {
    constructor(param) {
        super();
        this.kind = "param-len";
        this.param = param;
    }
    
    toSexp() {
        var escaped = this.param.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
        return (("(param-len \"" + escaped) + "\")");
    }
    
}

class ParamIndirect extends Node {
    constructor(param, op, arg) {
        super();
        this.kind = "param-indirect";
        this.param = param;
        this.op = op;
        this.arg = arg;
    }
    
    toSexp() {
        var escaped = this.param.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
        if ((this.op != null)) {
            var escaped_op = this.op.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
            if ((this.arg != null)) {
                var arg_val = this.arg;
            } else {
                arg_val = "";
            }
            var escaped_arg = arg_val.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"");
            return (((((("(param-indirect \"" + escaped) + "\" \"") + escaped_op) + "\" \"") + escaped_arg) + "\")");
        }
        return (("(param-indirect \"" + escaped) + "\")");
    }
    
}

class CommandSubstitution extends Node {
    constructor(command) {
        super();
        this.kind = "cmdsub";
        this.command = command;
    }
    
    toSexp() {
        return (("(cmdsub " + this.command.toSexp()) + ")");
    }
    
}

class ArithmeticExpansion extends Node {
    constructor(expression) {
        super();
        this.kind = "arith";
        this.expression = expression;
    }
    
    toSexp() {
        if ((this.expression == null)) {
            return "(arith)";
        }
        return (("(arith " + this.expression.toSexp()) + ")");
    }
    
}

class ArithmeticCommand extends Node {
    constructor(expression, redirects, raw_content) {
        super();
        if (raw_content == null) { raw_content = ""; }
        this.kind = "arith-cmd";
        this.expression = expression;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
        this.raw_content = raw_content;
    }
    
    toSexp() {
        // bash-oracle format: (arith (word "content"))
        // Redirects are siblings: (arith (word "...")) (redirect ...)
        var escaped = this.raw_content.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n");
        var result = (("(arith (word \"" + escaped) + "\"))");
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            var redirect_sexps = redirect_parts.join(" ");
            return ((result + " ") + redirect_sexps);
        }
        return result;
    }
    
}

// Arithmetic expression nodes
class ArithNumber extends Node {
    constructor(value) {
        super();
        this.kind = "number";
        this.value = value;
    }
    
    toSexp() {
        return (("(number \"" + this.value) + "\")");
    }
    
}

class ArithVar extends Node {
    constructor(name) {
        super();
        this.kind = "var";
        this.name = name;
    }
    
    toSexp() {
        return (("(var \"" + this.name) + "\")");
    }
    
}

class ArithBinaryOp extends Node {
    constructor(op, left, right) {
        super();
        this.kind = "binary-op";
        this.op = op;
        this.left = left;
        this.right = right;
    }
    
    toSexp() {
        return (((((("(binary-op \"" + this.op) + "\" ") + this.left.toSexp()) + " ") + this.right.toSexp()) + ")");
    }
    
}

class ArithUnaryOp extends Node {
    constructor(op, operand) {
        super();
        this.kind = "unary-op";
        this.op = op;
        this.operand = operand;
    }
    
    toSexp() {
        return (((("(unary-op \"" + this.op) + "\" ") + this.operand.toSexp()) + ")");
    }
    
}

class ArithPreIncr extends Node {
    constructor(operand) {
        super();
        this.kind = "pre-incr";
        this.operand = operand;
    }
    
    toSexp() {
        return (("(pre-incr " + this.operand.toSexp()) + ")");
    }
    
}

class ArithPostIncr extends Node {
    constructor(operand) {
        super();
        this.kind = "post-incr";
        this.operand = operand;
    }
    
    toSexp() {
        return (("(post-incr " + this.operand.toSexp()) + ")");
    }
    
}

class ArithPreDecr extends Node {
    constructor(operand) {
        super();
        this.kind = "pre-decr";
        this.operand = operand;
    }
    
    toSexp() {
        return (("(pre-decr " + this.operand.toSexp()) + ")");
    }
    
}

class ArithPostDecr extends Node {
    constructor(operand) {
        super();
        this.kind = "post-decr";
        this.operand = operand;
    }
    
    toSexp() {
        return (("(post-decr " + this.operand.toSexp()) + ")");
    }
    
}

class ArithAssign extends Node {
    constructor(op, target, value) {
        super();
        this.kind = "assign";
        this.op = op;
        this.target = target;
        this.value = value;
    }
    
    toSexp() {
        return (((((("(assign \"" + this.op) + "\" ") + this.target.toSexp()) + " ") + this.value.toSexp()) + ")");
    }
    
}

class ArithTernary extends Node {
    constructor(condition, if_true, if_false) {
        super();
        this.kind = "ternary";
        this.condition = condition;
        this.if_true = if_true;
        this.if_false = if_false;
    }
    
    toSexp() {
        return (((((("(ternary " + this.condition.toSexp()) + " ") + this.if_true.toSexp()) + " ") + this.if_false.toSexp()) + ")");
    }
    
}

class ArithComma extends Node {
    constructor(left, right) {
        super();
        this.kind = "comma";
        this.left = left;
        this.right = right;
    }
    
    toSexp() {
        return (((("(comma " + this.left.toSexp()) + " ") + this.right.toSexp()) + ")");
    }
    
}

class ArithSubscript extends Node {
    constructor(array, index) {
        super();
        this.kind = "subscript";
        this.array = array;
        this.index = index;
    }
    
    toSexp() {
        return (((("(subscript \"" + this.array) + "\" ") + this.index.toSexp()) + ")");
    }
    
}

class ArithEscape extends Node {
    constructor(char) {
        super();
        this.kind = "escape";
        this.char = char;
    }
    
    toSexp() {
        return (("(escape \"" + this.char) + "\")");
    }
    
}

class ArithDeprecated extends Node {
    constructor(expression) {
        super();
        this.kind = "arith-deprecated";
        this.expression = expression;
    }
    
    toSexp() {
        var escaped = this.expression.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n");
        return (("(arith-deprecated \"" + escaped) + "\")");
    }
    
}

class AnsiCQuote extends Node {
    constructor(content) {
        super();
        this.kind = "ansi-c";
        this.content = content;
    }
    
    toSexp() {
        var escaped = this.content.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n");
        return (("(ansi-c \"" + escaped) + "\")");
    }
    
}

class LocaleString extends Node {
    constructor(content) {
        super();
        this.kind = "locale";
        this.content = content;
    }
    
    toSexp() {
        var escaped = this.content.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n");
        return (("(locale \"" + escaped) + "\")");
    }
    
}

class ProcessSubstitution extends Node {
    constructor(direction, command) {
        super();
        this.kind = "procsub";
        this.direction = direction;
        this.command = command;
    }
    
    toSexp() {
        return (((("(procsub \"" + this.direction) + "\" ") + this.command.toSexp()) + ")");
    }
    
}

class Negation extends Node {
    constructor(pipeline) {
        super();
        this.kind = "negation";
        this.pipeline = pipeline;
    }
    
    toSexp() {
        if ((this.pipeline == null)) {
            // Bare "!" with no command - bash-oracle shows empty command
            return "(negation (command))";
        }
        return (("(negation " + this.pipeline.toSexp()) + ")");
    }
    
}

class Time extends Node {
    constructor(pipeline, posix) {
        super();
        if (posix == null) { posix = false; }
        this.kind = "time";
        this.pipeline = pipeline;
        this.posix = posix;
    }
    
    toSexp() {
        if ((this.pipeline == null)) {
            // Bare "time" with no command - bash-oracle shows empty command
            if (this.posix) {
                return "(time -p (command))";
            } else {
                return "(time (command))";
            }
        }
        if (this.posix) {
            return (("(time -p " + this.pipeline.toSexp()) + ")");
        }
        return (("(time " + this.pipeline.toSexp()) + ")");
    }
    
}

class ConditionalExpr extends Node {
    constructor(body, redirects) {
        super();
        this.kind = "cond-expr";
        this.body = body;
        if ((redirects == null)) {
            redirects = [];
        }
        this.redirects = redirects;
    }
    
    toSexp() {
        // bash-oracle format: (cond ...) not (cond-expr ...)
        // Redirects are siblings, not children: (cond ...) (redirect ...)
        var body_kind = (this.body.kind ?? null);
        if ((body_kind == null)) {
            // body is a string
            var escaped = this.body.replaceAll("\\", "\\\\").replaceAll("\"", "\\\"").replaceAll("\n", "\\n");
            var result = (("(cond \"" + escaped) + "\")");
        } else {
            result = (("(cond " + this.body.toSexp()) + ")");
        }
        if (this.redirects && this.redirects.length) {
            var redirect_parts = [];
            for (let r of this.redirects) {
                redirect_parts.push(r.toSexp());
            }
            var redirect_sexps = redirect_parts.join(" ");
            return ((result + " ") + redirect_sexps);
        }
        return result;
    }
    
}

class UnaryTest extends Node {
    constructor(op, operand) {
        super();
        this.kind = "unary-test";
        this.op = op;
        this.operand = operand;
    }
    
    toSexp() {
        // bash-oracle format: (cond-unary "-f" (cond-term "file"))
        // cond-term preserves content as-is (no backslash escaping)
        return (((("(cond-unary \"" + this.op) + "\" (cond-term \"") + this.operand.value) + "\"))");
    }
    
}

class BinaryTest extends Node {
    constructor(op, left, right) {
        super();
        this.kind = "binary-test";
        this.op = op;
        this.left = left;
        this.right = right;
    }
    
    toSexp() {
        // bash-oracle format: (cond-binary "==" (cond-term "x") (cond-term "y"))
        // cond-term preserves content as-is (no backslash escaping)
        var left_val = this.left.getCondFormattedValue();
        var right_val = this.right.getCondFormattedValue();
        return (((((("(cond-binary \"" + this.op) + "\" (cond-term \"") + left_val) + "\") (cond-term \"") + right_val) + "\"))");
    }
    
}

class CondAnd extends Node {
    constructor(left, right) {
        super();
        this.kind = "cond-and";
        this.left = left;
        this.right = right;
    }
    
    toSexp() {
        return (((("(cond-and " + this.left.toSexp()) + " ") + this.right.toSexp()) + ")");
    }
    
}

class CondOr extends Node {
    constructor(left, right) {
        super();
        this.kind = "cond-or";
        this.left = left;
        this.right = right;
    }
    
    toSexp() {
        return (((("(cond-or " + this.left.toSexp()) + " ") + this.right.toSexp()) + ")");
    }
    
}

class CondNot extends Node {
    constructor(operand) {
        super();
        this.kind = "cond-not";
        this.operand = operand;
    }
    
    toSexp() {
        // bash-oracle ignores negation - just output the operand
        return this.operand.toSexp();
    }
    
}

class CondParen extends Node {
    constructor(inner) {
        super();
        this.kind = "cond-paren";
        this.inner = inner;
    }
    
    toSexp() {
        return (("(cond-expr " + this.inner.toSexp()) + ")");
    }
    
}

class ArrayNode extends Node {
    constructor(elements) {
        super();
        this.kind = "array";
        this.elements = elements;
    }
    
    toSexp() {
        if (!this.elements) {
            return "(array)";
        }
        var parts = [];
        for (let e of this.elements) {
            parts.push(e.toSexp());
        }
        var inner = parts.join(" ");
        return (("(array " + inner) + ")");
    }
    
}

class Coproc extends Node {
    constructor(command, name) {
        super();
        this.kind = "coproc";
        this.command = command;
        this.name = name;
    }
    
    toSexp() {
        // Use provided name for compound commands, "COPROC" for simple commands
        if (this.name) {
            var name = this.name;
        } else {
            name = "COPROC";
        }
        return (((("(coproc \"" + name) + "\" ") + this.command.toSexp()) + ")");
    }
    
}

function FormatCmdsubNode(node, indent, in_procsub) {
    if (indent == null) { indent = 0; }
    if (in_procsub == null) { in_procsub = false; }
    var sp = " ".repeat(indent);
    var inner_sp = " ".repeat((indent + 4));
    if ((node.kind === "empty")) {
        return "";
    }
    if ((node.kind === "command")) {
        var parts = [];
        for (let w of node.words) {
            var val = w.ExpandAllAnsiCQuotes(w.value);
            val = w.FormatCommandSubstitutions(val);
            parts.push(val);
        }
        for (let r of node.redirects) {
            parts.push(FormatRedirect(r));
        }
        return parts.join(" ");
    }
    if ((node.kind === "pipeline")) {
        var cmd_parts = [];
        for (let cmd of node.commands) {
            cmd_parts.push(FormatCmdsubNode(cmd, indent));
        }
        return cmd_parts.join(" | ");
    }
    if ((node.kind === "list")) {
        // Join commands with operators
        var result = [];
        for (let p of node.parts) {
            if ((p.kind === "operator")) {
                if ((p.op === ";")) {
                    result.push(";");
                } else if ((p.op === "\n")) {
                    // Skip newline if it follows a semicolon (redundant separator)
                    if ((result.length > 0 && (result[(result.length - 1)] === ";"))) {
                        continue;
                    }
                    result.push("\n");
                } else if ((p.op === "&")) {
                    result.push(" &");
                } else {
                    result.push((" " + p.op));
                }
            } else {
                if ((result.length > 0 && !(result[(result.length - 1)].endsWith(" ") || result[(result.length - 1)].endsWith("\n")))) {
                    result.push(" ");
                }
                result.push(FormatCmdsubNode(p, indent));
            }
        }
        // Strip trailing ; or newline
        var s = result.join("");
        while ((s.endsWith(";") || s.endsWith("\n"))) {
            s = s.slice(0, (s.length - 1));
        }
        return s;
    }
    if ((node.kind === "if")) {
        var cond = FormatCmdsubNode(node.condition, indent);
        var then_body = FormatCmdsubNode(node.then_body, (indent + 4));
        result = ((((("if " + cond) + "; then\n") + inner_sp) + then_body) + ";");
        if (node.else_body) {
            var else_body = FormatCmdsubNode(node.else_body, (indent + 4));
            result = ((((((result + "\n") + sp) + "else\n") + inner_sp) + else_body) + ";");
        }
        result = (((result + "\n") + sp) + "fi");
        return result;
    }
    if ((node.kind === "while")) {
        cond = FormatCmdsubNode(node.condition, indent);
        var body = FormatCmdsubNode(node.body, (indent + 4));
        return ((((((("while " + cond) + "; do\n") + inner_sp) + body) + ";\n") + sp) + "done");
    }
    if ((node.kind === "until")) {
        cond = FormatCmdsubNode(node.condition, indent);
        body = FormatCmdsubNode(node.body, (indent + 4));
        return ((((((("until " + cond) + "; do\n") + inner_sp) + body) + ";\n") + sp) + "done");
    }
    if ((node.kind === "for")) {
        var variable = node.variable;
        body = FormatCmdsubNode(node.body, (indent + 4));
        if (node.words) {
            var word_vals = [];
            for (let w of node.words) {
                word_vals.push(w.value);
            }
            var words = word_vals.join(" ");
            return ((((((((("for " + variable) + " in ") + words) + ";\ndo\n") + inner_sp) + body) + ";\n") + sp) + "done");
        }
        return ((((((("for " + variable) + ";\ndo\n") + inner_sp) + body) + ";\n") + sp) + "done");
    }
    if ((node.kind === "case")) {
        var word = node.word.value;
        var patterns = [];
        var i = 0;
        while ((i < node.patterns.length)) {
            p = node.patterns[i];
            var pat = p.pattern.replaceAll("|", " | ");
            if (p.body) {
                body = FormatCmdsubNode(p.body, (indent + 8));
            } else {
                body = "";
            }
            var term = p.terminator;
            var pat_indent = " ".repeat((indent + 8));
            var term_indent = " ".repeat((indent + 4));
            if ((i === 0)) {
                // First pattern on same line as 'in'
                patterns.push((((((((" " + pat) + ")\n") + pat_indent) + body) + "\n") + term_indent) + term));
            } else {
                patterns.push(((((((pat + ")\n") + pat_indent) + body) + "\n") + term_indent) + term));
            }
            i += 1;
        }
        var pattern_str = patterns.join(("\n" + " ".repeat((indent + 4))));
        return (((((("case " + word) + " in") + pattern_str) + "\n") + sp) + "esac");
    }
    if ((node.kind === "function")) {
        var name = node.name;
        // Get the body content - if it's a BraceGroup, unwrap it
        if ((node.body.kind === "brace-group")) {
            body = FormatCmdsubNode(node.body.body, (indent + 4));
        } else {
            body = FormatCmdsubNode(node.body, (indent + 4));
        }
        body = body.replace(/[;]+$/, "");
        return ((((("function " + name) + " () \n{ \n") + inner_sp) + body) + "\n}");
    }
    if ((node.kind === "subshell")) {
        body = FormatCmdsubNode(node.body, indent, in_procsub);
        var redirects = "";
        if (node.redirects) {
            var redirect_parts = [];
            for (let r of node.redirects) {
                redirect_parts.push(FormatRedirect(r));
            }
            redirects = redirect_parts.join(" ");
        }
        if (in_procsub) {
            if (redirects) {
                return ((("(" + body) + ") ") + redirects);
            }
            return (("(" + body) + ")");
        }
        if (redirects) {
            return ((("( " + body) + " ) ") + redirects);
        }
        return (("( " + body) + " )");
    }
    if ((node.kind === "brace-group")) {
        body = FormatCmdsubNode(node.body, indent);
        body = body.replace(/[;]+$/, "");
        return (("{ " + body) + "; }");
    }
    if ((node.kind === "arith-cmd")) {
        return (("((" + node.raw_content) + "))");
    }
    // Fallback: return empty for unknown types
    return "";
}

function FormatRedirect(r) {
    if ((r.kind === "heredoc")) {
        // Include heredoc content: <<DELIM\ncontent\nDELIM\n
        if (r.strip_tabs) {
            var op = "<<-";
        } else {
            op = "<<";
        }
        if (r.quoted) {
            var delim = (("'" + r.delimiter) + "'");
        } else {
            delim = r.delimiter;
        }
        return (((((op + delim) + "\n") + r.content) + r.delimiter) + "\n");
    }
    op = r.op;
    var target = r.target.value;
    // For fd duplication (target starts with &), handle normalization
    if (target.startsWith("&")) {
        // Normalize N<&- to N>&- (close always uses >)
        if (((target === "&-") && op.endsWith("<"))) {
            op = (op.slice(0, (op.length - 1)) + ">");
        }
        // Add default fd for bare >&N or <&N
        if ((op === ">")) {
            op = "1>";
        } else if ((op === "<")) {
            op = "0<";
        }
        return (op + target);
    }
    return ((op + " ") + target);
}

function NormalizeFdRedirects(s) {
    // Match >&N or <&N not preceded by a digit, add default fd
    var result = [];
    var i = 0;
    while ((i < s.length)) {
        // Check for >&N or <&N
        if ((((i + 2) < s.length) && (s[(i + 1)] === "&") && /^[0-9]+$/.test(s[(i + 2)]))) {
            var prev_is_digit = ((i > 0) && /^[0-9]+$/.test(s[(i - 1)]));
            if (((s[i] === ">") && !prev_is_digit)) {
                result.push("1>&");
                result.push(s[(i + 2)]);
                i += 3;
                continue;
            } else if (((s[i] === "<") && !prev_is_digit)) {
                result.push("0<&");
                result.push(s[(i + 2)]);
                i += 3;
                continue;
            }
        }
        result.push(s[i]);
        i += 1;
    }
    return result.join("");
}

function FindCmdsubEnd(value, start) {
    var depth = 1;
    var i = start;
    var in_single = false;
    var in_double = false;
    var case_depth = 0;
    var in_case_patterns = false;
    while (((i < value.length) && (depth > 0))) {
        var c = value[i];
        // Handle escapes
        if (((c === "\\") && ((i + 1) < value.length) && !in_single)) {
            i += 2;
            continue;
        }
        // Handle quotes
        if (((c === "'") && !in_double)) {
            in_single = !in_single;
            i += 1;
            continue;
        }
        if (((c === "\"") && !in_single)) {
            in_double = !in_double;
            i += 1;
            continue;
        }
        if (in_single) {
            i += 1;
            continue;
        }
        if (in_double) {
            // Inside double quotes, $() command substitution is still active
            if ((StartsWithAt(value, i, "$(") && !StartsWithAt(value, i, "$(("))) {
                // Recursively find end of nested command substitution
                var j = FindCmdsubEnd(value, (i + 2));
                i = j;
                continue;
            }
            // Skip other characters inside double quotes
            i += 1;
            continue;
        }
        // Handle comments - skip from # to end of line
        // Only treat # as comment if preceded by whitespace or at start
        if (((c === "#") && ((i === start) || (value[(i - 1)] === " ") || (value[(i - 1)] === "\t") || (value[(i - 1)] === "\n") || (value[(i - 1)] === ";") || (value[(i - 1)] === "|") || (value[(i - 1)] === "&") || (value[(i - 1)] === "(") || (value[(i - 1)] === ")")))) {
            while (((i < value.length) && (value[i] !== "\n"))) {
                i += 1;
            }
            continue;
        }
        // Handle heredocs
        if (StartsWithAt(value, i, "<<")) {
            i = SkipHeredoc(value, i);
            continue;
        }
        // Check for 'case' keyword
        if ((StartsWithAt(value, i, "case") && IsWordBoundary(value, i, 4))) {
            case_depth += 1;
            in_case_patterns = false;
            i += 4;
            continue;
        }
        // Check for 'in' keyword (after case)
        if (((case_depth > 0) && StartsWithAt(value, i, "in") && IsWordBoundary(value, i, 2))) {
            in_case_patterns = true;
            i += 2;
            continue;
        }
        // Check for 'esac' keyword
        if ((StartsWithAt(value, i, "esac") && IsWordBoundary(value, i, 4))) {
            if ((case_depth > 0)) {
                case_depth -= 1;
                in_case_patterns = false;
            }
            i += 4;
            continue;
        }
        // Check for ';;' (end of case pattern, next pattern or esac follows)
        if (StartsWithAt(value, i, ";;")) {
            i += 2;
            continue;
        }
        // Handle parens
        if ((c === "(")) {
            depth += 1;
        } else if ((c === ")")) {
            // In case patterns, ) after pattern name is not a grouping paren
            if ((in_case_patterns && (case_depth > 0))) {
                // This ) is a case pattern terminator, skip it
            } else {
                depth -= 1;
            }
        }
        i += 1;
    }
    return i;
}

function SkipHeredoc(value, start) {
    var i = (start + 2);
    // Handle <<- (strip tabs)
    if (((i < value.length) && (value[i] === "-"))) {
        i += 1;
    }
    // Skip whitespace before delimiter
    while (((i < value.length) && IsWhitespaceNoNewline(value[i]))) {
        i += 1;
    }
    // Extract delimiter - may be quoted
    var delim_start = i;
    var quote_char = null;
    if (((i < value.length) && ((value[i] === "\"") || (value[i] === "'")))) {
        quote_char = value[i];
        i += 1;
        delim_start = i;
        while (((i < value.length) && (value[i] !== quote_char))) {
            i += 1;
        }
        var delimiter = value.slice(delim_start, i);
        if ((i < value.length)) {
            i += 1;
        }
    } else if (((i < value.length) && (value[i] === "\\"))) {
        // Backslash-quoted delimiter like <<\EOF
        i += 1;
        delim_start = i;
        while (((i < value.length) && !IsWhitespace(value[i]))) {
            i += 1;
        }
        delimiter = value.slice(delim_start, i);
    } else {
        // Unquoted delimiter
        while (((i < value.length) && !IsWhitespace(value[i]))) {
            i += 1;
        }
        delimiter = value.slice(delim_start, i);
    }
    // Skip to end of line (heredoc content starts on next line)
    while (((i < value.length) && (value[i] !== "\n"))) {
        i += 1;
    }
    if ((i < value.length)) {
        i += 1;
    }
    // Find the end delimiter on its own line
    while ((i < value.length)) {
        var line_start = i;
        // Find end of this line
        var line_end = i;
        while (((line_end < value.length) && (value[line_end] !== "\n"))) {
            line_end += 1;
        }
        var line = value.slice(line_start, line_end);
        // Check if this line is the delimiter (possibly with leading tabs for <<-)
        if ((((start + 2) < value.length) && (value[(start + 2)] === "-"))) {
            var stripped = line.replace(/^[\t]+/, "");
        } else {
            stripped = line;
        }
        if ((stripped === delimiter)) {
            // Found end - return position after delimiter line
            if ((line_end < value.length)) {
                return (line_end + 1);
            } else {
                return line_end;
            }
        }
        if ((line_end < value.length)) {
            i = (line_end + 1);
        } else {
            i = line_end;
        }
    }
    return i;
}

function IsWordBoundary(s, pos, word_len) {
    // Check character before
    if (((pos > 0) && /^[a-zA-Z0-9]$/.test(s[(pos - 1)]))) {
        return false;
    }
    // Check character after
    var end = (pos + word_len);
    if (((end < s.length) && /^[a-zA-Z0-9]$/.test(s[end]))) {
        return false;
    }
    return true;
}

// Reserved words that cannot be command names
var RESERVED_WORDS = new Set(["if", "then", "elif", "else", "fi", "while", "until", "for", "select", "do", "done", "case", "esac", "in", "function", "coproc"]);
// Metacharacters that break words (unquoted)
// Note: {} are NOT metacharacters - they're only special at command position
// for brace groups. In words like {a,b,c}, braces are literal.
var METACHAR = new Set(" \t\n|&;()<>");
var COND_UNARY_OPS = new Set(["-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"]);
var COND_BINARY_OPS = new Set(["==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"]);
var COMPOUND_KEYWORDS = new Set(["while", "until", "for", "if", "case", "select"]);
function IsQuote(c) {
    return ((c === "'") || (c === "\""));
}

function IsMetachar(c) {
    return ((c === " ") || (c === "\t") || (c === "\n") || (c === "|") || (c === "&") || (c === ";") || (c === "(") || (c === ")") || (c === "<") || (c === ">"));
}

function IsExtglobPrefix(c) {
    return ((c === "@") || (c === "?") || (c === "*") || (c === "+") || (c === "!"));
}

function IsRedirectChar(c) {
    return ((c === "<") || (c === ">"));
}

function IsSpecialParam(c) {
    return ((c === "?") || (c === "$") || (c === "!") || (c === "#") || (c === "@") || (c === "*") || (c === "-"));
}

function IsDigit(c) {
    return ((c >= "0") && (c <= "9"));
}

function IsSemicolonOrNewline(c) {
    return ((c === ";") || (c === "\n"));
}

function IsRightBracket(c) {
    return ((c === ")") || (c === "}"));
}

function IsWordStartContext(c) {
    return ((c === " ") || (c === "\t") || (c === "\n") || (c === ";") || (c === "|") || (c === "&") || (c === "<") || (c === "("));
}

function IsWordEndContext(c) {
    return ((c === " ") || (c === "\t") || (c === "\n") || (c === ";") || (c === "|") || (c === "&") || (c === "<") || (c === ">") || (c === "(") || (c === ")"));
}

function IsSpecialParamOrDigit(c) {
    return (IsSpecialParam(c) || IsDigit(c));
}

function IsParamExpansionOp(c) {
    return ((c === ":") || (c === "-") || (c === "=") || (c === "+") || (c === "?") || (c === "#") || (c === "%") || (c === "/") || (c === "^") || (c === ",") || (c === "@") || (c === "*") || (c === "["));
}

function IsSimpleParamOp(c) {
    return ((c === "-") || (c === "=") || (c === "?") || (c === "+"));
}

function IsEscapeCharInDquote(c) {
    return ((c === "$") || (c === "`") || (c === "\\"));
}

function IsListTerminator(c) {
    return ((c === "\n") || (c === "|") || (c === ";") || (c === "(") || (c === ")"));
}

function IsSemicolonOrAmp(c) {
    return ((c === ";") || (c === "&"));
}

function IsParen(c) {
    return ((c === "(") || (c === ")"));
}

function IsCaretOrBang(c) {
    return ((c === "!") || (c === "^"));
}

function IsAtOrStar(c) {
    return ((c === "@") || (c === "*"));
}

function IsDigitOrDash(c) {
    return (IsDigit(c) || (c === "-"));
}

function IsNewlineOrRightParen(c) {
    return ((c === "\n") || (c === ")"));
}

function IsNewlineOrRightBracket(c) {
    return ((c === "\n") || (c === ")") || (c === "}"));
}

function IsSemicolonNewlineBrace(c) {
    return ((c === ";") || (c === "\n") || (c === "{"));
}

function IsReservedWord(word) {
    return RESERVED_WORDS.has(word);
}

function IsCompoundKeyword(word) {
    return COMPOUND_KEYWORDS.has(word);
}

function IsCondUnaryOp(op) {
    return COND_UNARY_OPS.has(op);
}

function IsCondBinaryOp(op) {
    return COND_BINARY_OPS.has(op);
}

function StrContains(haystack, needle) {
    return (haystack.indexOf(needle) !== -1);
}

class Parser {
    constructor(source) {
        this.source = source;
        this.pos = 0;
        this.length = source.length;
        this._pending_heredoc_end = null;
    }
    
    atEnd() {
        return (this.pos >= this.length);
    }
    
    peek() {
        if (this.atEnd()) {
            return null;
        }
        return this.source[this.pos];
    }
    
    advance() {
        if (this.atEnd()) {
            return null;
        }
        var ch = this.source[this.pos];
        this.pos += 1;
        return ch;
    }
    
    skipWhitespace() {
        while (!this.atEnd()) {
            var ch = this.peek();
            if (IsWhitespaceNoNewline(ch)) {
                this.advance();
            } else if ((ch === "#")) {
                // Skip comment to end of line (but not the newline itself)
                while ((!this.atEnd() && (this.peek() !== "\n"))) {
                    this.advance();
                }
            } else if (((ch === "\\") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "\n"))) {
                // Backslash-newline is line continuation - skip both
                this.advance();
                this.advance();
            } else {
                break;
            }
        }
    }
    
    skipWhitespaceAndNewlines() {
        while (!this.atEnd()) {
            var ch = this.peek();
            if (IsWhitespace(ch)) {
                this.advance();
                // After advancing past a newline, skip any pending heredoc content
                if ((ch === "\n")) {
                    if (((this._pending_heredoc_end != null) && (this._pending_heredoc_end > this.pos))) {
                        this.pos = this._pending_heredoc_end;
                        this._pending_heredoc_end = null;
                    }
                }
            } else if ((ch === "#")) {
                // Skip comment to end of line
                while ((!this.atEnd() && (this.peek() !== "\n"))) {
                    this.advance();
                }
            } else if (((ch === "\\") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "\n"))) {
                // Backslash-newline is line continuation - skip both
                this.advance();
                this.advance();
            } else {
                break;
            }
        }
    }
    
    peekWord() {
        var saved_pos = this.pos;
        this.skipWhitespace();
        if ((this.atEnd() || IsMetachar(this.peek()))) {
            this.pos = saved_pos;
            return null;
        }
        var chars = [];
        while ((!this.atEnd() && !IsMetachar(this.peek()))) {
            var ch = this.peek();
            // Stop at quotes - don't include in peek
            if (IsQuote(ch)) {
                break;
            }
            chars.push(this.advance());
        }
        if (chars) {
            var word = chars.join("");
        } else {
            word = null;
        }
        this.pos = saved_pos;
        return word;
    }
    
    consumeWord(expected) {
        var saved_pos = this.pos;
        this.skipWhitespace();
        var word = this.peekWord();
        if ((word !== expected)) {
            this.pos = saved_pos;
            return false;
        }
        // Actually consume the word
        this.skipWhitespace();
        for (let _ of expected) {
            this.advance();
        }
        return true;
    }
    
    parseWord(at_command_start) {
        if (at_command_start == null) { at_command_start = false; }
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        var start = this.pos;
        var chars = [];
        var parts = [];
        var bracket_depth = 0;
        var seen_equals = false;
        while (!this.atEnd()) {
            var ch = this.peek();
            // Track bracket depth for array subscripts like a[1+2]=3
            // Inside brackets, metacharacters like | and ( are literal
            // Only track [ after we've seen some chars (so [ -f file ] still works)
            // Only at command start (array assignments), not in argument position
            // Only BEFORE = sign (key=1],a[1 should not track the [1 part)
            // Only after identifier char (not [[ which is conditional keyword)
            if (((ch === "[") && chars && at_command_start && !seen_equals)) {
                var prev_char = chars[(chars.length - 1)];
                if ((/^[a-zA-Z0-9]$/.test(prev_char) || ((prev_char === "_") || (prev_char === "]")))) {
                    bracket_depth += 1;
                    chars.push(this.advance());
                    continue;
                }
            }
            if (((ch === "]") && (bracket_depth > 0))) {
                bracket_depth -= 1;
                chars.push(this.advance());
                continue;
            }
            if (((ch === "=") && (bracket_depth === 0))) {
                seen_equals = true;
            }
            // Single-quoted string - no expansion
            if ((ch === "'")) {
                this.advance();
                chars.push("'");
                while ((!this.atEnd() && (this.peek() !== "'"))) {
                    chars.push(this.advance());
                }
                if (this.atEnd()) {
                    throw new ParseError("Unterminated single quote", start);
                }
                chars.push(this.advance());
            } else if ((ch === "\"")) {
                // Double-quoted string - expansions happen inside
                this.advance();
                chars.push("\"");
                while ((!this.atEnd() && (this.peek() !== "\""))) {
                    var c = this.peek();
                    // Handle escape sequences in double quotes
                    if (((c === "\\") && ((this.pos + 1) < this.length))) {
                        var next_c = this.source[(this.pos + 1)];
                        if ((next_c === "\n")) {
                            // Line continuation - skip both backslash and newline
                            this.advance();
                            this.advance();
                        } else {
                            chars.push(this.advance());
                            chars.push(this.advance());
                        }
                    } else if (((c === "$") && ((this.pos + 2) < this.length) && (this.source[(this.pos + 1)] === "(") && (this.source[(this.pos + 2)] === "("))) {
                        // Handle arithmetic expansion $((...))
                        var arith_result = this.ParseArithmeticExpansion();
                        var arith_node = arith_result[0];
                        var arith_text = arith_result[1];
                        if (arith_node) {
                            parts.push(arith_node);
                            chars.push(arith_text);
                        } else {
                            // Not arithmetic - try command substitution
                            var cmdsub_result = this.ParseCommandSubstitution();
                            var cmdsub_node = cmdsub_result[0];
                            var cmdsub_text = cmdsub_result[1];
                            if (cmdsub_node) {
                                parts.push(cmdsub_node);
                                chars.push(cmdsub_text);
                            } else {
                                chars.push(this.advance());
                            }
                        }
                    } else if (((c === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "["))) {
                        // Handle deprecated arithmetic expansion $[expr]
                        arith_result = this.ParseDeprecatedArithmetic();
                        arith_node = arith_result[0];
                        arith_text = arith_result[1];
                        if (arith_node) {
                            parts.push(arith_node);
                            chars.push(arith_text);
                        } else {
                            chars.push(this.advance());
                        }
                    } else if (((c === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                        // Handle command substitution $(...)
                        cmdsub_result = this.ParseCommandSubstitution();
                        cmdsub_node = cmdsub_result[0];
                        cmdsub_text = cmdsub_result[1];
                        if (cmdsub_node) {
                            parts.push(cmdsub_node);
                            chars.push(cmdsub_text);
                        } else {
                            chars.push(this.advance());
                        }
                    } else if ((c === "$")) {
                        // Handle parameter expansion inside double quotes
                        var param_result = this.ParseParamExpansion();
                        var param_node = param_result[0];
                        var param_text = param_result[1];
                        if (param_node) {
                            parts.push(param_node);
                            chars.push(param_text);
                        } else {
                            chars.push(this.advance());
                        }
                    } else if ((c === "`")) {
                        // Handle backtick command substitution
                        cmdsub_result = this.ParseBacktickSubstitution();
                        cmdsub_node = cmdsub_result[0];
                        cmdsub_text = cmdsub_result[1];
                        if (cmdsub_node) {
                            parts.push(cmdsub_node);
                            chars.push(cmdsub_text);
                        } else {
                            chars.push(this.advance());
                        }
                    } else {
                        chars.push(this.advance());
                    }
                }
                if (this.atEnd()) {
                    throw new ParseError("Unterminated double quote", start);
                }
                chars.push(this.advance());
            } else if (((ch === "\\") && ((this.pos + 1) < this.length))) {
                // Escape outside quotes
                var next_ch = this.source[(this.pos + 1)];
                if ((next_ch === "\n")) {
                    // Line continuation - skip both backslash and newline
                    this.advance();
                    this.advance();
                } else {
                    chars.push(this.advance());
                    chars.push(this.advance());
                }
            } else if (((ch === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "'"))) {
                // ANSI-C quoting $'...'
                var ansi_result = this.ParseAnsiCQuote();
                var ansi_node = ansi_result[0];
                var ansi_text = ansi_result[1];
                if (ansi_node) {
                    parts.push(ansi_node);
                    chars.push(ansi_text);
                } else {
                    chars.push(this.advance());
                }
            } else if (((ch === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "\""))) {
                // Locale translation $"..."
                var locale_result = this.ParseLocaleString();
                var locale_node = locale_result[0];
                var locale_text = locale_result[1];
                var inner_parts = locale_result[2];
                if (locale_node) {
                    parts.push(locale_node);
                    parts.push(...inner_parts);
                    chars.push(locale_text);
                } else {
                    chars.push(this.advance());
                }
            } else if (((ch === "$") && ((this.pos + 2) < this.length) && (this.source[(this.pos + 1)] === "(") && (this.source[(this.pos + 2)] === "("))) {
                // Arithmetic expansion $((...)) - try before command substitution
                // If it fails (returns None), fall through to command substitution
                arith_result = this.ParseArithmeticExpansion();
                arith_node = arith_result[0];
                arith_text = arith_result[1];
                if (arith_node) {
                    parts.push(arith_node);
                    chars.push(arith_text);
                } else {
                    // Not arithmetic (e.g., '$( ( ... ) )' is command sub + subshell)
                    cmdsub_result = this.ParseCommandSubstitution();
                    cmdsub_node = cmdsub_result[0];
                    cmdsub_text = cmdsub_result[1];
                    if (cmdsub_node) {
                        parts.push(cmdsub_node);
                        chars.push(cmdsub_text);
                    } else {
                        chars.push(this.advance());
                    }
                }
            } else if (((ch === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "["))) {
                // Deprecated arithmetic expansion $[expr]
                arith_result = this.ParseDeprecatedArithmetic();
                arith_node = arith_result[0];
                arith_text = arith_result[1];
                if (arith_node) {
                    parts.push(arith_node);
                    chars.push(arith_text);
                } else {
                    chars.push(this.advance());
                }
            } else if (((ch === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                // Command substitution $(...)
                cmdsub_result = this.ParseCommandSubstitution();
                cmdsub_node = cmdsub_result[0];
                cmdsub_text = cmdsub_result[1];
                if (cmdsub_node) {
                    parts.push(cmdsub_node);
                    chars.push(cmdsub_text);
                } else {
                    chars.push(this.advance());
                }
            } else if ((ch === "$")) {
                // Parameter expansion $var or ${...}
                param_result = this.ParseParamExpansion();
                param_node = param_result[0];
                param_text = param_result[1];
                if (param_node) {
                    parts.push(param_node);
                    chars.push(param_text);
                } else {
                    chars.push(this.advance());
                }
            } else if ((ch === "`")) {
                // Backtick command substitution
                cmdsub_result = this.ParseBacktickSubstitution();
                cmdsub_node = cmdsub_result[0];
                cmdsub_text = cmdsub_result[1];
                if (cmdsub_node) {
                    parts.push(cmdsub_node);
                    chars.push(cmdsub_text);
                } else {
                    chars.push(this.advance());
                }
            } else if ((IsRedirectChar(ch) && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                // Process substitution <(...) or >(...)
                var procsub_result = this.ParseProcessSubstitution();
                var procsub_node = procsub_result[0];
                var procsub_text = procsub_result[1];
                if (procsub_node) {
                    parts.push(procsub_node);
                    chars.push(procsub_text);
                } else {
                    // Not a process substitution, treat as metacharacter
                    break;
                }
            } else if (((ch === "(") && chars && ((chars[(chars.length - 1)] === "=") || ((chars.length >= 2) && (chars[(chars.length - 2)] === "+") && (chars[(chars.length - 1)] === "="))))) {
                // Array literal: name=(elements) or name+=(elements)
                var array_result = this.ParseArrayLiteral();
                var array_node = array_result[0];
                var array_text = array_result[1];
                if (array_node) {
                    parts.push(array_node);
                    chars.push(array_text);
                } else {
                    // Unexpected: ( without matching )
                    break;
                }
            } else if ((IsExtglobPrefix(ch) && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                // Extglob pattern @(), ?(), *(), +(), !()
                chars.push(this.advance());
                chars.push(this.advance());
                var extglob_depth = 1;
                while ((!this.atEnd() && (extglob_depth > 0))) {
                    c = this.peek();
                    if ((c === ")")) {
                        chars.push(this.advance());
                        extglob_depth -= 1;
                    } else if ((c === "(")) {
                        chars.push(this.advance());
                        extglob_depth += 1;
                    } else if ((c === "\\")) {
                        chars.push(this.advance());
                        if (!this.atEnd()) {
                            chars.push(this.advance());
                        }
                    } else if ((c === "'")) {
                        chars.push(this.advance());
                        while ((!this.atEnd() && (this.peek() !== "'"))) {
                            chars.push(this.advance());
                        }
                        if (!this.atEnd()) {
                            chars.push(this.advance());
                        }
                    } else if ((c === "\"")) {
                        chars.push(this.advance());
                        while ((!this.atEnd() && (this.peek() !== "\""))) {
                            if (((this.peek() === "\\") && ((this.pos + 1) < this.length))) {
                                chars.push(this.advance());
                            }
                            chars.push(this.advance());
                        }
                        if (!this.atEnd()) {
                            chars.push(this.advance());
                        }
                    } else if (((c === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                        // $() or $(()) inside extglob
                        chars.push(this.advance());
                        chars.push(this.advance());
                        if ((!this.atEnd() && (this.peek() === "("))) {
                            // $(()) arithmetic
                            chars.push(this.advance());
                            var paren_depth = 2;
                            while ((!this.atEnd() && (paren_depth > 0))) {
                                var pc = this.peek();
                                if ((pc === "(")) {
                                    paren_depth += 1;
                                } else if ((pc === ")")) {
                                    paren_depth -= 1;
                                }
                                chars.push(this.advance());
                            }
                        } else {
                            // $() command sub - count as nested paren
                            extglob_depth += 1;
                        }
                    } else if ((IsExtglobPrefix(c) && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                        // Nested extglob
                        chars.push(this.advance());
                        chars.push(this.advance());
                        extglob_depth += 1;
                    } else {
                        chars.push(this.advance());
                    }
                }
            } else if ((IsMetachar(ch) && (bracket_depth === 0))) {
                // Metacharacter ends the word (unless inside brackets like a[x|y]=1)
                break;
            } else {
                // Regular character (including metacharacters inside brackets)
                chars.push(this.advance());
            }
        }
        if (chars.length === 0) {
            return null;
        }
        if (parts) {
            return new Word(chars.join(""), parts);
        } else {
            return new Word(chars.join(""), null);
        }
    }
    
    ParseCommandSubstitution() {
        if ((this.atEnd() || (this.peek() !== "$"))) {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        if ((this.atEnd() || (this.peek() !== "("))) {
            this.pos = start;
            return [null, ""];
        }
        this.advance();
        // Find matching closing paren, being aware of:
        // - Nested $() and plain ()
        // - Quoted strings
        // - case statements (where ) after pattern isn't a closer)
        var content_start = this.pos;
        var depth = 1;
        var case_depth = 0;
        while ((!this.atEnd() && (depth > 0))) {
            var c = this.peek();
            // Single-quoted string - no special chars inside
            if ((c === "'")) {
                this.advance();
                while ((!this.atEnd() && (this.peek() !== "'"))) {
                    this.advance();
                }
                if (!this.atEnd()) {
                    this.advance();
                }
                continue;
            }
            // Double-quoted string - handle escapes and nested $()
            if ((c === "\"")) {
                this.advance();
                while ((!this.atEnd() && (this.peek() !== "\""))) {
                    if (((this.peek() === "\\") && ((this.pos + 1) < this.length))) {
                        this.advance();
                        this.advance();
                    } else if (((this.peek() === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                        // Nested $() in double quotes - recurse to find matching )
                        // Command substitution creates new quoting context
                        this.advance();
                        this.advance();
                        var nested_depth = 1;
                        while ((!this.atEnd() && (nested_depth > 0))) {
                            var nc = this.peek();
                            if ((nc === "'")) {
                                this.advance();
                                while ((!this.atEnd() && (this.peek() !== "'"))) {
                                    this.advance();
                                }
                                if (!this.atEnd()) {
                                    this.advance();
                                }
                            } else if ((nc === "\"")) {
                                this.advance();
                                while ((!this.atEnd() && (this.peek() !== "\""))) {
                                    if (((this.peek() === "\\") && ((this.pos + 1) < this.length))) {
                                        this.advance();
                                    }
                                    this.advance();
                                }
                                if (!this.atEnd()) {
                                    this.advance();
                                }
                            } else if (((nc === "\\") && ((this.pos + 1) < this.length))) {
                                this.advance();
                                this.advance();
                            } else if (((nc === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                                this.advance();
                                this.advance();
                                nested_depth += 1;
                            } else if ((nc === "(")) {
                                nested_depth += 1;
                                this.advance();
                            } else if ((nc === ")")) {
                                nested_depth -= 1;
                                if ((nested_depth > 0)) {
                                    this.advance();
                                }
                            } else {
                                this.advance();
                            }
                        }
                        if ((nested_depth === 0)) {
                            this.advance();
                        }
                    } else {
                        this.advance();
                    }
                }
                if (!this.atEnd()) {
                    this.advance();
                }
                continue;
            }
            // Backslash escape
            if (((c === "\\") && ((this.pos + 1) < this.length))) {
                this.advance();
                this.advance();
                continue;
            }
            // Comment - skip until newline
            if (((c === "#") && this.IsWordBoundaryBefore())) {
                while ((!this.atEnd() && (this.peek() !== "\n"))) {
                    this.advance();
                }
                continue;
            }
            // Heredoc - skip until delimiter line is found
            if (((c === "<") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "<"))) {
                this.advance();
                this.advance();
                // Check for <<- (strip tabs)
                if ((!this.atEnd() && (this.peek() === "-"))) {
                    this.advance();
                }
                // Skip whitespace before delimiter
                while ((!this.atEnd() && IsWhitespaceNoNewline(this.peek()))) {
                    this.advance();
                }
                // Parse delimiter (handle quoting)
                var delimiter_chars = [];
                if (!this.atEnd()) {
                    var ch = this.peek();
                    if (IsQuote(ch)) {
                        var quote = this.advance();
                        while ((!this.atEnd() && (this.peek() !== quote))) {
                            delimiter_chars.push(this.advance());
                        }
                        if (!this.atEnd()) {
                            this.advance();
                        }
                    } else if ((ch === "\\")) {
                        this.advance();
                        // Backslash quotes - first char can be special, then read word
                        if (!this.atEnd()) {
                            delimiter_chars.push(this.advance());
                        }
                        while ((!this.atEnd() && !IsMetachar(this.peek()))) {
                            delimiter_chars.push(this.advance());
                        }
                    } else {
                        // Unquoted delimiter with possible embedded quotes
                        while ((!this.atEnd() && !IsMetachar(this.peek()))) {
                            ch = this.peek();
                            if (IsQuote(ch)) {
                                quote = this.advance();
                                while ((!this.atEnd() && (this.peek() !== quote))) {
                                    delimiter_chars.push(this.advance());
                                }
                                if (!this.atEnd()) {
                                    this.advance();
                                }
                            } else if ((ch === "\\")) {
                                this.advance();
                                if (!this.atEnd()) {
                                    delimiter_chars.push(this.advance());
                                }
                            } else {
                                delimiter_chars.push(this.advance());
                            }
                        }
                    }
                }
                var delimiter = delimiter_chars.join("");
                if (delimiter) {
                    // Skip to end of current line
                    while ((!this.atEnd() && (this.peek() !== "\n"))) {
                        this.advance();
                    }
                    // Skip newline
                    if ((!this.atEnd() && (this.peek() === "\n"))) {
                        this.advance();
                    }
                    // Skip lines until we find the delimiter
                    while (!this.atEnd()) {
                        var line_start = this.pos;
                        var line_end = this.pos;
                        while (((line_end < this.length) && (this.source[line_end] !== "\n"))) {
                            line_end += 1;
                        }
                        var line = this.source.slice(line_start, line_end);
                        // Move position to end of line
                        this.pos = line_end;
                        // Check if this line matches delimiter
                        if (((line === delimiter) || (line.replace(/^[\t]+/, "") === delimiter))) {
                            // Skip newline after delimiter
                            if ((!this.atEnd() && (this.peek() === "\n"))) {
                                this.advance();
                            }
                            break;
                        }
                        // Skip newline and continue
                        if ((!this.atEnd() && (this.peek() === "\n"))) {
                            this.advance();
                        }
                    }
                }
                continue;
            }
            // Track case/esac for pattern terminator handling
            // Check for 'case' keyword (word boundary: preceded by space/newline/start)
            if (((c === "c") && this.IsWordBoundaryBefore())) {
                if (this.LookaheadKeyword("case")) {
                    case_depth += 1;
                    this.SkipKeyword("case");
                    continue;
                }
            }
            // Check for 'esac' keyword
            if (((c === "e") && this.IsWordBoundaryBefore() && (case_depth > 0))) {
                if (this.LookaheadKeyword("esac")) {
                    case_depth -= 1;
                    this.SkipKeyword("esac");
                    continue;
                }
            }
            // Handle parentheses
            if ((c === "(")) {
                depth += 1;
            } else if ((c === ")")) {
                // In case statement, ) after pattern is a terminator, not a paren
                // Only decrement depth if we're not in a case pattern position
                if (((case_depth > 0) && (depth === 1))) {
                    // This ) might be a case pattern terminator, not closing the $(
                    // Look ahead to see if there's still content that needs esac
                    var saved = this.pos;
                    this.advance();
                    // Scan ahead to see if we find esac that closes our case
                    // before finding a ) that could close our $(
                    var temp_depth = 0;
                    var temp_case_depth = case_depth;
                    var found_esac = false;
                    while (!this.atEnd()) {
                        var tc = this.peek();
                        if (((tc === "'") || (tc === "\""))) {
                            // Skip quoted strings
                            var q = tc;
                            this.advance();
                            while ((!this.atEnd() && (this.peek() !== q))) {
                                if (((q === "\"") && (this.peek() === "\\"))) {
                                    this.advance();
                                }
                                this.advance();
                            }
                            if (!this.atEnd()) {
                                this.advance();
                            }
                        } else if (((tc === "c") && this.IsWordBoundaryBefore() && this.LookaheadKeyword("case"))) {
                            // Nested case in lookahead
                            temp_case_depth += 1;
                            this.SkipKeyword("case");
                        } else if (((tc === "e") && this.IsWordBoundaryBefore() && this.LookaheadKeyword("esac"))) {
                            temp_case_depth -= 1;
                            if ((temp_case_depth === 0)) {
                                // All cases are closed
                                found_esac = true;
                                break;
                            }
                            this.SkipKeyword("esac");
                        } else if ((tc === "(")) {
                            temp_depth += 1;
                            this.advance();
                        } else if ((tc === ")")) {
                            // In case, ) is a pattern terminator, not a closer
                            if ((temp_case_depth > 0)) {
                                this.advance();
                            } else if ((temp_depth > 0)) {
                                temp_depth -= 1;
                                this.advance();
                            } else {
                                // Found a ) that could be our closer
                                break;
                            }
                        } else {
                            this.advance();
                        }
                    }
                    this.pos = saved;
                    if (found_esac) {
                        // This ) is a case pattern terminator, not our closer
                        this.advance();
                        continue;
                    }
                }
                depth -= 1;
            }
            if ((depth > 0)) {
                this.advance();
            }
        }
        if ((depth !== 0)) {
            this.pos = start;
            return [null, ""];
        }
        var content = this.source.slice(content_start, this.pos);
        this.advance();
        var text = this.source.slice(start, this.pos);
        // Parse the content as a command list
        var sub_parser = new Parser(content);
        var cmd = sub_parser.parseList();
        if ((cmd == null)) {
            cmd = new Empty();
        }
        return [new CommandSubstitution(cmd), text];
    }
    
    IsWordBoundaryBefore() {
        if ((this.pos === 0)) {
            return true;
        }
        var prev = this.source[(this.pos - 1)];
        return IsWordStartContext(prev);
    }
    
    IsAssignmentWord(word) {
        var in_single = false;
        var in_double = false;
        var i = 0;
        while ((i < word.value.length)) {
            var ch = word.value[i];
            if (((ch === "'") && !in_double)) {
                in_single = !in_single;
            } else if (((ch === "\"") && !in_single)) {
                in_double = !in_double;
            } else if (((ch === "\\") && !in_single && ((i + 1) < word.value.length))) {
                i += 1;
                continue;
            } else if (((ch === "=") && !in_single && !in_double)) {
                return true;
            }
            i += 1;
        }
        return false;
    }
    
    LookaheadKeyword(keyword) {
        if (((this.pos + keyword.length) > this.length)) {
            return false;
        }
        if (!StartsWithAt(this.source, this.pos, keyword)) {
            return false;
        }
        // Check word boundary after keyword
        var after_pos = (this.pos + keyword.length);
        if ((after_pos >= this.length)) {
            return true;
        }
        var after = this.source[after_pos];
        return IsWordEndContext(after);
    }
    
    SkipKeyword(keyword) {
        for (let _ of keyword) {
            this.advance();
        }
    }
    
    ParseBacktickSubstitution() {
        if ((this.atEnd() || (this.peek() !== "`"))) {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        // Find closing backtick, processing escape sequences as we go.
        // In backticks, backslash is special only before $, `, \, or newline.
        // \$ -> $, \` -> `, \\ -> \, \<newline> -> removed (line continuation)
        // other \X -> \X (backslash is literal)
        // content_chars: what gets parsed as the inner command
        // text_chars: what appears in the word representation (with line continuations removed)
        var content_chars = [];
        var text_chars = ["`"];
        while ((!this.atEnd() && (this.peek() !== "`"))) {
            var c = this.peek();
            if (((c === "\\") && ((this.pos + 1) < this.length))) {
                var next_c = this.source[(this.pos + 1)];
                if ((next_c === "\n")) {
                    // Line continuation: skip both backslash and newline
                    this.advance();
                    this.advance();
                } else if (IsEscapeCharInDquote(next_c)) {
                    // Don't add to content_chars or text_chars
                    // Escape sequence: skip backslash in content, keep both in text
                    this.advance();
                    var escaped = this.advance();
                    content_chars.push(escaped);
                    text_chars.push("\\");
                    text_chars.push(escaped);
                } else {
                    // Backslash is literal before other characters
                    var ch = this.advance();
                    content_chars.push(ch);
                    text_chars.push(ch);
                }
            } else {
                ch = this.advance();
                content_chars.push(ch);
                text_chars.push(ch);
            }
        }
        if (this.atEnd()) {
            this.pos = start;
            return [null, ""];
        }
        this.advance();
        text_chars.push("`");
        var text = text_chars.join("");
        var content = content_chars.join("");
        // Parse the content as a command list
        var sub_parser = new Parser(content);
        var cmd = sub_parser.parseList();
        if ((cmd == null)) {
            cmd = new Empty();
        }
        return [new CommandSubstitution(cmd), text];
    }
    
    ParseProcessSubstitution() {
        if ((this.atEnd() || !IsRedirectChar(this.peek()))) {
            return [null, ""];
        }
        var start = this.pos;
        var direction = this.advance();
        if ((this.atEnd() || (this.peek() !== "("))) {
            this.pos = start;
            return [null, ""];
        }
        this.advance();
        // Find matching ) - track nested parens and handle quotes
        var content_start = this.pos;
        var depth = 1;
        while ((!this.atEnd() && (depth > 0))) {
            var c = this.peek();
            // Single-quoted string
            if ((c === "'")) {
                this.advance();
                while ((!this.atEnd() && (this.peek() !== "'"))) {
                    this.advance();
                }
                if (!this.atEnd()) {
                    this.advance();
                }
                continue;
            }
            // Double-quoted string
            if ((c === "\"")) {
                this.advance();
                while ((!this.atEnd() && (this.peek() !== "\""))) {
                    if (((this.peek() === "\\") && ((this.pos + 1) < this.length))) {
                        this.advance();
                    }
                    this.advance();
                }
                if (!this.atEnd()) {
                    this.advance();
                }
                continue;
            }
            // Backslash escape
            if (((c === "\\") && ((this.pos + 1) < this.length))) {
                this.advance();
                this.advance();
                continue;
            }
            // Nested parentheses (including nested process substitutions)
            if ((c === "(")) {
                depth += 1;
            } else if ((c === ")")) {
                depth -= 1;
                if ((depth === 0)) {
                    break;
                }
            }
            this.advance();
        }
        if ((depth !== 0)) {
            this.pos = start;
            return [null, ""];
        }
        var content = this.source.slice(content_start, this.pos);
        this.advance();
        var text = this.source.slice(start, this.pos);
        // Parse the content as a command list
        var sub_parser = new Parser(content);
        var cmd = sub_parser.parseList();
        if ((cmd == null)) {
            cmd = new Empty();
        }
        return [new ProcessSubstitution(direction, cmd), text];
    }
    
    ParseArrayLiteral() {
        if ((this.atEnd() || (this.peek() !== "("))) {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        var elements = [];
        while (true) {
            // Skip whitespace and newlines between elements
            while ((!this.atEnd() && IsWhitespace(this.peek()))) {
                this.advance();
            }
            if (this.atEnd()) {
                throw new ParseError("Unterminated array literal", start);
            }
            if ((this.peek() === ")")) {
                break;
            }
            // Parse an element word
            var word = this.parseWord();
            if ((word == null)) {
                // Might be a closing paren or error
                if ((this.peek() === ")")) {
                    break;
                }
                throw new ParseError("Expected word in array literal", this.pos);
            }
            elements.push(word);
        }
        if ((this.atEnd() || (this.peek() !== ")"))) {
            throw new ParseError("Expected ) to close array literal", this.pos);
        }
        this.advance();
        var text = this.source.slice(start, this.pos);
        return [new ArrayNode(elements), text];
    }
    
    ParseArithmeticExpansion() {
        if ((this.atEnd() || (this.peek() !== "$"))) {
            return [null, ""];
        }
        var start = this.pos;
        // Check for $((
        if ((((this.pos + 2) >= this.length) || (this.source[(this.pos + 1)] !== "(") || (this.source[(this.pos + 2)] !== "("))) {
            return [null, ""];
        }
        this.advance();
        this.advance();
        this.advance();
        // Find matching )) - need to track nested parens
        // Must be )) with no space between - ') )' is command sub + subshell
        var content_start = this.pos;
        var depth = 1;
        while ((!this.atEnd() && (depth > 0))) {
            var c = this.peek();
            if ((c === "(")) {
                depth += 1;
                this.advance();
            } else if ((c === ")")) {
                // Check for ))
                if (((depth === 1) && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === ")"))) {
                    // Found the closing ))
                    break;
                }
                depth -= 1;
                if ((depth === 0)) {
                    // Closed with ) but next isn't ) - this is $( ( ... ) )
                    this.pos = start;
                    return [null, ""];
                }
                this.advance();
            } else {
                this.advance();
            }
        }
        if ((this.atEnd() || (depth !== 1))) {
            this.pos = start;
            return [null, ""];
        }
        var content = this.source.slice(content_start, this.pos);
        this.advance();
        this.advance();
        var text = this.source.slice(start, this.pos);
        // Parse the arithmetic expression
        var expr = this.ParseArithExpr(content);
        return [new ArithmeticExpansion(expr), text];
    }
    
    // ========== Arithmetic expression parser ==========
    // Operator precedence (lowest to highest):
    // 1. comma (,)
    // 2. assignment (= += -= *= /= %= <<= >>= &= ^= |=)
    // 3. ternary (? :)
    // 4. logical or (||)
    // 5. logical and (&&)
    // 6. bitwise or (|)
    // 7. bitwise xor (^)
    // 8. bitwise and (&)
    // 9. equality (== !=)
    // 10. comparison (< > <= >=)
    // 11. shift (<< >>)
    // 12. addition (+ -)
    // 13. multiplication (* / %)
    // 14. exponentiation (**)
    // 15. unary (! ~ + - ++ --)
    // 16. postfix (++ -- [])
    ParseArithExpr(content) {
        // Save any existing arith context (for nested parsing)
        var saved_arith_src = (this._arith_src ?? null);
        var saved_arith_pos = (this._arith_pos ?? null);
        var saved_arith_len = (this._arith_len ?? null);
        this._arith_src = content;
        this._arith_pos = 0;
        this._arith_len = content.length;
        this.ArithSkipWs();
        if (this.ArithAtEnd()) {
            var result = null;
        } else {
            result = this.ArithParseComma();
        }
        // Restore previous arith context
        if ((saved_arith_src != null)) {
            this._arith_src = saved_arith_src;
            this._arith_pos = saved_arith_pos;
            this._arith_len = saved_arith_len;
        }
        return result;
    }
    
    ArithAtEnd() {
        return (this._arith_pos >= this._arith_len);
    }
    
    ArithPeek(offset) {
        if (offset == null) { offset = 0; }
        var pos = (this._arith_pos + offset);
        if ((pos >= this._arith_len)) {
            return "";
        }
        return this._arith_src[pos];
    }
    
    ArithAdvance() {
        if (this.ArithAtEnd()) {
            return "";
        }
        var c = this._arith_src[this._arith_pos];
        this._arith_pos += 1;
        return c;
    }
    
    ArithSkipWs() {
        while (!this.ArithAtEnd()) {
            var c = this._arith_src[this._arith_pos];
            if (IsWhitespace(c)) {
                this._arith_pos += 1;
            } else if (((c === "\\") && ((this._arith_pos + 1) < this._arith_len) && (this._arith_src[(this._arith_pos + 1)] === "\n"))) {
                // Backslash-newline continuation
                this._arith_pos += 2;
            } else {
                break;
            }
        }
    }
    
    ArithMatch(s) {
        return StartsWithAt(this._arith_src, this._arith_pos, s);
    }
    
    ArithConsume(s) {
        if (this.ArithMatch(s)) {
            this._arith_pos += s.length;
            return true;
        }
        return false;
    }
    
    ArithParseComma() {
        var left = this.ArithParseAssign();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithConsume(",")) {
                this.ArithSkipWs();
                var right = this.ArithParseAssign();
                left = new ArithComma(left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseAssign() {
        var left = this.ArithParseTernary();
        this.ArithSkipWs();
        // Check for assignment operators
        var assign_ops = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="];
        for (let op of assign_ops) {
            if (this.ArithMatch(op)) {
                // Make sure it's not == or !=
                if (((op === "=") && (this.ArithPeek(1) === "="))) {
                    break;
                }
                this.ArithConsume(op);
                this.ArithSkipWs();
                var right = this.ArithParseAssign();
                return new ArithAssign(op, left, right);
            }
        }
        return left;
    }
    
    ArithParseTernary() {
        var cond = this.ArithParseLogicalOr();
        this.ArithSkipWs();
        if (this.ArithConsume("?")) {
            this.ArithSkipWs();
            // True branch can be empty (e.g., 4 ? : $A - invalid at runtime, valid syntax)
            if (this.ArithMatch(":")) {
                var if_true = null;
            } else {
                if_true = this.ArithParseAssign();
            }
            this.ArithSkipWs();
            // Check for : (may be missing in malformed expressions like 1 ? 20)
            if (this.ArithConsume(":")) {
                this.ArithSkipWs();
                // False branch can be empty (e.g., 4 ? 20 : - invalid at runtime)
                if ((this.ArithAtEnd() || (this.ArithPeek() === ")"))) {
                    var if_false = null;
                } else {
                    if_false = this.ArithParseTernary();
                }
            } else {
                if_false = null;
            }
            return new ArithTernary(cond, if_true, if_false);
        }
        return cond;
    }
    
    ArithParseLogicalOr() {
        var left = this.ArithParseLogicalAnd();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithMatch("||")) {
                this.ArithConsume("||");
                this.ArithSkipWs();
                var right = this.ArithParseLogicalAnd();
                left = new ArithBinaryOp("||", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseLogicalAnd() {
        var left = this.ArithParseBitwiseOr();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithMatch("&&")) {
                this.ArithConsume("&&");
                this.ArithSkipWs();
                var right = this.ArithParseBitwiseOr();
                left = new ArithBinaryOp("&&", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseBitwiseOr() {
        var left = this.ArithParseBitwiseXor();
        while (true) {
            this.ArithSkipWs();
            // Make sure it's not || or |=
            if (((this.ArithPeek() === "|") && ((this.ArithPeek(1) !== "|") && (this.ArithPeek(1) !== "=")))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseBitwiseXor();
                left = new ArithBinaryOp("|", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseBitwiseXor() {
        var left = this.ArithParseBitwiseAnd();
        while (true) {
            this.ArithSkipWs();
            // Make sure it's not ^=
            if (((this.ArithPeek() === "^") && (this.ArithPeek(1) !== "="))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseBitwiseAnd();
                left = new ArithBinaryOp("^", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseBitwiseAnd() {
        var left = this.ArithParseEquality();
        while (true) {
            this.ArithSkipWs();
            // Make sure it's not && or &=
            if (((this.ArithPeek() === "&") && ((this.ArithPeek(1) !== "&") && (this.ArithPeek(1) !== "=")))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseEquality();
                left = new ArithBinaryOp("&", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseEquality() {
        var left = this.ArithParseComparison();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithMatch("==")) {
                this.ArithConsume("==");
                this.ArithSkipWs();
                var right = this.ArithParseComparison();
                left = new ArithBinaryOp("==", left, right);
            } else if (this.ArithMatch("!=")) {
                this.ArithConsume("!=");
                this.ArithSkipWs();
                right = this.ArithParseComparison();
                left = new ArithBinaryOp("!=", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseComparison() {
        var left = this.ArithParseShift();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithMatch("<=")) {
                this.ArithConsume("<=");
                this.ArithSkipWs();
                var right = this.ArithParseShift();
                left = new ArithBinaryOp("<=", left, right);
            } else if (this.ArithMatch(">=")) {
                this.ArithConsume(">=");
                this.ArithSkipWs();
                right = this.ArithParseShift();
                left = new ArithBinaryOp(">=", left, right);
            } else if (((this.ArithPeek() === "<") && ((this.ArithPeek(1) !== "<") && (this.ArithPeek(1) !== "=")))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                right = this.ArithParseShift();
                left = new ArithBinaryOp("<", left, right);
            } else if (((this.ArithPeek() === ">") && ((this.ArithPeek(1) !== ">") && (this.ArithPeek(1) !== "=")))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                right = this.ArithParseShift();
                left = new ArithBinaryOp(">", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseShift() {
        var left = this.ArithParseAdditive();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithMatch("<<=")) {
                break;
            }
            if (this.ArithMatch(">>=")) {
                break;
            }
            if (this.ArithMatch("<<")) {
                this.ArithConsume("<<");
                this.ArithSkipWs();
                var right = this.ArithParseAdditive();
                left = new ArithBinaryOp("<<", left, right);
            } else if (this.ArithMatch(">>")) {
                this.ArithConsume(">>");
                this.ArithSkipWs();
                right = this.ArithParseAdditive();
                left = new ArithBinaryOp(">>", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseAdditive() {
        var left = this.ArithParseMultiplicative();
        while (true) {
            this.ArithSkipWs();
            var c = this.ArithPeek();
            var c2 = this.ArithPeek(1);
            if (((c === "+") && ((c2 !== "+") && (c2 !== "=")))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseMultiplicative();
                left = new ArithBinaryOp("+", left, right);
            } else if (((c === "-") && ((c2 !== "-") && (c2 !== "=")))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                right = this.ArithParseMultiplicative();
                left = new ArithBinaryOp("-", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseMultiplicative() {
        var left = this.ArithParseExponentiation();
        while (true) {
            this.ArithSkipWs();
            var c = this.ArithPeek();
            var c2 = this.ArithPeek(1);
            if (((c === "*") && ((c2 !== "*") && (c2 !== "=")))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                var right = this.ArithParseExponentiation();
                left = new ArithBinaryOp("*", left, right);
            } else if (((c === "/") && (c2 !== "="))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                right = this.ArithParseExponentiation();
                left = new ArithBinaryOp("/", left, right);
            } else if (((c === "%") && (c2 !== "="))) {
                this.ArithAdvance();
                this.ArithSkipWs();
                right = this.ArithParseExponentiation();
                left = new ArithBinaryOp("%", left, right);
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParseExponentiation() {
        var left = this.ArithParseUnary();
        this.ArithSkipWs();
        if (this.ArithMatch("**")) {
            this.ArithConsume("**");
            this.ArithSkipWs();
            var right = this.ArithParseExponentiation();
            return new ArithBinaryOp("**", left, right);
        }
        return left;
    }
    
    ArithParseUnary() {
        this.ArithSkipWs();
        // Pre-increment/decrement
        if (this.ArithMatch("++")) {
            this.ArithConsume("++");
            this.ArithSkipWs();
            var operand = this.ArithParseUnary();
            return new ArithPreIncr(operand);
        }
        if (this.ArithMatch("--")) {
            this.ArithConsume("--");
            this.ArithSkipWs();
            operand = this.ArithParseUnary();
            return new ArithPreDecr(operand);
        }
        // Unary operators
        var c = this.ArithPeek();
        if ((c === "!")) {
            this.ArithAdvance();
            this.ArithSkipWs();
            operand = this.ArithParseUnary();
            return new ArithUnaryOp("!", operand);
        }
        if ((c === "~")) {
            this.ArithAdvance();
            this.ArithSkipWs();
            operand = this.ArithParseUnary();
            return new ArithUnaryOp("~", operand);
        }
        if (((c === "+") && (this.ArithPeek(1) !== "+"))) {
            this.ArithAdvance();
            this.ArithSkipWs();
            operand = this.ArithParseUnary();
            return new ArithUnaryOp("+", operand);
        }
        if (((c === "-") && (this.ArithPeek(1) !== "-"))) {
            this.ArithAdvance();
            this.ArithSkipWs();
            operand = this.ArithParseUnary();
            return new ArithUnaryOp("-", operand);
        }
        return this.ArithParsePostfix();
    }
    
    ArithParsePostfix() {
        var left = this.ArithParsePrimary();
        while (true) {
            this.ArithSkipWs();
            if (this.ArithMatch("++")) {
                this.ArithConsume("++");
                left = new ArithPostIncr(left);
            } else if (this.ArithMatch("--")) {
                this.ArithConsume("--");
                left = new ArithPostDecr(left);
            } else if ((this.ArithPeek() === "[")) {
                // Array subscript - but only for variables
                if ((left.kind === "var")) {
                    this.ArithAdvance();
                    this.ArithSkipWs();
                    var index = this.ArithParseComma();
                    this.ArithSkipWs();
                    if (!this.ArithConsume("]")) {
                        throw new ParseError("Expected ']' in array subscript", this._arith_pos);
                    }
                    left = new ArithSubscript(left.name, index);
                } else {
                    break;
                }
            } else {
                break;
            }
        }
        return left;
    }
    
    ArithParsePrimary() {
        this.ArithSkipWs();
        var c = this.ArithPeek();
        // Parenthesized expression
        if ((c === "(")) {
            this.ArithAdvance();
            this.ArithSkipWs();
            var expr = this.ArithParseComma();
            this.ArithSkipWs();
            if (!this.ArithConsume(")")) {
                throw new ParseError("Expected ')' in arithmetic expression", this._arith_pos);
            }
            return expr;
        }
        // Parameter expansion ${...} or $var or $(...)
        if ((c === "$")) {
            return this.ArithParseExpansion();
        }
        // Single-quoted string - content becomes the number
        if ((c === "'")) {
            return this.ArithParseSingleQuote();
        }
        // Double-quoted string - may contain expansions
        if ((c === "\"")) {
            return this.ArithParseDoubleQuote();
        }
        // Backtick command substitution
        if ((c === "`")) {
            return this.ArithParseBacktick();
        }
        // Escape sequence \X (not line continuation, which is handled in _arith_skip_ws)
        // Escape covers only the single character after backslash
        if ((c === "\\")) {
            this.ArithAdvance();
            if (this.ArithAtEnd()) {
                throw new ParseError("Unexpected end after backslash in arithmetic", this._arith_pos);
            }
            var escaped_char = this.ArithAdvance();
            return new ArithEscape(escaped_char);
        }
        // Number or variable
        return this.ArithParseNumberOrVar();
    }
    
    ArithParseExpansion() {
        if (!this.ArithConsume("$")) {
            throw new ParseError("Expected '$'", this._arith_pos);
        }
        var c = this.ArithPeek();
        // Command substitution $(...)
        if ((c === "(")) {
            return this.ArithParseCmdsub();
        }
        // Braced parameter ${...}
        if ((c === "{")) {
            return this.ArithParseBracedParam();
        }
        // Simple $var
        var name_chars = [];
        while (!this.ArithAtEnd()) {
            var ch = this.ArithPeek();
            if ((/^[a-zA-Z0-9]$/.test(ch) || (ch === "_"))) {
                name_chars.push(this.ArithAdvance());
            } else if (((IsSpecialParamOrDigit(ch) || (ch === "#")) && name_chars.length === 0)) {
                // Special parameters
                name_chars.push(this.ArithAdvance());
                break;
            } else {
                break;
            }
        }
        if (name_chars.length === 0) {
            throw new ParseError("Expected variable name after $", this._arith_pos);
        }
        return new ParamExpansion(name_chars.join(""));
    }
    
    ArithParseCmdsub() {
        // We're positioned after $, at (
        this.ArithAdvance();
        // Check for $(( which is nested arithmetic
        if ((this.ArithPeek() === "(")) {
            this.ArithAdvance();
            var depth = 1;
            var content_start = this._arith_pos;
            while ((!this.ArithAtEnd() && (depth > 0))) {
                var ch = this.ArithPeek();
                if ((ch === "(")) {
                    depth += 1;
                    this.ArithAdvance();
                } else if ((ch === ")")) {
                    if (((depth === 1) && (this.ArithPeek(1) === ")"))) {
                        break;
                    }
                    depth -= 1;
                    this.ArithAdvance();
                } else {
                    this.ArithAdvance();
                }
            }
            var content = this._arith_src.slice(content_start, this._arith_pos);
            this.ArithAdvance();
            this.ArithAdvance();
            var inner_expr = this.ParseArithExpr(content);
            return new ArithmeticExpansion(inner_expr);
        }
        // Regular command substitution
        depth = 1;
        content_start = this._arith_pos;
        while ((!this.ArithAtEnd() && (depth > 0))) {
            ch = this.ArithPeek();
            if ((ch === "(")) {
                depth += 1;
                this.ArithAdvance();
            } else if ((ch === ")")) {
                depth -= 1;
                if ((depth === 0)) {
                    break;
                }
                this.ArithAdvance();
            } else {
                this.ArithAdvance();
            }
        }
        content = this._arith_src.slice(content_start, this._arith_pos);
        this.ArithAdvance();
        // Parse the command inside
        var saved_pos = this.pos;
        var saved_src = this.source;
        var saved_len = this.length;
        this.source = content;
        this.pos = 0;
        this.length = content.length;
        var cmd = this.parseList();
        this.source = saved_src;
        this.pos = saved_pos;
        this.length = saved_len;
        return new CommandSubstitution(cmd);
    }
    
    ArithParseBracedParam() {
        this.ArithAdvance();
        // Handle indirect ${!var}
        if ((this.ArithPeek() === "!")) {
            this.ArithAdvance();
            var name_chars = [];
            while ((!this.ArithAtEnd() && (this.ArithPeek() !== "}"))) {
                name_chars.push(this.ArithAdvance());
            }
            this.ArithConsume("}");
            return new ParamIndirect(name_chars.join(""));
        }
        // Handle length ${#var}
        if ((this.ArithPeek() === "#")) {
            this.ArithAdvance();
            name_chars = [];
            while ((!this.ArithAtEnd() && (this.ArithPeek() !== "}"))) {
                name_chars.push(this.ArithAdvance());
            }
            this.ArithConsume("}");
            return new ParamLength(name_chars.join(""));
        }
        // Regular ${var} or ${var...}
        name_chars = [];
        while (!this.ArithAtEnd()) {
            var ch = this.ArithPeek();
            if ((ch === "}")) {
                this.ArithAdvance();
                return new ParamExpansion(name_chars.join(""));
            }
            if (IsParamExpansionOp(ch)) {
                // Operator follows
                break;
            }
            name_chars.push(this.ArithAdvance());
        }
        var name = name_chars.join("");
        // Check for operator
        var op_chars = [];
        var depth = 1;
        while ((!this.ArithAtEnd() && (depth > 0))) {
            ch = this.ArithPeek();
            if ((ch === "{")) {
                depth += 1;
                op_chars.push(this.ArithAdvance());
            } else if ((ch === "}")) {
                depth -= 1;
                if ((depth === 0)) {
                    break;
                }
                op_chars.push(this.ArithAdvance());
            } else {
                op_chars.push(this.ArithAdvance());
            }
        }
        this.ArithConsume("}");
        var op_str = op_chars.join("");
        // Parse the operator
        if (op_str.startsWith(":-")) {
            return new ParamExpansion(name, ":-", op_str.slice(2, op_str.length));
        }
        if (op_str.startsWith(":=")) {
            return new ParamExpansion(name, ":=", op_str.slice(2, op_str.length));
        }
        if (op_str.startsWith(":+")) {
            return new ParamExpansion(name, ":+", op_str.slice(2, op_str.length));
        }
        if (op_str.startsWith(":?")) {
            return new ParamExpansion(name, ":?", op_str.slice(2, op_str.length));
        }
        if (op_str.startsWith(":")) {
            return new ParamExpansion(name, ":", op_str.slice(1, op_str.length));
        }
        if (op_str.startsWith("##")) {
            return new ParamExpansion(name, "##", op_str.slice(2, op_str.length));
        }
        if (op_str.startsWith("#")) {
            return new ParamExpansion(name, "#", op_str.slice(1, op_str.length));
        }
        if (op_str.startsWith("%%")) {
            return new ParamExpansion(name, "%%", op_str.slice(2, op_str.length));
        }
        if (op_str.startsWith("%")) {
            return new ParamExpansion(name, "%", op_str.slice(1, op_str.length));
        }
        if (op_str.startsWith("//")) {
            return new ParamExpansion(name, "//", op_str.slice(2, op_str.length));
        }
        if (op_str.startsWith("/")) {
            return new ParamExpansion(name, "/", op_str.slice(1, op_str.length));
        }
        return new ParamExpansion(name, "", op_str);
    }
    
    ArithParseSingleQuote() {
        this.ArithAdvance();
        var content_start = this._arith_pos;
        while ((!this.ArithAtEnd() && (this.ArithPeek() !== "'"))) {
            this.ArithAdvance();
        }
        var content = this._arith_src.slice(content_start, this._arith_pos);
        if (!this.ArithConsume("'")) {
            throw new ParseError("Unterminated single quote in arithmetic", this._arith_pos);
        }
        return new ArithNumber(content);
    }
    
    ArithParseDoubleQuote() {
        this.ArithAdvance();
        var content_start = this._arith_pos;
        while ((!this.ArithAtEnd() && (this.ArithPeek() !== "\""))) {
            var c = this.ArithPeek();
            if (((c === "\\") && !this.ArithAtEnd())) {
                this.ArithAdvance();
                this.ArithAdvance();
            } else {
                this.ArithAdvance();
            }
        }
        var content = this._arith_src.slice(content_start, this._arith_pos);
        if (!this.ArithConsume("\"")) {
            throw new ParseError("Unterminated double quote in arithmetic", this._arith_pos);
        }
        return new ArithNumber(content);
    }
    
    ArithParseBacktick() {
        this.ArithAdvance();
        var content_start = this._arith_pos;
        while ((!this.ArithAtEnd() && (this.ArithPeek() !== "`"))) {
            var c = this.ArithPeek();
            if (((c === "\\") && !this.ArithAtEnd())) {
                this.ArithAdvance();
                this.ArithAdvance();
            } else {
                this.ArithAdvance();
            }
        }
        var content = this._arith_src.slice(content_start, this._arith_pos);
        if (!this.ArithConsume("`")) {
            throw new ParseError("Unterminated backtick in arithmetic", this._arith_pos);
        }
        // Parse the command inside
        var saved_pos = this.pos;
        var saved_src = this.source;
        var saved_len = this.length;
        this.source = content;
        this.pos = 0;
        this.length = content.length;
        var cmd = this.parseList();
        this.source = saved_src;
        this.pos = saved_pos;
        this.length = saved_len;
        return new CommandSubstitution(cmd);
    }
    
    ArithParseNumberOrVar() {
        this.ArithSkipWs();
        var chars = [];
        var c = this.ArithPeek();
        // Check for number (starts with digit or base#)
        if (/^[0-9]+$/.test(c)) {
            // Could be decimal, hex (0x), octal (0), or base#n
            while (!this.ArithAtEnd()) {
                var ch = this.ArithPeek();
                if ((/^[a-zA-Z0-9]$/.test(ch) || ((ch === "#") || (ch === "_")))) {
                    chars.push(this.ArithAdvance());
                } else {
                    break;
                }
            }
            return new ArithNumber(chars.join(""));
        }
        // Variable name (starts with letter or _)
        if ((/^[a-zA-Z]$/.test(c) || (c === "_"))) {
            while (!this.ArithAtEnd()) {
                ch = this.ArithPeek();
                if ((/^[a-zA-Z0-9]$/.test(ch) || (ch === "_"))) {
                    chars.push(this.ArithAdvance());
                } else {
                    break;
                }
            }
            return new ArithVar(chars.join(""));
        }
        throw new ParseError((("Unexpected character '" + c) + "' in arithmetic expression"), this._arith_pos);
    }
    
    ParseDeprecatedArithmetic() {
        if ((this.atEnd() || (this.peek() !== "$"))) {
            return [null, ""];
        }
        var start = this.pos;
        // Check for $[
        if ((((this.pos + 1) >= this.length) || (this.source[(this.pos + 1)] !== "["))) {
            return [null, ""];
        }
        this.advance();
        this.advance();
        // Find matching ] - need to track nested brackets
        var content_start = this.pos;
        var depth = 1;
        while ((!this.atEnd() && (depth > 0))) {
            var c = this.peek();
            if ((c === "[")) {
                depth += 1;
                this.advance();
            } else if ((c === "]")) {
                depth -= 1;
                if ((depth === 0)) {
                    break;
                }
                this.advance();
            } else {
                this.advance();
            }
        }
        if ((this.atEnd() || (depth !== 0))) {
            this.pos = start;
            return [null, ""];
        }
        var content = this.source.slice(content_start, this.pos);
        this.advance();
        var text = this.source.slice(start, this.pos);
        return [new ArithDeprecated(content), text];
    }
    
    ParseAnsiCQuote() {
        if ((this.atEnd() || (this.peek() !== "$"))) {
            return [null, ""];
        }
        if ((((this.pos + 1) >= this.length) || (this.source[(this.pos + 1)] !== "'"))) {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        this.advance();
        var content_chars = [];
        var found_close = false;
        while (!this.atEnd()) {
            var ch = this.peek();
            if ((ch === "'")) {
                this.advance();
                found_close = true;
                break;
            } else if ((ch === "\\")) {
                // Escape sequence - include both backslash and following char in content
                content_chars.push(this.advance());
                if (!this.atEnd()) {
                    content_chars.push(this.advance());
                }
            } else {
                content_chars.push(this.advance());
            }
        }
        if (!found_close) {
            // Unterminated - reset and return None
            this.pos = start;
            return [null, ""];
        }
        var text = this.source.slice(start, this.pos);
        var content = content_chars.join("");
        return [new AnsiCQuote(content), text];
    }
    
    ParseLocaleString() {
        if ((this.atEnd() || (this.peek() !== "$"))) {
            return [null, "", []];
        }
        if ((((this.pos + 1) >= this.length) || (this.source[(this.pos + 1)] !== "\""))) {
            return [null, "", []];
        }
        var start = this.pos;
        this.advance();
        this.advance();
        var content_chars = [];
        var inner_parts = [];
        var found_close = false;
        while (!this.atEnd()) {
            var ch = this.peek();
            if ((ch === "\"")) {
                this.advance();
                found_close = true;
                break;
            } else if (((ch === "\\") && ((this.pos + 1) < this.length))) {
                // Escape sequence (line continuation removes both)
                var next_ch = this.source[(this.pos + 1)];
                if ((next_ch === "\n")) {
                    // Line continuation - skip both backslash and newline
                    this.advance();
                    this.advance();
                } else {
                    content_chars.push(this.advance());
                    content_chars.push(this.advance());
                }
            } else if (((ch === "$") && ((this.pos + 2) < this.length) && (this.source[(this.pos + 1)] === "(") && (this.source[(this.pos + 2)] === "("))) {
                // Handle arithmetic expansion $((...))
                var arith_result = this.ParseArithmeticExpansion();
                var arith_node = arith_result[0];
                var arith_text = arith_result[1];
                if (arith_node) {
                    inner_parts.push(arith_node);
                    content_chars.push(arith_text);
                } else {
                    // Not arithmetic - try command substitution
                    var cmdsub_result = this.ParseCommandSubstitution();
                    var cmdsub_node = cmdsub_result[0];
                    var cmdsub_text = cmdsub_result[1];
                    if (cmdsub_node) {
                        inner_parts.push(cmdsub_node);
                        content_chars.push(cmdsub_text);
                    } else {
                        content_chars.push(this.advance());
                    }
                }
            } else if (((ch === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                // Handle command substitution $(...)
                cmdsub_result = this.ParseCommandSubstitution();
                cmdsub_node = cmdsub_result[0];
                cmdsub_text = cmdsub_result[1];
                if (cmdsub_node) {
                    inner_parts.push(cmdsub_node);
                    content_chars.push(cmdsub_text);
                } else {
                    content_chars.push(this.advance());
                }
            } else if ((ch === "$")) {
                // Handle parameter expansion
                var param_result = this.ParseParamExpansion();
                var param_node = param_result[0];
                var param_text = param_result[1];
                if (param_node) {
                    inner_parts.push(param_node);
                    content_chars.push(param_text);
                } else {
                    content_chars.push(this.advance());
                }
            } else if ((ch === "`")) {
                // Handle backtick command substitution
                cmdsub_result = this.ParseBacktickSubstitution();
                cmdsub_node = cmdsub_result[0];
                cmdsub_text = cmdsub_result[1];
                if (cmdsub_node) {
                    inner_parts.push(cmdsub_node);
                    content_chars.push(cmdsub_text);
                } else {
                    content_chars.push(this.advance());
                }
            } else {
                content_chars.push(this.advance());
            }
        }
        if (!found_close) {
            // Unterminated - reset and return None
            this.pos = start;
            return [null, "", []];
        }
        var content = content_chars.join("");
        // Reconstruct text from parsed content (handles line continuation removal)
        var text = (("$\"" + content) + "\"");
        return [new LocaleString(content), text, inner_parts];
    }
    
    ParseParamExpansion() {
        if ((this.atEnd() || (this.peek() !== "$"))) {
            return [null, ""];
        }
        var start = this.pos;
        this.advance();
        if (this.atEnd()) {
            this.pos = start;
            return [null, ""];
        }
        var ch = this.peek();
        // Braced expansion ${...}
        if ((ch === "{")) {
            this.advance();
            return this.ParseBracedParam(start);
        }
        // Simple expansion $var or $special
        // Special parameters: ?$!#@*-0-9
        if ((IsSpecialParamOrDigit(ch) || (ch === "#"))) {
            this.advance();
            var text = this.source.slice(start, this.pos);
            return [new ParamExpansion(ch), text];
        }
        // Variable name [a-zA-Z_][a-zA-Z0-9_]*
        if ((/^[a-zA-Z]$/.test(ch) || (ch === "_"))) {
            var name_start = this.pos;
            while (!this.atEnd()) {
                var c = this.peek();
                if ((/^[a-zA-Z0-9]$/.test(c) || (c === "_"))) {
                    this.advance();
                } else {
                    break;
                }
            }
            var name = this.source.slice(name_start, this.pos);
            text = this.source.slice(start, this.pos);
            return [new ParamExpansion(name), text];
        }
        // Not a valid expansion, restore position
        this.pos = start;
        return [null, ""];
    }
    
    ParseBracedParam(start) {
        if (this.atEnd()) {
            this.pos = start;
            return [null, ""];
        }
        var ch = this.peek();
        // ${#param} - length
        if ((ch === "#")) {
            this.advance();
            var param = this.ConsumeParamName();
            if ((param && !this.atEnd() && (this.peek() === "}"))) {
                this.advance();
                var text = this.source.slice(start, this.pos);
                return [new ParamLength(param), text];
            }
            this.pos = start;
            return [null, ""];
        }
        // ${!param} or ${!param<op><arg>} - indirect
        if ((ch === "!")) {
            this.advance();
            param = this.ConsumeParamName();
            if (param) {
                // Skip optional whitespace before closing brace
                while ((!this.atEnd() && IsWhitespaceNoNewline(this.peek()))) {
                    this.advance();
                }
                if ((!this.atEnd() && (this.peek() === "}"))) {
                    this.advance();
                    text = this.source.slice(start, this.pos);
                    return [new ParamIndirect(param), text];
                }
                // ${!prefix@} and ${!prefix*} are prefix matching (lists variable names)
                // These are NOT operators - the @/* is part of the indirect form
                if ((!this.atEnd() && IsAtOrStar(this.peek()))) {
                    var suffix = this.advance();
                    while ((!this.atEnd() && IsWhitespaceNoNewline(this.peek()))) {
                        this.advance();
                    }
                    if ((!this.atEnd() && (this.peek() === "}"))) {
                        this.advance();
                        text = this.source.slice(start, this.pos);
                        return [new ParamIndirect((param + suffix)), text];
                    }
                    // Not a valid prefix match, reset
                    this.pos = start;
                    return [null, ""];
                }
                // Check for operator (e.g., ${!##} = indirect of # with # op)
                var op = this.ConsumeParamOperator();
                if ((op != null)) {
                    // Parse argument until closing brace
                    var arg_chars = [];
                    var depth = 1;
                    while ((!this.atEnd() && (depth > 0))) {
                        var c = this.peek();
                        if (((c === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "{"))) {
                            depth += 1;
                            arg_chars.push(this.advance());
                            arg_chars.push(this.advance());
                        } else if ((c === "}")) {
                            depth -= 1;
                            if ((depth > 0)) {
                                arg_chars.push(this.advance());
                            }
                        } else if ((c === "\\")) {
                            arg_chars.push(this.advance());
                            if (!this.atEnd()) {
                                arg_chars.push(this.advance());
                            }
                        } else {
                            arg_chars.push(this.advance());
                        }
                    }
                    if ((depth === 0)) {
                        this.advance();
                        var arg = arg_chars.join("");
                        text = this.source.slice(start, this.pos);
                        return [new ParamIndirect(param, op, arg), text];
                    }
                }
            }
            this.pos = start;
            return [null, ""];
        }
        // ${param} or ${param<op><arg>}
        param = this.ConsumeParamName();
        if (!param) {
            // Unknown syntax like ${(M)...} (zsh) - consume until matching }
            // Bash accepts these syntactically but fails at runtime
            depth = 1;
            var content_start = this.pos;
            while ((!this.atEnd() && (depth > 0))) {
                c = this.peek();
                if ((c === "{")) {
                    depth += 1;
                    this.advance();
                } else if ((c === "}")) {
                    depth -= 1;
                    if ((depth === 0)) {
                        break;
                    }
                    this.advance();
                } else if ((c === "\\")) {
                    this.advance();
                    if (!this.atEnd()) {
                        this.advance();
                    }
                } else {
                    this.advance();
                }
            }
            if ((depth === 0)) {
                var content = this.source.slice(content_start, this.pos);
                this.advance();
                text = this.source.slice(start, this.pos);
                return [new ParamExpansion(content), text];
            }
            this.pos = start;
            return [null, ""];
        }
        if (this.atEnd()) {
            this.pos = start;
            return [null, ""];
        }
        // Check for closing brace (simple expansion)
        if ((this.peek() === "}")) {
            this.advance();
            text = this.source.slice(start, this.pos);
            return [new ParamExpansion(param), text];
        }
        // Parse operator
        op = this.ConsumeParamOperator();
        if ((op == null)) {
            // Unknown operator - bash still parses these (fails at runtime)
            // Treat the current char as the operator
            op = this.advance();
        }
        // Parse argument (everything until closing brace)
        // Track quote state and nesting
        arg_chars = [];
        depth = 1;
        var in_single_quote = false;
        var in_double_quote = false;
        while ((!this.atEnd() && (depth > 0))) {
            c = this.peek();
            // Single quotes - no escapes, just scan to closing quote
            if (((c === "'") && !in_double_quote)) {
                if (in_single_quote) {
                    in_single_quote = false;
                } else {
                    in_single_quote = true;
                }
                arg_chars.push(this.advance());
            } else if (((c === "\"") && !in_single_quote)) {
                // Double quotes - toggle state
                in_double_quote = !in_double_quote;
                arg_chars.push(this.advance());
            } else if (((c === "\\") && !in_single_quote)) {
                // Escape - skip next char (line continuation removes both)
                if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "\n"))) {
                    // Line continuation - skip both backslash and newline
                    this.advance();
                    this.advance();
                } else {
                    arg_chars.push(this.advance());
                    if (!this.atEnd()) {
                        arg_chars.push(this.advance());
                    }
                }
            } else if (((c === "$") && !in_single_quote && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "{"))) {
                // Nested ${...} - increase depth (outside single quotes)
                depth += 1;
                arg_chars.push(this.advance());
                arg_chars.push(this.advance());
            } else if (((c === "$") && !in_single_quote && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                // Command substitution $(...) - scan to matching )
                arg_chars.push(this.advance());
                arg_chars.push(this.advance());
                var paren_depth = 1;
                while ((!this.atEnd() && (paren_depth > 0))) {
                    var pc = this.peek();
                    if ((pc === "(")) {
                        paren_depth += 1;
                    } else if ((pc === ")")) {
                        paren_depth -= 1;
                    } else if ((pc === "\\")) {
                        arg_chars.push(this.advance());
                        if (!this.atEnd()) {
                            arg_chars.push(this.advance());
                        }
                        continue;
                    }
                    arg_chars.push(this.advance());
                }
            } else if (((c === "`") && !in_single_quote)) {
                // Backtick command substitution - scan to matching `
                arg_chars.push(this.advance());
                while ((!this.atEnd() && (this.peek() !== "`"))) {
                    var bc = this.peek();
                    if (((bc === "\\") && ((this.pos + 1) < this.length))) {
                        var next_c = this.source[(this.pos + 1)];
                        if (IsEscapeCharInDquote(next_c)) {
                            arg_chars.push(this.advance());
                        }
                    }
                    arg_chars.push(this.advance());
                }
                if (!this.atEnd()) {
                    arg_chars.push(this.advance());
                }
            } else if ((c === "}")) {
                // Closing brace - handle depth for nested ${...}
                if (in_single_quote) {
                    // Inside single quotes, } is literal
                    arg_chars.push(this.advance());
                } else if (in_double_quote) {
                    // Inside double quotes, } can close nested ${...}
                    if ((depth > 1)) {
                        depth -= 1;
                        arg_chars.push(this.advance());
                    } else {
                        // Literal } in double quotes (not closing nested)
                        arg_chars.push(this.advance());
                    }
                } else {
                    depth -= 1;
                    if ((depth > 0)) {
                        arg_chars.push(this.advance());
                    }
                }
            } else {
                arg_chars.push(this.advance());
            }
        }
        if ((depth !== 0)) {
            this.pos = start;
            return [null, ""];
        }
        this.advance();
        arg = arg_chars.join("");
        // Reconstruct text from parsed components (handles line continuation removal)
        text = (((("${" + param) + op) + arg) + "}");
        return [new ParamExpansion(param, op, arg), text];
    }
    
    ConsumeParamName() {
        if (this.atEnd()) {
            return null;
        }
        var ch = this.peek();
        // Special parameters
        if (IsSpecialParam(ch)) {
            this.advance();
            return ch;
        }
        // Digits (positional params)
        if (/^[0-9]+$/.test(ch)) {
            var name_chars = [];
            while ((!this.atEnd() && /^[0-9]+$/.test(this.peek()))) {
                name_chars.push(this.advance());
            }
            return name_chars.join("");
        }
        // Variable name
        if ((/^[a-zA-Z]$/.test(ch) || (ch === "_"))) {
            name_chars = [];
            while (!this.atEnd()) {
                var c = this.peek();
                if ((/^[a-zA-Z0-9]$/.test(c) || (c === "_"))) {
                    name_chars.push(this.advance());
                } else if ((c === "[")) {
                    // Array subscript - track bracket depth
                    name_chars.push(this.advance());
                    var bracket_depth = 1;
                    while ((!this.atEnd() && (bracket_depth > 0))) {
                        var sc = this.peek();
                        if ((sc === "[")) {
                            bracket_depth += 1;
                        } else if ((sc === "]")) {
                            bracket_depth -= 1;
                            if ((bracket_depth === 0)) {
                                break;
                            }
                        }
                        name_chars.push(this.advance());
                    }
                    if ((!this.atEnd() && (this.peek() === "]"))) {
                        name_chars.push(this.advance());
                    }
                    break;
                } else {
                    break;
                }
            }
            if (name_chars) {
                return name_chars.join("");
            } else {
                return null;
            }
        }
        return null;
    }
    
    ConsumeParamOperator() {
        if (this.atEnd()) {
            return null;
        }
        var ch = this.peek();
        // Operators with optional colon prefix: :- := :? :+
        if ((ch === ":")) {
            this.advance();
            if (this.atEnd()) {
                return ":";
            }
            var next_ch = this.peek();
            if (IsSimpleParamOp(next_ch)) {
                this.advance();
                return (":" + next_ch);
            }
            // Just : (substring)
            return ":";
        }
        // Operators without colon: - = ? +
        if (IsSimpleParamOp(ch)) {
            this.advance();
            return ch;
        }
        // Pattern removal: # ## % %%
        if ((ch === "#")) {
            this.advance();
            if ((!this.atEnd() && (this.peek() === "#"))) {
                this.advance();
                return "##";
            }
            return "#";
        }
        if ((ch === "%")) {
            this.advance();
            if ((!this.atEnd() && (this.peek() === "%"))) {
                this.advance();
                return "%%";
            }
            return "%";
        }
        // Substitution: / // /# /%
        if ((ch === "/")) {
            this.advance();
            if (!this.atEnd()) {
                next_ch = this.peek();
                if ((next_ch === "/")) {
                    this.advance();
                    return "//";
                } else if ((next_ch === "#")) {
                    this.advance();
                    return "/#";
                } else if ((next_ch === "%")) {
                    this.advance();
                    return "/%";
                }
            }
            return "/";
        }
        // Case modification: ^ ^^ , ,,
        if ((ch === "^")) {
            this.advance();
            if ((!this.atEnd() && (this.peek() === "^"))) {
                this.advance();
                return "^^";
            }
            return "^";
        }
        if ((ch === ",")) {
            this.advance();
            if ((!this.atEnd() && (this.peek() === ","))) {
                this.advance();
                return ",,";
            }
            return ",";
        }
        // Transformation: @
        if ((ch === "@")) {
            this.advance();
            return "@";
        }
        return null;
    }
    
    parseRedirect() {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        var start = this.pos;
        var fd = null;
        var varfd = null;
        // Check for variable fd {varname} or {varname[subscript]} before redirect
        if ((this.peek() === "{")) {
            var saved = this.pos;
            this.advance();
            var varname_chars = [];
            while ((!this.atEnd() && ((this.peek() !== "}") && !IsRedirectChar(this.peek())))) {
                var ch = this.peek();
                if ((/^[a-zA-Z0-9]$/.test(ch) || ((ch === "_") || (ch === "[") || (ch === "]")))) {
                    varname_chars.push(this.advance());
                } else {
                    break;
                }
            }
            if ((!this.atEnd() && (this.peek() === "}") && varname_chars)) {
                this.advance();
                varfd = varname_chars.join("");
            } else {
                // Not a valid variable fd, restore
                this.pos = saved;
            }
        }
        // Check for optional fd number before redirect (if no varfd)
        if (((varfd == null) && this.peek() && /^[0-9]+$/.test(this.peek()))) {
            var fd_chars = [];
            while ((!this.atEnd() && /^[0-9]+$/.test(this.peek()))) {
                fd_chars.push(this.advance());
            }
            fd = parseInt(fd_chars.join(""), 10);
        }
        ch = this.peek();
        // Handle &> and &>> (redirect both stdout and stderr)
        // Note: &> does NOT take a preceding fd number. If we consumed digits,
        // they should be a separate word, not an fd. E.g., "2&>1" is command "2"
        // with redirect "&> 1", not fd 2 redirected.
        if (((ch === "&") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === ">"))) {
            if ((fd != null)) {
                // We consumed digits that should be a word, not an fd
                // Restore position and let parse_word handle them
                this.pos = start;
                return null;
            }
            this.advance();
            this.advance();
            if ((!this.atEnd() && (this.peek() === ">"))) {
                this.advance();
                var op = "&>>";
            } else {
                op = "&>";
            }
            this.skipWhitespace();
            var target = this.parseWord();
            if ((target == null)) {
                throw new ParseError(("Expected target for redirect " + op), this.pos);
            }
            return new Redirect(op, target);
        }
        if (((ch == null) || !IsRedirectChar(ch))) {
            // Not a redirect, restore position
            this.pos = start;
            return null;
        }
        // Check for process substitution <(...) or >(...) - not a redirect
        // Only treat as redirect if there's a space before ( or an fd number
        if (((fd == null) && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
            // This is a process substitution, not a redirect
            this.pos = start;
            return null;
        }
        // Parse the redirect operator
        op = this.advance();
        // Check for multi-char operators
        var strip_tabs = false;
        if (!this.atEnd()) {
            var next_ch = this.peek();
            if (((op === ">") && (next_ch === ">"))) {
                this.advance();
                op = ">>";
            } else if (((op === "<") && (next_ch === "<"))) {
                this.advance();
                if ((!this.atEnd() && (this.peek() === "<"))) {
                    this.advance();
                    op = "<<<";
                } else if ((!this.atEnd() && (this.peek() === "-"))) {
                    this.advance();
                    op = "<<";
                    strip_tabs = true;
                } else {
                    op = "<<";
                }
            } else if (((op === "<") && (next_ch === ">"))) {
                // Handle <> (read-write)
                this.advance();
                op = "<>";
            } else if (((op === ">") && (next_ch === "|"))) {
                // Handle >| (noclobber override)
                this.advance();
                op = ">|";
            } else if (((fd == null) && (varfd == null) && (op === ">") && (next_ch === "&"))) {
                // Only consume >& or <& as operators if NOT followed by a digit or -
                // (>&2 should be > with target &2, not >& with target 2)
                // (>&- should be > with target &-, not >& with target -)
                // Peek ahead to see if there's a digit or - after &
                if ((((this.pos + 1) >= this.length) || !IsDigitOrDash(this.source[(this.pos + 1)]))) {
                    this.advance();
                    op = ">&";
                }
            } else if (((fd == null) && (varfd == null) && (op === "<") && (next_ch === "&"))) {
                if ((((this.pos + 1) >= this.length) || !IsDigitOrDash(this.source[(this.pos + 1)]))) {
                    this.advance();
                    op = "<&";
                }
            }
        }
        // Handle here document
        if ((op === "<<")) {
            return this.ParseHeredoc(fd, strip_tabs);
        }
        // Combine fd or varfd with operator if present
        if ((varfd != null)) {
            op = ((("{" + varfd) + "}") + op);
        } else if ((fd != null)) {
            op = (String(fd) + op);
        }
        this.skipWhitespace();
        // Handle fd duplication targets like &1, &2, &-, &10-, &$var
        if ((!this.atEnd() && (this.peek() === "&"))) {
            this.advance();
            // Parse the fd number or - for close, including move syntax like &10-
            if ((!this.atEnd() && (/^[0-9]+$/.test(this.peek()) || (this.peek() === "-")))) {
                fd_chars = [];
                while ((!this.atEnd() && /^[0-9]+$/.test(this.peek()))) {
                    fd_chars.push(this.advance());
                }
                if (fd_chars) {
                    var fd_target = fd_chars.join("");
                } else {
                    fd_target = "";
                }
                // Handle just - for close, or N- for move syntax
                if ((!this.atEnd() && (this.peek() === "-"))) {
                    fd_target += this.advance();
                }
                target = new Word(("&" + fd_target));
            } else {
                // Could be &$var or &word - parse word and prepend &
                var inner_word = this.parseWord();
                if ((inner_word != null)) {
                    target = new Word(("&" + inner_word.value));
                    target.parts = inner_word.parts;
                } else {
                    throw new ParseError(("Expected target for redirect " + op), this.pos);
                }
            }
        } else {
            target = this.parseWord();
        }
        if ((target == null)) {
            throw new ParseError(("Expected target for redirect " + op), this.pos);
        }
        return new Redirect(op, target);
    }
    
    ParseHeredoc(fd, strip_tabs) {
        this.skipWhitespace();
        // Parse the delimiter, handling quoting (can be mixed like 'EOF'"2")
        var quoted = false;
        var delimiter_chars = [];
        while ((!this.atEnd() && !IsMetachar(this.peek()))) {
            var ch = this.peek();
            if ((ch === "\"")) {
                quoted = true;
                this.advance();
                while ((!this.atEnd() && (this.peek() !== "\""))) {
                    delimiter_chars.push(this.advance());
                }
                if (!this.atEnd()) {
                    this.advance();
                }
            } else if ((ch === "'")) {
                quoted = true;
                this.advance();
                while ((!this.atEnd() && (this.peek() !== "'"))) {
                    delimiter_chars.push(this.advance());
                }
                if (!this.atEnd()) {
                    this.advance();
                }
            } else if ((ch === "\\")) {
                this.advance();
                if (!this.atEnd()) {
                    var next_ch = this.peek();
                    if ((next_ch === "\n")) {
                        // Backslash-newline: continue delimiter on next line
                        this.advance();
                    } else {
                        // Regular escape - quotes the next char
                        quoted = true;
                        delimiter_chars.push(this.advance());
                    }
                }
            } else if (((ch === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                // Command substitution embedded in delimiter
                delimiter_chars.push(this.advance());
                delimiter_chars.push(this.advance());
                var depth = 1;
                while ((!this.atEnd() && (depth > 0))) {
                    var c = this.peek();
                    if ((c === "(")) {
                        depth += 1;
                    } else if ((c === ")")) {
                        depth -= 1;
                    }
                    delimiter_chars.push(this.advance());
                }
            } else {
                delimiter_chars.push(this.advance());
            }
        }
        var delimiter = delimiter_chars.join("");
        // Find the end of the current line (command continues until newline)
        // We need to mark where the heredoc content starts
        // Must be quote-aware - newlines inside quoted strings don't end the line
        var line_end = this.pos;
        while (((line_end < this.length) && (this.source[line_end] !== "\n"))) {
            ch = this.source[line_end];
            if ((ch === "'")) {
                // Single-quoted string - skip to closing quote (no escapes)
                line_end += 1;
                while (((line_end < this.length) && (this.source[line_end] !== "'"))) {
                    line_end += 1;
                }
            } else if ((ch === "\"")) {
                // Double-quoted string - skip to closing quote (with escapes)
                line_end += 1;
                while (((line_end < this.length) && (this.source[line_end] !== "\""))) {
                    if (((this.source[line_end] === "\\") && ((line_end + 1) < this.length))) {
                        line_end += 2;
                    } else {
                        line_end += 1;
                    }
                }
            } else if (((ch === "\\") && ((line_end + 1) < this.length))) {
                // Backslash escape - skip both chars
                line_end += 2;
                continue;
            }
            line_end += 1;
        }
        // Find heredoc content starting position
        // If there's already a pending heredoc, this one's content starts after that
        if (((this._pending_heredoc_end != null) && (this._pending_heredoc_end > line_end))) {
            var content_start = this._pending_heredoc_end;
        } else if ((line_end < this.length)) {
            content_start = (line_end + 1);
        } else {
            content_start = this.length;
        }
        // Find the delimiter line
        var content_lines = [];
        var scan_pos = content_start;
        while ((scan_pos < this.length)) {
            // Find end of current line
            var line_start = scan_pos;
            line_end = scan_pos;
            while (((line_end < this.length) && (this.source[line_end] !== "\n"))) {
                line_end += 1;
            }
            var line = this.source.slice(line_start, line_end);
            // For unquoted heredocs, process backslash-newline before checking delimiter
            // Join continued lines to check the full logical line against delimiter
            if (!quoted) {
                while ((line.endsWith("\\") && (line_end < this.length))) {
                    // Continue to next line
                    line = line.slice(0, (line.length - 1));
                    line_end += 1;
                    var next_line_start = line_end;
                    while (((line_end < this.length) && (this.source[line_end] !== "\n"))) {
                        line_end += 1;
                    }
                    line = (line + this.source.slice(next_line_start, line_end));
                }
            }
            // Check if this line is the delimiter
            var check_line = line;
            if (strip_tabs) {
                check_line = line.replace(/^[\t]+/, "");
            }
            if ((check_line === delimiter)) {
                // Found the end - update parser position past the heredoc
                // We need to consume the heredoc content from the input
                // But we can't do that here because we haven't finished parsing the command line
                // Store the heredoc info and let the command parser handle it
                break;
            }
            // Add line to content (with newline, since we consumed continuations above)
            if (strip_tabs) {
                line = line.replace(/^[\t]+/, "");
            }
            content_lines.push((line + "\n"));
            // Move past the newline
            if ((line_end < this.length)) {
                scan_pos = (line_end + 1);
            } else {
                scan_pos = this.length;
            }
        }
        // Join content (newlines already included per line)
        var content = content_lines.join("");
        // Store the position where heredoc content ends so we can skip it later
        // line_end points to the end of the delimiter line (after any continuations)
        var heredoc_end = line_end;
        if ((heredoc_end < this.length)) {
            heredoc_end += 1;
        }
        // Register this heredoc's end position
        if ((this._pending_heredoc_end == null)) {
            this._pending_heredoc_end = heredoc_end;
        } else {
            this._pending_heredoc_end = Math.max(this._pending_heredoc_end, heredoc_end);
        }
        return new HereDoc(delimiter, content, strip_tabs, quoted, fd);
    }
    
    parseCommand() {
        var words = [];
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            if (this.atEnd()) {
                break;
            }
            var ch = this.peek();
            // Check for command terminators, but &> and &>> are redirects, not terminators
            if (IsListTerminator(ch)) {
                break;
            }
            if (((ch === "&") && !(((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === ">")))) {
                break;
            }
            // } is only a terminator at command position (closing a brace group)
            // In argument position, } is just a regular word
            if (((this.peek() === "}") && !words)) {
                // Check if } would be a standalone word (next char is whitespace/meta/EOF)
                var next_pos = (this.pos + 1);
                if (((next_pos >= this.length) || IsWordEndContext(this.source[next_pos]))) {
                    break;
                }
            }
            // Try to parse a redirect first
            var redirect = this.parseRedirect();
            if ((redirect != null)) {
                redirects.push(redirect);
                continue;
            }
            // Otherwise parse a word
            // Allow array assignments like a[1 + 2]= in prefix position (before first non-assignment)
            // Check if all previous words were assignments (contain = not inside quotes)
            var all_assignments = true;
            for (let w of words) {
                if (!this.IsAssignmentWord(w)) {
                    all_assignments = false;
                    break;
                }
            }
            var word = this.parseWord((!words || all_assignments));
            if ((word == null)) {
                break;
            }
            words.push(word);
        }
        if ((!words && !redirects)) {
            return null;
        }
        return new Command(words, redirects);
    }
    
    parseSubshell() {
        this.skipWhitespace();
        if ((this.atEnd() || (this.peek() !== "("))) {
            return null;
        }
        this.advance();
        var body = this.parseList();
        if ((body == null)) {
            throw new ParseError("Expected command in subshell", this.pos);
        }
        this.skipWhitespace();
        if ((this.atEnd() || (this.peek() !== ")"))) {
            throw new ParseError("Expected ) to close subshell", this.pos);
        }
        this.advance();
        // Collect trailing redirects
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        if (redirects) {
            return new Subshell(body, redirects);
        } else {
            return new Subshell(body, null);
        }
    }
    
    parseArithmeticCommand() {
        this.skipWhitespace();
        // Check for ((
        if ((this.atEnd() || (this.peek() !== "(") || ((this.pos + 1) >= this.length) || (this.source[(this.pos + 1)] !== "("))) {
            return null;
        }
        var saved_pos = this.pos;
        this.advance();
        this.advance();
        // Find matching )) - track nested parens
        // Must be )) with no space between - ') )' is nested subshells
        var content_start = this.pos;
        var depth = 1;
        while ((!this.atEnd() && (depth > 0))) {
            var c = this.peek();
            if ((c === "(")) {
                depth += 1;
                this.advance();
            } else if ((c === ")")) {
                // Check for )) (must be consecutive, no space)
                if (((depth === 1) && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === ")"))) {
                    // Found the closing ))
                    break;
                }
                depth -= 1;
                if ((depth === 0)) {
                    // Closed with ) but next isn't ) - this is nested subshells, not arithmetic
                    this.pos = saved_pos;
                    return null;
                }
                this.advance();
            } else {
                this.advance();
            }
        }
        if ((this.atEnd() || (depth !== 1))) {
            // Didn't find )) - might be nested subshells or malformed
            this.pos = saved_pos;
            return null;
        }
        var content = this.source.slice(content_start, this.pos);
        this.advance();
        this.advance();
        // Parse the arithmetic expression
        var expr = this.ParseArithExpr(content);
        // Collect trailing redirects
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new ArithmeticCommand(expr, redir_arg, content);
    }
    
    // Unary operators for [[ ]] conditionals
    COND_UNARY_OPS = new Set(["-a", "-b", "-c", "-d", "-e", "-f", "-g", "-h", "-k", "-p", "-r", "-s", "-t", "-u", "-w", "-x", "-G", "-L", "-N", "-O", "-S", "-z", "-n", "-o", "-v", "-R"]);
    // Binary operators for [[ ]] conditionals
    COND_BINARY_OPS = new Set(["==", "!=", "=~", "=", "<", ">", "-eq", "-ne", "-lt", "-le", "-gt", "-ge", "-nt", "-ot", "-ef"]);
    parseConditionalExpr() {
        this.skipWhitespace();
        // Check for [[
        if ((this.atEnd() || (this.peek() !== "[") || ((this.pos + 1) >= this.length) || (this.source[(this.pos + 1)] !== "["))) {
            return null;
        }
        this.advance();
        this.advance();
        // Parse the conditional expression body
        var body = this.ParseCondOr();
        // Skip whitespace before ]]
        while ((!this.atEnd() && IsWhitespaceNoNewline(this.peek()))) {
            this.advance();
        }
        // Expect ]]
        if ((this.atEnd() || (this.peek() !== "]") || ((this.pos + 1) >= this.length) || (this.source[(this.pos + 1)] !== "]"))) {
            throw new ParseError("Expected ]] to close conditional expression", this.pos);
        }
        this.advance();
        this.advance();
        // Collect trailing redirects
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new ConditionalExpr(body, redir_arg);
    }
    
    CondSkipWhitespace() {
        while (!this.atEnd()) {
            if (IsWhitespaceNoNewline(this.peek())) {
                this.advance();
            } else if (((this.peek() === "\\") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "\n"))) {
                this.advance();
                this.advance();
            } else if ((this.peek() === "\n")) {
                // Bare newline is also allowed inside [[ ]]
                this.advance();
            } else {
                break;
            }
        }
    }
    
    CondAtEnd() {
        return (this.atEnd() || ((this.peek() === "]") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "]")));
    }
    
    ParseCondOr() {
        this.CondSkipWhitespace();
        var left = this.ParseCondAnd();
        this.CondSkipWhitespace();
        if ((!this.CondAtEnd() && (this.peek() === "|") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "|"))) {
            this.advance();
            this.advance();
            var right = this.ParseCondOr();
            return new CondOr(left, right);
        }
        return left;
    }
    
    ParseCondAnd() {
        this.CondSkipWhitespace();
        var left = this.ParseCondTerm();
        this.CondSkipWhitespace();
        if ((!this.CondAtEnd() && (this.peek() === "&") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "&"))) {
            this.advance();
            this.advance();
            var right = this.ParseCondAnd();
            return new CondAnd(left, right);
        }
        return left;
    }
    
    ParseCondTerm() {
        this.CondSkipWhitespace();
        if (this.CondAtEnd()) {
            throw new ParseError("Unexpected end of conditional expression", this.pos);
        }
        // Negation: ! term
        if ((this.peek() === "!")) {
            // Check it's not != operator (need whitespace after !)
            if ((((this.pos + 1) < this.length) && !IsWhitespaceNoNewline(this.source[(this.pos + 1)]))) {
            } else {
                this.advance();
                var operand = this.ParseCondTerm();
                return new CondNot(operand);
            }
        }
        // Parenthesized group: ( or_expr )
        if ((this.peek() === "(")) {
            this.advance();
            var inner = this.ParseCondOr();
            this.CondSkipWhitespace();
            if ((this.atEnd() || (this.peek() !== ")"))) {
                throw new ParseError("Expected ) in conditional expression", this.pos);
            }
            this.advance();
            return new CondParen(inner);
        }
        // Parse first word
        var word1 = this.ParseCondWord();
        if ((word1 == null)) {
            throw new ParseError("Expected word in conditional expression", this.pos);
        }
        this.CondSkipWhitespace();
        // Check if word1 is a unary operator
        if (IsCondUnaryOp(word1.value)) {
            // Unary test: -f file
            operand = this.ParseCondWord();
            if ((operand == null)) {
                throw new ParseError(("Expected operand after " + word1.value), this.pos);
            }
            return new UnaryTest(word1.value, operand);
        }
        // Check if next token is a binary operator
        if ((!this.CondAtEnd() && ((this.peek() !== "&") && (this.peek() !== "|") && (this.peek() !== ")")))) {
            // Handle < and > as binary operators (they terminate words)
            // But not <( or >( which are process substitution
            if ((IsRedirectChar(this.peek()) && !(((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "(")))) {
                var op = this.advance();
                this.CondSkipWhitespace();
                var word2 = this.ParseCondWord();
                if ((word2 == null)) {
                    throw new ParseError(("Expected operand after " + op), this.pos);
                }
                return new BinaryTest(op, word1, word2);
            }
            // Peek at next word to see if it's a binary operator
            var saved_pos = this.pos;
            var op_word = this.ParseCondWord();
            if ((op_word && IsCondBinaryOp(op_word.value))) {
                // Binary test: word1 op word2
                this.CondSkipWhitespace();
                // For =~ operator, the RHS is a regex where ( ) are grouping, not conditional grouping
                if ((op_word.value === "=~")) {
                    word2 = this.ParseCondRegexWord();
                } else {
                    word2 = this.ParseCondWord();
                }
                if ((word2 == null)) {
                    throw new ParseError(("Expected operand after " + op_word.value), this.pos);
                }
                return new BinaryTest(op_word.value, word1, word2);
            } else {
                // Not a binary op, restore position
                this.pos = saved_pos;
            }
        }
        // Bare word: implicit -n test
        return new UnaryTest("-n", word1);
    }
    
    ParseCondWord() {
        this.CondSkipWhitespace();
        if (this.CondAtEnd()) {
            return null;
        }
        // Check for special tokens that aren't words
        var c = this.peek();
        if (IsParen(c)) {
            return null;
        }
        // Note: ! alone is handled by _parse_cond_term() as negation operator
        // Here we allow ! as a word so it can be used as pattern in binary tests
        if (((c === "&") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "&"))) {
            return null;
        }
        if (((c === "|") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "|"))) {
            return null;
        }
        var start = this.pos;
        var chars = [];
        var parts = [];
        while (!this.atEnd()) {
            var ch = this.peek();
            // End of conditional
            if (((ch === "]") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "]"))) {
                break;
            }
            // Word terminators in conditionals
            if (IsWhitespaceNoNewline(ch)) {
                break;
            }
            // < and > are string comparison operators in [[ ]], terminate words
            // But <(...) and >(...) are process substitution - don't break
            if ((IsRedirectChar(ch) && !(((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "(")))) {
                break;
            }
            // ( and ) end words unless part of extended glob: @(...), ?(...), *(...), +(...), !(...)
            if ((ch === "(")) {
                // Check if this is an extended glob (preceded by @, ?, *, +, or !)
                if ((chars.length > 0 && IsExtglobPrefix(chars[(chars.length - 1)]))) {
                    // Extended glob - consume the parenthesized content
                    chars.push(this.advance());
                    var depth = 1;
                    while ((!this.atEnd() && (depth > 0))) {
                        c = this.peek();
                        if ((c === "(")) {
                            depth += 1;
                        } else if ((c === ")")) {
                            depth -= 1;
                        }
                        chars.push(this.advance());
                    }
                    continue;
                } else {
                    break;
                }
            }
            if ((ch === ")")) {
                break;
            }
            if (((ch === "&") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "&"))) {
                break;
            }
            if (((ch === "|") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "|"))) {
                break;
            }
            // Single-quoted string
            if ((ch === "'")) {
                this.advance();
                chars.push("'");
                while ((!this.atEnd() && (this.peek() !== "'"))) {
                    chars.push(this.advance());
                }
                if (this.atEnd()) {
                    throw new ParseError("Unterminated single quote", start);
                }
                chars.push(this.advance());
            } else if ((ch === "\"")) {
                // Double-quoted string
                this.advance();
                chars.push("\"");
                while ((!this.atEnd() && (this.peek() !== "\""))) {
                    c = this.peek();
                    if (((c === "\\") && ((this.pos + 1) < this.length))) {
                        var next_c = this.source[(this.pos + 1)];
                        if ((next_c === "\n")) {
                            // Line continuation - skip both backslash and newline
                            this.advance();
                            this.advance();
                        } else {
                            chars.push(this.advance());
                            chars.push(this.advance());
                        }
                    } else if ((c === "$")) {
                        // Handle expansions inside double quotes
                        if ((((this.pos + 2) < this.length) && (this.source[(this.pos + 1)] === "(") && (this.source[(this.pos + 2)] === "("))) {
                            var arith_result = this.ParseArithmeticExpansion();
                            var arith_node = arith_result[0];
                            var arith_text = arith_result[1];
                            if (arith_node) {
                                parts.push(arith_node);
                                chars.push(arith_text);
                            } else {
                                // Not arithmetic - try command substitution
                                var cmdsub_result = this.ParseCommandSubstitution();
                                var cmdsub_node = cmdsub_result[0];
                                var cmdsub_text = cmdsub_result[1];
                                if (cmdsub_node) {
                                    parts.push(cmdsub_node);
                                    chars.push(cmdsub_text);
                                } else {
                                    chars.push(this.advance());
                                }
                            }
                        } else if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                            cmdsub_result = this.ParseCommandSubstitution();
                            cmdsub_node = cmdsub_result[0];
                            cmdsub_text = cmdsub_result[1];
                            if (cmdsub_node) {
                                parts.push(cmdsub_node);
                                chars.push(cmdsub_text);
                            } else {
                                chars.push(this.advance());
                            }
                        } else {
                            var param_result = this.ParseParamExpansion();
                            var param_node = param_result[0];
                            var param_text = param_result[1];
                            if (param_node) {
                                parts.push(param_node);
                                chars.push(param_text);
                            } else {
                                chars.push(this.advance());
                            }
                        }
                    } else {
                        chars.push(this.advance());
                    }
                }
                if (this.atEnd()) {
                    throw new ParseError("Unterminated double quote", start);
                }
                chars.push(this.advance());
            } else if (((ch === "\\") && ((this.pos + 1) < this.length))) {
                // Escape
                chars.push(this.advance());
                chars.push(this.advance());
            } else if (((ch === "$") && ((this.pos + 2) < this.length) && (this.source[(this.pos + 1)] === "(") && (this.source[(this.pos + 2)] === "("))) {
                // Arithmetic expansion $((...))
                arith_result = this.ParseArithmeticExpansion();
                arith_node = arith_result[0];
                arith_text = arith_result[1];
                if (arith_node) {
                    parts.push(arith_node);
                    chars.push(arith_text);
                } else {
                    chars.push(this.advance());
                }
            } else if (((ch === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                // Command substitution $(...)
                cmdsub_result = this.ParseCommandSubstitution();
                cmdsub_node = cmdsub_result[0];
                cmdsub_text = cmdsub_result[1];
                if (cmdsub_node) {
                    parts.push(cmdsub_node);
                    chars.push(cmdsub_text);
                } else {
                    chars.push(this.advance());
                }
            } else if ((ch === "$")) {
                // Parameter expansion $var or ${...}
                param_result = this.ParseParamExpansion();
                param_node = param_result[0];
                param_text = param_result[1];
                if (param_node) {
                    parts.push(param_node);
                    chars.push(param_text);
                } else {
                    chars.push(this.advance());
                }
            } else if ((IsRedirectChar(ch) && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                // Process substitution <(...) or >(...)
                var procsub_result = this.ParseProcessSubstitution();
                var procsub_node = procsub_result[0];
                var procsub_text = procsub_result[1];
                if (procsub_node) {
                    parts.push(procsub_node);
                    chars.push(procsub_text);
                } else {
                    chars.push(this.advance());
                }
            } else if ((ch === "`")) {
                // Backtick command substitution
                cmdsub_result = this.ParseBacktickSubstitution();
                cmdsub_node = cmdsub_result[0];
                cmdsub_text = cmdsub_result[1];
                if (cmdsub_node) {
                    parts.push(cmdsub_node);
                    chars.push(cmdsub_text);
                } else {
                    chars.push(this.advance());
                }
            } else {
                // Regular character
                chars.push(this.advance());
            }
        }
        if (chars.length === 0) {
            return null;
        }
        var parts_arg = null;
        if (parts) {
            parts_arg = parts;
        }
        return new Word(chars.join(""), parts_arg);
    }
    
    ParseCondRegexWord() {
        this.CondSkipWhitespace();
        if (this.CondAtEnd()) {
            return null;
        }
        var start = this.pos;
        var chars = [];
        var parts = [];
        var paren_depth = 0;
        while (!this.atEnd()) {
            var ch = this.peek();
            // End of conditional
            if (((ch === "]") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "]"))) {
                break;
            }
            // Backslash-newline continuation (check before space/escape handling)
            if (((ch === "\\") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "\n"))) {
                this.advance();
                this.advance();
                continue;
            }
            // Escape sequences - consume both characters (including escaped spaces)
            if (((ch === "\\") && ((this.pos + 1) < this.length))) {
                chars.push(this.advance());
                chars.push(this.advance());
                continue;
            }
            // Track regex grouping parentheses
            if ((ch === "(")) {
                paren_depth += 1;
                chars.push(this.advance());
                continue;
            }
            if ((ch === ")")) {
                if ((paren_depth > 0)) {
                    paren_depth -= 1;
                    chars.push(this.advance());
                    continue;
                }
                // Unmatched ) - probably end of pattern
                break;
            }
            // Regex character class [...] - consume until closing ]
            // Handles [[:alpha:]], [^0-9], []a-z] (] as first char), etc.
            if ((ch === "[")) {
                chars.push(this.advance());
                // Handle negation [^
                if ((!this.atEnd() && (this.peek() === "^"))) {
                    chars.push(this.advance());
                }
                // Handle ] as first char (literal ])
                if ((!this.atEnd() && (this.peek() === "]"))) {
                    chars.push(this.advance());
                }
                // Consume until closing ]
                while (!this.atEnd()) {
                    var c = this.peek();
                    if ((c === "]")) {
                        chars.push(this.advance());
                        break;
                    }
                    if (((c === "[") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === ":"))) {
                        // POSIX class like [:alpha:] inside bracket expression
                        chars.push(this.advance());
                        chars.push(this.advance());
                        while ((!this.atEnd() && !((this.peek() === ":") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "]")))) {
                            chars.push(this.advance());
                        }
                        if (!this.atEnd()) {
                            chars.push(this.advance());
                            chars.push(this.advance());
                        }
                    } else {
                        chars.push(this.advance());
                    }
                }
                continue;
            }
            // Word terminators - space/tab ends the regex (unless inside parens), as do && and ||
            if ((IsWhitespace(ch) && (paren_depth === 0))) {
                break;
            }
            if ((IsWhitespace(ch) && (paren_depth > 0))) {
                // Space inside regex parens is part of the pattern
                chars.push(this.advance());
                continue;
            }
            if (((ch === "&") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "&"))) {
                break;
            }
            if (((ch === "|") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "|"))) {
                break;
            }
            // Single-quoted string
            if ((ch === "'")) {
                this.advance();
                chars.push("'");
                while ((!this.atEnd() && (this.peek() !== "'"))) {
                    chars.push(this.advance());
                }
                if (this.atEnd()) {
                    throw new ParseError("Unterminated single quote", start);
                }
                chars.push(this.advance());
                continue;
            }
            // Double-quoted string
            if ((ch === "\"")) {
                this.advance();
                chars.push("\"");
                while ((!this.atEnd() && (this.peek() !== "\""))) {
                    c = this.peek();
                    if (((c === "\\") && ((this.pos + 1) < this.length))) {
                        chars.push(this.advance());
                        chars.push(this.advance());
                    } else if ((c === "$")) {
                        var param_result = this.ParseParamExpansion();
                        var param_node = param_result[0];
                        var param_text = param_result[1];
                        if (param_node) {
                            parts.push(param_node);
                            chars.push(param_text);
                        } else {
                            chars.push(this.advance());
                        }
                    } else {
                        chars.push(this.advance());
                    }
                }
                if (this.atEnd()) {
                    throw new ParseError("Unterminated double quote", start);
                }
                chars.push(this.advance());
                continue;
            }
            // Command substitution $(...) or parameter expansion $var or ${...}
            if ((ch === "$")) {
                // Try command substitution first
                if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                    var cmdsub_result = this.ParseCommandSubstitution();
                    var cmdsub_node = cmdsub_result[0];
                    var cmdsub_text = cmdsub_result[1];
                    if (cmdsub_node) {
                        parts.push(cmdsub_node);
                        chars.push(cmdsub_text);
                        continue;
                    }
                }
                param_result = this.ParseParamExpansion();
                param_node = param_result[0];
                param_text = param_result[1];
                if (param_node) {
                    parts.push(param_node);
                    chars.push(param_text);
                } else {
                    chars.push(this.advance());
                }
                continue;
            }
            // Regular character (including ( ) which are regex grouping)
            chars.push(this.advance());
        }
        if (chars.length === 0) {
            return null;
        }
        var parts_arg = null;
        if (parts) {
            parts_arg = parts;
        }
        return new Word(chars.join(""), parts_arg);
    }
    
    parseBraceGroup() {
        this.skipWhitespace();
        if ((this.atEnd() || (this.peek() !== "{"))) {
            return null;
        }
        // Check that { is followed by whitespace (it's a reserved word)
        if ((((this.pos + 1) < this.length) && !IsWhitespace(this.source[(this.pos + 1)]))) {
            return null;
        }
        this.advance();
        this.skipWhitespaceAndNewlines();
        var body = this.parseList();
        if ((body == null)) {
            throw new ParseError("Expected command in brace group", this.pos);
        }
        this.skipWhitespace();
        if ((this.atEnd() || (this.peek() !== "}"))) {
            throw new ParseError("Expected } to close brace group", this.pos);
        }
        this.advance();
        // Collect trailing redirects
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new BraceGroup(body, redir_arg);
    }
    
    parseIf() {
        this.skipWhitespace();
        // Check for 'if' keyword
        if ((this.peekWord() !== "if")) {
            return null;
        }
        this.consumeWord("if");
        // Parse condition (a list that ends at 'then')
        var condition = this.parseListUntil(new Set(["then"]));
        if ((condition == null)) {
            throw new ParseError("Expected condition after 'if'", this.pos);
        }
        // Expect 'then'
        this.skipWhitespaceAndNewlines();
        if (!this.consumeWord("then")) {
            throw new ParseError("Expected 'then' after if condition", this.pos);
        }
        // Parse then body (ends at elif, else, or fi)
        var then_body = this.parseListUntil(new Set(["elif", "else", "fi"]));
        if ((then_body == null)) {
            throw new ParseError("Expected commands after 'then'", this.pos);
        }
        // Check what comes next: elif, else, or fi
        this.skipWhitespaceAndNewlines();
        var next_word = this.peekWord();
        var else_body = null;
        if ((next_word === "elif")) {
            // elif is syntactic sugar for else if ... fi
            this.consumeWord("elif");
            // Parse the rest as a nested if (but we've already consumed 'elif')
            // We need to parse: condition; then body [elif|else|fi]
            var elif_condition = this.parseListUntil(new Set(["then"]));
            if ((elif_condition == null)) {
                throw new ParseError("Expected condition after 'elif'", this.pos);
            }
            this.skipWhitespaceAndNewlines();
            if (!this.consumeWord("then")) {
                throw new ParseError("Expected 'then' after elif condition", this.pos);
            }
            var elif_then_body = this.parseListUntil(new Set(["elif", "else", "fi"]));
            if ((elif_then_body == null)) {
                throw new ParseError("Expected commands after 'then'", this.pos);
            }
            // Recursively handle more elif/else/fi
            this.skipWhitespaceAndNewlines();
            var inner_next = this.peekWord();
            var inner_else = null;
            if ((inner_next === "elif")) {
                // More elif - recurse by creating a fake "if" and parsing
                // Actually, let's just recursively call a helper
                inner_else = this.ParseElifChain();
            } else if ((inner_next === "else")) {
                this.consumeWord("else");
                inner_else = this.parseListUntil(new Set(["fi"]));
                if ((inner_else == null)) {
                    throw new ParseError("Expected commands after 'else'", this.pos);
                }
            }
            else_body = new If(elif_condition, elif_then_body, inner_else);
        } else if ((next_word === "else")) {
            this.consumeWord("else");
            else_body = this.parseListUntil(new Set(["fi"]));
            if ((else_body == null)) {
                throw new ParseError("Expected commands after 'else'", this.pos);
            }
        }
        // Expect 'fi'
        this.skipWhitespaceAndNewlines();
        if (!this.consumeWord("fi")) {
            throw new ParseError("Expected 'fi' to close if statement", this.pos);
        }
        // Parse optional trailing redirections
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new If(condition, then_body, else_body, redir_arg);
    }
    
    ParseElifChain() {
        this.consumeWord("elif");
        var condition = this.parseListUntil(new Set(["then"]));
        if ((condition == null)) {
            throw new ParseError("Expected condition after 'elif'", this.pos);
        }
        this.skipWhitespaceAndNewlines();
        if (!this.consumeWord("then")) {
            throw new ParseError("Expected 'then' after elif condition", this.pos);
        }
        var then_body = this.parseListUntil(new Set(["elif", "else", "fi"]));
        if ((then_body == null)) {
            throw new ParseError("Expected commands after 'then'", this.pos);
        }
        this.skipWhitespaceAndNewlines();
        var next_word = this.peekWord();
        var else_body = null;
        if ((next_word === "elif")) {
            else_body = this.ParseElifChain();
        } else if ((next_word === "else")) {
            this.consumeWord("else");
            else_body = this.parseListUntil(new Set(["fi"]));
            if ((else_body == null)) {
                throw new ParseError("Expected commands after 'else'", this.pos);
            }
        }
        return new If(condition, then_body, else_body);
    }
    
    parseWhile() {
        this.skipWhitespace();
        if ((this.peekWord() !== "while")) {
            return null;
        }
        this.consumeWord("while");
        // Parse condition (ends at 'do')
        var condition = this.parseListUntil(new Set(["do"]));
        if ((condition == null)) {
            throw new ParseError("Expected condition after 'while'", this.pos);
        }
        // Expect 'do'
        this.skipWhitespaceAndNewlines();
        if (!this.consumeWord("do")) {
            throw new ParseError("Expected 'do' after while condition", this.pos);
        }
        // Parse body (ends at 'done')
        var body = this.parseListUntil(new Set(["done"]));
        if ((body == null)) {
            throw new ParseError("Expected commands after 'do'", this.pos);
        }
        // Expect 'done'
        this.skipWhitespaceAndNewlines();
        if (!this.consumeWord("done")) {
            throw new ParseError("Expected 'done' to close while loop", this.pos);
        }
        // Parse optional trailing redirections
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new While(condition, body, redir_arg);
    }
    
    parseUntil() {
        this.skipWhitespace();
        if ((this.peekWord() !== "until")) {
            return null;
        }
        this.consumeWord("until");
        // Parse condition (ends at 'do')
        var condition = this.parseListUntil(new Set(["do"]));
        if ((condition == null)) {
            throw new ParseError("Expected condition after 'until'", this.pos);
        }
        // Expect 'do'
        this.skipWhitespaceAndNewlines();
        if (!this.consumeWord("do")) {
            throw new ParseError("Expected 'do' after until condition", this.pos);
        }
        // Parse body (ends at 'done')
        var body = this.parseListUntil(new Set(["done"]));
        if ((body == null)) {
            throw new ParseError("Expected commands after 'do'", this.pos);
        }
        // Expect 'done'
        this.skipWhitespaceAndNewlines();
        if (!this.consumeWord("done")) {
            throw new ParseError("Expected 'done' to close until loop", this.pos);
        }
        // Parse optional trailing redirections
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new Until(condition, body, redir_arg);
    }
    
    parseFor() {
        this.skipWhitespace();
        if ((this.peekWord() !== "for")) {
            return null;
        }
        this.consumeWord("for");
        this.skipWhitespace();
        // Check for C-style for loop: for ((init; cond; incr))
        if (((this.peek() === "(") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
            return this.ParseForArith();
        }
        // Parse variable name (bash allows reserved words as variable names in for loops)
        var var_name = this.peekWord();
        if ((var_name == null)) {
            throw new ParseError("Expected variable name after 'for'", this.pos);
        }
        this.consumeWord(var_name);
        this.skipWhitespace();
        // Handle optional semicolon or newline before 'in' or 'do'
        if ((this.peek() === ";")) {
            this.advance();
        }
        this.skipWhitespaceAndNewlines();
        // Check for optional 'in' clause
        var words = null;
        if ((this.peekWord() === "in")) {
            this.consumeWord("in");
            this.skipWhitespaceAndNewlines();
            // Parse words until semicolon, newline, or 'do'
            words = [];
            while (true) {
                this.skipWhitespace();
                // Check for end of word list
                if (this.atEnd()) {
                    break;
                }
                if (IsSemicolonOrNewline(this.peek())) {
                    if ((this.peek() === ";")) {
                        this.advance();
                    }
                    break;
                }
                if ((this.peekWord() === "do")) {
                    break;
                }
                var word = this.parseWord();
                if ((word == null)) {
                    break;
                }
                words.push(word);
            }
        }
        // Skip to 'do'
        this.skipWhitespaceAndNewlines();
        // Expect 'do'
        if (!this.consumeWord("do")) {
            throw new ParseError("Expected 'do' in for loop", this.pos);
        }
        // Parse body (ends at 'done')
        var body = this.parseListUntil(new Set(["done"]));
        if ((body == null)) {
            throw new ParseError("Expected commands after 'do'", this.pos);
        }
        // Expect 'done'
        this.skipWhitespaceAndNewlines();
        if (!this.consumeWord("done")) {
            throw new ParseError("Expected 'done' to close for loop", this.pos);
        }
        // Parse optional trailing redirections
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new For(var_name, words, body, redir_arg);
    }
    
    ParseForArith() {
        // We've already consumed 'for' and positioned at '(('
        this.advance();
        this.advance();
        // Parse the three expressions separated by semicolons
        // Each can be empty
        var parts = [];
        var current = [];
        var paren_depth = 0;
        while (!this.atEnd()) {
            var ch = this.peek();
            if ((ch === "(")) {
                paren_depth += 1;
                current.push(this.advance());
            } else if ((ch === ")")) {
                if ((paren_depth > 0)) {
                    paren_depth -= 1;
                    current.push(this.advance());
                } else if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === ")"))) {
                    // Check for closing ))
                    // End of ((...)) - preserve trailing whitespace
                    parts.push(current.join("").trimStart());
                    this.advance();
                    this.advance();
                    break;
                } else {
                    current.push(this.advance());
                }
            } else if (((ch === ";") && (paren_depth === 0))) {
                // Preserve trailing whitespace in expressions
                parts.push(current.join("").trimStart());
                current = [];
                this.advance();
            } else {
                current.push(this.advance());
            }
        }
        if ((parts.length !== 3)) {
            throw new ParseError("Expected three expressions in for ((;;))", this.pos);
        }
        var init = parts[0];
        var cond = parts[1];
        var incr = parts[2];
        this.skipWhitespace();
        // Handle optional semicolon
        if ((!this.atEnd() && (this.peek() === ";"))) {
            this.advance();
        }
        this.skipWhitespaceAndNewlines();
        // Parse body - either do/done or brace group
        if ((this.peek() === "{")) {
            var brace = this.parseBraceGroup();
            if ((brace == null)) {
                throw new ParseError("Expected brace group body in for loop", this.pos);
            }
            // Unwrap the brace-group to match bash-oracle output format
            var body = brace.body;
        } else if (this.consumeWord("do")) {
            body = this.parseListUntil(new Set(["done"]));
            if ((body == null)) {
                throw new ParseError("Expected commands after 'do'", this.pos);
            }
            this.skipWhitespaceAndNewlines();
            if (!this.consumeWord("done")) {
                throw new ParseError("Expected 'done' to close for loop", this.pos);
            }
        } else {
            throw new ParseError("Expected 'do' or '{' in for loop", this.pos);
        }
        // Parse optional trailing redirections
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new ForArith(init, cond, incr, body, redir_arg);
    }
    
    parseSelect() {
        this.skipWhitespace();
        if ((this.peekWord() !== "select")) {
            return null;
        }
        this.consumeWord("select");
        this.skipWhitespace();
        // Parse variable name
        var var_name = this.peekWord();
        if ((var_name == null)) {
            throw new ParseError("Expected variable name after 'select'", this.pos);
        }
        this.consumeWord(var_name);
        this.skipWhitespace();
        // Handle optional semicolon before 'in', 'do', or '{'
        if ((this.peek() === ";")) {
            this.advance();
        }
        this.skipWhitespaceAndNewlines();
        // Check for optional 'in' clause
        var words = null;
        if ((this.peekWord() === "in")) {
            this.consumeWord("in");
            this.skipWhitespaceAndNewlines();
            // Parse words until semicolon, newline, 'do', or '{'
            words = [];
            while (true) {
                this.skipWhitespace();
                // Check for end of word list
                if (this.atEnd()) {
                    break;
                }
                if (IsSemicolonNewlineBrace(this.peek())) {
                    if ((this.peek() === ";")) {
                        this.advance();
                    }
                    break;
                }
                if ((this.peekWord() === "do")) {
                    break;
                }
                var word = this.parseWord();
                if ((word == null)) {
                    break;
                }
                words.push(word);
            }
        }
        // Empty word list is allowed for select (unlike for)
        // Skip whitespace before body
        this.skipWhitespaceAndNewlines();
        // Parse body - either do/done or brace group
        if ((this.peek() === "{")) {
            var brace = this.parseBraceGroup();
            if ((brace == null)) {
                throw new ParseError("Expected brace group body in select", this.pos);
            }
            // Unwrap the brace-group to match bash-oracle output format
            var body = brace.body;
        } else if (this.consumeWord("do")) {
            // Parse body (ends at 'done')
            body = this.parseListUntil(new Set(["done"]));
            if ((body == null)) {
                throw new ParseError("Expected commands after 'do'", this.pos);
            }
            // Expect 'done'
            this.skipWhitespaceAndNewlines();
            if (!this.consumeWord("done")) {
                throw new ParseError("Expected 'done' to close select", this.pos);
            }
        } else {
            throw new ParseError("Expected 'do' or '{' in select", this.pos);
        }
        // Parse optional trailing redirections
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new Select(var_name, words, body, redir_arg);
    }
    
    IsCaseTerminator() {
        if ((this.atEnd() || (this.peek() !== ";"))) {
            return false;
        }
        if (((this.pos + 1) >= this.length)) {
            return false;
        }
        var next_ch = this.source[(this.pos + 1)];
        // ;; or ;& or ;;& (which is actually ;;&)
        return IsSemicolonOrAmp(next_ch);
    }
    
    ConsumeCaseTerminator() {
        if ((this.atEnd() || (this.peek() !== ";"))) {
            return ";;";
        }
        this.advance();
        if (this.atEnd()) {
            return ";;";
        }
        var ch = this.peek();
        if ((ch === ";")) {
            this.advance();
            // Check for ;;&
            if ((!this.atEnd() && (this.peek() === "&"))) {
                this.advance();
                return ";;&";
            }
            return ";;";
        } else if ((ch === "&")) {
            this.advance();
            return ";&";
        }
        return ";;";
    }
    
    parseCase() {
        this.skipWhitespace();
        if ((this.peekWord() !== "case")) {
            return null;
        }
        this.consumeWord("case");
        this.skipWhitespace();
        // Parse the word to match
        var word = this.parseWord();
        if ((word == null)) {
            throw new ParseError("Expected word after 'case'", this.pos);
        }
        this.skipWhitespaceAndNewlines();
        // Expect 'in'
        if (!this.consumeWord("in")) {
            throw new ParseError("Expected 'in' after case word", this.pos);
        }
        this.skipWhitespaceAndNewlines();
        // Parse pattern clauses until 'esac'
        var patterns = [];
        while (true) {
            this.skipWhitespaceAndNewlines();
            // Check if we're at 'esac' (but not 'esac)' which is esac as a pattern)
            if ((this.peekWord() === "esac")) {
                // Look ahead to see if esac is a pattern (esac followed by ) then body/;;)
                // or the closing keyword (esac followed by ) that closes containing construct)
                var saved = this.pos;
                this.skipWhitespace();
                // Consume "esac"
                while ((!this.atEnd() && !IsMetachar(this.peek()) && !IsQuote(this.peek()))) {
                    this.advance();
                }
                this.skipWhitespace();
                // Check for ) and what follows
                var is_pattern = false;
                if ((!this.atEnd() && (this.peek() === ")"))) {
                    this.advance();
                    this.skipWhitespace();
                    // esac is a pattern if there's body content or ;; after )
                    // Not a pattern if ) is followed by end, newline, or another )
                    if (!this.atEnd()) {
                        var next_ch = this.peek();
                        // If followed by ;; or actual command content, it's a pattern
                        if ((next_ch === ";")) {
                            is_pattern = true;
                        } else if (!IsNewlineOrRightParen(next_ch)) {
                            is_pattern = true;
                        }
                    }
                }
                this.pos = saved;
                if (!is_pattern) {
                    break;
                }
            }
            // Skip optional leading ( before pattern (POSIX allows this)
            this.skipWhitespaceAndNewlines();
            if ((!this.atEnd() && (this.peek() === "("))) {
                this.advance();
                this.skipWhitespaceAndNewlines();
            }
            // Parse pattern (everything until ')' at depth 0)
            // Pattern can contain | for alternation, quotes, globs, extglobs, etc.
            // Extglob patterns @(), ?(), *(), +(), !() contain nested parens
            var pattern_chars = [];
            var extglob_depth = 0;
            while (!this.atEnd()) {
                var ch = this.peek();
                if ((ch === ")")) {
                    if ((extglob_depth > 0)) {
                        // Inside extglob, consume the ) and decrement depth
                        pattern_chars.push(this.advance());
                        extglob_depth -= 1;
                    } else {
                        // End of pattern
                        this.advance();
                        break;
                    }
                } else if ((ch === "\\")) {
                    // Line continuation or backslash escape
                    if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "\n"))) {
                        // Line continuation - skip both backslash and newline
                        this.advance();
                        this.advance();
                    } else {
                        // Normal escape - consume both chars
                        pattern_chars.push(this.advance());
                        if (!this.atEnd()) {
                            pattern_chars.push(this.advance());
                        }
                    }
                } else if (((ch === "$") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                    // $( or $(( - command sub or arithmetic
                    pattern_chars.push(this.advance());
                    pattern_chars.push(this.advance());
                    if ((!this.atEnd() && (this.peek() === "("))) {
                        // $(( arithmetic - need to find matching ))
                        pattern_chars.push(this.advance());
                        var paren_depth = 2;
                        while ((!this.atEnd() && (paren_depth > 0))) {
                            var c = this.peek();
                            if ((c === "(")) {
                                paren_depth += 1;
                            } else if ((c === ")")) {
                                paren_depth -= 1;
                            }
                            pattern_chars.push(this.advance());
                        }
                    } else {
                        // $() command sub - track single paren
                        extglob_depth += 1;
                    }
                } else if (((ch === "(") && (extglob_depth > 0))) {
                    // Grouping paren inside extglob
                    pattern_chars.push(this.advance());
                    extglob_depth += 1;
                } else if ((IsExtglobPrefix(ch) && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                    // Extglob opener: @(, ?(, *(, +(, !(
                    pattern_chars.push(this.advance());
                    pattern_chars.push(this.advance());
                    extglob_depth += 1;
                } else if ((ch === "[")) {
                    // Character class - but only if there's a matching ]
                    // ] must come before ) at same depth (either extglob or pattern)
                    var is_char_class = false;
                    var scan_pos = (this.pos + 1);
                    var scan_depth = 0;
                    var has_first_bracket_literal = false;
                    // Skip [! or [^ at start
                    if (((scan_pos < this.length) && IsCaretOrBang(this.source[scan_pos]))) {
                        scan_pos += 1;
                    }
                    // Skip ] as first char (literal in char class) only if there's another ]
                    if (((scan_pos < this.length) && (this.source[scan_pos] === "]"))) {
                        // Check if there's another ] later
                        if ((this.source.indexOf("]", (scan_pos + 1)) !== -1)) {
                            scan_pos += 1;
                            has_first_bracket_literal = true;
                        }
                    }
                    while ((scan_pos < this.length)) {
                        var sc = this.source[scan_pos];
                        if (((sc === "]") && (scan_depth === 0))) {
                            is_char_class = true;
                            break;
                        } else if ((sc === "[")) {
                            scan_depth += 1;
                        } else if (((sc === ")") && (scan_depth === 0))) {
                            // Hit pattern/extglob closer before finding ]
                            break;
                        } else if (((sc === "|") && (scan_depth === 0) && (extglob_depth > 0))) {
                            // Hit alternation in extglob - ] must be in this branch
                            break;
                        }
                        scan_pos += 1;
                    }
                    if (is_char_class) {
                        pattern_chars.push(this.advance());
                        // Handle [! or [^ at start
                        if ((!this.atEnd() && IsCaretOrBang(this.peek()))) {
                            pattern_chars.push(this.advance());
                        }
                        // Handle ] as first char (literal) only if we detected it in scan
                        if ((has_first_bracket_literal && !this.atEnd() && (this.peek() === "]"))) {
                            pattern_chars.push(this.advance());
                        }
                        // Consume until closing ]
                        while ((!this.atEnd() && (this.peek() !== "]"))) {
                            pattern_chars.push(this.advance());
                        }
                        if (!this.atEnd()) {
                            pattern_chars.push(this.advance());
                        }
                    } else {
                        // Not a valid char class, treat [ as literal
                        pattern_chars.push(this.advance());
                    }
                } else if ((ch === "'")) {
                    // Single-quoted string in pattern
                    pattern_chars.push(this.advance());
                    while ((!this.atEnd() && (this.peek() !== "'"))) {
                        pattern_chars.push(this.advance());
                    }
                    if (!this.atEnd()) {
                        pattern_chars.push(this.advance());
                    }
                } else if ((ch === "\"")) {
                    // Double-quoted string in pattern
                    pattern_chars.push(this.advance());
                    while ((!this.atEnd() && (this.peek() !== "\""))) {
                        if (((this.peek() === "\\") && ((this.pos + 1) < this.length))) {
                            pattern_chars.push(this.advance());
                        }
                        pattern_chars.push(this.advance());
                    }
                    if (!this.atEnd()) {
                        pattern_chars.push(this.advance());
                    }
                } else if (IsWhitespace(ch)) {
                    // Skip whitespace at top level, but preserve inside $() or extglob
                    if ((extglob_depth > 0)) {
                        pattern_chars.push(this.advance());
                    } else {
                        this.advance();
                    }
                } else {
                    pattern_chars.push(this.advance());
                }
            }
            var pattern = pattern_chars.join("");
            if (!pattern) {
                throw new ParseError("Expected pattern in case statement", this.pos);
            }
            // Parse commands until ;;, ;&, ;;&, or esac
            // Commands are optional (can have empty body)
            this.skipWhitespace();
            var body = null;
            // Check for empty body: terminator right after pattern
            var is_empty_body = this.IsCaseTerminator();
            if (!is_empty_body) {
                // Skip newlines and check if there's content before terminator or esac
                this.skipWhitespaceAndNewlines();
                if ((!this.atEnd() && (this.peekWord() !== "esac"))) {
                    // Check again for terminator after whitespace/newlines
                    var is_at_terminator = this.IsCaseTerminator();
                    if (!is_at_terminator) {
                        body = this.parseListUntil(new Set(["esac"]));
                        this.skipWhitespace();
                    }
                }
            }
            // Handle terminator: ;;, ;&, or ;;&
            var terminator = this.ConsumeCaseTerminator();
            this.skipWhitespaceAndNewlines();
            patterns.push(new CasePattern(pattern, body, terminator));
        }
        // Expect 'esac'
        this.skipWhitespaceAndNewlines();
        if (!this.consumeWord("esac")) {
            throw new ParseError("Expected 'esac' to close case statement", this.pos);
        }
        // Collect trailing redirects
        var redirects = [];
        while (true) {
            this.skipWhitespace();
            var redirect = this.parseRedirect();
            if ((redirect == null)) {
                break;
            }
            redirects.push(redirect);
        }
        var redir_arg = null;
        if (redirects) {
            redir_arg = redirects;
        }
        return new Case(word, patterns, redir_arg);
    }
    
    parseCoproc() {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        if ((this.peekWord() !== "coproc")) {
            return null;
        }
        this.consumeWord("coproc");
        this.skipWhitespace();
        var name = null;
        // Check for compound command directly (no NAME)
        var ch = null;
        if (!this.atEnd()) {
            ch = this.peek();
        }
        if ((ch === "{")) {
            var body = this.parseBraceGroup();
            if ((body != null)) {
                return new Coproc(body, name);
            }
        }
        if ((ch === "(")) {
            if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                body = this.parseArithmeticCommand();
                if ((body != null)) {
                    return new Coproc(body, name);
                }
            }
            body = this.parseSubshell();
            if ((body != null)) {
                return new Coproc(body, name);
            }
        }
        // Check for reserved word compounds directly
        var next_word = this.peekWord();
        if (IsCompoundKeyword(next_word)) {
            body = this.parseCompoundCommand();
            if ((body != null)) {
                return new Coproc(body, name);
            }
        }
        // Check if first word is NAME followed by compound command
        var word_start = this.pos;
        var potential_name = this.peekWord();
        if (potential_name) {
            // Skip past the potential name
            while ((!this.atEnd() && !IsMetachar(this.peek()) && !IsQuote(this.peek()))) {
                this.advance();
            }
            this.skipWhitespace();
            // Check what follows
            ch = null;
            if (!this.atEnd()) {
                ch = this.peek();
            }
            next_word = this.peekWord();
            if ((ch === "{")) {
                // NAME { ... } - extract name
                name = potential_name;
                body = this.parseBraceGroup();
                if ((body != null)) {
                    return new Coproc(body, name);
                }
            } else if ((ch === "(")) {
                // NAME ( ... ) - extract name
                name = potential_name;
                if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
                    body = this.parseArithmeticCommand();
                } else {
                    body = this.parseSubshell();
                }
                if ((body != null)) {
                    return new Coproc(body, name);
                }
            } else if (IsCompoundKeyword(next_word)) {
                // NAME followed by reserved compound - extract name
                name = potential_name;
                body = this.parseCompoundCommand();
                if ((body != null)) {
                    return new Coproc(body, name);
                }
            }
            // Not followed by compound - restore position and parse as simple command
            this.pos = word_start;
        }
        // Parse as simple command (includes any "NAME" as part of the command)
        body = this.parseCommand();
        if ((body != null)) {
            return new Coproc(body, name);
        }
        throw new ParseError("Expected command after coproc", this.pos);
    }
    
    parseFunction() {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        var saved_pos = this.pos;
        // Check for 'function' keyword form
        if ((this.peekWord() === "function")) {
            this.consumeWord("function");
            this.skipWhitespace();
            // Get function name
            var name = this.peekWord();
            if ((name == null)) {
                this.pos = saved_pos;
                return null;
            }
            this.consumeWord(name);
            this.skipWhitespace();
            // Optional () after name - but only if it's actually ()
            // and not the start of a subshell body
            if ((!this.atEnd() && (this.peek() === "("))) {
                // Check if this is () or start of subshell
                if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === ")"))) {
                    this.advance();
                    this.advance();
                }
            }
            // else: the ( is start of subshell body, don't consume
            this.skipWhitespaceAndNewlines();
            // Parse body (any compound command)
            var body = this.ParseCompoundCommand();
            if ((body == null)) {
                throw new ParseError("Expected function body", this.pos);
            }
            return new Function(name, body);
        }
        // Check for POSIX form: name()
        // We need to peek ahead to see if there's a () after the word
        name = this.peekWord();
        if (((name == null) || IsReservedWord(name))) {
            return null;
        }
        // Assignment words (containing =) are not function definitions
        if (StrContains(name, "=")) {
            return null;
        }
        // Save position after the name
        this.skipWhitespace();
        var name_start = this.pos;
        // Consume the name
        while ((!this.atEnd() && !IsMetachar(this.peek()) && !IsQuote(this.peek()) && !IsParen(this.peek()))) {
            this.advance();
        }
        name = this.source.slice(name_start, this.pos);
        if (!name) {
            this.pos = saved_pos;
            return null;
        }
        // Check for () - whitespace IS allowed between name and (
        this.skipWhitespace();
        if ((this.atEnd() || (this.peek() !== "("))) {
            this.pos = saved_pos;
            return null;
        }
        this.advance();
        this.skipWhitespace();
        if ((this.atEnd() || (this.peek() !== ")"))) {
            this.pos = saved_pos;
            return null;
        }
        this.advance();
        this.skipWhitespaceAndNewlines();
        // Parse body (any compound command)
        body = this.ParseCompoundCommand();
        if ((body == null)) {
            throw new ParseError("Expected function body", this.pos);
        }
        return new Function(name, body);
    }
    
    ParseCompoundCommand() {
        // Try each compound command type
        var result = this.parseBraceGroup();
        if (result) {
            return result;
        }
        result = this.parseSubshell();
        if (result) {
            return result;
        }
        result = this.parseConditionalExpr();
        if (result) {
            return result;
        }
        result = this.parseIf();
        if (result) {
            return result;
        }
        result = this.parseWhile();
        if (result) {
            return result;
        }
        result = this.parseUntil();
        if (result) {
            return result;
        }
        result = this.parseFor();
        if (result) {
            return result;
        }
        result = this.parseCase();
        if (result) {
            return result;
        }
        result = this.parseSelect();
        if (result) {
            return result;
        }
        return null;
    }
    
    parseListUntil(stop_words) {
        // Check if we're already at a stop word
        this.skipWhitespaceAndNewlines();
        if (stop_words.has(this.peekWord())) {
            return null;
        }
        var pipeline = this.parsePipeline();
        if ((pipeline == null)) {
            return null;
        }
        var parts = [pipeline];
        while (true) {
            // Check for newline as implicit command separator
            this.skipWhitespace();
            var has_newline = false;
            while ((!this.atEnd() && (this.peek() === "\n"))) {
                has_newline = true;
                this.advance();
                // Skip past any pending heredoc content after newline
                if (((this._pending_heredoc_end != null) && (this._pending_heredoc_end > this.pos))) {
                    this.pos = this._pending_heredoc_end;
                    this._pending_heredoc_end = null;
                }
                this.skipWhitespace();
            }
            var op = this.parseListOperator();
            // Newline acts as implicit semicolon if followed by more commands
            if (((op == null) && has_newline)) {
                // Check if there's another command (not a stop word)
                if ((!this.atEnd() && !stop_words.has(this.peekWord()) && !IsRightBracket(this.peek()))) {
                    op = "\n";
                }
            }
            if ((op == null)) {
                break;
            }
            // For & at end of list, don't require another command
            if ((op === "&")) {
                parts.push(new Operator(op));
                this.skipWhitespaceAndNewlines();
                if ((this.atEnd() || stop_words.has(this.peekWord()) || IsNewlineOrRightBracket(this.peek()))) {
                    break;
                }
            }
            // For ; - check if it's a terminator before a stop word (don't include it)
            if ((op === ";")) {
                this.skipWhitespaceAndNewlines();
                // Also check for ;;, ;&, or ;;& (case terminators)
                var at_case_terminator = ((this.peek() === ";") && ((this.pos + 1) < this.length) && IsSemicolonOrAmp(this.source[(this.pos + 1)]));
                if ((this.atEnd() || stop_words.has(this.peekWord()) || IsNewlineOrRightBracket(this.peek()) || at_case_terminator)) {
                    // Don't include trailing semicolon - it's just a terminator
                    break;
                }
                parts.push(new Operator(op));
            } else if ((op !== "&")) {
                parts.push(new Operator(op));
            }
            // Check for stop words before parsing next pipeline
            this.skipWhitespaceAndNewlines();
            // Also check for ;;, ;&, or ;;& (case terminators)
            if (stop_words.has(this.peekWord())) {
                break;
            }
            if (((this.peek() === ";") && ((this.pos + 1) < this.length) && IsSemicolonOrAmp(this.source[(this.pos + 1)]))) {
                break;
            }
            pipeline = this.parsePipeline();
            if ((pipeline == null)) {
                throw new ParseError(("Expected command after " + op), this.pos);
            }
            parts.push(pipeline);
        }
        if ((parts.length === 1)) {
            return parts[0];
        }
        return new List(parts);
    }
    
    parseCompoundCommand() {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        var ch = this.peek();
        // Arithmetic command ((...)) - check before subshell
        if (((ch === "(") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "("))) {
            var result = this.parseArithmeticCommand();
            if ((result != null)) {
                return result;
            }
        }
        // Not arithmetic (e.g., '(( x ) )' is nested subshells) - fall through
        // Subshell
        if ((ch === "(")) {
            return this.parseSubshell();
        }
        // Brace group
        if ((ch === "{")) {
            result = this.parseBraceGroup();
            if ((result != null)) {
                return result;
            }
        }
        // Fall through to simple command if not a brace group
        // Conditional expression [[ ]] - check before reserved words
        if (((ch === "[") && ((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "["))) {
            return this.parseConditionalExpr();
        }
        // Check for reserved words
        var word = this.peekWord();
        // If statement
        if ((word === "if")) {
            return this.parseIf();
        }
        // While loop
        if ((word === "while")) {
            return this.parseWhile();
        }
        // Until loop
        if ((word === "until")) {
            return this.parseUntil();
        }
        // For loop
        if ((word === "for")) {
            return this.parseFor();
        }
        // Select statement
        if ((word === "select")) {
            return this.parseSelect();
        }
        // Case statement
        if ((word === "case")) {
            return this.parseCase();
        }
        // Function definition (function keyword form)
        if ((word === "function")) {
            return this.parseFunction();
        }
        // Coproc
        if ((word === "coproc")) {
            return this.parseCoproc();
        }
        // Try POSIX function definition (name() form) before simple command
        var func = this.parseFunction();
        if ((func != null)) {
            return func;
        }
        // Simple command
        return this.parseCommand();
    }
    
    parsePipeline() {
        this.skipWhitespace();
        // Track order of prefixes: "time", "negation", or "time_negation" or "negation_time"
        var prefix_order = null;
        var time_posix = false;
        // Check for 'time' prefix first
        if ((this.peekWord() === "time")) {
            this.consumeWord("time");
            prefix_order = "time";
            this.skipWhitespace();
            // Check for -p flag
            if ((!this.atEnd() && (this.peek() === "-"))) {
                var saved = this.pos;
                this.advance();
                if ((!this.atEnd() && (this.peek() === "p"))) {
                    this.advance();
                    if ((this.atEnd() || IsWhitespace(this.peek()))) {
                        time_posix = true;
                    } else {
                        this.pos = saved;
                    }
                } else {
                    this.pos = saved;
                }
            }
            this.skipWhitespace();
            // Check for -- (end of options) - implies -p per bash-oracle
            if ((!this.atEnd() && StartsWithAt(this.source, this.pos, "--"))) {
                if ((((this.pos + 2) >= this.length) || IsWhitespace(this.source[(this.pos + 2)]))) {
                    this.advance();
                    this.advance();
                    time_posix = true;
                    this.skipWhitespace();
                }
            }
            // Skip nested time keywords (time time X collapses to time X)
            while ((this.peekWord() === "time")) {
                this.consumeWord("time");
                this.skipWhitespace();
                // Check for -p after nested time
                if ((!this.atEnd() && (this.peek() === "-"))) {
                    saved = this.pos;
                    this.advance();
                    if ((!this.atEnd() && (this.peek() === "p"))) {
                        this.advance();
                        if ((this.atEnd() || IsWhitespace(this.peek()))) {
                            time_posix = true;
                        } else {
                            this.pos = saved;
                        }
                    } else {
                        this.pos = saved;
                    }
                }
                this.skipWhitespace();
            }
            // Check for ! after time
            if ((!this.atEnd() && (this.peek() === "!"))) {
                if ((((this.pos + 1) >= this.length) || IsWhitespace(this.source[(this.pos + 1)]))) {
                    this.advance();
                    prefix_order = "time_negation";
                    this.skipWhitespace();
                }
            }
        } else if ((!this.atEnd() && (this.peek() === "!"))) {
            // Check for '!' negation prefix (if no time yet)
            if ((((this.pos + 1) >= this.length) || IsWhitespace(this.source[(this.pos + 1)]))) {
                this.advance();
                this.skipWhitespace();
                // Recursively parse pipeline to handle ! ! cmd, ! time cmd, etc.
                // Bare ! (no following command) is valid POSIX - equivalent to false
                var inner = this.parsePipeline();
                // Double negation cancels out (! ! cmd -> cmd, ! ! -> empty command)
                if (((inner != null) && (inner.kind === "negation"))) {
                    if ((inner.pipeline != null)) {
                        return inner.pipeline;
                    } else {
                        return new Command([]);
                    }
                }
                return new Negation(inner);
            }
        }
        // Parse the actual pipeline
        var result = this.ParseSimplePipeline();
        // Wrap based on prefix order
        // Note: bare time and time ! are valid (null command timing)
        if ((prefix_order === "time")) {
            result = new Time(result, time_posix);
        } else if ((prefix_order === "negation")) {
            result = new Negation(result);
        } else if ((prefix_order === "time_negation")) {
            // time ! cmd -> Negation(Time(cmd)) per bash-oracle
            result = new Time(result, time_posix);
            result = new Negation(result);
        } else if ((prefix_order === "negation_time")) {
            // ! time cmd -> Negation(Time(cmd))
            result = new Time(result, time_posix);
            result = new Negation(result);
        } else if ((result == null)) {
            // No prefix and no pipeline
            return null;
        }
        return result;
    }
    
    ParseSimplePipeline() {
        var cmd = this.parseCompoundCommand();
        if ((cmd == null)) {
            return null;
        }
        var commands = [cmd];
        while (true) {
            this.skipWhitespace();
            if ((this.atEnd() || (this.peek() !== "|"))) {
                break;
            }
            // Check it's not ||
            if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "|"))) {
                break;
            }
            this.advance();
            // Check for |& (pipe stderr)
            var is_pipe_both = false;
            if ((!this.atEnd() && (this.peek() === "&"))) {
                this.advance();
                is_pipe_both = true;
            }
            this.skipWhitespaceAndNewlines();
            // Add pipe-both marker if this is a |& pipe
            if (is_pipe_both) {
                commands.push(new PipeBoth());
            }
            cmd = this.parseCompoundCommand();
            if ((cmd == null)) {
                throw new ParseError("Expected command after |", this.pos);
            }
            commands.push(cmd);
        }
        if ((commands.length === 1)) {
            return commands[0];
        }
        return new Pipeline(commands);
    }
    
    parseListOperator() {
        this.skipWhitespace();
        if (this.atEnd()) {
            return null;
        }
        var ch = this.peek();
        if ((ch === "&")) {
            // Check if this is &> or &>> (redirect), not background operator
            if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === ">"))) {
                return null;
            }
            this.advance();
            if ((!this.atEnd() && (this.peek() === "&"))) {
                this.advance();
                return "&&";
            }
            return "&";
        }
        if ((ch === "|")) {
            if ((((this.pos + 1) < this.length) && (this.source[(this.pos + 1)] === "|"))) {
                this.advance();
                this.advance();
                return "||";
            }
            return null;
        }
        if ((ch === ";")) {
            // Don't treat ;;, ;&, or ;;& as a single semicolon (they're case terminators)
            if ((((this.pos + 1) < this.length) && IsSemicolonOrAmp(this.source[(this.pos + 1)]))) {
                return null;
            }
            this.advance();
            return ";";
        }
        return null;
    }
    
    parseList(newline_as_separator) {
        if (newline_as_separator == null) { newline_as_separator = true; }
        if (newline_as_separator) {
            this.skipWhitespaceAndNewlines();
        } else {
            this.skipWhitespace();
        }
        var pipeline = this.parsePipeline();
        if ((pipeline == null)) {
            return null;
        }
        var parts = [pipeline];
        while (true) {
            // Check for newline as implicit command separator
            this.skipWhitespace();
            var has_newline = false;
            while ((!this.atEnd() && (this.peek() === "\n"))) {
                has_newline = true;
                // If not treating newlines as separators, stop here
                if (!newline_as_separator) {
                    break;
                }
                this.advance();
                // Skip past any pending heredoc content after newline
                if (((this._pending_heredoc_end != null) && (this._pending_heredoc_end > this.pos))) {
                    this.pos = this._pending_heredoc_end;
                    this._pending_heredoc_end = null;
                }
                this.skipWhitespace();
            }
            // If we hit a newline and not treating them as separators, stop
            if ((has_newline && !newline_as_separator)) {
                break;
            }
            var op = this.parseListOperator();
            // Newline acts as implicit semicolon if followed by more commands
            if (((op == null) && has_newline)) {
                if ((!this.atEnd() && !IsRightBracket(this.peek()))) {
                    op = "\n";
                }
            }
            if ((op == null)) {
                break;
            }
            // Don't add duplicate semicolon (e.g., explicit ; followed by newline)
            if (!((op === ";") && parts && (parts[(parts.length - 1)].kind === "operator") && (parts[(parts.length - 1)].op === ";"))) {
                parts.push(new Operator(op));
            }
            // For & at end of list, don't require another command
            if ((op === "&")) {
                this.skipWhitespace();
                if ((this.atEnd() || IsRightBracket(this.peek()))) {
                    break;
                }
                // Newline after & - in compound commands, skip it (& acts as separator)
                // At top level, newline terminates (separate commands)
                if ((this.peek() === "\n")) {
                    if (newline_as_separator) {
                        this.skipWhitespaceAndNewlines();
                        if ((this.atEnd() || IsRightBracket(this.peek()))) {
                            break;
                        }
                    } else {
                        break;
                    }
                }
            }
            // For ; at end of list, don't require another command
            if ((op === ";")) {
                this.skipWhitespace();
                if ((this.atEnd() || IsRightBracket(this.peek()))) {
                    break;
                }
                // Newline after ; means continue to see if more commands follow
                if ((this.peek() === "\n")) {
                    continue;
                }
            }
            // For && and ||, allow newlines before the next command
            if (((op === "&&") || (op === "||"))) {
                this.skipWhitespaceAndNewlines();
            }
            pipeline = this.parsePipeline();
            if ((pipeline == null)) {
                throw new ParseError(("Expected command after " + op), this.pos);
            }
            parts.push(pipeline);
        }
        if ((parts.length === 1)) {
            return parts[0];
        }
        return new List(parts);
    }
    
    parseComment() {
        if ((this.atEnd() || (this.peek() !== "#"))) {
            return null;
        }
        var start = this.pos;
        while ((!this.atEnd() && (this.peek() !== "\n"))) {
            this.advance();
        }
        var text = this.source.slice(start, this.pos);
        return new Comment(text);
    }
    
    parse() {
        var source = this.source.trim();
        if (!source) {
            return [new Empty()];
        }
        var results = [];
        // Skip leading comments (bash-oracle doesn't output them)
        while (true) {
            this.skipWhitespace();
            // Skip newlines but not comments
            while ((!this.atEnd() && (this.peek() === "\n"))) {
                this.advance();
            }
            if (this.atEnd()) {
                break;
            }
            var comment = this.parseComment();
            if (!comment) {
                break;
            }
        }
        // Don't add to results - bash-oracle doesn't output comments
        // Parse statements separated by newlines as separate top-level nodes
        while (!this.atEnd()) {
            var result = this.parseList(false);
            if ((result != null)) {
                results.push(result);
            }
            this.skipWhitespace();
            // Skip newlines (and any pending heredoc content) between statements
            var found_newline = false;
            while ((!this.atEnd() && (this.peek() === "\n"))) {
                found_newline = true;
                this.advance();
                // Skip past any pending heredoc content after newline
                if (((this._pending_heredoc_end != null) && (this._pending_heredoc_end > this.pos))) {
                    this.pos = this._pending_heredoc_end;
                    this._pending_heredoc_end = null;
                }
                this.skipWhitespace();
            }
            // If no newline and not at end, we have unparsed content
            if ((!found_newline && !this.atEnd())) {
                throw new ParseError("Parser not fully implemented yet", this.pos);
            }
        }
        if (results.length === 0) {
            return [new Empty()];
        }
        return results;
    }
    
}

function parse(source) {
    var parser = new Parser(source);
    return parser.parse();
}


module.exports = { parse, ParseError };
