"Parable - A recursive descent parser for bash.";
class ParseError extends Error {
	"Raised when parsing fails.";
	constructor(message, pos, line) {
		super();
		this.message = message;
		this.pos = pos;
		this.line = line;
	}

	FormatMessage() {
		if (this.line != null && this.pos != null) {
			return (
				"Parse error at line " +
				String(this.line) +
				", position " +
				String(this.pos) +
				": " +
				this.message
			);
		} else if (this.pos != null) {
			return (
				"Parse error at position " + String(this.pos) + ": " + this.message
			);
		}
		return "Parse error: " + this.message;
	}
}

function IsHexDigit(c) {
	return (
		(c >= "0" && c <= "9") || (c >= "a" && c <= "f") || (c >= "A" && c <= "F")
	);
}

function IsOctalDigit(c) {
	return c >= "0" && c <= "7";
}

var ANSI_C_ESCAPES = {
	a: 7,
	b: 8,
	e: 27,
	E: 27,
	f: 12,
	n: 10,
	r: 13,
	t: 9,
	v: 11,
	"\\": 92,
	'"': 34,
	"?": 63,
};
function GetAnsiEscape(c) {
	"Look up simple ANSI-C escape byte value. Returns -1 if not found.";
	if (c === "a") {
		return 7;
	}
	if (c === "b") {
		return 8;
	}
	if (c === "e" || c === "E") {
		return 27;
	}
	if (c === "f") {
		return 12;
	}
	if (c === "n") {
		return 10;
	}
	if (c === "r") {
		return 13;
	}
	if (c === "t") {
		return 9;
	}
	if (c === "v") {
		return 11;
	}
	if (c === "\\") {
		return 92;
	}
	if (c === '"') {
		return 34;
	}
	if (c === "?") {
		return 63;
	}
	return -1;
}

function IsWhitespace(c) {
	return c === " " || c === "\t" || c === "\n";
}

function IsWhitespaceNoNewline(c) {
	return c === " " || c === "\t";
}

function Substring(s, start, end) {
	"Extract substring from start to end (exclusive).";
	return s.slice(start, end);
}

function StartsWithAt(s, pos, prefix) {
	"Check if s starts with prefix at position pos.";
	return s.startsWith(prefix, pos);
}

function Sublist(lst, start, end) {
	"Extract sublist from start to end (exclusive).";
	return lst.slice(start, end);
}

function RepeatStr(s, n) {
	"Repeat string s n times.";
	var result = [];
	var i = 0;
	while (i < n) {
		result.push(s);
		i += 1;
	}
	return result.join("");
}

class Node {
	"Base class for all AST nodes.";
	toSexp() {
		"Convert node to S-expression string for testing.";
		throw new Error("Not implemented");
	}
}

class Word extends Node {
	"A word token, possibly containing expansions.";
	constructor(value, parts) {
		super();
		this.kind = "word";
		this.value = value;
		if (parts == null) {
			parts = [];
		}
		this.parts = parts;
	}

	toSexp() {
		var value = this.value;
		value = this.ExpandAllAnsiCQuotes(value);
		value = this.StripLocaleStringDollars(value);
		value = this.NormalizeArrayWhitespace(value);
		value = this.FormatCommandSubstitutions(value);
		value = this.StripArithLineContinuations(value);
		value = this.DoubleCtlescSmart(value);
		value = value.replaceAll("", "");
		value = value.replaceAll("\\", "\\\\");
		var escaped = value
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n")
			.replaceAll("\t", "\\t");
		return '(word "' + escaped + '")';
	}

	AppendWithCtlesc(result, byte_val) {
		"Append byte to result (CTLESC doubling happens later in to_sexp).";
		result.push(byte_val);
	}

	DoubleCtlescSmart(value) {
		"Double CTLESC bytes unless escaped by backslash inside double quotes.";
		var result = [];
		var in_single = false;
		var in_double = false;
		for (var c of value) {
			if (c === "'" && !in_double) {
				in_single = !in_single;
			} else if (c === '"' && !in_single) {
				in_double = !in_double;
			}
			result.push(c);
			if (c === "") {
				if (in_double) {
					var bs_count = 0;
					for (var j = result.length - 2; j > -1; j--) {
						if (result[j] === "\\") {
							bs_count += 1;
						} else {
							break;
						}
					}
					if (bs_count % 2 === 0) {
						result.push("");
					}
				} else {
					result.push("");
				}
			}
		}
		return result.join("");
	}

	ExpandAnsiCEscapes(value) {
		"Expand ANSI-C escape sequences in $'...' strings.\n\n        Uses bytes internally so \\x escapes can form valid UTF-8 sequences.\n        Invalid UTF-8 is replaced with U+FFFD.\n        ";
		if (!(value.startsWith("'") && value.endsWith("'"))) {
			return value;
		}
		var inner = Substring(value, 1, value.length - 1);
		var result = [];
		var i = 0;
		while (i < inner.length) {
			if (inner[i] === "\\" && i + 1 < inner.length) {
				var c = inner[i + 1];
				var simple = GetAnsiEscape(c);
				if (simple >= 0) {
					result.push(simple);
					i += 2;
				} else if (c === "'") {
					result.push(...[39, 92, 39, 39]);
					i += 2;
				} else if (c === "x") {
					if (i + 2 < inner.length && inner[i + 2] === "{") {
						var j = i + 3;
						while (j < inner.length && IsHexDigit(inner[j])) {
							j += 1;
						}
						var hex_str = Substring(inner, i + 3, j);
						if (j < inner.length && inner[j] === "}") {
							j += 1;
						}
						if (!hex_str) {
							return (
								"'" + new TextDecoder().decode(new Uint8Array(result)) + "'"
							);
						}
						var byte_val = parseInt(hex_str, 16, 10) & 255;
						if (byte_val === 0) {
							return (
								"'" + new TextDecoder().decode(new Uint8Array(result)) + "'"
							);
						}
						this.AppendWithCtlesc(result, byte_val);
						i = j;
					} else {
						j = i + 2;
						while (j < inner.length && j < i + 4 && IsHexDigit(inner[j])) {
							j += 1;
						}
						if (j > i + 2) {
							byte_val = parseInt(Substring(inner, i + 2, j), 16, 10);
							if (byte_val === 0) {
								return (
									"'" + new TextDecoder().decode(new Uint8Array(result)) + "'"
								);
							}
							this.AppendWithCtlesc(result, byte_val);
							i = j;
						} else {
							result.push(inner[i].charCodeAt(0));
							i += 1;
						}
					}
				} else if (c === "u") {
					j = i + 2;
					while (j < inner.length && j < i + 6 && IsHexDigit(inner[j])) {
						j += 1;
					}
					if (j > i + 2) {
						var codepoint = parseInt(Substring(inner, i + 2, j), 16, 10);
						if (codepoint === 0) {
							return (
								"'" + new TextDecoder().decode(new Uint8Array(result)) + "'"
							);
						}
						result.push(
							...Array.from(
								new TextEncoder().encode(String.fromCodePoint(codepoint)),
							),
						);
						i = j;
					} else {
						result.push(inner[i].charCodeAt(0));
						i += 1;
					}
				} else if (c === "U") {
					j = i + 2;
					while (j < inner.length && j < i + 10 && IsHexDigit(inner[j])) {
						j += 1;
					}
					if (j > i + 2) {
						codepoint = parseInt(Substring(inner, i + 2, j), 16, 10);
						if (codepoint === 0) {
							return (
								"'" + new TextDecoder().decode(new Uint8Array(result)) + "'"
							);
						}
						result.push(
							...Array.from(
								new TextEncoder().encode(String.fromCodePoint(codepoint)),
							),
						);
						i = j;
					} else {
						result.push(inner[i].charCodeAt(0));
						i += 1;
					}
				} else if (c === "c") {
					if (i + 3 <= inner.length) {
						var ctrl_char = inner[i + 2];
						var ctrl_val = ctrl_char.charCodeAt(0) & 31;
						if (ctrl_val === 0) {
							return (
								"'" + new TextDecoder().decode(new Uint8Array(result)) + "'"
							);
						}
						this.AppendWithCtlesc(result, ctrl_val);
						i += 3;
					} else {
						result.push(inner[i].charCodeAt(0));
						i += 1;
					}
				} else if (c === "0") {
					j = i + 2;
					while (j < inner.length && j < i + 5 && IsOctalDigit(inner[j])) {
						j += 1;
					}
					if (j > i + 2) {
						byte_val = parseInt(Substring(inner, i + 1, j), 8, 10);
						if (byte_val === 0) {
							return (
								"'" + new TextDecoder().decode(new Uint8Array(result)) + "'"
							);
						}
						this.AppendWithCtlesc(result, byte_val);
						i = j;
					} else {
						return "'" + new TextDecoder().decode(new Uint8Array(result)) + "'";
					}
				} else if (c >= "1" && c <= "7") {
					j = i + 1;
					while (j < inner.length && j < i + 4 && IsOctalDigit(inner[j])) {
						j += 1;
					}
					byte_val = parseInt(Substring(inner, i + 1, j), 8, 10);
					if (byte_val === 0) {
						return "'" + new TextDecoder().decode(new Uint8Array(result)) + "'";
					}
					this.AppendWithCtlesc(result, byte_val);
					i = j;
				} else {
					result.push(92);
					result.push(c.charCodeAt(0));
					i += 2;
				}
			} else {
				result.push(...Array.from(new TextEncoder().encode(inner[i])));
				i += 1;
			}
		}
		return "'" + new TextDecoder().decode(new Uint8Array(result)) + "'";
	}

	ExpandAllAnsiCQuotes(value) {
		"Find and expand ALL $'...' ANSI-C quoted strings in value.";
		var result = [];
		var i = 0;
		var in_single_quote = false;
		var in_double_quote = false;
		var brace_depth = 0;
		while (i < value.length) {
			var ch = value[i];
			if (!in_single_quote) {
				if (StartsWithAt(value, i, "${")) {
					brace_depth += 1;
					result.push("${");
					i += 2;
					continue;
				} else if (ch === "}" && brace_depth > 0) {
					brace_depth -= 1;
					result.push(ch);
					i += 1;
					continue;
				}
			}
			var effective_in_dquote = in_double_quote && brace_depth === 0;
			if (ch === "'" && !effective_in_dquote) {
				if (!in_single_quote && i > 0 && value[i - 1] === "$") {
					result.push(ch);
					i += 1;
				} else if (in_single_quote) {
					in_single_quote = false;
					result.push(ch);
					i += 1;
				} else {
					in_single_quote = true;
					result.push(ch);
					i += 1;
				}
			} else if (ch === '"' && !in_single_quote) {
				in_double_quote = !in_double_quote;
				result.push(ch);
				i += 1;
			} else if (ch === "\\" && i + 1 < value.length && !in_single_quote) {
				result.push(ch);
				result.push(value[i + 1]);
				i += 2;
			} else if (
				StartsWithAt(value, i, "$'") &&
				!in_single_quote &&
				!effective_in_dquote
			) {
				var j = i + 2;
				while (j < value.length) {
					if (value[j] === "\\" && j + 1 < value.length) {
						j += 2;
					} else if (value[j] === "'") {
						j += 1;
						break;
					} else {
						j += 1;
					}
				}
				var ansi_str = Substring(value, i, j);
				var expanded = this.ExpandAnsiCEscapes(
					Substring(ansi_str, 1, ansi_str.length),
				);
				if (
					brace_depth > 0 &&
					expanded.startsWith("'") &&
					expanded.endsWith("'")
				) {
					var inner = Substring(expanded, 1, expanded.length - 1);
					if (inner && inner.indexOf("") === -1) {
						if (result.length >= 2) {
							var prev = Sublist(result, result.length - 2, result.length).join(
								"",
							);
						} else {
							prev = "";
						}
						if (
							prev.endsWith(":-") ||
							prev.endsWith(":=") ||
							prev.endsWith(":+") ||
							prev.endsWith(":?")
						) {
							expanded = inner;
						} else if (result.length >= 1) {
							var last = result[result.length - 1];
							if (
								(last === "-" ||
									last === "=" ||
									last === "+" ||
									last === "?") &&
								(result.length < 2 || result[result.length - 2] !== ":")
							) {
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
		"Strip $ from locale strings $\"...\" while tracking quote context.";
		var result = [];
		var i = 0;
		var in_single_quote = false;
		var in_double_quote = false;
		while (i < value.length) {
			var ch = value[i];
			if (ch === "'" && !in_double_quote) {
				in_single_quote = !in_single_quote;
				result.push(ch);
				i += 1;
			} else if (ch === '"' && !in_single_quote) {
				in_double_quote = !in_double_quote;
				result.push(ch);
				i += 1;
			} else if (ch === "\\" && i + 1 < value.length) {
				result.push(ch);
				result.push(value[i + 1]);
				i += 2;
			} else if (
				StartsWithAt(value, i, '$"') &&
				!in_single_quote &&
				!in_double_quote
			) {
				result.push('"');
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
		"Normalize whitespace inside array assignments: arr=(a  b\tc) -> arr=(a b c).";
		if (!value.endsWith(")")) {
			return value;
		}
		var i = 0;
		if (
			!(i < value.length && (/^[a-zA-Z]$/.test(value[i]) || value[i] === "_"))
		) {
			return value;
		}
		i += 1;
		while (
			i < value.length &&
			(/^[a-zA-Z0-9]$/.test(value[i]) || value[i] === "_")
		) {
			i += 1;
		}
		if (i < value.length && value[i] === "+") {
			i += 1;
		}
		if (!(i + 1 < value.length && value[i] === "=" && value[i + 1] === "(")) {
			return value;
		}
		var prefix = Substring(value, 0, i + 1);
		var inner = Substring(value, prefix.length + 1, value.length - 1);
		var normalized = [];
		i = 0;
		var in_whitespace = true;
		while (i < inner.length) {
			var ch = inner[i];
			if (IsWhitespace(ch)) {
				if (!in_whitespace && normalized) {
					normalized.push(" ");
					in_whitespace = true;
				}
				i += 1;
			} else if (ch === "'") {
				in_whitespace = false;
				var j = i + 1;
				while (j < inner.length && inner[j] !== "'") {
					j += 1;
				}
				normalized.push(Substring(inner, i, j + 1));
				i = j + 1;
			} else if (ch === '"') {
				in_whitespace = false;
				j = i + 1;
				while (j < inner.length) {
					if (inner[j] === "\\" && j + 1 < inner.length) {
						j += 2;
					} else if (inner[j] === '"') {
						break;
					} else {
						j += 1;
					}
				}
				normalized.push(Substring(inner, i, j + 1));
				i = j + 1;
			} else if (ch === "\\" && i + 1 < inner.length) {
				in_whitespace = false;
				normalized.push(Substring(inner, i, i + 2));
				i += 2;
			} else {
				in_whitespace = false;
				normalized.push(ch);
				i += 1;
			}
		}
		var result = normalized.join("").replace(new RegExp("[" + " " + "]+$"), "");
		return prefix + "(" + result + ")";
	}

	StripArithLineContinuations(value) {
		"Strip backslash-newline (line continuation) from inside $((...)).";
		var result = [];
		var i = 0;
		while (i < value.length) {
			if (StartsWithAt(value, i, "$((")) {
				var start = i;
				i += 3;
				var depth = 1;
				var arith_content = [];
				while (i < value.length && depth > 0) {
					if (StartsWithAt(value, i, "((")) {
						arith_content.push("((");
						depth += 1;
						i += 2;
					} else if (StartsWithAt(value, i, "))")) {
						depth -= 1;
						if (depth > 0) {
							arith_content.push("))");
						}
						i += 2;
					} else if (
						value[i] === "\\" &&
						i + 1 < value.length &&
						value[i + 1] === "\n"
					) {
						i += 2;
					} else {
						arith_content.push(value[i]);
						i += 1;
					}
				}
				if (depth === 0) {
					result.push("$((" + arith_content.join("") + "))");
				} else {
					result.push(Substring(value, start, i));
				}
			} else {
				result.push(value[i]);
				i += 1;
			}
		}
		return result.join("");
	}

	CollectCmdsubs(node) {
		"Recursively collect CommandSubstitution nodes from an AST node.";
		var result = [];
		var node_kind = node["kind"] !== undefined ? node["kind"] : null;
		if (node_kind === "cmdsub") {
			result.push(node);
		} else {
			var expr = node["expression"] !== undefined ? node["expression"] : null;
			if (expr != null) {
				result.push(...this.CollectCmdsubs(expr));
			}
		}
		var left = node["left"] !== undefined ? node["left"] : null;
		if (left != null) {
			result.push(...this.CollectCmdsubs(left));
		}
		var right = node["right"] !== undefined ? node["right"] : null;
		if (right != null) {
			result.push(...this.CollectCmdsubs(right));
		}
		var operand = node["operand"] !== undefined ? node["operand"] : null;
		if (operand != null) {
			result.push(...this.CollectCmdsubs(operand));
		}
		var condition = node["condition"] !== undefined ? node["condition"] : null;
		if (condition != null) {
			result.push(...this.CollectCmdsubs(condition));
		}
		var true_value =
			node["true_value"] !== undefined ? node["true_value"] : null;
		if (true_value != null) {
			result.push(...this.CollectCmdsubs(true_value));
		}
		var false_value =
			node["false_value"] !== undefined ? node["false_value"] : null;
		if (false_value != null) {
			result.push(...this.CollectCmdsubs(false_value));
		}
		return result;
	}

	FormatCommandSubstitutions(value) {
		"Replace $(...) and >(...) / <(...) with bash-oracle-formatted AST output.";
		var cmdsub_parts = [];
		var procsub_parts = [];
		for (var p of this.parts) {
			if (p.kind === "cmdsub") {
				cmdsub_parts.push(p);
			} else if (p.kind === "procsub") {
				procsub_parts.push(p);
			} else {
				cmdsub_parts.push(...this.CollectCmdsubs(p));
			}
		}
		var has_brace_cmdsub =
			value.indexOf("${ ") !== -1 || value.indexOf("${|") !== -1;
		if (
			cmdsub_parts.length === 0 &&
			procsub_parts.length === 0 &&
			!has_brace_cmdsub
		) {
			return value;
		}
		var result = [];
		var i = 0;
		var cmdsub_idx = 0;
		var procsub_idx = 0;
		while (i < value.length) {
			if (
				StartsWithAt(value, i, "$(") &&
				!StartsWithAt(value, i, "$((") &&
				cmdsub_idx < cmdsub_parts.length
			) {
				var j = FindCmdsubEnd(value, i + 2);
				var node = cmdsub_parts[cmdsub_idx];
				var formatted = FormatCmdsubNode(node.command);
				if (formatted.startsWith("(")) {
					result.push("$( " + formatted + ")");
				} else {
					result.push("$(" + formatted + ")");
				}
				cmdsub_idx += 1;
				i = j;
			} else if (value[i] === "`" && cmdsub_idx < cmdsub_parts.length) {
				j = i + 1;
				while (j < value.length) {
					if (value[j] === "\\" && j + 1 < value.length) {
						j += 2;
						continue;
					}
					if (value[j] === "`") {
						j += 1;
						break;
					}
					j += 1;
				}
				result.push(Substring(value, i, j));
				cmdsub_idx += 1;
				i = j;
			} else if (
				(StartsWithAt(value, i, ">(") || StartsWithAt(value, i, "<(")) &&
				procsub_idx < procsub_parts.length
			) {
				var direction = value[i];
				j = FindCmdsubEnd(value, i + 2);
				node = procsub_parts[procsub_idx];
				formatted = FormatCmdsubNode(node.command, 0, true);
				result.push(direction + "(" + formatted + ")");
				procsub_idx += 1;
				i = j;
			} else if (
				StartsWithAt(value, i, "${ ") ||
				StartsWithAt(value, i, "${|")
			) {
				var prefix = Substring(value, i, i + 3);
				j = i + 3;
				var depth = 1;
				while (j < value.length && depth > 0) {
					if (value[j] === "{") {
						depth += 1;
					} else if (value[j] === "}") {
						depth -= 1;
					}
					j += 1;
				}
				var inner = Substring(value, i + 2, j - 1);
				if (inner.trim() === "") {
					result.push("${ }");
				} else {
					try {
						var parser = new Parser(
							inner.replace(new RegExp("^[" + " |" + "]+"), ""),
						);
						var parsed = parser.parseList();
						if (parsed) {
							formatted = FormatCmdsubNode(parsed);
							result.push(prefix + formatted + "; }");
						} else {
							result.push("${ }");
						}
					} catch (_) {
						result.push(Substring(value, i, j));
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
		"Return value with command substitutions formatted for cond-term output.";
		var value = this.ExpandAllAnsiCQuotes(this.value);
		value = this.FormatCommandSubstitutions(value);
		value = value.replaceAll("", "");
		return value.replace(new RegExp("[" + "\n" + "]+$"), "");
	}
}

class Command extends Node {
	"A simple command (words + redirections).";
	constructor(words, redirects) {
		super();
		this.kind = "command";
		this.words = words;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		var parts = [];
		for (var w of this.words) {
			parts.push(w.toSexp());
		}
		for (var r of this.redirects) {
			parts.push(r.toSexp());
		}
		var inner = parts.join(" ");
		if (!inner) {
			return "(command)";
		}
		return "(command " + inner + ")";
	}
}

class Pipeline extends Node {
	"A pipeline of commands.";
	constructor(commands) {
		super();
		this.kind = "pipeline";
		this.commands = commands;
	}

	toSexp() {
		if (this.commands.length === 1) {
			return this.commands[0].toSexp();
		}
		var cmds = [];
		var i = 0;
		while (i < this.commands.length) {
			var cmd = this.commands[i];
			if (cmd.kind === "pipe-both") {
				i += 1;
				continue;
			}
			var needs_redirect =
				i + 1 < this.commands.length &&
				this.commands[i + 1].kind === "pipe-both";
			cmds.push([cmd, needs_redirect]);
			i += 1;
		}
		if (cmds.length === 1) {
			var pair = cmds[0];
			cmd = pair[0];
			var needs = pair[1];
			return this.CmdSexp(cmd, needs);
		}
		var last_pair = cmds[cmds.length - 1];
		var last_cmd = last_pair[0];
		var last_needs = last_pair[1];
		var result = this.CmdSexp(last_cmd, last_needs);
		var j = cmds.length - 2;
		while (j >= 0) {
			pair = cmds[j];
			cmd = pair[0];
			needs = pair[1];
			if (needs && cmd.kind !== "command") {
				result = "(pipe " + cmd.toSexp() + ' (redirect ">&" 1) ' + result + ")";
			} else {
				result = "(pipe " + this.CmdSexp(cmd, needs) + " " + result + ")";
			}
			j -= 1;
		}
		return result;
	}

	CmdSexp(cmd, needs_redirect) {
		"Get s-expression for a command, optionally injecting pipe-both redirect.";
		if (!needs_redirect) {
			return cmd.toSexp();
		}
		if (cmd.kind === "command") {
			var parts = [];
			for (var w of cmd.words) {
				parts.push(w.toSexp());
			}
			for (var r of cmd.redirects) {
				parts.push(r.toSexp());
			}
			parts.push('(redirect ">&" 1)');
			return "(command " + parts.join(" ") + ")";
		}
		return cmd.toSexp();
	}
}

class List extends Node {
	"A list of pipelines with operators.";
	constructor(parts) {
		super();
		this.kind = "list";
		this.parts = parts;
	}

	toSexp() {
		var parts = Array.from(this.parts);
		var op_names = {
			"&&": "and",
			"||": "or",
			";": "semi",
			"\n": "semi",
			"&": "background",
		};
		while (
			parts.length > 1 &&
			parts[parts.length - 1].kind === "operator" &&
			(parts[parts.length - 1].op === ";" ||
				parts[parts.length - 1].op === "\n")
		) {
			parts = Sublist(parts, 0, parts.length - 1);
		}
		if (parts.length === 1) {
			return parts[0].toSexp();
		}
		if (
			parts[parts.length - 1].kind === "operator" &&
			parts[parts.length - 1].op === "&"
		) {
			for (var i = parts.length - 3; i > 0; i--) {
				if (
					parts[i].kind === "operator" &&
					(parts[i].op === ";" || parts[i].op === "\n")
				) {
					var left = Sublist(parts, 0, i);
					var right = Sublist(parts, i + 1, parts.length - 1);
					if (left.length > 1) {
						var left_sexp = new List(left).toSexp();
					} else {
						left_sexp = left[0].toSexp();
					}
					if (right.length > 1) {
						var right_sexp = new List(right).toSexp();
					} else {
						right_sexp = right[0].toSexp();
					}
					return "(semi " + left_sexp + " (background " + right_sexp + "))";
				}
			}
			var inner_parts = Sublist(parts, 0, parts.length - 1);
			if (inner_parts.length === 1) {
				return "(background " + inner_parts[0].toSexp() + ")";
			}
			var inner_list = new List(inner_parts);
			return "(background " + inner_list.toSexp() + ")";
		}
		return this.ToSexpWithPrecedence(parts, op_names);
	}

	ToSexpWithPrecedence(parts, op_names) {
		for (var i = parts.length - 2; i > 0; i--) {
			if (
				parts[i].kind === "operator" &&
				(parts[i].op === ";" || parts[i].op === "\n")
			) {
				var left = Sublist(parts, 0, i);
				var right = Sublist(parts, i + 1, parts.length);
				if (left.length > 1) {
					var left_sexp = new List(left).toSexp();
				} else {
					left_sexp = left[0].toSexp();
				}
				if (right.length > 1) {
					var right_sexp = new List(right).toSexp();
				} else {
					right_sexp = right[0].toSexp();
				}
				return "(semi " + left_sexp + " " + right_sexp + ")";
			}
		}
		for (var i = parts.length - 2; i > 0; i--) {
			if (parts[i].kind === "operator" && parts[i].op === "&") {
				left = Sublist(parts, 0, i);
				right = Sublist(parts, i + 1, parts.length);
				if (left.length > 1) {
					left_sexp = new List(left).toSexp();
				} else {
					left_sexp = left[0].toSexp();
				}
				if (right.length > 1) {
					right_sexp = new List(right).toSexp();
				} else {
					right_sexp = right[0].toSexp();
				}
				return "(background " + left_sexp + " " + right_sexp + ")";
			}
		}
		var result = parts[0].toSexp();
		for (var i = 1; i < parts.length - 1; i += 2) {
			var op = parts[i];
			var cmd = parts[i + 1];
			var op_name = op_names[op.op] !== undefined ? op_names[op.op] : op.op;
			result = "(" + op_name + " " + result + " " + cmd.toSexp() + ")";
		}
		return result;
	}
}

class Operator extends Node {
	"An operator token (&&, ||, ;, &, |).";
	constructor(op) {
		super();
		this.kind = "operator";
		this.op = op;
	}

	toSexp() {
		var names = {
			"&&": "and",
			"||": "or",
			";": "semi",
			"&": "bg",
			"|": "pipe",
		};
		return (
			"(" + (names[this.op] !== undefined ? names[this.op] : this.op) + ")"
		);
	}
}

class PipeBoth extends Node {
	"Marker for |& pipe (stdout + stderr).";
	constructor() {
		super();
		this.kind = "pipe-both";
	}

	toSexp() {
		return "(pipe-both)";
	}
}

class Empty extends Node {
	"Empty input.";
	constructor() {
		super();
		this.kind = "empty";
	}

	toSexp() {
		return "";
	}
}

class Comment extends Node {
	"A comment (# to end of line).";
	constructor(text) {
		super();
		this.kind = "comment";
		this.text = text;
	}

	toSexp() {
		return "";
	}
}

class Redirect extends Node {
	"A redirection.";
	fd = null;
	constructor(op, target, fd) {
		super();
		this.kind = "redirect";
		this.op = op;
		this.target = target;
		this.fd = fd;
	}

	toSexp() {
		var op = this.op.replace(new RegExp("^[" + "0123456789" + "]+"), "");
		if (op.startsWith("{")) {
			var j = 1;
			if (j < op.length && (/^[a-zA-Z]$/.test(op[j]) || op[j] === "_")) {
				j += 1;
				while (
					j < op.length &&
					(/^[a-zA-Z0-9]$/.test(op[j]) || op[j] === "_")
				) {
					j += 1;
				}
				if (j < op.length && op[j] === "}") {
					op = Substring(op, j + 1, op.length);
				}
			}
		}
		var target_val = this.target.value;
		target_val = new Word(target_val).ExpandAllAnsiCQuotes(target_val);
		target_val = target_val.replaceAll('$"', '"');
		if (target_val.startsWith("&")) {
			if (op === ">") {
				op = ">&";
			} else if (op === "<") {
				op = "<&";
			}
			var fd_target = Substring(target_val, 1, target_val.length).replace(
				new RegExp("[" + "-" + "]+$"),
				"",
			);
			if (/^[0-9]+$/.test(fd_target)) {
				return '(redirect "' + op + '" ' + fd_target + ")";
			} else if (target_val === "&-") {
				return '(redirect ">&-" 0)';
			} else {
				return '(redirect "' + op + '" "' + fd_target + '")';
			}
		}
		if (op === ">&" || op === "<&") {
			if (/^[0-9]+$/.test(target_val)) {
				return '(redirect "' + op + '" ' + target_val + ")";
			}
			target_val = target_val.replace(new RegExp("[" + "-" + "]+$"), "");
			return '(redirect "' + op + '" "' + target_val + '")';
		}
		return '(redirect "' + op + '" "' + target_val + '")';
	}
}

class HereDoc extends Node {
	"A here document <<DELIM ... DELIM.";
	strip_tabs = false;
	quoted = false;
	fd = null;
	constructor(delimiter, content, strip_tabs, quoted, fd) {
		super();
		if (strip_tabs == null) {
			strip_tabs = false;
		}
		if (quoted == null) {
			quoted = false;
		}
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
		return '(redirect "' + op + '" "' + this.content + '")';
	}
}

class Subshell extends Node {
	"A subshell ( list ).";
	redirects = null;
	constructor(body, redirects) {
		super();
		this.kind = "subshell";
		this.body = body;
		this.redirects = redirects;
	}

	toSexp() {
		var base = "(subshell " + this.body.toSexp() + ")";
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			return base + " " + redirect_parts.join(" ");
		}
		return base;
	}
}

class BraceGroup extends Node {
	"A brace group { list; }.";
	redirects = null;
	constructor(body, redirects) {
		super();
		this.kind = "brace-group";
		this.body = body;
		this.redirects = redirects;
	}

	toSexp() {
		var base = "(brace-group " + this.body.toSexp() + ")";
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			return base + " " + redirect_parts.join(" ");
		}
		return base;
	}
}

class If extends Node {
	"An if statement.";
	else_body = null;
	constructor(condition, then_body, else_body, redirects) {
		super();
		this.kind = "if";
		this.condition = condition;
		this.then_body = then_body;
		this.else_body = else_body;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		var result =
			"(if " + this.condition.toSexp() + " " + this.then_body.toSexp();
		if (this.else_body) {
			result = result + " " + this.else_body.toSexp();
		}
		result = result + ")";
		for (var r of this.redirects) {
			result = result + " " + r.toSexp();
		}
		return result;
	}
}

class While extends Node {
	"A while loop.";
	constructor(condition, body, redirects) {
		super();
		this.kind = "while";
		this.condition = condition;
		this.body = body;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		var base =
			"(while " + this.condition.toSexp() + " " + this.body.toSexp() + ")";
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			return base + " " + redirect_parts.join(" ");
		}
		return base;
	}
}

class Until extends Node {
	"An until loop.";
	constructor(condition, body, redirects) {
		super();
		this.kind = "until";
		this.condition = condition;
		this.body = body;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		var base =
			"(until " + this.condition.toSexp() + " " + this.body.toSexp() + ")";
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			return base + " " + redirect_parts.join(" ");
		}
		return base;
	}
}

class For extends Node {
	"A for loop.";
	constructor(variable, words, body, redirects) {
		super();
		this.kind = "for";
		this.variable = variable;
		this.words = words;
		this.body = body;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		var suffix = "";
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			suffix = " " + redirect_parts.join(" ");
		}
		var var_escaped = this.variable
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"');
		if (this.words == null) {
			return (
				'(for (word "' +
				var_escaped +
				'") (in (word "\\"$@\\"")) ' +
				this.body.toSexp() +
				")" +
				suffix
			);
		} else if (this.words.length === 0) {
			return (
				'(for (word "' +
				var_escaped +
				'") (in) ' +
				this.body.toSexp() +
				")" +
				suffix
			);
		} else {
			var word_parts = [];
			for (var w of this.words) {
				word_parts.push(w.toSexp());
			}
			var word_strs = word_parts.join(" ");
			return (
				'(for (word "' +
				var_escaped +
				'") (in ' +
				word_strs +
				") " +
				this.body.toSexp() +
				")" +
				suffix
			);
		}
	}
}

class ForArith extends Node {
	"A C-style for loop: for ((init; cond; incr)); do ... done.";
	constructor(init, cond, incr, body, redirects) {
		super();
		this.kind = "for-arith";
		this.init = init;
		this.cond = cond;
		this.incr = incr;
		this.body = body;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		function formatArithVal(s) {
			var w = new Word(s, []);
			var val = w.ExpandAllAnsiCQuotes(s);
			val = w.StripLocaleStringDollars(val);
			val = val.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			return val;
		}

		var suffix = "";
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			suffix = " " + redirect_parts.join(" ");
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
		return (
			'(arith-for (init (word "' +
			formatArithVal(init_val) +
			'")) ' +
			'(test (word "' +
			formatArithVal(cond_val) +
			'")) ' +
			'(step (word "' +
			formatArithVal(incr_val) +
			'")) ' +
			this.body.toSexp() +
			")" +
			suffix
		);
	}
}

class Select extends Node {
	"A select statement.";
	constructor(variable, words, body, redirects) {
		super();
		this.kind = "select";
		this.variable = variable;
		this.words = words;
		this.body = body;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		var suffix = "";
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			suffix = " " + redirect_parts.join(" ");
		}
		var var_escaped = this.variable
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"');
		if (this.words != null) {
			var word_parts = [];
			for (var w of this.words) {
				word_parts.push(w.toSexp());
			}
			var word_strs = word_parts.join(" ");
			if (this.words && this.words.length) {
				var in_clause = "(in " + word_strs + ")";
			} else {
				in_clause = "(in)";
			}
		} else {
			in_clause = '(in (word "\\"$@\\""))';
		}
		return (
			'(select (word "' +
			var_escaped +
			'") ' +
			in_clause +
			" " +
			this.body.toSexp() +
			")" +
			suffix
		);
	}
}

class Case extends Node {
	"A case statement.";
	constructor(word, patterns, redirects) {
		super();
		this.kind = "case";
		this.word = word;
		this.patterns = patterns;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		var parts = [];
		parts.push("(case " + this.word.toSexp());
		for (var p of this.patterns) {
			parts.push(p.toSexp());
		}
		var base = parts.join(" ") + ")";
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			return base + " " + redirect_parts.join(" ");
		}
		return base;
	}
}

function ConsumeSingleQuote(s, start) {
	"Consume '...' from start. Returns (end_index, chars_list).";
	var chars = ["'"];
	var i = start + 1;
	while (i < s.length && s[i] !== "'") {
		chars.push(s[i]);
		i += 1;
	}
	if (i < s.length) {
		chars.push(s[i]);
		i += 1;
	}
	return [i, chars];
}

function ConsumeDoubleQuote(s, start) {
	"Consume \"...\" from start, handling escapes. Returns (end_index, chars_list).";
	var chars = ['"'];
	var i = start + 1;
	while (i < s.length && s[i] !== '"') {
		if (s[i] === "\\" && i + 1 < s.length) {
			chars.push(s[i]);
			i += 1;
		}
		chars.push(s[i]);
		i += 1;
	}
	if (i < s.length) {
		chars.push(s[i]);
		i += 1;
	}
	return [i, chars];
}

function HasBracketClose(s, start, depth) {
	"Check if there's a ] before | or ) at depth 0.";
	var i = start;
	while (i < s.length) {
		if (s[i] === "]") {
			return true;
		}
		if ((s[i] === "|" || s[i] === ")") && depth === 0) {
			return false;
		}
		i += 1;
	}
	return false;
}

function ConsumeBracketClass(s, start, depth) {
	"Consume [...] bracket expression. Returns (end_index, chars_list, was_bracket).";
	var scan_pos = start + 1;
	if (scan_pos < s.length && (s[scan_pos] === "!" || s[scan_pos] === "^")) {
		scan_pos += 1;
	}
	if (scan_pos < s.length && s[scan_pos] === "]") {
		if (HasBracketClose(s, scan_pos + 1, depth)) {
			scan_pos += 1;
		}
	}
	var is_bracket = false;
	while (scan_pos < s.length) {
		if (s[scan_pos] === "]") {
			is_bracket = true;
			break;
		}
		if (s[scan_pos] === ")" && depth === 0) {
			break;
		}
		scan_pos += 1;
	}
	if (!is_bracket) {
		return [start + 1, ["["], false];
	}
	var chars = ["["];
	var i = start + 1;
	if (i < s.length && (s[i] === "!" || s[i] === "^")) {
		chars.push(s[i]);
		i += 1;
	}
	if (i < s.length && s[i] === "]") {
		if (HasBracketClose(s, i + 1, depth)) {
			chars.push(s[i]);
			i += 1;
		}
	}
	while (i < s.length && s[i] !== "]") {
		chars.push(s[i]);
		i += 1;
	}
	if (i < s.length) {
		chars.push(s[i]);
		i += 1;
	}
	return [i, chars, true];
}

class CasePattern extends Node {
	"A pattern clause in a case statement.";
	terminator = ";;";
	constructor(pattern, body, terminator) {
		super();
		if (terminator == null) {
			terminator = ";;";
		}
		this.kind = "pattern";
		this.pattern = pattern;
		this.body = body;
		this.terminator = terminator;
	}

	toSexp() {
		var alternatives = [];
		var current = [];
		var i = 0;
		var depth = 0;
		while (i < this.pattern.length) {
			var ch = this.pattern[i];
			if (ch === "\\" && i + 1 < this.pattern.length) {
				current.push(Substring(this.pattern, i, i + 2));
				i += 2;
			} else if (
				(ch === "@" || ch === "?" || ch === "*" || ch === "+" || ch === "!") &&
				i + 1 < this.pattern.length &&
				this.pattern[i + 1] === "("
			) {
				current.push(ch);
				current.push("(");
				depth += 1;
				i += 2;
			} else if (
				ch === "$" &&
				i + 1 < this.pattern.length &&
				this.pattern[i + 1] === "("
			) {
				current.push(ch);
				current.push("(");
				depth += 1;
				i += 2;
			} else if (ch === "(" && depth > 0) {
				current.push(ch);
				depth += 1;
				i += 1;
			} else if (ch === ")" && depth > 0) {
				current.push(ch);
				depth -= 1;
				i += 1;
			} else if (ch === "[") {
				var result = ConsumeBracketClass(this.pattern, i, depth);
				i = result[0];
				current.push(...result[1]);
			} else if (ch === "'" && depth === 0) {
				result = ConsumeSingleQuote(this.pattern, i);
				i = result[0];
				current.push(...result[1]);
			} else if (ch === '"' && depth === 0) {
				result = ConsumeDoubleQuote(this.pattern, i);
				i = result[0];
				current.push(...result[1]);
			} else if (ch === "|" && depth === 0) {
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
		for (var alt of alternatives) {
			word_list.push(new Word(alt).toSexp());
		}
		var pattern_str = word_list.join(" ");
		var parts = ["(pattern (" + pattern_str + ")"];
		if (this.body) {
			parts.push(" " + this.body.toSexp());
		} else {
			parts.push(" ()");
		}
		parts.push(")");
		return parts.join("");
	}
}

class Function extends Node {
	"A function definition.";
	constructor(name, body) {
		super();
		this.kind = "function";
		this.name = name;
		this.body = body;
	}

	toSexp() {
		return '(function "' + this.name + '" ' + this.body.toSexp() + ")";
	}
}

class ParamExpansion extends Node {
	"A parameter expansion ${var} or ${var:-default}.";
	op = null;
	arg = null;
	constructor(param, op, arg) {
		super();
		this.kind = "param";
		this.param = param;
		this.op = op;
		this.arg = arg;
	}

	toSexp() {
		var escaped_param = this.param
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"');
		if (this.op != null) {
			var escaped_op = this.op.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			if (this.arg != null) {
				var arg_val = this.arg;
			} else {
				arg_val = "";
			}
			var escaped_arg = arg_val.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			return (
				'(param "' +
				escaped_param +
				'" "' +
				escaped_op +
				'" "' +
				escaped_arg +
				'")'
			);
		}
		return '(param "' + escaped_param + '")';
	}
}

class ParamLength extends Node {
	"A parameter length expansion ${#var}.";
	constructor(param) {
		super();
		this.kind = "param-len";
		this.param = param;
	}

	toSexp() {
		var escaped = this.param.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
		return '(param-len "' + escaped + '")';
	}
}

class ParamIndirect extends Node {
	"An indirect parameter expansion ${!var} or ${!var<op><arg>}.";
	constructor(param, op, arg) {
		super();
		this.kind = "param-indirect";
		this.param = param;
		this.op = op;
		this.arg = arg;
	}

	toSexp() {
		var escaped = this.param.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
		if (this.op != null) {
			var escaped_op = this.op.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			if (this.arg != null) {
				var arg_val = this.arg;
			} else {
				arg_val = "";
			}
			var escaped_arg = arg_val.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			return (
				'(param-indirect "' +
				escaped +
				'" "' +
				escaped_op +
				'" "' +
				escaped_arg +
				'")'
			);
		}
		return '(param-indirect "' + escaped + '")';
	}
}

class CommandSubstitution extends Node {
	"A command substitution $(...) or `...`.";
	constructor(command) {
		super();
		this.kind = "cmdsub";
		this.command = command;
	}

	toSexp() {
		return "(cmdsub " + this.command.toSexp() + ")";
	}
}

class ArithmeticExpansion extends Node {
	"An arithmetic expansion $((...)) with parsed internals.";
	constructor(expression) {
		super();
		this.kind = "arith";
		this.expression = expression;
	}

	toSexp() {
		if (this.expression == null) {
			return "(arith)";
		}
		return "(arith " + this.expression.toSexp() + ")";
	}
}

class ArithmeticCommand extends Node {
	"An arithmetic command ((...)) with parsed internals.";
	constructor(expression, redirects, raw_content) {
		super();
		if (raw_content == null) {
			raw_content = "";
		}
		this.kind = "arith-cmd";
		this.expression = expression;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
		this.raw_content = raw_content;
	}

	toSexp() {
		var escaped = this.raw_content
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n");
		var result = '(arith (word "' + escaped + '"))';
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			var redirect_sexps = redirect_parts.join(" ");
			return result + " " + redirect_sexps;
		}
		return result;
	}
}

class ArithNumber extends Node {
	"A numeric literal in arithmetic context.";
	constructor(value) {
		super();
		this.kind = "number";
		this.value = value;
	}

	toSexp() {
		return '(number "' + this.value + '")';
	}
}

class ArithVar extends Node {
	"A variable reference in arithmetic context (without $).";
	constructor(name) {
		super();
		this.kind = "var";
		this.name = name;
	}

	toSexp() {
		return '(var "' + this.name + '")';
	}
}

class ArithBinaryOp extends Node {
	"A binary operation in arithmetic.";
	constructor(op, left, right) {
		super();
		this.kind = "binary-op";
		this.op = op;
		this.left = left;
		this.right = right;
	}

	toSexp() {
		return (
			'(binary-op "' +
			this.op +
			'" ' +
			this.left.toSexp() +
			" " +
			this.right.toSexp() +
			")"
		);
	}
}

class ArithUnaryOp extends Node {
	"A unary operation in arithmetic.";
	constructor(op, operand) {
		super();
		this.kind = "unary-op";
		this.op = op;
		this.operand = operand;
	}

	toSexp() {
		return '(unary-op "' + this.op + '" ' + this.operand.toSexp() + ")";
	}
}

class ArithPreIncr extends Node {
	"Pre-increment ++var.";
	constructor(operand) {
		super();
		this.kind = "pre-incr";
		this.operand = operand;
	}

	toSexp() {
		return "(pre-incr " + this.operand.toSexp() + ")";
	}
}

class ArithPostIncr extends Node {
	"Post-increment var++.";
	constructor(operand) {
		super();
		this.kind = "post-incr";
		this.operand = operand;
	}

	toSexp() {
		return "(post-incr " + this.operand.toSexp() + ")";
	}
}

class ArithPreDecr extends Node {
	"Pre-decrement --var.";
	constructor(operand) {
		super();
		this.kind = "pre-decr";
		this.operand = operand;
	}

	toSexp() {
		return "(pre-decr " + this.operand.toSexp() + ")";
	}
}

class ArithPostDecr extends Node {
	"Post-decrement var--.";
	constructor(operand) {
		super();
		this.kind = "post-decr";
		this.operand = operand;
	}

	toSexp() {
		return "(post-decr " + this.operand.toSexp() + ")";
	}
}

class ArithAssign extends Node {
	"Assignment operation (=, +=, -=, etc.).";
	constructor(op, target, value) {
		super();
		this.kind = "assign";
		this.op = op;
		this.target = target;
		this.value = value;
	}

	toSexp() {
		return (
			'(assign "' +
			this.op +
			'" ' +
			this.target.toSexp() +
			" " +
			this.value.toSexp() +
			")"
		);
	}
}

class ArithTernary extends Node {
	"Ternary conditional expr ? expr : expr.";
	constructor(condition, if_true, if_false) {
		super();
		this.kind = "ternary";
		this.condition = condition;
		this.if_true = if_true;
		this.if_false = if_false;
	}

	toSexp() {
		return (
			"(ternary " +
			this.condition.toSexp() +
			" " +
			this.if_true.toSexp() +
			" " +
			this.if_false.toSexp() +
			")"
		);
	}
}

class ArithComma extends Node {
	"Comma operator expr, expr.";
	constructor(left, right) {
		super();
		this.kind = "comma";
		this.left = left;
		this.right = right;
	}

	toSexp() {
		return "(comma " + this.left.toSexp() + " " + this.right.toSexp() + ")";
	}
}

class ArithSubscript extends Node {
	"Array subscript arr[expr].";
	constructor(array, index) {
		super();
		this.kind = "subscript";
		this.array = array;
		this.index = index;
	}

	toSexp() {
		return '(subscript "' + this.array + '" ' + this.index.toSexp() + ")";
	}
}

class ArithEscape extends Node {
	"An escaped character in arithmetic expression.";
	constructor(char) {
		super();
		this.kind = "escape";
		this.char = char;
	}

	toSexp() {
		return '(escape "' + this.char + '")';
	}
}

class ArithDeprecated extends Node {
	"A deprecated arithmetic expansion $[expr].";
	constructor(expression) {
		super();
		this.kind = "arith-deprecated";
		this.expression = expression;
	}

	toSexp() {
		var escaped = this.expression
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n");
		return '(arith-deprecated "' + escaped + '")';
	}
}

class AnsiCQuote extends Node {
	"An ANSI-C quoted string $'...'.";
	constructor(content) {
		super();
		this.kind = "ansi-c";
		this.content = content;
	}

	toSexp() {
		var escaped = this.content
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n");
		return '(ansi-c "' + escaped + '")';
	}
}

class LocaleString extends Node {
	'A locale-translated string $"...".';
	constructor(content) {
		super();
		this.kind = "locale";
		this.content = content;
	}

	toSexp() {
		var escaped = this.content
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n");
		return '(locale "' + escaped + '")';
	}
}

class ProcessSubstitution extends Node {
	"A process substitution <(...) or >(...).";
	constructor(direction, command) {
		super();
		this.kind = "procsub";
		this.direction = direction;
		this.command = command;
	}

	toSexp() {
		return '(procsub "' + this.direction + '" ' + this.command.toSexp() + ")";
	}
}

class Negation extends Node {
	"Pipeline negation with !.";
	constructor(pipeline) {
		super();
		this.kind = "negation";
		this.pipeline = pipeline;
	}

	toSexp() {
		if (this.pipeline == null) {
			return "(negation (command))";
		}
		return "(negation " + this.pipeline.toSexp() + ")";
	}
}

class Time extends Node {
	"Time measurement with time keyword.";
	posix = false;
	constructor(pipeline, posix) {
		super();
		if (posix == null) {
			posix = false;
		}
		this.kind = "time";
		this.pipeline = pipeline;
		this.posix = posix;
	}

	toSexp() {
		if (this.pipeline == null) {
			if (this.posix) {
				return "(time -p (command))";
			} else {
				return "(time (command))";
			}
		}
		if (this.posix) {
			return "(time -p " + this.pipeline.toSexp() + ")";
		}
		return "(time " + this.pipeline.toSexp() + ")";
	}
}

class ConditionalExpr extends Node {
	"A conditional expression [[ expression ]].";
	constructor(body, redirects) {
		super();
		this.kind = "cond-expr";
		this.body = body;
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		var body_kind = this.body["kind"] !== undefined ? this.body["kind"] : null;
		if (body_kind == null) {
			var escaped = this.body
				.replaceAll("\\", "\\\\")
				.replaceAll('"', '\\"')
				.replaceAll("\n", "\\n");
			var result = '(cond "' + escaped + '")';
		} else {
			result = "(cond " + this.body.toSexp() + ")";
		}
		if (this.redirects && this.redirects.length) {
			var redirect_parts = [];
			for (var r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			var redirect_sexps = redirect_parts.join(" ");
			return result + " " + redirect_sexps;
		}
		return result;
	}
}

class UnaryTest extends Node {
	"A unary test in [[ ]], e.g., -f file, -z string.";
	constructor(op, operand) {
		super();
		this.kind = "unary-test";
		this.op = op;
		this.operand = operand;
	}

	toSexp() {
		return (
			'(cond-unary "' + this.op + '" (cond-term "' + this.operand.value + '"))'
		);
	}
}

class BinaryTest extends Node {
	"A binary test in [[ ]], e.g., $a == $b, file1 -nt file2.";
	constructor(op, left, right) {
		super();
		this.kind = "binary-test";
		this.op = op;
		this.left = left;
		this.right = right;
	}

	toSexp() {
		var left_val = this.left.getCondFormattedValue();
		var right_val = this.right.getCondFormattedValue();
		return (
			'(cond-binary "' +
			this.op +
			'" (cond-term "' +
			left_val +
			'") (cond-term "' +
			right_val +
			'"))'
		);
	}
}

class CondAnd extends Node {
	"Logical AND in [[ ]], e.g., expr1 && expr2.";
	constructor(left, right) {
		super();
		this.kind = "cond-and";
		this.left = left;
		this.right = right;
	}

	toSexp() {
		return "(cond-and " + this.left.toSexp() + " " + this.right.toSexp() + ")";
	}
}

class CondOr extends Node {
	"Logical OR in [[ ]], e.g., expr1 || expr2.";
	constructor(left, right) {
		super();
		this.kind = "cond-or";
		this.left = left;
		this.right = right;
	}

	toSexp() {
		return "(cond-or " + this.left.toSexp() + " " + this.right.toSexp() + ")";
	}
}

class CondNot extends Node {
	"Logical NOT in [[ ]], e.g., ! expr.";
	constructor(operand) {
		super();
		this.kind = "cond-not";
		this.operand = operand;
	}

	toSexp() {
		return this.operand.toSexp();
	}
}

class CondParen extends Node {
	"Parenthesized group in [[ ]], e.g., ( expr ).";
	constructor(inner) {
		super();
		this.kind = "cond-paren";
		this.inner = inner;
	}

	toSexp() {
		return "(cond-expr " + this.inner.toSexp() + ")";
	}
}

class ArrayNode extends Node {
	"An array literal (word1 word2 ...).";
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
		for (var e of this.elements) {
			parts.push(e.toSexp());
		}
		var inner = parts.join(" ");
		return "(array " + inner + ")";
	}
}

class Coproc extends Node {
	"A coprocess coproc [NAME] command.";
	name = null;
	constructor(command, name) {
		super();
		this.kind = "coproc";
		this.command = command;
		this.name = name;
	}

	toSexp() {
		if (this.name) {
			var name = this.name;
		} else {
			name = "COPROC";
		}
		return '(coproc "' + name + '" ' + this.command.toSexp() + ")";
	}
}

function FormatCmdsubNode(node, indent, in_procsub) {
	if (indent == null) {
		indent = 0;
	}
	if (in_procsub == null) {
		in_procsub = false;
	}
	("Format an AST node for command substitution output (bash-oracle pretty-print format).");
	var sp = RepeatStr(" ", indent);
	var inner_sp = RepeatStr(" ", indent + 4);
	if (node.kind === "empty") {
		return "";
	}
	if (node.kind === "command") {
		var parts = [];
		for (var w of node.words) {
			var val = w.ExpandAllAnsiCQuotes(w.value);
			val = w.FormatCommandSubstitutions(val);
			parts.push(val);
		}
		for (var r of node.redirects) {
			parts.push(FormatRedirect(r));
		}
		return parts.join(" ");
	}
	if (node.kind === "pipeline") {
		var cmd_parts = [];
		for (var cmd of node.commands) {
			cmd_parts.push(FormatCmdsubNode(cmd, indent));
		}
		return cmd_parts.join(" | ");
	}
	if (node.kind === "list") {
		var result = [];
		for (var p of node.parts) {
			if (p.kind === "operator") {
				if (p.op === ";") {
					result.push(";");
				} else if (p.op === "\n") {
					if (result.length > 0 && result[result.length - 1] === ";") {
						continue;
					}
					result.push("\n");
				} else if (p.op === "&") {
					result.push(" &");
				} else {
					result.push(" " + p.op);
				}
			} else {
				if (
					result.length > 0 &&
					!(
						result[result.length - 1].endsWith(" ") ||
						result[result.length - 1].endsWith("\n")
					)
				) {
					result.push(" ");
				}
				result.push(FormatCmdsubNode(p, indent));
			}
		}
		var s = result.join("");
		while (s.endsWith(";") || s.endsWith("\n")) {
			s = Substring(s, 0, s.length - 1);
		}
		return s;
	}
	if (node.kind === "if") {
		var cond = FormatCmdsubNode(node.condition, indent);
		var then_body = FormatCmdsubNode(node.then_body, indent + 4);
		result = "if " + cond + "; then\n" + inner_sp + then_body + ";";
		if (node.else_body) {
			var else_body = FormatCmdsubNode(node.else_body, indent + 4);
			result = result + "\n" + sp + "else\n" + inner_sp + else_body + ";";
		}
		result = result + "\n" + sp + "fi";
		return result;
	}
	if (node.kind === "while") {
		cond = FormatCmdsubNode(node.condition, indent);
		var body = FormatCmdsubNode(node.body, indent + 4);
		return "while " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done";
	}
	if (node.kind === "until") {
		cond = FormatCmdsubNode(node.condition, indent);
		body = FormatCmdsubNode(node.body, indent + 4);
		return "until " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done";
	}
	if (node.kind === "for") {
		var variable = node.variable;
		body = FormatCmdsubNode(node.body, indent + 4);
		if (node.words) {
			var word_vals = [];
			for (var w of node.words) {
				word_vals.push(w.value);
			}
			var words = word_vals.join(" ");
			return (
				"for " +
				variable +
				" in " +
				words +
				";\ndo\n" +
				inner_sp +
				body +
				";\n" +
				sp +
				"done"
			);
		}
		return (
			"for " + variable + ";\ndo\n" + inner_sp + body + ";\n" + sp + "done"
		);
	}
	if (node.kind === "case") {
		var word = node.word.value;
		var patterns = [];
		var i = 0;
		while (i < node.patterns.length) {
			p = node.patterns[i];
			var pat = p.pattern.replaceAll("|", " | ");
			if (p.body) {
				body = FormatCmdsubNode(p.body, indent + 8);
			} else {
				body = "";
			}
			var term = p.terminator;
			var pat_indent = RepeatStr(" ", indent + 8);
			var term_indent = RepeatStr(" ", indent + 4);
			if (i === 0) {
				patterns.push(
					" " + pat + ")\n" + pat_indent + body + "\n" + term_indent + term,
				);
			} else {
				patterns.push(
					pat + ")\n" + pat_indent + body + "\n" + term_indent + term,
				);
			}
			i += 1;
		}
		var pattern_str = patterns.join("\n" + RepeatStr(" ", indent + 4));
		return "case " + word + " in" + pattern_str + "\n" + sp + "esac";
	}
	if (node.kind === "function") {
		var name = node.name;
		if (node.body.kind === "brace-group") {
			body = FormatCmdsubNode(node.body.body, indent + 4);
		} else {
			body = FormatCmdsubNode(node.body, indent + 4);
		}
		body = body.replace(new RegExp("[" + ";" + "]+$"), "");
		return "function " + name + " () \n{ \n" + inner_sp + body + "\n}";
	}
	if (node.kind === "subshell") {
		body = FormatCmdsubNode(node.body, indent, in_procsub);
		var redirects = "";
		if (node.redirects) {
			var redirect_parts = [];
			for (var r of node.redirects) {
				redirect_parts.push(FormatRedirect(r));
			}
			redirects = redirect_parts.join(" ");
		}
		if (in_procsub) {
			if (redirects) {
				return "(" + body + ") " + redirects;
			}
			return "(" + body + ")";
		}
		if (redirects) {
			return "( " + body + " ) " + redirects;
		}
		return "( " + body + " )";
	}
	if (node.kind === "brace-group") {
		body = FormatCmdsubNode(node.body, indent);
		body = body.replace(new RegExp("[" + ";" + "]+$"), "");
		return "{ " + body + "; }";
	}
	if (node.kind === "arith-cmd") {
		return "((" + node.raw_content + "))";
	}
	return "";
}

function FormatRedirect(r) {
	"Format a redirect for command substitution output.";
	if (r.kind === "heredoc") {
		if (r.strip_tabs) {
			var op = "<<-";
		} else {
			op = "<<";
		}
		if (r.quoted) {
			var delim = "'" + r.delimiter + "'";
		} else {
			delim = r.delimiter;
		}
		return op + delim + "\n" + r.content + r.delimiter + "\n";
	}
	op = r.op;
	var target = r.target.value;
	if (target.startsWith("&")) {
		if (target === "&-" && op.endsWith("<")) {
			op = Substring(op, 0, op.length - 1) + ">";
		}
		if (op === ">") {
			op = "1>";
		} else if (op === "<") {
			op = "0<";
		}
		return op + target;
	}
	return op + " " + target;
}

function NormalizeFdRedirects(s) {
	"Normalize fd redirects in a raw string: >&2 -> 1>&2, <&N -> 0<&N.";
	var result = [];
	var i = 0;
	while (i < s.length) {
		if (i + 2 < s.length && s[i + 1] === "&" && /^[0-9]+$/.test(s[i + 2])) {
			var prev_is_digit = i > 0 && /^[0-9]+$/.test(s[i - 1]);
			if (s[i] === ">" && !prev_is_digit) {
				result.push("1>&");
				result.push(s[i + 2]);
				i += 3;
				continue;
			} else if (s[i] === "<" && !prev_is_digit) {
				result.push("0<&");
				result.push(s[i + 2]);
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
	"Find the end of a $(...) command substitution, handling case statements.\n\n    Starts after the opening $(. Returns position after the closing ).\n    ";
	var depth = 1;
	var i = start;
	var in_single = false;
	var in_double = false;
	var case_depth = 0;
	var in_case_patterns = false;
	while (i < value.length && depth > 0) {
		var c = value[i];
		if (c === "\\" && i + 1 < value.length && !in_single) {
			i += 2;
			continue;
		}
		if (c === "'" && !in_double) {
			in_single = !in_single;
			i += 1;
			continue;
		}
		if (c === '"' && !in_single) {
			in_double = !in_double;
			i += 1;
			continue;
		}
		if (in_single) {
			i += 1;
			continue;
		}
		if (in_double) {
			if (StartsWithAt(value, i, "$(") && !StartsWithAt(value, i, "$((")) {
				var j = FindCmdsubEnd(value, i + 2);
				i = j;
				continue;
			}
			i += 1;
			continue;
		}
		if (
			c === "#" &&
			(i === start ||
				value[i - 1] === " " ||
				value[i - 1] === "\t" ||
				value[i - 1] === "\n" ||
				value[i - 1] === ";" ||
				value[i - 1] === "|" ||
				value[i - 1] === "&" ||
				value[i - 1] === "(" ||
				value[i - 1] === ")")
		) {
			while (i < value.length && value[i] !== "\n") {
				i += 1;
			}
			continue;
		}
		if (StartsWithAt(value, i, "<<")) {
			i = SkipHeredoc(value, i);
			continue;
		}
		if (StartsWithAt(value, i, "case") && IsWordBoundary(value, i, 4)) {
			case_depth += 1;
			in_case_patterns = false;
			i += 4;
			continue;
		}
		if (
			case_depth > 0 &&
			StartsWithAt(value, i, "in") &&
			IsWordBoundary(value, i, 2)
		) {
			in_case_patterns = true;
			i += 2;
			continue;
		}
		if (StartsWithAt(value, i, "esac") && IsWordBoundary(value, i, 4)) {
			if (case_depth > 0) {
				case_depth -= 1;
				in_case_patterns = false;
			}
			i += 4;
			continue;
		}
		if (StartsWithAt(value, i, ";;")) {
			i += 2;
			continue;
		}
		if (c === "(") {
			depth += 1;
		} else if (c === ")") {
			if (in_case_patterns && case_depth > 0) {
			} else {
				depth -= 1;
			}
		}
		i += 1;
	}
	return i;
}

function SkipHeredoc(value, start) {
	"Skip past a heredoc starting at <<. Returns position after heredoc content.";
	var i = start + 2;
	if (i < value.length && value[i] === "-") {
		i += 1;
	}
	while (i < value.length && IsWhitespaceNoNewline(value[i])) {
		i += 1;
	}
	var delim_start = i;
	var quote_char = null;
	if (i < value.length && (value[i] === '"' || value[i] === "'")) {
		quote_char = value[i];
		i += 1;
		delim_start = i;
		while (i < value.length && value[i] !== quote_char) {
			i += 1;
		}
		var delimiter = Substring(value, delim_start, i);
		if (i < value.length) {
			i += 1;
		}
	} else if (i < value.length && value[i] === "\\") {
		i += 1;
		delim_start = i;
		while (i < value.length && !IsWhitespace(value[i])) {
			i += 1;
		}
		delimiter = Substring(value, delim_start, i);
	} else {
		while (i < value.length && !IsWhitespace(value[i])) {
			i += 1;
		}
		delimiter = Substring(value, delim_start, i);
	}
	while (i < value.length && value[i] !== "\n") {
		i += 1;
	}
	if (i < value.length) {
		i += 1;
	}
	while (i < value.length) {
		var line_start = i;
		var line_end = i;
		while (line_end < value.length && value[line_end] !== "\n") {
			line_end += 1;
		}
		var line = Substring(value, line_start, line_end);
		if (start + 2 < value.length && value[start + 2] === "-") {
			var stripped = line.replace(new RegExp("^[" + "\t" + "]+"), "");
		} else {
			stripped = line;
		}
		if (stripped === delimiter) {
			if (line_end < value.length) {
				return line_end + 1;
			} else {
				return line_end;
			}
		}
		if (line_end < value.length) {
			i = line_end + 1;
		} else {
			i = line_end;
		}
	}
	return i;
}

function IsWordBoundary(s, pos, word_len) {
	"Check if the word at pos is a standalone word (not part of larger word).";
	if (pos > 0 && /^[a-zA-Z0-9]$/.test(s[pos - 1])) {
		return false;
	}
	var end = pos + word_len;
	if (end < s.length && /^[a-zA-Z0-9]$/.test(s[end])) {
		return false;
	}
	return true;
}

var RESERVED_WORDS = new Set([
	"if",
	"then",
	"elif",
	"else",
	"fi",
	"while",
	"until",
	"for",
	"select",
	"do",
	"done",
	"case",
	"esac",
	"in",
	"function",
	"coproc",
]);
var METACHAR = new Set(" \t\n|&;()<>");
var COND_UNARY_OPS = new Set([
	"-a",
	"-b",
	"-c",
	"-d",
	"-e",
	"-f",
	"-g",
	"-h",
	"-k",
	"-p",
	"-r",
	"-s",
	"-t",
	"-u",
	"-w",
	"-x",
	"-G",
	"-L",
	"-N",
	"-O",
	"-S",
	"-z",
	"-n",
	"-o",
	"-v",
	"-R",
]);
var COND_BINARY_OPS = new Set([
	"==",
	"!=",
	"=~",
	"=",
	"<",
	">",
	"-eq",
	"-ne",
	"-lt",
	"-le",
	"-gt",
	"-ge",
	"-nt",
	"-ot",
	"-ef",
]);
var COMPOUND_KEYWORDS = new Set([
	"while",
	"until",
	"for",
	"if",
	"case",
	"select",
]);
function IsQuote(c) {
	return c === "'" || c === '"';
}

function IsMetachar(c) {
	return (
		c === " " ||
		c === "\t" ||
		c === "\n" ||
		c === "|" ||
		c === "&" ||
		c === ";" ||
		c === "(" ||
		c === ")" ||
		c === "<" ||
		c === ">"
	);
}

function IsExtglobPrefix(c) {
	return c === "@" || c === "?" || c === "*" || c === "+" || c === "!";
}

function IsRedirectChar(c) {
	return c === "<" || c === ">";
}

function IsSpecialParam(c) {
	return (
		c === "?" ||
		c === "$" ||
		c === "!" ||
		c === "#" ||
		c === "@" ||
		c === "*" ||
		c === "-"
	);
}

function IsDigit(c) {
	return c >= "0" && c <= "9";
}

function IsSemicolonOrNewline(c) {
	return c === ";" || c === "\n";
}

function IsRightBracket(c) {
	return c === ")" || c === "}";
}

function IsWordStartContext(c) {
	"Check if char is a valid context for starting a word (whitespace or metachar except >).";
	return (
		c === " " ||
		c === "\t" ||
		c === "\n" ||
		c === ";" ||
		c === "|" ||
		c === "&" ||
		c === "<" ||
		c === "("
	);
}

function IsWordEndContext(c) {
	"Check if char ends a word context (whitespace or metachar).";
	return (
		c === " " ||
		c === "\t" ||
		c === "\n" ||
		c === ";" ||
		c === "|" ||
		c === "&" ||
		c === "<" ||
		c === ">" ||
		c === "(" ||
		c === ")"
	);
}

function IsSpecialParamOrDigit(c) {
	return IsSpecialParam(c) || IsDigit(c);
}

function IsParamExpansionOp(c) {
	return (
		c === ":" ||
		c === "-" ||
		c === "=" ||
		c === "+" ||
		c === "?" ||
		c === "#" ||
		c === "%" ||
		c === "/" ||
		c === "^" ||
		c === "," ||
		c === "@" ||
		c === "*" ||
		c === "["
	);
}

function IsSimpleParamOp(c) {
	return c === "-" || c === "=" || c === "?" || c === "+";
}

function IsEscapeCharInDquote(c) {
	return c === "$" || c === "`" || c === "\\";
}

function IsListTerminator(c) {
	return c === "\n" || c === "|" || c === ";" || c === "(" || c === ")";
}

function IsSemicolonOrAmp(c) {
	return c === ";" || c === "&";
}

function IsParen(c) {
	return c === "(" || c === ")";
}

function IsCaretOrBang(c) {
	return c === "!" || c === "^";
}

function IsAtOrStar(c) {
	return c === "@" || c === "*";
}

function IsDigitOrDash(c) {
	return IsDigit(c) || c === "-";
}

function IsNewlineOrRightParen(c) {
	return c === "\n" || c === ")";
}

function IsNewlineOrRightBracket(c) {
	return c === "\n" || c === ")" || c === "}";
}

function IsSemicolonNewlineBrace(c) {
	return c === ";" || c === "\n" || c === "{";
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
	"Check if haystack contains needle substring.";
	return haystack.indexOf(needle) !== -1;
}

class Parser {
	"Recursive descent parser for bash.";
	constructor(source) {
		this.source = source;
		this.pos = 0;
		this.length = source.length;
		this._pending_heredoc_end = null;
	}

	atEnd() {
		"Check if we've reached the end of input.";
		return this.pos >= this.length;
	}

	peek() {
		"Return current character without consuming.";
		if (this.atEnd()) {
			return null;
		}
		return this.source[this.pos];
	}

	advance() {
		"Consume and return current character.";
		if (this.atEnd()) {
			return null;
		}
		var ch = this.source[this.pos];
		this.pos += 1;
		return ch;
	}

	skipWhitespace() {
		"Skip spaces, tabs, comments, and backslash-newline continuations.";
		while (!this.atEnd()) {
			var ch = this.peek();
			if (IsWhitespaceNoNewline(ch)) {
				this.advance();
			} else if (ch === "#") {
				while (!this.atEnd() && this.peek() !== "\n") {
					this.advance();
				}
			} else if (
				ch === "\\" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "\n"
			) {
				this.advance();
				this.advance();
			} else {
				break;
			}
		}
	}

	skipWhitespaceAndNewlines() {
		"Skip spaces, tabs, newlines, comments, and backslash-newline continuations.";
		while (!this.atEnd()) {
			var ch = this.peek();
			if (IsWhitespace(ch)) {
				this.advance();
				if (ch === "\n") {
					if (
						this._pending_heredoc_end != null &&
						this._pending_heredoc_end > this.pos
					) {
						this.pos = this._pending_heredoc_end;
						this._pending_heredoc_end = null;
					}
				}
			} else if (ch === "#") {
				while (!this.atEnd() && this.peek() !== "\n") {
					this.advance();
				}
			} else if (
				ch === "\\" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "\n"
			) {
				this.advance();
				this.advance();
			} else {
				break;
			}
		}
	}

	peekWord() {
		"Peek at the next word without consuming it.";
		var saved_pos = this.pos;
		this.skipWhitespace();
		if (this.atEnd() || IsMetachar(this.peek())) {
			this.pos = saved_pos;
			return null;
		}
		var chars = [];
		while (!this.atEnd() && !IsMetachar(this.peek())) {
			var ch = this.peek();
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
		"Try to consume a specific reserved word. Returns True if successful.";
		var saved_pos = this.pos;
		this.skipWhitespace();
		var word = this.peekWord();
		if (word !== expected) {
			this.pos = saved_pos;
			return false;
		}
		this.skipWhitespace();
		for (var _ of expected) {
			this.advance();
		}
		return true;
	}

	parseWord(at_command_start) {
		if (at_command_start == null) {
			at_command_start = false;
		}
		("Parse a word token, detecting parameter expansions and command substitutions.\n\n        at_command_start: When True, preserve spaces inside brackets for array\n        assignments like a[1 + 2]=. When False, spaces break the word.\n        ");
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
			if (ch === "[" && chars && at_command_start && !seen_equals) {
				var prev_char = chars[chars.length - 1];
				if (
					/^[a-zA-Z0-9]$/.test(prev_char) ||
					prev_char === "_" ||
					prev_char === "]"
				) {
					bracket_depth += 1;
					chars.push(this.advance());
					continue;
				}
			}
			if (ch === "]" && bracket_depth > 0) {
				bracket_depth -= 1;
				chars.push(this.advance());
				continue;
			}
			if (ch === "=" && bracket_depth === 0) {
				seen_equals = true;
			}
			if (ch === "'") {
				this.advance();
				chars.push("'");
				while (!this.atEnd() && this.peek() !== "'") {
					chars.push(this.advance());
				}
				if (this.atEnd()) {
					throw new ParseError("Unterminated single quote", start);
				}
				chars.push(this.advance());
			} else if (ch === '"') {
				this.advance();
				chars.push('"');
				while (!this.atEnd() && this.peek() !== '"') {
					var c = this.peek();
					if (c === "\\" && this.pos + 1 < this.length) {
						var next_c = this.source[this.pos + 1];
						if (next_c === "\n") {
							this.advance();
							this.advance();
						} else {
							chars.push(this.advance());
							chars.push(this.advance());
						}
					} else if (
						c === "$" &&
						this.pos + 2 < this.length &&
						this.source[this.pos + 1] === "(" &&
						this.source[this.pos + 2] === "("
					) {
						var arith_result = this.ParseArithmeticExpansion();
						var arith_node = arith_result[0];
						var arith_text = arith_result[1];
						if (arith_node) {
							parts.push(arith_node);
							chars.push(arith_text);
						} else {
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
					} else if (
						c === "$" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "["
					) {
						arith_result = this.ParseDeprecatedArithmetic();
						arith_node = arith_result[0];
						arith_text = arith_result[1];
						if (arith_node) {
							parts.push(arith_node);
							chars.push(arith_text);
						} else {
							chars.push(this.advance());
						}
					} else if (
						c === "$" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "("
					) {
						cmdsub_result = this.ParseCommandSubstitution();
						cmdsub_node = cmdsub_result[0];
						cmdsub_text = cmdsub_result[1];
						if (cmdsub_node) {
							parts.push(cmdsub_node);
							chars.push(cmdsub_text);
						} else {
							chars.push(this.advance());
						}
					} else if (c === "$") {
						var param_result = this.ParseParamExpansion();
						var param_node = param_result[0];
						var param_text = param_result[1];
						if (param_node) {
							parts.push(param_node);
							chars.push(param_text);
						} else {
							chars.push(this.advance());
						}
					} else if (c === "`") {
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
			} else if (ch === "\\" && this.pos + 1 < this.length) {
				var next_ch = this.source[this.pos + 1];
				if (next_ch === "\n") {
					this.advance();
					this.advance();
				} else {
					chars.push(this.advance());
					chars.push(this.advance());
				}
			} else if (
				ch === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "'"
			) {
				var ansi_result = this.ParseAnsiCQuote();
				var ansi_node = ansi_result[0];
				var ansi_text = ansi_result[1];
				if (ansi_node) {
					parts.push(ansi_node);
					chars.push(ansi_text);
				} else {
					chars.push(this.advance());
				}
			} else if (
				ch === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === '"'
			) {
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
			} else if (
				ch === "$" &&
				this.pos + 2 < this.length &&
				this.source[this.pos + 1] === "(" &&
				this.source[this.pos + 2] === "("
			) {
				arith_result = this.ParseArithmeticExpansion();
				arith_node = arith_result[0];
				arith_text = arith_result[1];
				if (arith_node) {
					parts.push(arith_node);
					chars.push(arith_text);
				} else {
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
			} else if (
				ch === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "["
			) {
				arith_result = this.ParseDeprecatedArithmetic();
				arith_node = arith_result[0];
				arith_text = arith_result[1];
				if (arith_node) {
					parts.push(arith_node);
					chars.push(arith_text);
				} else {
					chars.push(this.advance());
				}
			} else if (
				ch === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				cmdsub_result = this.ParseCommandSubstitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					parts.push(cmdsub_node);
					chars.push(cmdsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "$") {
				param_result = this.ParseParamExpansion();
				param_node = param_result[0];
				param_text = param_result[1];
				if (param_node) {
					parts.push(param_node);
					chars.push(param_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "`") {
				cmdsub_result = this.ParseBacktickSubstitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					parts.push(cmdsub_node);
					chars.push(cmdsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (
				IsRedirectChar(ch) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				var procsub_result = this.ParseProcessSubstitution();
				var procsub_node = procsub_result[0];
				var procsub_text = procsub_result[1];
				if (procsub_node) {
					parts.push(procsub_node);
					chars.push(procsub_text);
				} else {
					break;
				}
			} else if (
				ch === "(" &&
				chars &&
				(chars[chars.length - 1] === "=" ||
					(chars.length >= 2 &&
						chars[chars.length - 2] === "+" &&
						chars[chars.length - 1] === "="))
			) {
				var array_result = this.ParseArrayLiteral();
				var array_node = array_result[0];
				var array_text = array_result[1];
				if (array_node) {
					parts.push(array_node);
					chars.push(array_text);
				} else {
					break;
				}
			} else if (
				IsExtglobPrefix(ch) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				chars.push(this.advance());
				chars.push(this.advance());
				var extglob_depth = 1;
				while (!this.atEnd() && extglob_depth > 0) {
					c = this.peek();
					if (c === ")") {
						chars.push(this.advance());
						extglob_depth -= 1;
					} else if (c === "(") {
						chars.push(this.advance());
						extglob_depth += 1;
					} else if (c === "\\") {
						chars.push(this.advance());
						if (!this.atEnd()) {
							chars.push(this.advance());
						}
					} else if (c === "'") {
						chars.push(this.advance());
						while (!this.atEnd() && this.peek() !== "'") {
							chars.push(this.advance());
						}
						if (!this.atEnd()) {
							chars.push(this.advance());
						}
					} else if (c === '"') {
						chars.push(this.advance());
						while (!this.atEnd() && this.peek() !== '"') {
							if (this.peek() === "\\" && this.pos + 1 < this.length) {
								chars.push(this.advance());
							}
							chars.push(this.advance());
						}
						if (!this.atEnd()) {
							chars.push(this.advance());
						}
					} else if (
						c === "$" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "("
					) {
						chars.push(this.advance());
						chars.push(this.advance());
						if (!this.atEnd() && this.peek() === "(") {
							chars.push(this.advance());
							var paren_depth = 2;
							while (!this.atEnd() && paren_depth > 0) {
								var pc = this.peek();
								if (pc === "(") {
									paren_depth += 1;
								} else if (pc === ")") {
									paren_depth -= 1;
								}
								chars.push(this.advance());
							}
						} else {
							extglob_depth += 1;
						}
					} else if (
						IsExtglobPrefix(c) &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "("
					) {
						chars.push(this.advance());
						chars.push(this.advance());
						extglob_depth += 1;
					} else {
						chars.push(this.advance());
					}
				}
			} else if (IsMetachar(ch) && bracket_depth === 0) {
				break;
			} else {
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
		"Parse a $(...) command substitution.\n\n        Returns (node, text) where node is CommandSubstitution and text is raw text.\n        ";
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		var start = this.pos;
		this.advance();
		if (this.atEnd() || this.peek() !== "(") {
			this.pos = start;
			return [null, ""];
		}
		this.advance();
		var content_start = this.pos;
		var depth = 1;
		var case_depth = 0;
		while (!this.atEnd() && depth > 0) {
			var c = this.peek();
			if (c === "'") {
				this.advance();
				while (!this.atEnd() && this.peek() !== "'") {
					this.advance();
				}
				if (!this.atEnd()) {
					this.advance();
				}
				continue;
			}
			if (c === '"') {
				this.advance();
				while (!this.atEnd() && this.peek() !== '"') {
					if (this.peek() === "\\" && this.pos + 1 < this.length) {
						this.advance();
						this.advance();
					} else if (
						this.peek() === "$" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "("
					) {
						this.advance();
						this.advance();
						var nested_depth = 1;
						while (!this.atEnd() && nested_depth > 0) {
							var nc = this.peek();
							if (nc === "'") {
								this.advance();
								while (!this.atEnd() && this.peek() !== "'") {
									this.advance();
								}
								if (!this.atEnd()) {
									this.advance();
								}
							} else if (nc === '"') {
								this.advance();
								while (!this.atEnd() && this.peek() !== '"') {
									if (this.peek() === "\\" && this.pos + 1 < this.length) {
										this.advance();
									}
									this.advance();
								}
								if (!this.atEnd()) {
									this.advance();
								}
							} else if (nc === "\\" && this.pos + 1 < this.length) {
								this.advance();
								this.advance();
							} else if (
								nc === "$" &&
								this.pos + 1 < this.length &&
								this.source[this.pos + 1] === "("
							) {
								this.advance();
								this.advance();
								nested_depth += 1;
							} else if (nc === "(") {
								nested_depth += 1;
								this.advance();
							} else if (nc === ")") {
								nested_depth -= 1;
								if (nested_depth > 0) {
									this.advance();
								}
							} else {
								this.advance();
							}
						}
						if (nested_depth === 0) {
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
			if (c === "\\" && this.pos + 1 < this.length) {
				this.advance();
				this.advance();
				continue;
			}
			if (c === "#" && this.IsWordBoundaryBefore()) {
				while (!this.atEnd() && this.peek() !== "\n") {
					this.advance();
				}
				continue;
			}
			if (
				c === "<" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "<"
			) {
				this.advance();
				this.advance();
				if (!this.atEnd() && this.peek() === "-") {
					this.advance();
				}
				while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
					this.advance();
				}
				var delimiter_chars = [];
				if (!this.atEnd()) {
					var ch = this.peek();
					if (IsQuote(ch)) {
						var quote = this.advance();
						while (!this.atEnd() && this.peek() !== quote) {
							delimiter_chars.push(this.advance());
						}
						if (!this.atEnd()) {
							this.advance();
						}
					} else if (ch === "\\") {
						this.advance();
						if (!this.atEnd()) {
							delimiter_chars.push(this.advance());
						}
						while (!this.atEnd() && !IsMetachar(this.peek())) {
							delimiter_chars.push(this.advance());
						}
					} else {
						while (!this.atEnd() && !IsMetachar(this.peek())) {
							ch = this.peek();
							if (IsQuote(ch)) {
								quote = this.advance();
								while (!this.atEnd() && this.peek() !== quote) {
									delimiter_chars.push(this.advance());
								}
								if (!this.atEnd()) {
									this.advance();
								}
							} else if (ch === "\\") {
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
					while (!this.atEnd() && this.peek() !== "\n") {
						this.advance();
					}
					if (!this.atEnd() && this.peek() === "\n") {
						this.advance();
					}
					while (!this.atEnd()) {
						var line_start = this.pos;
						var line_end = this.pos;
						while (line_end < this.length && this.source[line_end] !== "\n") {
							line_end += 1;
						}
						var line = Substring(this.source, line_start, line_end);
						this.pos = line_end;
						if (
							line === delimiter ||
							line.replace(new RegExp("^[" + "\t" + "]+"), "") === delimiter
						) {
							if (!this.atEnd() && this.peek() === "\n") {
								this.advance();
							}
							break;
						}
						if (!this.atEnd() && this.peek() === "\n") {
							this.advance();
						}
					}
				}
				continue;
			}
			if (c === "c" && this.IsWordBoundaryBefore()) {
				if (this.LookaheadKeyword("case")) {
					case_depth += 1;
					this.SkipKeyword("case");
					continue;
				}
			}
			if (c === "e" && this.IsWordBoundaryBefore() && case_depth > 0) {
				if (this.LookaheadKeyword("esac")) {
					case_depth -= 1;
					this.SkipKeyword("esac");
					continue;
				}
			}
			if (c === "(") {
				depth += 1;
			} else if (c === ")") {
				if (case_depth > 0 && depth === 1) {
					var saved = this.pos;
					this.advance();
					var temp_depth = 0;
					var temp_case_depth = case_depth;
					var found_esac = false;
					while (!this.atEnd()) {
						var tc = this.peek();
						if (tc === "'" || tc === '"') {
							var q = tc;
							this.advance();
							while (!this.atEnd() && this.peek() !== q) {
								if (q === '"' && this.peek() === "\\") {
									this.advance();
								}
								this.advance();
							}
							if (!this.atEnd()) {
								this.advance();
							}
						} else if (
							tc === "c" &&
							this.IsWordBoundaryBefore() &&
							this.LookaheadKeyword("case")
						) {
							temp_case_depth += 1;
							this.SkipKeyword("case");
						} else if (
							tc === "e" &&
							this.IsWordBoundaryBefore() &&
							this.LookaheadKeyword("esac")
						) {
							temp_case_depth -= 1;
							if (temp_case_depth === 0) {
								found_esac = true;
								break;
							}
							this.SkipKeyword("esac");
						} else if (tc === "(") {
							temp_depth += 1;
							this.advance();
						} else if (tc === ")") {
							if (temp_case_depth > 0) {
								this.advance();
							} else if (temp_depth > 0) {
								temp_depth -= 1;
								this.advance();
							} else {
								break;
							}
						} else {
							this.advance();
						}
					}
					this.pos = saved;
					if (found_esac) {
						this.advance();
						continue;
					}
				}
				depth -= 1;
			}
			if (depth > 0) {
				this.advance();
			}
		}
		if (depth !== 0) {
			this.pos = start;
			return [null, ""];
		}
		var content = Substring(this.source, content_start, this.pos);
		this.advance();
		var text = Substring(this.source, start, this.pos);
		var sub_parser = new Parser(content);
		var cmd = sub_parser.parseList();
		if (cmd == null) {
			cmd = new Empty();
		}
		return [new CommandSubstitution(cmd), text];
	}

	IsWordBoundaryBefore() {
		"Check if current position is at a word boundary (preceded by space/newline/start).";
		if (this.pos === 0) {
			return true;
		}
		var prev = this.source[this.pos - 1];
		return IsWordStartContext(prev);
	}

	IsAssignmentWord(word) {
		"Check if a word is an assignment (contains = outside of quotes).";
		var in_single = false;
		var in_double = false;
		var i = 0;
		while (i < word.value.length) {
			var ch = word.value[i];
			if (ch === "'" && !in_double) {
				in_single = !in_single;
			} else if (ch === '"' && !in_single) {
				in_double = !in_double;
			} else if (ch === "\\" && !in_single && i + 1 < word.value.length) {
				i += 1;
				continue;
			} else if (ch === "=" && !in_single && !in_double) {
				return true;
			}
			i += 1;
		}
		return false;
	}

	LookaheadKeyword(keyword) {
		"Check if keyword appears at current position followed by word boundary.";
		if (this.pos + keyword.length > this.length) {
			return false;
		}
		if (!StartsWithAt(this.source, this.pos, keyword)) {
			return false;
		}
		var after_pos = this.pos + keyword.length;
		if (after_pos >= this.length) {
			return true;
		}
		var after = this.source[after_pos];
		return IsWordEndContext(after);
	}

	SkipKeyword(keyword) {
		"Skip over a keyword.";
		for (var _ of keyword) {
			this.advance();
		}
	}

	ParseBacktickSubstitution() {
		"Parse a `...` command substitution.\n\n        Returns (node, text) where node is CommandSubstitution and text is raw text.\n        ";
		if (this.atEnd() || this.peek() !== "`") {
			return [null, ""];
		}
		var start = this.pos;
		this.advance();
		var content_chars = [];
		var text_chars = ["`"];
		while (!this.atEnd() && this.peek() !== "`") {
			var c = this.peek();
			if (c === "\\" && this.pos + 1 < this.length) {
				var next_c = this.source[this.pos + 1];
				if (next_c === "\n") {
					this.advance();
					this.advance();
				} else if (IsEscapeCharInDquote(next_c)) {
					this.advance();
					var escaped = this.advance();
					content_chars.push(escaped);
					text_chars.push("\\");
					text_chars.push(escaped);
				} else {
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
		var sub_parser = new Parser(content);
		var cmd = sub_parser.parseList();
		if (cmd == null) {
			cmd = new Empty();
		}
		return [new CommandSubstitution(cmd), text];
	}

	ParseProcessSubstitution() {
		"Parse a <(...) or >(...) process substitution.\n\n        Returns (node, text) where node is ProcessSubstitution and text is raw text.\n        ";
		if (this.atEnd() || !IsRedirectChar(this.peek())) {
			return [null, ""];
		}
		var start = this.pos;
		var direction = this.advance();
		if (this.atEnd() || this.peek() !== "(") {
			this.pos = start;
			return [null, ""];
		}
		this.advance();
		var content_start = this.pos;
		var depth = 1;
		while (!this.atEnd() && depth > 0) {
			var c = this.peek();
			if (c === "'") {
				this.advance();
				while (!this.atEnd() && this.peek() !== "'") {
					this.advance();
				}
				if (!this.atEnd()) {
					this.advance();
				}
				continue;
			}
			if (c === '"') {
				this.advance();
				while (!this.atEnd() && this.peek() !== '"') {
					if (this.peek() === "\\" && this.pos + 1 < this.length) {
						this.advance();
					}
					this.advance();
				}
				if (!this.atEnd()) {
					this.advance();
				}
				continue;
			}
			if (c === "\\" && this.pos + 1 < this.length) {
				this.advance();
				this.advance();
				continue;
			}
			if (c === "(") {
				depth += 1;
			} else if (c === ")") {
				depth -= 1;
				if (depth === 0) {
					break;
				}
			}
			this.advance();
		}
		if (depth !== 0) {
			this.pos = start;
			return [null, ""];
		}
		var content = Substring(this.source, content_start, this.pos);
		this.advance();
		var text = Substring(this.source, start, this.pos);
		var sub_parser = new Parser(content);
		var cmd = sub_parser.parseList();
		if (cmd == null) {
			cmd = new Empty();
		}
		return [new ProcessSubstitution(direction, cmd), text];
	}

	ParseArrayLiteral() {
		"Parse an array literal (word1 word2 ...).\n\n        Returns (node, text) where node is Array and text is raw text.\n        Called when positioned at the opening '(' after '=' or '+='.\n        ";
		if (this.atEnd() || this.peek() !== "(") {
			return [null, ""];
		}
		var start = this.pos;
		this.advance();
		var elements = [];
		while (true) {
			while (!this.atEnd() && IsWhitespace(this.peek())) {
				this.advance();
			}
			if (this.atEnd()) {
				throw new ParseError("Unterminated array literal", start);
			}
			if (this.peek() === ")") {
				break;
			}
			var word = this.parseWord();
			if (word == null) {
				if (this.peek() === ")") {
					break;
				}
				throw new ParseError("Expected word in array literal", this.pos);
			}
			elements.push(word);
		}
		if (this.atEnd() || this.peek() !== ")") {
			throw new ParseError("Expected ) to close array literal", this.pos);
		}
		this.advance();
		var text = Substring(this.source, start, this.pos);
		return [new ArrayNode(elements), text];
	}

	ParseArithmeticExpansion() {
		"Parse a $((...)) arithmetic expansion with parsed internals.\n\n        Returns (node, text) where node is ArithmeticExpansion and text is raw text.\n        Returns (None, \"\") if this is not arithmetic expansion (e.g., $( ( ... ) )\n        which is command substitution containing a subshell).\n        ";
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		var start = this.pos;
		if (
			this.pos + 2 >= this.length ||
			this.source[this.pos + 1] !== "(" ||
			this.source[this.pos + 2] !== "("
		) {
			return [null, ""];
		}
		this.advance();
		this.advance();
		this.advance();
		var content_start = this.pos;
		var depth = 1;
		while (!this.atEnd() && depth > 0) {
			var c = this.peek();
			if (c === "(") {
				depth += 1;
				this.advance();
			} else if (c === ")") {
				if (
					depth === 1 &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === ")"
				) {
					break;
				}
				depth -= 1;
				if (depth === 0) {
					this.pos = start;
					return [null, ""];
				}
				this.advance();
			} else {
				this.advance();
			}
		}
		if (this.atEnd() || depth !== 1) {
			this.pos = start;
			return [null, ""];
		}
		var content = Substring(this.source, content_start, this.pos);
		this.advance();
		this.advance();
		var text = Substring(this.source, start, this.pos);
		var expr = this.ParseArithExpr(content);
		return [new ArithmeticExpansion(expr), text];
	}

	ParseArithExpr(content) {
		"Parse an arithmetic expression string into AST nodes.";
		var saved_arith_src =
			this["_arith_src"] !== undefined ? this["_arith_src"] : null;
		var saved_arith_pos =
			this["_arith_pos"] !== undefined ? this["_arith_pos"] : null;
		var saved_arith_len =
			this["_arith_len"] !== undefined ? this["_arith_len"] : null;
		this._arith_src = content;
		this._arith_pos = 0;
		this._arith_len = content.length;
		this.ArithSkipWs();
		if (this.ArithAtEnd()) {
			var result = null;
		} else {
			result = this.ArithParseComma();
		}
		if (saved_arith_src != null) {
			this._arith_src = saved_arith_src;
			this._arith_pos = saved_arith_pos;
			this._arith_len = saved_arith_len;
		}
		return result;
	}

	ArithAtEnd() {
		return this._arith_pos >= this._arith_len;
	}

	ArithPeek(offset) {
		if (offset == null) {
			offset = 0;
		}
		var pos = this._arith_pos + offset;
		if (pos >= this._arith_len) {
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
			} else if (
				c === "\\" &&
				this._arith_pos + 1 < this._arith_len &&
				this._arith_src[this._arith_pos + 1] === "\n"
			) {
				this._arith_pos += 2;
			} else {
				break;
			}
		}
	}

	ArithMatch(s) {
		"Check if the next characters match s (without consuming).";
		return StartsWithAt(this._arith_src, this._arith_pos, s);
	}

	ArithConsume(s) {
		"If next chars match s, consume them and return True.";
		if (this.ArithMatch(s)) {
			this._arith_pos += s.length;
			return true;
		}
		return false;
	}

	ArithParseComma() {
		"Parse comma expressions (lowest precedence).";
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
		"Parse assignment expressions (right associative).";
		var left = this.ArithParseTernary();
		this.ArithSkipWs();
		var assign_ops = [
			"<<=",
			">>=",
			"+=",
			"-=",
			"*=",
			"/=",
			"%=",
			"&=",
			"^=",
			"|=",
			"=",
		];
		for (var op of assign_ops) {
			if (this.ArithMatch(op)) {
				if (op === "=" && this.ArithPeek(1) === "=") {
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
		"Parse ternary conditional (right associative).";
		var cond = this.ArithParseLogicalOr();
		this.ArithSkipWs();
		if (this.ArithConsume("?")) {
			this.ArithSkipWs();
			if (this.ArithMatch(":")) {
				var if_true = null;
			} else {
				if_true = this.ArithParseAssign();
			}
			this.ArithSkipWs();
			if (this.ArithConsume(":")) {
				this.ArithSkipWs();
				if (this.ArithAtEnd() || this.ArithPeek() === ")") {
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
		"Parse logical or (||).";
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
		"Parse logical and (&&).";
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
		"Parse bitwise or (|).";
		var left = this.ArithParseBitwiseXor();
		while (true) {
			this.ArithSkipWs();
			if (
				this.ArithPeek() === "|" &&
				this.ArithPeek(1) !== "|" &&
				this.ArithPeek(1) !== "="
			) {
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
		"Parse bitwise xor (^).";
		var left = this.ArithParseBitwiseAnd();
		while (true) {
			this.ArithSkipWs();
			if (this.ArithPeek() === "^" && this.ArithPeek(1) !== "=") {
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
		"Parse bitwise and (&).";
		var left = this.ArithParseEquality();
		while (true) {
			this.ArithSkipWs();
			if (
				this.ArithPeek() === "&" &&
				this.ArithPeek(1) !== "&" &&
				this.ArithPeek(1) !== "="
			) {
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
		"Parse equality (== !=).";
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
		"Parse comparison (< > <= >=).";
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
			} else if (
				this.ArithPeek() === "<" &&
				this.ArithPeek(1) !== "<" &&
				this.ArithPeek(1) !== "="
			) {
				this.ArithAdvance();
				this.ArithSkipWs();
				right = this.ArithParseShift();
				left = new ArithBinaryOp("<", left, right);
			} else if (
				this.ArithPeek() === ">" &&
				this.ArithPeek(1) !== ">" &&
				this.ArithPeek(1) !== "="
			) {
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
		"Parse shift (<< >>).";
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
		"Parse addition and subtraction (+ -).";
		var left = this.ArithParseMultiplicative();
		while (true) {
			this.ArithSkipWs();
			var c = this.ArithPeek();
			var c2 = this.ArithPeek(1);
			if (c === "+" && c2 !== "+" && c2 !== "=") {
				this.ArithAdvance();
				this.ArithSkipWs();
				var right = this.ArithParseMultiplicative();
				left = new ArithBinaryOp("+", left, right);
			} else if (c === "-" && c2 !== "-" && c2 !== "=") {
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
		"Parse multiplication, division, modulo (* / %).";
		var left = this.ArithParseExponentiation();
		while (true) {
			this.ArithSkipWs();
			var c = this.ArithPeek();
			var c2 = this.ArithPeek(1);
			if (c === "*" && c2 !== "*" && c2 !== "=") {
				this.ArithAdvance();
				this.ArithSkipWs();
				var right = this.ArithParseExponentiation();
				left = new ArithBinaryOp("*", left, right);
			} else if (c === "/" && c2 !== "=") {
				this.ArithAdvance();
				this.ArithSkipWs();
				right = this.ArithParseExponentiation();
				left = new ArithBinaryOp("/", left, right);
			} else if (c === "%" && c2 !== "=") {
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
		"Parse exponentiation (**) - right associative.";
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
		"Parse unary operators (! ~ + - ++ --).";
		this.ArithSkipWs();
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
		var c = this.ArithPeek();
		if (c === "!") {
			this.ArithAdvance();
			this.ArithSkipWs();
			operand = this.ArithParseUnary();
			return new ArithUnaryOp("!", operand);
		}
		if (c === "~") {
			this.ArithAdvance();
			this.ArithSkipWs();
			operand = this.ArithParseUnary();
			return new ArithUnaryOp("~", operand);
		}
		if (c === "+" && this.ArithPeek(1) !== "+") {
			this.ArithAdvance();
			this.ArithSkipWs();
			operand = this.ArithParseUnary();
			return new ArithUnaryOp("+", operand);
		}
		if (c === "-" && this.ArithPeek(1) !== "-") {
			this.ArithAdvance();
			this.ArithSkipWs();
			operand = this.ArithParseUnary();
			return new ArithUnaryOp("-", operand);
		}
		return this.ArithParsePostfix();
	}

	ArithParsePostfix() {
		"Parse postfix operators (++ -- []).";
		var left = this.ArithParsePrimary();
		while (true) {
			this.ArithSkipWs();
			if (this.ArithMatch("++")) {
				this.ArithConsume("++");
				left = new ArithPostIncr(left);
			} else if (this.ArithMatch("--")) {
				this.ArithConsume("--");
				left = new ArithPostDecr(left);
			} else if (this.ArithPeek() === "[") {
				if (left.kind === "var") {
					this.ArithAdvance();
					this.ArithSkipWs();
					var index = this.ArithParseComma();
					this.ArithSkipWs();
					if (!this.ArithConsume("]")) {
						throw new ParseError(
							"Expected ']' in array subscript",
							this._arith_pos,
						);
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
		"Parse primary expressions (numbers, variables, parens, expansions).";
		this.ArithSkipWs();
		var c = this.ArithPeek();
		if (c === "(") {
			this.ArithAdvance();
			this.ArithSkipWs();
			var expr = this.ArithParseComma();
			this.ArithSkipWs();
			if (!this.ArithConsume(")")) {
				throw new ParseError(
					"Expected ')' in arithmetic expression",
					this._arith_pos,
				);
			}
			return expr;
		}
		if (c === "$") {
			return this.ArithParseExpansion();
		}
		if (c === "'") {
			return this.ArithParseSingleQuote();
		}
		if (c === '"') {
			return this.ArithParseDoubleQuote();
		}
		if (c === "`") {
			return this.ArithParseBacktick();
		}
		if (c === "\\") {
			this.ArithAdvance();
			if (this.ArithAtEnd()) {
				throw new ParseError(
					"Unexpected end after backslash in arithmetic",
					this._arith_pos,
				);
			}
			var escaped_char = this.ArithAdvance();
			return new ArithEscape(escaped_char);
		}
		return this.ArithParseNumberOrVar();
	}

	ArithParseExpansion() {
		"Parse $var, ${...}, or $(...).";
		if (!this.ArithConsume("$")) {
			throw new ParseError("Expected '$'", this._arith_pos);
		}
		var c = this.ArithPeek();
		if (c === "(") {
			return this.ArithParseCmdsub();
		}
		if (c === "{") {
			return this.ArithParseBracedParam();
		}
		var name_chars = [];
		while (!this.ArithAtEnd()) {
			var ch = this.ArithPeek();
			if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
				name_chars.push(this.ArithAdvance());
			} else if (
				(IsSpecialParamOrDigit(ch) || ch === "#") &&
				name_chars.length === 0
			) {
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
		"Parse $(...) command substitution inside arithmetic.";
		this.ArithAdvance();
		if (this.ArithPeek() === "(") {
			this.ArithAdvance();
			var depth = 1;
			var content_start = this._arith_pos;
			while (!this.ArithAtEnd() && depth > 0) {
				var ch = this.ArithPeek();
				if (ch === "(") {
					depth += 1;
					this.ArithAdvance();
				} else if (ch === ")") {
					if (depth === 1 && this.ArithPeek(1) === ")") {
						break;
					}
					depth -= 1;
					this.ArithAdvance();
				} else {
					this.ArithAdvance();
				}
			}
			var content = Substring(this._arith_src, content_start, this._arith_pos);
			this.ArithAdvance();
			this.ArithAdvance();
			var inner_expr = this.ParseArithExpr(content);
			return new ArithmeticExpansion(inner_expr);
		}
		depth = 1;
		content_start = this._arith_pos;
		while (!this.ArithAtEnd() && depth > 0) {
			ch = this.ArithPeek();
			if (ch === "(") {
				depth += 1;
				this.ArithAdvance();
			} else if (ch === ")") {
				depth -= 1;
				if (depth === 0) {
					break;
				}
				this.ArithAdvance();
			} else {
				this.ArithAdvance();
			}
		}
		content = Substring(this._arith_src, content_start, this._arith_pos);
		this.ArithAdvance();
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
		"Parse ${...} parameter expansion inside arithmetic.";
		this.ArithAdvance();
		if (this.ArithPeek() === "!") {
			this.ArithAdvance();
			var name_chars = [];
			while (!this.ArithAtEnd() && this.ArithPeek() !== "}") {
				name_chars.push(this.ArithAdvance());
			}
			this.ArithConsume("}");
			return new ParamIndirect(name_chars.join(""));
		}
		if (this.ArithPeek() === "#") {
			this.ArithAdvance();
			name_chars = [];
			while (!this.ArithAtEnd() && this.ArithPeek() !== "}") {
				name_chars.push(this.ArithAdvance());
			}
			this.ArithConsume("}");
			return new ParamLength(name_chars.join(""));
		}
		name_chars = [];
		while (!this.ArithAtEnd()) {
			var ch = this.ArithPeek();
			if (ch === "}") {
				this.ArithAdvance();
				return new ParamExpansion(name_chars.join(""));
			}
			if (IsParamExpansionOp(ch)) {
				break;
			}
			name_chars.push(this.ArithAdvance());
		}
		var name = name_chars.join("");
		var op_chars = [];
		var depth = 1;
		while (!this.ArithAtEnd() && depth > 0) {
			ch = this.ArithPeek();
			if (ch === "{") {
				depth += 1;
				op_chars.push(this.ArithAdvance());
			} else if (ch === "}") {
				depth -= 1;
				if (depth === 0) {
					break;
				}
				op_chars.push(this.ArithAdvance());
			} else {
				op_chars.push(this.ArithAdvance());
			}
		}
		this.ArithConsume("}");
		var op_str = op_chars.join("");
		if (op_str.startsWith(":-")) {
			return new ParamExpansion(
				name,
				":-",
				Substring(op_str, 2, op_str.length),
			);
		}
		if (op_str.startsWith(":=")) {
			return new ParamExpansion(
				name,
				":=",
				Substring(op_str, 2, op_str.length),
			);
		}
		if (op_str.startsWith(":+")) {
			return new ParamExpansion(
				name,
				":+",
				Substring(op_str, 2, op_str.length),
			);
		}
		if (op_str.startsWith(":?")) {
			return new ParamExpansion(
				name,
				":?",
				Substring(op_str, 2, op_str.length),
			);
		}
		if (op_str.startsWith(":")) {
			return new ParamExpansion(name, ":", Substring(op_str, 1, op_str.length));
		}
		if (op_str.startsWith("##")) {
			return new ParamExpansion(
				name,
				"##",
				Substring(op_str, 2, op_str.length),
			);
		}
		if (op_str.startsWith("#")) {
			return new ParamExpansion(name, "#", Substring(op_str, 1, op_str.length));
		}
		if (op_str.startsWith("%%")) {
			return new ParamExpansion(
				name,
				"%%",
				Substring(op_str, 2, op_str.length),
			);
		}
		if (op_str.startsWith("%")) {
			return new ParamExpansion(name, "%", Substring(op_str, 1, op_str.length));
		}
		if (op_str.startsWith("//")) {
			return new ParamExpansion(
				name,
				"//",
				Substring(op_str, 2, op_str.length),
			);
		}
		if (op_str.startsWith("/")) {
			return new ParamExpansion(name, "/", Substring(op_str, 1, op_str.length));
		}
		return new ParamExpansion(name, "", op_str);
	}

	ArithParseSingleQuote() {
		"Parse '...' inside arithmetic - returns content as a number/string.";
		this.ArithAdvance();
		var content_start = this._arith_pos;
		while (!this.ArithAtEnd() && this.ArithPeek() !== "'") {
			this.ArithAdvance();
		}
		var content = Substring(this._arith_src, content_start, this._arith_pos);
		if (!this.ArithConsume("'")) {
			throw new ParseError(
				"Unterminated single quote in arithmetic",
				this._arith_pos,
			);
		}
		return new ArithNumber(content);
	}

	ArithParseDoubleQuote() {
		"Parse \"...\" inside arithmetic - may contain expansions.";
		this.ArithAdvance();
		var content_start = this._arith_pos;
		while (!this.ArithAtEnd() && this.ArithPeek() !== '"') {
			var c = this.ArithPeek();
			if (c === "\\" && !this.ArithAtEnd()) {
				this.ArithAdvance();
				this.ArithAdvance();
			} else {
				this.ArithAdvance();
			}
		}
		var content = Substring(this._arith_src, content_start, this._arith_pos);
		if (!this.ArithConsume('"')) {
			throw new ParseError(
				"Unterminated double quote in arithmetic",
				this._arith_pos,
			);
		}
		return new ArithNumber(content);
	}

	ArithParseBacktick() {
		"Parse `...` command substitution inside arithmetic.";
		this.ArithAdvance();
		var content_start = this._arith_pos;
		while (!this.ArithAtEnd() && this.ArithPeek() !== "`") {
			var c = this.ArithPeek();
			if (c === "\\" && !this.ArithAtEnd()) {
				this.ArithAdvance();
				this.ArithAdvance();
			} else {
				this.ArithAdvance();
			}
		}
		var content = Substring(this._arith_src, content_start, this._arith_pos);
		if (!this.ArithConsume("`")) {
			throw new ParseError(
				"Unterminated backtick in arithmetic",
				this._arith_pos,
			);
		}
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
		"Parse a number or variable name.";
		this.ArithSkipWs();
		var chars = [];
		var c = this.ArithPeek();
		if (/^[0-9]+$/.test(c)) {
			while (!this.ArithAtEnd()) {
				var ch = this.ArithPeek();
				if (/^[a-zA-Z0-9]$/.test(ch) || ch === "#" || ch === "_") {
					chars.push(this.ArithAdvance());
				} else {
					break;
				}
			}
			return new ArithNumber(chars.join(""));
		}
		if (/^[a-zA-Z]$/.test(c) || c === "_") {
			while (!this.ArithAtEnd()) {
				ch = this.ArithPeek();
				if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
					chars.push(this.ArithAdvance());
				} else {
					break;
				}
			}
			return new ArithVar(chars.join(""));
		}
		throw new ParseError(
			"Unexpected character '" + c + "' in arithmetic expression",
			this._arith_pos,
		);
	}

	ParseDeprecatedArithmetic() {
		"Parse a deprecated $[expr] arithmetic expansion.\n\n        Returns (node, text) where node is ArithDeprecated and text is raw text.\n        ";
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		var start = this.pos;
		if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== "[") {
			return [null, ""];
		}
		this.advance();
		this.advance();
		var content_start = this.pos;
		var depth = 1;
		while (!this.atEnd() && depth > 0) {
			var c = this.peek();
			if (c === "[") {
				depth += 1;
				this.advance();
			} else if (c === "]") {
				depth -= 1;
				if (depth === 0) {
					break;
				}
				this.advance();
			} else {
				this.advance();
			}
		}
		if (this.atEnd() || depth !== 0) {
			this.pos = start;
			return [null, ""];
		}
		var content = Substring(this.source, content_start, this.pos);
		this.advance();
		var text = Substring(this.source, start, this.pos);
		return [new ArithDeprecated(content), text];
	}

	ParseAnsiCQuote() {
		"Parse ANSI-C quoting $'...'.\n\n        Returns (node, text) where node is the AST node and text is the raw text.\n        Returns (None, \"\") if not a valid ANSI-C quote.\n        ";
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== "'") {
			return [null, ""];
		}
		var start = this.pos;
		this.advance();
		this.advance();
		var content_chars = [];
		var found_close = false;
		while (!this.atEnd()) {
			var ch = this.peek();
			if (ch === "'") {
				this.advance();
				found_close = true;
				break;
			} else if (ch === "\\") {
				content_chars.push(this.advance());
				if (!this.atEnd()) {
					content_chars.push(this.advance());
				}
			} else {
				content_chars.push(this.advance());
			}
		}
		if (!found_close) {
			this.pos = start;
			return [null, ""];
		}
		var text = Substring(this.source, start, this.pos);
		var content = content_chars.join("");
		return [new AnsiCQuote(content), text];
	}

	ParseLocaleString() {
		"Parse locale translation $\"...\".\n\n        Returns (node, text, inner_parts) where:\n        - node is the LocaleString AST node\n        - text is the raw text including $\"...\"\n        - inner_parts is a list of expansion nodes found inside\n        Returns (None, \"\", []) if not a valid locale string.\n        ";
		if (this.atEnd() || this.peek() !== "$") {
			return [null, "", []];
		}
		if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== '"') {
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
			if (ch === '"') {
				this.advance();
				found_close = true;
				break;
			} else if (ch === "\\" && this.pos + 1 < this.length) {
				var next_ch = this.source[this.pos + 1];
				if (next_ch === "\n") {
					this.advance();
					this.advance();
				} else {
					content_chars.push(this.advance());
					content_chars.push(this.advance());
				}
			} else if (
				ch === "$" &&
				this.pos + 2 < this.length &&
				this.source[this.pos + 1] === "(" &&
				this.source[this.pos + 2] === "("
			) {
				var arith_result = this.ParseArithmeticExpansion();
				var arith_node = arith_result[0];
				var arith_text = arith_result[1];
				if (arith_node) {
					inner_parts.push(arith_node);
					content_chars.push(arith_text);
				} else {
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
			} else if (
				ch === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				cmdsub_result = this.ParseCommandSubstitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					inner_parts.push(cmdsub_node);
					content_chars.push(cmdsub_text);
				} else {
					content_chars.push(this.advance());
				}
			} else if (ch === "$") {
				var param_result = this.ParseParamExpansion();
				var param_node = param_result[0];
				var param_text = param_result[1];
				if (param_node) {
					inner_parts.push(param_node);
					content_chars.push(param_text);
				} else {
					content_chars.push(this.advance());
				}
			} else if (ch === "`") {
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
			this.pos = start;
			return [null, "", []];
		}
		var content = content_chars.join("");
		var text = '$"' + content + '"';
		return [new LocaleString(content), text, inner_parts];
	}

	ParseParamExpansion() {
		"Parse a parameter expansion starting at $.\n\n        Returns (node, text) where node is the AST node and text is the raw text.\n        Returns (None, \"\") if not a valid parameter expansion.\n        ";
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		var start = this.pos;
		this.advance();
		if (this.atEnd()) {
			this.pos = start;
			return [null, ""];
		}
		var ch = this.peek();
		if (ch === "{") {
			this.advance();
			return this.ParseBracedParam(start);
		}
		if (IsSpecialParamOrDigit(ch) || ch === "#") {
			this.advance();
			var text = Substring(this.source, start, this.pos);
			return [new ParamExpansion(ch), text];
		}
		if (/^[a-zA-Z]$/.test(ch) || ch === "_") {
			var name_start = this.pos;
			while (!this.atEnd()) {
				var c = this.peek();
				if (/^[a-zA-Z0-9]$/.test(c) || c === "_") {
					this.advance();
				} else {
					break;
				}
			}
			var name = Substring(this.source, name_start, this.pos);
			text = Substring(this.source, start, this.pos);
			return [new ParamExpansion(name), text];
		}
		this.pos = start;
		return [null, ""];
	}

	ParseBracedParam(start) {
		"Parse contents of ${...} after the opening brace.\n\n        start is the position of the $.\n        Returns (node, text).\n        ";
		if (this.atEnd()) {
			this.pos = start;
			return [null, ""];
		}
		var ch = this.peek();
		if (ch === "#") {
			this.advance();
			var param = this.ConsumeParamName();
			if (param && !this.atEnd() && this.peek() === "}") {
				this.advance();
				var text = Substring(this.source, start, this.pos);
				return [new ParamLength(param), text];
			}
			this.pos = start;
			return [null, ""];
		}
		if (ch === "!") {
			this.advance();
			param = this.ConsumeParamName();
			if (param) {
				while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
					this.advance();
				}
				if (!this.atEnd() && this.peek() === "}") {
					this.advance();
					text = Substring(this.source, start, this.pos);
					return [new ParamIndirect(param), text];
				}
				if (!this.atEnd() && IsAtOrStar(this.peek())) {
					var suffix = this.advance();
					while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
						this.advance();
					}
					if (!this.atEnd() && this.peek() === "}") {
						this.advance();
						text = Substring(this.source, start, this.pos);
						return [new ParamIndirect(param + suffix), text];
					}
					this.pos = start;
					return [null, ""];
				}
				var op = this.ConsumeParamOperator();
				if (op != null) {
					var arg_chars = [];
					var depth = 1;
					while (!this.atEnd() && depth > 0) {
						var c = this.peek();
						if (
							c === "$" &&
							this.pos + 1 < this.length &&
							this.source[this.pos + 1] === "{"
						) {
							depth += 1;
							arg_chars.push(this.advance());
							arg_chars.push(this.advance());
						} else if (c === "}") {
							depth -= 1;
							if (depth > 0) {
								arg_chars.push(this.advance());
							}
						} else if (c === "\\") {
							arg_chars.push(this.advance());
							if (!this.atEnd()) {
								arg_chars.push(this.advance());
							}
						} else {
							arg_chars.push(this.advance());
						}
					}
					if (depth === 0) {
						this.advance();
						var arg = arg_chars.join("");
						text = Substring(this.source, start, this.pos);
						return [new ParamIndirect(param, op, arg), text];
					}
				}
			}
			this.pos = start;
			return [null, ""];
		}
		param = this.ConsumeParamName();
		if (!param) {
			depth = 1;
			var content_start = this.pos;
			while (!this.atEnd() && depth > 0) {
				c = this.peek();
				if (c === "{") {
					depth += 1;
					this.advance();
				} else if (c === "}") {
					depth -= 1;
					if (depth === 0) {
						break;
					}
					this.advance();
				} else if (c === "\\") {
					this.advance();
					if (!this.atEnd()) {
						this.advance();
					}
				} else {
					this.advance();
				}
			}
			if (depth === 0) {
				var content = Substring(this.source, content_start, this.pos);
				this.advance();
				text = Substring(this.source, start, this.pos);
				return [new ParamExpansion(content), text];
			}
			this.pos = start;
			return [null, ""];
		}
		if (this.atEnd()) {
			this.pos = start;
			return [null, ""];
		}
		if (this.peek() === "}") {
			this.advance();
			text = Substring(this.source, start, this.pos);
			return [new ParamExpansion(param), text];
		}
		op = this.ConsumeParamOperator();
		if (op == null) {
			op = this.advance();
		}
		arg_chars = [];
		depth = 1;
		var in_single_quote = false;
		var in_double_quote = false;
		while (!this.atEnd() && depth > 0) {
			c = this.peek();
			if (c === "'" && !in_double_quote) {
				if (in_single_quote) {
					in_single_quote = false;
				} else {
					in_single_quote = true;
				}
				arg_chars.push(this.advance());
			} else if (c === '"' && !in_single_quote) {
				in_double_quote = !in_double_quote;
				arg_chars.push(this.advance());
			} else if (c === "\\" && !in_single_quote) {
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
					this.advance();
					this.advance();
				} else {
					arg_chars.push(this.advance());
					if (!this.atEnd()) {
						arg_chars.push(this.advance());
					}
				}
			} else if (
				c === "$" &&
				!in_single_quote &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "{"
			) {
				depth += 1;
				arg_chars.push(this.advance());
				arg_chars.push(this.advance());
			} else if (
				c === "$" &&
				!in_single_quote &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				arg_chars.push(this.advance());
				arg_chars.push(this.advance());
				var paren_depth = 1;
				while (!this.atEnd() && paren_depth > 0) {
					var pc = this.peek();
					if (pc === "(") {
						paren_depth += 1;
					} else if (pc === ")") {
						paren_depth -= 1;
					} else if (pc === "\\") {
						arg_chars.push(this.advance());
						if (!this.atEnd()) {
							arg_chars.push(this.advance());
						}
						continue;
					}
					arg_chars.push(this.advance());
				}
			} else if (c === "`" && !in_single_quote) {
				arg_chars.push(this.advance());
				while (!this.atEnd() && this.peek() !== "`") {
					var bc = this.peek();
					if (bc === "\\" && this.pos + 1 < this.length) {
						var next_c = this.source[this.pos + 1];
						if (IsEscapeCharInDquote(next_c)) {
							arg_chars.push(this.advance());
						}
					}
					arg_chars.push(this.advance());
				}
				if (!this.atEnd()) {
					arg_chars.push(this.advance());
				}
			} else if (c === "}") {
				if (in_single_quote) {
					arg_chars.push(this.advance());
				} else if (in_double_quote) {
					if (depth > 1) {
						depth -= 1;
						arg_chars.push(this.advance());
					} else {
						arg_chars.push(this.advance());
					}
				} else {
					depth -= 1;
					if (depth > 0) {
						arg_chars.push(this.advance());
					}
				}
			} else {
				arg_chars.push(this.advance());
			}
		}
		if (depth !== 0) {
			this.pos = start;
			return [null, ""];
		}
		this.advance();
		arg = arg_chars.join("");
		text = "${" + param + op + arg + "}";
		return [new ParamExpansion(param, op, arg), text];
	}

	ConsumeParamName() {
		"Consume a parameter name (variable name, special char, or array subscript).";
		if (this.atEnd()) {
			return null;
		}
		var ch = this.peek();
		if (IsSpecialParam(ch)) {
			this.advance();
			return ch;
		}
		if (/^[0-9]+$/.test(ch)) {
			var name_chars = [];
			while (!this.atEnd() && /^[0-9]+$/.test(this.peek())) {
				name_chars.push(this.advance());
			}
			return name_chars.join("");
		}
		if (/^[a-zA-Z]$/.test(ch) || ch === "_") {
			name_chars = [];
			while (!this.atEnd()) {
				var c = this.peek();
				if (/^[a-zA-Z0-9]$/.test(c) || c === "_") {
					name_chars.push(this.advance());
				} else if (c === "[") {
					name_chars.push(this.advance());
					var bracket_depth = 1;
					while (!this.atEnd() && bracket_depth > 0) {
						var sc = this.peek();
						if (sc === "[") {
							bracket_depth += 1;
						} else if (sc === "]") {
							bracket_depth -= 1;
							if (bracket_depth === 0) {
								break;
							}
						}
						name_chars.push(this.advance());
					}
					if (!this.atEnd() && this.peek() === "]") {
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
		"Consume a parameter expansion operator.";
		if (this.atEnd()) {
			return null;
		}
		var ch = this.peek();
		if (ch === ":") {
			this.advance();
			if (this.atEnd()) {
				return ":";
			}
			var next_ch = this.peek();
			if (IsSimpleParamOp(next_ch)) {
				this.advance();
				return ":" + next_ch;
			}
			return ":";
		}
		if (IsSimpleParamOp(ch)) {
			this.advance();
			return ch;
		}
		if (ch === "#") {
			this.advance();
			if (!this.atEnd() && this.peek() === "#") {
				this.advance();
				return "##";
			}
			return "#";
		}
		if (ch === "%") {
			this.advance();
			if (!this.atEnd() && this.peek() === "%") {
				this.advance();
				return "%%";
			}
			return "%";
		}
		if (ch === "/") {
			this.advance();
			if (!this.atEnd()) {
				next_ch = this.peek();
				if (next_ch === "/") {
					this.advance();
					return "//";
				} else if (next_ch === "#") {
					this.advance();
					return "/#";
				} else if (next_ch === "%") {
					this.advance();
					return "/%";
				}
			}
			return "/";
		}
		if (ch === "^") {
			this.advance();
			if (!this.atEnd() && this.peek() === "^") {
				this.advance();
				return "^^";
			}
			return "^";
		}
		if (ch === ",") {
			this.advance();
			if (!this.atEnd() && this.peek() === ",") {
				this.advance();
				return ",,";
			}
			return ",";
		}
		if (ch === "@") {
			this.advance();
			return "@";
		}
		return null;
	}

	parseRedirect() {
		"Parse a redirection operator and target.";
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		var start = this.pos;
		var fd = null;
		var varfd = null;
		if (this.peek() === "{") {
			var saved = this.pos;
			this.advance();
			var varname_chars = [];
			while (
				!this.atEnd() &&
				this.peek() !== "}" &&
				!IsRedirectChar(this.peek())
			) {
				var ch = this.peek();
				if (
					/^[a-zA-Z0-9]$/.test(ch) ||
					ch === "_" ||
					ch === "[" ||
					ch === "]"
				) {
					varname_chars.push(this.advance());
				} else {
					break;
				}
			}
			if (!this.atEnd() && this.peek() === "}" && varname_chars) {
				this.advance();
				varfd = varname_chars.join("");
			} else {
				this.pos = saved;
			}
		}
		if (varfd == null && this.peek() && /^[0-9]+$/.test(this.peek())) {
			var fd_chars = [];
			while (!this.atEnd() && /^[0-9]+$/.test(this.peek())) {
				fd_chars.push(this.advance());
			}
			fd = parseInt(fd_chars.join(""), 10);
		}
		ch = this.peek();
		if (
			ch === "&" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === ">"
		) {
			if (fd != null) {
				this.pos = start;
				return null;
			}
			this.advance();
			this.advance();
			if (!this.atEnd() && this.peek() === ">") {
				this.advance();
				var op = "&>>";
			} else {
				op = "&>";
			}
			this.skipWhitespace();
			var target = this.parseWord();
			if (target == null) {
				throw new ParseError("Expected target for redirect " + op, this.pos);
			}
			return new Redirect(op, target);
		}
		if (ch == null || !IsRedirectChar(ch)) {
			this.pos = start;
			return null;
		}
		if (
			fd == null &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			this.pos = start;
			return null;
		}
		op = this.advance();
		var strip_tabs = false;
		if (!this.atEnd()) {
			var next_ch = this.peek();
			if (op === ">" && next_ch === ">") {
				this.advance();
				op = ">>";
			} else if (op === "<" && next_ch === "<") {
				this.advance();
				if (!this.atEnd() && this.peek() === "<") {
					this.advance();
					op = "<<<";
				} else if (!this.atEnd() && this.peek() === "-") {
					this.advance();
					op = "<<";
					strip_tabs = true;
				} else {
					op = "<<";
				}
			} else if (op === "<" && next_ch === ">") {
				this.advance();
				op = "<>";
			} else if (op === ">" && next_ch === "|") {
				this.advance();
				op = ">|";
			} else if (fd == null && varfd == null && op === ">" && next_ch === "&") {
				if (
					this.pos + 1 >= this.length ||
					!IsDigitOrDash(this.source[this.pos + 1])
				) {
					this.advance();
					op = ">&";
				}
			} else if (fd == null && varfd == null && op === "<" && next_ch === "&") {
				if (
					this.pos + 1 >= this.length ||
					!IsDigitOrDash(this.source[this.pos + 1])
				) {
					this.advance();
					op = "<&";
				}
			}
		}
		if (op === "<<") {
			return this.ParseHeredoc(fd, strip_tabs);
		}
		if (varfd != null) {
			op = "{" + varfd + "}" + op;
		} else if (fd != null) {
			op = String(fd) + op;
		}
		this.skipWhitespace();
		if (!this.atEnd() && this.peek() === "&") {
			this.advance();
			if (
				!this.atEnd() &&
				(/^[0-9]+$/.test(this.peek()) || this.peek() === "-")
			) {
				fd_chars = [];
				while (!this.atEnd() && /^[0-9]+$/.test(this.peek())) {
					fd_chars.push(this.advance());
				}
				if (fd_chars) {
					var fd_target = fd_chars.join("");
				} else {
					fd_target = "";
				}
				if (!this.atEnd() && this.peek() === "-") {
					fd_target += this.advance();
				}
				target = new Word("&" + fd_target);
			} else {
				var inner_word = this.parseWord();
				if (inner_word != null) {
					target = new Word("&" + inner_word.value);
					target.parts = inner_word.parts;
				} else {
					throw new ParseError("Expected target for redirect " + op, this.pos);
				}
			}
		} else {
			target = this.parseWord();
		}
		if (target == null) {
			throw new ParseError("Expected target for redirect " + op, this.pos);
		}
		return new Redirect(op, target);
	}

	ParseHeredoc(fd, strip_tabs) {
		"Parse a here document <<DELIM ... DELIM.";
		this.skipWhitespace();
		var quoted = false;
		var delimiter_chars = [];
		while (!this.atEnd() && !IsMetachar(this.peek())) {
			var ch = this.peek();
			if (ch === '"') {
				quoted = true;
				this.advance();
				while (!this.atEnd() && this.peek() !== '"') {
					delimiter_chars.push(this.advance());
				}
				if (!this.atEnd()) {
					this.advance();
				}
			} else if (ch === "'") {
				quoted = true;
				this.advance();
				while (!this.atEnd() && this.peek() !== "'") {
					delimiter_chars.push(this.advance());
				}
				if (!this.atEnd()) {
					this.advance();
				}
			} else if (ch === "\\") {
				this.advance();
				if (!this.atEnd()) {
					var next_ch = this.peek();
					if (next_ch === "\n") {
						this.advance();
					} else {
						quoted = true;
						delimiter_chars.push(this.advance());
					}
				}
			} else if (
				ch === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				delimiter_chars.push(this.advance());
				delimiter_chars.push(this.advance());
				var depth = 1;
				while (!this.atEnd() && depth > 0) {
					var c = this.peek();
					if (c === "(") {
						depth += 1;
					} else if (c === ")") {
						depth -= 1;
					}
					delimiter_chars.push(this.advance());
				}
			} else {
				delimiter_chars.push(this.advance());
			}
		}
		var delimiter = delimiter_chars.join("");
		var line_end = this.pos;
		while (line_end < this.length && this.source[line_end] !== "\n") {
			ch = this.source[line_end];
			if (ch === "'") {
				line_end += 1;
				while (line_end < this.length && this.source[line_end] !== "'") {
					line_end += 1;
				}
			} else if (ch === '"') {
				line_end += 1;
				while (line_end < this.length && this.source[line_end] !== '"') {
					if (this.source[line_end] === "\\" && line_end + 1 < this.length) {
						line_end += 2;
					} else {
						line_end += 1;
					}
				}
			} else if (ch === "\\" && line_end + 1 < this.length) {
				line_end += 2;
				continue;
			}
			line_end += 1;
		}
		if (
			this._pending_heredoc_end != null &&
			this._pending_heredoc_end > line_end
		) {
			var content_start = this._pending_heredoc_end;
		} else if (line_end < this.length) {
			content_start = line_end + 1;
		} else {
			content_start = this.length;
		}
		var content_lines = [];
		var scan_pos = content_start;
		while (scan_pos < this.length) {
			var line_start = scan_pos;
			line_end = scan_pos;
			while (line_end < this.length && this.source[line_end] !== "\n") {
				line_end += 1;
			}
			var line = Substring(this.source, line_start, line_end);
			if (!quoted) {
				while (line.endsWith("\\") && line_end < this.length) {
					line = Substring(line, 0, line.length - 1);
					line_end += 1;
					var next_line_start = line_end;
					while (line_end < this.length && this.source[line_end] !== "\n") {
						line_end += 1;
					}
					line = line + Substring(this.source, next_line_start, line_end);
				}
			}
			var check_line = line;
			if (strip_tabs) {
				check_line = line.replace(new RegExp("^[" + "\t" + "]+"), "");
			}
			if (check_line === delimiter) {
				break;
			}
			if (strip_tabs) {
				line = line.replace(new RegExp("^[" + "\t" + "]+"), "");
			}
			content_lines.push(line + "\n");
			if (line_end < this.length) {
				scan_pos = line_end + 1;
			} else {
				scan_pos = this.length;
			}
		}
		var content = content_lines.join("");
		var heredoc_end = line_end;
		if (heredoc_end < this.length) {
			heredoc_end += 1;
		}
		if (this._pending_heredoc_end == null) {
			this._pending_heredoc_end = heredoc_end;
		} else {
			this._pending_heredoc_end = Math.max(
				this._pending_heredoc_end,
				heredoc_end,
			);
		}
		return new HereDoc(delimiter, content, strip_tabs, quoted, fd);
	}

	parseCommand() {
		"Parse a simple command (sequence of words and redirections).";
		var words = [];
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			if (this.atEnd()) {
				break;
			}
			var ch = this.peek();
			if (IsListTerminator(ch)) {
				break;
			}
			if (
				ch === "&" &&
				!(this.pos + 1 < this.length && this.source[this.pos + 1] === ">")
			) {
				break;
			}
			if (this.peek() === "}" && !words) {
				var next_pos = this.pos + 1;
				if (
					next_pos >= this.length ||
					IsWordEndContext(this.source[next_pos])
				) {
					break;
				}
			}
			var redirect = this.parseRedirect();
			if (redirect != null) {
				redirects.push(redirect);
				continue;
			}
			var all_assignments = true;
			for (var w of words) {
				if (!this.IsAssignmentWord(w)) {
					all_assignments = false;
					break;
				}
			}
			var word = this.parseWord(!words || all_assignments);
			if (word == null) {
				break;
			}
			words.push(word);
		}
		if (!words && !redirects) {
			return null;
		}
		return new Command(words, redirects);
	}

	parseSubshell() {
		"Parse a subshell ( list ).";
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== "(") {
			return null;
		}
		this.advance();
		var body = this.parseList();
		if (body == null) {
			throw new ParseError("Expected command in subshell", this.pos);
		}
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== ")") {
			throw new ParseError("Expected ) to close subshell", this.pos);
		}
		this.advance();
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Parse an arithmetic command (( expression )) with parsed internals.\n\n        Returns None if this is not an arithmetic command (e.g., nested subshells\n        like '( ( x ) )' that close with ') )' instead of '))').\n        ";
		this.skipWhitespace();
		if (
			this.atEnd() ||
			this.peek() !== "(" ||
			this.pos + 1 >= this.length ||
			this.source[this.pos + 1] !== "("
		) {
			return null;
		}
		var saved_pos = this.pos;
		this.advance();
		this.advance();
		var content_start = this.pos;
		var depth = 1;
		while (!this.atEnd() && depth > 0) {
			var c = this.peek();
			if (c === "(") {
				depth += 1;
				this.advance();
			} else if (c === ")") {
				if (
					depth === 1 &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === ")"
				) {
					break;
				}
				depth -= 1;
				if (depth === 0) {
					this.pos = saved_pos;
					return null;
				}
				this.advance();
			} else {
				this.advance();
			}
		}
		if (this.atEnd() || depth !== 1) {
			this.pos = saved_pos;
			return null;
		}
		var content = Substring(this.source, content_start, this.pos);
		this.advance();
		this.advance();
		var expr = this.ParseArithExpr(content);
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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

	COND_UNARY_OPS = new Set([
		"-a",
		"-b",
		"-c",
		"-d",
		"-e",
		"-f",
		"-g",
		"-h",
		"-k",
		"-p",
		"-r",
		"-s",
		"-t",
		"-u",
		"-w",
		"-x",
		"-G",
		"-L",
		"-N",
		"-O",
		"-S",
		"-z",
		"-n",
		"-o",
		"-v",
		"-R",
	]);
	COND_BINARY_OPS = new Set([
		"==",
		"!=",
		"=~",
		"=",
		"<",
		">",
		"-eq",
		"-ne",
		"-lt",
		"-le",
		"-gt",
		"-ge",
		"-nt",
		"-ot",
		"-ef",
	]);
	parseConditionalExpr() {
		"Parse a conditional expression [[ expression ]].";
		this.skipWhitespace();
		if (
			this.atEnd() ||
			this.peek() !== "[" ||
			this.pos + 1 >= this.length ||
			this.source[this.pos + 1] !== "["
		) {
			return null;
		}
		this.advance();
		this.advance();
		var body = this.ParseCondOr();
		while (!this.atEnd() && IsWhitespaceNoNewline(this.peek())) {
			this.advance();
		}
		if (
			this.atEnd() ||
			this.peek() !== "]" ||
			this.pos + 1 >= this.length ||
			this.source[this.pos + 1] !== "]"
		) {
			throw new ParseError(
				"Expected ]] to close conditional expression",
				this.pos,
			);
		}
		this.advance();
		this.advance();
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Skip whitespace inside [[ ]], including backslash-newline continuation.";
		while (!this.atEnd()) {
			if (IsWhitespaceNoNewline(this.peek())) {
				this.advance();
			} else if (
				this.peek() === "\\" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "\n"
			) {
				this.advance();
				this.advance();
			} else if (this.peek() === "\n") {
				this.advance();
			} else {
				break;
			}
		}
	}

	CondAtEnd() {
		"Check if we're at ]] (end of conditional).";
		return (
			this.atEnd() ||
			(this.peek() === "]" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "]")
		);
	}

	ParseCondOr() {
		"Parse: or_expr = and_expr (|| or_expr)?  (right-associative)";
		this.CondSkipWhitespace();
		var left = this.ParseCondAnd();
		this.CondSkipWhitespace();
		if (
			!this.CondAtEnd() &&
			this.peek() === "|" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "|"
		) {
			this.advance();
			this.advance();
			var right = this.ParseCondOr();
			return new CondOr(left, right);
		}
		return left;
	}

	ParseCondAnd() {
		"Parse: and_expr = term (&& and_expr)?  (right-associative)";
		this.CondSkipWhitespace();
		var left = this.ParseCondTerm();
		this.CondSkipWhitespace();
		if (
			!this.CondAtEnd() &&
			this.peek() === "&" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "&"
		) {
			this.advance();
			this.advance();
			var right = this.ParseCondAnd();
			return new CondAnd(left, right);
		}
		return left;
	}

	ParseCondTerm() {
		"Parse: term = '!' term | '(' or_expr ')' | unary_test | binary_test | bare_word";
		this.CondSkipWhitespace();
		if (this.CondAtEnd()) {
			throw new ParseError(
				"Unexpected end of conditional expression",
				this.pos,
			);
		}
		if (this.peek() === "!") {
			if (
				this.pos + 1 < this.length &&
				!IsWhitespaceNoNewline(this.source[this.pos + 1])
			) {
			} else {
				this.advance();
				var operand = this.ParseCondTerm();
				return new CondNot(operand);
			}
		}
		if (this.peek() === "(") {
			this.advance();
			var inner = this.ParseCondOr();
			this.CondSkipWhitespace();
			if (this.atEnd() || this.peek() !== ")") {
				throw new ParseError("Expected ) in conditional expression", this.pos);
			}
			this.advance();
			return new CondParen(inner);
		}
		var word1 = this.ParseCondWord();
		if (word1 == null) {
			throw new ParseError("Expected word in conditional expression", this.pos);
		}
		this.CondSkipWhitespace();
		if (IsCondUnaryOp(word1.value)) {
			operand = this.ParseCondWord();
			if (operand == null) {
				throw new ParseError("Expected operand after " + word1.value, this.pos);
			}
			return new UnaryTest(word1.value, operand);
		}
		if (
			!this.CondAtEnd() &&
			this.peek() !== "&" &&
			this.peek() !== "|" &&
			this.peek() !== ")"
		) {
			if (
				IsRedirectChar(this.peek()) &&
				!(this.pos + 1 < this.length && this.source[this.pos + 1] === "(")
			) {
				var op = this.advance();
				this.CondSkipWhitespace();
				var word2 = this.ParseCondWord();
				if (word2 == null) {
					throw new ParseError("Expected operand after " + op, this.pos);
				}
				return new BinaryTest(op, word1, word2);
			}
			var saved_pos = this.pos;
			var op_word = this.ParseCondWord();
			if (op_word && IsCondBinaryOp(op_word.value)) {
				this.CondSkipWhitespace();
				if (op_word.value === "=~") {
					word2 = this.ParseCondRegexWord();
				} else {
					word2 = this.ParseCondWord();
				}
				if (word2 == null) {
					throw new ParseError(
						"Expected operand after " + op_word.value,
						this.pos,
					);
				}
				return new BinaryTest(op_word.value, word1, word2);
			} else {
				this.pos = saved_pos;
			}
		}
		return new UnaryTest("-n", word1);
	}

	ParseCondWord() {
		"Parse a word inside [[ ]], handling expansions but stopping at conditional operators.";
		this.CondSkipWhitespace();
		if (this.CondAtEnd()) {
			return null;
		}
		var c = this.peek();
		if (IsParen(c)) {
			return null;
		}
		if (
			c === "&" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "&"
		) {
			return null;
		}
		if (
			c === "|" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "|"
		) {
			return null;
		}
		var start = this.pos;
		var chars = [];
		var parts = [];
		while (!this.atEnd()) {
			var ch = this.peek();
			if (
				ch === "]" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "]"
			) {
				break;
			}
			if (IsWhitespaceNoNewline(ch)) {
				break;
			}
			if (
				IsRedirectChar(ch) &&
				!(this.pos + 1 < this.length && this.source[this.pos + 1] === "(")
			) {
				break;
			}
			if (ch === "(") {
				if (chars.length > 0 && IsExtglobPrefix(chars[chars.length - 1])) {
					chars.push(this.advance());
					var depth = 1;
					while (!this.atEnd() && depth > 0) {
						c = this.peek();
						if (c === "(") {
							depth += 1;
						} else if (c === ")") {
							depth -= 1;
						}
						chars.push(this.advance());
					}
					continue;
				} else {
					break;
				}
			}
			if (ch === ")") {
				break;
			}
			if (
				ch === "&" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "&"
			) {
				break;
			}
			if (
				ch === "|" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "|"
			) {
				break;
			}
			if (ch === "'") {
				this.advance();
				chars.push("'");
				while (!this.atEnd() && this.peek() !== "'") {
					chars.push(this.advance());
				}
				if (this.atEnd()) {
					throw new ParseError("Unterminated single quote", start);
				}
				chars.push(this.advance());
			} else if (ch === '"') {
				this.advance();
				chars.push('"');
				while (!this.atEnd() && this.peek() !== '"') {
					c = this.peek();
					if (c === "\\" && this.pos + 1 < this.length) {
						var next_c = this.source[this.pos + 1];
						if (next_c === "\n") {
							this.advance();
							this.advance();
						} else {
							chars.push(this.advance());
							chars.push(this.advance());
						}
					} else if (c === "$") {
						if (
							this.pos + 2 < this.length &&
							this.source[this.pos + 1] === "(" &&
							this.source[this.pos + 2] === "("
						) {
							var arith_result = this.ParseArithmeticExpansion();
							var arith_node = arith_result[0];
							var arith_text = arith_result[1];
							if (arith_node) {
								parts.push(arith_node);
								chars.push(arith_text);
							} else {
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
						} else if (
							this.pos + 1 < this.length &&
							this.source[this.pos + 1] === "("
						) {
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
			} else if (ch === "\\" && this.pos + 1 < this.length) {
				chars.push(this.advance());
				chars.push(this.advance());
			} else if (
				ch === "$" &&
				this.pos + 2 < this.length &&
				this.source[this.pos + 1] === "(" &&
				this.source[this.pos + 2] === "("
			) {
				arith_result = this.ParseArithmeticExpansion();
				arith_node = arith_result[0];
				arith_text = arith_result[1];
				if (arith_node) {
					parts.push(arith_node);
					chars.push(arith_text);
				} else {
					chars.push(this.advance());
				}
			} else if (
				ch === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				cmdsub_result = this.ParseCommandSubstitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					parts.push(cmdsub_node);
					chars.push(cmdsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "$") {
				param_result = this.ParseParamExpansion();
				param_node = param_result[0];
				param_text = param_result[1];
				if (param_node) {
					parts.push(param_node);
					chars.push(param_text);
				} else {
					chars.push(this.advance());
				}
			} else if (
				IsRedirectChar(ch) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				var procsub_result = this.ParseProcessSubstitution();
				var procsub_node = procsub_result[0];
				var procsub_text = procsub_result[1];
				if (procsub_node) {
					parts.push(procsub_node);
					chars.push(procsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "`") {
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
		"Parse a regex pattern word in [[ ]], where ( ) are regex grouping, not conditional grouping.";
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
			if (
				ch === "]" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "]"
			) {
				break;
			}
			if (
				ch === "\\" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "\n"
			) {
				this.advance();
				this.advance();
				continue;
			}
			if (ch === "\\" && this.pos + 1 < this.length) {
				chars.push(this.advance());
				chars.push(this.advance());
				continue;
			}
			if (ch === "(") {
				paren_depth += 1;
				chars.push(this.advance());
				continue;
			}
			if (ch === ")") {
				if (paren_depth > 0) {
					paren_depth -= 1;
					chars.push(this.advance());
					continue;
				}
				break;
			}
			if (ch === "[") {
				chars.push(this.advance());
				if (!this.atEnd() && this.peek() === "^") {
					chars.push(this.advance());
				}
				if (!this.atEnd() && this.peek() === "]") {
					chars.push(this.advance());
				}
				while (!this.atEnd()) {
					var c = this.peek();
					if (c === "]") {
						chars.push(this.advance());
						break;
					}
					if (
						c === "[" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === ":"
					) {
						chars.push(this.advance());
						chars.push(this.advance());
						while (
							!this.atEnd() &&
							!(
								this.peek() === ":" &&
								this.pos + 1 < this.length &&
								this.source[this.pos + 1] === "]"
							)
						) {
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
			if (IsWhitespace(ch) && paren_depth === 0) {
				break;
			}
			if (IsWhitespace(ch) && paren_depth > 0) {
				chars.push(this.advance());
				continue;
			}
			if (
				ch === "&" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "&"
			) {
				break;
			}
			if (
				ch === "|" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "|"
			) {
				break;
			}
			if (ch === "'") {
				this.advance();
				chars.push("'");
				while (!this.atEnd() && this.peek() !== "'") {
					chars.push(this.advance());
				}
				if (this.atEnd()) {
					throw new ParseError("Unterminated single quote", start);
				}
				chars.push(this.advance());
				continue;
			}
			if (ch === '"') {
				this.advance();
				chars.push('"');
				while (!this.atEnd() && this.peek() !== '"') {
					c = this.peek();
					if (c === "\\" && this.pos + 1 < this.length) {
						chars.push(this.advance());
						chars.push(this.advance());
					} else if (c === "$") {
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
			if (ch === "$") {
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
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
		"Parse a brace group { list }.";
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== "{") {
			return null;
		}
		if (
			this.pos + 1 < this.length &&
			!IsWhitespace(this.source[this.pos + 1])
		) {
			return null;
		}
		this.advance();
		this.skipWhitespaceAndNewlines();
		var body = this.parseList();
		if (body == null) {
			throw new ParseError("Expected command in brace group", this.pos);
		}
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== "}") {
			throw new ParseError("Expected } to close brace group", this.pos);
		}
		this.advance();
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Parse an if statement: if list; then list [elif list; then list]* [else list] fi.";
		this.skipWhitespace();
		if (this.peekWord() !== "if") {
			return null;
		}
		this.consumeWord("if");
		var condition = this.parseListUntil(new Set(["then"]));
		if (condition == null) {
			throw new ParseError("Expected condition after 'if'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("then")) {
			throw new ParseError("Expected 'then' after if condition", this.pos);
		}
		var then_body = this.parseListUntil(new Set(["elif", "else", "fi"]));
		if (then_body == null) {
			throw new ParseError("Expected commands after 'then'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		var next_word = this.peekWord();
		var else_body = null;
		if (next_word === "elif") {
			this.consumeWord("elif");
			var elif_condition = this.parseListUntil(new Set(["then"]));
			if (elif_condition == null) {
				throw new ParseError("Expected condition after 'elif'", this.pos);
			}
			this.skipWhitespaceAndNewlines();
			if (!this.consumeWord("then")) {
				throw new ParseError("Expected 'then' after elif condition", this.pos);
			}
			var elif_then_body = this.parseListUntil(new Set(["elif", "else", "fi"]));
			if (elif_then_body == null) {
				throw new ParseError("Expected commands after 'then'", this.pos);
			}
			this.skipWhitespaceAndNewlines();
			var inner_next = this.peekWord();
			var inner_else = null;
			if (inner_next === "elif") {
				inner_else = this.ParseElifChain();
			} else if (inner_next === "else") {
				this.consumeWord("else");
				inner_else = this.parseListUntil(new Set(["fi"]));
				if (inner_else == null) {
					throw new ParseError("Expected commands after 'else'", this.pos);
				}
			}
			else_body = new If(elif_condition, elif_then_body, inner_else);
		} else if (next_word === "else") {
			this.consumeWord("else");
			else_body = this.parseListUntil(new Set(["fi"]));
			if (else_body == null) {
				throw new ParseError("Expected commands after 'else'", this.pos);
			}
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("fi")) {
			throw new ParseError("Expected 'fi' to close if statement", this.pos);
		}
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Parse elif chain (after seeing 'elif' keyword).";
		this.consumeWord("elif");
		var condition = this.parseListUntil(new Set(["then"]));
		if (condition == null) {
			throw new ParseError("Expected condition after 'elif'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("then")) {
			throw new ParseError("Expected 'then' after elif condition", this.pos);
		}
		var then_body = this.parseListUntil(new Set(["elif", "else", "fi"]));
		if (then_body == null) {
			throw new ParseError("Expected commands after 'then'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		var next_word = this.peekWord();
		var else_body = null;
		if (next_word === "elif") {
			else_body = this.ParseElifChain();
		} else if (next_word === "else") {
			this.consumeWord("else");
			else_body = this.parseListUntil(new Set(["fi"]));
			if (else_body == null) {
				throw new ParseError("Expected commands after 'else'", this.pos);
			}
		}
		return new If(condition, then_body, else_body);
	}

	parseWhile() {
		"Parse a while loop: while list; do list; done.";
		this.skipWhitespace();
		if (this.peekWord() !== "while") {
			return null;
		}
		this.consumeWord("while");
		var condition = this.parseListUntil(new Set(["do"]));
		if (condition == null) {
			throw new ParseError("Expected condition after 'while'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("do")) {
			throw new ParseError("Expected 'do' after while condition", this.pos);
		}
		var body = this.parseListUntil(new Set(["done"]));
		if (body == null) {
			throw new ParseError("Expected commands after 'do'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("done")) {
			throw new ParseError("Expected 'done' to close while loop", this.pos);
		}
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Parse an until loop: until list; do list; done.";
		this.skipWhitespace();
		if (this.peekWord() !== "until") {
			return null;
		}
		this.consumeWord("until");
		var condition = this.parseListUntil(new Set(["do"]));
		if (condition == null) {
			throw new ParseError("Expected condition after 'until'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("do")) {
			throw new ParseError("Expected 'do' after until condition", this.pos);
		}
		var body = this.parseListUntil(new Set(["done"]));
		if (body == null) {
			throw new ParseError("Expected commands after 'do'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("done")) {
			throw new ParseError("Expected 'done' to close until loop", this.pos);
		}
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Parse a for loop: for name [in words]; do list; done or C-style for ((;;)).";
		this.skipWhitespace();
		if (this.peekWord() !== "for") {
			return null;
		}
		this.consumeWord("for");
		this.skipWhitespace();
		if (
			this.peek() === "(" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			return this.ParseForArith();
		}
		var var_name = this.peekWord();
		if (var_name == null) {
			throw new ParseError("Expected variable name after 'for'", this.pos);
		}
		this.consumeWord(var_name);
		this.skipWhitespace();
		if (this.peek() === ";") {
			this.advance();
		}
		this.skipWhitespaceAndNewlines();
		var words = null;
		if (this.peekWord() === "in") {
			this.consumeWord("in");
			this.skipWhitespaceAndNewlines();
			words = [];
			while (true) {
				this.skipWhitespace();
				if (this.atEnd()) {
					break;
				}
				if (IsSemicolonOrNewline(this.peek())) {
					if (this.peek() === ";") {
						this.advance();
					}
					break;
				}
				if (this.peekWord() === "do") {
					break;
				}
				var word = this.parseWord();
				if (word == null) {
					break;
				}
				words.push(word);
			}
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("do")) {
			throw new ParseError("Expected 'do' in for loop", this.pos);
		}
		var body = this.parseListUntil(new Set(["done"]));
		if (body == null) {
			throw new ParseError("Expected commands after 'do'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("done")) {
			throw new ParseError("Expected 'done' to close for loop", this.pos);
		}
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Parse C-style for loop: for ((init; cond; incr)); do list; done.";
		this.advance();
		this.advance();
		var parts = [];
		var current = [];
		var paren_depth = 0;
		while (!this.atEnd()) {
			var ch = this.peek();
			if (ch === "(") {
				paren_depth += 1;
				current.push(this.advance());
			} else if (ch === ")") {
				if (paren_depth > 0) {
					paren_depth -= 1;
					current.push(this.advance());
				} else if (
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === ")"
				) {
					parts.push(current.join("").trimStart());
					this.advance();
					this.advance();
					break;
				} else {
					current.push(this.advance());
				}
			} else if (ch === ";" && paren_depth === 0) {
				parts.push(current.join("").trimStart());
				current = [];
				this.advance();
			} else {
				current.push(this.advance());
			}
		}
		if (parts.length !== 3) {
			throw new ParseError(
				"Expected three expressions in for ((;;))",
				this.pos,
			);
		}
		var init = parts[0];
		var cond = parts[1];
		var incr = parts[2];
		this.skipWhitespace();
		if (!this.atEnd() && this.peek() === ";") {
			this.advance();
		}
		this.skipWhitespaceAndNewlines();
		if (this.peek() === "{") {
			var brace = this.parseBraceGroup();
			if (brace == null) {
				throw new ParseError("Expected brace group body in for loop", this.pos);
			}
			var body = brace.body;
		} else if (this.consumeWord("do")) {
			body = this.parseListUntil(new Set(["done"]));
			if (body == null) {
				throw new ParseError("Expected commands after 'do'", this.pos);
			}
			this.skipWhitespaceAndNewlines();
			if (!this.consumeWord("done")) {
				throw new ParseError("Expected 'done' to close for loop", this.pos);
			}
		} else {
			throw new ParseError("Expected 'do' or '{' in for loop", this.pos);
		}
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Parse a select statement: select name [in words]; do list; done.";
		this.skipWhitespace();
		if (this.peekWord() !== "select") {
			return null;
		}
		this.consumeWord("select");
		this.skipWhitespace();
		var var_name = this.peekWord();
		if (var_name == null) {
			throw new ParseError("Expected variable name after 'select'", this.pos);
		}
		this.consumeWord(var_name);
		this.skipWhitespace();
		if (this.peek() === ";") {
			this.advance();
		}
		this.skipWhitespaceAndNewlines();
		var words = null;
		if (this.peekWord() === "in") {
			this.consumeWord("in");
			this.skipWhitespaceAndNewlines();
			words = [];
			while (true) {
				this.skipWhitespace();
				if (this.atEnd()) {
					break;
				}
				if (IsSemicolonNewlineBrace(this.peek())) {
					if (this.peek() === ";") {
						this.advance();
					}
					break;
				}
				if (this.peekWord() === "do") {
					break;
				}
				var word = this.parseWord();
				if (word == null) {
					break;
				}
				words.push(word);
			}
		}
		this.skipWhitespaceAndNewlines();
		if (this.peek() === "{") {
			var brace = this.parseBraceGroup();
			if (brace == null) {
				throw new ParseError("Expected brace group body in select", this.pos);
			}
			var body = brace.body;
		} else if (this.consumeWord("do")) {
			body = this.parseListUntil(new Set(["done"]));
			if (body == null) {
				throw new ParseError("Expected commands after 'do'", this.pos);
			}
			this.skipWhitespaceAndNewlines();
			if (!this.consumeWord("done")) {
				throw new ParseError("Expected 'done' to close select", this.pos);
			}
		} else {
			throw new ParseError("Expected 'do' or '{' in select", this.pos);
		}
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Check if we're at a case pattern terminator (;;, ;&, or ;;&).";
		if (this.atEnd() || this.peek() !== ";") {
			return false;
		}
		if (this.pos + 1 >= this.length) {
			return false;
		}
		var next_ch = this.source[this.pos + 1];
		return IsSemicolonOrAmp(next_ch);
	}

	ConsumeCaseTerminator() {
		"Consume and return case pattern terminator (;;, ;&, or ;;&).";
		if (this.atEnd() || this.peek() !== ";") {
			return ";;";
		}
		this.advance();
		if (this.atEnd()) {
			return ";;";
		}
		var ch = this.peek();
		if (ch === ";") {
			this.advance();
			if (!this.atEnd() && this.peek() === "&") {
				this.advance();
				return ";;&";
			}
			return ";;";
		} else if (ch === "&") {
			this.advance();
			return ";&";
		}
		return ";;";
	}

	parseCase() {
		"Parse a case statement: case word in pattern) commands;; ... esac.";
		this.skipWhitespace();
		if (this.peekWord() !== "case") {
			return null;
		}
		this.consumeWord("case");
		this.skipWhitespace();
		var word = this.parseWord();
		if (word == null) {
			throw new ParseError("Expected word after 'case'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("in")) {
			throw new ParseError("Expected 'in' after case word", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		var patterns = [];
		while (true) {
			this.skipWhitespaceAndNewlines();
			if (this.peekWord() === "esac") {
				var saved = this.pos;
				this.skipWhitespace();
				while (
					!this.atEnd() &&
					!IsMetachar(this.peek()) &&
					!IsQuote(this.peek())
				) {
					this.advance();
				}
				this.skipWhitespace();
				var is_pattern = false;
				if (!this.atEnd() && this.peek() === ")") {
					this.advance();
					this.skipWhitespace();
					if (!this.atEnd()) {
						var next_ch = this.peek();
						if (next_ch === ";") {
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
			this.skipWhitespaceAndNewlines();
			if (!this.atEnd() && this.peek() === "(") {
				this.advance();
				this.skipWhitespaceAndNewlines();
			}
			var pattern_chars = [];
			var extglob_depth = 0;
			while (!this.atEnd()) {
				var ch = this.peek();
				if (ch === ")") {
					if (extglob_depth > 0) {
						pattern_chars.push(this.advance());
						extglob_depth -= 1;
					} else {
						this.advance();
						break;
					}
				} else if (ch === "\\") {
					if (
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "\n"
					) {
						this.advance();
						this.advance();
					} else {
						pattern_chars.push(this.advance());
						if (!this.atEnd()) {
							pattern_chars.push(this.advance());
						}
					}
				} else if (
					ch === "$" &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === "("
				) {
					pattern_chars.push(this.advance());
					pattern_chars.push(this.advance());
					if (!this.atEnd() && this.peek() === "(") {
						pattern_chars.push(this.advance());
						var paren_depth = 2;
						while (!this.atEnd() && paren_depth > 0) {
							var c = this.peek();
							if (c === "(") {
								paren_depth += 1;
							} else if (c === ")") {
								paren_depth -= 1;
							}
							pattern_chars.push(this.advance());
						}
					} else {
						extglob_depth += 1;
					}
				} else if (ch === "(" && extglob_depth > 0) {
					pattern_chars.push(this.advance());
					extglob_depth += 1;
				} else if (
					IsExtglobPrefix(ch) &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === "("
				) {
					pattern_chars.push(this.advance());
					pattern_chars.push(this.advance());
					extglob_depth += 1;
				} else if (ch === "[") {
					var is_char_class = false;
					var scan_pos = this.pos + 1;
					var scan_depth = 0;
					var has_first_bracket_literal = false;
					if (scan_pos < this.length && IsCaretOrBang(this.source[scan_pos])) {
						scan_pos += 1;
					}
					if (scan_pos < this.length && this.source[scan_pos] === "]") {
						if (this.source.indexOf("]", scan_pos + 1) !== -1) {
							scan_pos += 1;
							has_first_bracket_literal = true;
						}
					}
					while (scan_pos < this.length) {
						var sc = this.source[scan_pos];
						if (sc === "]" && scan_depth === 0) {
							is_char_class = true;
							break;
						} else if (sc === "[") {
							scan_depth += 1;
						} else if (sc === ")" && scan_depth === 0) {
							break;
						} else if (sc === "|" && scan_depth === 0 && extglob_depth > 0) {
							break;
						}
						scan_pos += 1;
					}
					if (is_char_class) {
						pattern_chars.push(this.advance());
						if (!this.atEnd() && IsCaretOrBang(this.peek())) {
							pattern_chars.push(this.advance());
						}
						if (
							has_first_bracket_literal &&
							!this.atEnd() &&
							this.peek() === "]"
						) {
							pattern_chars.push(this.advance());
						}
						while (!this.atEnd() && this.peek() !== "]") {
							pattern_chars.push(this.advance());
						}
						if (!this.atEnd()) {
							pattern_chars.push(this.advance());
						}
					} else {
						pattern_chars.push(this.advance());
					}
				} else if (ch === "'") {
					pattern_chars.push(this.advance());
					while (!this.atEnd() && this.peek() !== "'") {
						pattern_chars.push(this.advance());
					}
					if (!this.atEnd()) {
						pattern_chars.push(this.advance());
					}
				} else if (ch === '"') {
					pattern_chars.push(this.advance());
					while (!this.atEnd() && this.peek() !== '"') {
						if (this.peek() === "\\" && this.pos + 1 < this.length) {
							pattern_chars.push(this.advance());
						}
						pattern_chars.push(this.advance());
					}
					if (!this.atEnd()) {
						pattern_chars.push(this.advance());
					}
				} else if (IsWhitespace(ch)) {
					if (extglob_depth > 0) {
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
			this.skipWhitespace();
			var body = null;
			var is_empty_body = this.IsCaseTerminator();
			if (!is_empty_body) {
				this.skipWhitespaceAndNewlines();
				if (!this.atEnd() && this.peekWord() !== "esac") {
					var is_at_terminator = this.IsCaseTerminator();
					if (!is_at_terminator) {
						body = this.parseListUntil(new Set(["esac"]));
						this.skipWhitespace();
					}
				}
			}
			var terminator = this.ConsumeCaseTerminator();
			this.skipWhitespaceAndNewlines();
			patterns.push(new CasePattern(pattern, body, terminator));
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("esac")) {
			throw new ParseError("Expected 'esac' to close case statement", this.pos);
		}
		var redirects = [];
		while (true) {
			this.skipWhitespace();
			var redirect = this.parseRedirect();
			if (redirect == null) {
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
		"Parse a coproc statement.\n\n        bash-oracle behavior:\n        - For compound commands (brace group, if, while, etc.), extract NAME if present\n        - For simple commands, don't extract NAME (treat everything as the command)\n        ";
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		if (this.peekWord() !== "coproc") {
			return null;
		}
		this.consumeWord("coproc");
		this.skipWhitespace();
		var name = null;
		var ch = null;
		if (!this.atEnd()) {
			ch = this.peek();
		}
		if (ch === "{") {
			var body = this.parseBraceGroup();
			if (body != null) {
				return new Coproc(body, name);
			}
		}
		if (ch === "(") {
			if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
				body = this.parseArithmeticCommand();
				if (body != null) {
					return new Coproc(body, name);
				}
			}
			body = this.parseSubshell();
			if (body != null) {
				return new Coproc(body, name);
			}
		}
		var next_word = this.peekWord();
		if (IsCompoundKeyword(next_word)) {
			body = this.parseCompoundCommand();
			if (body != null) {
				return new Coproc(body, name);
			}
		}
		var word_start = this.pos;
		var potential_name = this.peekWord();
		if (potential_name) {
			while (
				!this.atEnd() &&
				!IsMetachar(this.peek()) &&
				!IsQuote(this.peek())
			) {
				this.advance();
			}
			this.skipWhitespace();
			ch = null;
			if (!this.atEnd()) {
				ch = this.peek();
			}
			next_word = this.peekWord();
			if (ch === "{") {
				name = potential_name;
				body = this.parseBraceGroup();
				if (body != null) {
					return new Coproc(body, name);
				}
			} else if (ch === "(") {
				name = potential_name;
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
					body = this.parseArithmeticCommand();
				} else {
					body = this.parseSubshell();
				}
				if (body != null) {
					return new Coproc(body, name);
				}
			} else if (IsCompoundKeyword(next_word)) {
				name = potential_name;
				body = this.parseCompoundCommand();
				if (body != null) {
					return new Coproc(body, name);
				}
			}
			this.pos = word_start;
		}
		body = this.parseCommand();
		if (body != null) {
			return new Coproc(body, name);
		}
		throw new ParseError("Expected command after coproc", this.pos);
	}

	parseFunction() {
		"Parse a function definition.\n\n        Forms:\n            name() compound_command           # POSIX form\n            function name compound_command    # bash form without parens\n            function name() compound_command  # bash form with parens\n        ";
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		var saved_pos = this.pos;
		if (this.peekWord() === "function") {
			this.consumeWord("function");
			this.skipWhitespace();
			var name = this.peekWord();
			if (name == null) {
				this.pos = saved_pos;
				return null;
			}
			this.consumeWord(name);
			this.skipWhitespace();
			if (!this.atEnd() && this.peek() === "(") {
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === ")") {
					this.advance();
					this.advance();
				}
			}
			this.skipWhitespaceAndNewlines();
			var body = this.ParseCompoundCommand();
			if (body == null) {
				throw new ParseError("Expected function body", this.pos);
			}
			return new Function(name, body);
		}
		name = this.peekWord();
		if (name == null || IsReservedWord(name)) {
			return null;
		}
		if (StrContains(name, "=")) {
			return null;
		}
		this.skipWhitespace();
		var name_start = this.pos;
		while (
			!this.atEnd() &&
			!IsMetachar(this.peek()) &&
			!IsQuote(this.peek()) &&
			!IsParen(this.peek())
		) {
			this.advance();
		}
		name = Substring(this.source, name_start, this.pos);
		if (!name) {
			this.pos = saved_pos;
			return null;
		}
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== "(") {
			this.pos = saved_pos;
			return null;
		}
		this.advance();
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== ")") {
			this.pos = saved_pos;
			return null;
		}
		this.advance();
		this.skipWhitespaceAndNewlines();
		body = this.ParseCompoundCommand();
		if (body == null) {
			throw new ParseError("Expected function body", this.pos);
		}
		return new Function(name, body);
	}

	ParseCompoundCommand() {
		"Parse any compound command (for function bodies, etc.).";
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
		"Parse a list that stops before certain reserved words.";
		this.skipWhitespaceAndNewlines();
		if (stop_words.has(this.peekWord())) {
			return null;
		}
		var pipeline = this.parsePipeline();
		if (pipeline == null) {
			return null;
		}
		var parts = [pipeline];
		while (true) {
			this.skipWhitespace();
			var has_newline = false;
			while (!this.atEnd() && this.peek() === "\n") {
				has_newline = true;
				this.advance();
				if (
					this._pending_heredoc_end != null &&
					this._pending_heredoc_end > this.pos
				) {
					this.pos = this._pending_heredoc_end;
					this._pending_heredoc_end = null;
				}
				this.skipWhitespace();
			}
			var op = this.parseListOperator();
			if (op == null && has_newline) {
				if (
					!this.atEnd() &&
					!stop_words.has(this.peekWord()) &&
					!IsRightBracket(this.peek())
				) {
					op = "\n";
				}
			}
			if (op == null) {
				break;
			}
			if (op === "&") {
				parts.push(new Operator(op));
				this.skipWhitespaceAndNewlines();
				if (
					this.atEnd() ||
					stop_words.has(this.peekWord()) ||
					IsNewlineOrRightBracket(this.peek())
				) {
					break;
				}
			}
			if (op === ";") {
				this.skipWhitespaceAndNewlines();
				var at_case_terminator =
					this.peek() === ";" &&
					this.pos + 1 < this.length &&
					IsSemicolonOrAmp(this.source[this.pos + 1]);
				if (
					this.atEnd() ||
					stop_words.has(this.peekWord()) ||
					IsNewlineOrRightBracket(this.peek()) ||
					at_case_terminator
				) {
					break;
				}
				parts.push(new Operator(op));
			} else if (op !== "&") {
				parts.push(new Operator(op));
			}
			this.skipWhitespaceAndNewlines();
			if (stop_words.has(this.peekWord())) {
				break;
			}
			if (
				this.peek() === ";" &&
				this.pos + 1 < this.length &&
				IsSemicolonOrAmp(this.source[this.pos + 1])
			) {
				break;
			}
			pipeline = this.parsePipeline();
			if (pipeline == null) {
				throw new ParseError("Expected command after " + op, this.pos);
			}
			parts.push(pipeline);
		}
		if (parts.length === 1) {
			return parts[0];
		}
		return new List(parts);
	}

	parseCompoundCommand() {
		"Parse a compound command (subshell, brace group, if, loops, or simple command).";
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		var ch = this.peek();
		if (
			ch === "(" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			var result = this.parseArithmeticCommand();
			if (result != null) {
				return result;
			}
		}
		if (ch === "(") {
			return this.parseSubshell();
		}
		if (ch === "{") {
			result = this.parseBraceGroup();
			if (result != null) {
				return result;
			}
		}
		if (
			ch === "[" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "["
		) {
			return this.parseConditionalExpr();
		}
		var word = this.peekWord();
		if (word === "if") {
			return this.parseIf();
		}
		if (word === "while") {
			return this.parseWhile();
		}
		if (word === "until") {
			return this.parseUntil();
		}
		if (word === "for") {
			return this.parseFor();
		}
		if (word === "select") {
			return this.parseSelect();
		}
		if (word === "case") {
			return this.parseCase();
		}
		if (word === "function") {
			return this.parseFunction();
		}
		if (word === "coproc") {
			return this.parseCoproc();
		}
		var func = this.parseFunction();
		if (func != null) {
			return func;
		}
		return this.parseCommand();
	}

	parsePipeline() {
		"Parse a pipeline (commands separated by |), with optional time/negation prefix.";
		this.skipWhitespace();
		var prefix_order = null;
		var time_posix = false;
		if (this.peekWord() === "time") {
			this.consumeWord("time");
			prefix_order = "time";
			this.skipWhitespace();
			if (!this.atEnd() && this.peek() === "-") {
				var saved = this.pos;
				this.advance();
				if (!this.atEnd() && this.peek() === "p") {
					this.advance();
					if (this.atEnd() || IsWhitespace(this.peek())) {
						time_posix = true;
					} else {
						this.pos = saved;
					}
				} else {
					this.pos = saved;
				}
			}
			this.skipWhitespace();
			if (!this.atEnd() && StartsWithAt(this.source, this.pos, "--")) {
				if (
					this.pos + 2 >= this.length ||
					IsWhitespace(this.source[this.pos + 2])
				) {
					this.advance();
					this.advance();
					time_posix = true;
					this.skipWhitespace();
				}
			}
			while (this.peekWord() === "time") {
				this.consumeWord("time");
				this.skipWhitespace();
				if (!this.atEnd() && this.peek() === "-") {
					saved = this.pos;
					this.advance();
					if (!this.atEnd() && this.peek() === "p") {
						this.advance();
						if (this.atEnd() || IsWhitespace(this.peek())) {
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
			if (!this.atEnd() && this.peek() === "!") {
				if (
					this.pos + 1 >= this.length ||
					IsWhitespace(this.source[this.pos + 1])
				) {
					this.advance();
					prefix_order = "time_negation";
					this.skipWhitespace();
				}
			}
		} else if (!this.atEnd() && this.peek() === "!") {
			if (
				this.pos + 1 >= this.length ||
				IsWhitespace(this.source[this.pos + 1])
			) {
				this.advance();
				this.skipWhitespace();
				var inner = this.parsePipeline();
				if (inner != null && inner.kind === "negation") {
					if (inner.pipeline != null) {
						return inner.pipeline;
					} else {
						return new Command([]);
					}
				}
				return new Negation(inner);
			}
		}
		var result = this.ParseSimplePipeline();
		if (prefix_order === "time") {
			result = new Time(result, time_posix);
		} else if (prefix_order === "negation") {
			result = new Negation(result);
		} else if (prefix_order === "time_negation") {
			result = new Time(result, time_posix);
			result = new Negation(result);
		} else if (prefix_order === "negation_time") {
			result = new Time(result, time_posix);
			result = new Negation(result);
		} else if (result == null) {
			return null;
		}
		return result;
	}

	ParseSimplePipeline() {
		"Parse a simple pipeline (commands separated by | or |&) without time/negation.";
		var cmd = this.parseCompoundCommand();
		if (cmd == null) {
			return null;
		}
		var commands = [cmd];
		while (true) {
			this.skipWhitespace();
			if (this.atEnd() || this.peek() !== "|") {
				break;
			}
			if (this.pos + 1 < this.length && this.source[this.pos + 1] === "|") {
				break;
			}
			this.advance();
			var is_pipe_both = false;
			if (!this.atEnd() && this.peek() === "&") {
				this.advance();
				is_pipe_both = true;
			}
			this.skipWhitespaceAndNewlines();
			if (is_pipe_both) {
				commands.push(new PipeBoth());
			}
			cmd = this.parseCompoundCommand();
			if (cmd == null) {
				throw new ParseError("Expected command after |", this.pos);
			}
			commands.push(cmd);
		}
		if (commands.length === 1) {
			return commands[0];
		}
		return new Pipeline(commands);
	}

	parseListOperator() {
		"Parse a list operator (&&, ||, ;, &).";
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		var ch = this.peek();
		if (ch === "&") {
			if (this.pos + 1 < this.length && this.source[this.pos + 1] === ">") {
				return null;
			}
			this.advance();
			if (!this.atEnd() && this.peek() === "&") {
				this.advance();
				return "&&";
			}
			return "&";
		}
		if (ch === "|") {
			if (this.pos + 1 < this.length && this.source[this.pos + 1] === "|") {
				this.advance();
				this.advance();
				return "||";
			}
			return null;
		}
		if (ch === ";") {
			if (
				this.pos + 1 < this.length &&
				IsSemicolonOrAmp(this.source[this.pos + 1])
			) {
				return null;
			}
			this.advance();
			return ";";
		}
		return null;
	}

	parseList(newline_as_separator) {
		if (newline_as_separator == null) {
			newline_as_separator = true;
		}
		("Parse a command list (pipelines separated by &&, ||, ;, &).\n\n        Args:\n            newline_as_separator: If True, treat newlines as implicit semicolons.\n                If False, stop at newlines (for top-level parsing).\n        ");
		if (newline_as_separator) {
			this.skipWhitespaceAndNewlines();
		} else {
			this.skipWhitespace();
		}
		var pipeline = this.parsePipeline();
		if (pipeline == null) {
			return null;
		}
		var parts = [pipeline];
		while (true) {
			this.skipWhitespace();
			var has_newline = false;
			while (!this.atEnd() && this.peek() === "\n") {
				has_newline = true;
				if (!newline_as_separator) {
					break;
				}
				this.advance();
				if (
					this._pending_heredoc_end != null &&
					this._pending_heredoc_end > this.pos
				) {
					this.pos = this._pending_heredoc_end;
					this._pending_heredoc_end = null;
				}
				this.skipWhitespace();
			}
			if (has_newline && !newline_as_separator) {
				break;
			}
			var op = this.parseListOperator();
			if (op == null && has_newline) {
				if (!this.atEnd() && !IsRightBracket(this.peek())) {
					op = "\n";
				}
			}
			if (op == null) {
				break;
			}
			if (
				!(
					op === ";" &&
					parts &&
					parts[parts.length - 1].kind === "operator" &&
					parts[parts.length - 1].op === ";"
				)
			) {
				parts.push(new Operator(op));
			}
			if (op === "&") {
				this.skipWhitespace();
				if (this.atEnd() || IsRightBracket(this.peek())) {
					break;
				}
				if (this.peek() === "\n") {
					if (newline_as_separator) {
						this.skipWhitespaceAndNewlines();
						if (this.atEnd() || IsRightBracket(this.peek())) {
							break;
						}
					} else {
						break;
					}
				}
			}
			if (op === ";") {
				this.skipWhitespace();
				if (this.atEnd() || IsRightBracket(this.peek())) {
					break;
				}
				if (this.peek() === "\n") {
					continue;
				}
			}
			if (op === "&&" || op === "||") {
				this.skipWhitespaceAndNewlines();
			}
			pipeline = this.parsePipeline();
			if (pipeline == null) {
				throw new ParseError("Expected command after " + op, this.pos);
			}
			parts.push(pipeline);
		}
		if (parts.length === 1) {
			return parts[0];
		}
		return new List(parts);
	}

	parseComment() {
		"Parse a comment (# to end of line).";
		if (this.atEnd() || this.peek() !== "#") {
			return null;
		}
		var start = this.pos;
		while (!this.atEnd() && this.peek() !== "\n") {
			this.advance();
		}
		var text = Substring(this.source, start, this.pos);
		return new Comment(text);
	}

	parse() {
		"Parse the entire input.";
		var source = this.source.trim();
		if (!source) {
			return [new Empty()];
		}
		var results = [];
		while (true) {
			this.skipWhitespace();
			while (!this.atEnd() && this.peek() === "\n") {
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
		while (!this.atEnd()) {
			var result = this.parseList(false);
			if (result != null) {
				results.push(result);
			}
			this.skipWhitespace();
			var found_newline = false;
			while (!this.atEnd() && this.peek() === "\n") {
				found_newline = true;
				this.advance();
				if (
					this._pending_heredoc_end != null &&
					this._pending_heredoc_end > this.pos
				) {
					this.pos = this._pending_heredoc_end;
					this._pending_heredoc_end = null;
				}
				this.skipWhitespace();
			}
			if (!found_newline && !this.atEnd()) {
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
	"\n    Parse bash source code and return a list of AST nodes.\n\n    Args:\n        source: The bash source code to parse.\n\n    Returns:\n        A list of AST nodes representing the parsed code.\n\n    Raises:\n        ParseError: If the source code cannot be parsed.\n    ";
	var parser = new Parser(source);
	return parser.parse();
}

module.exports = { parse, ParseError };
