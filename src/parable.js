/**
 * Parable.js - A recursive descent parser for bash.
 *
 * MIT License - https://github.com/ldayton/Parable
 *
 * import { parse } from './parable.js';
 * const ast = parse("ps aux | grep python | awk '{print $2}'")
 */

class ParseError extends Error {
	constructor(message, pos, line) {
		super();
		this.message = message;
		this.pos = pos;
		this.line = line;
	}

	_formatMessage() {
		if (this.line != null && this.pos != null) {
			return `Parse error at line ${this.line}, position ${this.pos}: ${this.message}`;
		} else if (this.pos != null) {
			return `Parse error at position ${this.pos}: ${this.message}`;
		}
		return `Parse error: ${this.message}`;
	}
}

function _isHexDigit(c) {
	return (
		(c >= "0" && c <= "9") || (c >= "a" && c <= "f") || (c >= "A" && c <= "F")
	);
}

function _isOctalDigit(c) {
	return c >= "0" && c <= "7";
}

// ANSI-C escape sequence byte values
const ANSI_C_ESCAPES = {
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
function _getAnsiEscape(c) {
	return ANSI_C_ESCAPES[c] ?? -1;
}

function _isWhitespace(c) {
	return c === " " || c === "\t" || c === "\n";
}

function _isWhitespaceNoNewline(c) {
	return c === " " || c === "\t";
}

function _startsWithAt(s, pos, prefix) {
	return s.startsWith(prefix, pos);
}

function _countConsecutiveDollarsBefore(s, pos) {
	let bs_count, count, j, k;
	count = 0;
	k = pos - 1;
	while (k >= 0 && s[k] === "$") {
		// Check if this dollar is escaped by counting preceding backslashes
		bs_count = 0;
		j = k - 1;
		while (j >= 0 && s[j] === "\\") {
			bs_count += 1;
			j -= 1;
		}
		if (bs_count % 2 === 1) {
			// Odd number of backslashes means the dollar is escaped, stop counting
			break;
		}
		count += 1;
		k -= 1;
	}
	return count;
}

function _stripLineContinuationsCommentAware(text) {
	let c,
		i,
		in_comment,
		in_double,
		in_single,
		j,
		num_preceding_backslashes,
		result;
	result = [];
	i = 0;
	in_comment = false;
	in_single = false;
	in_double = false;
	while (i < text.length) {
		c = text[i];
		if (c === "\\" && i + 1 < text.length && text[i + 1] === "\n") {
			// Count preceding backslashes to determine if this backslash is escaped
			num_preceding_backslashes = 0;
			j = i - 1;
			while (j >= 0 && text[j] === "\\") {
				num_preceding_backslashes += 1;
				j -= 1;
			}
			// If there's an even number of preceding backslashes (including 0),
			// this backslash escapes the newline (line continuation)
			// If odd, this backslash is itself escaped
			if (num_preceding_backslashes % 2 === 0) {
				// Line continuation
				if (in_comment) {
					result.push("\n");
				}
				i += 2;
				in_comment = false;
				continue;
			}
		}
		// else: backslash is escaped, don't treat as line continuation, fall through
		if (c === "\n") {
			in_comment = false;
			result.push(c);
			i += 1;
			continue;
		}
		if (c === "'" && !in_double && !in_comment) {
			in_single = !in_single;
		} else if (c === '"' && !in_single && !in_comment) {
			in_double = !in_double;
		} else if (c === "#" && !in_single && !in_comment) {
			in_comment = true;
		}
		result.push(c);
		i += 1;
	}
	return result.join("");
}

function _appendRedirects(base, redirects) {
	let parts, r;
	if (redirects && redirects.length) {
		parts = [];
		for (r of redirects) {
			parts.push(r.toSexp());
		}
		return `${base} ${parts.join(" ")}`;
	}
	return base;
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
		if (parts == null) {
			parts = [];
		}
		this.parts = parts;
	}

	toSexp() {
		let escaped, value;
		value = this.value;
		// Expand ALL $'...' ANSI-C quotes (handles escapes and strips $)
		value = this._expandAllAnsiCQuotes(value);
		// Strip $ from locale strings $"..." (quote-aware)
		value = this._stripLocaleStringDollars(value);
		// Normalize whitespace in array assignments: name=(a  b\tc) -> name=(a b c)
		value = this._normalizeArrayWhitespace(value);
		// Format command substitutions with bash-oracle pretty-printing (before escaping)
		value = this._formatCommandSubstitutions(value);
		// Convert newlines at param expansion boundaries to spaces (bash behavior)
		value = this._normalizeParamExpansionNewlines(value);
		// Strip line continuations (backslash-newline) from arithmetic expressions
		value = this._stripArithLineContinuations(value);
		// Double CTLESC (0x01) bytes - bash-oracle uses this for quoting control chars
		// Exception: don't double when preceded by odd number of backslashes (escaped)
		value = this._doubleCtlescSmart(value);
		// Prefix DEL (0x7f) with CTLESC - bash-oracle quotes this control char
		value = value.replaceAll("", "");
		// Escape backslashes for s-expression output
		value = value.replaceAll("\\", "\\\\");
		// Double trailing escaped backslash (bash-oracle outputs \\\\ for trailing \)
		if (value.endsWith("\\\\") && !value.endsWith("\\\\\\\\")) {
			value = `${value}\\\\`;
		}
		// Escape double quotes, newlines, and tabs
		escaped = value
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n")
			.replaceAll("\t", "\\t");
		return `(word "${escaped}")`;
	}

	_appendWithCtlesc(result, byte_val) {
		result.push(byte_val);
	}

	_doubleCtlescSmart(value) {
		let bs_count, c, in_double, in_single, j, result;
		result = [];
		in_single = false;
		in_double = false;
		for (c of value) {
			// Track quote state
			if (c === "'" && !in_double) {
				in_single = !in_single;
			} else if (c === '"' && !in_single) {
				in_double = !in_double;
			}
			result.push(c);
			if (c === "") {
				// Only count backslashes in double-quoted context (where they escape)
				// In single quotes, backslashes are literal, so always double CTLESC
				if (in_double) {
					bs_count = 0;
					for (j = result.length - 2; j > -1; j--) {
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
					// Outside double quotes (including single quotes): always double
					result.push("");
				}
			}
		}
		return result.join("");
	}

	_normalizeParamExpansionNewlines(value) {
		let c, ch, depth, had_leading_newline, i, in_double, in_single, result;
		result = [];
		i = 0;
		in_single = false;
		in_double = false;
		while (i < value.length) {
			c = value[i];
			// Track quote state
			if (c === "'" && !in_double) {
				in_single = !in_single;
				result.push(c);
				i += 1;
			} else if (c === '"' && !in_single) {
				in_double = !in_double;
				result.push(c);
				i += 1;
			} else if (
				c === "$" &&
				i + 1 < value.length &&
				value[i + 1] === "{" &&
				!in_single
			) {
				// Check for ${ param expansion
				result.push("$");
				result.push("{");
				i += 2;
				// Check for leading newline and convert to space
				had_leading_newline = i < value.length && value[i] === "\n";
				if (had_leading_newline) {
					result.push(" ");
					i += 1;
				}
				// Find matching close brace and process content
				depth = 1;
				while (i < value.length && depth > 0) {
					ch = value[i];
					if (ch === "\\" && i + 1 < value.length && !in_single) {
						if (value[i + 1] === "\n") {
							i += 2;
							continue;
						}
						result.push(ch);
						result.push(value[i + 1]);
						i += 2;
						continue;
					}
					if (ch === "'" && !in_double) {
						in_single = !in_single;
					} else if (ch === '"' && !in_single) {
						in_double = !in_double;
					} else if (!in_single && !in_double) {
						if (ch === "{") {
							depth += 1;
						} else if (ch === "}") {
							depth -= 1;
							if (depth === 0) {
								// Add trailing space if we had leading newline
								if (had_leading_newline) {
									result.push(" ");
								}
								result.push(ch);
								i += 1;
								break;
							}
						}
					}
					result.push(ch);
					i += 1;
				}
			} else {
				result.push(c);
				i += 1;
			}
		}
		return result.join("");
	}

	_expandAnsiCEscapes(value) {
		let byte_val,
			c,
			codepoint,
			ctrl_char,
			ctrl_val,
			hex_str,
			i,
			inner,
			j,
			result,
			simple;
		if (!(value.startsWith("'") && value.endsWith("'"))) {
			return value;
		}
		inner = value.slice(1, value.length - 1);
		result = [];
		i = 0;
		while (i < inner.length) {
			if (inner[i] === "\\" && i + 1 < inner.length) {
				c = inner[i + 1];
				// Check simple escapes first
				simple = _getAnsiEscape(c);
				if (simple >= 0) {
					result.push(simple);
					i += 2;
				} else if (c === "'") {
					// bash-oracle outputs \' as '\'' (shell quoting trick)
					result.push(...[39, 92, 39, 39]);
					i += 2;
				} else if (c === "x") {
					// Check for \x{...} brace syntax (bash 5.3+)
					if (i + 2 < inner.length && inner[i + 2] === "{") {
						// Find closing brace or end of hex digits
						j = i + 3;
						while (j < inner.length && _isHexDigit(inner[j])) {
							j += 1;
						}
						hex_str = inner.slice(i + 3, j);
						if (j < inner.length && inner[j] === "}") {
							j += 1;
						}
						// If no hex digits, treat as NUL (truncates)
						if (!hex_str) {
							return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
						}
						byte_val = parseInt(hex_str, 16) & 255;
						if (byte_val === 0) {
							return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
						}
						this._appendWithCtlesc(result, byte_val);
						i = j;
					} else {
						// Hex escape \xHH (1-2 hex digits) - raw byte
						j = i + 2;
						while (j < inner.length && j < i + 4 && _isHexDigit(inner[j])) {
							j += 1;
						}
						if (j > i + 2) {
							byte_val = parseInt(inner.slice(i + 2, j), 16);
							if (byte_val === 0) {
								// NUL truncates string
								return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
							}
							this._appendWithCtlesc(result, byte_val);
							i = j;
						} else {
							result.push(inner[i].charCodeAt(0));
							i += 1;
						}
					}
				} else if (c === "u") {
					// Unicode escape \uHHHH (1-4 hex digits) - encode as UTF-8
					j = i + 2;
					while (j < inner.length && j < i + 6 && _isHexDigit(inner[j])) {
						j += 1;
					}
					if (j > i + 2) {
						codepoint = parseInt(inner.slice(i + 2, j), 16);
						if (codepoint === 0) {
							// NUL truncates string
							return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
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
					// Unicode escape \UHHHHHHHH (1-8 hex digits) - encode as UTF-8
					j = i + 2;
					while (j < inner.length && j < i + 10 && _isHexDigit(inner[j])) {
						j += 1;
					}
					if (j > i + 2) {
						codepoint = parseInt(inner.slice(i + 2, j), 16);
						if (codepoint === 0) {
							// NUL truncates string
							return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
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
					// Control character \cX - mask with 0x1f
					if (i + 3 <= inner.length) {
						ctrl_char = inner[i + 2];
						ctrl_val = ctrl_char.charCodeAt(0) & 31;
						if (ctrl_val === 0) {
							// NUL truncates string
							return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
						}
						this._appendWithCtlesc(result, ctrl_val);
						i += 3;
					} else {
						result.push(inner[i].charCodeAt(0));
						i += 1;
					}
				} else if (c === "0") {
					// Nul or octal \0 or \0NN (up to 3 digits total)
					j = i + 2;
					while (j < inner.length && j < i + 4 && _isOctalDigit(inner[j])) {
						j += 1;
					}
					if (j > i + 2) {
						byte_val = parseInt(inner.slice(i + 1, j), 8) & 255;
						if (byte_val === 0) {
							// NUL truncates string
							return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
						}
						this._appendWithCtlesc(result, byte_val);
						i = j;
					} else {
						// Just \0 - NUL truncates string
						return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
					}
				} else if (c >= "1" && c <= "7") {
					// Octal escape \NNN (1-3 digits) - raw byte, wraps at 256
					j = i + 1;
					while (j < inner.length && j < i + 4 && _isOctalDigit(inner[j])) {
						j += 1;
					}
					byte_val = parseInt(inner.slice(i + 1, j), 8) & 255;
					if (byte_val === 0) {
						// NUL truncates string
						return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
					}
					this._appendWithCtlesc(result, byte_val);
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
		return `'${new TextDecoder().decode(new Uint8Array(result))}'`;
	}

	_expandAllAnsiCQuotes(value) {
		let after_brace,
			ansi_str,
			brace_depth,
			c,
			ch,
			effective_in_dquote,
			expanded,
			i,
			in_backtick,
			in_double_quote,
			in_pattern,
			in_single_quote,
			inner,
			is_ansi_c,
			j,
			last_brace_idx,
			op,
			op_start,
			outer_in_dquote,
			quote_stack,
			result,
			result_str,
			var_name_len;
		result = [];
		i = 0;
		in_single_quote = false;
		in_double_quote = false;
		in_backtick = false;
		brace_depth = 0;
		quote_stack = [];
		while (i < value.length) {
			ch = value[i];
			// Track backtick context - don't expand $'...' inside backticks
			if (ch === "`" && !in_single_quote) {
				in_backtick = !in_backtick;
				result.push(ch);
				i += 1;
				continue;
			}
			// Inside backticks, just copy everything as-is
			if (in_backtick) {
				if (ch === "\\" && i + 1 < value.length) {
					result.push(ch);
					result.push(value[i + 1]);
					i += 2;
				} else {
					result.push(ch);
					i += 1;
				}
				continue;
			}
			// Track brace depth for parameter expansions
			if (!in_single_quote) {
				if (_startsWithAt(value, i, "${")) {
					brace_depth += 1;
					quote_stack.push([in_single_quote, in_double_quote]);
					in_single_quote = false;
					in_double_quote = false;
					result.push("${");
					i += 2;
					continue;
				} else if (ch === "}" && brace_depth > 0 && !in_double_quote) {
					brace_depth -= 1;
					result.push(ch);
					if (quote_stack) {
						[in_single_quote, in_double_quote] = quote_stack.pop();
					}
					i += 1;
					continue;
				}
			}
			// Double quotes inside ${...} still protect $'...' from expansion
			effective_in_dquote = in_double_quote;
			// Track quote state to avoid matching $' inside regular quotes
			if (ch === "'" && !effective_in_dquote) {
				// Toggle quote state unless this is $' that will be expanded as ANSI-C
				is_ansi_c =
					!in_single_quote &&
					i > 0 &&
					value[i - 1] === "$" &&
					_countConsecutiveDollarsBefore(value, i - 1) % 2 === 0;
				if (!is_ansi_c) {
					in_single_quote = !in_single_quote;
				}
				result.push(ch);
				i += 1;
			} else if (ch === '"' && !in_single_quote) {
				in_double_quote = !in_double_quote;
				result.push(ch);
				i += 1;
			} else if (ch === "\\" && i + 1 < value.length && !in_single_quote) {
				// Backslash escape - skip both chars to avoid misinterpreting \" or \'
				result.push(ch);
				result.push(value[i + 1]);
				i += 2;
			} else if (
				_startsWithAt(value, i, "$'") &&
				!in_single_quote &&
				!effective_in_dquote &&
				_countConsecutiveDollarsBefore(value, i) % 2 === 0
			) {
				// ANSI-C quoted string - find matching closing quote
				j = i + 2;
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
				// Extract and expand the $'...' sequence
				ansi_str = value.slice(i, j);
				// Strip the $ and expand escapes
				expanded = this._expandAnsiCEscapes(ansi_str.slice(1, ansi_str.length));
				// Inside ${...} that's itself in double quotes, check if quotes should be stripped
				outer_in_dquote =
					quote_stack.length > 0
						? quote_stack[quote_stack.length - 1][1]
						: false;
				if (
					brace_depth > 0 &&
					outer_in_dquote &&
					expanded.startsWith("'") &&
					expanded.endsWith("'")
				) {
					inner = expanded.slice(1, expanded.length - 1);
					// Only strip if non-empty and no CTLESC
					if (inner && inner.indexOf("") === -1) {
						// Check if we're in a pattern context (%, %%, #, ##, /, //)
						// For pattern operators, keep quotes; for others (like ~), strip them
						result_str = result.join("");
						in_pattern = false;
						// Find the last ${
						last_brace_idx = result_str.lastIndexOf("${");
						if (last_brace_idx >= 0) {
							// Get the content after ${
							after_brace = result_str.slice(last_brace_idx + 2);
							// Parse variable name to find where operator starts
							var_name_len = 0;
							if (after_brace) {
								// Special parameters like $, @, *, etc.
								if ("@*#?-$!0123456789_".includes(after_brace[0])) {
									var_name_len = 1;
								} else if (
									/^[a-zA-Z]$/.test(after_brace[0]) ||
									after_brace[0] === "_"
								) {
									// Regular variable names
									while (var_name_len < after_brace.length) {
										c = after_brace[var_name_len];
										if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
											break;
										}
										var_name_len += 1;
									}
								}
							}
							// Check if operator immediately after variable name is a pattern operator
							if (var_name_len > 0 && var_name_len < after_brace.length) {
								op_start = after_brace.slice(var_name_len);
								// Check if it starts with a pattern operator
								for (op of ["//", "%%", "##", "/", "%", "#"]) {
									if (op_start.startsWith(op)) {
										in_pattern = true;
										break;
									}
								}
							}
						}
						if (!in_pattern) {
							expanded = inner;
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

	_stripLocaleStringDollars(value) {
		let brace_depth,
			brace_in_double_quote,
			bracket_depth,
			bracket_in_double_quote,
			ch,
			dollar_count,
			i,
			in_double_quote,
			in_single_quote,
			result;
		result = [];
		i = 0;
		in_single_quote = false;
		in_double_quote = false;
		brace_depth = 0;
		bracket_depth = 0;
		// Track quote state inside brace expansions separately
		brace_in_double_quote = false;
		bracket_in_double_quote = false;
		while (i < value.length) {
			ch = value[i];
			if (ch === "\\" && i + 1 < value.length) {
				// Escape - copy both chars
				result.push(ch);
				result.push(value[i + 1]);
				i += 2;
			} else if (_startsWithAt(value, i, "${") && !in_single_quote) {
				brace_depth += 1;
				brace_in_double_quote = false;
				result.push("$");
				result.push("{");
				i += 2;
			} else if (
				ch === "}" &&
				brace_depth > 0 &&
				!in_single_quote &&
				!brace_in_double_quote
			) {
				brace_depth -= 1;
				result.push(ch);
				i += 1;
			} else if (
				ch === "[" &&
				brace_depth > 0 &&
				!in_single_quote &&
				!brace_in_double_quote
			) {
				// Start of subscript inside brace expansion
				bracket_depth += 1;
				bracket_in_double_quote = false;
				result.push(ch);
				i += 1;
			} else if (
				ch === "]" &&
				bracket_depth > 0 &&
				!in_single_quote &&
				!bracket_in_double_quote
			) {
				// End of subscript
				bracket_depth -= 1;
				result.push(ch);
				i += 1;
			} else if (ch === "'" && !in_double_quote && brace_depth === 0) {
				in_single_quote = !in_single_quote;
				result.push(ch);
				i += 1;
			} else if (ch === '"' && !in_single_quote && brace_depth === 0) {
				in_double_quote = !in_double_quote;
				result.push(ch);
				i += 1;
			} else if (ch === '"' && !in_single_quote && bracket_depth > 0) {
				// Toggle quote state inside bracket (subscript)
				bracket_in_double_quote = !bracket_in_double_quote;
				result.push(ch);
				i += 1;
			} else if (ch === '"' && !in_single_quote && brace_depth > 0) {
				// Toggle quote state inside brace expansion
				brace_in_double_quote = !brace_in_double_quote;
				result.push(ch);
				i += 1;
			} else if (
				_startsWithAt(value, i, '$"') &&
				!in_single_quote &&
				(brace_depth > 0 || bracket_depth > 0 || !in_double_quote) &&
				!brace_in_double_quote &&
				!bracket_in_double_quote
			) {
				// Count consecutive $ chars ending at i to check for $$ (PID param)
				dollar_count = 1 + _countConsecutiveDollarsBefore(value, i);
				if (dollar_count % 2 === 1) {
					// Odd count: locale string $"..." - strip the $ and enter double quote
					result.push('"');
					if (bracket_depth > 0) {
						bracket_in_double_quote = true;
					} else if (brace_depth > 0) {
						brace_in_double_quote = true;
					} else {
						in_double_quote = true;
					}
					i += 2;
				} else {
					// Even count: this $ is part of $$ (PID), just append it
					result.push(ch);
					i += 1;
				}
			} else {
				result.push(ch);
				i += 1;
			}
		}
		return result.join("");
	}

	_normalizeArrayWhitespace(value) {
		let close_paren_pos,
			depth,
			i,
			inner,
			open_paren_pos,
			prefix,
			result,
			suffix;
		// Match array assignment pattern: name=( or name+=( or name[sub]=( or name[sub]+=(
		// Parse identifier: starts with letter/underscore, then alnum/underscore
		i = 0;
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
		// Optional subscript(s): [...]
		while (i < value.length && value[i] === "[") {
			depth = 1;
			i += 1;
			while (i < value.length && depth > 0) {
				if (value[i] === "[") {
					depth += 1;
				} else if (value[i] === "]") {
					depth -= 1;
				}
				i += 1;
			}
			if (depth !== 0) {
				return value;
			}
		}
		// Optional + for +=
		if (i < value.length && value[i] === "+") {
			i += 1;
		}
		// Must have =(
		if (!(i + 1 < value.length && value[i] === "=" && value[i + 1] === "(")) {
			return value;
		}
		prefix = value.slice(0, i + 1);
		open_paren_pos = i + 1;
		// Find matching closing paren
		if (value.endsWith(")")) {
			close_paren_pos = value.length - 1;
		} else {
			close_paren_pos = this._findMatchingParen(value, open_paren_pos);
			if (close_paren_pos < 0) {
				return value;
			}
		}
		// Extract content inside parentheses
		inner = value.slice(open_paren_pos + 1, close_paren_pos);
		suffix = value.slice(close_paren_pos + 1, value.length);
		result = this._normalizeArrayInner(inner);
		return `${prefix}(${result})${suffix}`;
	}

	_findMatchingParen(value, open_pos) {
		let ch, depth, i;
		if (open_pos >= value.length || value[open_pos] !== "(") {
			return -1;
		}
		i = open_pos + 1;
		depth = 1;
		while (i < value.length && depth > 0) {
			ch = value[i];
			if (ch === "'") {
				i += 1;
				while (i < value.length && value[i] !== "'") {
					i += 1;
				}
				i += 1;
			} else if (ch === '"') {
				i += 1;
				while (i < value.length) {
					if (value[i] === "\\" && i + 1 < value.length) {
						i += 2;
					} else if (value[i] === '"') {
						i += 1;
						break;
					} else {
						i += 1;
					}
				}
			} else if (ch === "\\" && i + 1 < value.length) {
				i += 2;
			} else if (ch === "(") {
				depth += 1;
				i += 1;
			} else if (ch === ")") {
				depth -= 1;
				if (depth === 0) {
					return i;
				}
				i += 1;
			} else {
				i += 1;
			}
		}
		return -1;
	}

	_normalizeArrayInner(inner) {
		let brace_depth,
			bracket_depth,
			ch,
			depth,
			dq_brace_depth,
			dq_content,
			i,
			in_whitespace,
			j,
			normalized;
		normalized = [];
		i = 0;
		in_whitespace = true;
		brace_depth = 0;
		bracket_depth = 0;
		while (i < inner.length) {
			ch = inner[i];
			if (_isWhitespace(ch)) {
				if (
					!in_whitespace &&
					normalized &&
					brace_depth === 0 &&
					bracket_depth === 0
				) {
					normalized.push(" ");
					in_whitespace = true;
				}
				if (brace_depth > 0 || bracket_depth > 0) {
					normalized.push(ch);
				}
				i += 1;
			} else if (ch === "'") {
				// Single-quoted string - preserve as-is
				in_whitespace = false;
				j = i + 1;
				while (j < inner.length && inner[j] !== "'") {
					j += 1;
				}
				normalized.push(inner.slice(i, j + 1));
				i = j + 1;
			} else if (ch === '"') {
				// Double-quoted string - strip line continuations
				// Track ${...} nesting since quotes inside expansions don't end the string
				in_whitespace = false;
				j = i + 1;
				dq_content = ['"'];
				dq_brace_depth = 0;
				while (j < inner.length) {
					if (inner[j] === "\\" && j + 1 < inner.length) {
						if (inner[j + 1] === "\n") {
							// Skip line continuation
							j += 2;
						} else {
							dq_content.push(inner[j]);
							dq_content.push(inner[j + 1]);
							j += 2;
						}
					} else if (
						inner[j] === "$" &&
						j + 1 < inner.length &&
						inner[j + 1] === "{"
					) {
						// Start of ${...} expansion
						dq_content.push("${");
						dq_brace_depth += 1;
						j += 2;
					} else if (inner[j] === "}" && dq_brace_depth > 0) {
						// End of ${...} expansion
						dq_content.push("}");
						dq_brace_depth -= 1;
						j += 1;
					} else if (inner[j] === '"' && dq_brace_depth === 0) {
						dq_content.push('"');
						j += 1;
						break;
					} else {
						dq_content.push(inner[j]);
						j += 1;
					}
				}
				normalized.push(dq_content.join(""));
				i = j;
			} else if (ch === "\\" && i + 1 < inner.length) {
				if (inner[i + 1] === "\n") {
					// Line continuation - skip both backslash and newline
					i += 2;
				} else {
					// Escape sequence - preserve
					in_whitespace = false;
					normalized.push(inner.slice(i, i + 2));
					i += 2;
				}
			} else if (
				ch === "$" &&
				i + 2 < inner.length &&
				inner[i + 1] === "(" &&
				inner[i + 2] === "("
			) {
				// Arithmetic expansion $(( - find matching )) and preserve as-is
				in_whitespace = false;
				j = i + 3;
				depth = 1;
				while (j < inner.length && depth > 0) {
					if (
						j + 1 < inner.length &&
						inner[j] === "(" &&
						inner[j + 1] === "("
					) {
						depth += 1;
						j += 2;
					} else if (
						j + 1 < inner.length &&
						inner[j] === ")" &&
						inner[j + 1] === ")"
					) {
						depth -= 1;
						j += 2;
					} else {
						j += 1;
					}
				}
				normalized.push(inner.slice(i, j));
				i = j;
			} else if (ch === "$" && i + 1 < inner.length && inner[i + 1] === "(") {
				// Command substitution - find matching ) and preserve as-is
				// (formatting is handled later by _format_command_substitutions)
				in_whitespace = false;
				j = i + 2;
				depth = 1;
				while (j < inner.length && depth > 0) {
					if (inner[j] === "(" && j > 0 && inner[j - 1] === "$") {
						depth += 1;
					} else if (inner[j] === ")") {
						depth -= 1;
					} else if (inner[j] === "'") {
						j += 1;
						while (j < inner.length && inner[j] !== "'") {
							j += 1;
						}
					} else if (inner[j] === '"') {
						j += 1;
						while (j < inner.length) {
							if (inner[j] === "\\" && j + 1 < inner.length) {
								j += 2;
								continue;
							}
							if (inner[j] === '"') {
								break;
							}
							j += 1;
						}
					}
					j += 1;
				}
				// Preserve command substitution as-is
				normalized.push(inner.slice(i, j));
				i = j;
			} else if (
				(ch === "<" || ch === ">") &&
				i + 1 < inner.length &&
				inner[i + 1] === "("
			) {
				// Process substitution <(...) or >(...) - find matching ) and preserve as-is
				// (formatting is handled later by _format_command_substitutions)
				in_whitespace = false;
				j = i + 2;
				depth = 1;
				while (j < inner.length && depth > 0) {
					if (inner[j] === "(") {
						depth += 1;
					} else if (inner[j] === ")") {
						depth -= 1;
					} else if (inner[j] === "'") {
						j += 1;
						while (j < inner.length && inner[j] !== "'") {
							j += 1;
						}
					} else if (inner[j] === '"') {
						j += 1;
						while (j < inner.length) {
							if (inner[j] === "\\" && j + 1 < inner.length) {
								j += 2;
								continue;
							}
							if (inner[j] === '"') {
								break;
							}
							j += 1;
						}
					}
					j += 1;
				}
				// Preserve process substitution as-is
				normalized.push(inner.slice(i, j));
				i = j;
			} else if (ch === "$" && i + 1 < inner.length && inner[i + 1] === "{") {
				// Start of ${...} expansion
				in_whitespace = false;
				normalized.push("${");
				brace_depth += 1;
				i += 2;
			} else if (ch === "{" && brace_depth > 0) {
				// Nested brace inside expansion
				normalized.push(ch);
				brace_depth += 1;
				i += 1;
			} else if (ch === "}" && brace_depth > 0) {
				// End of expansion
				normalized.push(ch);
				brace_depth -= 1;
				i += 1;
			} else if (ch === "#" && brace_depth === 0 && in_whitespace) {
				// Comment - skip to end of line (only at top level, start of word)
				while (i < inner.length && inner[i] !== "\n") {
					i += 1;
				}
			} else if (ch === "[") {
				// Only start subscript tracking if at word start (for [key]=val patterns)
				// Mid-word [ like a[ is literal, not a subscript
				if (in_whitespace) {
					bracket_depth += 1;
				}
				in_whitespace = false;
				normalized.push(ch);
				i += 1;
			} else if (ch === "]" && bracket_depth > 0) {
				// End of subscript
				normalized.push(ch);
				bracket_depth -= 1;
				i += 1;
			} else {
				in_whitespace = false;
				normalized.push(ch);
				i += 1;
			}
		}
		// Strip trailing whitespace
		return normalized.join("").trimEnd();
	}

	_stripArithLineContinuations(value) {
		let arith_content,
			closing,
			content,
			depth,
			first_close_idx,
			i,
			j,
			num_backslashes,
			result,
			start;
		result = [];
		i = 0;
		while (i < value.length) {
			// Check for $(( arithmetic expression
			if (_startsWithAt(value, i, "$((")) {
				start = i;
				i += 3;
				depth = 2;
				arith_content = [];
				// Track position of first ) that brings depth 2→1
				first_close_idx = null;
				while (i < value.length && depth > 0) {
					if (value[i] === "(") {
						arith_content.push("(");
						depth += 1;
						i += 1;
						if (depth > 1) {
							first_close_idx = null;
						}
					} else if (value[i] === ")") {
						if (depth === 2) {
							first_close_idx = arith_content.length;
						}
						depth -= 1;
						if (depth > 0) {
							arith_content.push(")");
						}
						i += 1;
					} else if (
						value[i] === "\\" &&
						i + 1 < value.length &&
						value[i + 1] === "\n"
					) {
						// Count preceding backslashes in arith_content
						num_backslashes = 0;
						j = arith_content.length - 1;
						// Skip trailing newlines before counting backslashes
						while (j >= 0 && arith_content[j] === "\n") {
							j -= 1;
						}
						while (j >= 0 && arith_content[j] === "\\") {
							num_backslashes += 1;
							j -= 1;
						}
						// If odd number of preceding backslashes, this backslash is escaped
						if (num_backslashes % 2 === 1) {
							arith_content.push("\\");
							arith_content.push("\n");
							i += 2;
						} else {
							// Skip backslash-newline (line continuation)
							i += 2;
						}
						if (depth === 1) {
							first_close_idx = null;
						}
					} else {
						arith_content.push(value[i]);
						i += 1;
						if (depth === 1) {
							first_close_idx = null;
						}
					}
				}
				if (depth === 0 || (depth === 1 && first_close_idx != null)) {
					content = arith_content.join("");
					if (first_close_idx != null) {
						// Standard close: trim content, add ))
						content = content.slice(0, first_close_idx);
						// If depth==1, we only found one closing paren, add )
						// If depth==0, we found both closing parens, add ))
						closing = depth === 0 ? "))" : ")";
						result.push(`$((${content}${closing}`);
					} else {
						// Content after first close: content has intermediate ), add single )
						result.push(`$((${content})`);
					}
				} else {
					// Didn't close properly - pass through original
					result.push(value.slice(start, i));
				}
			} else {
				result.push(value[i]);
				i += 1;
			}
		}
		return result.join("");
	}

	_collectCmdsubs(node) {
		let condition,
			elem,
			elements,
			expr,
			false_value,
			left,
			node_kind,
			operand,
			p,
			parts,
			result,
			right,
			true_value;
		result = [];
		node_kind = node.kind ?? null;
		if (node_kind === "cmdsub") {
			result.push(node);
		} else if (node_kind === "array") {
			// Array node - collect from each element's parts
			elements = node.elements ?? [];
			for (elem of elements) {
				parts = elem.parts ?? [];
				for (p of parts) {
					if ((p.kind ?? null) === "cmdsub") {
						result.push(p);
					} else {
						result.push(...this._collectCmdsubs(p));
					}
				}
			}
		} else {
			expr = node.expression ?? null;
			if (expr != null) {
				// ArithmeticExpansion, ArithBinaryOp, etc.
				result.push(...this._collectCmdsubs(expr));
			}
		}
		left = node.left ?? null;
		if (left != null) {
			result.push(...this._collectCmdsubs(left));
		}
		right = node.right ?? null;
		if (right != null) {
			result.push(...this._collectCmdsubs(right));
		}
		operand = node.operand ?? null;
		if (operand != null) {
			result.push(...this._collectCmdsubs(operand));
		}
		condition = node.condition ?? null;
		if (condition != null) {
			result.push(...this._collectCmdsubs(condition));
		}
		true_value = node.true_value ?? null;
		if (true_value != null) {
			result.push(...this._collectCmdsubs(true_value));
		}
		false_value = node.false_value ?? null;
		if (false_value != null) {
			result.push(...this._collectCmdsubs(false_value));
		}
		return result;
	}

	_collectProcsubs(node) {
		let elem, elements, node_kind, p, parts, result;
		result = [];
		node_kind = node.kind ?? null;
		if (node_kind === "procsub") {
			result.push(node);
		} else if (node_kind === "array") {
			elements = node.elements ?? [];
			for (elem of elements) {
				parts = elem.parts ?? [];
				for (p of parts) {
					if ((p.kind ?? null) === "procsub") {
						result.push(p);
					} else {
						result.push(...this._collectProcsubs(p));
					}
				}
			}
		}
		return result;
	}

	_formatCommandSubstitutions(value, in_arith) {
		let arith_depth,
			arith_paren_depth,
			c,
			cmdsub_idx,
			cmdsub_parts,
			compact,
			deprecated_arith_depth,
			depth,
			direction,
			extglob_depth,
			formatted,
			formatted_inner,
			has_arith,
			has_brace_cmdsub,
			has_untracked_cmdsub,
			has_untracked_procsub,
			i,
			idx,
			in_double,
			in_double_quote,
			in_single,
			inner,
			is_procsub,
			j,
			leading_ws,
			leading_ws_end,
			node,
			normalized_ws,
			p,
			parsed,
			parser,
			prefix,
			procsub_idx,
			procsub_parts,
			raw_content,
			raw_stripped,
			result,
			spaced,
			stripped,
			terminator;
		if (in_arith == null) {
			in_arith = false;
		}
		// Collect command substitutions from all parts, including nested ones
		cmdsub_parts = [];
		procsub_parts = [];
		has_arith = false;
		for (p of this.parts) {
			if (p.kind === "cmdsub") {
				cmdsub_parts.push(p);
			} else if (p.kind === "procsub") {
				procsub_parts.push(p);
			} else if (p.kind === "arith") {
				has_arith = true;
			} else {
				cmdsub_parts.push(...this._collectCmdsubs(p));
				procsub_parts.push(...this._collectProcsubs(p));
			}
		}
		// Check if we have ${ or ${| brace command substitutions to format
		has_brace_cmdsub =
			value.indexOf("${ ") !== -1 ||
			value.indexOf("${\t") !== -1 ||
			value.indexOf("${|") !== -1;
		// Check if there's an untracked $( that isn't $((, skipping over quotes only
		has_untracked_cmdsub = false;
		has_untracked_procsub = false;
		idx = 0;
		in_double = false;
		while (idx < value.length) {
			if (value[idx] === '"') {
				in_double = !in_double;
				idx += 1;
			} else if (value[idx] === "'" && !in_double) {
				// Skip over single-quoted string (contents are literal)
				// But only when not inside double quotes
				idx += 1;
				while (idx < value.length && value[idx] !== "'") {
					idx += 1;
				}
				if (idx < value.length) {
					idx += 1;
				}
			} else if (
				_startsWithAt(value, idx, "$(") &&
				!_startsWithAt(value, idx, "$((") &&
				!_isBackslashEscaped(value, idx) &&
				!_isDollarDollarParen(value, idx)
			) {
				has_untracked_cmdsub = true;
				break;
			} else if (
				(_startsWithAt(value, idx, "<(") || _startsWithAt(value, idx, ">(")) &&
				!in_double
			) {
				// Only treat as process substitution if not preceded by alphanumeric or quote
				// (e.g., "i<(3)" is arithmetic comparison, not process substitution)
				// Also don't treat as process substitution inside double quotes or after quotes
				if (
					idx === 0 ||
					(!/^[a-zA-Z0-9]$/.test(value[idx - 1]) &&
						!"\"'".includes(value[idx - 1]))
				) {
					has_untracked_procsub = true;
					break;
				}
				idx += 1;
			} else {
				idx += 1;
			}
		}
		if (
			cmdsub_parts.length === 0 &&
			procsub_parts.length === 0 &&
			!has_brace_cmdsub &&
			!has_untracked_cmdsub &&
			!has_untracked_procsub
		) {
			return value;
		}
		result = [];
		i = 0;
		cmdsub_idx = 0;
		procsub_idx = 0;
		in_double_quote = false;
		extglob_depth = 0;
		deprecated_arith_depth = 0;
		arith_depth = 0;
		arith_paren_depth = 0;
		while (i < value.length) {
			// Check for extglob start: @( ?( *( +( !(
			if (
				i > 0 &&
				_isExtglobPrefix(value[i - 1]) &&
				value[i] === "(" &&
				!_isBackslashEscaped(value, i - 1)
			) {
				extglob_depth += 1;
				result.push(value[i]);
				i += 1;
				continue;
			}
			// Track ) that closes extglob (but not inside cmdsub/procsub)
			if (value[i] === ")" && extglob_depth > 0) {
				extglob_depth -= 1;
				result.push(value[i]);
				i += 1;
				continue;
			}
			// Track deprecated arithmetic $[...] - inside it, >( and <( are not procsub
			if (_startsWithAt(value, i, "$[") && !_isBackslashEscaped(value, i)) {
				deprecated_arith_depth += 1;
				result.push(value[i]);
				i += 1;
				continue;
			}
			if (value[i] === "]" && deprecated_arith_depth > 0) {
				deprecated_arith_depth -= 1;
				result.push(value[i]);
				i += 1;
				continue;
			}
			// Track $((...)) arithmetic - inside it, >( and <( are not process subs
			// But skip if this is actually $( ( (command substitution with subshell)
			if (
				_startsWithAt(value, i, "$((") &&
				!_isBackslashEscaped(value, i) &&
				has_arith
			) {
				arith_depth += 1;
				arith_paren_depth += 2;
				result.push("$((");
				i += 3;
				continue;
			}
			// Track )) that closes arithmetic (only when no inner parens open)
			if (
				arith_depth > 0 &&
				arith_paren_depth === 2 &&
				_startsWithAt(value, i, "))")
			) {
				arith_depth -= 1;
				arith_paren_depth -= 2;
				result.push("))");
				i += 2;
				continue;
			}
			// Track ( and ) inside arithmetic
			if (arith_depth > 0) {
				if (value[i] === "(") {
					arith_paren_depth += 1;
					result.push(value[i]);
					i += 1;
					continue;
				} else if (value[i] === ")") {
					arith_paren_depth -= 1;
					result.push(value[i]);
					i += 1;
					continue;
				}
			}
			// Check for $( command substitution (but not $(( arithmetic or escaped \$()
			// Special case: $(( without arithmetic nodes - preserve as-is
			if (_startsWithAt(value, i, "$((") && !has_arith) {
				// This looks like $(( but wasn't parsed as arithmetic
				// It's actually $( ( ... ) ) - preserve original text
				j = _findCmdsubEnd(value, i + 2);
				result.push(value.slice(i, j));
				if (cmdsub_idx < cmdsub_parts.length) {
					cmdsub_idx += 1;
				}
				i = j;
				continue;
			}
			// Regular command substitution
			if (
				_startsWithAt(value, i, "$(") &&
				!_startsWithAt(value, i, "$((") &&
				!_isBackslashEscaped(value, i) &&
				!_isDollarDollarParen(value, i)
			) {
				// Find matching close paren using bash-aware matching
				j = _findCmdsubEnd(value, i + 2);
				// Inside extglob: don't format, just copy raw content
				if (extglob_depth > 0) {
					result.push(value.slice(i, j));
					if (cmdsub_idx < cmdsub_parts.length) {
						cmdsub_idx += 1;
					}
					i = j;
					continue;
				}
				// Format this command substitution
				if (cmdsub_idx < cmdsub_parts.length) {
					node = cmdsub_parts[cmdsub_idx];
					formatted = _formatCmdsubNode(node.command);
					cmdsub_idx += 1;
				} else {
					// No AST node (e.g., inside arithmetic) - parse content on the fly
					inner = value.slice(i + 2, j - 1);
					try {
						parser = new Parser(inner);
						parsed = parser.parseList();
						formatted = parsed ? _formatCmdsubNode(parsed) : "";
					} catch (_) {
						formatted = inner;
					}
				}
				// Add space after $( if content starts with ( to avoid $((
				if (formatted.startsWith("(")) {
					result.push(`$( ${formatted})`);
				} else {
					result.push(`$(${formatted})`);
				}
				i = j;
			} else if (value[i] === "`" && cmdsub_idx < cmdsub_parts.length) {
				// Check for backtick command substitution
				// Find matching backtick
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
				// Keep backtick substitutions as-is (bash-oracle doesn't reformat them)
				result.push(value.slice(i, j));
				cmdsub_idx += 1;
				i = j;
			} else if (
				(_startsWithAt(value, i, ">(") || _startsWithAt(value, i, "<(")) &&
				!in_double_quote &&
				deprecated_arith_depth === 0 &&
				arith_depth === 0
			) {
				// Check for >( or <( process substitution (not inside double quotes, $[...], or $((...)))
				// Check if this is actually a process substitution or just comparison + parens
				// Process substitution: not preceded by alphanumeric or quote
				is_procsub =
					i === 0 ||
					(!/^[a-zA-Z0-9]$/.test(value[i - 1]) &&
						!"\"'".includes(value[i - 1]));
				// Inside extglob: don't format, just copy raw content
				if (extglob_depth > 0) {
					j = _findCmdsubEnd(value, i + 2);
					result.push(value.slice(i, j));
					if (procsub_idx < procsub_parts.length) {
						procsub_idx += 1;
					}
					i = j;
					continue;
				}
				if (procsub_idx < procsub_parts.length) {
					// Have parsed AST node - use it
					direction = value[i];
					j = _findCmdsubEnd(value, i + 2);
					node = procsub_parts[procsub_idx];
					compact = _startsWithSubshell(node.command);
					formatted = _formatCmdsubNode(node.command, 0, true, compact, true);
					raw_content = value.slice(i + 2, j - 1);
					if (node.command.kind === "subshell") {
						// Extract leading whitespace
						leading_ws_end = 0;
						while (
							leading_ws_end < raw_content.length &&
							" \t\n".includes(raw_content[leading_ws_end])
						) {
							leading_ws_end += 1;
						}
						leading_ws = raw_content.slice(0, leading_ws_end);
						stripped = raw_content.slice(leading_ws_end);
						if (stripped.startsWith("(")) {
							if (leading_ws) {
								// Leading whitespace before subshell: normalize ws + format subshell with spaces
								normalized_ws = leading_ws
									.replaceAll("\n", " ")
									.replaceAll("\t", " ");
								spaced = _formatCmdsubNode(node.command, 0, false);
								result.push(`${direction}(${normalized_ws}${spaced})`);
							} else {
								// No leading whitespace - preserve original raw content
								raw_content = raw_content.replaceAll("\\\n", "");
								result.push(`${direction}(${raw_content})`);
							}
							procsub_idx += 1;
							i = j;
							continue;
						}
					}
					// Extract raw content for further checks
					raw_content = value.slice(i + 2, j - 1);
					raw_stripped = raw_content.replaceAll("\\\n", "");
					// Check for pattern: subshell followed by operator with no space (e.g., "(0)&+")
					// In this case, preserve original to match bash-oracle behavior
					if (_startsWithSubshell(node.command) && formatted !== raw_stripped) {
						// Starts with subshell and formatting would change it - preserve original
						result.push(`${direction}(${raw_stripped})`);
					} else {
						result.push(`${direction}(${formatted})`);
					}
					procsub_idx += 1;
					i = j;
				} else if (is_procsub && this.parts.length) {
					// No AST node but valid procsub context - parse content on the fly
					direction = value[i];
					j = _findCmdsubEnd(value, i + 2);
					// Check if we found a valid closing ) - if not, treat as literal characters
					if (
						j > value.length ||
						(j > 0 && j <= value.length && value[j - 1] !== ")")
					) {
						result.push(value[i]);
						i += 1;
						continue;
					}
					inner = value.slice(i + 2, j - 1);
					try {
						parser = new Parser(inner);
						parsed = parser.parseList();
						// Only use parsed result if parser consumed all input and no newlines in content
						// (newlines would be lost during formatting)
						if (
							parsed &&
							parser.pos === inner.length &&
							!inner.includes("\n")
						) {
							compact = _startsWithSubshell(parsed);
							formatted = _formatCmdsubNode(parsed, 0, true, compact, true);
						} else {
							formatted = inner;
						}
					} catch (_) {
						formatted = inner;
					}
					result.push(`${direction}(${formatted})`);
					i = j;
				} else if (is_procsub) {
					// Process substitution but no parts (failed to parse or in arithmetic context)
					direction = value[i];
					j = _findCmdsubEnd(value, i + 2);
					if (
						j > value.length ||
						(j > 0 && j <= value.length && value[j - 1] !== ")")
					) {
						// Couldn't find closing paren, treat as literal
						result.push(value[i]);
						i += 1;
						continue;
					}
					inner = value.slice(i + 2, j - 1);
					// In arithmetic context, preserve whitespace; otherwise strip leading whitespace
					if (in_arith) {
						result.push(`${direction}(${inner})`);
					} else if (inner.trim()) {
						stripped = inner.replace(/^[ \t]+/, "");
						result.push(`${direction}(${stripped})`);
					} else {
						result.push(`${direction}(${inner})`);
					}
					i = j;
				} else {
					// Not a process substitution (e.g., arithmetic comparison)
					result.push(value[i]);
					i += 1;
				}
			} else if (
				(_startsWithAt(value, i, "${ ") ||
					_startsWithAt(value, i, "${\t") ||
					_startsWithAt(value, i, "${|")) &&
				!_isBackslashEscaped(value, i)
			) {
				// Check for ${ (space/tab) or ${| brace command substitution
				// But not if the $ is escaped by a backslash
				prefix = value.slice(i, i + 3).replaceAll("\t", " ");
				// Find matching close brace
				j = i + 3;
				depth = 1;
				while (j < value.length && depth > 0) {
					if (value[j] === "{") {
						depth += 1;
					} else if (value[j] === "}") {
						depth -= 1;
					}
					j += 1;
				}
				// Parse and format the inner content
				inner = value.slice(i + 2, j - 1);
				// Check if content is all whitespace - normalize to single space
				if (inner.trim() === "") {
					result.push("${ }");
				} else {
					try {
						parser = new Parser(inner.replace(/^[ \t|]+/, ""));
						parsed = parser.parseList();
						if (parsed) {
							formatted = _formatCmdsubNode(parsed);
							formatted = formatted.replace(/[;]+$/, "");
							// Preserve trailing newline from original if present
							if (inner.replace(/[ \t]+$/, "").endsWith("\n")) {
								terminator = "\n }";
							} else if (formatted.endsWith(" &")) {
								terminator = " }";
							} else {
								terminator = "; }";
							}
							result.push(prefix + formatted + terminator);
						} else {
							result.push("${ }");
						}
					} catch (_) {
						result.push(value.slice(i, j));
					}
				}
				i = j;
			} else if (
				_startsWithAt(value, i, "${") &&
				!_isBackslashEscaped(value, i)
			) {
				// Process regular ${...} parameter expansions (recursively format cmdsubs inside)
				// But not if the $ is escaped by a backslash
				// Find matching close brace, respecting nesting, quotes, and cmdsubs
				j = i + 2;
				depth = 1;
				in_single = false;
				in_double = false;
				while (j < value.length && depth > 0) {
					c = value[j];
					if (c === "\\" && j + 1 < value.length && !in_single) {
						j += 2;
						continue;
					}
					if (c === "'" && !in_double) {
						in_single = !in_single;
					} else if (c === '"' && !in_single) {
						in_double = !in_double;
					} else if (!in_single && !in_double) {
						// Skip over $(...) command substitutions
						if (
							_startsWithAt(value, j, "$(") &&
							!_startsWithAt(value, j, "$((")
						) {
							j = _findCmdsubEnd(value, j + 2);
							continue;
						}
						if (c === "{") {
							depth += 1;
						} else if (c === "}") {
							depth -= 1;
						}
					}
					j += 1;
				}
				// Recursively format any cmdsubs inside the param expansion
				inner = value.slice(i + 2, j - 1);
				formatted_inner = this._formatCommandSubstitutions(inner);
				result.push(`\${${formatted_inner}}`);
				i = j;
			} else if (value[i] === '"') {
				// Track double-quote state (single quotes inside double quotes are literal)
				in_double_quote = !in_double_quote;
				result.push(value[i]);
				i += 1;
			} else if (value[i] === "'" && !in_double_quote) {
				// Skip single-quoted strings (contents are literal, don't look for cmdsubs)
				// But only when NOT inside double quotes (where single quotes are literal)
				j = i + 1;
				while (j < value.length && value[j] !== "'") {
					j += 1;
				}
				if (j < value.length) {
					j += 1;
				}
				result.push(value.slice(i, j));
				i = j;
			} else {
				result.push(value[i]);
				i += 1;
			}
		}
		return result.join("");
	}

	_normalizeExtglobWhitespace(value) {
		let current_part,
			depth,
			i,
			in_double_quote,
			part_content,
			pattern_parts,
			prefix_char,
			result;
		result = [];
		i = 0;
		in_double_quote = false;
		while (i < value.length) {
			// Track double-quote state
			if (value[i] === '"') {
				in_double_quote = !in_double_quote;
				result.push(value[i]);
				i += 1;
				continue;
			}
			// Check for >( or <( pattern (process substitution-like in regex)
			// Only process these patterns when NOT inside double quotes
			if (i + 1 < value.length && value[i + 1] === "(") {
				prefix_char = value[i];
				if ("><".includes(prefix_char) && !in_double_quote) {
					// Found pattern start
					result.push(prefix_char);
					result.push("(");
					i += 2;
					// Process content until matching )
					depth = 1;
					pattern_parts = [];
					current_part = [];
					while (i < value.length && depth > 0) {
						if (value[i] === "\\" && i + 1 < value.length) {
							// Escaped character, keep as-is
							current_part.push(value.slice(i, i + 2));
							i += 2;
							continue;
						} else if (value[i] === "(") {
							depth += 1;
							current_part.push(value[i]);
							i += 1;
						} else if (value[i] === ")") {
							depth -= 1;
							if (depth === 0) {
								// End of pattern
								part_content = current_part.join("");
								// Don't strip if this looks like a process substitution with heredoc
								if (part_content.includes("<<")) {
									pattern_parts.push(part_content);
								} else {
									pattern_parts.push(part_content.trim());
								}
								break;
							}
							current_part.push(value[i]);
							i += 1;
						} else if (value[i] === "|" && depth === 1) {
							// Top-level pipe separator
							part_content = current_part.join("");
							// Don't strip if this looks like a process substitution with heredoc
							if (part_content.includes("<<")) {
								pattern_parts.push(part_content);
							} else {
								pattern_parts.push(part_content.trim());
							}
							current_part = [];
							i += 1;
						} else {
							current_part.push(value[i]);
							i += 1;
						}
					}
					// Join parts with " | "
					result.push(pattern_parts.join(" | "));
					result.push(")");
					i += 1;
					continue;
				}
			}
			result.push(value[i]);
			i += 1;
		}
		return result.join("");
	}

	getCondFormattedValue() {
		let value;
		// Expand ANSI-C quotes
		value = this._expandAllAnsiCQuotes(this.value);
		// Strip $ from locale strings $"..."
		value = this._stripLocaleStringDollars(value);
		// Format command substitutions
		value = this._formatCommandSubstitutions(value);
		// Normalize whitespace in extglob-like patterns
		value = this._normalizeExtglobWhitespace(value);
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
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		let inner, parts, r, w;
		parts = [];
		for (w of this.words) {
			parts.push(w.toSexp());
		}
		for (r of this.redirects) {
			parts.push(r.toSexp());
		}
		inner = parts.join(" ");
		if (!inner) {
			return "(command)";
		}
		return `(command ${inner})`;
	}
}

class Pipeline extends Node {
	constructor(commands) {
		super();
		this.kind = "pipeline";
		this.commands = commands;
	}

	toSexp() {
		let cmd,
			cmds,
			i,
			j,
			last_cmd,
			last_needs,
			last_pair,
			needs,
			needs_redirect,
			pair,
			result;
		if (this.commands.length === 1) {
			return this.commands[0].toSexp();
		}
		// Build list of (cmd, needs_pipe_both_redirect) filtering out PipeBoth markers
		cmds = [];
		i = 0;
		while (i < this.commands.length) {
			cmd = this.commands[i];
			if (cmd.kind === "pipe-both") {
				i += 1;
				continue;
			}
			// Check if next element is PipeBoth
			needs_redirect =
				i + 1 < this.commands.length &&
				this.commands[i + 1].kind === "pipe-both";
			cmds.push([cmd, needs_redirect]);
			i += 1;
		}
		if (cmds.length === 1) {
			pair = cmds[0];
			cmd = pair[0];
			needs = pair[1];
			return this._cmdSexp(cmd, needs);
		}
		// Nest right-associatively: (pipe a (pipe b c))
		last_pair = cmds[cmds.length - 1];
		last_cmd = last_pair[0];
		last_needs = last_pair[1];
		result = this._cmdSexp(last_cmd, last_needs);
		j = cmds.length - 2;
		while (j >= 0) {
			pair = cmds[j];
			cmd = pair[0];
			needs = pair[1];
			if (needs && cmd.kind !== "command") {
				// Compound command: redirect as sibling in pipe
				result = `(pipe ${cmd.toSexp()} (redirect ">&" 1) ${result})`;
			} else {
				result = `(pipe ${this._cmdSexp(cmd, needs)} ${result})`;
			}
			j -= 1;
		}
		return result;
	}

	_cmdSexp(cmd, needs_redirect) {
		let parts, r, w;
		if (!needs_redirect) {
			return cmd.toSexp();
		}
		if (cmd.kind === "command") {
			// Inject redirect inside command
			parts = [];
			for (w of cmd.words) {
				parts.push(w.toSexp());
			}
			for (r of cmd.redirects) {
				parts.push(r.toSexp());
			}
			parts.push('(redirect ">&" 1)');
			return `(command ${parts.join(" ")})`;
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
		let i,
			inner_list,
			inner_parts,
			left,
			left_sexp,
			op_names,
			parts,
			right,
			right_sexp;
		// parts = [cmd, op, cmd, op, cmd, ...]
		// Bash precedence: && and || bind tighter than ; and &
		parts = Array.from(this.parts);
		op_names = {
			"&&": "and",
			"||": "or",
			";": "semi",
			"\n": "semi",
			"&": "background",
		};
		// Strip trailing ; or \n (bash ignores it)
		while (
			parts.length > 1 &&
			parts[parts.length - 1].kind === "operator" &&
			(parts[parts.length - 1].op === ";" ||
				parts[parts.length - 1].op === "\n")
		) {
			parts = parts.slice(0, parts.length - 1);
		}
		if (parts.length === 1) {
			return parts[0].toSexp();
		}
		// Handle trailing & as unary background operator
		// & only applies to the immediately preceding pipeline, not the whole list
		if (
			parts[parts.length - 1].kind === "operator" &&
			parts[parts.length - 1].op === "&"
		) {
			// Find rightmost ; or \n to split there
			for (i = parts.length - 3; i > 0; i--) {
				if (
					parts[i].kind === "operator" &&
					(parts[i].op === ";" || parts[i].op === "\n")
				) {
					left = parts.slice(0, i);
					right = parts.slice(i + 1, parts.length - 1);
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
					return `(semi ${left_sexp} (background ${right_sexp}))`;
				}
			}
			// No ; or \n found, background the whole list (minus trailing &)
			inner_parts = parts.slice(0, parts.length - 1);
			if (inner_parts.length === 1) {
				return `(background ${inner_parts[0].toSexp()})`;
			}
			inner_list = new List(inner_parts);
			return `(background ${inner_list.toSexp()})`;
		}
		// Process by precedence: first split on ; and &, then on && and ||
		return this._toSexpWithPrecedence(parts, op_names);
	}

	_toSexpWithPrecedence(parts, op_names) {
		let i, pos, result, seg, segments, semi_positions, start;
		// Process operators by precedence: ; (lowest), then &, then && and ||
		// Use iterative approach to avoid stack overflow on large lists
		// Find all ; or \n positions (may not be at regular intervals due to consecutive ops)
		semi_positions = [];
		for (i = 0; i < parts.length; i++) {
			if (
				parts[i].kind === "operator" &&
				(parts[i].op === ";" || parts[i].op === "\n")
			) {
				semi_positions.push(i);
			}
		}
		if (semi_positions) {
			// Split into segments at ; and \n positions, filtering empty/operator-only segments
			segments = [];
			start = 0;
			for (pos of semi_positions) {
				seg = parts.slice(start, pos);
				if (seg.length > 0 && seg[0].kind !== "operator") {
					segments.push(seg);
				}
				start = pos + 1;
			}
			// Final segment
			seg = parts.slice(start, parts.length);
			if (seg.length > 0 && seg[0].kind !== "operator") {
				segments.push(seg);
			}
			if (!segments) {
				return "()";
			}
			// Build left-associative result iteratively
			result = this._toSexpAmpAndHigher(segments[0], op_names);
			for (i = 1; i < segments.length; i++) {
				result = `(semi ${result} ${this._toSexpAmpAndHigher(segments[i], op_names)})`;
			}
			return result;
		}
		// No ; or \n, handle & and higher
		return this._toSexpAmpAndHigher(parts, op_names);
	}

	_toSexpAmpAndHigher(parts, op_names) {
		let amp_positions, i, pos, result, segments, start;
		// Handle & operator iteratively
		if (parts.length === 1) {
			return parts[0].toSexp();
		}
		amp_positions = [];
		for (i = 1; i < parts.length - 1; i += 2) {
			if (parts[i].kind === "operator" && parts[i].op === "&") {
				amp_positions.push(i);
			}
		}
		if (amp_positions) {
			// Split into segments at & positions
			segments = [];
			start = 0;
			for (pos of amp_positions) {
				segments.push(parts.slice(start, pos));
				start = pos + 1;
			}
			segments.push(parts.slice(start, parts.length));
			// Build left-associative result iteratively
			result = this._toSexpAndOr(segments[0], op_names);
			for (i = 1; i < segments.length; i++) {
				result = `(background ${result} ${this._toSexpAndOr(segments[i], op_names)})`;
			}
			return result;
		}
		// No &, handle && and ||
		return this._toSexpAndOr(parts, op_names);
	}

	_toSexpAndOr(parts, op_names) {
		let cmd, i, op, op_name, result;
		// Process && and || left-associatively (already iterative)
		if (parts.length === 1) {
			return parts[0].toSexp();
		}
		result = parts[0].toSexp();
		for (i = 1; i < parts.length - 1; i += 2) {
			op = parts[i];
			cmd = parts[i + 1];
			op_name = op_names[op.op] ?? op.op;
			result = `(${op_name} ${result} ${cmd.toSexp()})`;
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
		let names;
		names = { "&&": "and", "||": "or", ";": "semi", "&": "bg", "|": "pipe" };
		return `(${names[this.op] ?? this.op})`;
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
		let fd_target, j, op, out_val, raw, target_val;
		// Strip fd prefix from operator (e.g., "2>" -> ">", "{fd}>" -> ">")
		op = this.op.replace(/^[0123456789]+/, "");
		// Strip {varname} or {varname[subscript]} prefix if present
		if (op.startsWith("{")) {
			j = 1;
			if (j < op.length && (/^[a-zA-Z]$/.test(op[j]) || op[j] === "_")) {
				j += 1;
				while (
					j < op.length &&
					(/^[a-zA-Z0-9]$/.test(op[j]) || op[j] === "_")
				) {
					j += 1;
				}
				// Handle optional [subscript] part
				if (j < op.length && op[j] === "[") {
					j += 1;
					while (j < op.length && op[j] !== "]") {
						j += 1;
					}
					if (j < op.length && op[j] === "]") {
						j += 1;
					}
				}
				if (j < op.length && op[j] === "}") {
					op = op.slice(j + 1, op.length);
				}
			}
		}
		target_val = this.target.value;
		// Expand ANSI-C $'...' quotes (converts escapes like \n to actual newline)
		target_val = this.target._expandAllAnsiCQuotes(target_val);
		// Strip $ from locale strings $"..."
		target_val = this.target._stripLocaleStringDollars(target_val);
		// Format command/process substitutions (uses self.target for parts access)
		target_val = this.target._formatCommandSubstitutions(target_val);
		// Strip line continuations (backslash-newline) from arithmetic expressions
		target_val = this.target._stripArithLineContinuations(target_val);
		// Escape trailing backslash (would escape the closing quote otherwise)
		if (target_val.endsWith("\\") && !target_val.endsWith("\\\\")) {
			target_val = `${target_val}\\`;
		}
		// For fd duplication, target starts with & (e.g., "&1", "&2", "&-")
		if (target_val.startsWith("&")) {
			// Determine the real operator
			if (op === ">") {
				op = ">&";
			} else if (op === "<") {
				op = "<&";
			}
			raw = target_val.slice(1, target_val.length);
			// Pure digits: dup fd N
			if (/^[0-9]+$/.test(raw)) {
				return `(redirect "${op}" ${parseInt(raw, 10)})`;
			}
			// Exact move syntax: N- (digits + exactly one dash)
			if (raw.endsWith("-") && /^[0-9]+$/.test(raw.slice(0, -1))) {
				return `(redirect "${op}" ${parseInt(raw.slice(0, -1), 10)})`;
			}
			if (target_val === "&-") {
				return '(redirect ">&-" 0)';
			}
			// Variable/word target: strip exactly one trailing dash if present
			fd_target = raw.endsWith("-") ? raw.slice(0, -1) : raw;
			return `(redirect "${op}" "${fd_target}")`;
		}
		// Handle case where op is already >& or <&
		if (op === ">&" || op === "<&") {
			if (/^[0-9]+$/.test(target_val)) {
				return `(redirect "${op}" ${parseInt(target_val, 10)})`;
			}
			// Handle close: <& - or >& - (with space before -)
			if (target_val === "-") {
				return '(redirect ">&-" 0)';
			}
			// Exact move syntax: N- (digits + exactly one dash)
			if (
				target_val.endsWith("-") &&
				/^[0-9]+$/.test(target_val.slice(0, -1))
			) {
				return `(redirect "${op}" ${parseInt(target_val.slice(0, -1), 10)})`;
			}
			// Variable/word target: strip exactly one trailing dash if present
			out_val = target_val.endsWith("-") ? target_val.slice(0, -1) : target_val;
			return `(redirect "${op}" "${out_val}")`;
		}
		return `(redirect "${op}" "${target_val}")`;
	}
}

class HereDoc extends Node {
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
		let content, op;
		op = this.strip_tabs ? "<<-" : "<<";
		content = this.content;
		// Escape trailing backslash (would escape the closing quote otherwise)
		if (content.endsWith("\\") && !content.endsWith("\\\\")) {
			content = `${content}\\`;
		}
		return `(redirect "${op}" "${content}")`;
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
		let base;
		base = `(subshell ${this.body.toSexp()})`;
		return _appendRedirects(base, this.redirects);
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
		let base;
		base = `(brace-group ${this.body.toSexp()})`;
		return _appendRedirects(base, this.redirects);
	}
}

class If extends Node {
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
		let r, result;
		result = `(if ${this.condition.toSexp()} ${this.then_body.toSexp()}`;
		if (this.else_body) {
			result = `${result} ${this.else_body.toSexp()}`;
		}
		result = `${result})`;
		for (r of this.redirects) {
			result = `${result} ${r.toSexp()}`;
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
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		let base;
		base = `(while ${this.condition.toSexp()} ${this.body.toSexp()})`;
		return _appendRedirects(base, this.redirects);
	}
}

class Until extends Node {
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
		let base;
		base = `(until ${this.condition.toSexp()} ${this.body.toSexp()})`;
		return _appendRedirects(base, this.redirects);
	}
}

class For extends Node {
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
		let r,
			redirect_parts,
			suffix,
			temp_word,
			var_escaped,
			var_formatted,
			w,
			word_parts,
			word_strs;
		// bash-oracle format: (for (word "var") (in (word "a") ...) body)
		suffix = "";
		if (this.redirects && this.redirects.length) {
			redirect_parts = [];
			for (r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			suffix = ` ${redirect_parts.join(" ")}`;
		}
		// Format command substitutions in var (e.g., for $(echo i) normalizes whitespace)
		temp_word = new Word(this.variable, []);
		var_formatted = temp_word._formatCommandSubstitutions(this.variable);
		var_escaped = var_formatted.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
		if (this.words == null) {
			// No 'in' clause - bash-oracle implies (in (word "\"$@\""))
			return `(for (word "${var_escaped}") (in (word "\\"$@\\"")) ${this.body.toSexp()})${suffix}`;
		} else if (this.words.length === 0) {
			// Empty 'in' clause - bash-oracle outputs (in)
			return `(for (word "${var_escaped}") (in) ${this.body.toSexp()})${suffix}`;
		} else {
			word_parts = [];
			for (w of this.words) {
				word_parts.push(w.toSexp());
			}
			word_strs = word_parts.join(" ");
			return `(for (word "${var_escaped}") (in ${word_strs}) ${this.body.toSexp()})${suffix}`;
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
		if (redirects == null) {
			redirects = [];
		}
		this.redirects = redirects;
	}

	toSexp() {
		let body_str,
			cond_str,
			cond_val,
			incr_str,
			incr_val,
			init_str,
			init_val,
			r,
			redirect_parts,
			suffix;
		// bash-oracle format: (arith-for (init (word "x")) (test (word "y")) (step (word "z")) body)
		function formatArithVal(s) {
			let val, w;
			// Use Word's methods to expand ANSI-C quotes and strip locale $
			w = new Word(s, []);
			val = w._expandAllAnsiCQuotes(s);
			val = w._stripLocaleStringDollars(val);
			val = w._formatCommandSubstitutions(val);
			val = val.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			val = val.replaceAll("\n", "\\n").replaceAll("\t", "\\t");
			return val;
		}

		suffix = "";
		if (this.redirects && this.redirects.length) {
			redirect_parts = [];
			for (r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			suffix = ` ${redirect_parts.join(" ")}`;
		}
		init_val = this.init ? this.init : "1";
		cond_val = this.cond ? this.cond : "1";
		incr_val = this.incr ? this.incr : "1";
		init_str = formatArithVal(init_val);
		cond_str = formatArithVal(cond_val);
		incr_str = formatArithVal(incr_val);
		body_str = this.body.toSexp();
		return `(arith-for (init (word "${init_str}")) (test (word "${cond_str}")) (step (word "${incr_str}")) ${body_str})${suffix}`;
	}
}

class Select extends Node {
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
		let in_clause,
			r,
			redirect_parts,
			suffix,
			var_escaped,
			w,
			word_parts,
			word_strs;
		// bash-oracle format: (select (word "var") (in (word "a") ...) body)
		suffix = "";
		if (this.redirects && this.redirects.length) {
			redirect_parts = [];
			for (r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			suffix = ` ${redirect_parts.join(" ")}`;
		}
		var_escaped = this.variable.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
		if (this.words != null) {
			word_parts = [];
			for (w of this.words) {
				word_parts.push(w.toSexp());
			}
			word_strs = word_parts.join(" ");
			if (this.words && this.words.length) {
				in_clause = `(in ${word_strs})`;
			} else {
				in_clause = "(in)";
			}
		} else {
			// No 'in' clause means implicit "$@"
			in_clause = '(in (word "\\"$@\\""))';
		}
		return `(select (word "${var_escaped}") ${in_clause} ${this.body.toSexp()})${suffix}`;
	}
}

class Case extends Node {
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
		let base, p, parts;
		parts = [];
		parts.push(`(case ${this.word.toSexp()}`);
		for (p of this.patterns) {
			parts.push(p.toSexp());
		}
		base = `${parts.join(" ")})`;
		return _appendRedirects(base, this.redirects);
	}
}

function _consumeSingleQuote(s, start) {
	let chars, i;
	chars = ["'"];
	i = start + 1;
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

function _consumeDoubleQuote(s, start) {
	let chars, i;
	chars = ['"'];
	i = start + 1;
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

function _hasBracketClose(s, start, depth) {
	let i;
	i = start;
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

function _consumeBracketClass(s, start, depth) {
	let chars, i, is_bracket, scan_pos;
	// First scan to see if this is a valid bracket expression
	scan_pos = start + 1;
	// Skip [! or [^ at start
	if (scan_pos < s.length && (s[scan_pos] === "!" || s[scan_pos] === "^")) {
		scan_pos += 1;
	}
	// Handle ] as first char
	if (scan_pos < s.length && s[scan_pos] === "]") {
		if (_hasBracketClose(s, scan_pos + 1, depth)) {
			scan_pos += 1;
		}
	}
	// Scan for closing ]
	is_bracket = false;
	while (scan_pos < s.length) {
		if (s[scan_pos] === "]") {
			is_bracket = true;
			break;
		}
		if (s[scan_pos] === ")" && depth === 0) {
			break;
		}
		if (s[scan_pos] === "|" && depth === 0) {
			break;
		}
		scan_pos += 1;
	}
	if (!is_bracket) {
		return [start + 1, ["["], false];
	}
	// Valid bracket - consume it
	chars = ["["];
	i = start + 1;
	// Handle [! or [^
	if (i < s.length && (s[i] === "!" || s[i] === "^")) {
		chars.push(s[i]);
		i += 1;
	}
	// Handle ] as first char
	if (i < s.length && s[i] === "]") {
		if (_hasBracketClose(s, i + 1, depth)) {
			chars.push(s[i]);
			i += 1;
		}
	}
	// Consume until ]
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
		let alt,
			alternatives,
			ch,
			current,
			depth,
			i,
			parts,
			pattern_str,
			result,
			word_list;
		// bash-oracle format: (pattern ((word "a") (word "b")) body)
		// Split pattern by | respecting escapes, extglobs, quotes, and brackets
		alternatives = [];
		current = [];
		i = 0;
		depth = 0;
		while (i < this.pattern.length) {
			ch = this.pattern[i];
			if (ch === "\\" && i + 1 < this.pattern.length) {
				current.push(this.pattern.slice(i, i + 2));
				i += 2;
			} else if (
				(ch === "@" || ch === "?" || ch === "*" || ch === "+" || ch === "!") &&
				i + 1 < this.pattern.length &&
				this.pattern[i + 1] === "("
			) {
				// Start of extglob: @(, ?(, *(, +(, !(
				current.push(ch);
				current.push("(");
				depth += 1;
				i += 2;
			} else if (
				ch === "$" &&
				i + 1 < this.pattern.length &&
				this.pattern[i + 1] === "("
			) {
				// $( command sub or $(( arithmetic - track depth
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
				result = _consumeBracketClass(this.pattern, i, depth);
				i = result[0];
				current.push(...result[1]);
			} else if (ch === "'" && depth === 0) {
				result = _consumeSingleQuote(this.pattern, i);
				i = result[0];
				current.push(...result[1]);
			} else if (ch === '"' && depth === 0) {
				result = _consumeDoubleQuote(this.pattern, i);
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
		word_list = [];
		for (alt of alternatives) {
			// Use Word.to_sexp() to properly expand ANSI-C quotes and escape
			word_list.push(new Word(alt).toSexp());
		}
		pattern_str = word_list.join(" ");
		parts = [`(pattern (${pattern_str})`];
		if (this.body) {
			parts.push(` ${this.body.toSexp()}`);
		} else {
			parts.push(" ()");
		}
		// bash-oracle doesn't output fallthrough/falltest markers
		parts.push(")");
		return parts.join("");
	}
}

class FunctionNode extends Node {
	constructor(name, body) {
		super();
		this.kind = "function";
		this.name = name;
		this.body = body;
	}

	toSexp() {
		return `(function "${this.name}" ${this.body.toSexp()})`;
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
		let arg_val, escaped_arg, escaped_op, escaped_param;
		escaped_param = this.param.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
		if (this.op != null) {
			escaped_op = this.op.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			if (this.arg != null) {
				arg_val = this.arg;
			} else {
				arg_val = "";
			}
			escaped_arg = arg_val.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			return `(param "${escaped_param}" "${escaped_op}" "${escaped_arg}")`;
		}
		return `(param "${escaped_param}")`;
	}
}

class ParamLength extends Node {
	constructor(param) {
		super();
		this.kind = "param-len";
		this.param = param;
	}

	toSexp() {
		let escaped;
		escaped = this.param.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
		return `(param-len "${escaped}")`;
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
		let arg_val, escaped, escaped_arg, escaped_op;
		escaped = this.param.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
		if (this.op != null) {
			escaped_op = this.op.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			if (this.arg != null) {
				arg_val = this.arg;
			} else {
				arg_val = "";
			}
			escaped_arg = arg_val.replaceAll("\\", "\\\\").replaceAll('"', '\\"');
			return `(param-indirect "${escaped}" "${escaped_op}" "${escaped_arg}")`;
		}
		return `(param-indirect "${escaped}")`;
	}
}

class CommandSubstitution extends Node {
	constructor(command) {
		super();
		this.kind = "cmdsub";
		this.command = command;
	}

	toSexp() {
		return `(cmdsub ${this.command.toSexp()})`;
	}
}

class ArithmeticExpansion extends Node {
	constructor(expression) {
		super();
		this.kind = "arith";
		this.expression = expression;
	}

	toSexp() {
		if (this.expression == null) {
			return "(arith)";
		}
		return `(arith ${this.expression.toSexp()})`;
	}
}

class ArithmeticCommand extends Node {
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
		let escaped, formatted, r, redirect_parts, redirect_sexps, result;
		// bash-oracle format: (arith (word "content"))
		// Redirects are siblings: (arith (word "...")) (redirect ...)
		// Format command substitutions using Word's method
		formatted = new Word(this.raw_content)._formatCommandSubstitutions(
			this.raw_content,
			true,
		);
		escaped = formatted
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n")
			.replaceAll("\t", "\\t");
		result = `(arith (word "${escaped}"))`;
		if (this.redirects && this.redirects.length) {
			redirect_parts = [];
			for (r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			redirect_sexps = redirect_parts.join(" ");
			return `${result} ${redirect_sexps}`;
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
		return `(number "${this.value}")`;
	}
}

class ArithEmpty extends Node {
	constructor() {
		super();
		this.kind = "empty";
	}

	toSexp() {
		return "(empty)";
	}
}

class ArithVar extends Node {
	constructor(name) {
		super();
		this.kind = "var";
		this.name = name;
	}

	toSexp() {
		return `(var "${this.name}")`;
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
		return `(binary-op "${this.op}" ${this.left.toSexp()} ${this.right.toSexp()})`;
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
		return `(unary-op "${this.op}" ${this.operand.toSexp()})`;
	}
}

class ArithPreIncr extends Node {
	constructor(operand) {
		super();
		this.kind = "pre-incr";
		this.operand = operand;
	}

	toSexp() {
		return `(pre-incr ${this.operand.toSexp()})`;
	}
}

class ArithPostIncr extends Node {
	constructor(operand) {
		super();
		this.kind = "post-incr";
		this.operand = operand;
	}

	toSexp() {
		return `(post-incr ${this.operand.toSexp()})`;
	}
}

class ArithPreDecr extends Node {
	constructor(operand) {
		super();
		this.kind = "pre-decr";
		this.operand = operand;
	}

	toSexp() {
		return `(pre-decr ${this.operand.toSexp()})`;
	}
}

class ArithPostDecr extends Node {
	constructor(operand) {
		super();
		this.kind = "post-decr";
		this.operand = operand;
	}

	toSexp() {
		return `(post-decr ${this.operand.toSexp()})`;
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
		return `(assign "${this.op}" ${this.target.toSexp()} ${this.value.toSexp()})`;
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
		return `(ternary ${this.condition.toSexp()} ${this.if_true.toSexp()} ${this.if_false.toSexp()})`;
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
		return `(comma ${this.left.toSexp()} ${this.right.toSexp()})`;
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
		return `(subscript "${this.array}" ${this.index.toSexp()})`;
	}
}

class ArithEscape extends Node {
	constructor(char) {
		super();
		this.kind = "escape";
		this.char = char;
	}

	toSexp() {
		return `(escape "${this.char}")`;
	}
}

class ArithDeprecated extends Node {
	constructor(expression) {
		super();
		this.kind = "arith-deprecated";
		this.expression = expression;
	}

	toSexp() {
		let escaped;
		escaped = this.expression
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n");
		return `(arith-deprecated "${escaped}")`;
	}
}

class ArithConcat extends Node {
	constructor(parts) {
		super();
		this.kind = "arith-concat";
		this.parts = parts;
	}

	toSexp() {
		let p, sexps;
		sexps = [];
		for (p of this.parts) {
			sexps.push(p.toSexp());
		}
		return `(arith-concat ${sexps.join(" ")})`;
	}
}

class AnsiCQuote extends Node {
	constructor(content) {
		super();
		this.kind = "ansi-c";
		this.content = content;
	}

	toSexp() {
		let escaped;
		escaped = this.content
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n");
		return `(ansi-c "${escaped}")`;
	}
}

class LocaleString extends Node {
	constructor(content) {
		super();
		this.kind = "locale";
		this.content = content;
	}

	toSexp() {
		let escaped;
		escaped = this.content
			.replaceAll("\\", "\\\\")
			.replaceAll('"', '\\"')
			.replaceAll("\n", "\\n");
		return `(locale "${escaped}")`;
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
		return `(procsub "${this.direction}" ${this.command.toSexp()})`;
	}
}

class Negation extends Node {
	constructor(pipeline) {
		super();
		this.kind = "negation";
		this.pipeline = pipeline;
	}

	toSexp() {
		if (this.pipeline == null) {
			// Bare "!" with no command - bash-oracle shows empty command
			return "(negation (command))";
		}
		return `(negation ${this.pipeline.toSexp()})`;
	}
}

class Time extends Node {
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
			// Bare "time" with no command - bash-oracle shows empty command
			if (this.posix) {
				return "(time -p (command))";
			} else {
				return "(time (command))";
			}
		}
		if (this.posix) {
			return `(time -p ${this.pipeline.toSexp()})`;
		}
		return `(time ${this.pipeline.toSexp()})`;
	}
}

class ConditionalExpr extends Node {
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
		let body_kind, escaped, r, redirect_parts, redirect_sexps, result;
		// bash-oracle format: (cond ...) not (cond-expr ...)
		// Redirects are siblings, not children: (cond ...) (redirect ...)
		body_kind = this.body.kind ?? null;
		if (body_kind == null) {
			// body is a string
			escaped = this.body
				.replaceAll("\\", "\\\\")
				.replaceAll('"', '\\"')
				.replaceAll("\n", "\\n");
			result = `(cond "${escaped}")`;
		} else {
			result = `(cond ${this.body.toSexp()})`;
		}
		if (this.redirects && this.redirects.length) {
			redirect_parts = [];
			for (r of this.redirects) {
				redirect_parts.push(r.toSexp());
			}
			redirect_sexps = redirect_parts.join(" ");
			return `${result} ${redirect_sexps}`;
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
		let operand_val;
		// bash-oracle format: (cond-unary "-f" (cond-term "file"))
		// cond-term preserves content as-is (no backslash escaping)
		operand_val = this.operand.getCondFormattedValue();
		return `(cond-unary "${this.op}" (cond-term "${operand_val}"))`;
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
		let left_val, right_val;
		// bash-oracle format: (cond-binary "==" (cond-term "x") (cond-term "y"))
		// cond-term preserves content as-is (no backslash escaping)
		left_val = this.left.getCondFormattedValue();
		right_val = this.right.getCondFormattedValue();
		return `(cond-binary "${this.op}" (cond-term "${left_val}") (cond-term "${right_val}"))`;
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
		return `(cond-and ${this.left.toSexp()} ${this.right.toSexp()})`;
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
		return `(cond-or ${this.left.toSexp()} ${this.right.toSexp()})`;
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
		return `(cond-expr ${this.inner.toSexp()})`;
	}
}

class ArrayNode extends Node {
	constructor(elements) {
		super();
		this.kind = "array";
		this.elements = elements;
	}

	toSexp() {
		let e, inner, parts;
		if (!this.elements) {
			return "(array)";
		}
		parts = [];
		for (e of this.elements) {
			parts.push(e.toSexp());
		}
		inner = parts.join(" ");
		return `(array ${inner})`;
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
		let name;
		// Use provided name for compound commands, "COPROC" for simple commands
		if (this.name) {
			name = this.name;
		} else {
			name = "COPROC";
		}
		return `(coproc "${name}" ${this.command.toSexp()})`;
	}
}

function _formatCondBody(node) {
	let kind, left_val, operand_val, right_val;
	kind = node.kind;
	if (kind === "unary-test") {
		operand_val = node.operand.getCondFormattedValue();
		return `${node.op} ${operand_val}`;
	}
	if (kind === "binary-test") {
		left_val = node.left.getCondFormattedValue();
		right_val = node.right.getCondFormattedValue();
		return `${left_val} ${node.op} ${right_val}`;
	}
	if (kind === "cond-and") {
		return `${_formatCondBody(node.left)} && ${_formatCondBody(node.right)}`;
	}
	if (kind === "cond-or") {
		return `${_formatCondBody(node.left)} || ${_formatCondBody(node.right)}`;
	}
	if (kind === "cond-not") {
		return `! ${_formatCondBody(node.operand)}`;
	}
	if (kind === "cond-paren") {
		return `( ${_formatCondBody(node.body)} )`;
	}
	return "";
}

function _startsWithSubshell(node) {
	let p;
	if (node.kind === "subshell") {
		return true;
	}
	if (node.kind === "list") {
		for (p of node.parts) {
			if (p.kind !== "operator") {
				return _startsWithSubshell(p);
			}
		}
		return false;
	}
	if (node.kind === "pipeline") {
		if (node.commands && node.commands.length) {
			return _startsWithSubshell(node.commands[0]);
		}
		return false;
	}
	return false;
}

function _formatCmdsubNode(
	node,
	indent,
	in_procsub,
	compact_redirects,
	procsub_first,
) {
	let body,
		body_part,
		cmd,
		cmd_count,
		cmds,
		compact_pipe,
		cond,
		else_body,
		first_nl,
		formatted,
		formatted_cmd,
		h,
		has_heredoc,
		heredocs,
		i,
		idx,
		inner_body,
		inner_sp,
		is_last,
		last,
		name,
		needs_redirect,
		p,
		part,
		parts,
		pat,
		pat_indent,
		pattern_str,
		patterns,
		prefix,
		r,
		redirect_parts,
		redirects,
		result,
		result_parts,
		s,
		skipped_semi,
		sp,
		term,
		term_indent,
		terminator,
		then_body,
		val,
		variable,
		w,
		word,
		word_parts,
		word_vals,
		words;
	if (indent == null) {
		indent = 0;
	}
	if (in_procsub == null) {
		in_procsub = false;
	}
	if (compact_redirects == null) {
		compact_redirects = false;
	}
	if (procsub_first == null) {
		procsub_first = false;
	}
	if (node == null) {
		return "";
	}
	sp = " ".repeat(indent);
	inner_sp = " ".repeat(indent + 4);
	if (node.kind === "empty") {
		return "";
	}
	if (node.kind === "command") {
		parts = [];
		for (w of node.words) {
			val = w._expandAllAnsiCQuotes(w.value);
			// Strip $ from locale strings $"..." (quote-aware)
			val = w._stripLocaleStringDollars(val);
			val = w._formatCommandSubstitutions(val);
			parts.push(val);
		}
		// Check for heredocs - their bodies need to come at the end
		heredocs = [];
		for (r of node.redirects) {
			if (r.kind === "heredoc") {
				heredocs.push(r);
			}
		}
		for (r of node.redirects) {
			// For heredocs, output just the operator part; body comes at end
			parts.push(_formatRedirect(r, compact_redirects, true));
		}
		// In compact mode with words, don't add space before redirects
		if (compact_redirects && node.words && node.redirects) {
			word_parts = parts.slice(0, node.words.length);
			redirect_parts = parts.slice(node.words.length);
			result = word_parts.join(" ") + redirect_parts.join("");
		} else {
			result = parts.join(" ");
		}
		// Append heredoc bodies at the end
		for (h of heredocs) {
			result = result + _formatHeredocBody(h);
		}
		return result;
	}
	if (node.kind === "pipeline") {
		// Build list of (cmd, needs_pipe_both_redirect) filtering out PipeBoth markers
		cmds = [];
		i = 0;
		while (i < node.commands.length) {
			cmd = node.commands[i];
			if (cmd.kind === "pipe-both") {
				i += 1;
				continue;
			}
			// Check if next element is PipeBoth
			needs_redirect =
				i + 1 < node.commands.length &&
				node.commands[i + 1].kind === "pipe-both";
			cmds.push([cmd, needs_redirect]);
			i += 1;
		}
		// Format pipeline, handling heredocs specially
		result_parts = [];
		idx = 0;
		while (idx < cmds.length) {
			[cmd, needs_redirect] = cmds[idx];
			// Only first command in pipeline inherits procsub_first
			formatted = _formatCmdsubNode(
				cmd,
				indent,
				in_procsub,
				false,
				procsub_first && idx === 0,
			);
			if (needs_redirect) {
				formatted = `${formatted} 2>&1`;
			}
			is_last = idx === cmds.length - 1;
			// Check if command has actual heredoc redirects
			has_heredoc = false;
			if (cmd.kind === "command" && cmd.redirects) {
				for (r of cmd.redirects) {
					if (r.kind === "heredoc") {
						has_heredoc = true;
						break;
					}
				}
			}
			if (!is_last && has_heredoc) {
				// Heredoc present - insert pipe after heredoc delimiter, before content
				// Pattern: "... <<DELIM\ncontent\nDELIM\n" -> "... <<DELIM |\ncontent\nDELIM\n"
				first_nl = formatted.indexOf("\n");
				if (first_nl !== -1) {
					formatted = `${formatted.slice(0, first_nl)} |${formatted.slice(first_nl)}`;
				}
				result_parts.push(formatted);
			} else {
				result_parts.push(formatted);
			}
			idx += 1;
		}
		// Join with " | " for commands without heredocs, or just join if heredocs handled
		// In procsub, if first command is subshell, use compact "|" separator
		compact_pipe = in_procsub && cmds && cmds[0][0].kind === "subshell";
		result = "";
		idx = 0;
		while (idx < result_parts.length) {
			part = result_parts[idx];
			if (idx > 0) {
				// If previous part ends with heredoc (newline), add indented command
				if (result.endsWith("\n")) {
					result = `${result}  ${part}`;
				} else if (compact_pipe) {
					result = `${result}|${part}`;
				} else {
					result = `${result} | ${part}`;
				}
			} else {
				result = part;
			}
			idx += 1;
		}
		return result;
	}
	if (node.kind === "list") {
		// Check if any command in the list has a heredoc redirect
		has_heredoc = false;
		for (p of node.parts) {
			if (p.kind === "command" && p.redirects) {
				for (r of p.redirects) {
					if (r.kind === "heredoc") {
						has_heredoc = true;
						break;
					}
				}
			} else if (p.kind === "pipeline") {
				// Check commands within the pipeline
				for (cmd of p.commands) {
					if (cmd.kind === "command" && cmd.redirects) {
						for (r of cmd.redirects) {
							if (r.kind === "heredoc") {
								has_heredoc = true;
								break;
							}
						}
					}
					if (has_heredoc) {
						break;
					}
				}
			}
		}
		// Join commands with operators
		result = [];
		skipped_semi = false;
		cmd_count = 0;
		for (p of node.parts) {
			if (p.kind === "operator") {
				if (p.op === ";") {
					// Skip semicolon if previous command ends with heredoc (newline)
					if (result.length > 0 && result[result.length - 1].endsWith("\n")) {
						skipped_semi = true;
						continue;
					}
					result.push(";");
					skipped_semi = false;
				} else if (p.op === "\n") {
					// Skip newline if it follows a semicolon (redundant separator)
					if (result.length > 0 && result[result.length - 1] === ";") {
						skipped_semi = false;
						continue;
					}
					// If previous ends with heredoc newline
					if (result.length > 0 && result[result.length - 1].endsWith("\n")) {
						// Add space if semicolon was skipped, else newline
						result.push(skipped_semi ? " " : "\n");
						skipped_semi = false;
						continue;
					}
					result.push("\n");
					skipped_semi = false;
				} else if (p.op === "&") {
					// If previous command has heredoc, insert & before heredoc content
					if (
						result.length > 0 &&
						result[result.length - 1].includes("<<") &&
						result[result.length - 1].includes("\n")
					) {
						last = result[result.length - 1];
						first_nl = last.indexOf("\n");
						result[result.length - 1] =
							`${last.slice(0, first_nl)} &${last.slice(first_nl)}`;
					} else {
						result.push(" &");
					}
				} else if (
					result.length > 0 &&
					result[result.length - 1].includes("<<") &&
					result[result.length - 1].includes("\n")
				) {
					// For || and &&, insert before heredoc content like we do for &
					last = result[result.length - 1];
					first_nl = last.indexOf("\n");
					result[result.length - 1] =
						`${last.slice(0, first_nl)} ${p.op} ${last.slice(first_nl)}`;
				} else {
					result.push(` ${p.op}`);
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
				// Only first command in list inherits procsub_first
				formatted_cmd = _formatCmdsubNode(
					p,
					indent,
					in_procsub,
					compact_redirects,
					procsub_first && cmd_count === 0,
				);
				// After heredoc with || or && inserted, add leading space to next command
				if (result.length > 0) {
					last = result[result.length - 1];
					if (last.includes(" || \n") || last.includes(" && \n")) {
						formatted_cmd = ` ${formatted_cmd}`;
					}
				}
				// When semicolon was skipped due to heredoc, add leading space
				if (skipped_semi) {
					formatted_cmd = ` ${formatted_cmd}`;
					skipped_semi = false;
				}
				result.push(formatted_cmd);
				cmd_count += 1;
			}
		}
		// Strip trailing ; or newline (but preserve heredoc's trailing newline)
		s = result.join("");
		// If we have & with heredoc (& before newline content), preserve trailing newline and add space
		if (s.includes(" &\n") && s.endsWith("\n")) {
			return `${s} `;
		}
		while (s.endsWith(";")) {
			s = s.slice(0, s.length - 1);
		}
		if (!has_heredoc) {
			while (s.endsWith("\n")) {
				s = s.slice(0, s.length - 1);
			}
		}
		return s;
	}
	if (node.kind === "if") {
		cond = _formatCmdsubNode(node.condition, indent);
		then_body = _formatCmdsubNode(node.then_body, indent + 4);
		result = `if ${cond}; then\n${inner_sp}${then_body};`;
		if (node.else_body) {
			else_body = _formatCmdsubNode(node.else_body, indent + 4);
			result = `${result}\n${sp}else\n${inner_sp}${else_body};`;
		}
		result = `${result}\n${sp}fi`;
		return result;
	}
	if (node.kind === "while") {
		cond = _formatCmdsubNode(node.condition, indent);
		body = _formatCmdsubNode(node.body, indent + 4);
		result = `while ${cond}; do\n${inner_sp}${body};\n${sp}done`;
		if (node.redirects && node.redirects.length) {
			for (r of node.redirects) {
				result = `${result} ${_formatRedirect(r)}`;
			}
		}
		return result;
	}
	if (node.kind === "until") {
		cond = _formatCmdsubNode(node.condition, indent);
		body = _formatCmdsubNode(node.body, indent + 4);
		result = `until ${cond}; do\n${inner_sp}${body};\n${sp}done`;
		if (node.redirects && node.redirects.length) {
			for (r of node.redirects) {
				result = `${result} ${_formatRedirect(r)}`;
			}
		}
		return result;
	}
	if (node.kind === "for") {
		variable = node.variable;
		body = _formatCmdsubNode(node.body, indent + 4);
		if (node.words && node.words.length) {
			word_vals = [];
			for (w of node.words) {
				word_vals.push(w.value);
			}
			words = word_vals.join(" ");
			result = `for ${variable} in ${words};\n${sp}do\n${inner_sp}${body};\n${sp}done`;
		} else {
			result = `for ${variable};\n${sp}do\n${inner_sp}${body};\n${sp}done`;
		}
		if (node.redirects && node.redirects.length) {
			for (r of node.redirects) {
				result = `${result} ${_formatRedirect(r)}`;
			}
		}
		return result;
	}
	if (node.kind === "for-arith") {
		body = _formatCmdsubNode(node.body, indent + 4);
		result = `for ((${node.init}; ${node.cond}; ${node.incr}))\ndo\n${inner_sp}${body};\n${sp}done`;
		if (node.redirects && node.redirects.length) {
			for (r of node.redirects) {
				result = `${result} ${_formatRedirect(r)}`;
			}
		}
		return result;
	}
	if (node.kind === "case") {
		word = node.word.value;
		patterns = [];
		i = 0;
		while (i < node.patterns.length) {
			p = node.patterns[i];
			pat = p.pattern.replaceAll("|", " | ");
			if (p.body) {
				body = _formatCmdsubNode(p.body, indent + 8);
			} else {
				body = "";
			}
			term = p.terminator;
			pat_indent = " ".repeat(indent + 8);
			term_indent = " ".repeat(indent + 4);
			body_part = body ? `${pat_indent + body}\n` : "\n";
			if (i === 0) {
				// First pattern on same line as 'in'
				patterns.push(` ${pat})\n${body_part}${term_indent}${term}`);
			} else {
				patterns.push(`${pat})\n${body_part}${term_indent}${term}`);
			}
			i += 1;
		}
		pattern_str = patterns.join(`\n${" ".repeat(indent + 4)}`);
		redirects = "";
		if (node.redirects && node.redirects.length) {
			redirect_parts = [];
			for (r of node.redirects) {
				redirect_parts.push(_formatRedirect(r));
			}
			redirects = ` ${redirect_parts.join(" ")}`;
		}
		return `case ${word} in${pattern_str}\n${sp}esac${redirects}`;
	}
	if (node.kind === "function") {
		name = node.name;
		// Get the body content - if it's a BraceGroup, unwrap it
		inner_body = node.body.kind === "brace-group" ? node.body.body : node.body;
		body = _formatCmdsubNode(inner_body, indent + 4).replace(/[;]+$/, "");
		return `function ${name} () \n{ \n${inner_sp}${body}\n}`;
	}
	if (node.kind === "subshell") {
		body = _formatCmdsubNode(node.body, indent, in_procsub, compact_redirects);
		redirects = "";
		if (node.redirects && node.redirects.length) {
			redirect_parts = [];
			for (r of node.redirects) {
				redirect_parts.push(_formatRedirect(r));
			}
			redirects = redirect_parts.join(" ");
		}
		// Use compact format only when subshell is at the start of a procsub
		if (procsub_first) {
			if (redirects && redirects.length) {
				return `(${body}) ${redirects}`;
			}
			return `(${body})`;
		}
		if (redirects && redirects.length) {
			return `( ${body} ) ${redirects}`;
		}
		return `( ${body} )`;
	}
	if (node.kind === "brace-group") {
		body = _formatCmdsubNode(node.body, indent);
		body = body.replace(/[;]+$/, "");
		// Don't add semicolon after background operator
		terminator = body.endsWith(" &") ? " }" : "; }";
		redirects = "";
		if (node.redirects && node.redirects.length) {
			redirect_parts = [];
			for (r of node.redirects) {
				redirect_parts.push(_formatRedirect(r));
			}
			redirects = redirect_parts.join(" ");
		}
		if (redirects && redirects.length) {
			return `{ ${body}${terminator} ${redirects}`;
		}
		return `{ ${body}${terminator}`;
	}
	if (node.kind === "arith-cmd") {
		return `((${node.raw_content}))`;
	}
	if (node.kind === "cond-expr") {
		body = _formatCondBody(node.body);
		return `[[ ${body} ]]`;
	}
	if (node.kind === "negation") {
		if (node.pipeline) {
			return `! ${_formatCmdsubNode(node.pipeline, indent)}`;
		}
		return "! ";
	}
	if (node.kind === "time") {
		prefix = node.posix ? "time -p " : "time ";
		if (node.pipeline) {
			return prefix + _formatCmdsubNode(node.pipeline, indent);
		}
		return prefix;
	}
	// Fallback: return empty for unknown types
	return "";
}

function _formatRedirect(r, compact, heredoc_op_only) {
	let after_amp, delim, is_literal_fd, op, target, was_input_close;
	if (compact == null) {
		compact = false;
	}
	if (heredoc_op_only == null) {
		heredoc_op_only = false;
	}
	if (r.kind === "heredoc") {
		if (r.strip_tabs) {
			op = "<<-";
		} else {
			op = "<<";
		}
		if (r.fd != null && r.fd !== 0) {
			op = String(r.fd) + op;
		}
		if (r.quoted) {
			delim = `'${r.delimiter}'`;
		} else {
			delim = r.delimiter;
		}
		if (heredoc_op_only) {
			// Just the operator part (<<DELIM), body comes separately
			return op + delim;
		}
		// Include heredoc content: <<DELIM\ncontent\nDELIM\n
		return `${op + delim}\n${r.content}${r.delimiter}\n`;
	}
	op = r.op;
	// Normalize default fd: 1> -> >, 0< -> <
	if (op === "1>") {
		op = ">";
	} else if (op === "0<") {
		op = "<";
	}
	target = r.target.value;
	// Expand ANSI-C $'...' quotes
	target = r.target._expandAllAnsiCQuotes(target);
	// Strip $ from locale strings $"..."
	target = r.target._stripLocaleStringDollars(target);
	// Format command/process substitutions
	target = r.target._formatCommandSubstitutions(target);
	// For fd duplication (target starts with &), handle normalization
	if (target.startsWith("&")) {
		// Normalize N<&- to N>&- (close always uses >)
		was_input_close = false;
		if (target === "&-" && op.endsWith("<")) {
			was_input_close = true;
			op = `${op.slice(0, op.length - 1)}>`;
		}
		// Check if target is a literal fd (digit or -)
		after_amp = target.slice(1, target.length);
		is_literal_fd =
			after_amp === "-" ||
			(after_amp.length > 0 && /^[0-9]+$/.test(after_amp[0]));
		if (is_literal_fd) {
			// Add default fd for bare >&N or <&N
			if (op === ">") {
				// If we normalized from <&-, use fd 0 (stdin), otherwise fd 1 (stdout)
				op = was_input_close ? "0>" : "1>";
			} else if (op === "<") {
				op = "0<";
			}
		} else if (op === "1>") {
			// Variable target: use bare >& or <&
			op = ">";
		} else if (op === "0<") {
			op = "<";
		}
		return op + target;
	}
	// For >& and <& (fd dup operators), no space before target
	if (op.endsWith("&")) {
		return op + target;
	}
	if (compact) {
		return op + target;
	}
	return `${op} ${target}`;
}

function _formatHeredocBody(r) {
	return `\n${r.content}${r.delimiter}\n`;
}

function _normalizeFdRedirects(s) {
	let i, prev_is_digit, prev_is_same_op, result;
	// Match >&N or <&N not preceded by a digit, add default fd
	result = [];
	i = 0;
	while (i < s.length) {
		// Check for >&N or <&N
		if (i + 2 < s.length && s[i + 1] === "&" && /^[0-9]+$/.test(s[i + 2])) {
			prev_is_digit = i > 0 && /^[0-9]+$/.test(s[i - 1]);
			prev_is_same_op = i > 0 && s[i - 1] === s[i];
			if (s[i] === ">" && !prev_is_digit && !prev_is_same_op) {
				result.push("1>&");
				result.push(s[i + 2]);
				i += 3;
				continue;
			} else if (s[i] === "<" && !prev_is_digit && !prev_is_same_op) {
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

function _findCmdsubEnd(value, start) {
	let arith_depth,
		arith_paren_depth,
		c,
		case_depth,
		depth,
		found_esac,
		i,
		in_case_patterns,
		in_double,
		in_single,
		is_valid_arith,
		j,
		lookahead_c,
		lookahead_case_depth,
		lookahead_i,
		quote,
		scan_c,
		scan_i,
		scan_paren;
	depth = 1;
	i = start;
	in_single = false;
	in_double = false;
	case_depth = 0;
	in_case_patterns = false;
	arith_depth = 0;
	arith_paren_depth = 0;
	while (i < value.length && depth > 0) {
		c = value[i];
		// Handle escapes
		if (c === "\\" && i + 1 < value.length && !in_single) {
			i += 2;
			continue;
		}
		// Handle quotes
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
			// Inside double quotes, $() command substitution is still active
			if (_startsWithAt(value, i, "$(") && !_startsWithAt(value, i, "$((")) {
				// Recursively find end of nested command substitution
				j = _findCmdsubEnd(value, i + 2);
				i = j;
				continue;
			}
			// Skip other characters inside double quotes
			i += 1;
			continue;
		}
		// Handle comments - skip from # to end of line
		// Only treat # as comment if preceded by whitespace or at start
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
		// Handle here-strings (<<< word) - must check before heredocs
		if (_startsWithAt(value, i, "<<<")) {
			i += 3;
			// Skip whitespace
			while (i < value.length && (value[i] === " " || value[i] === "\t")) {
				i += 1;
			}
			// Skip the word (may be quoted)
			if (i < value.length && value[i] === '"') {
				i += 1;
				while (i < value.length && value[i] !== '"') {
					if (value[i] === "\\" && i + 1 < value.length) {
						i += 2;
					} else {
						i += 1;
					}
				}
				if (i < value.length) {
					i += 1;
				}
			} else if (i < value.length && value[i] === "'") {
				i += 1;
				while (i < value.length && value[i] !== "'") {
					i += 1;
				}
				if (i < value.length) {
					i += 1;
				}
			} else {
				// Unquoted word - skip until whitespace or special char
				while (i < value.length && !" \t\n;|&<>()".includes(value[i])) {
					i += 1;
				}
			}
			continue;
		}
		// Handle arithmetic expressions $((
		// Check for valid arithmetic by scanning for closing )) at top level
		if (_startsWithAt(value, i, "$((")) {
			is_valid_arith = true;
			scan_paren = 0;
			scan_i = i + 3;
			while (scan_i < value.length) {
				scan_c = value[scan_i];
				// Skip over $( command subs - their parens shouldn't count
				if (
					scan_c === "$" &&
					scan_i + 1 < value.length &&
					value[scan_i + 1] === "("
				) {
					scan_i = _findCmdsubEnd(value, scan_i + 2);
					continue;
				}
				if (scan_c === "(") {
					scan_paren += 1;
				} else if (scan_c === ")") {
					if (scan_paren > 0) {
						scan_paren -= 1;
					} else if (scan_i + 1 < value.length && value[scan_i + 1] === ")") {
						break;
					} else {
						// Single ) at top level without following ) - not valid arithmetic
						is_valid_arith = false;
						break;
					}
				}
				scan_i += 1;
			}
			if (is_valid_arith) {
				arith_depth += 1;
				i += 3;
				continue;
			}
			// else: not valid arithmetic, treat $( as nested cmdsub and ( as paren
			j = _findCmdsubEnd(value, i + 2);
			i = j;
			continue;
		}
		// Handle arithmetic close )) - only when no inner grouping parens are open
		if (
			arith_depth > 0 &&
			arith_paren_depth === 0 &&
			_startsWithAt(value, i, "))")
		) {
			arith_depth -= 1;
			i += 2;
			continue;
		}
		// Handle heredocs (but not << inside arithmetic, which is shift operator)
		if (arith_depth === 0 && _startsWithAt(value, i, "<<")) {
			i = _skipHeredoc(value, i);
			continue;
		}
		// Check for 'case' keyword
		if (_startsWithAt(value, i, "case") && _isWordBoundary(value, i, 4)) {
			case_depth += 1;
			in_case_patterns = false;
			i += 4;
			continue;
		}
		// Check for 'in' keyword (after case)
		if (
			case_depth > 0 &&
			_startsWithAt(value, i, "in") &&
			_isWordBoundary(value, i, 2)
		) {
			in_case_patterns = true;
			i += 2;
			continue;
		}
		// Check for 'esac' keyword
		if (_startsWithAt(value, i, "esac") && _isWordBoundary(value, i, 4)) {
			if (case_depth > 0) {
				case_depth -= 1;
				in_case_patterns = false;
			}
			i += 4;
			continue;
		}
		// Check for ';;' (end of case pattern, next pattern or esac follows)
		if (_startsWithAt(value, i, ";;")) {
			i += 2;
			continue;
		}
		// Handle parens
		if (c === "(") {
			// In case patterns, ( before pattern name is optional and not a grouping paren
			if (!(in_case_patterns && case_depth > 0)) {
				if (arith_depth > 0) {
					arith_paren_depth += 1;
				} else {
					depth += 1;
				}
			}
		} else if (c === ")") {
			// In case patterns, ) after pattern name is not a grouping paren
			if (in_case_patterns && case_depth > 0 && depth > 1) {
				// This might be a case pattern terminator, but check if there's an esac
				// If we're at depth 1 (outermost level), this ) might close the cmdsub
				// Do lookahead to find if there's an esac for this case
				lookahead_i = i + 1;
				lookahead_case_depth = case_depth;
				found_esac = false;
				while (lookahead_i < value.length) {
					lookahead_c = value[lookahead_i];
					if (lookahead_c === "'" || lookahead_c === '"') {
						// Skip quoted strings in lookahead
						quote = lookahead_c;
						lookahead_i += 1;
						while (lookahead_i < value.length && value[lookahead_i] !== quote) {
							if (lookahead_c === '"' && value[lookahead_i] === "\\") {
								lookahead_i += 1;
							}
							lookahead_i += 1;
						}
						if (lookahead_i < value.length) {
							lookahead_i += 1;
						}
					} else if (
						_startsWithAt(value, lookahead_i, "case") &&
						_isWordBoundary(value, lookahead_i, 4)
					) {
						lookahead_case_depth += 1;
						lookahead_i += 4;
					} else if (
						_startsWithAt(value, lookahead_i, "esac") &&
						_isWordBoundary(value, lookahead_i, 4)
					) {
						lookahead_case_depth -= 1;
						if (lookahead_case_depth === 0) {
							found_esac = true;
							break;
						}
						lookahead_i += 4;
					} else if (lookahead_c === "(") {
						lookahead_i += 1;
					} else if (lookahead_c === ")") {
						// Hit another ) before finding esac - stop lookahead
						if (lookahead_case_depth > 0) {
							lookahead_i += 1;
						} else {
							break;
						}
					} else {
						lookahead_i += 1;
					}
				}
				if (found_esac) {
					// This ) is a case pattern terminator, skip it
				} else {
					// No esac found, this ) closes the command substitution
					depth -= 1;
				}
			} else if (in_case_patterns && case_depth > 0) {
				// At depth 1, check for esac (same lookahead logic)
				// If no esac, this ) closes the cmdsub
				lookahead_i = i + 1;
				lookahead_case_depth = case_depth;
				found_esac = false;
				while (lookahead_i < value.length) {
					lookahead_c = value[lookahead_i];
					if (lookahead_c === "'" || lookahead_c === '"') {
						quote = lookahead_c;
						lookahead_i += 1;
						while (lookahead_i < value.length && value[lookahead_i] !== quote) {
							if (lookahead_c === '"' && value[lookahead_i] === "\\") {
								lookahead_i += 1;
							}
							lookahead_i += 1;
						}
						if (lookahead_i < value.length) {
							lookahead_i += 1;
						}
					} else if (
						_startsWithAt(value, lookahead_i, "case") &&
						_isWordBoundary(value, lookahead_i, 4)
					) {
						lookahead_case_depth += 1;
						lookahead_i += 4;
					} else if (
						_startsWithAt(value, lookahead_i, "esac") &&
						_isWordBoundary(value, lookahead_i, 4)
					) {
						lookahead_case_depth -= 1;
						if (lookahead_case_depth === 0) {
							found_esac = true;
							break;
						}
						lookahead_i += 4;
					} else if (lookahead_c === ")") {
						// Hit another ) before finding esac - stop lookahead
						if (lookahead_case_depth > 0) {
							lookahead_i += 1;
						} else {
							break;
						}
					} else {
						lookahead_i += 1;
					}
				}
				if (found_esac) {
					// This ) is a case pattern terminator, skip it
				} else {
					// No esac found, this ) closes the command substitution
					depth -= 1;
				}
			} else if (arith_depth > 0) {
				if (arith_paren_depth > 0) {
					arith_paren_depth -= 1;
				}
			} else {
				// else: single ) in arithmetic without matching ( - skip it
				depth -= 1;
			}
		}
		i += 1;
	}
	return i;
}

function _skipHeredoc(value, start) {
	let delim_start,
		delimiter,
		i,
		j,
		line,
		line_end,
		line_start,
		next_line_start,
		paren_depth,
		quote_char,
		stripped,
		tabs_stripped,
		trailing_bs;
	i = start + 2;
	// Handle <<- (strip tabs)
	if (i < value.length && value[i] === "-") {
		i += 1;
	}
	// Skip whitespace before delimiter
	while (i < value.length && _isWhitespaceNoNewline(value[i])) {
		i += 1;
	}
	// Extract delimiter - may be quoted
	delim_start = i;
	quote_char = null;
	if (i < value.length && (value[i] === '"' || value[i] === "'")) {
		quote_char = value[i];
		i += 1;
		delim_start = i;
		while (i < value.length && value[i] !== quote_char) {
			i += 1;
		}
		delimiter = value.slice(delim_start, i);
		if (i < value.length) {
			i += 1;
		}
	} else if (i < value.length && value[i] === "\\") {
		// Backslash-quoted delimiter like <<\EOF
		i += 1;
		delim_start = i;
		if (i < value.length) {
			i += 1;
		}
		while (i < value.length && !_isMetachar(value[i])) {
			i += 1;
		}
		delimiter = value.slice(delim_start, i);
	} else {
		// Unquoted delimiter - stop at metacharacters like )
		while (i < value.length && !_isMetachar(value[i])) {
			i += 1;
		}
		delimiter = value.slice(delim_start, i);
	}
	// Skip to end of line (heredoc content starts on next line)
	// But track paren depth - if we hit a ) at depth 0, it closes the cmdsub
	// Must handle quotes and backticks since newlines in them don't end the line
	paren_depth = 0;
	while (i < value.length && value[i] !== "\n") {
		if (value[i] === "(") {
			paren_depth += 1;
		} else if (value[i] === ")") {
			if (paren_depth === 0) {
				// This ) closes the enclosing command substitution, stop here
				break;
			}
			paren_depth -= 1;
		} else if (value[i] === "'") {
			// Single-quoted string - skip to closing quote
			i += 1;
			while (i < value.length && value[i] !== "'") {
				i += 1;
			}
		} else if (value[i] === '"') {
			// Double-quoted string - skip to closing quote (with escapes)
			i += 1;
			while (i < value.length && value[i] !== '"') {
				if (value[i] === "\\" && i + 1 < value.length) {
					i += 2;
				} else {
					i += 1;
				}
			}
		} else if (value[i] === "`") {
			// Backtick command substitution - skip to closing backtick
			i += 1;
			while (i < value.length && value[i] !== "`") {
				if (value[i] === "\\" && i + 1 < value.length) {
					i += 2;
				} else {
					i += 1;
				}
			}
		}
		i += 1;
	}
	// If we stopped at ) (closing cmdsub), return here - no heredoc content
	if (i < value.length && value[i] === ")") {
		return i;
	}
	if (i < value.length && value[i] === "\n") {
		i += 1;
	}
	// Find the end delimiter on its own line
	while (i < value.length) {
		line_start = i;
		// Find end of this line - heredoc content can contain )
		line_end = i;
		while (line_end < value.length && value[line_end] !== "\n") {
			line_end += 1;
		}
		line = value.slice(line_start, line_end);
		// Handle backslash-newline continuation (join continued lines)
		while (line_end < value.length) {
			trailing_bs = 0;
			for (j = line.length - 1; j > -1; j--) {
				if (line[j] === "\\") {
					trailing_bs += 1;
				} else {
					break;
				}
			}
			if (trailing_bs % 2 === 0) {
				break;
			}
			// Odd backslashes - line continuation
			line = line.slice(0, -1);
			line_end += 1;
			next_line_start = line_end;
			while (line_end < value.length && value[line_end] !== "\n") {
				line_end += 1;
			}
			line = line + value.slice(next_line_start, line_end);
		}
		// Check if this line is the delimiter (possibly with leading tabs for <<-)
		if (start + 2 < value.length && value[start + 2] === "-") {
			stripped = line.replace(/^[\t]+/, "");
		} else {
			stripped = line;
		}
		if (stripped === delimiter) {
			// Found end - return position after delimiter line
			if (line_end < value.length) {
				return line_end + 1;
			} else {
				return line_end;
			}
		}
		// Check if line starts with delimiter followed by other content
		// This handles cases like "Xb)" where X is delimiter and b) continues the cmdsub
		if (stripped.startsWith(delimiter) && stripped.length > delimiter.length) {
			// Return position right after the delimiter
			tabs_stripped = line.length - stripped.length;
			return line_start + tabs_stripped + delimiter.length;
		}
		if (line_end < value.length) {
			i = line_end + 1;
		} else {
			i = line_end;
		}
	}
	return i;
}

function _extractHeredocDelimiters(content) {
	let delim_start, delimiters, i, quote, strip_tabs;
	delimiters = [];
	i = 0;
	while (i < content.length) {
		if (content[i] === "'") {
			i += 1;
			while (i < content.length && content[i] !== "'") {
				i += 1;
			}
			if (i < content.length) {
				i += 1;
			}
			continue;
		}
		if (content[i] === '"') {
			i += 1;
			while (i < content.length && content[i] !== '"') {
				if (content[i] === "\\" && i + 1 < content.length) {
					i += 2;
					continue;
				}
				i += 1;
			}
			if (i < content.length) {
				i += 1;
			}
			continue;
		}
		if (
			content[i] === "<" &&
			i + 1 < content.length &&
			content[i + 1] === "<"
		) {
			i += 2;
			strip_tabs = false;
			if (i < content.length && content[i] === "-") {
				strip_tabs = true;
				i += 1;
			}
			while (i < content.length && _isWhitespaceNoNewline(content[i])) {
				i += 1;
			}
			if (i < content.length && (content[i] === '"' || content[i] === "'")) {
				quote = content[i];
				i += 1;
				delim_start = i;
				while (i < content.length && content[i] !== quote) {
					i += 1;
				}
				delimiters.push([content.slice(delim_start, i), strip_tabs]);
				if (i < content.length) {
					i += 1;
				}
			} else if (i < content.length && content[i] === "\\") {
				i += 1;
				delim_start = i;
				while (i < content.length && !_isWhitespace(content[i])) {
					i += 1;
				}
				delimiters.push([content.slice(delim_start, i), strip_tabs]);
			} else {
				delim_start = i;
				while (i < content.length && !_isMetachar(content[i])) {
					i += 1;
				}
				delimiters.push([content.slice(delim_start, i), strip_tabs]);
			}
			continue;
		}
		i += 1;
	}
	return delimiters;
}

function _findHeredocContentEnd(source, start, delimiters) {
	let content_start,
		delimiter,
		line,
		line_end,
		line_start,
		line_stripped,
		pos,
		strip_tabs;
	if (!delimiters) {
		return [start, start];
	}
	pos = start;
	// Skip to end of current line (including non-whitespace)
	while (pos < source.length && source[pos] !== "\n") {
		pos += 1;
	}
	if (pos >= source.length) {
		return [start, start];
	}
	content_start = pos;
	pos += 1;
	for ([delimiter, strip_tabs] of delimiters) {
		while (pos < source.length) {
			line_start = pos;
			line_end = pos;
			while (line_end < source.length && source[line_end] !== "\n") {
				line_end += 1;
			}
			line = source.slice(line_start, line_end);
			if (strip_tabs) {
				line_stripped = line.replace(/^[\t]+/, "");
			} else {
				line_stripped = line;
			}
			if (line_stripped === delimiter) {
				pos = line_end < source.length ? line_end + 1 : line_end;
				break;
			}
			pos = line_end < source.length ? line_end + 1 : line_end;
		}
	}
	return [content_start, pos];
}

function _isWordBoundary(s, pos, word_len) {
	let end;
	// Check character before
	if (pos > 0 && /^[a-zA-Z0-9]$/.test(s[pos - 1])) {
		return false;
	}
	// Check character after
	end = pos + word_len;
	if (end < s.length && /^[a-zA-Z0-9]$/.test(s[end])) {
		return false;
	}
	return true;
}

// Reserved words that cannot be command names
const RESERVED_WORDS = new Set([
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
// Metacharacters that break words (unquoted)
// Note: {} are NOT metacharacters - they're only special at command position
// for brace groups. In words like {a,b,c}, braces are literal.
const COND_UNARY_OPS = new Set([
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
const COND_BINARY_OPS = new Set([
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
const COMPOUND_KEYWORDS = new Set([
	"while",
	"until",
	"for",
	"if",
	"case",
	"select",
]);
function _isQuote(c) {
	return c === "'" || c === '"';
}

function _isMetachar(c) {
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

function _isExtglobPrefix(c) {
	return c === "@" || c === "?" || c === "*" || c === "+" || c === "!";
}

function _isRedirectChar(c) {
	return c === "<" || c === ">";
}

function _isSpecialParam(c) {
	return (
		c === "?" ||
		c === "$" ||
		c === "!" ||
		c === "#" ||
		c === "@" ||
		c === "*" ||
		c === "-" ||
		c === "&"
	);
}

function _isSpecialParamUnbraced(c) {
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

function _isDigit(c) {
	return c >= "0" && c <= "9";
}

function _isSemicolonOrNewline(c) {
	return c === ";" || c === "\n";
}

function _isRightBracket(c) {
	return c === ")" || c === "}";
}

function _isWordStartContext(c) {
	return (
		c === " " ||
		c === "\t" ||
		c === "\n" ||
		c === ";" ||
		c === "|" ||
		c === "&" ||
		c === "<" ||
		c === "(" ||
		c === "{"
	);
}

function _isWordEndContext(c) {
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

function _isArrayAssignmentPrefix(chars) {
	let depth, i;
	if (chars.length === 0) {
		return false;
	}
	if (!(/^[a-zA-Z]$/.test(chars[0]) || chars[0] === "_")) {
		return false;
	}
	i = 1;
	while (
		i < chars.length &&
		(/^[a-zA-Z0-9]$/.test(chars[i]) || chars[i] === "_")
	) {
		i += 1;
	}
	while (i < chars.length) {
		if (chars[i] !== "[") {
			return false;
		}
		depth = 1;
		i += 1;
		while (i < chars.length && depth > 0) {
			if (chars[i] === "[") {
				depth += 1;
			} else if (chars[i] === "]") {
				depth -= 1;
			}
			i += 1;
		}
		if (depth !== 0) {
			return false;
		}
	}
	return true;
}

function _isSpecialParamOrDigit(c) {
	return _isSpecialParam(c) || _isDigit(c);
}

function _isParamExpansionOp(c) {
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

function _isSimpleParamOp(c) {
	return c === "-" || c === "=" || c === "?" || c === "+";
}

function _isEscapeCharInDquote(c) {
	return c === "$" || c === "`" || c === "\\";
}

function _isListTerminator(c) {
	return c === "\n" || c === "|" || c === ";" || c === "(" || c === ")";
}

function _isNegationBoundary(c) {
	return (
		_isWhitespace(c) ||
		c === ";" ||
		c === "|" ||
		c === ")" ||
		c === "&" ||
		c === ">" ||
		c === "<"
	);
}

function _isBackslashEscaped(value, idx) {
	let bs_count, j;
	bs_count = 0;
	j = idx - 1;
	while (j >= 0 && value[j] === "\\") {
		bs_count += 1;
		j -= 1;
	}
	return bs_count % 2 === 1;
}

function _isDollarDollarParen(value, idx) {
	let dollar_count, j;
	dollar_count = 0;
	j = idx - 1;
	while (j >= 0 && value[j] === "$") {
		dollar_count += 1;
		j -= 1;
	}
	return dollar_count % 2 === 1;
}

function _isSemicolonOrAmp(c) {
	return c === ";" || c === "&";
}

function _isParen(c) {
	return c === "(" || c === ")";
}

function _isCaretOrBang(c) {
	return c === "!" || c === "^";
}

function _isAtOrStar(c) {
	return c === "@" || c === "*";
}

function _isDigitOrDash(c) {
	return _isDigit(c) || c === "-";
}

function _isNewlineOrRightParen(c) {
	return c === "\n" || c === ")";
}

function _isNewlineOrRightBracket(c) {
	return c === "\n" || c === ")" || c === "}";
}

function _isSemicolonNewlineBrace(c) {
	return c === ";" || c === "\n" || c === "{";
}

function _strContains(haystack, needle) {
	return haystack.indexOf(needle) !== -1;
}

function _looksLikeAssignment(s) {
	let c, eq_pos, name;
	eq_pos = s.indexOf("=");
	if (eq_pos === -1) {
		return false;
	}
	name = s.slice(0, eq_pos);
	// Handle NAME+= (array append)
	if (name.endsWith("+")) {
		name = name.slice(0, -1);
	}
	if (!name) {
		return false;
	}
	if (!(/^[a-zA-Z]$/.test(name[0]) || name[0] === "_")) {
		return false;
	}
	for (c of name.slice(1)) {
		if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
			return false;
		}
	}
	return true;
}

function _isValidIdentifier(name) {
	let c;
	if (!name) {
		return false;
	}
	if (!(/^[a-zA-Z]$/.test(name[0]) || name[0] === "_")) {
		return false;
	}
	for (c of name.slice(1)) {
		if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
			return false;
		}
	}
	return true;
}

class Parser {
	constructor(source, in_process_sub) {
		if (in_process_sub == null) {
			in_process_sub = false;
		}
		this.source = source;
		this.pos = 0;
		this.length = source.length;
		this._pending_heredoc_end = null;
		this._saw_newline_in_single_quote = false;
		this._in_process_sub = in_process_sub;
	}

	atEnd() {
		return this.pos >= this.length;
	}

	peek() {
		if (this.atEnd()) {
			return null;
		}
		return this.source[this.pos];
	}

	advance() {
		let ch;
		if (this.atEnd()) {
			return null;
		}
		ch = this.source[this.pos];
		this.pos += 1;
		return ch;
	}

	_isBangFollowedByProcsub() {
		let next_char;
		if (this.pos + 2 >= this.length) {
			return false;
		}
		next_char = this.source[this.pos + 1];
		if (next_char !== ">" && next_char !== "<") {
			return false;
		}
		return this.source[this.pos + 2] === "(";
	}

	skipWhitespace() {
		let ch;
		while (!this.atEnd()) {
			ch = this.peek();
			if (_isWhitespaceNoNewline(ch)) {
				this.advance();
			} else if (ch === "#") {
				// Skip comment to end of line (but not the newline itself)
				while (!this.atEnd() && this.peek() !== "\n") {
					this.advance();
				}
			} else if (
				ch === "\\" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "\n"
			) {
				// Backslash-newline is line continuation - skip both
				this.advance();
				this.advance();
			} else {
				break;
			}
		}
	}

	skipWhitespaceAndNewlines() {
		let ch;
		while (!this.atEnd()) {
			ch = this.peek();
			if (_isWhitespace(ch)) {
				this.advance();
				// After advancing past a newline, skip any pending heredoc content
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
				// Skip comment to end of line
				while (!this.atEnd() && this.peek() !== "\n") {
					this.advance();
				}
			} else if (
				ch === "\\" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "\n"
			) {
				// Backslash-newline is line continuation - skip both
				this.advance();
				this.advance();
			} else {
				break;
			}
		}
	}

	_collectRedirects() {
		let redirect, redirects;
		redirects = [];
		while (true) {
			this.skipWhitespace();
			redirect = this.parseRedirect();
			if (redirect == null) {
				break;
			}
			redirects.push(redirect);
		}
		return redirects ? redirects : null;
	}

	_parseLoopBody(context) {
		let body, brace;
		if (this.peek() === "{") {
			brace = this.parseBraceGroup();
			if (brace == null) {
				throw new ParseError(
					`Expected brace group body in ${context}`,
					this.pos,
				);
			}
			return brace.body;
		}
		if (this.consumeWord("do")) {
			body = this.parseListUntil(new Set(["done"]));
			if (body == null) {
				throw new ParseError("Expected commands after 'do'", this.pos);
			}
			this.skipWhitespaceAndNewlines();
			if (!this.consumeWord("done")) {
				throw new ParseError(`Expected 'done' to close ${context}`, this.pos);
			}
			return body;
		}
		throw new ParseError(`Expected 'do' or '{' in ${context}`, this.pos);
	}

	peekWord() {
		let ch, chars, saved_pos, word;
		saved_pos = this.pos;
		this.skipWhitespace();
		if (this.atEnd() || _isMetachar(this.peek())) {
			this.pos = saved_pos;
			return null;
		}
		chars = [];
		while (!this.atEnd() && !_isMetachar(this.peek())) {
			ch = this.peek();
			// Stop at quotes - don't include in peek
			if (_isQuote(ch)) {
				break;
			}
			// Stop at backslash-newline (line continuation)
			if (
				ch === "\\" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "\n"
			) {
				break;
			}
			// Handle backslash escaping next character (even metacharacters)
			if (ch === "\\" && this.pos + 1 < this.length) {
				chars.push(this.advance());
				chars.push(this.advance());
				continue;
			}
			chars.push(this.advance());
		}
		if (chars) {
			word = chars.join("");
		} else {
			word = null;
		}
		this.pos = saved_pos;
		return word;
	}

	consumeWord(expected) {
		let _, saved_pos, word;
		saved_pos = this.pos;
		this.skipWhitespace();
		word = this.peekWord();
		if (word !== expected) {
			this.pos = saved_pos;
			return false;
		}
		// Actually consume the word
		this.skipWhitespace();
		for (_ of expected) {
			this.advance();
		}
		// Skip trailing backslash-newline (line continuation)
		while (
			this.peek() === "\\" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "\n"
		) {
			this.advance();
			this.advance();
		}
		return true;
	}

	parseWord(at_command_start, in_array_literal) {
		let ansi_node,
			ansi_result,
			ansi_text,
			arith_node,
			arith_result,
			arith_text,
			array_node,
			array_result,
			array_text,
			bracket_depth,
			c,
			ch,
			chars,
			cmdsub_node,
			cmdsub_result,
			cmdsub_text,
			extglob_depth,
			in_single_in_dquote,
			inner_parts,
			locale_node,
			locale_result,
			locale_text,
			next_c,
			next_ch,
			param_node,
			param_result,
			param_text,
			paren_depth,
			parts,
			pc,
			prev_char,
			procsub_node,
			procsub_result,
			procsub_text,
			seen_equals,
			start;
		if (at_command_start == null) {
			at_command_start = false;
		}
		if (in_array_literal == null) {
			in_array_literal = false;
		}
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		start = this.pos;
		chars = [];
		parts = [];
		bracket_depth = 0;
		seen_equals = false;
		while (!this.atEnd()) {
			ch = this.peek();
			// Track bracket depth for array subscripts like a[1+2]=3
			// Inside brackets, metacharacters like | and ( are literal
			// Only track [ after we've seen some chars (so [ -f file ] still works)
			// Only at command start (array assignments), not in argument position
			// Only BEFORE = sign (key=1],a[1 should not track the [1 part)
			// Only after identifier char (not [[ which is conditional keyword)
			// Also track in array elements like ([key]=val) to match brackets properly
			if (ch === "[") {
				if (bracket_depth > 0) {
					bracket_depth += 1;
					chars.push(this.advance());
					continue;
				}
				if (
					chars &&
					at_command_start &&
					!seen_equals &&
					_isArrayAssignmentPrefix(chars)
				) {
					prev_char = chars[chars.length - 1];
					if (/^[a-zA-Z0-9]$/.test(prev_char) || prev_char === "_") {
						bracket_depth += 1;
						chars.push(this.advance());
						continue;
					}
				}
				// Track brackets at start of word for array elements: ['key']=val or [key]=val
				// This ensures we find the matching ] even across newlines
				// Only applies when inside array literal (to avoid tracking [ in other contexts)
				if (chars.length === 0 && !seen_equals && in_array_literal) {
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
			// Single-quoted string - no expansion
			if (ch === "'") {
				this.advance();
				chars.push("'");
				while (!this.atEnd() && this.peek() !== "'") {
					c = this.advance();
					if (c === "\n") {
						this._saw_newline_in_single_quote = true;
					}
					chars.push(c);
				}
				if (this.atEnd()) {
					throw new ParseError("Unterminated single quote", start);
				}
				chars.push(this.advance());
			} else if (ch === '"') {
				// Double-quoted string - expansions happen inside
				this.advance();
				chars.push('"');
				in_single_in_dquote = false;
				while (!this.atEnd() && (in_single_in_dquote || this.peek() !== '"')) {
					c = this.peek();
					// Inside single-quoted section (from param subscript)
					if (in_single_in_dquote) {
						chars.push(this.advance());
						if (c === "'") {
							in_single_in_dquote = false;
						}
						continue;
					}
					// Handle escape sequences in double quotes
					if (c === "\\" && this.pos + 1 < this.length) {
						next_c = this.source[this.pos + 1];
						if (next_c === "\n") {
							// Line continuation - skip both backslash and newline
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
						// Handle arithmetic expansion $((...))
						arith_result = this._parseArithmeticExpansion();
						arith_node = arith_result[0];
						arith_text = arith_result[1];
						if (arith_node) {
							parts.push(arith_node);
							chars.push(arith_text);
						} else {
							// Not arithmetic - try command substitution
							cmdsub_result = this._parseCommandSubstitution();
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
						c === "$" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "["
					) {
						// Handle deprecated arithmetic expansion $[expr]
						arith_result = this._parseDeprecatedArithmetic();
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
						// Handle command substitution $(...)
						cmdsub_result = this._parseCommandSubstitution();
						cmdsub_node = cmdsub_result[0];
						cmdsub_text = cmdsub_result[1];
						if (cmdsub_node) {
							parts.push(cmdsub_node);
							chars.push(cmdsub_text);
						} else {
							chars.push(this.advance());
						}
					} else if (c === "$") {
						// Handle parameter expansion inside double quotes
						param_result = this._parseParamExpansion();
						param_node = param_result[0];
						param_text = param_result[1];
						if (param_node) {
							parts.push(param_node);
							chars.push(param_text);
						} else {
							chars.push(this.advance());
						}
					} else if (c === "`") {
						// Handle backtick command substitution
						cmdsub_result = this._parseBacktickSubstitution();
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
				// Escape outside quotes
				next_ch = this.source[this.pos + 1];
				if (next_ch === "\n") {
					// Line continuation - skip both backslash and newline
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
				// ANSI-C quoting $'...'
				ansi_result = this._parseAnsiCQuote();
				ansi_node = ansi_result[0];
				ansi_text = ansi_result[1];
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
				// Locale translation $"..."
				locale_result = this._parseLocaleString();
				locale_node = locale_result[0];
				locale_text = locale_result[1];
				inner_parts = locale_result[2];
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
				// Arithmetic expansion $((...)) - try before command substitution
				// If it fails (returns None), fall through to command substitution
				arith_result = this._parseArithmeticExpansion();
				arith_node = arith_result[0];
				arith_text = arith_result[1];
				if (arith_node) {
					parts.push(arith_node);
					chars.push(arith_text);
				} else {
					// Not arithmetic (e.g., '$( ( ... ) )' is command sub + subshell)
					cmdsub_result = this._parseCommandSubstitution();
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
				// Deprecated arithmetic expansion $[expr]
				arith_result = this._parseDeprecatedArithmetic();
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
				// Command substitution $(...)
				cmdsub_result = this._parseCommandSubstitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					parts.push(cmdsub_node);
					chars.push(cmdsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "$") {
				// Parameter expansion $var or ${...}
				param_result = this._parseParamExpansion();
				param_node = param_result[0];
				param_text = param_result[1];
				if (param_node) {
					parts.push(param_node);
					chars.push(param_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "`") {
				// Backtick command substitution
				cmdsub_result = this._parseBacktickSubstitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					parts.push(cmdsub_node);
					chars.push(cmdsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (
				_isRedirectChar(ch) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				// Process substitution <(...) or >(...)
				procsub_result = this._parseProcessSubstitution();
				procsub_node = procsub_result[0];
				procsub_text = procsub_result[1];
				if (procsub_node) {
					parts.push(procsub_node);
					chars.push(procsub_text);
				} else if (procsub_text) {
					// Not a valid process substitution, treat full <(...) as literal
					chars.push(procsub_text);
				} else {
					// Couldn't parse at all, treat <( as literal chars
					chars.push(this.advance());
					chars.push(this.advance());
				}
			} else if (
				ch === "(" &&
				chars &&
				bracket_depth === 0 &&
				(chars[chars.length - 1] === "=" ||
					(chars.length >= 2 &&
						chars[chars.length - 2] === "+" &&
						chars[chars.length - 1] === "="))
			) {
				// Array literal: name=(elements) or name+=(elements)
				// But not when inside brackets, as that would be part of array element
				array_result = this._parseArrayLiteral();
				array_node = array_result[0];
				array_text = array_result[1];
				if (array_node) {
					parts.push(array_node);
					chars.push(array_text);
				} else {
					// Unexpected: ( without matching )
					break;
				}
			} else if (
				_isExtglobPrefix(ch) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				// Extglob pattern @(), ?(), *(), +(), !()
				chars.push(this.advance());
				chars.push(this.advance());
				extglob_depth = 1;
				while (!this.atEnd() && extglob_depth > 0) {
					c = this.peek();
					if (c === ")") {
						chars.push(this.advance());
						extglob_depth -= 1;
					} else if (c === "(") {
						chars.push(this.advance());
						extglob_depth += 1;
					} else if (c === "\\") {
						if (
							this.pos + 1 < this.length &&
							this.source[this.pos + 1] === "\n"
						) {
							// Backslash-newline is line continuation - skip both
							this.advance();
							this.advance();
						} else {
							chars.push(this.advance());
							if (!this.atEnd()) {
								chars.push(this.advance());
							}
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
						// $() or $(()) inside extglob
						chars.push(this.advance());
						chars.push(this.advance());
						if (!this.atEnd() && this.peek() === "(") {
							// $(()) arithmetic
							chars.push(this.advance());
							paren_depth = 2;
							while (!this.atEnd() && paren_depth > 0) {
								pc = this.peek();
								if (pc === "(") {
									paren_depth += 1;
								} else if (pc === ")") {
									paren_depth -= 1;
								}
								chars.push(this.advance());
							}
						} else {
							// $() command sub - count as nested paren
							extglob_depth += 1;
						}
					} else if (
						_isExtglobPrefix(c) &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "("
					) {
						// Nested extglob
						chars.push(this.advance());
						chars.push(this.advance());
						extglob_depth += 1;
					} else {
						chars.push(this.advance());
					}
				}
			} else if (_isMetachar(ch) && bracket_depth === 0) {
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
		if (parts && parts.length) {
			return new Word(chars.join(""), parts);
		} else {
			return new Word(chars.join(""), null);
		}
	}

	_parseCommandSubstitution() {
		let all_heredoc_delimiters,
			arith_depth,
			c,
			case_depth,
			ch,
			check_line,
			cmd,
			content,
			content_start,
			delim,
			delimiter,
			delimiter_chars,
			depth,
			found_esac,
			found_in_content,
			heredoc_delimiters,
			heredoc_end,
			heredoc_start,
			line,
			line_end,
			line_start,
			nc,
			nested_depth,
			q,
			quote,
			saved,
			start,
			strip_tabs,
			sub_parser,
			tabs_stripped,
			tc,
			temp_case_depth,
			temp_depth,
			text,
			text_end;
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		start = this.pos;
		this.advance();
		if (this.atEnd() || this.peek() !== "(") {
			this.pos = start;
			return [null, ""];
		}
		this.advance();
		// Find matching closing paren, being aware of:
		// - Nested $() and plain ()
		// - Quoted strings
		// - case statements (where ) after pattern isn't a closer)
		content_start = this.pos;
		depth = 1;
		case_depth = 0;
		arith_depth = 0;
		while (!this.atEnd() && depth > 0) {
			c = this.peek();
			// ANSI-C quoted string $'...' - handle escape sequences
			if (
				c === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "'"
			) {
				this.advance();
				this.advance();
				while (!this.atEnd()) {
					if (this.peek() === "'") {
						this.advance();
						break;
					}
					if (this.peek() === "\\" && this.pos + 1 < this.length) {
						this.advance();
						this.advance();
					} else {
						this.advance();
					}
				}
				continue;
			}
			// Single-quoted string - no special chars inside
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
			// Double-quoted string - handle escapes and nested $()
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
						// Nested $() in double quotes - recurse to find matching )
						// Command substitution creates new quoting context
						this.advance();
						this.advance();
						nested_depth = 1;
						while (!this.atEnd() && nested_depth > 0) {
							nc = this.peek();
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
			// Backslash escape
			if (c === "\\" && this.pos + 1 < this.length) {
				this.advance();
				this.advance();
				continue;
			}
			// Comment - skip until newline
			if (c === "#" && this._isWordBoundaryBefore()) {
				while (!this.atEnd() && this.peek() !== "\n") {
					this.advance();
				}
				continue;
			}
			// Handle arithmetic expressions $((
			if (
				c === "$" &&
				this.pos + 2 < this.length &&
				this.source[this.pos + 1] === "(" &&
				this.source[this.pos + 2] === "("
			) {
				arith_depth += 1;
				this.advance();
				this.advance();
				this.advance();
				continue;
			}
			// Handle arithmetic close ))
			if (
				arith_depth > 0 &&
				c === ")" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === ")"
			) {
				arith_depth -= 1;
				this.advance();
				this.advance();
				continue;
			}
			// Heredoc - skip until delimiter line is found (not inside arithmetic)
			if (
				arith_depth === 0 &&
				c === "<" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "<"
			) {
				this.advance();
				this.advance();
				// Check for <<- (strip tabs)
				if (!this.atEnd() && this.peek() === "-") {
					this.advance();
				}
				// Skip whitespace before delimiter
				while (!this.atEnd() && _isWhitespaceNoNewline(this.peek())) {
					this.advance();
				}
				// Parse delimiter (handle quoting)
				delimiter_chars = [];
				if (!this.atEnd()) {
					ch = this.peek();
					if (_isQuote(ch)) {
						quote = this.advance();
						while (!this.atEnd() && this.peek() !== quote) {
							delimiter_chars.push(this.advance());
						}
						if (!this.atEnd()) {
							this.advance();
						}
					} else if (ch === "\\") {
						this.advance();
						// Backslash quotes - first char can be special, then read word
						if (!this.atEnd()) {
							delimiter_chars.push(this.advance());
						}
						while (!this.atEnd() && !_isMetachar(this.peek())) {
							delimiter_chars.push(this.advance());
						}
					} else {
						// Unquoted delimiter with possible embedded quotes
						while (!this.atEnd() && !_isMetachar(this.peek())) {
							ch = this.peek();
							if (_isQuote(ch)) {
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
				delimiter = delimiter_chars.join("");
				if (delimiter) {
					// Check if ) immediately follows (closes cmdsub with empty heredoc)
					if (!this.atEnd() && this.peek() === ")") {
						// Heredoc has no content - will be resolved later
						continue;
					}
					// Skip to end of current line
					while (!this.atEnd() && this.peek() !== "\n") {
						this.advance();
					}
					// Skip newline
					if (!this.atEnd() && this.peek() === "\n") {
						this.advance();
					}
					// Skip lines until we find the delimiter
					while (!this.atEnd()) {
						line_start = this.pos;
						line_end = this.pos;
						// Scan to end of line - heredoc content can contain )
						while (line_end < this.length && this.source[line_end] !== "\n") {
							line_end += 1;
						}
						line = this.source.slice(line_start, line_end);
						// Move position to end of line
						this.pos = line_end;
						// Check if this line matches delimiter
						check_line = line.replace(/^[\t]+/, "");
						if (check_line === delimiter) {
							// Skip newline after delimiter
							if (!this.atEnd() && this.peek() === "\n") {
								this.advance();
							}
							break;
						}
						// Also check for delimiter followed by other content
						// (e.g., "Xb)" where X is delimiter and b) continues the cmdsub)
						if (
							check_line.startsWith(delimiter) &&
							check_line.length > delimiter.length
						) {
							// Position parser right after the delimiter
							tabs_stripped = line.length - check_line.length;
							this.pos = line_start + tabs_stripped + delimiter.length;
							break;
						}
						// Skip newline and continue
						if (!this.atEnd() && this.peek() === "\n") {
							this.advance();
						}
					}
				}
				continue;
			}
			// Track case/esac for pattern terminator handling
			// Check for 'case' keyword (word boundary: preceded by space/newline/start)
			if (c === "c" && this._isWordBoundaryBefore()) {
				if (this._lookaheadKeyword("case")) {
					case_depth += 1;
					this._skipKeyword("case");
					continue;
				}
			}
			// Check for 'esac' keyword
			if (c === "e" && this._isWordBoundaryBefore() && case_depth > 0) {
				if (this._lookaheadKeyword("esac")) {
					case_depth -= 1;
					this._skipKeyword("esac");
					continue;
				}
			}
			// Handle parentheses
			if (c === "(") {
				depth += 1;
			} else if (c === ")") {
				// In case statement, ) after pattern is a terminator, not a paren
				// Only decrement depth if we're not in a case pattern position
				if (case_depth > 0 && depth === 1) {
					// This ) might be a case pattern terminator, not closing the $(
					// Look ahead to see if there's still content that needs esac
					saved = this.pos;
					this.advance();
					// Scan ahead to see if we find esac that closes our case
					// before finding a ) that could close our $(
					temp_depth = 0;
					temp_case_depth = case_depth;
					found_esac = false;
					while (!this.atEnd()) {
						tc = this.peek();
						if (tc === "'" || tc === '"') {
							// Skip quoted strings
							q = tc;
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
							this._isWordBoundaryBefore() &&
							this._lookaheadKeyword("case")
						) {
							// Nested case in lookahead
							temp_case_depth += 1;
							this._skipKeyword("case");
						} else if (
							tc === "e" &&
							this._isWordBoundaryBefore() &&
							this._lookaheadKeyword("esac")
						) {
							temp_case_depth -= 1;
							if (temp_case_depth === 0) {
								// All cases are closed
								found_esac = true;
								break;
							}
							this._skipKeyword("esac");
						} else if (tc === "(") {
							temp_depth += 1;
							this.advance();
						} else if (tc === ")") {
							// In case, ) is a pattern terminator, not a closer
							if (temp_case_depth > 0) {
								this.advance();
							} else if (temp_depth > 0) {
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
			if (depth > 0) {
				this.advance();
			}
		}
		if (depth !== 0) {
			this.pos = start;
			return [null, ""];
		}
		content = this.source.slice(content_start, this.pos);
		this.advance();
		// Save position after ) for text (before skipping heredoc content)
		text_end = this.pos;
		// Check for heredocs in content whose bodies follow the )
		// This handles cases like $(cmd <<X) where ) immediately follows <<X
		// Only process if there's a newline after ) - otherwise no heredoc content exists
		if (!this.atEnd() && this.peek() === "\n") {
			// Filter to only heredocs that weren't already consumed during parsing
			all_heredoc_delimiters = _extractHeredocDelimiters(content);
			heredoc_delimiters = [];
			for ([delim, strip_tabs] of all_heredoc_delimiters) {
				// Check if this delimiter was already consumed (appears on its own line in content)
				found_in_content = false;
				for (line of content.split("\n")) {
					check_line = strip_tabs ? line.replace(/^[\t]+/, "") : line;
					if (check_line === delim) {
						found_in_content = true;
						break;
					}
				}
				if (!found_in_content) {
					heredoc_delimiters.push([delim, strip_tabs]);
				}
			}
			if (heredoc_delimiters) {
				[heredoc_start, heredoc_end] = _findHeredocContentEnd(
					this.source,
					this.pos,
					heredoc_delimiters,
				);
				if (heredoc_end > heredoc_start) {
					content = content + this.source.slice(heredoc_start, heredoc_end);
					if (this._pending_heredoc_end == null) {
						this._pending_heredoc_end = heredoc_end;
					} else {
						this._pending_heredoc_end = Math.max(
							this._pending_heredoc_end,
							heredoc_end,
						);
					}
				}
			}
		}
		text = this.source.slice(start, text_end);
		// Parse the content as a command list
		sub_parser = new Parser(content, true);
		cmd = sub_parser.parseList();
		if (cmd == null) {
			cmd = new Empty();
		}
		// Ensure all content was consumed - if not, there's a syntax error
		sub_parser.skipWhitespaceAndNewlines();
		if (!sub_parser.atEnd()) {
			throw new ParseError("Unexpected content in command substitution", start);
		}
		return [new CommandSubstitution(cmd), text];
	}

	_isWordBoundaryBefore() {
		let prev;
		if (this.pos === 0) {
			return true;
		}
		prev = this.source[this.pos - 1];
		return _isWordStartContext(prev);
	}

	_isAssignmentWord(word) {
		let bracket_depth, ch, i, in_double, in_single;
		// Assignment must start with identifier (letter or underscore), not quoted
		if (
			!word.value ||
			!(/^[a-zA-Z]$/.test(word.value[0]) || word.value[0] === "_")
		) {
			return false;
		}
		in_single = false;
		in_double = false;
		bracket_depth = 0;
		i = 0;
		while (i < word.value.length) {
			ch = word.value[i];
			if (ch === "'" && !in_double) {
				in_single = !in_single;
			} else if (ch === '"' && !in_single) {
				in_double = !in_double;
			} else if (ch === "\\" && !in_single && i + 1 < word.value.length) {
				i += 1;
				continue;
			} else if (ch === "[" && !in_single && !in_double) {
				bracket_depth += 1;
			} else if (ch === "]" && !in_single && !in_double) {
				bracket_depth -= 1;
			} else if (
				ch === "=" &&
				!in_single &&
				!in_double &&
				bracket_depth === 0
			) {
				return true;
			} else if (
				!in_single &&
				!in_double &&
				bracket_depth === 0 &&
				!(/^[a-zA-Z0-9]$/.test(ch) || ch === "_")
			) {
				// Invalid char in identifier part before =
				return false;
			}
			i += 1;
		}
		return false;
	}

	_lookaheadKeyword(keyword) {
		let after, after_pos;
		if (this.pos + keyword.length > this.length) {
			return false;
		}
		if (!_startsWithAt(this.source, this.pos, keyword)) {
			return false;
		}
		// Check word boundary after keyword
		after_pos = this.pos + keyword.length;
		if (after_pos >= this.length) {
			return true;
		}
		after = this.source[after_pos];
		return _isWordEndContext(after);
	}

	_skipKeyword(keyword) {
		let _;
		for (_ of keyword) {
			this.advance();
		}
	}

	_parseBacktickSubstitution() {
		let c,
			ch,
			cmd,
			content,
			content_chars,
			escaped,
			next_c,
			start,
			sub_parser,
			text,
			text_chars;
		if (this.atEnd() || this.peek() !== "`") {
			return [null, ""];
		}
		start = this.pos;
		this.advance();
		// Find closing backtick, processing escape sequences as we go.
		// In backticks, backslash is special only before $, `, \, or newline.
		// \$ -> $, \` -> `, \\ -> \, \<newline> -> removed (line continuation)
		// other \X -> \X (backslash is literal)
		// content_chars: what gets parsed as the inner command
		// text_chars: what appears in the word representation (with line continuations removed)
		content_chars = [];
		text_chars = ["`"];
		while (!this.atEnd() && this.peek() !== "`") {
			c = this.peek();
			if (c === "\\" && this.pos + 1 < this.length) {
				next_c = this.source[this.pos + 1];
				if (next_c === "\n") {
					// Line continuation: skip both backslash and newline
					this.advance();
					this.advance();
				} else if (_isEscapeCharInDquote(next_c)) {
					// Don't add to content_chars or text_chars
					// Escape sequence: skip backslash in content, keep both in text
					this.advance();
					escaped = this.advance();
					content_chars.push(escaped);
					text_chars.push("\\");
					text_chars.push(escaped);
				} else {
					// Backslash is literal before other characters
					ch = this.advance();
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
			throw new ParseError("Unterminated backtick", start);
		}
		this.advance();
		text_chars.push("`");
		text = text_chars.join("");
		content = content_chars.join("");
		// Parse the content as a command list
		sub_parser = new Parser(content);
		cmd = sub_parser.parseList();
		if (cmd == null) {
			cmd = new Empty();
		}
		return [new CommandSubstitution(cmd), text];
	}

	_parseProcessSubstitution() {
		let c,
			cmd,
			content,
			content_start,
			depth,
			direction,
			heredoc_delimiters,
			heredoc_end,
			heredoc_start,
			start,
			sub_parser,
			text,
			text_end;
		if (this.atEnd() || !_isRedirectChar(this.peek())) {
			return [null, ""];
		}
		start = this.pos;
		direction = this.advance();
		if (this.atEnd() || this.peek() !== "(") {
			this.pos = start;
			return [null, ""];
		}
		this.advance();
		// Find matching ) - track nested parens and handle quotes
		content_start = this.pos;
		depth = 1;
		while (!this.atEnd() && depth > 0) {
			c = this.peek();
			// Comment - skip to end of line (quotes in comments are not special)
			if (c === "#") {
				while (!this.atEnd() && this.peek() !== "\n") {
					this.advance();
				}
				continue;
			}
			// Single-quoted string
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
			// Double-quoted string
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
			// Backslash escape
			if (c === "\\" && this.pos + 1 < this.length) {
				this.advance();
				this.advance();
				continue;
			}
			// Nested parentheses (including nested process substitutions)
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
		content = this.source.slice(content_start, this.pos);
		this.advance();
		// Save position after ) for text (before skipping heredoc content)
		text_end = this.pos;
		// Check for heredocs in content - their bodies follow the )
		heredoc_delimiters = _extractHeredocDelimiters(content);
		if (heredoc_delimiters) {
			[heredoc_start, heredoc_end] = _findHeredocContentEnd(
				this.source,
				this.pos,
				heredoc_delimiters,
			);
			if (heredoc_end > heredoc_start) {
				content = content + this.source.slice(heredoc_start, heredoc_end);
				// Use pending mechanism to skip heredoc after current line is parsed
				if (this._pending_heredoc_end == null) {
					this._pending_heredoc_end = heredoc_end;
				} else {
					this._pending_heredoc_end = Math.max(
						this._pending_heredoc_end,
						heredoc_end,
					);
				}
			}
		}
		text = this.source.slice(start, text_end);
		// Strip line continuations (backslash-newline) from text used for word construction
		// Use comment-aware stripping to preserve newlines that terminate comments
		text = _stripLineContinuationsCommentAware(text);
		// Parse the content as a command list
		sub_parser = new Parser(content, true);
		cmd = sub_parser.parseList();
		if (cmd == null) {
			cmd = new Empty();
		}
		// If content wasn't fully consumed, this isn't a valid process substitution
		// Return the text so caller can treat it as literal characters
		if (!sub_parser.atEnd()) {
			return [null, text];
		}
		return [new ProcessSubstitution(direction, cmd), text];
	}

	_parseArrayLiteral() {
		let elements, start, text, word;
		if (this.atEnd() || this.peek() !== "(") {
			return [null, ""];
		}
		start = this.pos;
		this.advance();
		elements = [];
		while (true) {
			// Skip whitespace, newlines, and comments between elements
			this.skipWhitespaceAndNewlines();
			if (this.atEnd()) {
				throw new ParseError("Unterminated array literal", start);
			}
			if (this.peek() === ")") {
				break;
			}
			// Parse an element word
			word = this.parseWord(false, true);
			if (word == null) {
				// Might be a closing paren or error
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
		text = this.source.slice(start, this.pos);
		return [new ArrayNode(elements), text];
	}

	_parseArithmeticExpansion() {
		let c, content, content_start, depth, expr, first_close_pos, start, text;
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		start = this.pos;
		// Check for $((
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
		// Find matching )) by tracking paren depth (starting at 2 for $(()
		// The closing )) are: first ) that brings depth 2→1, and ) that brings 1→0
		// Content excludes these UNLESS there's expression content between them
		content_start = this.pos;
		depth = 2;
		first_close_pos = null;
		while (!this.atEnd() && depth > 0) {
			c = this.peek();
			if (c === "(") {
				depth += 1;
				this.advance();
			} else if (c === ")") {
				if (depth === 2) {
					first_close_pos = this.pos;
				}
				depth -= 1;
				if (depth === 0) {
					break;
				}
				this.advance();
			} else {
				if (depth === 1) {
					// Content after first closing ), so include up to final )
					first_close_pos = null;
				}
				this.advance();
			}
		}
		if (depth !== 0) {
			this.pos = start;
			return [null, ""];
		}
		// Content ends at first_close_pos if set, else at final )
		if (first_close_pos != null) {
			content = this.source.slice(content_start, first_close_pos);
		} else {
			content = this.source.slice(content_start, this.pos);
		}
		this.advance();
		text = this.source.slice(start, this.pos);
		// Parse the arithmetic expression
		// If parsing fails, this isn't arithmetic (e.g., $(((cmd))) is command sub + subshell)
		try {
			expr = this._parseArithExpr(content);
		} catch (_) {
			this.pos = start;
			return [null, ""];
		}
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
	_parseArithExpr(content) {
		let result, saved_arith_len, saved_arith_pos, saved_arith_src;
		// Save any existing arith context (for nested parsing)
		saved_arith_src = this._arithSrc ?? null;
		saved_arith_pos = this._arithPos ?? null;
		saved_arith_len = this._arithLen ?? null;
		this._arith_src = content;
		this._arith_pos = 0;
		this._arith_len = content.length;
		this._arithSkipWs();
		if (this._arithAtEnd()) {
			result = null;
		} else {
			result = this._arithParseComma();
		}
		// Restore previous arith context
		if (saved_arith_src != null) {
			this._arith_src = saved_arith_src;
			this._arith_pos = saved_arith_pos;
			this._arith_len = saved_arith_len;
		}
		return result;
	}

	_arithAtEnd() {
		return this._arith_pos >= this._arith_len;
	}

	_arithPeek(offset) {
		let pos;
		if (offset == null) {
			offset = 0;
		}
		pos = this._arith_pos + offset;
		if (pos >= this._arith_len) {
			return "";
		}
		return this._arith_src[pos];
	}

	_arithAdvance() {
		let c;
		if (this._arithAtEnd()) {
			return "";
		}
		c = this._arith_src[this._arith_pos];
		this._arith_pos += 1;
		return c;
	}

	_arithSkipWs() {
		let c;
		while (!this._arithAtEnd()) {
			c = this._arith_src[this._arith_pos];
			if (_isWhitespace(c)) {
				this._arith_pos += 1;
			} else if (
				c === "\\" &&
				this._arith_pos + 1 < this._arith_len &&
				this._arith_src[this._arith_pos + 1] === "\n"
			) {
				// Backslash-newline continuation
				this._arith_pos += 2;
			} else {
				break;
			}
		}
	}

	_arithMatch(s) {
		return _startsWithAt(this._arith_src, this._arith_pos, s);
	}

	_arithConsume(s) {
		if (this._arithMatch(s)) {
			this._arith_pos += s.length;
			return true;
		}
		return false;
	}

	_arithParseComma() {
		let left, right;
		left = this._arithParseAssign();
		while (true) {
			this._arithSkipWs();
			if (this._arithConsume(",")) {
				this._arithSkipWs();
				right = this._arithParseAssign();
				left = new ArithComma(left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arithParseAssign() {
		let assign_ops, left, op, right;
		left = this._arithParseTernary();
		this._arithSkipWs();
		// Check for assignment operators
		assign_ops = [
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
		for (op of assign_ops) {
			if (this._arithMatch(op)) {
				// Make sure it's not == or !=
				if (op === "=" && this._arithPeek(1) === "=") {
					break;
				}
				this._arithConsume(op);
				this._arithSkipWs();
				right = this._arithParseAssign();
				return new ArithAssign(op, left, right);
			}
		}
		return left;
	}

	_arithParseTernary() {
		let cond, if_false, if_true;
		cond = this._arithParseLogicalOr();
		this._arithSkipWs();
		if (this._arithConsume("?")) {
			this._arithSkipWs();
			// True branch can be empty (e.g., 4 ? : $A - invalid at runtime, valid syntax)
			if (this._arithMatch(":")) {
				if_true = null;
			} else {
				if_true = this._arithParseAssign();
			}
			this._arithSkipWs();
			// Check for : (may be missing in malformed expressions like 1 ? 20)
			if (this._arithConsume(":")) {
				this._arithSkipWs();
				// False branch can be empty (e.g., 4 ? 20 : - invalid at runtime)
				if (this._arithAtEnd() || this._arithPeek() === ")") {
					if_false = null;
				} else {
					if_false = this._arithParseTernary();
				}
			} else {
				if_false = null;
			}
			return new ArithTernary(cond, if_true, if_false);
		}
		return cond;
	}

	_arithParseLeftAssoc(ops, parsefn) {
		let left, matched, op;
		left = parsefn();
		while (true) {
			this._arithSkipWs();
			matched = false;
			for (op of ops) {
				if (this._arithMatch(op)) {
					this._arithConsume(op);
					this._arithSkipWs();
					left = new ArithBinaryOp(op, left, parsefn());
					matched = true;
					break;
				}
			}
			if (!matched) {
				break;
			}
		}
		return left;
	}

	_arithParseLogicalOr() {
		return this._arithParseLeftAssoc(
			["||"],
			this._arithParseLogicalAnd.bind(this),
		);
	}

	_arithParseLogicalAnd() {
		return this._arithParseLeftAssoc(
			["&&"],
			this._arithParseBitwiseOr.bind(this),
		);
	}

	_arithParseBitwiseOr() {
		let left, right;
		left = this._arithParseBitwiseXor();
		while (true) {
			this._arithSkipWs();
			// Make sure it's not || or |=
			if (
				this._arithPeek() === "|" &&
				this._arithPeek(1) !== "|" &&
				this._arithPeek(1) !== "="
			) {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseBitwiseXor();
				left = new ArithBinaryOp("|", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arithParseBitwiseXor() {
		let left, right;
		left = this._arithParseBitwiseAnd();
		while (true) {
			this._arithSkipWs();
			// Make sure it's not ^=
			if (this._arithPeek() === "^" && this._arithPeek(1) !== "=") {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseBitwiseAnd();
				left = new ArithBinaryOp("^", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arithParseBitwiseAnd() {
		let left, right;
		left = this._arithParseEquality();
		while (true) {
			this._arithSkipWs();
			// Make sure it's not && or &=
			if (
				this._arithPeek() === "&" &&
				this._arithPeek(1) !== "&" &&
				this._arithPeek(1) !== "="
			) {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseEquality();
				left = new ArithBinaryOp("&", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arithParseEquality() {
		return this._arithParseLeftAssoc(
			["==", "!="],
			this._arithParseComparison.bind(this),
		);
	}

	_arithParseComparison() {
		let left, right;
		left = this._arithParseShift();
		while (true) {
			this._arithSkipWs();
			if (this._arithMatch("<=")) {
				this._arithConsume("<=");
				this._arithSkipWs();
				right = this._arithParseShift();
				left = new ArithBinaryOp("<=", left, right);
			} else if (this._arithMatch(">=")) {
				this._arithConsume(">=");
				this._arithSkipWs();
				right = this._arithParseShift();
				left = new ArithBinaryOp(">=", left, right);
			} else if (
				this._arithPeek() === "<" &&
				this._arithPeek(1) !== "<" &&
				this._arithPeek(1) !== "="
			) {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseShift();
				left = new ArithBinaryOp("<", left, right);
			} else if (
				this._arithPeek() === ">" &&
				this._arithPeek(1) !== ">" &&
				this._arithPeek(1) !== "="
			) {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseShift();
				left = new ArithBinaryOp(">", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arithParseShift() {
		let left, right;
		left = this._arithParseAdditive();
		while (true) {
			this._arithSkipWs();
			if (this._arithMatch("<<=")) {
				break;
			}
			if (this._arithMatch(">>=")) {
				break;
			}
			if (this._arithMatch("<<")) {
				this._arithConsume("<<");
				this._arithSkipWs();
				right = this._arithParseAdditive();
				left = new ArithBinaryOp("<<", left, right);
			} else if (this._arithMatch(">>")) {
				this._arithConsume(">>");
				this._arithSkipWs();
				right = this._arithParseAdditive();
				left = new ArithBinaryOp(">>", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arithParseAdditive() {
		let c, c2, left, right;
		left = this._arithParseMultiplicative();
		while (true) {
			this._arithSkipWs();
			c = this._arithPeek();
			c2 = this._arithPeek(1);
			if (c === "+" && c2 !== "+" && c2 !== "=") {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseMultiplicative();
				left = new ArithBinaryOp("+", left, right);
			} else if (c === "-" && c2 !== "-" && c2 !== "=") {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseMultiplicative();
				left = new ArithBinaryOp("-", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arithParseMultiplicative() {
		let c, c2, left, right;
		left = this._arithParseExponentiation();
		while (true) {
			this._arithSkipWs();
			c = this._arithPeek();
			c2 = this._arithPeek(1);
			if (c === "*" && c2 !== "*" && c2 !== "=") {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseExponentiation();
				left = new ArithBinaryOp("*", left, right);
			} else if (c === "/" && c2 !== "=") {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseExponentiation();
				left = new ArithBinaryOp("/", left, right);
			} else if (c === "%" && c2 !== "=") {
				this._arithAdvance();
				this._arithSkipWs();
				right = this._arithParseExponentiation();
				left = new ArithBinaryOp("%", left, right);
			} else {
				break;
			}
		}
		return left;
	}

	_arithParseExponentiation() {
		let left, right;
		left = this._arithParseUnary();
		this._arithSkipWs();
		if (this._arithMatch("**")) {
			this._arithConsume("**");
			this._arithSkipWs();
			right = this._arithParseExponentiation();
			return new ArithBinaryOp("**", left, right);
		}
		return left;
	}

	_arithParseUnary() {
		let c, operand;
		this._arithSkipWs();
		// Pre-increment/decrement
		if (this._arithMatch("++")) {
			this._arithConsume("++");
			this._arithSkipWs();
			operand = this._arithParseUnary();
			return new ArithPreIncr(operand);
		}
		if (this._arithMatch("--")) {
			this._arithConsume("--");
			this._arithSkipWs();
			operand = this._arithParseUnary();
			return new ArithPreDecr(operand);
		}
		// Unary operators
		c = this._arithPeek();
		if (c === "!") {
			this._arithAdvance();
			this._arithSkipWs();
			operand = this._arithParseUnary();
			return new ArithUnaryOp("!", operand);
		}
		if (c === "~") {
			this._arithAdvance();
			this._arithSkipWs();
			operand = this._arithParseUnary();
			return new ArithUnaryOp("~", operand);
		}
		if (c === "+" && this._arithPeek(1) !== "+") {
			this._arithAdvance();
			this._arithSkipWs();
			operand = this._arithParseUnary();
			return new ArithUnaryOp("+", operand);
		}
		if (c === "-" && this._arithPeek(1) !== "-") {
			this._arithAdvance();
			this._arithSkipWs();
			operand = this._arithParseUnary();
			return new ArithUnaryOp("-", operand);
		}
		return this._arithParsePostfix();
	}

	_arithParsePostfix() {
		let index, left;
		left = this._arithParsePrimary();
		while (true) {
			this._arithSkipWs();
			if (this._arithMatch("++")) {
				this._arithConsume("++");
				left = new ArithPostIncr(left);
			} else if (this._arithMatch("--")) {
				this._arithConsume("--");
				left = new ArithPostDecr(left);
			} else if (this._arithPeek() === "[") {
				// Array subscript - but only for variables
				if (left.kind === "var") {
					this._arithAdvance();
					this._arithSkipWs();
					index = this._arithParseComma();
					this._arithSkipWs();
					if (!this._arithConsume("]")) {
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

	_arithParsePrimary() {
		let c, escaped_char, expr;
		this._arithSkipWs();
		c = this._arithPeek();
		// Parenthesized expression
		if (c === "(") {
			this._arithAdvance();
			this._arithSkipWs();
			expr = this._arithParseComma();
			this._arithSkipWs();
			if (!this._arithConsume(")")) {
				throw new ParseError(
					"Expected ')' in arithmetic expression",
					this._arith_pos,
				);
			}
			return expr;
		}
		// Parameter length #$var or #${...}
		if (c === "#" && this._arithPeek(1) === "$") {
			this._arithAdvance();
			return this._arithParseExpansion();
		}
		// Parameter expansion ${...} or $var or $(...)
		if (c === "$") {
			return this._arithParseExpansion();
		}
		// Single-quoted string - content becomes the number
		if (c === "'") {
			return this._arithParseSingleQuote();
		}
		// Double-quoted string - may contain expansions
		if (c === '"') {
			return this._arithParseDoubleQuote();
		}
		// Backtick command substitution
		if (c === "`") {
			return this._arithParseBacktick();
		}
		// Escape sequence \X (not line continuation, which is handled in _arith_skip_ws)
		// Escape covers only the single character after backslash
		if (c === "\\") {
			this._arithAdvance();
			if (this._arithAtEnd()) {
				throw new ParseError(
					"Unexpected end after backslash in arithmetic",
					this._arith_pos,
				);
			}
			escaped_char = this._arithAdvance();
			return new ArithEscape(escaped_char);
		}
		// Check for end of expression or operators - bash allows missing operands
		// (defers validation to runtime), so we return an empty node
		// Include #{} and ; which bash accepts syntactically but fails at runtime
		if (this._arithAtEnd() || ")]:,;?|&<>=!+-*/%^~#{}".includes(c)) {
			return new ArithEmpty();
		}
		// Number or variable
		return this._arithParseNumberOrVar();
	}

	_arithParseExpansion() {
		let c, ch, name_chars;
		if (!this._arithConsume("$")) {
			throw new ParseError("Expected '$'", this._arith_pos);
		}
		c = this._arithPeek();
		// Command substitution $(...)
		if (c === "(") {
			return this._arithParseCmdsub();
		}
		// Braced parameter ${...}
		if (c === "{") {
			return this._arithParseBracedParam();
		}
		// Simple $var
		name_chars = [];
		while (!this._arithAtEnd()) {
			ch = this._arithPeek();
			if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
				name_chars.push(this._arithAdvance());
			} else if (
				(_isSpecialParamOrDigit(ch) || ch === "#") &&
				name_chars.length === 0
			) {
				// Special parameters
				name_chars.push(this._arithAdvance());
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

	_arithParseCmdsub() {
		let ch,
			cmd,
			content,
			content_start,
			depth,
			inner_expr,
			saved_len,
			saved_pos,
			saved_src;
		// We're positioned after $, at (
		this._arithAdvance();
		// Check for $(( which is nested arithmetic
		if (this._arithPeek() === "(") {
			this._arithAdvance();
			depth = 1;
			content_start = this._arith_pos;
			while (!this._arithAtEnd() && depth > 0) {
				ch = this._arithPeek();
				if (ch === "(") {
					depth += 1;
					this._arithAdvance();
				} else if (ch === ")") {
					if (depth === 1 && this._arithPeek(1) === ")") {
						break;
					}
					depth -= 1;
					this._arithAdvance();
				} else {
					this._arithAdvance();
				}
			}
			content = this._arith_src.slice(content_start, this._arith_pos);
			this._arithAdvance();
			this._arithAdvance();
			inner_expr = this._parseArithExpr(content);
			return new ArithmeticExpansion(inner_expr);
		}
		// Regular command substitution
		depth = 1;
		content_start = this._arith_pos;
		while (!this._arithAtEnd() && depth > 0) {
			ch = this._arithPeek();
			if (ch === "(") {
				depth += 1;
				this._arithAdvance();
			} else if (ch === ")") {
				depth -= 1;
				if (depth === 0) {
					break;
				}
				this._arithAdvance();
			} else {
				this._arithAdvance();
			}
		}
		content = this._arith_src.slice(content_start, this._arith_pos);
		this._arithAdvance();
		// Parse the command inside
		saved_pos = this.pos;
		saved_src = this.source;
		saved_len = this.length;
		this.source = content;
		this.pos = 0;
		this.length = content.length;
		cmd = this.parseList();
		this.source = saved_src;
		this.pos = saved_pos;
		this.length = saved_len;
		return new CommandSubstitution(cmd);
	}

	_arithParseBracedParam() {
		let ch, depth, name, name_chars, op_chars, op_str;
		this._arithAdvance();
		// Handle indirect ${!var}
		if (this._arithPeek() === "!") {
			this._arithAdvance();
			name_chars = [];
			while (!this._arithAtEnd() && this._arithPeek() !== "}") {
				name_chars.push(this._arithAdvance());
			}
			this._arithConsume("}");
			return new ParamIndirect(name_chars.join(""));
		}
		// Handle length ${#var}
		if (this._arithPeek() === "#") {
			this._arithAdvance();
			name_chars = [];
			while (!this._arithAtEnd() && this._arithPeek() !== "}") {
				name_chars.push(this._arithAdvance());
			}
			this._arithConsume("}");
			return new ParamLength(name_chars.join(""));
		}
		// Regular ${var} or ${var...}
		name_chars = [];
		while (!this._arithAtEnd()) {
			ch = this._arithPeek();
			if (ch === "}") {
				this._arithAdvance();
				return new ParamExpansion(name_chars.join(""));
			}
			if (_isParamExpansionOp(ch)) {
				// Operator follows
				break;
			}
			name_chars.push(this._arithAdvance());
		}
		name = name_chars.join("");
		// Check for operator
		op_chars = [];
		depth = 1;
		while (!this._arithAtEnd() && depth > 0) {
			ch = this._arithPeek();
			if (ch === "{") {
				depth += 1;
				op_chars.push(this._arithAdvance());
			} else if (ch === "}") {
				depth -= 1;
				if (depth === 0) {
					break;
				}
				op_chars.push(this._arithAdvance());
			} else {
				op_chars.push(this._arithAdvance());
			}
		}
		this._arithConsume("}");
		op_str = op_chars.join("");
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

	_arithParseSingleQuote() {
		let content, content_start;
		this._arithAdvance();
		content_start = this._arith_pos;
		while (!this._arithAtEnd() && this._arithPeek() !== "'") {
			this._arithAdvance();
		}
		content = this._arith_src.slice(content_start, this._arith_pos);
		if (!this._arithConsume("'")) {
			throw new ParseError(
				"Unterminated single quote in arithmetic",
				this._arith_pos,
			);
		}
		return new ArithNumber(content);
	}

	_arithParseDoubleQuote() {
		let c, content, content_start;
		this._arithAdvance();
		content_start = this._arith_pos;
		while (!this._arithAtEnd() && this._arithPeek() !== '"') {
			c = this._arithPeek();
			if (c === "\\" && !this._arithAtEnd()) {
				this._arithAdvance();
				this._arithAdvance();
			} else {
				this._arithAdvance();
			}
		}
		content = this._arith_src.slice(content_start, this._arith_pos);
		if (!this._arithConsume('"')) {
			throw new ParseError(
				"Unterminated double quote in arithmetic",
				this._arith_pos,
			);
		}
		return new ArithNumber(content);
	}

	_arithParseBacktick() {
		let c, cmd, content, content_start, saved_len, saved_pos, saved_src;
		this._arithAdvance();
		content_start = this._arith_pos;
		while (!this._arithAtEnd() && this._arithPeek() !== "`") {
			c = this._arithPeek();
			if (c === "\\" && !this._arithAtEnd()) {
				this._arithAdvance();
				this._arithAdvance();
			} else {
				this._arithAdvance();
			}
		}
		content = this._arith_src.slice(content_start, this._arith_pos);
		if (!this._arithConsume("`")) {
			throw new ParseError(
				"Unterminated backtick in arithmetic",
				this._arith_pos,
			);
		}
		// Parse the command inside
		saved_pos = this.pos;
		saved_src = this.source;
		saved_len = this.length;
		this.source = content;
		this.pos = 0;
		this.length = content.length;
		cmd = this.parseList();
		this.source = saved_src;
		this.pos = saved_pos;
		this.length = saved_len;
		return new CommandSubstitution(cmd);
	}

	_arithParseNumberOrVar() {
		let c, ch, chars, expansion, prefix;
		this._arithSkipWs();
		chars = [];
		c = this._arithPeek();
		// Check for number (starts with digit or base#)
		if (/^[0-9]+$/.test(c)) {
			// Could be decimal, hex (0x), octal (0), or base#n
			while (!this._arithAtEnd()) {
				ch = this._arithPeek();
				if (/^[a-zA-Z0-9]$/.test(ch) || ch === "#" || ch === "_") {
					chars.push(this._arithAdvance());
				} else {
					break;
				}
			}
			prefix = chars.join("");
			// Check if followed by $ expansion (e.g., 0x$var)
			if (!this._arithAtEnd() && this._arithPeek() === "$") {
				expansion = this._arithParseExpansion();
				return new ArithConcat([new ArithNumber(prefix), expansion]);
			}
			return new ArithNumber(prefix);
		}
		// Variable name (starts with letter or _)
		if (/^[a-zA-Z]$/.test(c) || c === "_") {
			while (!this._arithAtEnd()) {
				ch = this._arithPeek();
				if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
					chars.push(this._arithAdvance());
				} else {
					break;
				}
			}
			return new ArithVar(chars.join(""));
		}
		throw new ParseError(
			`Unexpected character '${c}' in arithmetic expression`,
			this._arith_pos,
		);
	}

	_parseDeprecatedArithmetic() {
		let c, content, content_start, depth, start, text;
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		start = this.pos;
		// Check for $[
		if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== "[") {
			return [null, ""];
		}
		this.advance();
		this.advance();
		// Find matching ] - need to track nested brackets
		content_start = this.pos;
		depth = 1;
		while (!this.atEnd() && depth > 0) {
			c = this.peek();
			if (c === "[" && !_isBackslashEscaped(this.source, this.pos)) {
				depth += 1;
				this.advance();
			} else if (c === "]") {
				if (!_isBackslashEscaped(this.source, this.pos)) {
					depth -= 1;
					if (depth === 0) {
						break;
					}
				}
				this.advance();
			} else {
				this.advance();
			}
		}
		if (this.atEnd() || depth !== 0) {
			throw new ParseError("Unterminated $[", start);
		}
		content = this.source.slice(content_start, this.pos);
		this.advance();
		text = this.source.slice(start, this.pos);
		return [new ArithDeprecated(content), text];
	}

	_parseAnsiCQuote() {
		let ch, content, content_chars, found_close, start, text;
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== "'") {
			return [null, ""];
		}
		start = this.pos;
		this.advance();
		this.advance();
		content_chars = [];
		found_close = false;
		while (!this.atEnd()) {
			ch = this.peek();
			if (ch === "'") {
				this.advance();
				found_close = true;
				break;
			} else if (ch === "\\") {
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
		text = this.source.slice(start, this.pos);
		content = content_chars.join("");
		return [new AnsiCQuote(content), text];
	}

	_parseLocaleString() {
		let arith_node,
			arith_result,
			arith_text,
			ch,
			cmdsub_node,
			cmdsub_result,
			cmdsub_text,
			content,
			content_chars,
			found_close,
			inner_parts,
			next_ch,
			param_node,
			param_result,
			param_text,
			start,
			text;
		if (this.atEnd() || this.peek() !== "$") {
			return [null, "", []];
		}
		if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== '"') {
			return [null, "", []];
		}
		start = this.pos;
		this.advance();
		this.advance();
		content_chars = [];
		inner_parts = [];
		found_close = false;
		while (!this.atEnd()) {
			ch = this.peek();
			if (ch === '"') {
				this.advance();
				found_close = true;
				break;
			} else if (ch === "\\" && this.pos + 1 < this.length) {
				// Escape sequence (line continuation removes both)
				next_ch = this.source[this.pos + 1];
				if (next_ch === "\n") {
					// Line continuation - skip both backslash and newline
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
				// Handle arithmetic expansion $((...))
				arith_result = this._parseArithmeticExpansion();
				arith_node = arith_result[0];
				arith_text = arith_result[1];
				if (arith_node) {
					inner_parts.push(arith_node);
					content_chars.push(arith_text);
				} else {
					// Not arithmetic - try command substitution
					cmdsub_result = this._parseCommandSubstitution();
					cmdsub_node = cmdsub_result[0];
					cmdsub_text = cmdsub_result[1];
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
				// Handle command substitution $(...)
				cmdsub_result = this._parseCommandSubstitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					inner_parts.push(cmdsub_node);
					content_chars.push(cmdsub_text);
				} else {
					content_chars.push(this.advance());
				}
			} else if (ch === "$") {
				// Handle parameter expansion
				param_result = this._parseParamExpansion();
				param_node = param_result[0];
				param_text = param_result[1];
				if (param_node) {
					inner_parts.push(param_node);
					content_chars.push(param_text);
				} else {
					content_chars.push(this.advance());
				}
			} else if (ch === "`") {
				// Handle backtick command substitution
				cmdsub_result = this._parseBacktickSubstitution();
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
		content = content_chars.join("");
		// Reconstruct text from parsed content (handles line continuation removal)
		text = `$"${content}"`;
		return [new LocaleString(content), text, inner_parts];
	}

	_parseParamExpansion() {
		let c, ch, name, name_start, start, text;
		if (this.atEnd() || this.peek() !== "$") {
			return [null, ""];
		}
		start = this.pos;
		this.advance();
		if (this.atEnd()) {
			this.pos = start;
			return [null, ""];
		}
		ch = this.peek();
		// Braced expansion ${...}
		if (ch === "{") {
			this.advance();
			return this._parseBracedParam(start);
		}
		// Simple expansion $var or $special
		// Special parameters: ?$!#@*-0-9 (but NOT & which is a shell metachar)
		if (_isSpecialParamUnbraced(ch) || _isDigit(ch) || ch === "#") {
			this.advance();
			text = this.source.slice(start, this.pos);
			return [new ParamExpansion(ch), text];
		}
		// Variable name [a-zA-Z_][a-zA-Z0-9_]*
		if (/^[a-zA-Z]$/.test(ch) || ch === "_") {
			name_start = this.pos;
			while (!this.atEnd()) {
				c = this.peek();
				if (/^[a-zA-Z0-9]$/.test(c) || c === "_") {
					this.advance();
				} else {
					break;
				}
			}
			name = this.source.slice(name_start, this.pos);
			text = this.source.slice(start, this.pos);
			return [new ParamExpansion(name), text];
		}
		// Not a valid expansion, restore position
		this.pos = start;
		return [null, ""];
	}

	_parseBracedParam(start) {
		let arg,
			arg_chars,
			backtick_pos,
			backtick_start,
			bc,
			c,
			ch,
			content,
			content_chars,
			depth,
			dollar_count,
			in_double_inner,
			in_double_quote,
			in_single,
			in_single_quote,
			next_c,
			op,
			param,
			paren_depth,
			pc,
			suffix,
			text,
			trailing;
		if (this.atEnd()) {
			this.pos = start;
			return [null, ""];
		}
		ch = this.peek();
		// ${#param} - length
		if (ch === "#") {
			this.advance();
			param = this._consumeParamName();
			if (param && !this.atEnd() && this.peek() === "}") {
				this.advance();
				text = this.source.slice(start, this.pos);
				return [new ParamLength(param), text];
			}
			// Not a simple length expansion - fall through to parse as regular expansion
			this.pos = start + 2;
		}
		// ${!param} or ${!param<op><arg>} - indirect
		if (ch === "!") {
			this.advance();
			while (!this.atEnd() && _isWhitespaceNoNewline(this.peek())) {
				this.advance();
			}
			param = this._consumeParamName();
			if (param) {
				// Skip optional whitespace before closing brace
				while (!this.atEnd() && _isWhitespaceNoNewline(this.peek())) {
					this.advance();
				}
				if (!this.atEnd() && this.peek() === "}") {
					this.advance();
					text = this.source.slice(start, this.pos);
					return [new ParamIndirect(param), text];
				}
				// ${!prefix@} and ${!prefix*} are prefix matching (lists variable names)
				// These are NOT operators - the @/* is part of the indirect form
				if (!this.atEnd() && _isAtOrStar(this.peek())) {
					suffix = this.advance();
					// Consume any trailing content until closing brace
					// Bash accepts this syntactically (fails at runtime)
					trailing = [];
					depth = 1;
					while (!this.atEnd() && depth > 0) {
						c = this.peek();
						if (
							c === "$" &&
							this.pos + 1 < this.length &&
							this.source[this.pos + 1] === "{"
						) {
							depth += 1;
							trailing.push(this.advance());
							trailing.push(this.advance());
						} else if (c === "}") {
							depth -= 1;
							if (depth === 0) {
								break;
							}
							trailing.push(this.advance());
						} else if (c === "\\") {
							trailing.push(this.advance());
							if (!this.atEnd()) {
								trailing.push(this.advance());
							}
						} else {
							trailing.push(this.advance());
						}
					}
					if (depth === 0) {
						this.advance();
						text = this.source.slice(start, this.pos);
						return [
							new ParamIndirect(param + suffix + trailing.join("")),
							text,
						];
					}
					// Unclosed brace
					this.pos = start;
					return [null, ""];
				}
				// Check for operator (e.g., ${!##} = indirect of # with # op)
				op = this._consumeParamOperator();
				if (op == null && !this.atEnd() && this.peek() !== "}") {
					// Unknown operator - bash still parses these (fails at runtime)
					op = this.advance();
				}
				if (op != null) {
					// Parse argument until closing brace
					arg_chars = [];
					depth = 1;
					while (!this.atEnd() && depth > 0) {
						c = this.peek();
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
						arg = arg_chars.join("");
						text = this.source.slice(start, this.pos);
						return [new ParamIndirect(param, op, arg), text];
					}
				}
				// Fell through - pattern didn't match, return None
				this.pos = start;
				return [null, ""];
			} else {
				// ${! followed by non-param char like | - fall through to regular parsing
				this.pos = start + 2;
			}
		}
		// ${param} or ${param<op><arg>}
		param = this._consumeParamName();
		if (!param) {
			// Allow empty parameter for simple operators like ${:-word}
			if (
				!this.atEnd() &&
				("-=+?".includes(this.peek()) ||
					(this.peek() === ":" &&
						this.pos + 1 < this.length &&
						_isSimpleParamOp(this.source[this.pos + 1])))
			) {
				param = "";
			} else {
				// Unknown syntax like ${(M)...} (zsh) - consume until matching }
				// Bash accepts these syntactically but fails at runtime
				// Must track quotes - inside subscripts, quotes span until closed
				depth = 1;
				content_chars = [];
				in_single = false;
				in_double_inner = false;
				while (!this.atEnd() && depth > 0) {
					c = this.peek();
					if (in_single) {
						content_chars.push(this.advance());
						if (c === "'") {
							in_single = false;
						}
						continue;
					}
					if (in_double_inner) {
						if (c === "\\" && this.pos + 1 < this.length) {
							content_chars.push(this.advance());
							if (!this.atEnd()) {
								content_chars.push(this.advance());
							}
							continue;
						}
						content_chars.push(this.advance());
						if (c === '"') {
							in_double_inner = false;
						}
						continue;
					}
					if (c === "'") {
						in_single = true;
						content_chars.push(this.advance());
						continue;
					}
					if (c === '"') {
						in_double_inner = true;
						content_chars.push(this.advance());
						continue;
					}
					if (c === "`") {
						backtick_start = this.pos;
						content_chars.push(this.advance());
						while (!this.atEnd() && this.peek() !== "`") {
							bc = this.peek();
							if (bc === "\\" && this.pos + 1 < this.length) {
								next_c = this.source[this.pos + 1];
								if (_isEscapeCharInDquote(next_c)) {
									content_chars.push(this.advance());
								}
							}
							content_chars.push(this.advance());
						}
						if (this.atEnd()) {
							throw new ParseError("Unterminated backtick", backtick_start);
						}
						content_chars.push(this.advance());
						continue;
					}
					if (
						c === "$" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "{"
					) {
						depth += 1;
						content_chars.push(this.advance());
						content_chars.push(this.advance());
					} else if (c === "}") {
						depth -= 1;
						if (depth === 0) {
							break;
						}
						content_chars.push(this.advance());
					} else if (c === "\\") {
						if (
							this.pos + 1 < this.length &&
							this.source[this.pos + 1] === "\n"
						) {
							// Line continuation - skip both backslash and newline
							this.advance();
							this.advance();
						} else {
							content_chars.push(this.advance());
							if (!this.atEnd()) {
								content_chars.push(this.advance());
							}
						}
					} else {
						content_chars.push(this.advance());
					}
				}
				if (depth === 0) {
					content = content_chars.join("");
					this.advance();
					text = `\${${content}}`;
					return [new ParamExpansion(content), text];
				}
				throw new ParseError("Unclosed parameter expansion", start);
			}
		}
		if (this.atEnd()) {
			this.pos = start;
			return [null, ""];
		}
		// Check for closing brace (simple expansion)
		if (this.peek() === "}") {
			this.advance();
			text = this.source.slice(start, this.pos);
			return [new ParamExpansion(param), text];
		}
		// Parse operator
		op = this._consumeParamOperator();
		if (op == null) {
			// Check for $" or $' which should have $ stripped (locale/ANSI-C quotes)
			if (
				!this.atEnd() &&
				this.peek() === "$" &&
				this.pos + 1 < this.length &&
				['"', "'"].includes(this.source[this.pos + 1])
			) {
				// Count consecutive $ chars to check for $$ (PID param)
				dollar_count =
					1 + _countConsecutiveDollarsBefore(this.source, this.pos);
				if (dollar_count % 2 === 1) {
					// Odd count: locale/ANSI-C string - skip the $ and treat as operator
					this.advance();
					op = "";
				} else {
					// Even count: this $ is part of $$ (PID), treat as unknown operator
					op = this.advance();
				}
			} else if (!this.atEnd() && this.peek() === "`") {
				// Backtick requires matching closing backtick
				backtick_pos = this.pos;
				this.advance();
				while (!this.atEnd() && this.peek() !== "`") {
					bc = this.peek();
					if (bc === "\\" && this.pos + 1 < this.length) {
						next_c = this.source[this.pos + 1];
						if (_isEscapeCharInDquote(next_c)) {
							this.advance();
						}
					}
					this.advance();
				}
				if (this.atEnd()) {
					throw new ParseError("Unterminated backtick", backtick_pos);
				}
				this.advance();
				op = "`";
			} else {
				// Unknown operator - bash still parses these (fails at runtime)
				// Treat the current char as the operator
				op = this.advance();
			}
		}
		// Parse argument (everything until closing brace)
		// Track quote state and nesting
		arg_chars = [];
		depth = 1;
		in_single_quote = false;
		in_double_quote = false;
		while (!this.atEnd() && depth > 0) {
			c = this.peek();
			// Single quotes - no escapes, just scan to closing quote
			if (c === "'" && !in_double_quote) {
				in_single_quote = !in_single_quote;
				arg_chars.push(this.advance());
			} else if (c === '"' && !in_single_quote) {
				// Double quotes - toggle state
				in_double_quote = !in_double_quote;
				arg_chars.push(this.advance());
			} else if (c === "\\" && !in_single_quote) {
				// Escape - skip next char (line continuation removes both)
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === "\n") {
					// Line continuation - skip both backslash and newline
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
				// Nested ${...} - increase depth (outside single quotes)
				depth += 1;
				arg_chars.push(this.advance());
				arg_chars.push(this.advance());
			} else if (
				c === "$" &&
				!in_single_quote &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "'"
			) {
				// ANSI-C quoted string $'...' - scan to matching ' with escapes
				arg_chars.push(this.advance());
				arg_chars.push(this.advance());
				// Scan to closing ' handling escape sequences
				while (!this.atEnd() && this.peek() !== "'") {
					if (this.peek() === "\\") {
						arg_chars.push(this.advance());
						if (!this.atEnd()) {
							arg_chars.push(this.advance());
						}
					} else {
						arg_chars.push(this.advance());
					}
				}
				if (!this.atEnd()) {
					arg_chars.push(this.advance());
				}
			} else if (
				c === "$" &&
				!in_single_quote &&
				!in_double_quote &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === '"'
			) {
				// Locale string $"..." - strip $ and enter double quote
				// Count consecutive $ chars to check for $$ (PID param)
				dollar_count =
					1 + _countConsecutiveDollarsBefore(this.source, this.pos);
				if (dollar_count % 2 === 1) {
					// Odd count: locale string $"..." - strip the $ and enter double quote
					this.advance();
					in_double_quote = true;
					arg_chars.push(this.advance());
				} else {
					// Even count: this $ is part of $$ (PID), keep it
					arg_chars.push(this.advance());
				}
			} else if (
				c === "$" &&
				!in_single_quote &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				// Command substitution $(...) - scan to matching )
				arg_chars.push(this.advance());
				arg_chars.push(this.advance());
				paren_depth = 1;
				while (!this.atEnd() && paren_depth > 0) {
					pc = this.peek();
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
				// Backtick command substitution - scan to matching `
				backtick_start = this.pos;
				arg_chars.push(this.advance());
				while (!this.atEnd() && this.peek() !== "`") {
					bc = this.peek();
					if (bc === "\\" && this.pos + 1 < this.length) {
						next_c = this.source[this.pos + 1];
						if (_isEscapeCharInDquote(next_c)) {
							arg_chars.push(this.advance());
						}
					}
					arg_chars.push(this.advance());
				}
				if (this.atEnd()) {
					throw new ParseError("Unterminated backtick", backtick_start);
				}
				arg_chars.push(this.advance());
			} else if (c === "}") {
				// Closing brace - handle depth for nested ${...}
				if (in_single_quote) {
					// Inside single quotes, } is literal
					arg_chars.push(this.advance());
				} else if (in_double_quote) {
					// Inside double quotes, } can close nested ${...}
					if (depth > 1) {
						depth -= 1;
						arg_chars.push(this.advance());
					} else {
						// Literal } in double quotes (not closing nested)
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
		// Reconstruct text from parsed components (handles line continuation removal)
		text = `\${${param}${op}${arg}}`;
		return [new ParamExpansion(param, op, arg), text];
	}

	_paramSubscriptHasClose(start_pos) {
		let c, depth, i, in_double, in_single;
		depth = 1;
		i = start_pos + 1;
		in_single = false;
		in_double = false;
		while (i < this.length) {
			c = this.source[i];
			if (in_single) {
				if (c === "'") {
					in_single = false;
				}
				i += 1;
				continue;
			}
			if (in_double) {
				if (c === "\\" && i + 1 < this.length) {
					i += 2;
					continue;
				}
				if (c === '"') {
					in_double = false;
				}
				i += 1;
				continue;
			}
			if (c === "'") {
				in_single = true;
				i += 1;
				continue;
			}
			if (c === '"') {
				in_double = true;
				i += 1;
				continue;
			}
			if (c === "\\") {
				i += 2;
				continue;
			}
			if (c === "}") {
				return false;
			}
			if (c === "[") {
				depth += 1;
			} else if (c === "]") {
				depth -= 1;
				if (depth === 0) {
					return true;
				}
			}
			i += 1;
		}
		return false;
	}

	_consumeParamName() {
		let bracket_depth, c, ch, in_double_sub, in_single, name_chars, sc;
		if (this.atEnd()) {
			return null;
		}
		ch = this.peek();
		// Special parameters
		// But NOT $ followed by { - that's a nested ${...} expansion
		if (_isSpecialParam(ch)) {
			if (
				ch === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "{"
			) {
				return null;
			}
			this.advance();
			return ch;
		}
		// Digits (positional params)
		if (/^[0-9]+$/.test(ch)) {
			name_chars = [];
			while (!this.atEnd() && /^[0-9]+$/.test(this.peek())) {
				name_chars.push(this.advance());
			}
			return name_chars.join("");
		}
		// Variable name
		if (/^[a-zA-Z]$/.test(ch) || ch === "_") {
			name_chars = [];
			while (!this.atEnd()) {
				c = this.peek();
				if (/^[a-zA-Z0-9]$/.test(c) || c === "_") {
					name_chars.push(this.advance());
				} else if (c === "[") {
					if (!this._paramSubscriptHasClose(this.pos)) {
						break;
					}
					// Array subscript - track bracket depth and quotes
					name_chars.push(this.advance());
					bracket_depth = 1;
					in_single = false;
					in_double_sub = false;
					while (!this.atEnd() && bracket_depth > 0) {
						sc = this.peek();
						if (in_single) {
							name_chars.push(this.advance());
							if (sc === "'") {
								in_single = false;
							}
							continue;
						}
						if (in_double_sub) {
							if (sc === "\\" && this.pos + 1 < this.length) {
								name_chars.push(this.advance());
								if (!this.atEnd()) {
									name_chars.push(this.advance());
								}
								continue;
							}
							name_chars.push(this.advance());
							if (sc === '"') {
								in_double_sub = false;
							}
							continue;
						}
						if (sc === "'") {
							in_single = true;
							name_chars.push(this.advance());
							continue;
						}
						if (
							sc === "$" &&
							this.pos + 1 < this.length &&
							this.source[this.pos + 1] === '"'
						) {
							// Locale string $"..." - strip the $ and enter double quote
							this.advance();
							in_double_sub = true;
							name_chars.push(this.advance());
							continue;
						}
						if (sc === '"') {
							in_double_sub = true;
							name_chars.push(this.advance());
							continue;
						}
						if (sc === "\\") {
							name_chars.push(this.advance());
							if (!this.atEnd()) {
								name_chars.push(this.advance());
							}
							continue;
						}
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

	_consumeParamOperator() {
		let ch, next_ch;
		if (this.atEnd()) {
			return null;
		}
		ch = this.peek();
		// Operators with optional colon prefix: :- := :? :+
		if (ch === ":") {
			this.advance();
			if (this.atEnd()) {
				return ":";
			}
			next_ch = this.peek();
			if (_isSimpleParamOp(next_ch)) {
				this.advance();
				return `:${next_ch}`;
			}
			// Just : (substring)
			return ":";
		}
		// Operators without colon: - = ? +
		if (_isSimpleParamOp(ch)) {
			this.advance();
			return ch;
		}
		// Pattern removal: # ## % %%
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
		// Substitution: / // /# /%
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
		// Case modification: ^ ^^ , ,,
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
		// Transformation: @
		if (ch === "@") {
			this.advance();
			return "@";
		}
		return null;
	}

	parseRedirect() {
		let base,
			c,
			ch,
			fd,
			fd_chars,
			fd_target,
			in_bracket,
			inner_word,
			is_valid_varfd,
			left,
			next_ch,
			op,
			right,
			saved,
			start,
			strip_tabs,
			target,
			varfd,
			varname,
			varname_chars,
			word_start;
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		start = this.pos;
		fd = null;
		varfd = null;
		// Check for variable fd {varname} or {varname[subscript]} before redirect
		if (this.peek() === "{") {
			saved = this.pos;
			this.advance();
			varname_chars = [];
			in_bracket = false;
			while (!this.atEnd() && !_isRedirectChar(this.peek())) {
				ch = this.peek();
				if (ch === "}" && !in_bracket) {
					break;
				} else if (ch === "[") {
					in_bracket = true;
					varname_chars.push(this.advance());
				} else if (ch === "]") {
					in_bracket = false;
					varname_chars.push(this.advance());
				} else if (/^[a-zA-Z0-9]$/.test(ch) || ch === "_") {
					varname_chars.push(this.advance());
				} else if (in_bracket && !_isMetachar(ch)) {
					varname_chars.push(this.advance());
				} else {
					break;
				}
			}
			varname = varname_chars.join("");
			is_valid_varfd = false;
			if (varname) {
				if (/^[a-zA-Z]$/.test(varname[0]) || varname[0] === "_") {
					if (varname.includes("[") || varname.includes("]")) {
						left = varname.indexOf("[");
						right = varname.lastIndexOf("]");
						if (
							left !== -1 &&
							right === varname.length - 1 &&
							right > left + 1
						) {
							base = varname.slice(0, left);
							if (
								base.length > 0 &&
								(/^[a-zA-Z]$/.test(base[0]) || base[0] === "_")
							) {
								is_valid_varfd = true;
								for (c of base.slice(1)) {
									if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
										is_valid_varfd = false;
										break;
									}
								}
							}
						}
					} else {
						is_valid_varfd = true;
						for (c of varname.slice(1)) {
							if (!(/^[a-zA-Z0-9]$/.test(c) || c === "_")) {
								is_valid_varfd = false;
								break;
							}
						}
					}
				}
			}
			if (!this.atEnd() && this.peek() === "}" && is_valid_varfd) {
				this.advance();
				varfd = varname;
			} else {
				// Not a valid variable fd, restore
				this.pos = saved;
			}
		}
		// Check for optional fd number before redirect (if no varfd)
		if (varfd == null && this.peek() && /^[0-9]+$/.test(this.peek())) {
			fd_chars = [];
			while (!this.atEnd() && /^[0-9]+$/.test(this.peek())) {
				fd_chars.push(this.advance());
			}
			fd = parseInt(fd_chars.join(""), 10);
		}
		ch = this.peek();
		// Handle &> and &>> (redirect both stdout and stderr)
		// Note: &> does NOT take a preceding fd number. If we consumed digits,
		// they should be a separate word, not an fd. E.g., "2&>1" is command "2"
		// with redirect "&> 1", not fd 2 redirected.
		if (
			ch === "&" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === ">"
		) {
			if (fd != null || varfd != null) {
				// We consumed digits/varfd that should be a word, not an fd
				// Restore position and let parse_word handle them
				this.pos = start;
				return null;
			}
			this.advance();
			this.advance();
			if (!this.atEnd() && this.peek() === ">") {
				this.advance();
				op = "&>>";
			} else {
				op = "&>";
			}
			this.skipWhitespace();
			target = this.parseWord();
			if (target == null) {
				throw new ParseError(`Expected target for redirect ${op}`, this.pos);
			}
			return new Redirect(op, target);
		}
		if (ch == null || !_isRedirectChar(ch)) {
			// Not a redirect, restore position
			this.pos = start;
			return null;
		}
		// Check for process substitution <(...) or >(...) - not a redirect
		// Only treat as redirect if there's a space before ( or an fd number
		if (
			fd == null &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			// This is a process substitution, not a redirect
			this.pos = start;
			return null;
		}
		// Parse the redirect operator
		op = this.advance();
		// Check for multi-char operators
		strip_tabs = false;
		if (!this.atEnd()) {
			next_ch = this.peek();
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
				// Handle <> (read-write)
				this.advance();
				op = "<>";
			} else if (op === ">" && next_ch === "|") {
				// Handle >| (noclobber override)
				this.advance();
				op = ">|";
			} else if (fd == null && varfd == null && op === ">" && next_ch === "&") {
				// Only consume >& or <& as operators if NOT followed by a digit or -
				// (>&2 should be > with target &2, not >& with target 2)
				// (>&- should be > with target &-, not >& with target -)
				// Peek ahead to see if there's a digit or - after &
				if (
					this.pos + 1 >= this.length ||
					!_isDigitOrDash(this.source[this.pos + 1])
				) {
					this.advance();
					op = ">&";
				}
			} else if (fd == null && varfd == null && op === "<" && next_ch === "&") {
				if (
					this.pos + 1 >= this.length ||
					!_isDigitOrDash(this.source[this.pos + 1])
				) {
					this.advance();
					op = "<&";
				}
			}
		}
		// Handle here document
		if (op === "<<") {
			return this._parseHeredoc(fd, strip_tabs);
		}
		// Combine fd or varfd with operator if present
		if (varfd != null) {
			op = `{${varfd}}${op}`;
		} else if (fd != null) {
			op = String(fd) + op;
		}
		// Handle fd duplication targets like &1, &2, &-, &10-, &$var
		// NOTE: No whitespace allowed between operator and & (e.g., <&- is valid, < &- is not)
		if (!this.atEnd() && this.peek() === "&") {
			this.advance();
			// Skip whitespace after & to check what follows
			this.skipWhitespace();
			// Check for "& -" followed by non-metachar (e.g., "3>& -5" -> 3>&- + word "5")
			if (!this.atEnd() && this.peek() === "-") {
				if (
					this.pos + 1 < this.length &&
					!_isMetachar(this.source[this.pos + 1])
				) {
					// Consume just the - as close target, leave rest for next word
					this.advance();
					target = new Word("&-");
				} else {
					// Set target to None to fall through to normal parsing
					target = null;
				}
			} else {
				target = null;
			}
			// If we didn't handle close syntax above, continue with normal parsing
			if (target == null) {
				if (
					!this.atEnd() &&
					(/^[0-9]+$/.test(this.peek()) || this.peek() === "-")
				) {
					word_start = this.pos;
					fd_chars = [];
					while (!this.atEnd() && /^[0-9]+$/.test(this.peek())) {
						fd_chars.push(this.advance());
					}
					if (fd_chars) {
						fd_target = fd_chars.join("");
					} else {
						fd_target = "";
					}
					// Handle just - for close, or N- for move syntax
					if (!this.atEnd() && this.peek() === "-") {
						fd_target += this.advance();
					}
					// If more word characters follow, treat the whole target as a word (e.g., <&0=)
					// BUT: bare "-" (close syntax) is always complete - trailing chars are separate words
					if (fd_target !== "-" && !this.atEnd() && !_isMetachar(this.peek())) {
						this.pos = word_start;
						inner_word = this.parseWord();
						if (inner_word != null) {
							target = new Word(`&${inner_word.value}`);
							target.parts = inner_word.parts;
						} else {
							throw new ParseError(
								`Expected target for redirect ${op}`,
								this.pos,
							);
						}
					} else {
						target = new Word(`&${fd_target}`);
					}
				} else {
					// Could be &$var or &word - parse word and prepend &
					inner_word = this.parseWord();
					if (inner_word != null) {
						target = new Word(`&${inner_word.value}`);
						target.parts = inner_word.parts;
					} else {
						throw new ParseError(
							`Expected target for redirect ${op}`,
							this.pos,
						);
					}
				}
			}
		} else {
			this.skipWhitespace();
			// Handle >& - or <& - where space precedes the close syntax
			// If op is >& or <& and next char is -, check for trailing word chars
			// that should become a separate word (e.g., ">& -b" -> >&- + word "b")
			if ([">&", "<&"].includes(op) && !this.atEnd() && this.peek() === "-") {
				if (
					this.pos + 1 < this.length &&
					!_isMetachar(this.source[this.pos + 1])
				) {
					// Consume just the - as close target, leave rest for next word
					this.advance();
					target = new Word("&-");
				} else {
					target = this.parseWord();
				}
			} else {
				target = this.parseWord();
			}
		}
		if (target == null) {
			throw new ParseError(`Expected target for redirect ${op}`, this.pos);
		}
		return new Redirect(op, target);
	}

	_parseHeredoc(fd, strip_tabs) {
		let add_newline,
			c,
			ch,
			check_line,
			content,
			content_lines,
			content_start,
			delimiter,
			delimiter_chars,
			depth,
			dollar_count,
			esc,
			esc_val,
			heredoc_end,
			i,
			j,
			line,
			line_end,
			line_start,
			next_ch,
			next_line_start,
			quoted,
			scan_pos,
			tabs_stripped,
			trailing_bs;
		this.skipWhitespace();
		// Parse the delimiter, handling quoting (can be mixed like 'EOF'"2")
		quoted = false;
		delimiter_chars = [];
		while (true) {
			while (!this.atEnd() && !_isMetachar(this.peek())) {
				ch = this.peek();
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
						c = this.advance();
						if (c === "\n") {
							this._saw_newline_in_single_quote = true;
						}
						delimiter_chars.push(c);
					}
					if (!this.atEnd()) {
						this.advance();
					}
				} else if (ch === "\\") {
					this.advance();
					if (!this.atEnd()) {
						next_ch = this.peek();
						if (next_ch === "\n") {
							// Backslash-newline: continue delimiter on next line
							this.advance();
						} else {
							// Regular escape - quotes the next char
							quoted = true;
							delimiter_chars.push(this.advance());
						}
					}
				} else if (
					ch === "$" &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === "'"
				) {
					// ANSI-C quoting $'...' - skip $ and quotes, expand escapes
					quoted = true;
					this.advance();
					this.advance();
					while (!this.atEnd() && this.peek() !== "'") {
						c = this.peek();
						if (c === "\\" && this.pos + 1 < this.length) {
							this.advance();
							esc = this.peek();
							// Handle ANSI-C escapes using the lookup table
							esc_val = _getAnsiEscape(esc);
							if (esc_val >= 0) {
								delimiter_chars.push(String.fromCodePoint(esc_val));
								this.advance();
							} else if (esc === "'") {
								delimiter_chars.push(this.advance());
							} else {
								// Other escapes - just use the escaped char
								delimiter_chars.push(this.advance());
							}
						} else {
							delimiter_chars.push(this.advance());
						}
					}
					if (!this.atEnd()) {
						this.advance();
					}
				} else if (
					ch === "$" &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === "("
				) {
					// Command substitution embedded in delimiter
					delimiter_chars.push(this.advance());
					delimiter_chars.push(this.advance());
					depth = 1;
					while (!this.atEnd() && depth > 0) {
						c = this.peek();
						if (c === "(") {
							depth += 1;
						} else if (c === ")") {
							depth -= 1;
						}
						delimiter_chars.push(this.advance());
					}
				} else if (
					ch === "$" &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === "{"
				) {
					// Check if this is $${ where $$ is PID and { ends delimiter
					dollar_count = 0;
					j = this.pos - 1;
					while (j >= 0 && this.source[j] === "$") {
						dollar_count += 1;
						j -= 1;
					}
					if (dollar_count % 2 === 1) {
						// Odd number of $ before: this $ pairs with previous to form $$
						// Don't consume the {, let it end the delimiter
						delimiter_chars.push(this.advance());
					} else {
						// Parameter expansion embedded in delimiter
						delimiter_chars.push(this.advance());
						delimiter_chars.push(this.advance());
						depth = 1;
						while (!this.atEnd() && depth > 0) {
							c = this.peek();
							if (c === "{") {
								depth += 1;
							} else if (c === "}") {
								depth -= 1;
							}
							delimiter_chars.push(this.advance());
						}
					}
				} else if (
					ch === "$" &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === "["
				) {
					// Check if this is $$[ where $$ is PID and [ ends delimiter
					dollar_count = 0;
					j = this.pos - 1;
					while (j >= 0 && this.source[j] === "$") {
						dollar_count += 1;
						j -= 1;
					}
					if (dollar_count % 2 === 1) {
						// Odd number of $ before: this $ pairs with previous to form $$
						// Don't consume the [, let it end the delimiter
						delimiter_chars.push(this.advance());
					} else {
						// Arithmetic expansion $[...] embedded in delimiter
						delimiter_chars.push(this.advance());
						delimiter_chars.push(this.advance());
						depth = 1;
						while (!this.atEnd() && depth > 0) {
							c = this.peek();
							if (c === "[") {
								depth += 1;
							} else if (c === "]") {
								depth -= 1;
							}
							delimiter_chars.push(this.advance());
						}
					}
				} else if (ch === "`") {
					// Backtick command substitution embedded in delimiter
					// Note: In bash, backtick closes command sub even with unclosed quotes inside
					delimiter_chars.push(this.advance());
					while (!this.atEnd() && this.peek() !== "`") {
						c = this.peek();
						if (c === "'") {
							// Single-quoted string inside backtick - skip to closing quote or `
							delimiter_chars.push(this.advance());
							while (
								!this.atEnd() &&
								this.peek() !== "'" &&
								this.peek() !== "`"
							) {
								delimiter_chars.push(this.advance());
							}
							if (!this.atEnd() && this.peek() === "'") {
								delimiter_chars.push(this.advance());
							}
						} else if (c === '"') {
							// Double-quoted string inside backtick - skip to closing quote or `
							delimiter_chars.push(this.advance());
							while (
								!this.atEnd() &&
								this.peek() !== '"' &&
								this.peek() !== "`"
							) {
								if (this.peek() === "\\" && this.pos + 1 < this.length) {
									delimiter_chars.push(this.advance());
								}
								delimiter_chars.push(this.advance());
							}
							if (!this.atEnd() && this.peek() === '"') {
								delimiter_chars.push(this.advance());
							}
						} else if (c === "\\" && this.pos + 1 < this.length) {
							delimiter_chars.push(this.advance());
							delimiter_chars.push(this.advance());
						} else {
							delimiter_chars.push(this.advance());
						}
					}
					if (!this.atEnd()) {
						delimiter_chars.push(this.advance());
					}
				} else {
					delimiter_chars.push(this.advance());
				}
			}
			// Check for process substitution syntax <( or >( which is part of delimiter
			if (
				!this.atEnd() &&
				"<>".includes(this.peek()) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				// Process substitution embedded in delimiter
				delimiter_chars.push(this.advance());
				delimiter_chars.push(this.advance());
				depth = 1;
				while (!this.atEnd() && depth > 0) {
					c = this.peek();
					if (c === "(") {
						depth += 1;
					} else if (c === ")") {
						depth -= 1;
					}
					delimiter_chars.push(this.advance());
				}
				continue;
			}
			break;
		}
		delimiter = delimiter_chars.join("");
		// Find the end of the current line (command continues until newline)
		// We need to mark where the heredoc content starts
		// Must be quote-aware - newlines inside quoted strings don't end the line
		line_end = this.pos;
		while (line_end < this.length && this.source[line_end] !== "\n") {
			ch = this.source[line_end];
			if (ch === "#") {
				// Comment - skip to end of line (don't parse quotes in comments)
				while (line_end < this.length && this.source[line_end] !== "\n") {
					line_end += 1;
				}
				break;
			} else if (ch === "'") {
				// Single-quoted string - skip to closing quote (no escapes)
				line_end += 1;
				while (line_end < this.length && this.source[line_end] !== "'") {
					line_end += 1;
				}
			} else if (ch === '"') {
				// Double-quoted string - skip to closing quote (with escapes)
				line_end += 1;
				while (line_end < this.length && this.source[line_end] !== '"') {
					if (this.source[line_end] === "\\" && line_end + 1 < this.length) {
						line_end += 2;
					} else {
						line_end += 1;
					}
				}
			} else if (ch === "`") {
				// Backtick command substitution - skip to closing backtick
				line_end += 1;
				while (line_end < this.length && this.source[line_end] !== "`") {
					if (this.source[line_end] === "\\" && line_end + 1 < this.length) {
						line_end += 2;
					} else {
						line_end += 1;
					}
				}
			} else if (ch === "\\") {
				if (line_end + 1 < this.length) {
					// Backslash escape - skip both chars
					line_end += 2;
					continue;
				} else {
					// Backslash at EOF - treat as attempted line continuation
					// Bash consumes this without an error
					line_end += 1;
					break;
				}
			}
			line_end += 1;
		}
		// Find heredoc content starting position
		// If there's already a pending heredoc, this one's content starts after that
		if (
			this._pending_heredoc_end != null &&
			this._pending_heredoc_end > line_end
		) {
			content_start = this._pending_heredoc_end;
		} else if (line_end < this.length) {
			content_start = line_end + 1;
		} else {
			content_start = this.length;
		}
		// Find the delimiter line
		content_lines = [];
		scan_pos = content_start;
		while (scan_pos < this.length) {
			// Find end of current line
			line_start = scan_pos;
			line_end = scan_pos;
			while (line_end < this.length && this.source[line_end] !== "\n") {
				line_end += 1;
			}
			line = this.source.slice(line_start, line_end);
			// For unquoted heredocs, process backslash-newline before checking delimiter
			// Join continued lines to check the full logical line against delimiter
			// Only odd number of trailing backslashes means continuation (even = literal)
			if (!quoted) {
				while (line_end < this.length) {
					// Count trailing backslashes
					trailing_bs = 0;
					for (i = line.length - 1; i > -1; i--) {
						if (line[i] === "\\") {
							trailing_bs += 1;
						} else {
							break;
						}
					}
					if (trailing_bs % 2 === 0) {
						break;
					}
					// Odd backslashes - line continuation
					line = line.slice(0, line.length - 1);
					line_end += 1;
					next_line_start = line_end;
					while (line_end < this.length && this.source[line_end] !== "\n") {
						line_end += 1;
					}
					line = line + this.source.slice(next_line_start, line_end);
				}
			}
			// Check if this line is the delimiter
			check_line = line;
			if (strip_tabs) {
				check_line = line.replace(/^[\t]+/, "");
			}
			if (check_line === delimiter) {
				// Found the end - update parser position past the heredoc
				// We need to consume the heredoc content from the input
				// But we can't do that here because we haven't finished parsing the command line
				// Store the heredoc info and let the command parser handle it
				break;
			}
			// At EOF with line starting with delimiter - heredoc terminates (process sub case)
			// e.g. <(<<a\na ) - the "a " line starts with delimiter "a" and we're at EOF
			// In command substitutions, bash accepts the delimiter prefix and treats
			// remaining characters as subsequent commands (e.g., <<X\nXb → X is delimiter, b is command)
			if (
				line_end >= this.length &&
				check_line.startsWith(delimiter) &&
				this._in_process_sub
			) {
				// At EOF in process/command sub, treat delimiter prefix as matching
				// Adjust line_end to point just past the delimiter, not the whole line
				// This allows remaining content after delimiter to be parsed as commands
				tabs_stripped = line.length - check_line.length;
				line_end = line_start + tabs_stripped + delimiter.length;
				break;
			}
			// Add line to content (with newline, since we consumed continuations above)
			if (strip_tabs) {
				line = line.replace(/^[\t]+/, "");
			}
			// Only add newline if there was actually a newline in the source (not EOF)
			if (line_end < this.length) {
				content_lines.push(`${line}\n`);
				scan_pos = line_end + 1;
			} else {
				// EOF - bash keeps the trailing newline unless escaped by an odd backslash
				add_newline = true;
				if (!quoted) {
					trailing_bs = 0;
					for (i = line.length - 1; i > -1; i--) {
						if (line[i] === "\\") {
							trailing_bs += 1;
						} else {
							break;
						}
					}
					if (trailing_bs % 2 === 1) {
						add_newline = false;
					}
				}
				content_lines.push(line + (add_newline ? "\n" : ""));
				scan_pos = this.length;
			}
		}
		// Join content (newlines already included per line)
		content = content_lines.join("");
		// Store the position where heredoc content ends so we can skip it later
		// line_end points to the end of the delimiter line (after any continuations)
		heredoc_end = line_end;
		if (heredoc_end < this.length && this.source[heredoc_end] === "\n") {
			heredoc_end += 1;
		}
		// Register this heredoc's end position
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
		let all_assignments, ch, next_pos, redirect, redirects, w, word, words;
		words = [];
		redirects = [];
		while (true) {
			this.skipWhitespace();
			if (this.atEnd()) {
				break;
			}
			ch = this.peek();
			// Check for command terminators, but &> and &>> are redirects, not terminators
			if (_isListTerminator(ch)) {
				break;
			}
			if (
				ch === "&" &&
				!(this.pos + 1 < this.length && this.source[this.pos + 1] === ">")
			) {
				break;
			}
			// } is only a terminator at command position (closing a brace group)
			// In argument position, } is just a regular word
			if (this.peek() === "}" && !words) {
				// Check if } would be a standalone word (next char is whitespace/meta/EOF)
				next_pos = this.pos + 1;
				if (
					next_pos >= this.length ||
					_isWordEndContext(this.source[next_pos])
				) {
					break;
				}
			}
			// Try to parse a redirect first
			redirect = this.parseRedirect();
			if (redirect != null) {
				redirects.push(redirect);
				continue;
			}
			// Otherwise parse a word
			// Allow array assignments like a[1 + 2]= in prefix position (before first non-assignment)
			// Check if all previous words were assignments (contain = not inside quotes)
			// and no redirects have been seen (redirects break assignment context)
			all_assignments = true;
			for (w of words) {
				if (!this._isAssignmentWord(w)) {
					all_assignments = false;
					break;
				}
			}
			word = this.parseWord(
				!words || (all_assignments && redirects.length === 0),
			);
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
		let body;
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== "(") {
			return null;
		}
		this.advance();
		body = this.parseList();
		if (body == null) {
			throw new ParseError("Expected command in subshell", this.pos);
		}
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== ")") {
			throw new ParseError("Expected ) to close subshell", this.pos);
		}
		this.advance();
		return new Subshell(body, this._collectRedirects());
	}

	parseArithmeticCommand() {
		let c, content, content_start, depth, expr, saved_pos;
		this.skipWhitespace();
		// Check for ((
		if (
			this.atEnd() ||
			this.peek() !== "(" ||
			this.pos + 1 >= this.length ||
			this.source[this.pos + 1] !== "("
		) {
			return null;
		}
		saved_pos = this.pos;
		this.advance();
		this.advance();
		// Find matching )) - track nested parens
		// Must be )) with no space between - ') )' is nested subshells
		content_start = this.pos;
		depth = 1;
		while (!this.atEnd() && depth > 0) {
			c = this.peek();
			// Skip single-quoted strings (parens inside don't count)
			if (c === "'") {
				this.advance();
				while (!this.atEnd() && this.peek() !== "'") {
					this.advance();
				}
				if (!this.atEnd()) {
					this.advance();
				}
			} else if (c === '"') {
				// Skip double-quoted strings (parens inside don't count)
				this.advance();
				while (!this.atEnd()) {
					if (this.peek() === "\\" && this.pos + 1 < this.length) {
						this.advance();
						this.advance();
					} else if (this.peek() === '"') {
						this.advance();
						break;
					} else {
						this.advance();
					}
				}
			} else if (c === "\\" && this.pos + 1 < this.length) {
				// Handle backslash escapes outside quotes
				this.advance();
				this.advance();
			} else if (c === "(") {
				depth += 1;
				this.advance();
			} else if (c === ")") {
				// Check for )) (must be consecutive, no space)
				if (
					depth === 1 &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === ")"
				) {
					// Found the closing ))
					break;
				}
				depth -= 1;
				if (depth === 0) {
					// Closed with ) but next isn't ) - this is nested subshells, not arithmetic
					this.pos = saved_pos;
					return null;
				}
				this.advance();
			} else {
				this.advance();
			}
		}
		if (this.atEnd() || depth !== 1) {
			// Didn't find )) - might be nested subshells or malformed
			this.pos = saved_pos;
			return null;
		}
		content = this.source.slice(content_start, this.pos);
		// Strip backslash-newline line continuations
		content = content.replaceAll("\\\n", "");
		this.advance();
		this.advance();
		// Parse the arithmetic expression
		expr = this._parseArithExpr(content);
		return new ArithmeticCommand(expr, this._collectRedirects(), content);
	}

	// Unary operators for [[ ]] conditionals
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
	// Binary operators for [[ ]] conditionals
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
		let body, next_pos;
		this.skipWhitespace();
		// Check for [[
		if (
			this.atEnd() ||
			this.peek() !== "[" ||
			this.pos + 1 >= this.length ||
			this.source[this.pos + 1] !== "["
		) {
			return null;
		}
		next_pos = this.pos + 2;
		if (
			next_pos < this.length &&
			!(
				_isWhitespace(this.source[next_pos]) ||
				(this.source[next_pos] === "\\" &&
					next_pos + 1 < this.length &&
					this.source[next_pos + 1] === "\n")
			)
		) {
			return null;
		}
		this.advance();
		this.advance();
		// Parse the conditional expression body
		body = this._parseCondOr();
		// Skip whitespace before ]]
		while (!this.atEnd() && _isWhitespaceNoNewline(this.peek())) {
			this.advance();
		}
		// Expect ]]
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
		return new ConditionalExpr(body, this._collectRedirects());
	}

	_condSkipWhitespace() {
		while (!this.atEnd()) {
			if (_isWhitespaceNoNewline(this.peek())) {
				this.advance();
			} else if (
				this.peek() === "\\" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "\n"
			) {
				this.advance();
				this.advance();
			} else if (this.peek() === "\n") {
				// Bare newline is also allowed inside [[ ]]
				this.advance();
			} else {
				break;
			}
		}
	}

	_condAtEnd() {
		return (
			this.atEnd() ||
			(this.peek() === "]" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "]")
		);
	}

	_parseCondOr() {
		let left, right;
		this._condSkipWhitespace();
		left = this._parseCondAnd();
		this._condSkipWhitespace();
		if (
			!this._condAtEnd() &&
			this.peek() === "|" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "|"
		) {
			this.advance();
			this.advance();
			right = this._parseCondOr();
			return new CondOr(left, right);
		}
		return left;
	}

	_parseCondAnd() {
		let left, right;
		this._condSkipWhitespace();
		left = this._parseCondTerm();
		this._condSkipWhitespace();
		if (
			!this._condAtEnd() &&
			this.peek() === "&" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "&"
		) {
			this.advance();
			this.advance();
			right = this._parseCondAnd();
			return new CondAnd(left, right);
		}
		return left;
	}

	_parseCondTerm() {
		let inner, op, op_word, operand, saved_pos, word1, word2;
		this._condSkipWhitespace();
		if (this._condAtEnd()) {
			throw new ParseError(
				"Unexpected end of conditional expression",
				this.pos,
			);
		}
		// Negation: ! term
		if (this.peek() === "!") {
			// Check it's not != operator (need whitespace after !)
			if (
				this.pos + 1 < this.length &&
				!_isWhitespaceNoNewline(this.source[this.pos + 1])
			) {
			} else {
				this.advance();
				operand = this._parseCondTerm();
				return new CondNot(operand);
			}
		}
		// Parenthesized group: ( or_expr )
		if (this.peek() === "(") {
			this.advance();
			inner = this._parseCondOr();
			this._condSkipWhitespace();
			if (this.atEnd() || this.peek() !== ")") {
				throw new ParseError("Expected ) in conditional expression", this.pos);
			}
			this.advance();
			return new CondParen(inner);
		}
		// Parse first word
		word1 = this._parseCondWord();
		if (word1 == null) {
			throw new ParseError("Expected word in conditional expression", this.pos);
		}
		this._condSkipWhitespace();
		// Check if word1 is a unary operator
		if (COND_UNARY_OPS.has(word1.value)) {
			// Unary test: -f file
			operand = this._parseCondWord();
			if (operand == null) {
				throw new ParseError(`Expected operand after ${word1.value}`, this.pos);
			}
			return new UnaryTest(word1.value, operand);
		}
		// Check if next token is a binary operator
		if (
			!this._condAtEnd() &&
			this.peek() !== "&" &&
			this.peek() !== "|" &&
			this.peek() !== ")"
		) {
			// Handle < and > as binary operators (they terminate words)
			// But not <( or >( which are process substitution
			if (
				_isRedirectChar(this.peek()) &&
				!(this.pos + 1 < this.length && this.source[this.pos + 1] === "(")
			) {
				op = this.advance();
				this._condSkipWhitespace();
				word2 = this._parseCondWord();
				if (word2 == null) {
					throw new ParseError(`Expected operand after ${op}`, this.pos);
				}
				return new BinaryTest(op, word1, word2);
			}
			// Peek at next word to see if it's a binary operator
			saved_pos = this.pos;
			op_word = this._parseCondWord();
			if (op_word && COND_BINARY_OPS.has(op_word.value)) {
				// Binary test: word1 op word2
				this._condSkipWhitespace();
				// For =~ operator, the RHS is a regex where ( ) are grouping, not conditional grouping
				if (op_word.value === "=~") {
					word2 = this._parseCondRegexWord();
				} else {
					word2 = this._parseCondWord();
				}
				if (word2 == null) {
					throw new ParseError(
						`Expected operand after ${op_word.value}`,
						this.pos,
					);
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

	_parseCondWord() {
		let ansi_node,
			ansi_result,
			ansi_text,
			arith_node,
			arith_result,
			arith_text,
			c,
			ch,
			chars,
			cmdsub_node,
			cmdsub_result,
			cmdsub_text,
			depth,
			inner_parts,
			locale_node,
			locale_result,
			locale_text,
			next_c,
			next_ch,
			param_node,
			param_result,
			param_text,
			parts,
			parts_arg,
			procsub_node,
			procsub_result,
			procsub_text,
			start;
		this._condSkipWhitespace();
		if (this._condAtEnd()) {
			return null;
		}
		// Check for special tokens that aren't words
		c = this.peek();
		if (_isParen(c)) {
			return null;
		}
		// Note: ! alone is handled by _parse_cond_term() as negation operator
		// Here we allow ! as a word so it can be used as pattern in binary tests
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
		start = this.pos;
		chars = [];
		parts = [];
		while (!this.atEnd()) {
			ch = this.peek();
			// End of conditional
			if (
				ch === "]" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "]"
			) {
				break;
			}
			// Word terminators in conditionals
			if (_isWhitespaceNoNewline(ch)) {
				break;
			}
			// < and > are string comparison operators in [[ ]], terminate words
			// But <(...) and >(...) are process substitution - don't break
			if (
				_isRedirectChar(ch) &&
				!(this.pos + 1 < this.length && this.source[this.pos + 1] === "(")
			) {
				break;
			}
			// ( and ) end words unless part of extended glob: @(...), ?(...), *(...), +(...), !(...)
			if (ch === "(") {
				// Check if this is an extended glob (preceded by @, ?, *, +, or !)
				if (chars.length > 0 && _isExtglobPrefix(chars[chars.length - 1])) {
					// Extended glob - consume the parenthesized content
					chars.push(this.advance());
					depth = 1;
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
			// Semicolons are not valid inside conditionals
			if (ch === ";") {
				break;
			}
			// Glob bracket expression [...] - consume until closing ]
			// Handles [[:alpha:]], [^0-9], []a-z] (] as first char), etc.
			if (ch === "[") {
				// Check if [ is immediately followed by whitespace or terminator
				// If so, treat [ as literal, not as bracket expression start
				if (this.pos + 1 >= this.length) {
					// [ at EOF is literal
					chars.push(this.advance());
					continue;
				}
				next_ch = this.source[this.pos + 1];
				if (_isWhitespaceNoNewline(next_ch)) {
					// [ followed by whitespace is literal
					chars.push(this.advance());
					continue;
				}
				chars.push(this.advance());
				// Handle negation [^
				if (!this.atEnd() && this.peek() === "^") {
					chars.push(this.advance());
				}
				// Handle ] as first char (literal ])
				if (!this.atEnd() && this.peek() === "]") {
					chars.push(this.advance());
				}
				// Consume until closing ]
				while (!this.atEnd()) {
					c = this.peek();
					if (c === "]") {
						chars.push(this.advance());
						break;
					}
					if (
						c === "[" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === ":"
					) {
						// POSIX class like [:alpha:] inside bracket expression
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
					} else if (
						c === "[" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "="
					) {
						// Equivalence class like [=a=] inside bracket expression
						chars.push(this.advance());
						chars.push(this.advance());
						while (
							!this.atEnd() &&
							!(
								this.peek() === "=" &&
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
					} else if (
						c === "[" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "."
					) {
						// Collating symbol like [.ch.] inside bracket expression
						chars.push(this.advance());
						chars.push(this.advance());
						while (
							!this.atEnd() &&
							!(
								this.peek() === "." &&
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
			// Single-quoted string
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
				// Double-quoted string
				this.advance();
				chars.push('"');
				while (!this.atEnd() && this.peek() !== '"') {
					c = this.peek();
					if (c === "\\" && this.pos + 1 < this.length) {
						next_c = this.source[this.pos + 1];
						if (next_c === "\n") {
							// Line continuation - skip both backslash and newline
							this.advance();
							this.advance();
						} else {
							chars.push(this.advance());
							chars.push(this.advance());
						}
					} else if (c === "$") {
						// Handle expansions inside double quotes
						if (
							this.pos + 2 < this.length &&
							this.source[this.pos + 1] === "(" &&
							this.source[this.pos + 2] === "("
						) {
							arith_result = this._parseArithmeticExpansion();
							arith_node = arith_result[0];
							arith_text = arith_result[1];
							if (arith_node) {
								parts.push(arith_node);
								chars.push(arith_text);
							} else {
								// Not arithmetic - try command substitution
								cmdsub_result = this._parseCommandSubstitution();
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
							this.pos + 1 < this.length &&
							this.source[this.pos + 1] === "("
						) {
							cmdsub_result = this._parseCommandSubstitution();
							cmdsub_node = cmdsub_result[0];
							cmdsub_text = cmdsub_result[1];
							if (cmdsub_node) {
								parts.push(cmdsub_node);
								chars.push(cmdsub_text);
							} else {
								chars.push(this.advance());
							}
						} else {
							param_result = this._parseParamExpansion();
							param_node = param_result[0];
							param_text = param_result[1];
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
				// Escape
				chars.push(this.advance());
				chars.push(this.advance());
			} else if (
				ch === "$" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "'"
			) {
				// ANSI-C quoting $'...'
				ansi_result = this._parseAnsiCQuote();
				ansi_node = ansi_result[0];
				ansi_text = ansi_result[1];
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
				// Locale translation $"..."
				locale_result = this._parseLocaleString();
				locale_node = locale_result[0];
				locale_text = locale_result[1];
				inner_parts = locale_result[2];
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
				// Arithmetic expansion $((...))
				arith_result = this._parseArithmeticExpansion();
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
				// Command substitution $(...)
				cmdsub_result = this._parseCommandSubstitution();
				cmdsub_node = cmdsub_result[0];
				cmdsub_text = cmdsub_result[1];
				if (cmdsub_node) {
					parts.push(cmdsub_node);
					chars.push(cmdsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "$") {
				// Parameter expansion $var or ${...}
				param_result = this._parseParamExpansion();
				param_node = param_result[0];
				param_text = param_result[1];
				if (param_node) {
					parts.push(param_node);
					chars.push(param_text);
				} else {
					chars.push(this.advance());
				}
			} else if (
				_isRedirectChar(ch) &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "("
			) {
				// Process substitution <(...) or >(...)
				procsub_result = this._parseProcessSubstitution();
				procsub_node = procsub_result[0];
				procsub_text = procsub_result[1];
				if (procsub_node) {
					parts.push(procsub_node);
					chars.push(procsub_text);
				} else {
					chars.push(this.advance());
				}
			} else if (ch === "`") {
				// Backtick command substitution
				cmdsub_result = this._parseBacktickSubstitution();
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
		parts_arg = null;
		if (parts && parts.length) {
			parts_arg = parts;
		}
		return new Word(chars.join(""), parts_arg);
	}

	_parseCondRegexWord() {
		let arith_node,
			arith_result,
			arith_text,
			bracket_will_close,
			c,
			ch,
			chars,
			cmdsub_node,
			cmdsub_result,
			cmdsub_text,
			param_node,
			param_result,
			param_text,
			paren_depth,
			parts,
			parts_arg,
			sc,
			scan,
			start;
		this._condSkipWhitespace();
		if (this._condAtEnd()) {
			return null;
		}
		start = this.pos;
		chars = [];
		parts = [];
		paren_depth = 0;
		while (!this.atEnd()) {
			ch = this.peek();
			// End of conditional
			if (
				ch === "]" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "]"
			) {
				break;
			}
			// Backslash-newline continuation (check before space/escape handling)
			if (
				ch === "\\" &&
				this.pos + 1 < this.length &&
				this.source[this.pos + 1] === "\n"
			) {
				this.advance();
				this.advance();
				continue;
			}
			// Escape sequences - consume both characters (including escaped spaces)
			if (ch === "\\" && this.pos + 1 < this.length) {
				chars.push(this.advance());
				chars.push(this.advance());
				continue;
			}
			// Track regex grouping parentheses
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
				// Unmatched ) - probably end of pattern
				break;
			}
			// Regex character class [...] - consume until closing ]
			// Handles [[:alpha:]], [^0-9], []a-z] (] as first char), etc.
			if (ch === "[") {
				// Lookahead: check if bracket expression will close properly
				// before hitting ]] or ) (when inside paren group)
				scan = this.pos + 1;
				// Skip ^ for negation
				if (scan < this.length && this.source[scan] === "^") {
					scan += 1;
				}
				// Skip ] as first char (literal)
				if (scan < this.length && this.source[scan] === "]") {
					scan += 1;
				}
				bracket_will_close = false;
				while (scan < this.length) {
					sc = this.source[scan];
					// Check for ]] - end of conditional
					if (
						sc === "]" &&
						scan + 1 < this.length &&
						this.source[scan + 1] === "]"
					) {
						break;
					}
					// Check for ) when inside paren group
					if (sc === ")" && paren_depth > 0) {
						break;
					}
					// Check for && - this terminates the regex even inside brackets
					if (
						sc === "&" &&
						scan + 1 < this.length &&
						this.source[scan + 1] === "&"
					) {
						break;
					}
					if (sc === "]") {
						bracket_will_close = true;
						break;
					}
					// Skip POSIX classes [:...:]
					if (
						sc === "[" &&
						scan + 1 < this.length &&
						this.source[scan + 1] === ":"
					) {
						scan += 2;
						while (
							scan < this.length &&
							!(
								this.source[scan] === ":" &&
								scan + 1 < this.length &&
								this.source[scan + 1] === "]"
							)
						) {
							scan += 1;
						}
						if (scan < this.length) {
							scan += 2;
						}
						continue;
					}
					scan += 1;
				}
				if (!bracket_will_close) {
					// Treat [ as literal
					chars.push(this.advance());
					continue;
				}
				chars.push(this.advance());
				// Handle negation [^
				if (!this.atEnd() && this.peek() === "^") {
					chars.push(this.advance());
				}
				// Handle ] as first char (literal ])
				if (!this.atEnd() && this.peek() === "]") {
					chars.push(this.advance());
				}
				// Consume until closing ]
				while (!this.atEnd()) {
					c = this.peek();
					if (c === "]") {
						chars.push(this.advance());
						break;
					}
					if (
						c === "[" &&
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === ":"
					) {
						// POSIX class like [:alpha:] inside bracket expression
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
					} else if (c === "$") {
						// Handle parameter/arithmetic expansions inside bracket expression
						if (
							this.pos + 1 < this.length &&
							this.source[this.pos + 1] === "("
						) {
							// Could be $((...)) arithmetic or $(...) command substitution
							if (
								this.pos + 2 < this.length &&
								this.source[this.pos + 2] === "("
							) {
								// Arithmetic expansion $((...))
								arith_result = this._parseArithmeticExpansion();
								arith_node = arith_result[0];
								arith_text = arith_result[1];
								if (arith_node) {
									parts.push(arith_node);
									chars.push(arith_text);
								} else {
									chars.push(this.advance());
								}
							} else {
								// Command substitution $(...)
								cmdsub_result = this._parseCommandSubstitution();
								cmdsub_node = cmdsub_result[0];
								cmdsub_text = cmdsub_result[1];
								if (cmdsub_node) {
									parts.push(cmdsub_node);
									chars.push(cmdsub_text);
								} else {
									chars.push(this.advance());
								}
							}
						} else {
							// Parameter expansion ${...} or $var
							param_result = this._parseParamExpansion();
							param_node = param_result[0];
							param_text = param_result[1];
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
				continue;
			}
			// Word terminators - space/tab ends the regex (unless inside parens), as does &&
			if (_isWhitespace(ch) && paren_depth === 0) {
				break;
			}
			if (_isWhitespace(ch) && paren_depth > 0) {
				// Space inside regex parens is part of the pattern
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
			// Single-quoted string
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
			// Double-quoted string
			if (ch === '"') {
				this.advance();
				chars.push('"');
				while (!this.atEnd() && this.peek() !== '"') {
					c = this.peek();
					if (c === "\\" && this.pos + 1 < this.length) {
						chars.push(this.advance());
						chars.push(this.advance());
					} else if (c === "$") {
						param_result = this._parseParamExpansion();
						param_node = param_result[0];
						param_text = param_result[1];
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
			if (ch === "$") {
				// Try command substitution first
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === "(") {
					cmdsub_result = this._parseCommandSubstitution();
					cmdsub_node = cmdsub_result[0];
					cmdsub_text = cmdsub_result[1];
					if (cmdsub_node) {
						parts.push(cmdsub_node);
						chars.push(cmdsub_text);
						continue;
					}
				}
				param_result = this._parseParamExpansion();
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
		parts_arg = null;
		if (parts && parts.length) {
			parts_arg = parts;
		}
		return new Word(chars.join(""), parts_arg);
	}

	parseBraceGroup() {
		let body, next_ch;
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== "{") {
			return null;
		}
		// Check that { is followed by whitespace or a valid command starter
		// {( is valid: brace group containing a subshell
		// {< and {> are valid: brace group starting with a redirect
		if (this.pos + 1 < this.length) {
			next_ch = this.source[this.pos + 1];
			if (!_isWhitespace(next_ch) && !"(<>".includes(next_ch)) {
				return null;
			}
		}
		this.advance();
		this.skipWhitespaceAndNewlines();
		body = this.parseList();
		if (body == null) {
			throw new ParseError("Expected command in brace group", this.pos);
		}
		this.skipWhitespace();
		if (this.atEnd() || this.peek() !== "}") {
			throw new ParseError("Expected } to close brace group", this.pos);
		}
		this.advance();
		return new BraceGroup(body, this._collectRedirects());
	}

	parseIf() {
		let condition,
			elif_condition,
			elif_then_body,
			else_body,
			inner_else,
			inner_next,
			next_word,
			then_body;
		if (!this.consumeWord("if")) {
			return null;
		}
		// Parse condition (a list that ends at 'then')
		condition = this.parseListUntil(new Set(["then"]));
		if (condition == null) {
			throw new ParseError("Expected condition after 'if'", this.pos);
		}
		// Expect 'then'
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("then")) {
			throw new ParseError("Expected 'then' after if condition", this.pos);
		}
		// Parse then body (ends at elif, else, or fi)
		then_body = this.parseListUntil(new Set(["elif", "else", "fi"]));
		if (then_body == null) {
			throw new ParseError("Expected commands after 'then'", this.pos);
		}
		// Check what comes next: elif, else, or fi
		this.skipWhitespaceAndNewlines();
		next_word = this.peekWord();
		else_body = null;
		if (next_word === "elif") {
			// elif is syntactic sugar for else if ... fi
			this.consumeWord("elif");
			// Parse the rest as a nested if (but we've already consumed 'elif')
			// We need to parse: condition; then body [elif|else|fi]
			elif_condition = this.parseListUntil(new Set(["then"]));
			if (elif_condition == null) {
				throw new ParseError("Expected condition after 'elif'", this.pos);
			}
			this.skipWhitespaceAndNewlines();
			if (!this.consumeWord("then")) {
				throw new ParseError("Expected 'then' after elif condition", this.pos);
			}
			elif_then_body = this.parseListUntil(new Set(["elif", "else", "fi"]));
			if (elif_then_body == null) {
				throw new ParseError("Expected commands after 'then'", this.pos);
			}
			// Recursively handle more elif/else/fi
			this.skipWhitespaceAndNewlines();
			inner_next = this.peekWord();
			inner_else = null;
			if (inner_next === "elif") {
				// More elif - recurse by creating a fake "if" and parsing
				// Actually, let's just recursively call a helper
				inner_else = this._parseElifChain();
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
		// Expect 'fi'
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("fi")) {
			throw new ParseError("Expected 'fi' to close if statement", this.pos);
		}
		return new If(condition, then_body, else_body, this._collectRedirects());
	}

	_parseElifChain() {
		let condition, else_body, next_word, then_body;
		this.consumeWord("elif");
		condition = this.parseListUntil(new Set(["then"]));
		if (condition == null) {
			throw new ParseError("Expected condition after 'elif'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("then")) {
			throw new ParseError("Expected 'then' after elif condition", this.pos);
		}
		then_body = this.parseListUntil(new Set(["elif", "else", "fi"]));
		if (then_body == null) {
			throw new ParseError("Expected commands after 'then'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		next_word = this.peekWord();
		else_body = null;
		if (next_word === "elif") {
			else_body = this._parseElifChain();
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
		let body, condition;
		if (!this.consumeWord("while")) {
			return null;
		}
		// Parse condition (ends at 'do')
		condition = this.parseListUntil(new Set(["do"]));
		if (condition == null) {
			throw new ParseError("Expected condition after 'while'", this.pos);
		}
		// Expect 'do'
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("do")) {
			throw new ParseError("Expected 'do' after while condition", this.pos);
		}
		// Parse body (ends at 'done')
		body = this.parseListUntil(new Set(["done"]));
		if (body == null) {
			throw new ParseError("Expected commands after 'do'", this.pos);
		}
		// Expect 'done'
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("done")) {
			throw new ParseError("Expected 'done' to close while loop", this.pos);
		}
		return new While(condition, body, this._collectRedirects());
	}

	parseUntil() {
		let body, condition;
		if (!this.consumeWord("until")) {
			return null;
		}
		// Parse condition (ends at 'do')
		condition = this.parseListUntil(new Set(["do"]));
		if (condition == null) {
			throw new ParseError("Expected condition after 'until'", this.pos);
		}
		// Expect 'do'
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("do")) {
			throw new ParseError("Expected 'do' after until condition", this.pos);
		}
		// Parse body (ends at 'done')
		body = this.parseListUntil(new Set(["done"]));
		if (body == null) {
			throw new ParseError("Expected commands after 'do'", this.pos);
		}
		// Expect 'done'
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("done")) {
			throw new ParseError("Expected 'done' to close until loop", this.pos);
		}
		return new Until(condition, body, this._collectRedirects());
	}

	parseFor() {
		let body, brace_group, saw_delimiter, var_name, var_word, word, words;
		if (!this.consumeWord("for")) {
			return null;
		}
		this.skipWhitespace();
		// Check for C-style for loop: for ((init; cond; incr))
		if (
			this.peek() === "(" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			return this._parseForArith();
		}
		// Parse variable name (bash allows reserved words and command substitutions as variable names)
		if (this.peek() === "$") {
			// Command substitution as variable name: for $(echo i) in ...
			var_word = this.parseWord();
			if (var_word == null) {
				throw new ParseError("Expected variable name after 'for'", this.pos);
			}
			var_name = var_word.value;
		} else {
			var_name = this.peekWord();
			if (var_name == null) {
				throw new ParseError("Expected variable name after 'for'", this.pos);
			}
			this.consumeWord(var_name);
		}
		this.skipWhitespace();
		// Handle optional semicolon or newline before 'in' or 'do'
		if (this.peek() === ";") {
			this.advance();
		}
		this.skipWhitespaceAndNewlines();
		// Check for optional 'in' clause
		words = null;
		if (this.peekWord() === "in") {
			this.consumeWord("in");
			this.skipWhitespace();
			// Check for immediate delimiter (;, newline) after 'in'
			saw_delimiter = _isSemicolonOrNewline(this.peek());
			if (this.peek() === ";") {
				this.advance();
			}
			this.skipWhitespaceAndNewlines();
			// Parse words until semicolon or newline (not 'do' directly)
			words = [];
			while (true) {
				this.skipWhitespace();
				// Check for end of word list
				if (this.atEnd()) {
					break;
				}
				if (_isSemicolonOrNewline(this.peek())) {
					saw_delimiter = true;
					if (this.peek() === ";") {
						this.advance();
					}
					break;
				}
				// 'do' only terminates if preceded by delimiter
				if (this.peekWord() === "do") {
					if (saw_delimiter) {
						break;
					}
					// 'for x in do' or 'for x in a b c do' is invalid
					throw new ParseError("Expected ';' or newline before 'do'", this.pos);
				}
				word = this.parseWord();
				if (word == null) {
					break;
				}
				words.push(word);
			}
		}
		// Skip to 'do' or '{'
		this.skipWhitespaceAndNewlines();
		// Check for brace group body as alternative to do/done
		if (this.peek() === "{") {
			// Bash allows: for x in a b; { cmd; }
			brace_group = this.parseBraceGroup();
			if (brace_group == null) {
				throw new ParseError("Expected brace group in for loop", this.pos);
			}
			return new For(
				var_name,
				words,
				brace_group.body,
				this._collectRedirects(),
			);
		}
		// Expect 'do'
		if (!this.consumeWord("do")) {
			throw new ParseError("Expected 'do' in for loop", this.pos);
		}
		// Parse body (ends at 'done')
		body = this.parseListUntil(new Set(["done"]));
		if (body == null) {
			throw new ParseError("Expected commands after 'do'", this.pos);
		}
		// Expect 'done'
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("done")) {
			throw new ParseError("Expected 'done' to close for loop", this.pos);
		}
		return new For(var_name, words, body, this._collectRedirects());
	}

	_parseForArith() {
		let body, ch, cond, current, incr, init, paren_depth, parts;
		// We've already consumed 'for' and positioned at '(('
		this.advance();
		this.advance();
		// Parse the three expressions separated by semicolons
		// Each can be empty
		parts = [];
		current = [];
		paren_depth = 0;
		while (!this.atEnd()) {
			ch = this.peek();
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
					// Check for closing ))
					// End of ((...)) - preserve trailing whitespace
					parts.push(current.join("").replace(/^[ \t]+/, ""));
					this.advance();
					this.advance();
					break;
				} else {
					current.push(this.advance());
				}
			} else if (ch === ";" && paren_depth === 0) {
				// Preserve trailing whitespace in expressions
				parts.push(current.join("").replace(/^[ \t]+/, ""));
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
		init = parts[0];
		cond = parts[1];
		incr = parts[2];
		this.skipWhitespace();
		// Handle optional semicolon
		if (!this.atEnd() && this.peek() === ";") {
			this.advance();
		}
		this.skipWhitespaceAndNewlines();
		body = this._parseLoopBody("for loop");
		return new ForArith(init, cond, incr, body, this._collectRedirects());
	}

	parseSelect() {
		let body, var_name, word, words;
		if (!this.consumeWord("select")) {
			return null;
		}
		this.skipWhitespace();
		// Parse variable name
		var_name = this.peekWord();
		if (var_name == null) {
			throw new ParseError("Expected variable name after 'select'", this.pos);
		}
		this.consumeWord(var_name);
		this.skipWhitespace();
		// Handle optional semicolon before 'in', 'do', or '{'
		if (this.peek() === ";") {
			this.advance();
		}
		this.skipWhitespaceAndNewlines();
		// Check for optional 'in' clause
		words = null;
		if (this.peekWord() === "in") {
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
				if (_isSemicolonNewlineBrace(this.peek())) {
					if (this.peek() === ";") {
						this.advance();
					}
					break;
				}
				if (this.peekWord() === "do") {
					break;
				}
				word = this.parseWord();
				if (word == null) {
					break;
				}
				words.push(word);
			}
		}
		// Empty word list is allowed for select (unlike for)
		// Skip whitespace before body
		this.skipWhitespaceAndNewlines();
		body = this._parseLoopBody("select");
		return new Select(var_name, words, body, this._collectRedirects());
	}

	_isCaseTerminator() {
		let next_ch;
		if (this.atEnd() || this.peek() !== ";") {
			return false;
		}
		if (this.pos + 1 >= this.length) {
			return false;
		}
		next_ch = this.source[this.pos + 1];
		// ;; or ;& or ;;& (which is actually ;;&)
		return _isSemicolonOrAmp(next_ch);
	}

	_consumeCaseTerminator() {
		let ch;
		if (this.atEnd() || this.peek() !== ";") {
			return ";;";
		}
		this.advance();
		if (this.atEnd()) {
			return ";;";
		}
		ch = this.peek();
		if (ch === ";") {
			this.advance();
			// Check for ;;&
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
		let body,
			c,
			ch,
			extglob_depth,
			has_first_bracket_literal,
			is_at_terminator,
			is_char_class,
			is_empty_body,
			is_pattern,
			next_ch,
			paren_depth,
			pattern,
			pattern_chars,
			patterns,
			saved,
			sc,
			scan_depth,
			scan_pos,
			terminator,
			word;
		if (!this.consumeWord("case")) {
			return null;
		}
		this.skipWhitespace();
		// Parse the word to match
		word = this.parseWord();
		if (word == null) {
			throw new ParseError("Expected word after 'case'", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		// Expect 'in'
		if (!this.consumeWord("in")) {
			throw new ParseError("Expected 'in' after case word", this.pos);
		}
		this.skipWhitespaceAndNewlines();
		// Parse pattern clauses until 'esac'
		patterns = [];
		while (true) {
			this.skipWhitespaceAndNewlines();
			// Check if we're at 'esac' (but not 'esac)' which is esac as a pattern)
			if (this.peekWord() === "esac") {
				// Look ahead to see if esac is a pattern (esac followed by ) then body/;;)
				// or the closing keyword (esac followed by ) that closes containing construct)
				saved = this.pos;
				this.skipWhitespace();
				// Consume "esac"
				while (
					!this.atEnd() &&
					!_isMetachar(this.peek()) &&
					!_isQuote(this.peek())
				) {
					this.advance();
				}
				this.skipWhitespace();
				// Check for ) and what follows
				is_pattern = false;
				if (!this.atEnd() && this.peek() === ")") {
					this.advance();
					this.skipWhitespace();
					// esac is a pattern if there's body content or ;; after )
					// Not a pattern if ) is followed by end, newline, or another )
					if (!this.atEnd()) {
						next_ch = this.peek();
						// If followed by ;; or actual command content, it's a pattern
						if (next_ch === ";") {
							is_pattern = true;
						} else if (!_isNewlineOrRightParen(next_ch)) {
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
			if (!this.atEnd() && this.peek() === "(") {
				this.advance();
				this.skipWhitespaceAndNewlines();
			}
			// Parse pattern (everything until ')' at depth 0)
			// Pattern can contain | for alternation, quotes, globs, extglobs, etc.
			// Extglob patterns @(), ?(), *(), +(), !() contain nested parens
			pattern_chars = [];
			extglob_depth = 0;
			while (!this.atEnd()) {
				ch = this.peek();
				if (ch === ")") {
					if (extglob_depth > 0) {
						// Inside extglob, consume the ) and decrement depth
						pattern_chars.push(this.advance());
						extglob_depth -= 1;
					} else {
						// End of pattern
						this.advance();
						break;
					}
				} else if (ch === "\\") {
					// Line continuation or backslash escape
					if (
						this.pos + 1 < this.length &&
						this.source[this.pos + 1] === "\n"
					) {
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
				} else if (
					ch === "$" &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === "("
				) {
					// $( or $(( - command sub or arithmetic
					pattern_chars.push(this.advance());
					pattern_chars.push(this.advance());
					if (!this.atEnd() && this.peek() === "(") {
						// $(( arithmetic - need to find matching ))
						pattern_chars.push(this.advance());
						paren_depth = 2;
						while (!this.atEnd() && paren_depth > 0) {
							c = this.peek();
							if (c === "(") {
								paren_depth += 1;
							} else if (c === ")") {
								paren_depth -= 1;
							}
							pattern_chars.push(this.advance());
						}
					} else {
						// $() command sub - track single paren
						extglob_depth += 1;
					}
				} else if (ch === "(" && extglob_depth > 0) {
					// Grouping paren inside extglob
					pattern_chars.push(this.advance());
					extglob_depth += 1;
				} else if (
					_isExtglobPrefix(ch) &&
					this.pos + 1 < this.length &&
					this.source[this.pos + 1] === "("
				) {
					// Extglob opener: @(, ?(, *(, +(, !(
					pattern_chars.push(this.advance());
					pattern_chars.push(this.advance());
					extglob_depth += 1;
				} else if (ch === "[") {
					// Character class - but only if there's a matching ]
					// ] must come before ) at same depth (either extglob or pattern)
					is_char_class = false;
					scan_pos = this.pos + 1;
					scan_depth = 0;
					has_first_bracket_literal = false;
					// Skip [! or [^ at start
					if (scan_pos < this.length && _isCaretOrBang(this.source[scan_pos])) {
						scan_pos += 1;
					}
					// Skip ] as first char (literal in char class) only if there's another ]
					if (scan_pos < this.length && this.source[scan_pos] === "]") {
						// Check if there's another ] later
						if (this.source.indexOf("]", scan_pos + 1) !== -1) {
							scan_pos += 1;
							has_first_bracket_literal = true;
						}
					}
					while (scan_pos < this.length) {
						sc = this.source[scan_pos];
						if (sc === "]" && scan_depth === 0) {
							is_char_class = true;
							break;
						} else if (sc === "[") {
							scan_depth += 1;
						} else if (sc === ")" && scan_depth === 0) {
							// Hit pattern/extglob closer before finding ]
							break;
						} else if (sc === "|" && scan_depth === 0) {
							// Hit pattern separator (| in case pattern or extglob alternation)
							break;
						}
						scan_pos += 1;
					}
					if (is_char_class) {
						pattern_chars.push(this.advance());
						// Handle [! or [^ at start
						if (!this.atEnd() && _isCaretOrBang(this.peek())) {
							pattern_chars.push(this.advance());
						}
						// Handle ] as first char (literal) only if we detected it in scan
						if (
							has_first_bracket_literal &&
							!this.atEnd() &&
							this.peek() === "]"
						) {
							pattern_chars.push(this.advance());
						}
						// Consume until closing ]
						while (!this.atEnd() && this.peek() !== "]") {
							pattern_chars.push(this.advance());
						}
						if (!this.atEnd()) {
							pattern_chars.push(this.advance());
						}
					} else {
						// Not a valid char class, treat [ as literal
						pattern_chars.push(this.advance());
					}
				} else if (ch === "'") {
					// Single-quoted string in pattern
					pattern_chars.push(this.advance());
					while (!this.atEnd() && this.peek() !== "'") {
						pattern_chars.push(this.advance());
					}
					if (!this.atEnd()) {
						pattern_chars.push(this.advance());
					}
				} else if (ch === '"') {
					// Double-quoted string in pattern
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
				} else if (_isWhitespace(ch)) {
					// Skip whitespace at top level, but preserve inside $() or extglob
					if (extglob_depth > 0) {
						pattern_chars.push(this.advance());
					} else {
						this.advance();
					}
				} else {
					pattern_chars.push(this.advance());
				}
			}
			pattern = pattern_chars.join("");
			if (!pattern) {
				throw new ParseError("Expected pattern in case statement", this.pos);
			}
			// Parse commands until ;;, ;&, ;;&, or esac
			// Commands are optional (can have empty body)
			this.skipWhitespace();
			body = null;
			// Check for empty body: terminator right after pattern
			is_empty_body = this._isCaseTerminator();
			if (!is_empty_body) {
				// Skip newlines and check if there's content before terminator or esac
				this.skipWhitespaceAndNewlines();
				if (!this.atEnd() && this.peekWord() !== "esac") {
					// Check again for terminator after whitespace/newlines
					is_at_terminator = this._isCaseTerminator();
					if (!is_at_terminator) {
						body = this.parseListUntil(new Set(["esac"]));
						this.skipWhitespace();
					}
				}
			}
			// Handle terminator: ;;, ;&, or ;;&
			terminator = this._consumeCaseTerminator();
			this.skipWhitespaceAndNewlines();
			patterns.push(new CasePattern(pattern, body, terminator));
		}
		// Expect 'esac'
		this.skipWhitespaceAndNewlines();
		if (!this.consumeWord("esac")) {
			throw new ParseError("Expected 'esac' to close case statement", this.pos);
		}
		return new Case(word, patterns, this._collectRedirects());
	}

	parseCoproc() {
		let body, ch, name, next_word, potential_name, word_start;
		if (!this.consumeWord("coproc")) {
			return null;
		}
		this.skipWhitespace();
		name = null;
		// Check for compound command directly (no NAME)
		ch = null;
		if (!this.atEnd()) {
			ch = this.peek();
		}
		if (ch === "{") {
			body = this.parseBraceGroup();
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
		// Check for reserved word compounds directly
		next_word = this.peekWord();
		if (COMPOUND_KEYWORDS.has(next_word)) {
			body = this.parseCompoundCommand();
			if (body != null) {
				return new Coproc(body, name);
			}
		}
		// Check if first word is NAME followed by compound command
		word_start = this.pos;
		potential_name = this.peekWord();
		if (potential_name) {
			// Skip past the potential name
			while (
				!this.atEnd() &&
				!_isMetachar(this.peek()) &&
				!_isQuote(this.peek())
			) {
				this.advance();
			}
			this.skipWhitespace();
			// Check what follows
			ch = null;
			if (!this.atEnd()) {
				ch = this.peek();
			}
			next_word = this.peekWord();
			if (_isValidIdentifier(potential_name)) {
				// Valid identifier followed by compound command - extract name
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
				} else if (COMPOUND_KEYWORDS.has(next_word)) {
					name = potential_name;
					body = this.parseCompoundCommand();
					if (body != null) {
						return new Coproc(body, name);
					}
				}
			}
			// Not followed by compound - restore position and parse as simple command
			this.pos = word_start;
		}
		// Parse as simple command (includes any "NAME" as part of the command)
		body = this.parseCommand();
		if (body != null) {
			return new Coproc(body, name);
		}
		throw new ParseError("Expected command after coproc", this.pos);
	}

	parseFunction() {
		let body,
			brace_depth,
			has_whitespace,
			i,
			name,
			name_start,
			pos_after_name,
			saved_pos;
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		saved_pos = this.pos;
		// Check for 'function' keyword form
		if (this.peekWord() === "function") {
			this.consumeWord("function");
			this.skipWhitespace();
			// Get function name
			name = this.peekWord();
			if (name == null) {
				this.pos = saved_pos;
				return null;
			}
			this.consumeWord(name);
			this.skipWhitespace();
			// Optional () after name - but only if it's actually ()
			// and not the start of a subshell body
			if (!this.atEnd() && this.peek() === "(") {
				// Check if this is () or start of subshell
				if (this.pos + 1 < this.length && this.source[this.pos + 1] === ")") {
					this.advance();
					this.advance();
				}
			}
			// else: the ( is start of subshell body, don't consume
			this.skipWhitespaceAndNewlines();
			// Parse body (any compound command)
			body = this._parseCompoundCommand();
			if (body == null) {
				throw new ParseError("Expected function body", this.pos);
			}
			return new FunctionNode(name, body);
		}
		// Check for POSIX form: name()
		// We need to peek ahead to see if there's a () after the word
		name = this.peekWord();
		if (name == null || RESERVED_WORDS.has(name)) {
			return null;
		}
		// Assignment words (NAME=...) are not function definitions
		if (_looksLikeAssignment(name)) {
			return null;
		}
		// Save position after the name
		this.skipWhitespace();
		name_start = this.pos;
		// Consume the name
		while (
			!this.atEnd() &&
			!_isMetachar(this.peek()) &&
			!_isQuote(this.peek()) &&
			!_isParen(this.peek())
		) {
			this.advance();
		}
		name = this.source.slice(name_start, this.pos);
		if (!name) {
			this.pos = saved_pos;
			return null;
		}
		// Check if name contains unclosed parameter expansion ${...}
		// If so, () is inside the expansion, not function definition syntax
		brace_depth = 0;
		i = 0;
		while (i < name.length) {
			if (i + 1 < name.length && name[i] === "$" && name[i + 1] === "{") {
				brace_depth += 1;
				i += 2;
				continue;
			}
			if (name[i] === "}") {
				brace_depth -= 1;
			}
			i += 1;
		}
		if (brace_depth > 0) {
			this.pos = saved_pos;
			return null;
		}
		// Check for () - whitespace IS allowed between name and (
		// But if name ends with extglob prefix (*?@+!) and () is adjacent,
		// it's an extglob pattern, not a function definition
		// Similarly, if name ends with $ and () is adjacent, it's a command
		// substitution, not a function definition
		pos_after_name = this.pos;
		this.skipWhitespace();
		has_whitespace = this.pos > pos_after_name;
		if (!has_whitespace && name && "*?@+!$".includes(name[name.length - 1])) {
			this.pos = saved_pos;
			return null;
		}
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
		// Parse body (any compound command)
		body = this._parseCompoundCommand();
		if (body == null) {
			throw new ParseError("Expected function body", this.pos);
		}
		return new FunctionNode(name, body);
	}

	_parseCompoundCommand() {
		let result;
		// Try each compound command type
		result = this.parseBraceGroup();
		if (result) {
			return result;
		}
		// Arithmetic command ((...)) - check before subshell
		if (
			!this.atEnd() &&
			this.peek() === "(" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			result = this.parseArithmeticCommand();
			if (result != null) {
				return result;
			}
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
		let at_case_terminator,
			has_newline,
			is_standalone_brace,
			next_pos,
			op,
			parts,
			pipeline;
		// Check if we're already at a stop word
		this.skipWhitespaceAndNewlines();
		if (stop_words.has(this.peekWord())) {
			return null;
		}
		pipeline = this.parsePipeline();
		if (pipeline == null) {
			return null;
		}
		parts = [pipeline];
		while (true) {
			// Check for newline as implicit command separator
			this.skipWhitespace();
			has_newline = false;
			while (!this.atEnd() && this.peek() === "\n") {
				has_newline = true;
				this.advance();
				// Skip past any pending heredoc content after newline
				if (
					this._pending_heredoc_end != null &&
					this._pending_heredoc_end > this.pos
				) {
					this.pos = this._pending_heredoc_end;
					this._pending_heredoc_end = null;
				}
				this.skipWhitespace();
			}
			op = this.parseListOperator();
			// Newline acts as implicit semicolon if followed by more commands
			if (op == null && has_newline) {
				// Check if there's another command (not a stop word)
				// } is only a terminator if it's standalone (closing brace group), not part of a word
				is_standalone_brace = false;
				if (!this.atEnd() && this.peek() === "}") {
					next_pos = this.pos + 1;
					if (
						next_pos >= this.length ||
						_isWordEndContext(this.source[next_pos])
					) {
						is_standalone_brace = true;
					}
				}
				if (
					!this.atEnd() &&
					!stop_words.has(this.peekWord()) &&
					this.peek() !== ")" &&
					!is_standalone_brace
				) {
					op = "\n";
				}
			}
			if (op == null) {
				break;
			}
			// For & at end of list, don't require another command
			if (op === "&") {
				parts.push(new Operator(op));
				this.skipWhitespaceAndNewlines();
				// Check for standalone } (closing brace), not } as part of a word
				is_standalone_brace = false;
				if (!this.atEnd() && this.peek() === "}") {
					next_pos = this.pos + 1;
					if (
						next_pos >= this.length ||
						_isWordEndContext(this.source[next_pos])
					) {
						is_standalone_brace = true;
					}
				}
				if (
					this.atEnd() ||
					stop_words.has(this.peekWord()) ||
					this.peek() === "\n" ||
					this.peek() === ")" ||
					is_standalone_brace
				) {
					break;
				}
			}
			// For ; - check if it's a terminator before a stop word (don't include it)
			if (op === ";") {
				this.skipWhitespaceAndNewlines();
				// Also check for ;;, ;&, or ;;& (case terminators)
				at_case_terminator =
					this.peek() === ";" &&
					this.pos + 1 < this.length &&
					_isSemicolonOrAmp(this.source[this.pos + 1]);
				// Check for standalone } (closing brace), not } as part of a word
				is_standalone_brace = false;
				if (!this.atEnd() && this.peek() === "}") {
					next_pos = this.pos + 1;
					if (
						next_pos >= this.length ||
						_isWordEndContext(this.source[next_pos])
					) {
						is_standalone_brace = true;
					}
				}
				if (
					this.atEnd() ||
					stop_words.has(this.peekWord()) ||
					this.peek() === "\n" ||
					this.peek() === ")" ||
					is_standalone_brace ||
					at_case_terminator
				) {
					// Don't include trailing semicolon - it's just a terminator
					break;
				}
				parts.push(new Operator(op));
			} else if (op !== "&") {
				parts.push(new Operator(op));
			}
			// Check for stop words before parsing next pipeline
			this.skipWhitespaceAndNewlines();
			// Also check for ;;, ;&, or ;;& (case terminators)
			if (stop_words.has(this.peekWord())) {
				break;
			}
			if (
				this.peek() === ";" &&
				this.pos + 1 < this.length &&
				_isSemicolonOrAmp(this.source[this.pos + 1])
			) {
				break;
			}
			pipeline = this.parsePipeline();
			if (pipeline == null) {
				throw new ParseError(`Expected command after ${op}`, this.pos);
			}
			parts.push(pipeline);
		}
		if (parts.length === 1) {
			return parts[0];
		}
		return new List(parts);
	}

	parseCompoundCommand() {
		let ch, func, result, word;
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		ch = this.peek();
		// Arithmetic command ((...)) - check before subshell
		if (
			ch === "(" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "("
		) {
			result = this.parseArithmeticCommand();
			if (result != null) {
				return result;
			}
		}
		// Not arithmetic (e.g., '(( x ) )' is nested subshells) - fall through
		// Subshell
		if (ch === "(") {
			return this.parseSubshell();
		}
		// Brace group
		if (ch === "{") {
			result = this.parseBraceGroup();
			if (result != null) {
				return result;
			}
		}
		// Fall through to simple command if not a brace group
		// Conditional expression [[ ]] - check before reserved words
		if (
			ch === "[" &&
			this.pos + 1 < this.length &&
			this.source[this.pos + 1] === "["
		) {
			result = this.parseConditionalExpr();
			if (result != null) {
				return result;
			}
		}
		// Fall through to simple command if [[ is not a conditional keyword
		// Check for reserved words
		word = this.peekWord();
		// Reserved words that cannot start a statement (only valid in specific contexts)
		if (
			["fi", "then", "elif", "else", "done", "esac", "do", "in"].includes(word)
		) {
			throw new ParseError(`Unexpected reserved word '${word}'`, this.pos);
		}
		// If statement
		if (word === "if") {
			return this.parseIf();
		}
		// While loop
		if (word === "while") {
			return this.parseWhile();
		}
		// Until loop
		if (word === "until") {
			return this.parseUntil();
		}
		// For loop
		if (word === "for") {
			return this.parseFor();
		}
		// Select statement
		if (word === "select") {
			return this.parseSelect();
		}
		// Case statement
		if (word === "case") {
			return this.parseCase();
		}
		// Function definition (function keyword form)
		if (word === "function") {
			return this.parseFunction();
		}
		// Coproc
		if (word === "coproc") {
			return this.parseCoproc();
		}
		// Try POSIX function definition (name() form) before simple command
		func = this.parseFunction();
		if (func != null) {
			return func;
		}
		// Simple command
		return this.parseCommand();
	}

	parsePipeline() {
		let inner, prefix_order, result, saved, time_posix;
		this.skipWhitespace();
		// Track order of prefixes: "time", "negation", or "time_negation" or "negation_time"
		prefix_order = null;
		time_posix = false;
		// Check for 'time' prefix first
		if (this.peekWord() === "time") {
			this.consumeWord("time");
			prefix_order = "time";
			this.skipWhitespace();
			// Check for -p flag
			if (!this.atEnd() && this.peek() === "-") {
				saved = this.pos;
				this.advance();
				if (!this.atEnd() && this.peek() === "p") {
					this.advance();
					if (this.atEnd() || _isMetachar(this.peek())) {
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
			if (!this.atEnd() && _startsWithAt(this.source, this.pos, "--")) {
				if (
					this.pos + 2 >= this.length ||
					_isWhitespace(this.source[this.pos + 2])
				) {
					this.advance();
					this.advance();
					time_posix = true;
					this.skipWhitespace();
				}
			}
			// Skip nested time keywords (time time X collapses to time X)
			while (this.peekWord() === "time") {
				this.consumeWord("time");
				this.skipWhitespace();
				// Check for -p after nested time
				if (!this.atEnd() && this.peek() === "-") {
					saved = this.pos;
					this.advance();
					if (!this.atEnd() && this.peek() === "p") {
						this.advance();
						if (this.atEnd() || _isMetachar(this.peek())) {
							time_posix = true;
						} else {
							this.pos = saved;
						}
					} else {
						this.pos = saved;
					}
				}
			}
			this.skipWhitespace();
			// Check for ! after time
			if (!this.atEnd() && this.peek() === "!") {
				if (
					(this.pos + 1 >= this.length ||
						_isNegationBoundary(this.source[this.pos + 1])) &&
					!this._isBangFollowedByProcsub()
				) {
					this.advance();
					prefix_order = "time_negation";
					this.skipWhitespace();
				}
			}
		} else if (!this.atEnd() && this.peek() === "!") {
			// Check for '!' negation prefix (if no time yet)
			if (
				(this.pos + 1 >= this.length ||
					_isNegationBoundary(this.source[this.pos + 1])) &&
				!this._isBangFollowedByProcsub()
			) {
				this.advance();
				this.skipWhitespace();
				// Recursively parse pipeline to handle ! ! cmd, ! time cmd, etc.
				// Bare ! (no following command) is valid POSIX - equivalent to false
				inner = this.parsePipeline();
				// Double negation cancels out (! ! cmd -> cmd, ! ! -> empty command)
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
		// Parse the actual pipeline
		result = this._parseSimplePipeline();
		// Wrap based on prefix order
		// Note: bare time and time ! are valid (null command timing)
		if (prefix_order === "time") {
			result = new Time(result, time_posix);
		} else if (prefix_order === "negation") {
			result = new Negation(result);
		} else if (prefix_order === "time_negation") {
			// time ! cmd -> Negation(Time(cmd)) per bash-oracle
			result = new Time(result, time_posix);
			result = new Negation(result);
		} else if (prefix_order === "negation_time") {
			// ! time cmd -> Negation(Time(cmd))
			result = new Time(result, time_posix);
			result = new Negation(result);
		} else if (result == null) {
			// No prefix and no pipeline
			return null;
		}
		return result;
	}

	_parseSimplePipeline() {
		let cmd, commands, is_pipe_both;
		cmd = this.parseCompoundCommand();
		if (cmd == null) {
			return null;
		}
		commands = [cmd];
		while (true) {
			this.skipWhitespace();
			if (this.atEnd() || this.peek() !== "|") {
				break;
			}
			// Check it's not ||
			if (this.pos + 1 < this.length && this.source[this.pos + 1] === "|") {
				break;
			}
			this.advance();
			// Check for |& (pipe stderr)
			is_pipe_both = false;
			if (!this.atEnd() && this.peek() === "&") {
				this.advance();
				is_pipe_both = true;
			}
			this.skipWhitespaceAndNewlines();
			// Add pipe-both marker if this is a |& pipe
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
		let ch;
		this.skipWhitespace();
		if (this.atEnd()) {
			return null;
		}
		ch = this.peek();
		if (ch === "&") {
			// Check if this is &> or &>> (redirect), not background operator
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
			// Don't treat ;;, ;&, or ;;& as a single semicolon (they're case terminators)
			if (
				this.pos + 1 < this.length &&
				_isSemicolonOrAmp(this.source[this.pos + 1])
			) {
				return null;
			}
			this.advance();
			return ";";
		}
		return null;
	}

	parseList(newline_as_separator) {
		let has_newline, op, parts, pipeline;
		if (newline_as_separator == null) {
			newline_as_separator = true;
		}
		if (newline_as_separator) {
			this.skipWhitespaceAndNewlines();
		} else {
			this.skipWhitespace();
		}
		pipeline = this.parsePipeline();
		if (pipeline == null) {
			return null;
		}
		parts = [pipeline];
		while (true) {
			// Check for newline as implicit command separator
			this.skipWhitespace();
			has_newline = false;
			while (!this.atEnd() && this.peek() === "\n") {
				has_newline = true;
				// If not treating newlines as separators, stop here
				if (!newline_as_separator) {
					break;
				}
				this.advance();
				// Skip past any pending heredoc content after newline
				if (
					this._pending_heredoc_end != null &&
					this._pending_heredoc_end > this.pos
				) {
					this.pos = this._pending_heredoc_end;
					this._pending_heredoc_end = null;
				}
				this.skipWhitespace();
			}
			// If we hit a newline and not treating them as separators, stop
			if (has_newline && !newline_as_separator) {
				break;
			}
			op = this.parseListOperator();
			// Newline acts as implicit semicolon if followed by more commands
			if (op == null && has_newline) {
				if (!this.atEnd() && !_isRightBracket(this.peek())) {
					op = "\n";
				}
			}
			if (op == null) {
				break;
			}
			// Don't add duplicate semicolon (e.g., explicit ; followed by newline)
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
			// For & at end of list, don't require another command
			if (op === "&") {
				this.skipWhitespace();
				if (this.atEnd() || _isRightBracket(this.peek())) {
					break;
				}
				// Newline after & - in compound commands, skip it (& acts as separator)
				// At top level, newline terminates (separate commands)
				if (this.peek() === "\n") {
					if (newline_as_separator) {
						this.skipWhitespaceAndNewlines();
						if (this.atEnd() || _isRightBracket(this.peek())) {
							break;
						}
					} else {
						break;
					}
				}
			}
			// For ; at end of list, don't require another command
			if (op === ";") {
				this.skipWhitespace();
				if (this.atEnd() || _isRightBracket(this.peek())) {
					break;
				}
				// Newline after ; means continue to see if more commands follow
				if (this.peek() === "\n") {
					continue;
				}
			}
			// For && and ||, allow newlines before the next command
			if (op === "&&" || op === "||") {
				this.skipWhitespaceAndNewlines();
			}
			pipeline = this.parsePipeline();
			if (pipeline == null) {
				throw new ParseError(`Expected command after ${op}`, this.pos);
			}
			parts.push(pipeline);
		}
		if (parts.length === 1) {
			return parts[0];
		}
		return new List(parts);
	}

	parseComment() {
		let start, text;
		if (this.atEnd() || this.peek() !== "#") {
			return null;
		}
		start = this.pos;
		while (!this.atEnd() && this.peek() !== "\n") {
			this.advance();
		}
		text = this.source.slice(start, this.pos);
		return new Comment(text);
	}

	parse() {
		let comment, found_newline, result, results, source;
		source = this.source.trim();
		if (!source) {
			return [new Empty()];
		}
		results = [];
		// Skip leading comments (bash-oracle doesn't output them)
		while (true) {
			this.skipWhitespace();
			// Skip newlines but not comments
			while (!this.atEnd() && this.peek() === "\n") {
				this.advance();
			}
			if (this.atEnd()) {
				break;
			}
			comment = this.parseComment();
			if (!comment) {
				break;
			}
		}
		// Don't add to results - bash-oracle doesn't output comments
		// Parse statements separated by newlines as separate top-level nodes
		while (!this.atEnd()) {
			result = this.parseList(false);
			if (result != null) {
				results.push(result);
			}
			this.skipWhitespace();
			// Skip newlines (and any pending heredoc content) between statements
			found_newline = false;
			while (!this.atEnd() && this.peek() === "\n") {
				found_newline = true;
				this.advance();
				// Skip past any pending heredoc content after newline
				if (
					this._pending_heredoc_end != null &&
					this._pending_heredoc_end > this.pos
				) {
					this.pos = this._pending_heredoc_end;
					this._pending_heredoc_end = null;
				}
				this.skipWhitespace();
			}
			// If no newline and not at end, we have unparsed content
			if (!found_newline && !this.atEnd()) {
				throw new ParseError("Parser not fully implemented yet", this.pos);
			}
		}
		if (results.length === 0) {
			return [new Empty()];
		}
		// bash-oracle strips trailing backslash at EOF when there was a newline
		// inside single quotes and the last word is on the same line as other content
		// (not on its own line after a newline)
		// Exception: keep backslash if it's on a continuation line (preceded by \<newline>)
		if (
			this._saw_newline_in_single_quote &&
			this.source &&
			this.source[this.source.length - 1] === "\\" &&
			!(
				this.source.length >= 3 &&
				this.source.slice(this.source.length - 3, this.source.length - 1) ===
					"\\\n"
			)
		) {
			// Check if the last word started on its own line (after a newline)
			// If so, keep the backslash. Otherwise, strip it as line continuation.
			if (!this._lastWordOnOwnLine(results)) {
				this._stripTrailingBackslashFromLastWord(results);
			}
		}
		return results;
	}

	_lastWordOnOwnLine(nodes) {
		// If we have multiple top-level nodes, they were separated by newlines,
		// so the last node is on its own line
		return nodes.length >= 2;
	}

	_stripTrailingBackslashFromLastWord(nodes) {
		let last_node, last_word;
		if (!nodes) {
			return;
		}
		last_node = nodes[nodes.length - 1];
		// Find the last Word in the structure
		last_word = this._findLastWord(last_node);
		if (last_word && last_word.value.endsWith("\\")) {
			last_word.value = last_word.value.slice(0, last_word.value.length - 1);
			// If the word is now empty, remove it from the command
			if (!last_word.value && last_node instanceof Command && last_node.words) {
				last_node.words.pop();
			}
		}
	}

	_findLastWord(node) {
		if (node instanceof Word) {
			return node;
		}
		if (node instanceof Command) {
			if (node.words && node.words.length) {
				return node.words[node.words.length - 1];
			}
		}
		if (node instanceof Pipeline) {
			if (node.commands && node.commands.length) {
				return this._findLastWord(node.commands[node.commands.length - 1]);
			}
		}
		if (node instanceof List) {
			if (node.parts && node.parts.length) {
				return this._findLastWord(node.parts[node.parts.length - 1]);
			}
		}
		return null;
	}
}

function parse(source) {
	let parser;
	parser = new Parser(source);
	return parser.parse();
}

module.exports = { parse, ParseError };
