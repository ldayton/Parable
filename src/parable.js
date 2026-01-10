"Parable - A recursive descent bash parser in pure Python.";
class ParseError extends Error {
	"Raised when parsing fails.";
	constructor(message, pos, line) {
		super(this._format_message());
		this.message = message;
		this.pos = pos;
		this.line = line;
	}

	_format_message() {
		if (this.line !== null && this.pos !== null) {
			return (
				"Parse error at line " +
				String(this.line) +
				", position " +
				String(this.pos) +
				": " +
				this.message
			);
		} else if (this.pos !== null) {
			return (
				"Parse error at position " + String(this.pos) + ": " + this.message
			);
		}
		return "Parse error: " + this.message;
	}
}

function _is_hex_digit(c) {
	return (
		(c >= "0" && c <= "9") || (c >= "a" && c <= "f") || (c >= "A" && c <= "F")
	);
}

function _is_octal_digit(c) {
	return c >= "0" && c <= "7";
}

let ANSI_C_ESCAPES = {
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
function _get_ansi_escape(c) {
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

function _is_whitespace(c) {
	return c === " " || c === "\t" || c === "\n";
}

function _is_whitespace_no_newline(c) {
	return c === " " || c === "\t";
}

function _substring(s, start, end) {
	"Extract substring from start to end (exclusive).";
	return s.slice(start, end);
}

function _starts_with_at(s, pos, prefix) {
	"Check if s starts with prefix at position pos.";
	return s.startsWith(prefix, pos);
}

function _sublist(lst, start, end) {
	"Extract sublist from start to end (exclusive).";
	return lst.slice(start, end);
}

function _repeat_str(s, n) {
	"Repeat string s n times.";
	let result = [];
	let i = 0;
	while (i < n) {
		result.push(s);
		i += 1;
	}
	return result.join("");
}

class Node {
	"Base class for all AST nodes.";
	to_sexp() {
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
		if (parts === null) {
			parts = [];
		}
		this.parts = parts;
	}

	to_sexp() {
		let value = this.value;
		value = this._expand_all_ansi_c_quotes(value);
		value = this._strip_locale_string_dollars(value);
		value = this._normalize_array_whitespace(value);
		value = this._format_command_substitutions(value);
		value = this._strip_arith_line_continuations(value);
		value = this._double_ctlesc_smart(value);
		value = value.replace("", "");
		value = value.replace("\\", "\\\\");
		let escaped = value
			.replace('"', '\\"')
			.replace("\n", "\\n")
			.replace("\t", "\\t");
		return '(word "' + escaped + '")';
	}

	_append_with_ctlesc(result, byte_val) {
		"Append byte to result (CTLESC doubling happens later in to_sexp).";
		result.push(byte_val);
	}

	_double_ctlesc_smart(value) {
		"Double CTLESC bytes unless escaped by backslash inside double quotes.";
		let result = [];
		let in_single = false;
		let in_double = false;
		for (const c of value) {
			if (c === "'" && !in_double) {
				in_single = !in_single;
			} else if (c === '"' && !in_single) {
				in_double = !in_double;
			}
			result.push(c);
			if (c === "") {
				if (in_double) {
					let bs_count = 0;
					for (let j = result.length - 2; j > -1; j--) {
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

	_expand_ansi_c_escapes(value) {
		"Expand ANSI-C escape sequences in $'...' strings.\n\n        Uses bytes internally so \\x escapes can form valid UTF-8 sequences.\n        Invalid UTF-8 is replaced with U+FFFD.\n        ";
		if (!(value.startsWith("'") && value.endsWith("'"))) {
			return value;
		}
		let inner = _substring(value, 1, value.length - 1);
		let result = [];
		let i = 0;
		while (i < inner.length) {
			if (inner[i] === "\\" && i + 1 < inner.length) {
				let c = inner[i + 1];
				let simple = _get_ansi_escape(c);
				if (simple >= 0) {
					result.push(simple);
					i += 2;
				} else if (c === "'") {
					result.extend([39, 92, 39, 39]);
					i += 2;
				} else if (c === "x") {
					if (i + 2 < inner.length && inner[i + 2] === "{") {
						let j = i + 3;
						while (j < inner.length && _is_hex_digit(inner[j])) {
							j += 1;
						}
						let hex_str = _substring(inner, i + 3, j);
						if (j < inner.length && inner[j] === "}") {
							j += 1;
						}
						if (!hex_str) {
							return "'" + result.decode("utf-8") + "'";
						}
						let byte_val = parseInt(hex_str, 16, 10) & 255;
						if (byte_val === 0) {
							return "'" + result.decode("utf-8") + "'";
						}
						this._append_with_ctlesc(result, byte_val);
						i = j;
					} else {
						j = i + 2;
						while (j < inner.length && j < i + 4 && _is_hex_digit(inner[j])) {
							j += 1;
						}
						if (j > i + 2) {
							byte_val = parseInt(_substring(inner, i + 2, j), 16, 10);
							if (byte_val === 0) {
								return "'" + result.decode("utf-8") + "'";
							}
							this._append_with_ctlesc(result, byte_val);
							i = j;
						} else {
							result.push(inner[i].charCodeAt(0));
							i += 1;
						}
					}
				} else if (c === "u") {
					j = i + 2;
					while (j < inner.length && j < i + 6 && _is_hex_digit(inner[j])) {
						j += 1;
					}
					if (j > i + 2) {
						let codepoint = parseInt(_substring(inner, i + 2, j), 16, 10);
						if (codepoint === 0) {
							return "'" + result.decode("utf-8") + "'";
						}
						result.extend(String.fromCharCode(codepoint).encode("utf-8"));
						i = j;
					} else {
						result.push(inner[i].charCodeAt(0));
						i += 1;
					}
				} else if (c === "U") {
					j = i + 2;
					while (j < inner.length && j < i + 10 && _is_hex_digit(inner[j])) {
						j += 1;
					}
					if (j > i + 2) {
						codepoint = parseInt(_substring(inner, i + 2, j), 16, 10);
						if (codepoint === 0) {
							return "'" + result.decode("utf-8") + "'";
						}
						result.extend(String.fromCharCode(codepoint).encode("utf-8"));
						i = j;
					} else {
						result.push(inner[i].charCodeAt(0));
						i += 1;
					}
				} else if (c === "c") {
					if (i + 3 <= inner.length) {
						let ctrl_char = inner[i + 2];
						let ctrl_val = ctrl_char.charCodeAt(0) & 31;
						if (ctrl_val === 0) {
							return "'" + result.decode("utf-8") + "'";
						}
						this._append_with_ctlesc(result, ctrl_val);
						i += 3;
					} else {
						result.push(inner[i].charCodeAt(0));
						i += 1;
					}
				} else if (c === "0") {
					j = i + 2;
					while (j < inner.length && j < i + 5 && _is_octal_digit(inner[j])) {
						j += 1;
					}
					if (j > i + 2) {
						byte_val = parseInt(_substring(inner, i + 1, j), 8, 10);
						if (byte_val === 0) {
							return "'" + result.decode("utf-8") + "'";
						}
						this._append_with_ctlesc(result, byte_val);
						i = j;
					} else {
						return "'" + result.decode("utf-8") + "'";
					}
				} else if (c >= "1" && c <= "7") {
					j = i + 1;
					while (j < inner.length && j < i + 4 && _is_octal_digit(inner[j])) {
						j += 1;
					}
					byte_val = parseInt(_substring(inner, i + 1, j), 8, 10);
					if (byte_val === 0) {
						return "'" + result.decode("utf-8") + "'";
					}
					this._append_with_ctlesc(result, byte_val);
					i = j;
				} else {
					result.push(92);
					result.push(c.charCodeAt(0));
					i += 2;
				}
			} else {
				result.extend(inner[i].encode("utf-8"));
				i += 1;
			}
		}
		return "'" + result.decode("utf-8") + "'";
	}

	_expand_all_ansi_c_quotes(value) {
		"Find and expand ALL $'...' ANSI-C quoted strings in value.";
		let result = [];
		let i = 0;
		let in_single_quote = false;
		let in_double_quote = false;
		let brace_depth = 0;
		while (i < value.length) {
			let ch = value[i];
			if (!in_single_quote) {
				if (_starts_with_at(value, i, "${")) {
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
			let effective_in_dquote = in_double_quote && brace_depth === 0;
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
				_starts_with_at(value, i, "$'") &&
				!in_single_quote &&
				!effective_in_dquote
			) {
				let j = i + 2;
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
				let ansi_str = _substring(value, i, j);
				let expanded = this._expand_ansi_c_escapes(
					_substring(ansi_str, 1, ansi_str.length),
				);
				if (
					brace_depth > 0 &&
					expanded.startsWith("'") &&
					expanded.endsWith("'")
				) {
					let inner = _substring(expanded, 1, expanded.length - 1);
					if (inner && inner.find("") === -1) {
						if (result.length >= 2) {
							let prev = _sublist(
								result,
								result.length - 2,
								result.length,
							).join("");
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
							let last = result[result.length - 1];
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

	_strip_locale_string_dollars(value) {
		"Strip $ from locale strings $\"...\" while tracking quote context.";
		let result = [];
		let i = 0;
		let in_single_quote = false;
		let in_double_quote = false;
		while (i < value.length) {
			let ch = value[i];
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
				_starts_with_at(value, i, '$"') &&
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

	_normalize_array_whitespace(value) {
		"Normalize whitespace inside array assignments: arr=(a  b\tc) -> arr=(a b c).";
		if (!value.endsWith(")")) {
			return value;
		}
		let i = 0;
		if (!(i < value.length && (value[i].isalpha() || value[i] === "_"))) {
			return value;
		}
		i += 1;
		while (i < value.length && (value[i].isalnum() || value[i] === "_")) {
			i += 1;
		}
		if (i < value.length && value[i] === "+") {
			i += 1;
		}
		if (!(i + 1 < value.length && value[i] === "=" && value[i + 1] === "(")) {
			return value;
		}
		let prefix = _substring(value, 0, i + 1);
		let inner = _substring(value, prefix.length + 1, value.length - 1);
		let normalized = [];
		i = 0;
		let in_whitespace = true;
		while (i < inner.length) {
			let ch = inner[i];
			if (_is_whitespace(ch)) {
				if (!in_whitespace && normalized) {
					normalized.push(" ");
					in_whitespace = true;
				}
				i += 1;
			} else if (ch === "'") {
				in_whitespace = false;
				let j = i + 1;
				while (j < inner.length && inner[j] !== "'") {
					j += 1;
				}
				normalized.push(_substring(inner, i, j + 1));
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
				normalized.push(_substring(inner, i, j + 1));
				i = j + 1;
			} else if (ch === "\\" && i + 1 < inner.length) {
				in_whitespace = false;
				normalized.push(_substring(inner, i, i + 2));
				i += 2;
			} else {
				in_whitespace = false;
				normalized.push(ch);
				i += 1;
			}
		}
		let result = normalized.join("").rstrip(" ");
		return prefix + "(" + result + ")";
	}

	_strip_arith_line_continuations(value) {
		"Strip backslash-newline (line continuation) from inside $((...)).";
		let result = [];
		let i = 0;
		while (i < value.length) {
			if (_starts_with_at(value, i, "$((")) {
				let start = i;
				i += 3;
				let depth = 1;
				let arith_content = [];
				while (i < value.length && depth > 0) {
					if (_starts_with_at(value, i, "((")) {
						arith_content.push("((");
						depth += 1;
						i += 2;
					} else if (_starts_with_at(value, i, "))")) {
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
					result.push(_substring(value, start, i));
				}
			} else {
				result.push(value[i]);
				i += 1;
			}
		}
		return result.join("");
	}

	_collect_cmdsubs(node) {
		"Recursively collect CommandSubstitution nodes from an AST node.";
		let result = [];
		let node_kind = getattr(node, "kind", null);
		if (node_kind === "cmdsub") {
			result.push(node);
		} else {
			let expr = getattr(node, "expression", null);
			if (expr !== null) {
				result.extend(this._collect_cmdsubs(expr));
			}
		}
		let left = getattr(node, "left", null);
		if (left !== null) {
			result.extend(this._collect_cmdsubs(left));
		}
		let right = getattr(node, "right", null);
		if (right !== null) {
			result.extend(this._collect_cmdsubs(right));
		}
		let operand = getattr(node, "operand", null);
		if (operand !== null) {
			result.extend(this._collect_cmdsubs(operand));
		}
		let condition = getattr(node, "condition", null);
		if (condition !== null) {
			result.extend(this._collect_cmdsubs(condition));
		}
		let true_value = getattr(node, "true_value", null);
		if (true_value !== null) {
			result.extend(this._collect_cmdsubs(true_value));
		}
		let false_value = getattr(node, "false_value", null);
		if (false_value !== null) {
			result.extend(this._collect_cmdsubs(false_value));
		}
		return result;
	}

	_format_command_substitutions(value) {
		"Replace $(...) and >(...) / <(...) with bash-oracle-formatted AST output.";
		let cmdsub_parts = [];
		let procsub_parts = [];
		for (const p of this.parts) {
			if (p.kind === "cmdsub") {
				cmdsub_parts.push(p);
			} else if (p.kind === "procsub") {
				procsub_parts.push(p);
			} else {
				cmdsub_parts.extend(this._collect_cmdsubs(p));
			}
		}
		let has_brace_cmdsub = value.find("${ ") !== -1 || value.find("${|") !== -1;
		if (!cmdsub_parts && !procsub_parts && !has_brace_cmdsub) {
			return value;
		}
		let result = [];
		let i = 0;
		let cmdsub_idx = 0;
		let procsub_idx = 0;
		while (i < value.length) {
			if (
				_starts_with_at(value, i, "$(") &&
				!_starts_with_at(value, i, "$((") &&
				cmdsub_idx < cmdsub_parts.length
			) {
				let j = _find_cmdsub_end(value, i + 2);
				let node = cmdsub_parts[cmdsub_idx];
				let formatted = _format_cmdsub_node(node.command);
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
				result.push(_substring(value, i, j));
				cmdsub_idx += 1;
				i = j;
			} else if (
				(_starts_with_at(value, i, ">(") || _starts_with_at(value, i, "<(")) &&
				procsub_idx < procsub_parts.length
			) {
				let direction = value[i];
				j = _find_cmdsub_end(value, i + 2);
				node = procsub_parts[procsub_idx];
				formatted = _format_cmdsub_node(node.command);
				result.push(direction + "(" + formatted + ")");
				procsub_idx += 1;
				i = j;
			} else if (
				_starts_with_at(value, i, "${ ") ||
				_starts_with_at(value, i, "${|")
			) {
				let prefix = _substring(value, i, i + 3);
				j = i + 3;
				let depth = 1;
				while (j < value.length && depth > 0) {
					if (value[j] === "{") {
						depth += 1;
					} else if (value[j] === "}") {
						depth -= 1;
					}
					j += 1;
				}
				let inner = _substring(value, i + 2, j - 1);
				if (inner.strip() === "") {
					result.push("${ }");
				} else {
					try {
						let parser = Parser(inner.lstrip(" |"));
						let parsed = parser.parse_list();
						if (parsed) {
							formatted = _format_cmdsub_node(parsed);
							result.push(prefix + formatted + "; }");
						} else {
							result.push("${ }");
						}
					} catch (_) {
						result.push(_substring(value, i, j));
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

	get_cond_formatted_value() {
		"Return value with command substitutions formatted for cond-term output.";
		let value = this._expand_all_ansi_c_quotes(this.value);
		value = this._format_command_substitutions(value);
		value = value.replace("", "");
		return value.rstrip("\n");
	}
}

class Command extends Node {
	"A simple command (words + redirections).";
	constructor(words, redirects) {
		super();
		this.kind = "command";
		this.words = words;
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	to_sexp() {
		let parts = [];
		for (const w of this.words) {
			parts.push(w.to_sexp());
		}
		for (const r of this.redirects) {
			parts.push(r.to_sexp());
		}
		let inner = parts.join(" ");
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

	to_sexp() {
		if (this.commands.length === 1) {
			return this.commands[0].to_sexp();
		}
		let cmds = [];
		let i = 0;
		while (i < this.commands.length) {
			let cmd = this.commands[i];
			if (cmd.kind === "pipe-both") {
				i += 1;
				continue;
			}
			let needs_redirect =
				i + 1 < this.commands.length &&
				this.commands[i + 1].kind === "pipe-both";
			cmds.push([cmd, needs_redirect]);
			i += 1;
		}
		if (cmds.length === 1) {
			let pair = cmds[0];
			cmd = pair[0];
			let needs = pair[1];
			return this._cmd_sexp(cmd, needs);
		}
		let last_pair = cmds[cmds.length - 1];
		let last_cmd = last_pair[0];
		let last_needs = last_pair[1];
		let result = this._cmd_sexp(last_cmd, last_needs);
		let j = cmds.length - 2;
		while (j >= 0) {
			pair = cmds[j];
			cmd = pair[0];
			needs = pair[1];
			if (needs && cmd.kind !== "command") {
				result =
					"(pipe " + cmd.to_sexp() + ' (redirect ">&" 1) ' + result + ")";
			} else {
				result = "(pipe " + this._cmd_sexp(cmd, needs) + " " + result + ")";
			}
			j -= 1;
		}
		return result;
	}

	_cmd_sexp(cmd, needs_redirect) {
		"Get s-expression for a command, optionally injecting pipe-both redirect.";
		if (!needs_redirect) {
			return cmd.to_sexp();
		}
		if (cmd.kind === "command") {
			let parts = [];
			for (const w of cmd.words) {
				parts.push(w.to_sexp());
			}
			for (const r of cmd.redirects) {
				parts.push(r.to_sexp());
			}
			parts.push('(redirect ">&" 1)');
			return "(command " + parts.join(" ") + ")";
		}
		return cmd.to_sexp();
	}
}

class List extends Node {
	"A list of pipelines with operators.";
	constructor(parts) {
		super();
		this.kind = "list";
		this.parts = parts;
	}

	to_sexp() {
		let parts = list(this.parts);
		let op_names = {
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
			parts = _sublist(parts, 0, parts.length - 1);
		}
		if (parts.length === 1) {
			return parts[0].to_sexp();
		}
		if (
			parts[parts.length - 1].kind === "operator" &&
			parts[parts.length - 1].op === "&"
		) {
			for (let i = parts.length - 3; i > 0; i--) {
				if (
					parts[i].kind === "operator" &&
					(parts[i].op === ";" || parts[i].op === "\n")
				) {
					let left = _sublist(parts, 0, i);
					let right = _sublist(parts, i + 1, parts.length - 1);
					if (left.length > 1) {
						let left_sexp = List(left).to_sexp();
					} else {
						left_sexp = left[0].to_sexp();
					}
					if (right.length > 1) {
						let right_sexp = List(right).to_sexp();
					} else {
						right_sexp = right[0].to_sexp();
					}
					return "(semi " + left_sexp + " (background " + right_sexp + "))";
				}
			}
			let inner_parts = _sublist(parts, 0, parts.length - 1);
			if (inner_parts.length === 1) {
				return "(background " + inner_parts[0].to_sexp() + ")";
			}
			let inner_list = List(inner_parts);
			return "(background " + inner_list.to_sexp() + ")";
		}
		return this._to_sexp_with_precedence(parts, op_names);
	}

	_to_sexp_with_precedence(parts, op_names) {
		for (let i = parts.length - 2; i > 0; i--) {
			if (
				parts[i].kind === "operator" &&
				(parts[i].op === ";" || parts[i].op === "\n")
			) {
				let left = _sublist(parts, 0, i);
				let right = _sublist(parts, i + 1, parts.length);
				if (left.length > 1) {
					let left_sexp = List(left).to_sexp();
				} else {
					left_sexp = left[0].to_sexp();
				}
				if (right.length > 1) {
					let right_sexp = List(right).to_sexp();
				} else {
					right_sexp = right[0].to_sexp();
				}
				return "(semi " + left_sexp + " " + right_sexp + ")";
			}
		}
		for (let i = parts.length - 2; i > 0; i--) {
			if (parts[i].kind === "operator" && parts[i].op === "&") {
				left = _sublist(parts, 0, i);
				right = _sublist(parts, i + 1, parts.length);
				if (left.length > 1) {
					left_sexp = List(left).to_sexp();
				} else {
					left_sexp = left[0].to_sexp();
				}
				if (right.length > 1) {
					right_sexp = List(right).to_sexp();
				} else {
					right_sexp = right[0].to_sexp();
				}
				return "(background " + left_sexp + " " + right_sexp + ")";
			}
		}
		let result = parts[0].to_sexp();
		for (let i = 1; i < parts.length - 1; i += 2) {
			let op = parts[i];
			let cmd = parts[i + 1];
			let op_name = op_names.get(op.op, op.op);
			result = "(" + op_name + " " + result + " " + cmd.to_sexp() + ")";
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

	to_sexp() {
		let names = {
			"&&": "and",
			"||": "or",
			";": "semi",
			"&": "bg",
			"|": "pipe",
		};
		return "(" + names.get(this.op, this.op) + ")";
	}
}

class PipeBoth extends Node {
	"Marker for |& pipe (stdout + stderr).";
	constructor() {
		super();
		this.kind = "pipe-both";
	}

	to_sexp() {
		return "(pipe-both)";
	}
}

class Empty extends Node {
	"Empty input.";
	constructor() {
		super();
		this.kind = "empty";
	}

	to_sexp() {
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

	to_sexp() {
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

	to_sexp() {
		let op = this.op.lstrip("0123456789");
		if (op.startsWith("{")) {
			let j = 1;
			if (j < op.length && (op[j].isalpha() || op[j] === "_")) {
				j += 1;
				while (j < op.length && (op[j].isalnum() || op[j] === "_")) {
					j += 1;
				}
				if (j < op.length && op[j] === "}") {
					op = _substring(op, j + 1, op.length);
				}
			}
		}
		let target_val = this.target.value;
		target_val = Word(target_val)._expand_all_ansi_c_quotes(target_val);
		target_val = target_val.replace('$"', '"');
		if (target_val.startsWith("&")) {
			if (op === ">") {
				op = ">&";
			} else if (op === "<") {
				op = "<&";
			}
			let fd_target = _substring(target_val, 1, target_val.length).rstrip("-");
			if (fd_target.isdigit()) {
				return '(redirect "' + op + '" ' + fd_target + ")";
			} else if (target_val === "&-") {
				return '(redirect ">&-" 0)';
			} else {
				return '(redirect "' + op + '" "' + fd_target + '")';
			}
		}
		if (op === ">&" || op === "<&") {
			if (target_val.isdigit()) {
				return '(redirect "' + op + '" ' + target_val + ")";
			}
			target_val = target_val.rstrip("-");
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
		this.kind = "heredoc";
		this.delimiter = delimiter;
		this.content = content;
		this.strip_tabs = strip_tabs;
		this.quoted = quoted;
		this.fd = fd;
	}

	to_sexp() {
		if (this.strip_tabs) {
			let op = "<<-";
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

	to_sexp() {
		let base = "(subshell " + this.body.to_sexp() + ")";
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
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

	to_sexp() {
		let base = "(brace-group " + this.body.to_sexp() + ")";
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
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
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	to_sexp() {
		let result =
			"(if " + this.condition.to_sexp() + " " + this.then_body.to_sexp();
		if (this.else_body) {
			result = result + " " + this.else_body.to_sexp();
		}
		result = result + ")";
		for (const r of this.redirects) {
			result = result + " " + r.to_sexp();
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
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	to_sexp() {
		let base =
			"(while " + this.condition.to_sexp() + " " + this.body.to_sexp() + ")";
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
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
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	to_sexp() {
		let base =
			"(until " + this.condition.to_sexp() + " " + this.body.to_sexp() + ")";
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
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
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	to_sexp() {
		let suffix = "";
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
			}
			suffix = " " + redirect_parts.join(" ");
		}
		let var_escaped = this.variable.replace("\\", "\\\\").replace('"', '\\"');
		if (this.words === null) {
			return (
				'(for (word "' +
				var_escaped +
				'") (in (word "\\"$@\\"")) ' +
				this.body.to_sexp() +
				")" +
				suffix
			);
		} else if (this.words.length === 0) {
			return (
				'(for (word "' +
				var_escaped +
				'") (in) ' +
				this.body.to_sexp() +
				")" +
				suffix
			);
		} else {
			let word_parts = [];
			for (const w of this.words) {
				word_parts.push(w.to_sexp());
			}
			let word_strs = word_parts.join(" ");
			return (
				'(for (word "' +
				var_escaped +
				'") (in ' +
				word_strs +
				") " +
				this.body.to_sexp() +
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
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	to_sexp() {
		function format_arith_val(s) {
			let w = Word(s, []);
			let val = w._expand_all_ansi_c_quotes(s);
			val = w._strip_locale_string_dollars(val);
			val = val.replace("\\", "\\\\").replace('"', '\\"');
			return val;
		}

		let suffix = "";
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
			}
			suffix = " " + redirect_parts.join(" ");
		}
		if (this.init) {
			let init_val = this.init;
		} else {
			init_val = "1";
		}
		if (this.cond) {
			let cond_val = _normalize_fd_redirects(this.cond);
		} else {
			cond_val = "1";
		}
		if (this.incr) {
			let incr_val = this.incr;
		} else {
			incr_val = "1";
		}
		return (
			'(arith-for (init (word "' +
			format_arith_val(init_val) +
			'")) ' +
			'(test (word "' +
			format_arith_val(cond_val) +
			'")) ' +
			'(step (word "' +
			format_arith_val(incr_val) +
			'")) ' +
			this.body.to_sexp() +
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
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	to_sexp() {
		let suffix = "";
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
			}
			suffix = " " + redirect_parts.join(" ");
		}
		let var_escaped = this.variable.replace("\\", "\\\\").replace('"', '\\"');
		if (this.words !== null) {
			let word_parts = [];
			for (const w of this.words) {
				word_parts.push(w.to_sexp());
			}
			let word_strs = word_parts.join(" ");
			if (this.words) {
				let in_clause = "(in " + word_strs + ")";
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
			this.body.to_sexp() +
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
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	to_sexp() {
		let parts = [];
		parts.push("(case " + this.word.to_sexp());
		for (const p of this.patterns) {
			parts.push(p.to_sexp());
		}
		let base = parts.join(" ") + ")";
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
			}
			return base + " " + redirect_parts.join(" ");
		}
		return base;
	}
}

function _consume_single_quote(s, start) {
	"Consume '...' from start. Returns (end_index, chars_list).";
	let chars = ["'"];
	let i = start + 1;
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

function _consume_double_quote(s, start) {
	"Consume \"...\" from start, handling escapes. Returns (end_index, chars_list).";
	let chars = ['"'];
	let i = start + 1;
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

function _has_bracket_close(s, start, depth) {
	"Check if there's a ] before | or ) at depth 0.";
	let i = start;
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

function _consume_bracket_class(s, start, depth) {
	"Consume [...] bracket expression. Returns (end_index, chars_list, was_bracket).";
	let scan_pos = start + 1;
	if (scan_pos < s.length && (s[scan_pos] === "!" || s[scan_pos] === "^")) {
		scan_pos += 1;
	}
	if (scan_pos < s.length && s[scan_pos] === "]") {
		if (_has_bracket_close(s, scan_pos + 1, depth)) {
			scan_pos += 1;
		}
	}
	let is_bracket = false;
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
	let chars = ["["];
	let i = start + 1;
	if (i < s.length && (s[i] === "!" || s[i] === "^")) {
		chars.push(s[i]);
		i += 1;
	}
	if (i < s.length && s[i] === "]") {
		if (_has_bracket_close(s, i + 1, depth)) {
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
		this.kind = "pattern";
		this.pattern = pattern;
		this.body = body;
		this.terminator = terminator;
	}

	to_sexp() {
		let alternatives = [];
		let current = [];
		let i = 0;
		let depth = 0;
		while (i < this.pattern.length) {
			let ch = this.pattern[i];
			if (ch === "\\" && i + 1 < this.pattern.length) {
				current.push(_substring(this.pattern, i, i + 2));
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
				let result = _consume_bracket_class(this.pattern, i, depth);
				i = result[0];
				current.extend(result[1]);
			} else if (ch === "'" && depth === 0) {
				result = _consume_single_quote(this.pattern, i);
				i = result[0];
				current.extend(result[1]);
			} else if (ch === '"' && depth === 0) {
				result = _consume_double_quote(this.pattern, i);
				i = result[0];
				current.extend(result[1]);
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
		let word_list = [];
		for (const alt of alternatives) {
			word_list.push(Word(alt).to_sexp());
		}
		let pattern_str = word_list.join(" ");
		let parts = ["(pattern (" + pattern_str + ")"];
		if (this.body) {
			parts.push(" " + this.body.to_sexp());
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

	to_sexp() {
		return '(function "' + this.name + '" ' + this.body.to_sexp() + ")";
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

	to_sexp() {
		let escaped_param = this.param.replace("\\", "\\\\").replace('"', '\\"');
		if (this.op !== null) {
			let escaped_op = this.op.replace("\\", "\\\\").replace('"', '\\"');
			if (this.arg !== null) {
				let arg_val = this.arg;
			} else {
				arg_val = "";
			}
			let escaped_arg = arg_val.replace("\\", "\\\\").replace('"', '\\"');
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

	to_sexp() {
		let escaped = this.param.replace("\\", "\\\\").replace('"', '\\"');
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

	to_sexp() {
		let escaped = this.param.replace("\\", "\\\\").replace('"', '\\"');
		if (this.op !== null) {
			let escaped_op = this.op.replace("\\", "\\\\").replace('"', '\\"');
			if (this.arg !== null) {
				let arg_val = this.arg;
			} else {
				arg_val = "";
			}
			let escaped_arg = arg_val.replace("\\", "\\\\").replace('"', '\\"');
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

	to_sexp() {
		return "(cmdsub " + this.command.to_sexp() + ")";
	}
}

class ArithmeticExpansion extends Node {
	"An arithmetic expansion $((...)) with parsed internals.";
	constructor(expression) {
		super();
		this.kind = "arith";
		this.expression = expression;
	}

	to_sexp() {
		if (this.expression === null) {
			return "(arith)";
		}
		return "(arith " + this.expression.to_sexp() + ")";
	}
}

class ArithmeticCommand extends Node {
	"An arithmetic command ((...)) with parsed internals.";
	constructor(expression, redirects, raw_content) {
		super();
		this.kind = "arith-cmd";
		this.expression = expression;
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
		this.raw_content = raw_content;
	}

	to_sexp() {
		let escaped = this.raw_content
			.replace("\\", "\\\\")
			.replace('"', '\\"')
			.replace("\n", "\\n");
		let result = '(arith (word "' + escaped + '"))';
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
			}
			let redirect_sexps = redirect_parts.join(" ");
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

	to_sexp() {
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

	to_sexp() {
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

	to_sexp() {
		return (
			'(binary-op "' +
			this.op +
			'" ' +
			this.left.to_sexp() +
			" " +
			this.right.to_sexp() +
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

	to_sexp() {
		return '(unary-op "' + this.op + '" ' + this.operand.to_sexp() + ")";
	}
}

class ArithPreIncr extends Node {
	"Pre-increment ++var.";
	constructor(operand) {
		super();
		this.kind = "pre-incr";
		this.operand = operand;
	}

	to_sexp() {
		return "(pre-incr " + this.operand.to_sexp() + ")";
	}
}

class ArithPostIncr extends Node {
	"Post-increment var++.";
	constructor(operand) {
		super();
		this.kind = "post-incr";
		this.operand = operand;
	}

	to_sexp() {
		return "(post-incr " + this.operand.to_sexp() + ")";
	}
}

class ArithPreDecr extends Node {
	"Pre-decrement --var.";
	constructor(operand) {
		super();
		this.kind = "pre-decr";
		this.operand = operand;
	}

	to_sexp() {
		return "(pre-decr " + this.operand.to_sexp() + ")";
	}
}

class ArithPostDecr extends Node {
	"Post-decrement var--.";
	constructor(operand) {
		super();
		this.kind = "post-decr";
		this.operand = operand;
	}

	to_sexp() {
		return "(post-decr " + this.operand.to_sexp() + ")";
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

	to_sexp() {
		return (
			'(assign "' +
			this.op +
			'" ' +
			this.target.to_sexp() +
			" " +
			this.value.to_sexp() +
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

	to_sexp() {
		return (
			"(ternary " +
			this.condition.to_sexp() +
			" " +
			this.if_true.to_sexp() +
			" " +
			this.if_false.to_sexp() +
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

	to_sexp() {
		return "(comma " + this.left.to_sexp() + " " + this.right.to_sexp() + ")";
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

	to_sexp() {
		return '(subscript "' + this.array + '" ' + this.index.to_sexp() + ")";
	}
}

class ArithEscape extends Node {
	"An escaped character in arithmetic expression.";
	constructor(char) {
		super();
		this.kind = "escape";
		this.char = char;
	}

	to_sexp() {
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

	to_sexp() {
		let escaped = this.expression
			.replace("\\", "\\\\")
			.replace('"', '\\"')
			.replace("\n", "\\n");
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

	to_sexp() {
		let escaped = this.content
			.replace("\\", "\\\\")
			.replace('"', '\\"')
			.replace("\n", "\\n");
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

	to_sexp() {
		let escaped = this.content
			.replace("\\", "\\\\")
			.replace('"', '\\"')
			.replace("\n", "\\n");
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

	to_sexp() {
		return '(procsub "' + this.direction + '" ' + this.command.to_sexp() + ")";
	}
}

class Negation extends Node {
	"Pipeline negation with !.";
	constructor(pipeline) {
		super();
		this.kind = "negation";
		this.pipeline = pipeline;
	}

	to_sexp() {
		if (this.pipeline === null) {
			return "(negation (command))";
		}
		return "(negation " + this.pipeline.to_sexp() + ")";
	}
}

class Time extends Node {
	"Time measurement with time keyword.";
	posix = false;
	constructor(pipeline, posix) {
		super();
		this.kind = "time";
		this.pipeline = pipeline;
		this.posix = posix;
	}

	to_sexp() {
		if (this.pipeline === null) {
			if (this.posix) {
				return "(time -p (command))";
			} else {
				return "(time (command))";
			}
		}
		if (this.posix) {
			return "(time -p " + this.pipeline.to_sexp() + ")";
		}
		return "(time " + this.pipeline.to_sexp() + ")";
	}
}

class ConditionalExpr extends Node {
	"A conditional expression [[ expression ]].";
	constructor(body, redirects) {
		super();
		this.kind = "cond-expr";
		this.body = body;
		if (redirects === null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	to_sexp() {
		let body_kind = getattr(this.body, "kind", null);
		if (body_kind === null) {
			let escaped = this.body
				.replace("\\", "\\\\")
				.replace('"', '\\"')
				.replace("\n", "\\n");
			let result = '(cond "' + escaped + '")';
		} else {
			result = "(cond " + this.body.to_sexp() + ")";
		}
		if (this.redirects) {
			let redirect_parts = [];
			for (const r of this.redirects) {
				redirect_parts.push(r.to_sexp());
			}
			let redirect_sexps = redirect_parts.join(" ");
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

	to_sexp() {
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

	to_sexp() {
		let left_val = this.left.get_cond_formatted_value();
		let right_val = this.right.get_cond_formatted_value();
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

	to_sexp() {
		return (
			"(cond-and " + this.left.to_sexp() + " " + this.right.to_sexp() + ")"
		);
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

	to_sexp() {
		return "(cond-or " + this.left.to_sexp() + " " + this.right.to_sexp() + ")";
	}
}

class CondNot extends Node {
	"Logical NOT in [[ ]], e.g., ! expr.";
	constructor(operand) {
		super();
		this.kind = "cond-not";
		this.operand = operand;
	}

	to_sexp() {
		return this.operand.to_sexp();
	}
}

class CondParen extends Node {
	"Parenthesized group in [[ ]], e.g., ( expr ).";
	constructor(inner) {
		super();
		this.kind = "cond-paren";
		this.inner = inner;
	}

	to_sexp() {
		return "(cond-expr " + this.inner.to_sexp() + ")";
	}
}

class Array extends Node {
	"An array literal (word1 word2 ...).";
	constructor(elements) {
		super();
		this.kind = "array";
		this.elements = elements;
	}

	to_sexp() {
		if (!this.elements) {
			return "(array)";
		}
		let parts = [];
		for (const e of this.elements) {
			parts.push(e.to_sexp());
		}
		let inner = parts.join(" ");
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

	to_sexp() {
		if (this.name) {
			let name = this.name;
		} else {
			name = "COPROC";
		}
		return '(coproc "' + name + '" ' + this.command.to_sexp() + ")";
	}
}

function _format_cmdsub_node(node, indent, in_procsub) {
	"Format an AST node for command substitution output (bash-oracle pretty-print format).";
	let sp = _repeat_str(" ", indent);
	let inner_sp = _repeat_str(" ", indent + 4);
	if (node.kind === "empty") {
		return "";
	}
	if (node.kind === "command") {
		let parts = [];
		for (const w of node.words) {
			let val = w._expand_all_ansi_c_quotes(w.value);
			val = w._format_command_substitutions(val);
			parts.push(val);
		}
		for (const r of node.redirects) {
			parts.push(_format_redirect(r));
		}
		return parts.join(" ");
	}
	if (node.kind === "pipeline") {
		let cmd_parts = [];
		for (const cmd of node.commands) {
			cmd_parts.push(_format_cmdsub_node(cmd, indent));
		}
		return cmd_parts.join(" | ");
	}
	if (node.kind === "list") {
		let result = [];
		for (const p of node.parts) {
			if (p.kind === "operator") {
				if (p.op === ";") {
					result.push(";");
				} else if (p.op === "\n") {
					if (result && result[result.length - 1] === ";") {
						continue;
					}
					result.push("\n");
				} else if (p.op === "&") {
					result.push(" &");
				} else {
					result.push(" " + p.op);
				}
			} else {
				if (result && !result[result.length - 1].endsWith([" ", "\n"])) {
					result.push(" ");
				}
				result.push(_format_cmdsub_node(p, indent));
			}
		}
		let s = result.join("");
		while (s.endsWith(";") || s.endsWith("\n")) {
			s = _substring(s, 0, s.length - 1);
		}
		return s;
	}
	if (node.kind === "if") {
		let cond = _format_cmdsub_node(node.condition, indent);
		let then_body = _format_cmdsub_node(node.then_body, indent + 4);
		result = "if " + cond + "; then\n" + inner_sp + then_body + ";";
		if (node.else_body) {
			let else_body = _format_cmdsub_node(node.else_body, indent + 4);
			result = result + "\n" + sp + "else\n" + inner_sp + else_body + ";";
		}
		result = result + "\n" + sp + "fi";
		return result;
	}
	if (node.kind === "while") {
		cond = _format_cmdsub_node(node.condition, indent);
		let body = _format_cmdsub_node(node.body, indent + 4);
		return "while " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done";
	}
	if (node.kind === "until") {
		cond = _format_cmdsub_node(node.condition, indent);
		body = _format_cmdsub_node(node.body, indent + 4);
		return "until " + cond + "; do\n" + inner_sp + body + ";\n" + sp + "done";
	}
	if (node.kind === "for") {
		let variable = node.variable;
		body = _format_cmdsub_node(node.body, indent + 4);
		if (node.words) {
			let word_vals = [];
			for (const w of node.words) {
				word_vals.push(w.value);
			}
			let words = word_vals.join(" ");
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
		let word = node.word.value;
		let patterns = [];
		let i = 0;
		while (i < node.patterns.length) {
			p = node.patterns[i];
			let pat = p.pattern.replace("|", " | ");
			if (p.body) {
				body = _format_cmdsub_node(p.body, indent + 8);
			} else {
				body = "";
			}
			let term = p.terminator;
			let pat_indent = _repeat_str(" ", indent + 8);
			let term_indent = _repeat_str(" ", indent + 4);
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
		let pattern_str = ("\n" + _repeat_str(" ", indent + 4)).join(patterns);
		return "case " + word + " in" + pattern_str + "\n" + sp + "esac";
	}
	if (node.kind === "function") {
		let name = node.name;
		if (node.body.kind === "brace-group") {
			body = _format_cmdsub_node(node.body.body, indent + 4);
		} else {
			body = _format_cmdsub_node(node.body, indent + 4);
		}
		body = body.rstrip(";");
		return "function " + name + " () \n{ \n" + inner_sp + body + "\n}";
	}
	if (node.kind === "subshell") {
		body = _format_cmdsub_node(node.body, indent, in_procsub);
		let redirects = "";
		if (node.redirects) {
			let redirect_parts = [];
			for (const r of node.redirects) {
				redirect_parts.push(_format_redirect(r));
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
		body = _format_cmdsub_node(node.body, indent);
		body = body.rstrip(";");
		return "{ " + body + "; }";
	}
	if (node.kind === "arith-cmd") {
		return "((" + node.raw_content + "))";
	}
	return "";
}

function _format_redirect(r) {
	"Format a redirect for command substitution output.";
	if (r.kind === "heredoc") {
		if (r.strip_tabs) {
			let op = "<<-";
		} else {
			op = "<<";
		}
		if (r.quoted) {
			let delim = "'" + r.delimiter + "'";
		} else {
			delim = r.delimiter;
		}
		return op + delim + "\n" + r.content + r.delimiter + "\n";
	}
	op = r.op;
	let target = r.target.value;
	if (target.startsWith("&")) {
		if (target === "&-" && op.endsWith("<")) {
			op = _substring(op, 0, op.length - 1) + ">";
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

function _normalize_fd_redirects(s) {
	"Normalize fd redirects in a raw string: >&2 -> 1>&2, <&N -> 0<&N.";
	let result = [];
	let i = 0;
	while (i < s.length) {
		if (i + 2 < s.length && s[i + 1] === "&" && s[i + 2].isdigit()) {
			let prev_is_digit = i > 0 && s[i - 1].isdigit();
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

function _find_cmdsub_end(value, start) {
	"Find the end of a $(...) command substitution, handling case statements.\n\n    Starts after the opening $(. Returns position after the closing ).\n    ";
	let depth = 1;
	let i = start;
	let in_single = false;
	let in_double = false;
	let case_depth = 0;
	let in_case_patterns = false;
	while (i < value.length && depth > 0) {
		let c = value[i];
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
			if (
				_starts_with_at(value, i, "$(") &&
				!_starts_with_at(value, i, "$((")
			) {
				let j = _find_cmdsub_end(value, i + 2);
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
		if (_starts_with_at(value, i, "<<")) {
			i = _skip_heredoc(value, i);
			continue;
		}
		if (_starts_with_at(value, i, "case") && _is_word_boundary(value, i, 4)) {
			case_depth += 1;
			in_case_patterns = false;
			i += 4;
			continue;
		}
		if (
			case_depth > 0 &&
			_starts_with_at(value, i, "in") &&
			_is_word_boundary(value, i, 2)
		) {
			in_case_patterns = true;
			i += 2;
			continue;
		}
		if (_starts_with_at(value, i, "esac") && _is_word_boundary(value, i, 4)) {
			if (case_depth > 0) {
				case_depth -= 1;
				in_case_patterns = false;
			}
			i += 4;
			continue;
		}
		if (_starts_with_at(value, i, ";;")) {
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

function _skip_heredoc(value, start) {
	"Skip past a heredoc starting at <<. Returns position after heredoc content.";
	let i = start + 2;
	if (i < value.length && value[i] === "-") {
		i += 1;
	}
	while (i < value.length && _is_whitespace_no_newline(value[i])) {
		i += 1;
	}
	let delim_start = i;
	let quote_char = null;
	if (i < value.length && (value[i] === '"' || value[i] === "'")) {
		quote_char = value[i];
		i += 1;
		delim_start = i;
		while (i < value.length && value[i] !== quote_char) {
			i += 1;
		}
		let delimiter = _substring(value, delim_start, i);
		if (i < value.length) {
			i += 1;
		}
	} else if (i < value.length && value[i] === "\\") {
		i += 1;
		delim_start = i;
		while (i < value.length && !_is_whitespace(value[i])) {
			i += 1;
		}
		delimiter = _substring(value, delim_start, i);
	} else {
		while (i < value.length && !_is_whitespace(value[i])) {
			i += 1;
		}
		delimiter = _substring(value, delim_start, i);
	}
	while (i < value.length && value[i] !== "\n") {
		i += 1;
	}
	if (i < value.length) {
		i += 1;
	}
	while (i < value.length) {
		let line_start = i;
		let line_end = i;
		while (line_end < value.length && value[line_end] !== "\n") {
			line_end += 1;
		}
		let line = _substring(value, line_start, line_end);
		if (start + 2 < value.length && value[start + 2] === "-") {
			let stripped = line.lstrip("\t");
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

function _is_word_boundary(s, pos, word_len) {
	"Check if the word at pos is a standalone word (not part of larger word).";
	if (pos > 0 && s[pos - 1].isalnum()) {
		return false;
	}
	let end = pos + word_len;
	if (end < s.length && s[end].isalnum()) {
		return false;
	}
	return true;
}

let RESERVED_WORDS = new Set([
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
let METACHAR = new Set(" \t\n|&;()<>");
let COND_UNARY_OPS = new Set([
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
let COND_BINARY_OPS = new Set([
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
let COMPOUND_KEYWORDS = new Set([
	"while",
	"until",
	"for",
	"if",
	"case",
	"select",
]);
function _is_quote(c) {
	return c === "'" || c === '"';
}

function _is_metachar(c) {
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

function _is_extglob_prefix(c) {
	return c === "@" || c === "?" || c === "*" || c === "+" || c === "!";
}

function _is_redirect_char(c) {
	return c === "<" || c === ">";
}

function _is_special_param(c) {
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

function _is_digit(c) {
	return c >= "0" && c <= "9";
}

function _is_semicolon_or_newline(c) {
	return c === ";" || c === "\n";
}

function _is_right_bracket(c) {
	return c === ")" || c === "}";
}

function _is_word_start_context(c) {
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

function _is_word_end_context(c) {
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

function _is_special_param_or_digit(c) {
	return _is_special_param(c) || _is_digit(c);
}

function _is_param_expansion_op(c) {
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

function _is_simple_param_op(c) {
	return c === "-" || c === "=" || c === "?" || c === "+";
}

function _is_escape_char_in_dquote(c) {
	return c === "$" || c === "`" || c === "\\";
}

function _is_list_terminator(c) {
	return c === "\n" || c === "|" || c === ";" || c === "(" || c === ")";
}

function _is_semicolon_or_amp(c) {
	return c === ";" || c === "&";
}

function _is_paren(c) {
	return c === "(" || c === ")";
}

function _is_caret_or_bang(c) {
	return c === "!" || c === "^";
}

function _is_at_or_star(c) {
	return c === "@" || c === "*";
}

function _is_digit_or_dash(c) {
	return _is_digit(c) || c === "-";
}

function _is_newline_or_right_paren(c) {
	return c === "\n" || c === ")";
}

function _is_newline_or_right_bracket(c) {
	return c === "\n" || c === ")" || c === "}";
}

function _is_semicolon_newline_brace(c) {
	return c === ";" || c === "\n" || c === "{";
}

function _is_reserved_word(word) {
	return RESERVED_WORDS.has(word);
}

function _is_compound_keyword(word) {
	return COMPOUND_KEYWORDS.has(word);
}

function _is_cond_unary_op(op) {
	return COND_UNARY_OPS.has(op);
}

function _is_cond_binary_op(op) {
	return COND_BINARY_OPS.has(op);
}

function _str_contains(haystack, needle) {
	"Check if haystack contains needle substring.";
	return haystack.find(needle) !== -1;
}

class Parser {
	"Recursive descent parser for bash.";
	constructor(source) {
		this.source = source;
		this.pos = 0;
		this.length = source.length;
		this._pending_heredoc_end = null;
	}

	at_end() {
		"Check if we've reached the end of input.";
		return this.pos >= this.length;
	}

	peek() {
		"Return current character without consuming.";
		if (this.at_end()) {
			return null;
		}
		return this.source[this.pos];
	}

	advance() {
		"Consume and return current character.";
		if (this.at_end()) {
			return null;
		}
		let ch = this.source[this.pos];
		this.pos += 1;
		return ch;
	}

	skip_whitespace() {
		"Skip spaces, tabs, comments, and backslash-newline continuations.";
		while (!this.at_end()) {
			let ch = this.peek();
			if (_is_whitespace_no_newline(ch)) {
				this.advance();
			} else if (ch === "#") {
				while (!this.at_end() && this.peek() !== "\n") {
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

	skip_whitespace_and_newlines() {
		"Skip spaces, tabs, newlines, comments, and backslash-newline continuations.";
		while (!this.at_end()) {
			let ch = this.peek();
			if (_is_whitespace(ch)) {
				this.advance();
				if (ch === "\n") {
					if (
						this._pending_heredoc_end !== null &&
						this._pending_heredoc_end > this.pos
					) {
						this.pos = this._pending_heredoc_end;
						this._pending_heredoc_end = null;
					}
				}
			} else if (ch === "#") {
				while (!this.at_end() && this.peek() !== "\n") {
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

	peek_word() {
		"Peek at the next word without consuming it.";
		let saved_pos = this.pos;
		this.skip_whitespace();
		if (this.at_end() || _is_metachar(this.peek())) {
			this.pos = saved_pos;
			return null;
		}
		let chars = [];
		while (!this.at_end() && !_is_metachar(this.peek())) {
			let ch = this.peek();
			if (_is_quote(ch)) {
				break;
			}
			chars.push(this.advance());
		}
		if (chars) {
			let word = chars.join("");
		} else {
			word = null;
		}
		this.pos = saved_pos;
		return word;
	}

	consume_word(expected) {
		"Try to consume a specific reserved word. Returns True if successful.";
		let saved_pos = this.pos;
		this.skip_whitespace();
		let word = this.peek_word();
		if (word !== expected) {
			this.pos = saved_pos;
			return false;
		}
		this.skip_whitespace();
		for (const _ of expected) {
			this.advance();
		}
		return true;
	}

	parse_word(at_command_start) {
		"Parse a word token, detecting parameter expansions and command substitutions.\n\n        at_command_start: When True, preserve spaces inside brackets for array\n        assignments like a[1 + 2]=. When False, spaces break the word.\n        ";
		this.skip_whitespace();
		if (this.at_end()) {
			return null;
		}
		let start = this.pos;
		let chars = [];
		let parts = [];
		let bracket_depth = 0;
		let seen_equals = false;
		while (!this.at_end()) {
			let ch = this.peek();
			if (ch === "[" && chars && at_command_start && !seen_equals) {
				let prev_char = chars[chars.length - 1];
				if (prev_char.isalnum() || prev_char === "_" || prev_char === "]") {
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
				while (!this.at_end() && this.peek() !== "'") {
					chars.push(this.advance());
				}
				if (this.at_end()) {
					throw ParseError("Unterminated single quote");
				}
				chars.push(this.advance());
			} else if (ch === '"') {
				this.advance();
				chars.push('"');
				while (!this.at_end() && this.peek() !== '"') {
					let c = this.peek();
					if (c === "\\" && this.pos + 1 < this.length) {
						let next_c = this.source[this.pos + 1];
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
						let arith_result = this._parse_arithmetic_expansion();
						let arith_node = arith_result[0];
						let arith_text = arith_result[1];
						if (arith_node) {
							parts.push(arith_node);
							chars.push(arith_text);
						} else {
							let cmdsub_result = this._parse_command_substitution();
							let cmdsub_node = cmdsub_result[0];
							let cmdsub_text = cmdsub_result[1];
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
						arith_result = this._parse_deprecated_arithmetic();
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
						cmdsub_result = this._parse_command_substitution();
						cmdsub_node = cmdsub_result[0];
						cmdsub_text = cmdsub_result[1];
						if (cmdsub_node) {
							parts.push(cmdsub_node);
							chars.push(cmdsub_text);
						} else {
							chars.push(this.advance());
						}
					} else if (c === "$") {
						let param_result = this._parse_param_expansion();
						let param_node = param_result[0];
						let param_text = param_result[1];
						if (param_node) {
							parts.push(param_node);
							chars.push(param_text);
						} else {
							chars.push(this.advance());
						}
					} else if (c === "`") {
						cmdsub_result = this._parse_backtick_substitution();
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
				if (this.at_end()) {
					throw ParseError("Unterminated double quote");
				}
				chars.push(this.advance());
			} else if (ch === "\\" && this.pos + 1 < this.length) {
				let next_ch = this.source[this.pos + 1];
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
				let ansi_result = this._parse_ansi_c_quote();
				let ansi_node = ansi_result[0];
				let ansi_text = ansi_result[1];
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
				let locale_result = this._parse_locale_string();
				let locale_node = locale_result[0];
				let locale_text = locale_result[1];
				let inner_parts = locale_result[2];
				if (locale_node) {
					parts.push(locale_node);
					parts.extend(inner_parts);
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
				arith_result = this._parse_arithmetic_expansion();
				arith_node = arith_result[0];
				arith_text = arith_result[1];
				if (arith_node) {
					parts.push(arith_node);
					chars.push(arith_text);
				} else {
					cmdsub_result = this._parse_command_substitution();
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
				arith_result = this._parse_deprecated_arithmetic();
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
				cmdsub_result = this._parse_command_substitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					parts.push(cmdsub_node);
					chars.push(cmdsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "$") {
				param_result = this._parse_param_expansion();
				param_node = param_result[0];
				param_text = param_result[1];
				if (param_node) {
					parts.push(param_node);
					chars.push(param_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "`") {
				cmdsub_result = this._parse_backtick_substitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					parts.push(cmdsub_node);
					chars.push(cmdsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (
				_is_redirect_char(ch) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				let procsub_result = this._parse_process_substitution();
				let procsub_node = procsub_result[0];
				let procsub_text = procsub_result[1];
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
				let array_result = this._parse_array_literal();
				let array_node = array_result[0];
				let array_text = array_result[1];
				if (array_node) {
					parts.push(array_node);
					chars.push(array_text);
				} else {
					break;
				}
			} else if (
				_is_extglob_prefix(ch) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				chars.push(this.advance());
				chars.push(this.advance());
				let extglob_depth = 1;
				while (!this.at_end() && extglob_depth > 0) {
					c = this.peek();
					if (c === ")") {
						chars.push(this.advance());
						extglob_depth -= 1;
					} else if (c === "(") {
						chars.push(this.advance());
						extglob_depth += 1;
					} else if (c === "\\") {
						chars.push(this.advance());
						if (!this.at_end()) {
							chars.push(this.advance());
						}
					} else if (c === "'") {
						chars.push(this.advance());
						while (!this.at_end() && this.peek() !== "'") {
							chars.push(this.advance());
						}
						if (!this.at_end()) {
							chars.push(this.advance());
						}
					} else if (c === '"') {
						chars.push(this.advance());
						while (!this.at_end() && this.peek() !== '"') {
							if (this.peek() === "\\" && this.pos + 1 < this.length) {
								chars.push(this.advance());
							}
							chars.push(this.advance());
						}
						if (!this.at_end()) {
							chars.push(this.advance());
						}
					} else if (
						c === "$" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "("
					) {
						chars.push(this.advance());
						chars.push(this.advance());
						if (!this.at_end() && this.peek() === "(") {
							chars.push(this.advance());
							let paren_depth = 2;
							while (!this.at_end() && paren_depth > 0) {
								let pc = this.peek();
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
						_is_extglob_prefix(c) &&
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
			} else if (_is_metachar(ch) && bracket_depth === 0) {
				break;
			} else {
				chars.push(this.advance());
			}
		}
		if (!chars) {
			return null;
		}
		if (parts) {
			return Word(chars.join(""), parts);
		} else {
			return Word(chars.join(""), null);
		}
	}

	_parse_command_substitution() {
		"Parse a $(...) command substitution.\n\n        Returns (node, text) where node is CommandSubstitution and text is raw text.\n        ";
		if (this.at_end() || this.peek() !== "$") {
			return [null, ""];
		}
		let start = this.pos;
		this.advance();
		if (this.at_end() || this.peek() !== "(") {
			this.pos = start;
			return [null, ""];
		}
		this.advance();
		let content_start = this.pos;
		let depth = 1;
		let case_depth = 0;
		while (!this.at_end() && depth > 0) {
			let c = this.peek();
			if (c === "'") {
				this.advance();
				while (!this.at_end() && this.peek() !== "'") {
					this.advance();
				}
				if (!this.at_end()) {
					this.advance();
				}
				continue;
			}
			if (c === '"') {
				this.advance();
				while (!this.at_end() && this.peek() !== '"') {
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
						let nested_depth = 1;
						while (!this.at_end() && nested_depth > 0) {
							let nc = this.peek();
							if (nc === "'") {
								this.advance();
								while (!this.at_end() && this.peek() !== "'") {
									this.advance();
								}
								if (!this.at_end()) {
									this.advance();
								}
							} else if (nc === '"') {
								this.advance();
								while (!this.at_end() && this.peek() !== '"') {
									if (this.peek() === "\\" && this.pos + 1 < this.length) {
										this.advance();
									}
									this.advance();
								}
								if (!this.at_end()) {
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
				if (!this.at_end()) {
					this.advance();
				}
				continue;
			}
			if (c === "\\" && this.pos + 1 < this.length) {
				this.advance();
				this.advance();
				continue;
			}
			if (c === "#" && this._is_word_boundary_before()) {
				while (!this.at_end() && this.peek() !== "\n") {
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
				if (!this.at_end() && this.peek() === "-") {
					this.advance();
				}
				while (!this.at_end() && _is_whitespace_no_newline(this.peek())) {
					this.advance();
				}
				let delimiter_chars = [];
				if (!this.at_end()) {
					let ch = this.peek();
					if (_is_quote(ch)) {
						let quote = this.advance();
						while (!this.at_end() && this.peek() !== quote) {
							delimiter_chars.push(this.advance());
						}
						if (!this.at_end()) {
							this.advance();
						}
					} else if (ch === "\\") {
						this.advance();
						if (!this.at_end()) {
							delimiter_chars.push(this.advance());
						}
						while (!this.at_end() && !_is_metachar(this.peek())) {
							delimiter_chars.push(this.advance());
						}
					} else {
						while (!this.at_end() && !_is_metachar(this.peek())) {
							ch = this.peek();
							if (_is_quote(ch)) {
								quote = this.advance();
								while (!this.at_end() && this.peek() !== quote) {
									delimiter_chars.push(this.advance());
								}
								if (!this.at_end()) {
									this.advance();
								}
							} else if (ch === "\\") {
								this.advance();
								if (!this.at_end()) {
									delimiter_chars.push(this.advance());
								}
							} else {
								delimiter_chars.push(this.advance());
							}
						}
					}
				}
				let delimiter = delimiter_chars.join("");
				if (delimiter) {
					while (!this.at_end() && this.peek() !== "\n") {
						this.advance();
					}
					if (!this.at_end() && this.peek() === "\n") {
						this.advance();
					}
					while (!this.at_end()) {
						let line_start = this.pos;
						let line_end = this.pos;
						while (line_end < this.length && this.source[line_end] !== "\n") {
							line_end += 1;
						}
						let line = _substring(this.source, line_start, line_end);
						this.pos = line_end;
						if (line === delimiter || line.lstrip("\t") === delimiter) {
							if (!this.at_end() && this.peek() === "\n") {
								this.advance();
							}
							break;
						}
						if (!this.at_end() && this.peek() === "\n") {
							this.advance();
						}
					}
				}
				continue;
			}
			if (c === "c" && this._is_word_boundary_before()) {
				if (this._lookahead_keyword("case")) {
					case_depth += 1;
					this._skip_keyword("case");
					continue;
				}
			}
			if (c === "e" && this._is_word_boundary_before() && case_depth > 0) {
				if (this._lookahead_keyword("esac")) {
					case_depth -= 1;
					this._skip_keyword("esac");
					continue;
				}
			}
			if (c === "(") {
				depth += 1;
			} else if (c === ")") {
				if (case_depth > 0 && depth === 1) {
					let saved = this.pos;
					this.advance();
					let temp_depth = 0;
					let temp_case_depth = case_depth;
					let found_esac = false;
					while (!this.at_end()) {
						let tc = this.peek();
						if (tc === "'" || tc === '"') {
							let q = tc;
							this.advance();
							while (!this.at_end() && this.peek() !== q) {
								if (q === '"' && this.peek() === "\\") {
									this.advance();
								}
								this.advance();
							}
							if (!this.at_end()) {
								this.advance();
							}
						} else if (
							tc === "c" &&
							this._is_word_boundary_before() &&
							this._lookahead_keyword("case")
						) {
							temp_case_depth += 1;
							this._skip_keyword("case");
						} else if (
							tc === "e" &&
							this._is_word_boundary_before() &&
							this._lookahead_keyword("esac")
						) {
							temp_case_depth -= 1;
							if (temp_case_depth === 0) {
								found_esac = true;
								break;
							}
							this._skip_keyword("esac");
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
		let content = _substring(this.source, content_start, this.pos);
		this.advance();
		let text = _substring(this.source, start, this.pos);
		let sub_parser = Parser(content);
		let cmd = sub_parser.parse_list();
		if (cmd === null) {
			cmd = Empty();
		}
		return [CommandSubstitution(cmd), text];
	}

	_is_word_boundary_before() {
		"Check if current position is at a word boundary (preceded by space/newline/start).";
		if (this.pos === 0) {
			return true;
		}
		let prev = this.source[this.pos - 1];
		return _is_word_start_context(prev);
	}

	_is_assignment_word(word) {
		"Check if a word is an assignment (contains = outside of quotes).";
		let in_single = false;
		let in_double = false;
		let i = 0;
		while (i < word.value.length) {
			let ch = word.value[i];
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

	_lookahead_keyword(keyword) {
		"Check if keyword appears at current position followed by word boundary.";
		if (this.pos + keyword.length > this.length) {
			return false;
		}
		if (!_starts_with_at(this.source, this.pos, keyword)) {
			return false;
		}
		let after_pos = this.pos + keyword.length;
		if (after_pos >= this.length) {
			return true;
		}
		let after = this.source[after_pos];
		return _is_word_end_context(after);
	}

	_skip_keyword(keyword) {
		"Skip over a keyword.";
		for (const _ of keyword) {
			this.advance();
		}
	}

	_parse_backtick_substitution() {
		"Parse a `...` command substitution.\n\n        Returns (node, text) where node is CommandSubstitution and text is raw text.\n        ";
		if (this.at_end() || this.peek() !== "`") {
			return [null, ""];
		}
		let start = this.pos;
		this.advance();
		let content_chars = [];
		let text_chars = ["`"];
		while (!this.at_end() && this.peek() !== "`") {
			let c = this.peek();
			if (c === "\\" && this.pos + 1 < this.length) {
				let next_c = this.source[this.pos + 1];
				if (next_c === "\n") {
					this.advance();
					this.advance();
				} else if (_is_escape_char_in_dquote(next_c)) {
					this.advance();
					let escaped = this.advance();
					content_chars.push(escaped);
					text_chars.push("\\");
					text_chars.push(escaped);
				} else {
					let ch = this.advance();
					content_chars.push(ch);
					text_chars.push(ch);
				}
			} else {
				ch = this.advance();
				content_chars.push(ch);
				text_chars.push(ch);
			}
		}
		if (this.at_end()) {
			this.pos = start;
			return [null, ""];
		}
		this.advance();
		text_chars.push("`");
		let text = text_chars.join("");
		let content = content_chars.join("");
		let sub_parser = Parser(content);
		let cmd = sub_parser.parse_list();
		if (cmd === null) {
			cmd = Empty();
		}
		return [CommandSubstitution(cmd), text];
	}

	_parse_process_substitution() {
		"Parse a <(...) or >(...) process substitution.\n\n        Returns (node, text) where node is ProcessSubstitution and text is raw text.\n        ";
		if (this.at_end() || !_is_redirect_char(this.peek())) {
			return [null, ""];
		}
		let start = this.pos;
		let direction = this.advance();
		if (this.at_end() || this.peek() !== "(") {
			this.pos = start;
			return [null, ""];
		}
		this.advance();
		let content_start = this.pos;
		let depth = 1;
		while (!this.at_end() && depth > 0) {
			let c = this.peek();
			if (c === "'") {
				this.advance();
				while (!this.at_end() && this.peek() !== "'") {
					this.advance();
				}
				if (!this.at_end()) {
					this.advance();
				}
				continue;
			}
			if (c === '"') {
				this.advance();
				while (!this.at_end() && this.peek() !== '"') {
					if (this.peek() === "\\" && this.pos + 1 < this.length) {
						this.advance();
					}
					this.advance();
				}
				if (!this.at_end()) {
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
		let content = _substring(this.source, content_start, this.pos);
		this.advance();
		let text = _substring(this.source, start, this.pos);
		let sub_parser = Parser(content);
		let cmd = sub_parser.parse_list();
		if (cmd === null) {
			cmd = Empty();
		}
		return [ProcessSubstitution(direction, cmd), text];
	}

	_parse_array_literal() {
		"Parse an array literal (word1 word2 ...).\n\n        Returns (node, text) where node is Array and text is raw text.\n        Called when positioned at the opening '(' after '=' or '+='.\n        ";
		if (this.at_end() || this.peek() !== "(") {
			return [null, ""];
		}
		let start = this.pos;
		this.advance();
		let elements = [];
		while (true) {
			while (!this.at_end() && _is_whitespace(this.peek())) {
				this.advance();
			}
			if (this.at_end()) {
				throw ParseError("Unterminated array literal");
			}
			if (this.peek() === ")") {
				break;
			}
			let word = this.parse_word();
			if (word === null) {
				if (this.peek() === ")") {
					break;
				}
				throw ParseError("Expected word in array literal");
			}
			elements.push(word);
		}
		if (this.at_end() || this.peek() !== ")") {
			throw ParseError("Expected ) to close array literal");
		}
		this.advance();
		let text = _substring(this.source, start, this.pos);
		return [Array(elements), text];
	}

	_parse_arithmetic_expansion() {
		"Parse a $((...)) arithmetic expansion with parsed internals.\n\n        Returns (node, text) where node is ArithmeticExpansion and text is raw text.\n        Returns (None, \"\") if this is not arithmetic expansion (e.g., $( ( ... ) )\n        which is command substitution containing a subshell).\n        ";
		if (this.at_end() || this.peek() !== "$") {
			return [null, ""];
		}
		let start = this.pos;
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
		let content_start = this.pos;
		let depth = 1;
		while (!this.at_end() && depth > 0) {
			let c = this.peek();
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
		if (this.at_end() || depth !== 1) {
			this.pos = start;
			return [null, ""];
		}
		let content = _substring(this.source, content_start, this.pos);
		this.advance();
		this.advance();
		let text = _substring(this.source, start, this.pos);
		let expr = this._parse_arith_expr(content);
		return [ArithmeticExpansion(expr), text];
	}

	_parse_arith_expr(content) {
		"Parse an arithmetic expression string into AST nodes.";
		let saved_arith_src = getattr(this, "_arith_src", null);
		let saved_arith_pos = getattr(this, "_arith_pos", null);
		let saved_arith_len = getattr(this, "_arith_len", null);
		this._arith_src = content;
		this._arith_pos = 0;
		this._arith_len = content.length;
		this._arith_skip_ws();
		if (this._arith_at_end()) {
			let result = null;
		} else {
			result = this._arith_parse_comma();
		}
		if (saved_arith_src !== null) {
			this._arith_src = saved_arith_src;
			this._arith_pos = saved_arith_pos;
			this._arith_len = saved_arith_len;
		}
		return result;
	}

	_arith_at_end() {
		return this._arith_pos >= this._arith_len;
	}

	_arith_peek(offset) {
		let pos = this._arith_pos + offset;
		if (pos >= this._arith_len) {
			return "";
		}
		return this._arith_src[pos];
	}

	_arith_advance() {
		if (this._arith_at_end()) {
			return "";
		}
		let c = this._arith_src[this._arith_pos];
		this._arith_pos += 1;
		return c;
	}

	_arith_skip_ws() {
		while (!this._arith_at_end()) {
			let c = this._arith_src[this._arith_pos];
			if (_is_whitespace(c)) {
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

	_arith_match(s) {
		"Check if the next characters match s (without consuming).";
		return _starts_with_at(this._arith_src, this._arith_pos, s);
	}

	_arith_consume(s) {
		"If next chars match s, consume them and return True.";
		if (this._arith_match(s)) {
			this._arith_pos += s.length;
			return true;
		}
		return false;
	}

	_arith_parse_comma() {
		"Parse comma expressions (lowest precedence).";
		let left = this._arith_parse_assign();
		while (true) {
			this._arith_skip_ws();
			if (this._arith_consume(",")) {
				this._arith_skip_ws();
				let right = this._arith_parse_assign();
				left = ArithComma(left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_assign() {
		"Parse assignment expressions (right associative).";
		let left = this._arith_parse_ternary();
		this._arith_skip_ws();
		let assign_ops = [
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
		for (const op of assign_ops) {
			if (this._arith_match(op)) {
				if (op === "=" && this._arith_peek(1) === "=") {
					break;
				}
				this._arith_consume(op);
				this._arith_skip_ws();
				let right = this._arith_parse_assign();
				return ArithAssign(op, left, right);
			}
		}
		return left;
	}

	_arith_parse_ternary() {
		"Parse ternary conditional (right associative).";
		let cond = this._arith_parse_logical_or();
		this._arith_skip_ws();
		if (this._arith_consume("?")) {
			this._arith_skip_ws();
			if (this._arith_match(":")) {
				let if_true = null;
			} else {
				if_true = this._arith_parse_assign();
			}
			this._arith_skip_ws();
			if (this._arith_consume(":")) {
				this._arith_skip_ws();
				if (this._arith_at_end() || this._arith_peek() === ")") {
					let if_false = null;
				} else {
					if_false = this._arith_parse_ternary();
				}
			} else {
				if_false = null;
			}
			return ArithTernary(cond, if_true, if_false);
		}
		return cond;
	}

	_arith_parse_logical_or() {
		"Parse logical or (||).";
		let left = this._arith_parse_logical_and();
		while (true) {
			this._arith_skip_ws();
			if (this._arith_match("||")) {
				this._arith_consume("||");
				this._arith_skip_ws();
				let right = this._arith_parse_logical_and();
				left = ArithBinaryOp("||", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_logical_and() {
		"Parse logical and (&&).";
		let left = this._arith_parse_bitwise_or();
		while (true) {
			this._arith_skip_ws();
			if (this._arith_match("&&")) {
				this._arith_consume("&&");
				this._arith_skip_ws();
				let right = this._arith_parse_bitwise_or();
				left = ArithBinaryOp("&&", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_bitwise_or() {
		"Parse bitwise or (|).";
		let left = this._arith_parse_bitwise_xor();
		while (true) {
			this._arith_skip_ws();
			if (
				this._arith_peek() === "|" &&
				this._arith_peek(1) !== "|" &&
				this._arith_peek(1) !== "="
			) {
				this._arith_advance();
				this._arith_skip_ws();
				let right = this._arith_parse_bitwise_xor();
				left = ArithBinaryOp("|", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_bitwise_xor() {
		"Parse bitwise xor (^).";
		let left = this._arith_parse_bitwise_and();
		while (true) {
			this._arith_skip_ws();
			if (this._arith_peek() === "^" && this._arith_peek(1) !== "=") {
				this._arith_advance();
				this._arith_skip_ws();
				let right = this._arith_parse_bitwise_and();
				left = ArithBinaryOp("^", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_bitwise_and() {
		"Parse bitwise and (&).";
		let left = this._arith_parse_equality();
		while (true) {
			this._arith_skip_ws();
			if (
				this._arith_peek() === "&" &&
				this._arith_peek(1) !== "&" &&
				this._arith_peek(1) !== "="
			) {
				this._arith_advance();
				this._arith_skip_ws();
				let right = this._arith_parse_equality();
				left = ArithBinaryOp("&", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_equality() {
		"Parse equality (== !=).";
		let left = this._arith_parse_comparison();
		while (true) {
			this._arith_skip_ws();
			if (this._arith_match("==")) {
				this._arith_consume("==");
				this._arith_skip_ws();
				let right = this._arith_parse_comparison();
				left = ArithBinaryOp("==", left, right);
			} else if (this._arith_match("!=")) {
				this._arith_consume("!=");
				this._arith_skip_ws();
				right = this._arith_parse_comparison();
				left = ArithBinaryOp("!=", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_comparison() {
		"Parse comparison (< > <= >=).";
		let left = this._arith_parse_shift();
		while (true) {
			this._arith_skip_ws();
			if (this._arith_match("<=")) {
				this._arith_consume("<=");
				this._arith_skip_ws();
				let right = this._arith_parse_shift();
				left = ArithBinaryOp("<=", left, right);
			} else if (this._arith_match(">=")) {
				this._arith_consume(">=");
				this._arith_skip_ws();
				right = this._arith_parse_shift();
				left = ArithBinaryOp(">=", left, right);
			} else if (
				this._arith_peek() === "<" &&
				this._arith_peek(1) !== "<" &&
				this._arith_peek(1) !== "="
			) {
				this._arith_advance();
				this._arith_skip_ws();
				right = this._arith_parse_shift();
				left = ArithBinaryOp("<", left, right);
			} else if (
				this._arith_peek() === ">" &&
				this._arith_peek(1) !== ">" &&
				this._arith_peek(1) !== "="
			) {
				this._arith_advance();
				this._arith_skip_ws();
				right = this._arith_parse_shift();
				left = ArithBinaryOp(">", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_shift() {
		"Parse shift (<< >>).";
		let left = this._arith_parse_additive();
		while (true) {
			this._arith_skip_ws();
			if (this._arith_match("<<=")) {
				break;
			}
			if (this._arith_match(">>=")) {
				break;
			}
			if (this._arith_match("<<")) {
				this._arith_consume("<<");
				this._arith_skip_ws();
				let right = this._arith_parse_additive();
				left = ArithBinaryOp("<<", left, right);
			} else if (this._arith_match(">>")) {
				this._arith_consume(">>");
				this._arith_skip_ws();
				right = this._arith_parse_additive();
				left = ArithBinaryOp(">>", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_additive() {
		"Parse addition and subtraction (+ -).";
		let left = this._arith_parse_multiplicative();
		while (true) {
			this._arith_skip_ws();
			let c = this._arith_peek();
			let c2 = this._arith_peek(1);
			if (c === "+" && c2 !== "+" && c2 !== "=") {
				this._arith_advance();
				this._arith_skip_ws();
				let right = this._arith_parse_multiplicative();
				left = ArithBinaryOp("+", left, right);
			} else if (c === "-" && c2 !== "-" && c2 !== "=") {
				this._arith_advance();
				this._arith_skip_ws();
				right = this._arith_parse_multiplicative();
				left = ArithBinaryOp("-", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_multiplicative() {
		"Parse multiplication, division, modulo (* / %).";
		let left = this._arith_parse_exponentiation();
		while (true) {
			this._arith_skip_ws();
			let c = this._arith_peek();
			let c2 = this._arith_peek(1);
			if (c === "*" && c2 !== "*" && c2 !== "=") {
				this._arith_advance();
				this._arith_skip_ws();
				let right = this._arith_parse_exponentiation();
				left = ArithBinaryOp("*", left, right);
			} else if (c === "/" && c2 !== "=") {
				this._arith_advance();
				this._arith_skip_ws();
				right = this._arith_parse_exponentiation();
				left = ArithBinaryOp("/", left, right);
			} else if (c === "%" && c2 !== "=") {
				this._arith_advance();
				this._arith_skip_ws();
				right = this._arith_parse_exponentiation();
				left = ArithBinaryOp("%", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_exponentiation() {
		"Parse exponentiation (**) - right associative.";
		let left = this._arith_parse_unary();
		this._arith_skip_ws();
		if (this._arith_match("**")) {
			this._arith_consume("**");
			this._arith_skip_ws();
			let right = this._arith_parse_exponentiation();
			return ArithBinaryOp("**", left, right);
		}
		return left;
	}

	_arith_parse_unary() {
		"Parse unary operators (! ~ + - ++ --).";
		this._arith_skip_ws();
		if (this._arith_match("++")) {
			this._arith_consume("++");
			this._arith_skip_ws();
			let operand = this._arith_parse_unary();
			return ArithPreIncr(operand);
		}
		if (this._arith_match("--")) {
			this._arith_consume("--");
			this._arith_skip_ws();
			operand = this._arith_parse_unary();
			return ArithPreDecr(operand);
		}
		let c = this._arith_peek();
		if (c === "!") {
			this._arith_advance();
			this._arith_skip_ws();
			operand = this._arith_parse_unary();
			return ArithUnaryOp("!", operand);
		}
		if (c === "~") {
			this._arith_advance();
			this._arith_skip_ws();
			operand = this._arith_parse_unary();
			return ArithUnaryOp("~", operand);
		}
		if (c === "+" && this._arith_peek(1) !== "+") {
			this._arith_advance();
			this._arith_skip_ws();
			operand = this._arith_parse_unary();
			return ArithUnaryOp("+", operand);
		}
		if (c === "-" && this._arith_peek(1) !== "-") {
			this._arith_advance();
			this._arith_skip_ws();
			operand = this._arith_parse_unary();
			return ArithUnaryOp("-", operand);
		}
		return this._arith_parse_postfix();
	}

	_arith_parse_postfix() {
		"Parse postfix operators (++ -- []).";
		let left = this._arith_parse_primary();
		while (true) {
			this._arith_skip_ws();
			if (this._arith_match("++")) {
				this._arith_consume("++");
				left = ArithPostIncr(left);
			} else if (this._arith_match("--")) {
				this._arith_consume("--");
				left = ArithPostDecr(left);
			} else if (this._arith_peek() === "[") {
				if (left.kind === "var") {
					this._arith_advance();
					this._arith_skip_ws();
					let index = this._arith_parse_comma();
					this._arith_skip_ws();
					if (!this._arith_consume("]")) {
						throw ParseError("Expected ']' in array subscript");
					}
					left = ArithSubscript(left.name, index);
				} else {
					break;
				}
			} else {
				break;
			}
		}
		return left;
	}

	_arith_parse_primary() {
		"Parse primary expressions (numbers, variables, parens, expansions).";
		this._arith_skip_ws();
		let c = this._arith_peek();
		if (c === "(") {
			this._arith_advance();
			this._arith_skip_ws();
			let expr = this._arith_parse_comma();
			this._arith_skip_ws();
			if (!this._arith_consume(")")) {
				throw ParseError("Expected ')' in arithmetic expression");
			}
			return expr;
		}
		if (c === "$") {
			return this._arith_parse_expansion();
		}
		if (c === "'") {
			return this._arith_parse_single_quote();
		}
		if (c === '"') {
			return this._arith_parse_double_quote();
		}
		if (c === "`") {
			return this._arith_parse_backtick();
		}
		if (c === "\\") {
			this._arith_advance();
			if (this._arith_at_end()) {
				throw ParseError("Unexpected end after backslash in arithmetic");
			}
			let escaped_char = this._arith_advance();
			return ArithEscape(escaped_char);
		}
		return this._arith_parse_number_or_var();
	}

	_arith_parse_expansion() {
		"Parse $var, ${...}, or $(...).";
		if (!this._arith_consume("$")) {
			throw ParseError("Expected '$'");
		}
		let c = this._arith_peek();
		if (c === "(") {
			return this._arith_parse_cmdsub();
		}
		if (c === "{") {
			return this._arith_parse_braced_param();
		}
		let name_chars = [];
		while (!this._arith_at_end()) {
			let ch = this._arith_peek();
			if (ch.isalnum() || ch === "_") {
				name_chars.push(this._arith_advance());
			} else if (
				(_is_special_param_or_digit(ch) || ch === "#") &&
				!name_chars
			) {
				name_chars.push(this._arith_advance());
				break;
			} else {
				break;
			}
		}
		if (!name_chars) {
			throw ParseError("Expected variable name after $");
		}
		return ParamExpansion(name_chars.join(""));
	}

	_arith_parse_cmdsub() {
		"Parse $(...) command substitution inside arithmetic.";
		this._arith_advance();
		if (this._arith_peek() === "(") {
			this._arith_advance();
			let depth = 1;
			let content_start = this._arith_pos;
			while (!this._arith_at_end() && depth > 0) {
				let ch = this._arith_peek();
				if (ch === "(") {
					depth += 1;
					this._arith_advance();
				} else if (ch === ")") {
					if (depth === 1 && this._arith_peek(1) === ")") {
						break;
					}
					depth -= 1;
					this._arith_advance();
				} else {
					this._arith_advance();
				}
			}
			let content = _substring(this._arith_src, content_start, this._arith_pos);
			this._arith_advance();
			this._arith_advance();
			let inner_expr = this._parse_arith_expr(content);
			return ArithmeticExpansion(inner_expr);
		}
		depth = 1;
		content_start = this._arith_pos;
		while (!this._arith_at_end() && depth > 0) {
			ch = this._arith_peek();
			if (ch === "(") {
				depth += 1;
				this._arith_advance();
			} else if (ch === ")") {
				depth -= 1;
				if (depth === 0) {
					break;
				}
				this._arith_advance();
			} else {
				this._arith_advance();
			}
		}
		content = _substring(this._arith_src, content_start, this._arith_pos);
		this._arith_advance();
		let saved_pos = this.pos;
		let saved_src = this.source;
		let saved_len = this.length;
		this.source = content;
		this.pos = 0;
		this.length = content.length;
		let cmd = this.parse_list();
		this.source = saved_src;
		this.pos = saved_pos;
		this.length = saved_len;
		return CommandSubstitution(cmd);
	}

	_arith_parse_braced_param() {
		"Parse ${...} parameter expansion inside arithmetic.";
		this._arith_advance();
		if (this._arith_peek() === "!") {
			this._arith_advance();
			let name_chars = [];
			while (!this._arith_at_end() && this._arith_peek() !== "}") {
				name_chars.push(this._arith_advance());
			}
			this._arith_consume("}");
			return ParamIndirect(name_chars.join(""));
		}
		if (this._arith_peek() === "#") {
			this._arith_advance();
			name_chars = [];
			while (!this._arith_at_end() && this._arith_peek() !== "}") {
				name_chars.push(this._arith_advance());
			}
			this._arith_consume("}");
			return ParamLength(name_chars.join(""));
		}
		name_chars = [];
		while (!this._arith_at_end()) {
			let ch = this._arith_peek();
			if (ch === "}") {
				this._arith_advance();
				return ParamExpansion(name_chars.join(""));
			}
			if (_is_param_expansion_op(ch)) {
				break;
			}
			name_chars.push(this._arith_advance());
		}
		let name = name_chars.join("");
		let op_chars = [];
		let depth = 1;
		while (!this._arith_at_end() && depth > 0) {
			ch = this._arith_peek();
			if (ch === "{") {
				depth += 1;
				op_chars.push(this._arith_advance());
			} else if (ch === "}") {
				depth -= 1;
				if (depth === 0) {
					break;
				}
				op_chars.push(this._arith_advance());
			} else {
				op_chars.push(this._arith_advance());
			}
		}
		this._arith_consume("}");
		let op_str = op_chars.join("");
		if (op_str.startsWith(":-")) {
			return ParamExpansion(name, ":-", _substring(op_str, 2, op_str.length));
		}
		if (op_str.startsWith(":=")) {
			return ParamExpansion(name, ":=", _substring(op_str, 2, op_str.length));
		}
		if (op_str.startsWith(":+")) {
			return ParamExpansion(name, ":+", _substring(op_str, 2, op_str.length));
		}
		if (op_str.startsWith(":?")) {
			return ParamExpansion(name, ":?", _substring(op_str, 2, op_str.length));
		}
		if (op_str.startsWith(":")) {
			return ParamExpansion(name, ":", _substring(op_str, 1, op_str.length));
		}
		if (op_str.startsWith("##")) {
			return ParamExpansion(name, "##", _substring(op_str, 2, op_str.length));
		}
		if (op_str.startsWith("#")) {
			return ParamExpansion(name, "#", _substring(op_str, 1, op_str.length));
		}
		if (op_str.startsWith("%%")) {
			return ParamExpansion(name, "%%", _substring(op_str, 2, op_str.length));
		}
		if (op_str.startsWith("%")) {
			return ParamExpansion(name, "%", _substring(op_str, 1, op_str.length));
		}
		if (op_str.startsWith("//")) {
			return ParamExpansion(name, "//", _substring(op_str, 2, op_str.length));
		}
		if (op_str.startsWith("/")) {
			return ParamExpansion(name, "/", _substring(op_str, 1, op_str.length));
		}
		return ParamExpansion(name, "", op_str);
	}

	_arith_parse_single_quote() {
		"Parse '...' inside arithmetic - returns content as a number/string.";
		this._arith_advance();
		let content_start = this._arith_pos;
		while (!this._arith_at_end() && this._arith_peek() !== "'") {
			this._arith_advance();
		}
		let content = _substring(this._arith_src, content_start, this._arith_pos);
		if (!this._arith_consume("'")) {
			throw ParseError("Unterminated single quote in arithmetic");
		}
		return ArithNumber(content);
	}

	_arith_parse_double_quote() {
		"Parse \"...\" inside arithmetic - may contain expansions.";
		this._arith_advance();
		let content_start = this._arith_pos;
		while (!this._arith_at_end() && this._arith_peek() !== '"') {
			let c = this._arith_peek();
			if (c === "\\" && !this._arith_at_end()) {
				this._arith_advance();
				this._arith_advance();
			} else {
				this._arith_advance();
			}
		}
		let content = _substring(this._arith_src, content_start, this._arith_pos);
		if (!this._arith_consume('"')) {
			throw ParseError("Unterminated double quote in arithmetic");
		}
		return ArithNumber(content);
	}

	_arith_parse_backtick() {
		"Parse `...` command substitution inside arithmetic.";
		this._arith_advance();
		let content_start = this._arith_pos;
		while (!this._arith_at_end() && this._arith_peek() !== "`") {
			let c = this._arith_peek();
			if (c === "\\" && !this._arith_at_end()) {
				this._arith_advance();
				this._arith_advance();
			} else {
				this._arith_advance();
			}
		}
		let content = _substring(this._arith_src, content_start, this._arith_pos);
		if (!this._arith_consume("`")) {
			throw ParseError("Unterminated backtick in arithmetic");
		}
		let saved_pos = this.pos;
		let saved_src = this.source;
		let saved_len = this.length;
		this.source = content;
		this.pos = 0;
		this.length = content.length;
		let cmd = this.parse_list();
		this.source = saved_src;
		this.pos = saved_pos;
		this.length = saved_len;
		return CommandSubstitution(cmd);
	}

	_arith_parse_number_or_var() {
		"Parse a number or variable name.";
		this._arith_skip_ws();
		let chars = [];
		let c = this._arith_peek();
		if (c.isdigit()) {
			while (!this._arith_at_end()) {
				let ch = this._arith_peek();
				if (ch.isalnum() || ch === "#" || ch === "_") {
					chars.push(this._arith_advance());
				} else {
					break;
				}
			}
			return ArithNumber(chars.join(""));
		}
		if (c.isalpha() || c === "_") {
			while (!this._arith_at_end()) {
				ch = this._arith_peek();
				if (ch.isalnum() || ch === "_") {
					chars.push(this._arith_advance());
				} else {
					break;
				}
			}
			return ArithVar(chars.join(""));
		}
		throw ParseError(
			"Unexpected character '" + c + "' in arithmetic expression",
		);
	}

	_parse_deprecated_arithmetic() {
		"Parse a deprecated $[expr] arithmetic expansion.\n\n        Returns (node, text) where node is ArithDeprecated and text is raw text.\n        ";
		if (this.at_end() || this.peek() !== "$") {
			return [null, ""];
		}
		let start = this.pos;
		if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== "[") {
			return [null, ""];
		}
		this.advance();
		this.advance();
		let content_start = this.pos;
		let depth = 1;
		while (!this.at_end() && depth > 0) {
			let c = this.peek();
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
		if (this.at_end() || depth !== 0) {
			this.pos = start;
			return [null, ""];
		}
		let content = _substring(this.source, content_start, this.pos);
		this.advance();
		let text = _substring(this.source, start, this.pos);
		return [ArithDeprecated(content), text];
	}

	_parse_ansi_c_quote() {
		"Parse ANSI-C quoting $'...'.\n\n        Returns (node, text) where node is the AST node and text is the raw text.\n        Returns (None, \"\") if not a valid ANSI-C quote.\n        ";
		if (this.at_end() || this.peek() !== "$") {
			return [null, ""];
		}
		if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== "'") {
			return [null, ""];
		}
		let start = this.pos;
		this.advance();
		this.advance();
		let content_chars = [];
		let found_close = false;
		while (!this.at_end()) {
			let ch = this.peek();
			if (ch === "'") {
				this.advance();
				found_close = true;
				break;
			} else if (ch === "\\") {
				content_chars.push(this.advance());
				if (!this.at_end()) {
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
		let text = _substring(this.source, start, this.pos);
		let content = content_chars.join("");
		return [AnsiCQuote(content), text];
	}

	_parse_locale_string() {
		"Parse locale translation $\"...\".\n\n        Returns (node, text, inner_parts) where:\n        - node is the LocaleString AST node\n        - text is the raw text including $\"...\"\n        - inner_parts is a list of expansion nodes found inside\n        Returns (None, \"\", []) if not a valid locale string.\n        ";
		if (this.at_end() || this.peek() !== "$") {
			return [null, "", []];
		}
		if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== '"') {
			return [null, "", []];
		}
		let start = this.pos;
		this.advance();
		this.advance();
		let content_chars = [];
		let inner_parts = [];
		let found_close = false;
		while (!this.at_end()) {
			let ch = this.peek();
			if (ch === '"') {
				this.advance();
				found_close = true;
				break;
			} else if (ch === "\\" && this.pos + 1 < this.length) {
				let next_ch = this.source[this.pos + 1];
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
				let arith_result = this._parse_arithmetic_expansion();
				let arith_node = arith_result[0];
				let arith_text = arith_result[1];
				if (arith_node) {
					inner_parts.push(arith_node);
					content_chars.push(arith_text);
				} else {
					let cmdsub_result = this._parse_command_substitution();
					let cmdsub_node = cmdsub_result[0];
					let cmdsub_text = cmdsub_result[1];
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
				cmdsub_result = this._parse_command_substitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					inner_parts.push(cmdsub_node);
					content_chars.push(cmdsub_text);
				} else {
					content_chars.push(this.advance());
				}
			} else if (ch === "$") {
				let param_result = this._parse_param_expansion();
				let param_node = param_result[0];
				let param_text = param_result[1];
				if (param_node) {
					inner_parts.push(param_node);
					content_chars.push(param_text);
				} else {
					content_chars.push(this.advance());
				}
			} else if (ch === "`") {
				cmdsub_result = this._parse_backtick_substitution();
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
		let content = content_chars.join("");
		let text = '$"' + content + '"';
		return [LocaleString(content), text, inner_parts];
	}

	_parse_param_expansion() {
		"Parse a parameter expansion starting at $.\n\n        Returns (node, text) where node is the AST node and text is the raw text.\n        Returns (None, \"\") if not a valid parameter expansion.\n        ";
		if (this.at_end() || this.peek() !== "$") {
			return [null, ""];
		}
		let start = this.pos;
		this.advance();
		if (this.at_end()) {
			this.pos = start;
			return [null, ""];
		}
		let ch = this.peek();
		if (ch === "{") {
			this.advance();
			return this._parse_braced_param(start);
		}
		if (_is_special_param_or_digit(ch) || ch === "#") {
			this.advance();
			let text = _substring(this.source, start, this.pos);
			return [ParamExpansion(ch), text];
		}
		if (ch.isalpha() || ch === "_") {
			let name_start = this.pos;
			while (!this.at_end()) {
				let c = this.peek();
				if (c.isalnum() || c === "_") {
					this.advance();
				} else {
					break;
				}
			}
			let name = _substring(this.source, name_start, this.pos);
			text = _substring(this.source, start, this.pos);
			return [ParamExpansion(name), text];
		}
		this.pos = start;
		return [null, ""];
	}

	_parse_braced_param(start) {
		"Parse contents of ${...} after the opening brace.\n\n        start is the position of the $.\n        Returns (node, text).\n        ";
		if (this.at_end()) {
			this.pos = start;
			return [null, ""];
		}
		let ch = this.peek();
		if (ch === "#") {
			this.advance();
			let param = this._consume_param_name();
			if (param && !this.at_end() && this.peek() === "}") {
				this.advance();
				let text = _substring(this.source, start, this.pos);
				return [ParamLength(param), text];
			}
			this.pos = start;
			return [null, ""];
		}
		if (ch === "!") {
			this.advance();
			param = this._consume_param_name();
			if (param) {
				while (!this.at_end() && _is_whitespace_no_newline(this.peek())) {
					this.advance();
				}
				if (!this.at_end() && this.peek() === "}") {
					this.advance();
					text = _substring(this.source, start, this.pos);
					return [ParamIndirect(param), text];
				}
				if (!this.at_end() && _is_at_or_star(this.peek())) {
					let suffix = this.advance();
					while (!this.at_end() && _is_whitespace_no_newline(this.peek())) {
						this.advance();
					}
					if (!this.at_end() && this.peek() === "}") {
						this.advance();
						text = _substring(this.source, start, this.pos);
						return [ParamIndirect(param + suffix), text];
					}
					this.pos = start;
					return [null, ""];
				}
				let op = this._consume_param_operator();
				if (op !== null) {
					let arg_chars = [];
					let depth = 1;
					while (!this.at_end() && depth > 0) {
						let c = this.peek();
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
							if (!this.at_end()) {
								arg_chars.push(this.advance());
							}
						} else {
							arg_chars.push(this.advance());
						}
					}
					if (depth === 0) {
						this.advance();
						let arg = arg_chars.join("");
						text = _substring(this.source, start, this.pos);
						return [ParamIndirect(param, op, arg), text];
					}
				}
			}
			this.pos = start;
			return [null, ""];
		}
		param = this._consume_param_name();
		if (!param) {
			depth = 1;
			let content_start = this.pos;
			while (!this.at_end() && depth > 0) {
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
					if (!this.at_end()) {
						this.advance();
					}
				} else {
					this.advance();
				}
			}
			if (depth === 0) {
				let content = _substring(this.source, content_start, this.pos);
				this.advance();
				text = _substring(this.source, start, this.pos);
				return [ParamExpansion(content), text];
			}
			this.pos = start;
			return [null, ""];
		}
		if (this.at_end()) {
			this.pos = start;
			return [null, ""];
		}
		if (this.peek() === "}") {
			this.advance();
			text = _substring(this.source, start, this.pos);
			return [ParamExpansion(param), text];
		}
		op = this._consume_param_operator();
		if (op === null) {
			op = this.advance();
		}
		arg_chars = [];
		depth = 1;
		let in_single_quote = false;
		let in_double_quote = false;
		while (!this.at_end() && depth > 0) {
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
					if (!this.at_end()) {
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
				let paren_depth = 1;
				while (!this.at_end() && paren_depth > 0) {
					let pc = this.peek();
					if (pc === "(") {
						paren_depth += 1;
					} else if (pc === ")") {
						paren_depth -= 1;
					} else if (pc === "\\") {
						arg_chars.push(this.advance());
						if (!this.at_end()) {
							arg_chars.push(this.advance());
						}
						continue;
					}
					arg_chars.push(this.advance());
				}
			} else if (c === "`" && !in_single_quote) {
				arg_chars.push(this.advance());
				while (!this.at_end() && this.peek() !== "`") {
					let bc = this.peek();
					if (bc === "\\" && this.pos + 1 < this.length) {
						let next_c = this.source[this.pos + 1];
						if (_is_escape_char_in_dquote(next_c)) {
							arg_chars.push(this.advance());
						}
					}
					arg_chars.push(this.advance());
				}
				if (!this.at_end()) {
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
		return [ParamExpansion(param, op, arg), text];
	}

	_consume_param_name() {
		"Consume a parameter name (variable name, special char, or array subscript).";
		if (this.at_end()) {
			return null;
		}
		let ch = this.peek();
		if (_is_special_param(ch)) {
			this.advance();
			return ch;
		}
		if (ch.isdigit()) {
			let name_chars = [];
			while (!this.at_end() && this.peek().isdigit()) {
				name_chars.push(this.advance());
			}
			return name_chars.join("");
		}
		if (ch.isalpha() || ch === "_") {
			name_chars = [];
			while (!this.at_end()) {
				let c = this.peek();
				if (c.isalnum() || c === "_") {
					name_chars.push(this.advance());
				} else if (c === "[") {
					name_chars.push(this.advance());
					let bracket_depth = 1;
					while (!this.at_end() && bracket_depth > 0) {
						let sc = this.peek();
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
					if (!this.at_end() && this.peek() === "]") {
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

	_consume_param_operator() {
		"Consume a parameter expansion operator.";
		if (this.at_end()) {
			return null;
		}
		let ch = this.peek();
		if (ch === ":") {
			this.advance();
			if (this.at_end()) {
				return ":";
			}
			let next_ch = this.peek();
			if (_is_simple_param_op(next_ch)) {
				this.advance();
				return ":" + next_ch;
			}
			return ":";
		}
		if (_is_simple_param_op(ch)) {
			this.advance();
			return ch;
		}
		if (ch === "#") {
			this.advance();
			if (!this.at_end() && this.peek() === "#") {
				this.advance();
				return "##";
			}
			return "#";
		}
		if (ch === "%") {
			this.advance();
			if (!this.at_end() && this.peek() === "%") {
				this.advance();
				return "%%";
			}
			return "%";
		}
		if (ch === "/") {
			this.advance();
			if (!this.at_end()) {
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
			if (!this.at_end() && this.peek() === "^") {
				this.advance();
				return "^^";
			}
			return "^";
		}
		if (ch === ",") {
			this.advance();
			if (!this.at_end() && this.peek() === ",") {
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

	parse_redirect() {
		"Parse a redirection operator and target.";
		this.skip_whitespace();
		if (this.at_end()) {
			return null;
		}
		let start = this.pos;
		let fd = null;
		let varfd = null;
		if (this.peek() === "{") {
			let saved = this.pos;
			this.advance();
			let varname_chars = [];
			while (
				!this.at_end() &&
				this.peek() !== "}" &&
				!_is_redirect_char(this.peek())
			) {
				let ch = this.peek();
				if (ch.isalnum() || ch === "_" || ch === "[" || ch === "]") {
					varname_chars.push(this.advance());
				} else {
					break;
				}
			}
			if (!this.at_end() && this.peek() === "}" && varname_chars) {
				this.advance();
				varfd = varname_chars.join("");
			} else {
				this.pos = saved;
			}
		}
		if (varfd === null && this.peek() && this.peek().isdigit()) {
			let fd_chars = [];
			while (!this.at_end() && this.peek().isdigit()) {
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
			if (fd !== null) {
				this.pos = start;
				return null;
			}
			this.advance();
			this.advance();
			if (!this.at_end() && this.peek() === ">") {
				this.advance();
				let op = "&>>";
			} else {
				op = "&>";
			}
			this.skip_whitespace();
			let target = this.parse_word();
			if (target === null) {
				throw ParseError("Expected target for redirect " + op);
			}
			return Redirect(op, target);
		}
		if (ch === null || !_is_redirect_char(ch)) {
			this.pos = start;
			return null;
		}
		if (
			fd === null &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			this.pos = start;
			return null;
		}
		op = this.advance();
		let strip_tabs = false;
		if (!this.at_end()) {
			let next_ch = this.peek();
			if (op === ">" && next_ch === ">") {
				this.advance();
				op = ">>";
			} else if (op === "<" && next_ch === "<") {
				this.advance();
				if (!this.at_end() && this.peek() === "<") {
					this.advance();
					op = "<<<";
				} else if (!this.at_end() && this.peek() === "-") {
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
			} else if (
				fd === null &&
				varfd === null &&
				op === ">" &&
				next_ch === "&"
			) {
				if (
					this.pos + 1 >= this.length ||
					!_is_digit_or_dash(this.source[this.pos + 1])
				) {
					this.advance();
					op = ">&";
				}
			} else if (
				fd === null &&
				varfd === null &&
				op === "<" &&
				next_ch === "&"
			) {
				if (
					this.pos + 1 >= this.length ||
					!_is_digit_or_dash(this.source[this.pos + 1])
				) {
					this.advance();
					op = "<&";
				}
			}
		}
		if (op === "<<") {
			return this._parse_heredoc(fd, strip_tabs);
		}
		if (varfd !== null) {
			op = "{" + varfd + "}" + op;
		} else if (fd !== null) {
			op = String(fd) + op;
		}
		this.skip_whitespace();
		if (!this.at_end() && this.peek() === "&") {
			this.advance();
			if (!this.at_end() && (this.peek().isdigit() || this.peek() === "-")) {
				fd_chars = [];
				while (!this.at_end() && this.peek().isdigit()) {
					fd_chars.push(this.advance());
				}
				if (fd_chars) {
					let fd_target = fd_chars.join("");
				} else {
					fd_target = "";
				}
				if (!this.at_end() && this.peek() === "-") {
					fd_target += this.advance();
				}
				target = Word("&" + fd_target);
			} else {
				let inner_word = this.parse_word();
				if (inner_word !== null) {
					target = Word("&" + inner_word.value);
					target.parts = inner_word.parts;
				} else {
					throw ParseError("Expected target for redirect " + op);
				}
			}
		} else {
			target = this.parse_word();
		}
		if (target === null) {
			throw ParseError("Expected target for redirect " + op);
		}
		return Redirect(op, target);
	}

	_parse_heredoc(fd, strip_tabs) {
		"Parse a here document <<DELIM ... DELIM.";
		this.skip_whitespace();
		let quoted = false;
		let delimiter_chars = [];
		while (!this.at_end() && !_is_metachar(this.peek())) {
			let ch = this.peek();
			if (ch === '"') {
				quoted = true;
				this.advance();
				while (!this.at_end() && this.peek() !== '"') {
					delimiter_chars.push(this.advance());
				}
				if (!this.at_end()) {
					this.advance();
				}
			} else if (ch === "'") {
				quoted = true;
				this.advance();
				while (!this.at_end() && this.peek() !== "'") {
					delimiter_chars.push(this.advance());
				}
				if (!this.at_end()) {
					this.advance();
				}
			} else if (ch === "\\") {
				this.advance();
				if (!this.at_end()) {
					let next_ch = this.peek();
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
				let depth = 1;
				while (!this.at_end() && depth > 0) {
					let c = this.peek();
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
		let delimiter = delimiter_chars.join("");
		let line_end = this.pos;
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
			this._pending_heredoc_end !== null &&
			this._pending_heredoc_end > line_end
		) {
			let content_start = this._pending_heredoc_end;
		} else if (line_end < this.length) {
			content_start = line_end + 1;
		} else {
			content_start = this.length;
		}
		let content_lines = [];
		let scan_pos = content_start;
		while (scan_pos < this.length) {
			let line_start = scan_pos;
			line_end = scan_pos;
			while (line_end < this.length && this.source[line_end] !== "\n") {
				line_end += 1;
			}
			let line = _substring(this.source, line_start, line_end);
			if (!quoted) {
				while (line.endsWith("\\") && line_end < this.length) {
					line = _substring(line, 0, line.length - 1);
					line_end += 1;
					let next_line_start = line_end;
					while (line_end < this.length && this.source[line_end] !== "\n") {
						line_end += 1;
					}
					line = line + _substring(this.source, next_line_start, line_end);
				}
			}
			let check_line = line;
			if (strip_tabs) {
				check_line = line.lstrip("\t");
			}
			if (check_line === delimiter) {
				break;
			}
			if (strip_tabs) {
				line = line.lstrip("\t");
			}
			content_lines.push(line + "\n");
			if (line_end < this.length) {
				scan_pos = line_end + 1;
			} else {
				scan_pos = this.length;
			}
		}
		let content = content_lines.join("");
		let heredoc_end = line_end;
		if (heredoc_end < this.length) {
			heredoc_end += 1;
		}
		if (this._pending_heredoc_end === null) {
			this._pending_heredoc_end = heredoc_end;
		} else {
			this._pending_heredoc_end = max(this._pending_heredoc_end, heredoc_end);
		}
		return HereDoc(delimiter, content, strip_tabs, quoted, fd);
	}

	parse_command() {
		"Parse a simple command (sequence of words and redirections).";
		let words = [];
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			if (this.at_end()) {
				break;
			}
			let ch = this.peek();
			if (_is_list_terminator(ch)) {
				break;
			}
			if (
				ch === "&" &&
				!(this.pos + 1 < this.length && this.source[this.pos + 1] === ">")
			) {
				break;
			}
			if (this.peek() === "}" && !words) {
				let next_pos = this.pos + 1;
				if (
					next_pos >= this.length ||
					_is_word_end_context(this.source[next_pos])
				) {
					break;
				}
			}
			let redirect = this.parse_redirect();
			if (redirect !== null) {
				redirects.push(redirect);
				continue;
			}
			let all_assignments = true;
			for (const w of words) {
				if (!this._is_assignment_word(w)) {
					all_assignments = false;
					break;
				}
			}
			let word = this.parse_word();
			if (word === null) {
				break;
			}
			words.push(word);
		}
		if (!words && !redirects) {
			return null;
		}
		return Command(words, redirects);
	}

	parse_subshell() {
		"Parse a subshell ( list ).";
		this.skip_whitespace();
		if (this.at_end() || this.peek() !== "(") {
			return null;
		}
		this.advance();
		let body = this.parse_list();
		if (body === null) {
			throw ParseError("Expected command in subshell");
		}
		this.skip_whitespace();
		if (this.at_end() || this.peek() !== ")") {
			throw ParseError("Expected ) to close subshell");
		}
		this.advance();
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		if (redirects) {
			return Subshell(body, redirects);
		} else {
			return Subshell(body, null);
		}
	}

	parse_arithmetic_command() {
		"Parse an arithmetic command (( expression )) with parsed internals.\n\n        Returns None if this is not an arithmetic command (e.g., nested subshells\n        like '( ( x ) )' that close with ') )' instead of '))').\n        ";
		this.skip_whitespace();
		if (
			this.at_end() ||
			this.peek() !== "(" ||
			this.pos + 1 >= this.length ||
			this.source[this.pos + 1] !== "("
		) {
			return null;
		}
		let saved_pos = this.pos;
		this.advance();
		this.advance();
		let content_start = this.pos;
		let depth = 1;
		while (!this.at_end() && depth > 0) {
			let c = this.peek();
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
		if (this.at_end() || depth !== 1) {
			this.pos = saved_pos;
			return null;
		}
		let content = _substring(this.source, content_start, this.pos);
		this.advance();
		this.advance();
		let expr = this._parse_arith_expr(content);
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return ArithmeticCommand(expr, redir_arg);
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
	parse_conditional_expr() {
		"Parse a conditional expression [[ expression ]].";
		this.skip_whitespace();
		if (
			this.at_end() ||
			this.peek() !== "[" ||
			this.pos + 1 >= this.length ||
			this.source[this.pos + 1] !== "["
		) {
			return null;
		}
		this.advance();
		this.advance();
		let body = this._parse_cond_or();
		while (!this.at_end() && _is_whitespace_no_newline(this.peek())) {
			this.advance();
		}
		if (
			this.at_end() ||
			this.peek() !== "]" ||
			this.pos + 1 >= this.length ||
			this.source[this.pos + 1] !== "]"
		) {
			throw ParseError("Expected ]] to close conditional expression");
		}
		this.advance();
		this.advance();
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return ConditionalExpr(body, redir_arg);
	}

	_cond_skip_whitespace() {
		"Skip whitespace inside [[ ]], including backslash-newline continuation.";
		while (!this.at_end()) {
			if (_is_whitespace_no_newline(this.peek())) {
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

	_cond_at_end() {
		"Check if we're at ]] (end of conditional).";
		return (
			this.at_end() ||
			(this.peek() === "]" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "]")
		);
	}

	_parse_cond_or() {
		"Parse: or_expr = and_expr (|| or_expr)?  (right-associative)";
		this._cond_skip_whitespace();
		let left = this._parse_cond_and();
		this._cond_skip_whitespace();
		if (
			!this._cond_at_end() &&
			this.peek() === "|" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "|"
		) {
			this.advance();
			this.advance();
			let right = this._parse_cond_or();
			return CondOr(left, right);
		}
		return left;
	}

	_parse_cond_and() {
		"Parse: and_expr = term (&& and_expr)?  (right-associative)";
		this._cond_skip_whitespace();
		let left = this._parse_cond_term();
		this._cond_skip_whitespace();
		if (
			!this._cond_at_end() &&
			this.peek() === "&" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "&"
		) {
			this.advance();
			this.advance();
			let right = this._parse_cond_and();
			return CondAnd(left, right);
		}
		return left;
	}

	_parse_cond_term() {
		"Parse: term = '!' term | '(' or_expr ')' | unary_test | binary_test | bare_word";
		this._cond_skip_whitespace();
		if (this._cond_at_end()) {
			throw ParseError("Unexpected end of conditional expression");
		}
		if (this.peek() === "!") {
			if (
				this.pos + 1 < this.length &&
				!_is_whitespace_no_newline(this.source[this.pos + 1])
			) {
			} else {
				this.advance();
				let operand = this._parse_cond_term();
				return CondNot(operand);
			}
		}
		if (this.peek() === "(") {
			this.advance();
			let inner = this._parse_cond_or();
			this._cond_skip_whitespace();
			if (this.at_end() || this.peek() !== ")") {
				throw ParseError("Expected ) in conditional expression");
			}
			this.advance();
			return CondParen(inner);
		}
		let word1 = this._parse_cond_word();
		if (word1 === null) {
			throw ParseError("Expected word in conditional expression");
		}
		this._cond_skip_whitespace();
		if (_is_cond_unary_op(word1.value)) {
			operand = this._parse_cond_word();
			if (operand === null) {
				throw ParseError("Expected operand after " + word1.value);
			}
			return UnaryTest(word1.value, operand);
		}
		if (
			!this._cond_at_end() &&
			this.peek() !== "&" && this.peek() !== "|" &&
			this.peek() !== ")"
		) {
			if (
				_is_redirect_char(this.peek()) &&
				!(this.pos + 1 < this.length && this.source[this.pos + 1] === "(")
			) {
				let op = this.advance();
				this._cond_skip_whitespace();
				let word2 = this._parse_cond_word();
				if (word2 === null) {
					throw ParseError("Expected operand after " + op);
				}
				return BinaryTest(op, word1, word2);
			}
			let saved_pos = this.pos;
			let op_word = this._parse_cond_word();
			if (op_word && _is_cond_binary_op(op_word.value)) {
				this._cond_skip_whitespace();
				if (op_word.value === "=~") {
					word2 = this._parse_cond_regex_word();
				} else {
					word2 = this._parse_cond_word();
				}
				if (word2 === null) {
					throw ParseError("Expected operand after " + op_word.value);
				}
				return BinaryTest(op_word.value, word1, word2);
			} else {
				this.pos = saved_pos;
			}
		}
		return UnaryTest("-n", word1);
	}

	_parse_cond_word() {
		"Parse a word inside [[ ]], handling expansions but stopping at conditional operators.";
		this._cond_skip_whitespace();
		if (this._cond_at_end()) {
			return null;
		}
		let c = this.peek();
		if (_is_paren(c)) {
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
		let start = this.pos;
		let chars = [];
		let parts = [];
		while (!this.at_end()) {
			let ch = this.peek();
			if (
				ch === "]" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "]"
			) {
				break;
			}
			if (_is_whitespace_no_newline(ch)) {
				break;
			}
			if (
				_is_redirect_char(ch) &&
				!(this.pos + 1 < this.length && this.source[this.pos + 1] === "(")
			) {
				break;
			}
			if (ch === "(") {
				if (chars && _is_extglob_prefix(chars[chars.length - 1])) {
					chars.push(this.advance());
					let depth = 1;
					while (!this.at_end() && depth > 0) {
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
				while (!this.at_end() && this.peek() !== "'") {
					chars.push(this.advance());
				}
				if (this.at_end()) {
					throw ParseError("Unterminated single quote");
				}
				chars.push(this.advance());
			} else if (ch === '"') {
				this.advance();
				chars.push('"');
				while (!this.at_end() && this.peek() !== '"') {
					c = this.peek();
					if (c === "\\" && this.pos + 1 < this.length) {
						let next_c = this.source[this.pos + 1];
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
							let arith_result = this._parse_arithmetic_expansion();
							let arith_node = arith_result[0];
							let arith_text = arith_result[1];
							if (arith_node) {
								parts.push(arith_node);
								chars.push(arith_text);
							} else {
								let cmdsub_result = this._parse_command_substitution();
								let cmdsub_node = cmdsub_result[0];
								let cmdsub_text = cmdsub_result[1];
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
							cmdsub_result = this._parse_command_substitution();
							cmdsub_node = cmdsub_result[0];
							cmdsub_text = cmdsub_result[1];
							if (cmdsub_node) {
								parts.push(cmdsub_node);
								chars.push(cmdsub_text);
							} else {
								chars.push(this.advance());
							}
						} else {
							let param_result = this._parse_param_expansion();
							let param_node = param_result[0];
							let param_text = param_result[1];
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
				if (this.at_end()) {
					throw ParseError("Unterminated double quote");
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
				arith_result = this._parse_arithmetic_expansion();
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
				cmdsub_result = this._parse_command_substitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					parts.push(cmdsub_node);
					chars.push(cmdsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "$") {
				param_result = this._parse_param_expansion();
				param_node = param_result[0];
				param_text = param_result[1];
				if (param_node) {
					parts.push(param_node);
					chars.push(param_text);
				} else {
					chars.push(this.advance());
				}
			} else if (
				_is_redirect_char(ch) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				let procsub_result = this._parse_process_substitution();
				let procsub_node = procsub_result[0];
				let procsub_text = procsub_result[1];
				if (procsub_node) {
					parts.push(procsub_node);
					chars.push(procsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "`") {
				cmdsub_result = this._parse_backtick_substitution();
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
		if (!chars) {
			return null;
		}
		let parts_arg = null;
		if (parts) {
			parts_arg = parts;
		}
		return Word(chars.join(""), parts_arg);
	}

	_parse_cond_regex_word() {
		"Parse a regex pattern word in [[ ]], where ( ) are regex grouping, not conditional grouping.";
		this._cond_skip_whitespace();
		if (this._cond_at_end()) {
			return null;
		}
		let start = this.pos;
		let chars = [];
		let parts = [];
		let paren_depth = 0;
		while (!this.at_end()) {
			let ch = this.peek();
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
				if (!this.at_end() && this.peek() === "^") {
					chars.push(this.advance());
				}
				if (!this.at_end() && this.peek() === "]") {
					chars.push(this.advance());
				}
				while (!this.at_end()) {
					let c = this.peek();
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
							!this.at_end() &&
							!(
								this.peek() === ":" &&
								this.pos + 1 < this.length &&
								this.source[this.pos + 1] === "]"
							)
						) {
							chars.push(this.advance());
						}
						if (!this.at_end()) {
							chars.push(this.advance());
							chars.push(this.advance());
						}
					} else {
						chars.push(this.advance());
					}
				}
				continue;
			}
			if (_is_whitespace(ch) && paren_depth === 0) {
				break;
			}
			if (_is_whitespace(ch) && paren_depth > 0) {
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
				while (!this.at_end() && this.peek() !== "'") {
					chars.push(this.advance());
				}
				if (this.at_end()) {
					throw ParseError("Unterminated single quote");
				}
				chars.push(this.advance());
				continue;
			}
			if (ch === '"') {
				this.advance();
				chars.push('"');
				while (!this.at_end() && this.peek() !== '"') {
					c = this.peek();
					if (c === "\\" && this.pos + 1 < this.length) {
						chars.push(this.advance());
						chars.push(this.advance());
					} else if (c === "$") {
						let param_result = this._parse_param_expansion();
						let param_node = param_result[0];
						let param_text = param_result[1];
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
				if (this.at_end()) {
					throw ParseError("Unterminated double quote");
				}
				chars.push(this.advance());
				continue;
			}
			if (ch === "$") {
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
					let cmdsub_result = this._parse_command_substitution();
					let cmdsub_node = cmdsub_result[0];
					let cmdsub_text = cmdsub_result[1];
					if (cmdsub_node) {
						parts.push(cmdsub_node);
						chars.push(cmdsub_text);
						continue;
					}
				}
				param_result = this._parse_param_expansion();
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
		if (!chars) {
			return null;
		}
		let parts_arg = null;
		if (parts) {
			parts_arg = parts;
		}
		return Word(chars.join(""), parts_arg);
	}

	parse_brace_group() {
		"Parse a brace group { list }.";
		this.skip_whitespace();
		if (this.at_end() || this.peek() !== "{") {
			return null;
		}
		if (
			this.pos + 1 < this.length &&
			!_is_whitespace(this.source[this.pos + 1])
		) {
			return null;
		}
		this.advance();
		this.skip_whitespace_and_newlines();
		let body = this.parse_list();
		if (body === null) {
			throw ParseError("Expected command in brace group");
		}
		this.skip_whitespace();
		if (this.at_end() || this.peek() !== "}") {
			throw ParseError("Expected } to close brace group");
		}
		this.advance();
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return BraceGroup(body, redir_arg);
	}

	parse_if() {
		"Parse an if statement: if list; then list [elif list; then list]* [else list] fi.";
		this.skip_whitespace();
		if (this.peek_word() !== "if") {
			return null;
		}
		this.consume_word("if");
		let condition = this.parse_list_until(new Set(["then"]));
		if (condition === null) {
			throw ParseError("Expected condition after 'if'");
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("then")) {
			throw ParseError("Expected 'then' after if condition");
		}
		let then_body = this.parse_list_until(new Set(["elif", "else", "fi"]));
		if (then_body === null) {
			throw ParseError("Expected commands after 'then'");
		}
		this.skip_whitespace_and_newlines();
		let next_word = this.peek_word();
		let else_body = null;
		if (next_word === "elif") {
			this.consume_word("elif");
			let elif_condition = this.parse_list_until(new Set(["then"]));
			if (elif_condition === null) {
				throw ParseError("Expected condition after 'elif'");
			}
			this.skip_whitespace_and_newlines();
			if (!this.consume_word("then")) {
				throw ParseError("Expected 'then' after elif condition");
			}
			let elif_then_body = this.parse_list_until(
				new Set(["elif", "else", "fi"]),
			);
			if (elif_then_body === null) {
				throw ParseError("Expected commands after 'then'");
			}
			this.skip_whitespace_and_newlines();
			let inner_next = this.peek_word();
			let inner_else = null;
			if (inner_next === "elif") {
				inner_else = this._parse_elif_chain();
			} else if (inner_next === "else") {
				this.consume_word("else");
				inner_else = this.parse_list_until(new Set(["fi"]));
				if (inner_else === null) {
					throw ParseError("Expected commands after 'else'");
				}
			}
			else_body = If(elif_condition, elif_then_body, inner_else);
		} else if (next_word === "else") {
			this.consume_word("else");
			else_body = this.parse_list_until(new Set(["fi"]));
			if (else_body === null) {
				throw ParseError("Expected commands after 'else'");
			}
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("fi")) {
			throw ParseError("Expected 'fi' to close if statement");
		}
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return If(condition, then_body, else_body, redir_arg);
	}

	_parse_elif_chain() {
		"Parse elif chain (after seeing 'elif' keyword).";
		this.consume_word("elif");
		let condition = this.parse_list_until(new Set(["then"]));
		if (condition === null) {
			throw ParseError("Expected condition after 'elif'");
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("then")) {
			throw ParseError("Expected 'then' after elif condition");
		}
		let then_body = this.parse_list_until(new Set(["elif", "else", "fi"]));
		if (then_body === null) {
			throw ParseError("Expected commands after 'then'");
		}
		this.skip_whitespace_and_newlines();
		let next_word = this.peek_word();
		let else_body = null;
		if (next_word === "elif") {
			else_body = this._parse_elif_chain();
		} else if (next_word === "else") {
			this.consume_word("else");
			else_body = this.parse_list_until(new Set(["fi"]));
			if (else_body === null) {
				throw ParseError("Expected commands after 'else'");
			}
		}
		return If(condition, then_body, else_body);
	}

	parse_while() {
		"Parse a while loop: while list; do list; done.";
		this.skip_whitespace();
		if (this.peek_word() !== "while") {
			return null;
		}
		this.consume_word("while");
		let condition = this.parse_list_until(new Set(["do"]));
		if (condition === null) {
			throw ParseError("Expected condition after 'while'");
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("do")) {
			throw ParseError("Expected 'do' after while condition");
		}
		let body = this.parse_list_until(new Set(["done"]));
		if (body === null) {
			throw ParseError("Expected commands after 'do'");
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("done")) {
			throw ParseError("Expected 'done' to close while loop");
		}
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return While(condition, body, redir_arg);
	}

	parse_until() {
		"Parse an until loop: until list; do list; done.";
		this.skip_whitespace();
		if (this.peek_word() !== "until") {
			return null;
		}
		this.consume_word("until");
		let condition = this.parse_list_until(new Set(["do"]));
		if (condition === null) {
			throw ParseError("Expected condition after 'until'");
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("do")) {
			throw ParseError("Expected 'do' after until condition");
		}
		let body = this.parse_list_until(new Set(["done"]));
		if (body === null) {
			throw ParseError("Expected commands after 'do'");
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("done")) {
			throw ParseError("Expected 'done' to close until loop");
		}
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return Until(condition, body, redir_arg);
	}

	parse_for() {
		"Parse a for loop: for name [in words]; do list; done or C-style for ((;;)).";
		this.skip_whitespace();
		if (this.peek_word() !== "for") {
			return null;
		}
		this.consume_word("for");
		this.skip_whitespace();
		if (
			this.peek() === "(" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			return this._parse_for_arith();
		}
		let var_name = this.peek_word();
		if (var_name === null) {
			throw ParseError("Expected variable name after 'for'");
		}
		this.consume_word(var_name);
		this.skip_whitespace();
		if (this.peek() === ";") {
			this.advance();
		}
		this.skip_whitespace_and_newlines();
		let words = null;
		if (this.peek_word() === "in") {
			this.consume_word("in");
			this.skip_whitespace_and_newlines();
			words = [];
			while (true) {
				this.skip_whitespace();
				if (this.at_end()) {
					break;
				}
				if (_is_semicolon_or_newline(this.peek())) {
					if (this.peek() === ";") {
						this.advance();
					}
					break;
				}
				if (this.peek_word() === "do") {
					break;
				}
				let word = this.parse_word();
				if (word === null) {
					break;
				}
				words.push(word);
			}
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("do")) {
			throw ParseError("Expected 'do' in for loop");
		}
		let body = this.parse_list_until(new Set(["done"]));
		if (body === null) {
			throw ParseError("Expected commands after 'do'");
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("done")) {
			throw ParseError("Expected 'done' to close for loop");
		}
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return For(var_name, words, body, redir_arg);
	}

	_parse_for_arith() {
		"Parse C-style for loop: for ((init; cond; incr)); do list; done.";
		this.advance();
		this.advance();
		let parts = [];
		let current = [];
		let paren_depth = 0;
		while (!this.at_end()) {
			let ch = this.peek();
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
					parts.push(current.join("").lstrip());
					this.advance();
					this.advance();
					break;
				} else {
					current.push(this.advance());
				}
			} else if (ch === ";" && paren_depth === 0) {
				parts.push(current.join("").lstrip());
				current = [];
				this.advance();
			} else {
				current.push(this.advance());
			}
		}
		if (parts.length !== 3) {
			throw ParseError("Expected three expressions in for ((;;))");
		}
		let init = parts[0];
		let cond = parts[1];
		let incr = parts[2];
		this.skip_whitespace();
		if (!this.at_end() && this.peek() === ";") {
			this.advance();
		}
		this.skip_whitespace_and_newlines();
		if (this.peek() === "{") {
			let brace = this.parse_brace_group();
			if (brace === null) {
				throw ParseError("Expected brace group body in for loop");
			}
			let body = brace.body;
		} else if (this.consume_word("do")) {
			body = this.parse_list_until(new Set(["done"]));
			if (body === null) {
				throw ParseError("Expected commands after 'do'");
			}
			this.skip_whitespace_and_newlines();
			if (!this.consume_word("done")) {
				throw ParseError("Expected 'done' to close for loop");
			}
		} else {
			throw ParseError("Expected 'do' or '{' in for loop");
		}
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return ForArith(init, cond, incr, body, redir_arg);
	}

	parse_select() {
		"Parse a select statement: select name [in words]; do list; done.";
		this.skip_whitespace();
		if (this.peek_word() !== "select") {
			return null;
		}
		this.consume_word("select");
		this.skip_whitespace();
		let var_name = this.peek_word();
		if (var_name === null) {
			throw ParseError("Expected variable name after 'select'");
		}
		this.consume_word(var_name);
		this.skip_whitespace();
		if (this.peek() === ";") {
			this.advance();
		}
		this.skip_whitespace_and_newlines();
		let words = null;
		if (this.peek_word() === "in") {
			this.consume_word("in");
			this.skip_whitespace_and_newlines();
			words = [];
			while (true) {
				this.skip_whitespace();
				if (this.at_end()) {
					break;
				}
				if (_is_semicolon_newline_brace(this.peek())) {
					if (this.peek() === ";") {
						this.advance();
					}
					break;
				}
				if (this.peek_word() === "do") {
					break;
				}
				let word = this.parse_word();
				if (word === null) {
					break;
				}
				words.push(word);
			}
		}
		this.skip_whitespace_and_newlines();
		if (this.peek() === "{") {
			let brace = this.parse_brace_group();
			if (brace === null) {
				throw ParseError("Expected brace group body in select");
			}
			let body = brace.body;
		} else if (this.consume_word("do")) {
			body = this.parse_list_until(new Set(["done"]));
			if (body === null) {
				throw ParseError("Expected commands after 'do'");
			}
			this.skip_whitespace_and_newlines();
			if (!this.consume_word("done")) {
				throw ParseError("Expected 'done' to close select");
			}
		} else {
			throw ParseError("Expected 'do' or '{' in select");
		}
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return Select(var_name, words, body, redir_arg);
	}

	_is_case_terminator() {
		"Check if we're at a case pattern terminator (;;, ;&, or ;;&).";
		if (this.at_end() || this.peek() !== ";") {
			return false;
		}
		if (this.pos + 1 >= this.length) {
			return false;
		}
		let next_ch = this.source[this.pos + 1];
		return _is_semicolon_or_amp(next_ch);
	}

	_consume_case_terminator() {
		"Consume and return case pattern terminator (;;, ;&, or ;;&).";
		if (this.at_end() || this.peek() !== ";") {
			return ";;";
		}
		this.advance();
		if (this.at_end()) {
			return ";;";
		}
		let ch = this.peek();
		if (ch === ";") {
			this.advance();
			if (!this.at_end() && this.peek() === "&") {
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

	parse_case() {
		"Parse a case statement: case word in pattern) commands;; ... esac.";
		this.skip_whitespace();
		if (this.peek_word() !== "case") {
			return null;
		}
		this.consume_word("case");
		this.skip_whitespace();
		let word = this.parse_word();
		if (word === null) {
			throw ParseError("Expected word after 'case'");
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("in")) {
			throw ParseError("Expected 'in' after case word");
		}
		this.skip_whitespace_and_newlines();
		let patterns = [];
		while (true) {
			this.skip_whitespace_and_newlines();
			if (this.peek_word() === "esac") {
				let saved = this.pos;
				this.skip_whitespace();
				while (
					!this.at_end() &&
					!_is_metachar(this.peek()) &&
					!_is_quote(this.peek())
				) {
					this.advance();
				}
				this.skip_whitespace();
				let is_pattern = false;
				if (!this.at_end() && this.peek() === ")") {
					this.advance();
					this.skip_whitespace();
					if (!this.at_end()) {
						let next_ch = this.peek();
						if (next_ch === ";") {
							is_pattern = true;
						} else if (!_is_newline_or_right_paren(next_ch)) {
							is_pattern = true;
						}
					}
				}
				this.pos = saved;
				if (!is_pattern) {
					break;
				}
			}
			this.skip_whitespace_and_newlines();
			if (!this.at_end() && this.peek() === "(") {
				this.advance();
				this.skip_whitespace_and_newlines();
			}
			let pattern_chars = [];
			let extglob_depth = 0;
			while (!this.at_end()) {
				let ch = this.peek();
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
						if (!this.at_end()) {
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
					if (!this.at_end() && this.peek() === "(") {
						pattern_chars.push(this.advance());
						let paren_depth = 2;
						while (!this.at_end() && paren_depth > 0) {
							let c = this.peek();
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
					_is_extglob_prefix(ch) &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === "("
				) {
					pattern_chars.push(this.advance());
					pattern_chars.push(this.advance());
					extglob_depth += 1;
				} else if (ch === "[") {
					let is_char_class = false;
					let scan_pos = this.pos + 1;
					let scan_depth = 0;
					let has_first_bracket_literal = false;
					if (
						scan_pos < this.length &&
						_is_caret_or_bang(this.source[scan_pos])
					) {
						scan_pos += 1;
					}
					if (scan_pos < this.length && this.source[scan_pos] === "]") {
						if (this.source.find("]", scan_pos + 1) !== -1) {
							scan_pos += 1;
							has_first_bracket_literal = true;
						}
					}
					while (scan_pos < this.length) {
						let sc = this.source[scan_pos];
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
						if (!this.at_end() && _is_caret_or_bang(this.peek())) {
							pattern_chars.push(this.advance());
						}
						if (
							has_first_bracket_literal &&
							!this.at_end() &&
							this.peek() === "]"
						) {
							pattern_chars.push(this.advance());
						}
						while (!this.at_end() && this.peek() !== "]") {
							pattern_chars.push(this.advance());
						}
						if (!this.at_end()) {
							pattern_chars.push(this.advance());
						}
					} else {
						pattern_chars.push(this.advance());
					}
				} else if (ch === "'") {
					pattern_chars.push(this.advance());
					while (!this.at_end() && this.peek() !== "'") {
						pattern_chars.push(this.advance());
					}
					if (!this.at_end()) {
						pattern_chars.push(this.advance());
					}
				} else if (ch === '"') {
					pattern_chars.push(this.advance());
					while (!this.at_end() && this.peek() !== '"') {
						if (this.peek() === "\\" && this.pos + 1 < this.length) {
							pattern_chars.push(this.advance());
						}
						pattern_chars.push(this.advance());
					}
					if (!this.at_end()) {
						pattern_chars.push(this.advance());
					}
				} else if (_is_whitespace(ch)) {
					if (extglob_depth > 0) {
						pattern_chars.push(this.advance());
					} else {
						this.advance();
					}
				} else {
					pattern_chars.push(this.advance());
				}
			}
			let pattern = pattern_chars.join("");
			if (!pattern) {
				throw ParseError("Expected pattern in case statement");
			}
			this.skip_whitespace();
			let body = null;
			let is_empty_body = this._is_case_terminator();
			if (!is_empty_body) {
				this.skip_whitespace_and_newlines();
				if (!this.at_end() && this.peek_word() !== "esac") {
					let is_at_terminator = this._is_case_terminator();
					if (!is_at_terminator) {
						body = this.parse_list_until(new Set(["esac"]));
						this.skip_whitespace();
					}
				}
			}
			let terminator = this._consume_case_terminator();
			this.skip_whitespace_and_newlines();
			patterns.push(CasePattern(pattern, body, terminator));
		}
		this.skip_whitespace_and_newlines();
		if (!this.consume_word("esac")) {
			throw ParseError("Expected 'esac' to close case statement");
		}
		let redirects = [];
		while (true) {
			this.skip_whitespace();
			let redirect = this.parse_redirect();
			if (redirect === null) {
				break;
			}
			redirects.push(redirect);
		}
		let redir_arg = null;
		if (redirects) {
			redir_arg = redirects;
		}
		return Case(word, patterns, redir_arg);
	}

	parse_coproc() {
		"Parse a coproc statement.\n\n        bash-oracle behavior:\n        - For compound commands (brace group, if, while, etc.), extract NAME if present\n        - For simple commands, don't extract NAME (treat everything as the command)\n        ";
		this.skip_whitespace();
		if (this.at_end()) {
			return null;
		}
		if (this.peek_word() !== "coproc") {
			return null;
		}
		this.consume_word("coproc");
		this.skip_whitespace();
		let name = null;
		let ch = null;
		if (!this.at_end()) {
			ch = this.peek();
		}
		if (ch === "{") {
			let body = this.parse_brace_group();
			if (body !== null) {
				return Coproc(body, name);
			}
		}
		if (ch === "(") {
			if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
				body = this.parse_arithmetic_command();
				if (body !== null) {
					return Coproc(body, name);
				}
			}
			body = this.parse_subshell();
			if (body !== null) {
				return Coproc(body, name);
			}
		}
		let next_word = this.peek_word();
		if (_is_compound_keyword(next_word)) {
			body = this.parse_compound_command();
			if (body !== null) {
				return Coproc(body, name);
			}
		}
		let word_start = this.pos;
		let potential_name = this.peek_word();
		if (potential_name) {
			while (
				!this.at_end() &&
				!_is_metachar(this.peek()) &&
				!_is_quote(this.peek())
			) {
				this.advance();
			}
			this.skip_whitespace();
			ch = null;
			if (!this.at_end()) {
				ch = this.peek();
			}
			next_word = this.peek_word();
			if (ch === "{") {
				name = potential_name;
				body = this.parse_brace_group();
				if (body !== null) {
					return Coproc(body, name);
				}
			} else if (ch === "(") {
				name = potential_name;
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
					body = this.parse_arithmetic_command();
				} else {
					body = this.parse_subshell();
				}
				if (body !== null) {
					return Coproc(body, name);
				}
			} else if (_is_compound_keyword(next_word)) {
				name = potential_name;
				body = this.parse_compound_command();
				if (body !== null) {
					return Coproc(body, name);
				}
			}
			this.pos = word_start;
		}
		body = this.parse_command();
		if (body !== null) {
			return Coproc(body, name);
		}
		throw ParseError("Expected command after coproc");
	}

	parse_function() {
		"Parse a function definition.\n\n        Forms:\n            name() compound_command           # POSIX form\n            function name compound_command    # bash form without parens\n            function name() compound_command  # bash form with parens\n        ";
		this.skip_whitespace();
		if (this.at_end()) {
			return null;
		}
		let saved_pos = this.pos;
		if (this.peek_word() === "function") {
			this.consume_word("function");
			this.skip_whitespace();
			let name = this.peek_word();
			if (name === null) {
				this.pos = saved_pos;
				return null;
			}
			this.consume_word(name);
			this.skip_whitespace();
			if (!this.at_end() && this.peek() === "(") {
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === ")") {
					this.advance();
					this.advance();
				}
			}
			this.skip_whitespace_and_newlines();
			let body = this._parse_compound_command();
			if (body === null) {
				throw ParseError("Expected function body");
			}
			return Function(name, body);
		}
		name = this.peek_word();
		if (name === null || _is_reserved_word(name)) {
			return null;
		}
		if (_str_contains(name, "=")) {
			return null;
		}
		this.skip_whitespace();
		let name_start = this.pos;
		while (
			!this.at_end() &&
			!_is_metachar(this.peek()) &&
			!_is_quote(this.peek()) &&
			!_is_paren(this.peek())
		) {
			this.advance();
		}
		name = _substring(this.source, name_start, this.pos);
		if (!name) {
			this.pos = saved_pos;
			return null;
		}
		this.skip_whitespace();
		if (this.at_end() || this.peek() !== "(") {
			this.pos = saved_pos;
			return null;
		}
		this.advance();
		this.skip_whitespace();
		if (this.at_end() || this.peek() !== ")") {
			this.pos = saved_pos;
			return null;
		}
		this.advance();
		this.skip_whitespace_and_newlines();
		body = this._parse_compound_command();
		if (body === null) {
			throw ParseError("Expected function body");
		}
		return Function(name, body);
	}

	_parse_compound_command() {
		"Parse any compound command (for function bodies, etc.).";
		let result = this.parse_brace_group();
		if (result) {
			return result;
		}
		result = this.parse_subshell();
		if (result) {
			return result;
		}
		result = this.parse_conditional_expr();
		if (result) {
			return result;
		}
		result = this.parse_if();
		if (result) {
			return result;
		}
		result = this.parse_while();
		if (result) {
			return result;
		}
		result = this.parse_until();
		if (result) {
			return result;
		}
		result = this.parse_for();
		if (result) {
			return result;
		}
		result = this.parse_case();
		if (result) {
			return result;
		}
		result = this.parse_select();
		if (result) {
			return result;
		}
		return null;
	}

	parse_list_until(stop_words) {
		"Parse a list that stops before certain reserved words.";
		this.skip_whitespace_and_newlines();
		if (stop_words.has(this.peek_word())) {
			return null;
		}
		let pipeline = this.parse_pipeline();
		if (pipeline === null) {
			return null;
		}
		let parts = [pipeline];
		while (true) {
			this.skip_whitespace();
			let has_newline = false;
			while (!this.at_end() && this.peek() === "\n") {
				has_newline = true;
				this.advance();
				if (
					this._pending_heredoc_end !== null &&
					this._pending_heredoc_end > this.pos
				) {
					this.pos = this._pending_heredoc_end;
					this._pending_heredoc_end = null;
				}
				this.skip_whitespace();
			}
			let op = this.parse_list_operator();
			if (op === null && has_newline) {
				if (
					!this.at_end() &&
					!stop_words.has(this.peek_word()) &&
					!_is_right_bracket(this.peek())
				) {
					op = "\n";
				}
			}
			if (op === null) {
				break;
			}
			if (op === "&") {
				parts.push(Operator(op));
				this.skip_whitespace_and_newlines();
				if (
					this.at_end() ||
					stop_words.has(this.peek_word()) ||
					_is_newline_or_right_bracket(this.peek())
				) {
					break;
				}
			}
			if (op === ";") {
				this.skip_whitespace_and_newlines();
				let at_case_terminator =
					this.peek() === ";" &&
					this.pos + 1 < this.length &&
					_is_semicolon_or_amp(this.source[this.pos + 1]);
				if (
					this.at_end() ||
					stop_words.has(this.peek_word()) ||
					_is_newline_or_right_bracket(this.peek()) ||
					at_case_terminator
				) {
					break;
				}
				parts.push(Operator(op));
			} else if (op !== "&") {
				parts.push(Operator(op));
			}
			this.skip_whitespace_and_newlines();
			if (stop_words.has(this.peek_word())) {
				break;
			}
			if (
				this.peek() === ";" &&
				this.pos + 1 < this.length &&
				_is_semicolon_or_amp(this.source[this.pos + 1])
			) {
				break;
			}
			pipeline = this.parse_pipeline();
			if (pipeline === null) {
				throw ParseError("Expected command after " + op);
			}
			parts.push(pipeline);
		}
		if (parts.length === 1) {
			return parts[0];
		}
		return List(parts);
	}

	parse_compound_command() {
		"Parse a compound command (subshell, brace group, if, loops, or simple command).";
		this.skip_whitespace();
		if (this.at_end()) {
			return null;
		}
		let ch = this.peek();
		if (
			ch === "(" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			let result = this.parse_arithmetic_command();
			if (result !== null) {
				return result;
			}
		}
		if (ch === "(") {
			return this.parse_subshell();
		}
		if (ch === "{") {
			result = this.parse_brace_group();
			if (result !== null) {
				return result;
			}
		}
		if (
			ch === "[" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "["
		) {
			return this.parse_conditional_expr();
		}
		let word = this.peek_word();
		if (word === "if") {
			return this.parse_if();
		}
		if (word === "while") {
			return this.parse_while();
		}
		if (word === "until") {
			return this.parse_until();
		}
		if (word === "for") {
			return this.parse_for();
		}
		if (word === "select") {
			return this.parse_select();
		}
		if (word === "case") {
			return this.parse_case();
		}
		if (word === "function") {
			return this.parse_function();
		}
		if (word === "coproc") {
			return this.parse_coproc();
		}
		let func = this.parse_function();
		if (func !== null) {
			return func;
		}
		return this.parse_command();
	}

	parse_pipeline() {
		"Parse a pipeline (commands separated by |), with optional time/negation prefix.";
		this.skip_whitespace();
		let prefix_order = null;
		let time_posix = false;
		if (this.peek_word() === "time") {
			this.consume_word("time");
			prefix_order = "time";
			this.skip_whitespace();
			if (!this.at_end() && this.peek() === "-") {
				let saved = this.pos;
				this.advance();
				if (!this.at_end() && this.peek() === "p") {
					this.advance();
					if (this.at_end() || _is_whitespace(this.peek())) {
						time_posix = true;
					} else {
						this.pos = saved;
					}
				} else {
					this.pos = saved;
				}
			}
			this.skip_whitespace();
			if (!this.at_end() && _starts_with_at(this.source, this.pos, "--")) {
				if (
					this.pos + 2 >= this.length ||
					_is_whitespace(this.source[this.pos + 2])
				) {
					this.advance();
					this.advance();
					time_posix = true;
					this.skip_whitespace();
				}
			}
			while (this.peek_word() === "time") {
				this.consume_word("time");
				this.skip_whitespace();
				if (!this.at_end() && this.peek() === "-") {
					saved = this.pos;
					this.advance();
					if (!this.at_end() && this.peek() === "p") {
						this.advance();
						if (this.at_end() || _is_whitespace(this.peek())) {
							time_posix = true;
						} else {
							this.pos = saved;
						}
					} else {
						this.pos = saved;
					}
				}
				this.skip_whitespace();
			}
			if (!this.at_end() && this.peek() === "!") {
				if (
					this.pos + 1 >= this.length ||
					_is_whitespace(this.source[this.pos + 1])
				) {
					this.advance();
					prefix_order = "time_negation";
					this.skip_whitespace();
				}
			}
		} else if (!this.at_end() && this.peek() === "!") {
			if (
				this.pos + 1 >= this.length ||
				_is_whitespace(this.source[this.pos + 1])
			) {
				this.advance();
				this.skip_whitespace();
				let inner = this.parse_pipeline();
				if (inner !== null && inner.kind === "negation") {
					if (inner.pipeline !== null) {
						return inner.pipeline;
					} else {
						return Command([]);
					}
				}
				return Negation(inner);
			}
		}
		let result = this._parse_simple_pipeline();
		if (prefix_order === "time") {
			result = Time(result, time_posix);
		} else if (prefix_order === "negation") {
			result = Negation(result);
		} else if (prefix_order === "time_negation") {
			result = Time(result, time_posix);
			result = Negation(result);
		} else if (prefix_order === "negation_time") {
			result = Time(result, time_posix);
			result = Negation(result);
		} else if (result === null) {
			return null;
		}
		return result;
	}

	_parse_simple_pipeline() {
		"Parse a simple pipeline (commands separated by | or |&) without time/negation.";
		let cmd = this.parse_compound_command();
		if (cmd === null) {
			return null;
		}
		let commands = [cmd];
		while (true) {
			this.skip_whitespace();
			if (this.at_end() || this.peek() !== "|") {
				break;
			}
			if (this.pos + 1 < this.length && this.source[this.pos + 1] === "|") {
				break;
			}
			this.advance();
			let is_pipe_both = false;
			if (!this.at_end() && this.peek() === "&") {
				this.advance();
				is_pipe_both = true;
			}
			this.skip_whitespace_and_newlines();
			if (is_pipe_both) {
				commands.push(PipeBoth());
			}
			cmd = this.parse_compound_command();
			if (cmd === null) {
				throw ParseError("Expected command after |");
			}
			commands.push(cmd);
		}
		if (commands.length === 1) {
			return commands[0];
		}
		return Pipeline(commands);
	}

	parse_list_operator() {
		"Parse a list operator (&&, ||, ;, &).";
		this.skip_whitespace();
		if (this.at_end()) {
			return null;
		}
		let ch = this.peek();
		if (ch === "&") {
			if (this.pos + 1 < this.length && this.source[this.pos + 1] === ">") {
				return null;
			}
			this.advance();
			if (!this.at_end() && this.peek() === "&") {
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
				_is_semicolon_or_amp(this.source[this.pos + 1])
			) {
				return null;
			}
			this.advance();
			return ";";
		}
		return null;
	}

	parse_list(newline_as_separator) {
		"Parse a command list (pipelines separated by &&, ||, ;, &).\n\n        Args:\n            newline_as_separator: If True, treat newlines as implicit semicolons.\n                If False, stop at newlines (for top-level parsing).\n        ";
		if (newline_as_separator) {
			this.skip_whitespace_and_newlines();
		} else {
			this.skip_whitespace();
		}
		let pipeline = this.parse_pipeline();
		if (pipeline === null) {
			return null;
		}
		let parts = [pipeline];
		while (true) {
			this.skip_whitespace();
			let has_newline = false;
			while (!this.at_end() && this.peek() === "\n") {
				has_newline = true;
				if (!newline_as_separator) {
					break;
				}
				this.advance();
				if (
					this._pending_heredoc_end !== null &&
					this._pending_heredoc_end > this.pos
				) {
					this.pos = this._pending_heredoc_end;
					this._pending_heredoc_end = null;
				}
				this.skip_whitespace();
			}
			if (has_newline && !newline_as_separator) {
				break;
			}
			let op = this.parse_list_operator();
			if (op === null && has_newline) {
				if (!this.at_end() && !_is_right_bracket(this.peek())) {
					op = "\n";
				}
			}
			if (op === null) {
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
				parts.push(Operator(op));
			}
			if (op === "&") {
				this.skip_whitespace();
				if (this.at_end() || _is_right_bracket(this.peek())) {
					break;
				}
				if (this.peek() === "\n") {
					if (newline_as_separator) {
						this.skip_whitespace_and_newlines();
						if (this.at_end() || _is_right_bracket(this.peek())) {
							break;
						}
					} else {
						break;
					}
				}
			}
			if (op === ";") {
				this.skip_whitespace();
				if (this.at_end() || _is_right_bracket(this.peek())) {
					break;
				}
				if (this.peek() === "\n") {
					continue;
				}
			}
			if (op === "&&" || op === "||") {
				this.skip_whitespace_and_newlines();
			}
			pipeline = this.parse_pipeline();
			if (pipeline === null) {
				throw ParseError("Expected command after " + op);
			}
			parts.push(pipeline);
		}
		if (parts.length === 1) {
			return parts[0];
		}
		return List(parts);
	}

	parse_comment() {
		"Parse a comment (# to end of line).";
		if (this.at_end() || this.peek() !== "#") {
			return null;
		}
		let start = this.pos;
		while (!this.at_end() && this.peek() !== "\n") {
			this.advance();
		}
		let text = _substring(this.source, start, this.pos);
		return Comment(text);
	}

	parse() {
		"Parse the entire input.";
		let source = this.source.strip();
		if (!source) {
			return [Empty()];
		}
		let results = [];
		while (true) {
			this.skip_whitespace();
			while (!this.at_end() && this.peek() === "\n") {
				this.advance();
			}
			if (this.at_end()) {
				break;
			}
			let comment = this.parse_comment();
			if (!comment) {
				break;
			}
		}
		while (!this.at_end()) {
			let result = this.parse_list();
			if (result !== null) {
				results.push(result);
			}
			this.skip_whitespace();
			let found_newline = false;
			while (!this.at_end() && this.peek() === "\n") {
				found_newline = true;
				this.advance();
				if (
					this._pending_heredoc_end !== null &&
					this._pending_heredoc_end > this.pos
				) {
					this.pos = this._pending_heredoc_end;
					this._pending_heredoc_end = null;
				}
				this.skip_whitespace();
			}
			if (!found_newline && !this.at_end()) {
				throw ParseError("Parser not fully implemented yet");
			}
		}
		if (!results) {
			return [Empty()];
		}
		return results;
	}
}

function parse(source) {
	"\n    Parse bash source code and return a list of AST nodes.\n\n    Args:\n        source: The bash source code to parse.\n\n    Returns:\n        A list of AST nodes representing the parsed code.\n\n    Raises:\n        ParseError: If the source code cannot be parsed.\n    ";
	let parser = Parser(source);
	return parser.parse();
}
