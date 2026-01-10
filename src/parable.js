/**
 * Parable - A recursive descent bash parser in pure JavaScript.
 * Translated from Python for cross-language portability.
 */

// ============================================================================
// ParseError
// ============================================================================

class ParseError extends Error {
  constructor(message, pos = null, line = null) {
    super();
    this.message = message;
    this.pos = pos;
    this.line = line;
    this.name = 'ParseError';
    super.message = this._formatMessage();
  }

  _formatMessage() {
    if (this.line !== null && this.pos !== null) {
      return 'Parse error at line ' + String(this.line) + ', position ' + String(this.pos) + ': ' + this.message;
    } else if (this.pos !== null) {
      return 'Parse error at position ' + String(this.pos) + ': ' + this.message;
    }
    return 'Parse error: ' + this.message;
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

function _isHexDigit(c) {
  return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
}

function _isOctalDigit(c) {
  return c >= '0' && c <= '7';
}

function _getAnsiEscape(c) {
  if (c === 'a') return 0x07;
  if (c === 'b') return 0x08;
  if (c === 'e' || c === 'E') return 0x1b;
  if (c === 'f') return 0x0c;
  if (c === 'n') return 0x0a;
  if (c === 'r') return 0x0d;
  if (c === 't') return 0x09;
  if (c === 'v') return 0x0b;
  if (c === '\\') return 0x5c;
  if (c === '"') return 0x22;
  if (c === '?') return 0x3f;
  return -1;
}

function _isWhitespace(c) {
  return c === ' ' || c === '\t' || c === '\n';
}

function _isWhitespaceNoNewline(c) {
  return c === ' ' || c === '\t';
}

function _substring(s, start, end) {
  return s.slice(start, end);
}

function _startsWithAt(s, pos, prefix) {
  return s.startsWith(prefix, pos);
}

function _sublist(lst, start, end) {
  return lst.slice(start, end);
}

function _repeatStr(s, n) {
  const result = [];
  let i = 0;
  while (i < n) {
    result.push(s);
    i += 1;
  }
  return result.join('');
}

function _isQuote(c) {
  return c === '"' || c === "'" || c === '`';
}

function _isMetachar(c) {
  return c === ' ' || c === '\t' || c === '\n' || c === '|' || c === '&' || c === ';' || c === '(' || c === ')' || c === '<' || c === '>';
}

function _isExtglobPrefix(c) {
  return c === '@' || c === '?' || c === '*' || c === '+' || c === '!';
}

function _isRedirectChar(c) {
  return c === '<' || c === '>';
}

function _isSpecialParam(c) {
  return c === '@' || c === '*' || c === '#' || c === '?' || c === '-' || c === '$' || c === '!' || c === '_';
}

function _isDigit(c) {
  return c >= '0' && c <= '9';
}

function _isSemicolonOrNewline(c) {
  return c === ';' || c === '\n';
}

function _isRightBracket(c) {
  return c === ']';
}

function _isWordStartContext(c) {
  return c === '|' || c === '&' || c === ';' || c === '(' || c === ')' || c === '\n' || c === '<' || c === '>' || c === ' ' || c === '\t';
}

function _isWordEndContext(c) {
  return c === '|' || c === '&' || c === ';' || c === '(' || c === ')' || c === '\n' || c === '<' || c === '>' || c === ' ' || c === '\t' || c === '"' || c === "'" || c === '`';
}

function _isSpecialParamOrDigit(c) {
  return _isSpecialParam(c) || _isDigit(c);
}

function _isParamExpansionOp(c) {
  return c === ':' || c === '-' || c === '+' || c === '=' || c === '?' || c === '#' || c === '%' || c === '/' || c === '^' || c === ',' || c === '@';
}

function _isSimpleParamOp(c) {
  return c === '-' || c === '+' || c === '=' || c === '?';
}

function _isEscapeCharInDquote(c) {
  return c === '$' || c === '`' || c === '"' || c === '\\' || c === '\n';
}

function _isListTerminator(c) {
  return c === ')' || c === '}' || c === ']';
}

function _isSemicolonOrAmp(c) {
  return c === ';' || c === '&';
}

function _isParen(c) {
  return c === '(' || c === ')';
}

function _isCaretOrBang(c) {
  return c === '^' || c === '!';
}

function _isAtOrStar(c) {
  return c === '@' || c === '*';
}

function _isDigitOrDash(c) {
  return _isDigit(c) || c === '-';
}

function _isNewlineOrRightParen(c) {
  return c === '\n' || c === ')';
}

function _isNewlineOrRightBracket(c) {
  return c === '\n' || c === ']';
}

function _isSemicolonNewlineBrace(c) {
  return c === ';' || c === '\n' || c === '{';
}

// Reserved words and keywords as Sets for O(1) lookup
const RESERVED_WORDS = new Set([
  'if', 'then', 'else', 'elif', 'fi',
  'case', 'esac', 'for', 'select', 'while', 'until',
  'do', 'done', 'in', 'function', 'time',
  '{', '}', '!', '[[', ']]', 'coproc'
]);

const COMPOUND_KEYWORDS = new Set([
  'if', 'case', 'for', 'select', 'while', 'until', '{', '[[', '(('
]);

const COND_UNARY_OPS = new Set([
  '-a', '-b', '-c', '-d', '-e', '-f', '-g', '-h', '-k', '-p',
  '-r', '-s', '-t', '-u', '-w', '-x', '-G', '-L', '-N', '-O',
  '-S', '-z', '-n', '-o', '-v', '-R'
]);

const COND_BINARY_OPS = new Set([
  '==', '!=', '=~', '=', '<', '>',
  '-eq', '-ne', '-lt', '-le', '-gt', '-ge',
  '-nt', '-ot', '-ef'
]);

function _isReservedWord(word) {
  return RESERVED_WORDS.has(word);
}

function _isCompoundKeyword(word) {
  return COMPOUND_KEYWORDS.has(word);
}

function _isCondUnaryOp(op) {
  return COND_UNARY_OPS.has(op);
}

function _isCondBinaryOp(op) {
  return COND_BINARY_OPS.has(op);
}

function _strContains(haystack, needle) {
  return haystack.indexOf(needle) !== -1;
}

// ============================================================================
// AST Node Base Class
// ============================================================================

class Node {
  constructor() {
    this.kind = 'node';
  }

  toSexp() {
    throw new Error('NotImplementedError');
  }
}

// ============================================================================
// Word Node
// ============================================================================

class Word extends Node {
  constructor(value, parts = null) {
    super();
    this.kind = 'word';
    this.value = value;
    if (parts === null) {
      parts = [];
    }
    this.parts = parts;
  }

  toSexp() {
    let value = this.value;
    value = this._expandAllAnsiCQuotes(value);
    value = this._stripLocaleStringDollars(value);
    value = this._normalizeArrayWhitespace(value);
    value = this._formatCommandSubstitutions(value);
    value = this._stripArithLineContinuations(value);
    value = this._doubleCtlescSmart(value);
    value = value.replace(/\x7f/g, '\x01\x7f');
    value = value.replace(/\\/g, '\\\\');
    const escaped = value.replace(/"/g, '\\"').replace(/\n/g, '\\n').replace(/\t/g, '\\t');
    return '(word "' + escaped + '")';
  }

  _appendWithCtlesc(result, byteVal) {
    result.push(byteVal);
  }

  _doubleCtlescSmart(value) {
    const result = [];
    let inSingle = false;
    let inDouble = false;
    for (let idx = 0; idx < value.length; idx++) {
      const c = value[idx];
      if (c === "'" && !inDouble) {
        inSingle = !inSingle;
      } else if (c === '"' && !inSingle) {
        inDouble = !inDouble;
      }
      result.push(c);
      if (c === '\x01') {
        if (inDouble) {
          let bsCount = 0;
          for (let j = result.length - 2; j >= 0; j--) {
            if (result[j] === '\\') {
              bsCount += 1;
            } else {
              break;
            }
          }
          if (bsCount % 2 === 0) {
            result.push('\x01');
          }
        } else {
          result.push('\x01');
        }
      }
    }
    return result.join('');
  }

  _expandAnsiCEscapes(value) {
    if (!(value.startsWith("'") && value.endsWith("'"))) {
      return value;
    }
    const inner = _substring(value, 1, value.length - 1);
    const result = [];
    let i = 0;
    while (i < inner.length) {
      if (inner[i] === '\\' && i + 1 < inner.length) {
        const c = inner[i + 1];
        const simple = _getAnsiEscape(c);
        if (simple >= 0) {
          result.push(simple);
          i += 2;
        } else if (c === "'") {
          result.push(39, 92, 39, 39); // '\\''
          i += 2;
        } else if (c === 'x') {
          if (i + 2 < inner.length && inner[i + 2] === '{') {
            let j = i + 3;
            while (j < inner.length && _isHexDigit(inner[j])) {
              j += 1;
            }
            const hexStr = _substring(inner, i + 3, j);
            if (j < inner.length && inner[j] === '}') {
              j += 1;
            }
            if (!hexStr) {
              return "'" + this._decodeBytes(result) + "'";
            }
            const byteVal = parseInt(hexStr, 16) & 0xff;
            if (byteVal === 0) {
              return "'" + this._decodeBytes(result) + "'";
            }
            this._appendWithCtlesc(result, byteVal);
            i = j;
          } else {
            let j = i + 2;
            while (j < inner.length && j < i + 4 && _isHexDigit(inner[j])) {
              j += 1;
            }
            if (j > i + 2) {
              const byteVal = parseInt(_substring(inner, i + 2, j), 16);
              if (byteVal === 0) {
                return "'" + this._decodeBytes(result) + "'";
              }
              this._appendWithCtlesc(result, byteVal);
              i = j;
            } else {
              result.push(inner.charCodeAt(i));
              i += 1;
            }
          }
        } else if (c === 'u') {
          let j = i + 2;
          while (j < inner.length && j < i + 6 && _isHexDigit(inner[j])) {
            j += 1;
          }
          if (j > i + 2) {
            const codepoint = parseInt(_substring(inner, i + 2, j), 16);
            if (codepoint === 0) {
              return "'" + this._decodeBytes(result) + "'";
            }
            const encoded = this._encodeUtf8(codepoint);
            for (let k = 0; k < encoded.length; k++) {
              result.push(encoded[k]);
            }
            i = j;
          } else {
            result.push(inner.charCodeAt(i));
            i += 1;
          }
        } else if (c === 'U') {
          let j = i + 2;
          while (j < inner.length && j < i + 10 && _isHexDigit(inner[j])) {
            j += 1;
          }
          if (j > i + 2) {
            const codepoint = parseInt(_substring(inner, i + 2, j), 16);
            if (codepoint === 0) {
              return "'" + this._decodeBytes(result) + "'";
            }
            const encoded = this._encodeUtf8(codepoint);
            for (let k = 0; k < encoded.length; k++) {
              result.push(encoded[k]);
            }
            i = j;
          } else {
            result.push(inner.charCodeAt(i));
            i += 1;
          }
        } else if (c === 'c') {
          if (i + 3 <= inner.length) {
            const ctrlChar = inner[i + 2];
            const ctrlVal = ctrlChar.charCodeAt(0) & 0x1f;
            if (ctrlVal === 0) {
              return "'" + this._decodeBytes(result) + "'";
            }
            this._appendWithCtlesc(result, ctrlVal);
            i += 3;
          } else {
            result.push(inner.charCodeAt(i));
            i += 1;
          }
        } else if (c === '0') {
          let j = i + 2;
          while (j < inner.length && j < i + 5 && _isOctalDigit(inner[j])) {
            j += 1;
          }
          if (j > i + 2) {
            const byteVal = parseInt(_substring(inner, i + 1, j), 8);
            if (byteVal === 0) {
              return "'" + this._decodeBytes(result) + "'";
            }
            this._appendWithCtlesc(result, byteVal);
            i = j;
          } else {
            return "'" + this._decodeBytes(result) + "'";
          }
        } else if (c >= '1' && c <= '7') {
          let j = i + 1;
          while (j < inner.length && j < i + 4 && _isOctalDigit(inner[j])) {
            j += 1;
          }
          const byteVal = parseInt(_substring(inner, i + 1, j), 8);
          if (byteVal === 0) {
            return "'" + this._decodeBytes(result) + "'";
          }
          this._appendWithCtlesc(result, byteVal);
          i = j;
        } else {
          result.push(0x5c);
          result.push(c.charCodeAt(0));
          i += 2;
        }
      } else {
        const bytes = this._encodeUtf8(inner.charCodeAt(i));
        for (let k = 0; k < bytes.length; k++) {
          result.push(bytes[k]);
        }
        i += 1;
      }
    }
    return "'" + this._decodeBytes(result) + "'";
  }

  _encodeUtf8(codepoint) {
    if (codepoint < 0x80) {
      return [codepoint];
    } else if (codepoint < 0x800) {
      return [0xc0 | (codepoint >> 6), 0x80 | (codepoint & 0x3f)];
    } else if (codepoint < 0x10000) {
      return [0xe0 | (codepoint >> 12), 0x80 | ((codepoint >> 6) & 0x3f), 0x80 | (codepoint & 0x3f)];
    } else {
      return [0xf0 | (codepoint >> 18), 0x80 | ((codepoint >> 12) & 0x3f), 0x80 | ((codepoint >> 6) & 0x3f), 0x80 | (codepoint & 0x3f)];
    }
  }

  _decodeBytes(bytes) {
    try {
      const arr = new Uint8Array(bytes);
      return new TextDecoder('utf-8', { fatal: false }).decode(arr);
    } catch (e) {
      return String.fromCharCode.apply(null, bytes);
    }
  }

  _expandAllAnsiCQuotes(value) {
    const result = [];
    let i = 0;
    let inSingleQuote = false;
    let inDoubleQuote = false;
    let braceDepth = 0;
    while (i < value.length) {
      const ch = value[i];
      if (!inSingleQuote) {
        if (_startsWithAt(value, i, '${')) {
          braceDepth += 1;
          result.push('${');
          i += 2;
          continue;
        } else if (ch === '}' && braceDepth > 0) {
          braceDepth -= 1;
          result.push(ch);
          i += 1;
          continue;
        }
      }
      const effectiveInDquote = inDoubleQuote && braceDepth === 0;
      if (ch === "'" && !effectiveInDquote) {
        if (!inSingleQuote && i > 0 && value[i - 1] === '$') {
          result.push(ch);
          i += 1;
        } else if (inSingleQuote) {
          inSingleQuote = false;
          result.push(ch);
          i += 1;
        } else {
          inSingleQuote = true;
          result.push(ch);
          i += 1;
        }
      } else if (ch === '"' && !inSingleQuote) {
        inDoubleQuote = !inDoubleQuote;
        result.push(ch);
        i += 1;
      } else if (ch === '\\' && i + 1 < value.length && !inSingleQuote) {
        result.push(ch);
        result.push(value[i + 1]);
        i += 2;
      } else if (_startsWithAt(value, i, "$'") && !inSingleQuote && !effectiveInDquote) {
        let j = i + 2;
        while (j < value.length) {
          if (value[j] === '\\' && j + 1 < value.length) {
            j += 2;
          } else if (value[j] === "'") {
            j += 1;
            break;
          } else {
            j += 1;
          }
        }
        const ansiStr = _substring(value, i, j);
        let expanded = this._expandAnsiCEscapes(_substring(ansiStr, 1, ansiStr.length));
        if (braceDepth > 0 && expanded.startsWith("'") && expanded.endsWith("'")) {
          const inner = _substring(expanded, 1, expanded.length - 1);
          if (inner && inner.indexOf('\x01') === -1) {
            let prev = '';
            if (result.length >= 2) {
              prev = _sublist(result, result.length - 2, result.length).join('');
            }
            if (prev.endsWith(':-') || prev.endsWith(':=') || prev.endsWith(':+') || prev.endsWith(':?')) {
              expanded = inner;
            } else if (result.length >= 1) {
              const last = result[result.length - 1];
              if ((last === '-' || last === '=' || last === '+' || last === '?') &&
                  (result.length < 2 || result[result.length - 2] !== ':')) {
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
    return result.join('');
  }

  _stripLocaleStringDollars(value) {
    const result = [];
    let i = 0;
    let inSingleQuote = false;
    let inDoubleQuote = false;
    while (i < value.length) {
      const ch = value[i];
      if (ch === "'" && !inDoubleQuote) {
        inSingleQuote = !inSingleQuote;
        result.push(ch);
        i += 1;
      } else if (ch === '"' && !inSingleQuote) {
        inDoubleQuote = !inDoubleQuote;
        result.push(ch);
        i += 1;
      } else if (ch === '\\' && i + 1 < value.length) {
        result.push(ch);
        result.push(value[i + 1]);
        i += 2;
      } else if (_startsWithAt(value, i, '$"') && !inSingleQuote && !inDoubleQuote) {
        result.push('"');
        inDoubleQuote = true;
        i += 2;
      } else {
        result.push(ch);
        i += 1;
      }
    }
    return result.join('');
  }

  _normalizeArrayWhitespace(value) {
    if (!value.endsWith(')')) {
      return value;
    }
    let i = 0;
    if (!(i < value.length && (value[i].match(/[a-zA-Z]/) || value[i] === '_'))) {
      return value;
    }
    i += 1;
    while (i < value.length && (value[i].match(/[a-zA-Z0-9]/) || value[i] === '_')) {
      i += 1;
    }
    if (i < value.length && value[i] === '+') {
      i += 1;
    }
    if (!(i + 1 < value.length && value[i] === '=' && value[i + 1] === '(')) {
      return value;
    }
    const prefix = _substring(value, 0, i + 1);
    const inner = _substring(value, prefix.length + 1, value.length - 1);
    const normalized = [];
    i = 0;
    let inWhitespace = true;
    while (i < inner.length) {
      const ch = inner[i];
      if (_isWhitespace(ch)) {
        if (!inWhitespace && normalized.length > 0) {
          normalized.push(' ');
          inWhitespace = true;
        }
        i += 1;
      } else if (ch === "'") {
        inWhitespace = false;
        let j = i + 1;
        while (j < inner.length && inner[j] !== "'") {
          j += 1;
        }
        normalized.push(_substring(inner, i, j + 1));
        i = j + 1;
      } else if (ch === '"') {
        inWhitespace = false;
        let j = i + 1;
        while (j < inner.length && inner[j] !== '"') {
          if (inner[j] === '\\' && j + 1 < inner.length) {
            j += 2;
          } else {
            j += 1;
          }
        }
        normalized.push(_substring(inner, i, j + 1));
        i = j + 1;
      } else if (ch === '\\' && i + 1 < inner.length) {
        inWhitespace = false;
        normalized.push(_substring(inner, i, i + 2));
        i += 2;
      } else {
        inWhitespace = false;
        normalized.push(ch);
        i += 1;
      }
    }
    const resultStr = normalized.join('').trimEnd();
    return prefix + '(' + resultStr + ')';
  }

  _stripArithLineContinuations(value) {
    const result = [];
    let i = 0;
    while (i < value.length) {
      if (_startsWithAt(value, i, '$((')) {
        const start = i;
        i += 3;
        let depth = 1;
        const arithContent = [];
        while (i < value.length && depth > 0) {
          if (_startsWithAt(value, i, '((')) {
            arithContent.push('((');
            depth += 1;
            i += 2;
          } else if (_startsWithAt(value, i, '))')) {
            depth -= 1;
            if (depth > 0) {
              arithContent.push('))');
            }
            i += 2;
          } else if (value[i] === '\\' && i + 1 < value.length && value[i + 1] === '\n') {
            i += 2;
          } else {
            arithContent.push(value[i]);
            i += 1;
          }
        }
        if (depth === 0) {
          result.push('$((' + arithContent.join('') + '))');
        } else {
          result.push(_substring(value, start, i));
        }
      } else {
        result.push(value[i]);
        i += 1;
      }
    }
    return result.join('');
  }

  _collectCmdsubs(node) {
    const result = [];
    const nodeKind = node && node.kind ? node.kind : null;
    if (nodeKind === 'cmdsub') {
      result.push(node);
    } else {
      const expr = node && node.expression !== undefined ? node.expression : null;
      if (expr !== null) {
        const sub = this._collectCmdsubs(expr);
        for (let k = 0; k < sub.length; k++) {
          result.push(sub[k]);
        }
      }
    }
    const left = node && node.left !== undefined ? node.left : null;
    if (left !== null) {
      const sub = this._collectCmdsubs(left);
      for (let k = 0; k < sub.length; k++) {
        result.push(sub[k]);
      }
    }
    const right = node && node.right !== undefined ? node.right : null;
    if (right !== null) {
      const sub = this._collectCmdsubs(right);
      for (let k = 0; k < sub.length; k++) {
        result.push(sub[k]);
      }
    }
    const operand = node && node.operand !== undefined ? node.operand : null;
    if (operand !== null) {
      const sub = this._collectCmdsubs(operand);
      for (let k = 0; k < sub.length; k++) {
        result.push(sub[k]);
      }
    }
    const condition = node && node.condition !== undefined ? node.condition : null;
    if (condition !== null) {
      const sub = this._collectCmdsubs(condition);
      for (let k = 0; k < sub.length; k++) {
        result.push(sub[k]);
      }
    }
    const trueValue = node && node.true_value !== undefined ? node.true_value : null;
    if (trueValue !== null) {
      const sub = this._collectCmdsubs(trueValue);
      for (let k = 0; k < sub.length; k++) {
        result.push(sub[k]);
      }
    }
    const falseValue = node && node.false_value !== undefined ? node.false_value : null;
    if (falseValue !== null) {
      const sub = this._collectCmdsubs(falseValue);
      for (let k = 0; k < sub.length; k++) {
        result.push(sub[k]);
      }
    }
    return result;
  }

  _formatCommandSubstitutions(value) {
    const cmdsubParts = [];
    const procsubParts = [];
    for (let idx = 0; idx < this.parts.length; idx++) {
      const p = this.parts[idx];
      if (p.kind === 'cmdsub') {
        cmdsubParts.push(p);
      } else if (p.kind === 'procsub') {
        procsubParts.push(p);
      } else {
        const subs = this._collectCmdsubs(p);
        for (let k = 0; k < subs.length; k++) {
          cmdsubParts.push(subs[k]);
        }
      }
    }
    const hasBraceCmdsub = value.indexOf('${ ') !== -1 || value.indexOf('${|') !== -1;
    if (cmdsubParts.length === 0 && procsubParts.length === 0 && !hasBraceCmdsub) {
      return value;
    }
    const result = [];
    let i = 0;
    let cmdsubIdx = 0;
    let procsubIdx = 0;
    while (i < value.length) {
      if (_startsWithAt(value, i, '$(') && !_startsWithAt(value, i, '$((') && cmdsubIdx < cmdsubParts.length) {
        const j = _findCmdsubEnd(value, i + 2);
        const node = cmdsubParts[cmdsubIdx];
        const formatted = _formatCmdsubNode(node.command);
        if (formatted.startsWith('(')) {
          result.push('$( ' + formatted + ')');
        } else {
          result.push('$(' + formatted + ')');
        }
        cmdsubIdx += 1;
        i = j;
      } else if (value[i] === '`' && cmdsubIdx < cmdsubParts.length) {
        let j = i + 1;
        while (j < value.length) {
          if (value[j] === '\\' && j + 1 < value.length) {
            j += 2;
            continue;
          }
          if (value[j] === '`') {
            j += 1;
            break;
          }
          j += 1;
        }
        result.push(_substring(value, i, j));
        cmdsubIdx += 1;
        i = j;
      } else if ((_startsWithAt(value, i, '>(') || _startsWithAt(value, i, '<(')) && procsubIdx < procsubParts.length) {
        const direction = value[i];
        const j = _findCmdsubEnd(value, i + 2);
        const node = procsubParts[procsubIdx];
        const formatted = _formatCmdsubNode(node.command, true);
        result.push(direction + '(' + formatted + ')');
        procsubIdx += 1;
        i = j;
      } else if (_startsWithAt(value, i, '${ ') || _startsWithAt(value, i, '${|')) {
        const prefix = _substring(value, i, i + 3);
        let j = i + 3;
        let depth = 1;
        while (j < value.length && depth > 0) {
          if (value[j] === '{') {
            depth += 1;
          } else if (value[j] === '}') {
            depth -= 1;
          }
          j += 1;
        }
        const inner = _substring(value, i + 2, j - 1);
        if (inner.trim() === '') {
          result.push('${ }');
        } else {
          try {
            const parser = new Parser(inner.replace(/^[ |]+/, ''));
            const parsed = parser.parseList();
            if (parsed) {
              const formatted = _formatCmdsubNode(parsed);
              result.push(prefix + formatted + '; }');
            } else {
              result.push('${ }');
            }
          } catch (e) {
            result.push(_substring(value, i, j));
          }
        }
        i = j;
      } else {
        result.push(value[i]);
        i += 1;
      }
    }
    return result.join('');
  }

  getCondFormattedValue() {
    let value = this._expandAllAnsiCQuotes(this.value);
    value = this._formatCommandSubstitutions(value);
    value = value.replace(/\x01/g, '\x01\x01');
    return value.replace(/\n+$/, '');
  }
}

// ============================================================================
// Command Node
// ============================================================================

class Command extends Node {
  constructor(words, redirects = null) {
    super();
    this.kind = 'command';
    this.words = words;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    const parts = [];
    for (let i = 0; i < this.words.length; i++) {
      parts.push(this.words[i].toSexp());
    }
    for (let i = 0; i < this.redirects.length; i++) {
      parts.push(this.redirects[i].toSexp());
    }
    const inner = parts.join(' ');
    if (!inner) {
      return '(command)';
    }
    return '(command ' + inner + ')';
  }
}

// ============================================================================
// Pipeline Node
// ============================================================================

class Pipeline extends Node {
  constructor(commands) {
    super();
    this.kind = 'pipeline';
    this.commands = commands;
  }

  toSexp() {
    if (this.commands.length === 1) {
      return this.commands[0].toSexp();
    }
    const cmds = [];
    let i = 0;
    while (i < this.commands.length) {
      const cmd = this.commands[i];
      if (cmd.kind === 'pipe-both') {
        i += 1;
        continue;
      }
      const needsRedirect = i + 1 < this.commands.length && this.commands[i + 1].kind === 'pipe-both';
      cmds.push([cmd, needsRedirect]);
      i += 1;
    }
    if (cmds.length === 1) {
      const pair = cmds[0];
      return this._cmdSexp(pair[0], pair[1]);
    }
    const lastPair = cmds[cmds.length - 1];
    let result = this._cmdSexp(lastPair[0], lastPair[1]);
    let j = cmds.length - 2;
    while (j >= 0) {
      const pair = cmds[j];
      const cmd = pair[0];
      const needs = pair[1];
      if (needs && cmd.kind !== 'command') {
        result = '(pipe ' + cmd.toSexp() + ' (redirect ">&" 1) ' + result + ')';
      } else {
        result = '(pipe ' + this._cmdSexp(cmd, needs) + ' ' + result + ')';
      }
      j -= 1;
    }
    return result;
  }

  _cmdSexp(cmd, needsRedirect) {
    if (!needsRedirect) {
      return cmd.toSexp();
    }
    if (cmd.kind === 'command') {
      const parts = [];
      for (let i = 0; i < cmd.words.length; i++) {
        parts.push(cmd.words[i].toSexp());
      }
      for (let i = 0; i < cmd.redirects.length; i++) {
        parts.push(cmd.redirects[i].toSexp());
      }
      parts.push('(redirect ">&" 1)');
      return '(command ' + parts.join(' ') + ')';
    }
    return cmd.toSexp();
  }
}

// ============================================================================
// List Node
// ============================================================================

class List extends Node {
  constructor(parts) {
    super();
    this.kind = 'list';
    this.parts = parts;
  }

  toSexp() {
    let parts = this.parts.slice();
    const opNames = { '&&': 'and', '||': 'or', ';': 'semi', '\n': 'semi', '&': 'background' };
    while (parts.length > 1 && parts[parts.length - 1].kind === 'operator' &&
           (parts[parts.length - 1].op === ';' || parts[parts.length - 1].op === '\n')) {
      parts = _sublist(parts, 0, parts.length - 1);
    }
    if (parts.length === 1) {
      return parts[0].toSexp();
    }
    if (parts[parts.length - 1].kind === 'operator' && parts[parts.length - 1].op === '&') {
      for (let i = parts.length - 3; i > 0; i -= 2) {
        if (parts[i].kind === 'operator' && (parts[i].op === ';' || parts[i].op === '\n')) {
          const left = _sublist(parts, 0, i);
          const right = _sublist(parts, i + 1, parts.length - 1);
          let leftSexp;
          if (left.length > 1) {
            leftSexp = new List(left).toSexp();
          } else {
            leftSexp = left[0].toSexp();
          }
          let rightSexp;
          if (right.length > 1) {
            rightSexp = new List(right).toSexp();
          } else {
            rightSexp = right[0].toSexp();
          }
          return '(semi ' + leftSexp + ' (background ' + rightSexp + '))';
        }
      }
      const innerParts = _sublist(parts, 0, parts.length - 1);
      if (innerParts.length === 1) {
        return '(background ' + innerParts[0].toSexp() + ')';
      }
      const innerList = new List(innerParts);
      return '(background ' + innerList.toSexp() + ')';
    }
    return this._toSexpWithPrecedence(parts, opNames);
  }

  _toSexpWithPrecedence(parts, opNames) {
    for (let i = parts.length - 2; i > 0; i -= 2) {
      if (parts[i].kind === 'operator' && (parts[i].op === ';' || parts[i].op === '\n')) {
        const left = _sublist(parts, 0, i);
        const right = _sublist(parts, i + 1, parts.length);
        let leftSexp;
        if (left.length > 1) {
          leftSexp = new List(left).toSexp();
        } else {
          leftSexp = left[0].toSexp();
        }
        let rightSexp;
        if (right.length > 1) {
          rightSexp = new List(right).toSexp();
        } else {
          rightSexp = right[0].toSexp();
        }
        return '(semi ' + leftSexp + ' ' + rightSexp + ')';
      }
    }
    for (let i = parts.length - 2; i > 0; i -= 2) {
      if (parts[i].kind === 'operator' && parts[i].op === '&') {
        const left = _sublist(parts, 0, i);
        const right = _sublist(parts, i + 1, parts.length);
        let leftSexp;
        if (left.length > 1) {
          leftSexp = new List(left).toSexp();
        } else {
          leftSexp = left[0].toSexp();
        }
        let rightSexp;
        if (right.length > 1) {
          rightSexp = new List(right).toSexp();
        } else {
          rightSexp = right[0].toSexp();
        }
        return '(background ' + leftSexp + ' ' + rightSexp + ')';
      }
    }
    let result = parts[0].toSexp();
    for (let i = 1; i < parts.length - 1; i += 2) {
      const op = parts[i];
      const cmd = parts[i + 1];
      const opName = opNames[op.op] || op.op;
      result = '(' + opName + ' ' + result + ' ' + cmd.toSexp() + ')';
    }
    return result;
  }
}

// ============================================================================
// Operator Node
// ============================================================================

class Operator extends Node {
  constructor(op) {
    super();
    this.kind = 'operator';
    this.op = op;
  }

  toSexp() {
    const names = { '&&': 'and', '||': 'or', ';': 'semi', '&': 'bg', '|': 'pipe' };
    return '(' + (names[this.op] || this.op) + ')';
  }
}

// ============================================================================
// PipeBoth Node
// ============================================================================

class PipeBoth extends Node {
  constructor() {
    super();
    this.kind = 'pipe-both';
  }

  toSexp() {
    return '(pipe-both)';
  }
}

// ============================================================================
// Empty Node
// ============================================================================

class Empty extends Node {
  constructor() {
    super();
    this.kind = 'empty';
  }

  toSexp() {
    return '';
  }
}

// ============================================================================
// Comment Node
// ============================================================================

class Comment extends Node {
  constructor(text) {
    super();
    this.kind = 'comment';
    this.text = text;
  }

  toSexp() {
    return '';
  }
}

// ============================================================================
// Redirect Node
// ============================================================================

class Redirect extends Node {
  constructor(op, target, fd = null) {
    super();
    this.kind = 'redirect';
    this.op = op;
    this.target = target;
    this.fd = fd;
  }

  toSexp() {
    let op = this.op.replace(/^[0-9]+/, '');
    if (op.startsWith('{')) {
      let j = 1;
      if (j < op.length && (op[j].match(/[a-zA-Z]/) || op[j] === '_')) {
        j += 1;
        while (j < op.length && (op[j].match(/[a-zA-Z0-9]/) || op[j] === '_')) {
          j += 1;
        }
        if (j < op.length && op[j] === '}') {
          op = _substring(op, j + 1, op.length);
        }
      }
    }
    let targetVal = this.target.value;
    targetVal = new Word(targetVal)._expandAllAnsiCQuotes(targetVal);
    targetVal = targetVal.replace(/\$"/g, '"');
    if (targetVal.startsWith('&')) {
      if (op === '>') {
        op = '>&';
      } else if (op === '<') {
        op = '<&';
      }
      const fdTarget = _substring(targetVal, 1, targetVal.length).replace(/-$/, '');
      if (fdTarget.match(/^\d+$/)) {
        return '(redirect "' + op + '" ' + fdTarget + ')';
      } else if (targetVal === '&-') {
        return '(redirect ">&-" 0)';
      } else {
        return '(redirect "' + op + '" "' + fdTarget + '")';
      }
    }
    if (op === '>&' || op === '<&') {
      if (targetVal.match(/^\d+$/)) {
        return '(redirect "' + op + '" ' + targetVal + ')';
      }
      targetVal = targetVal.replace(/-$/, '');
      return '(redirect "' + op + '" "' + targetVal + '")';
    }
    return '(redirect "' + op + '" "' + targetVal + '")';
  }
}

// ============================================================================
// HereDoc Node
// ============================================================================

class HereDoc extends Node {
  constructor(delimiter, content, stripTabs = false, quoted = false, fd = null) {
    super();
    this.kind = 'heredoc';
    this.delimiter = delimiter;
    this.content = content;
    this.stripTabs = stripTabs;
    this.quoted = quoted;
    this.fd = fd;
  }

  toSexp() {
    let op;
    if (this.stripTabs) {
      op = '<<-';
    } else {
      op = '<<';
    }
    return '(redirect "' + op + '" "' + this.content + '")';
  }
}

// ============================================================================
// Subshell Node
// ============================================================================

class Subshell extends Node {
  constructor(body, redirects = null) {
    super();
    this.kind = 'subshell';
    this.body = body;
    this.redirects = redirects;
  }

  toSexp() {
    const base = '(subshell ' + this.body.toSexp() + ')';
    if (this.redirects) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      return base + ' ' + redirectParts.join(' ');
    }
    return base;
  }
}

// ============================================================================
// BraceGroup Node
// ============================================================================

class BraceGroup extends Node {
  constructor(body, redirects = null) {
    super();
    this.kind = 'brace-group';
    this.body = body;
    this.redirects = redirects;
  }

  toSexp() {
    const base = '(brace-group ' + this.body.toSexp() + ')';
    if (this.redirects) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      return base + ' ' + redirectParts.join(' ');
    }
    return base;
  }
}

// ============================================================================
// If Node
// ============================================================================

class If extends Node {
  constructor(condition, thenBody, elseBody = null, redirects = null) {
    super();
    this.kind = 'if';
    this.condition = condition;
    this.thenBody = thenBody;
    this.elseBody = elseBody;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    let result = '(if ' + this.condition.toSexp() + ' ' + this.thenBody.toSexp();
    if (this.elseBody) {
      result = result + ' ' + this.elseBody.toSexp();
    }
    result = result + ')';
    for (let i = 0; i < this.redirects.length; i++) {
      result = result + ' ' + this.redirects[i].toSexp();
    }
    return result;
  }
}

// ============================================================================
// While Node
// ============================================================================

class While extends Node {
  constructor(condition, body, redirects = null) {
    super();
    this.kind = 'while';
    this.condition = condition;
    this.body = body;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    const base = '(while ' + this.condition.toSexp() + ' ' + this.body.toSexp() + ')';
    if (this.redirects.length > 0) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      return base + ' ' + redirectParts.join(' ');
    }
    return base;
  }
}

// ============================================================================
// Until Node
// ============================================================================

class Until extends Node {
  constructor(condition, body, redirects = null) {
    super();
    this.kind = 'until';
    this.condition = condition;
    this.body = body;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    const base = '(until ' + this.condition.toSexp() + ' ' + this.body.toSexp() + ')';
    if (this.redirects.length > 0) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      return base + ' ' + redirectParts.join(' ');
    }
    return base;
  }
}

// ============================================================================
// For Node
// ============================================================================

class For extends Node {
  constructor(varName, words, body, redirects = null) {
    super();
    this.kind = 'for';
    this.var = varName;
    this.words = words;
    this.body = body;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    let suffix = '';
    if (this.redirects.length > 0) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      suffix = ' ' + redirectParts.join(' ');
    }
    const varEscaped = this.var.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    if (this.words === null) {
      return '(for (word "' + varEscaped + '") (in (word "\\"$@\\"")) ' + this.body.toSexp() + ')' + suffix;
    } else if (this.words.length === 0) {
      return '(for (word "' + varEscaped + '") (in) ' + this.body.toSexp() + ')' + suffix;
    } else {
      const wordParts = [];
      for (let i = 0; i < this.words.length; i++) {
        wordParts.push(this.words[i].toSexp());
      }
      const wordStrs = wordParts.join(' ');
      return '(for (word "' + varEscaped + '") (in ' + wordStrs + ') ' + this.body.toSexp() + ')' + suffix;
    }
  }
}

// ============================================================================
// ForArith Node
// ============================================================================

class ForArith extends Node {
  constructor(init, cond, incr, body, redirects = null) {
    super();
    this.kind = 'for-arith';
    this.init = init;
    this.cond = cond;
    this.incr = incr;
    this.body = body;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    function formatArithVal(s) {
      const w = new Word(s, []);
      let val = w._expandAllAnsiCQuotes(s);
      val = w._stripLocaleStringDollars(val);
      val = val.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
      return val;
    }
    let suffix = '';
    if (this.redirects.length > 0) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      suffix = ' ' + redirectParts.join(' ');
    }
    let initVal;
    if (this.init) {
      initVal = this.init;
    } else {
      initVal = '1';
    }
    let condVal;
    if (this.cond) {
      condVal = _normalizeFdRedirects(this.cond);
    } else {
      condVal = '1';
    }
    let incrVal;
    if (this.incr) {
      incrVal = this.incr;
    } else {
      incrVal = '1';
    }
    return '(arith-for (init (word "' + formatArithVal(initVal) + '")) ' +
           '(test (word "' + formatArithVal(condVal) + '")) ' +
           '(step (word "' + formatArithVal(incrVal) + '")) ' +
           this.body.toSexp() + ')' + suffix;
  }
}

// ============================================================================
// Select Node
// ============================================================================

class Select extends Node {
  constructor(varName, words, body, redirects = null) {
    super();
    this.kind = 'select';
    this.var = varName;
    this.words = words;
    this.body = body;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    let suffix = '';
    if (this.redirects.length > 0) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      suffix = ' ' + redirectParts.join(' ');
    }
    const varEscaped = this.var.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    let inClause;
    if (this.words !== null) {
      const wordParts = [];
      for (let i = 0; i < this.words.length; i++) {
        wordParts.push(this.words[i].toSexp());
      }
      const wordStrs = wordParts.join(' ');
      if (this.words.length > 0) {
        inClause = '(in ' + wordStrs + ')';
      } else {
        inClause = '(in)';
      }
    } else {
      inClause = '(in (word "\\"$@\\""))';
    }
    return '(select (word "' + varEscaped + '") ' + inClause + ' ' + this.body.toSexp() + ')' + suffix;
  }
}

// ============================================================================
// Case Node
// ============================================================================

class Case extends Node {
  constructor(word, patterns, redirects = null) {
    super();
    this.kind = 'case';
    this.word = word;
    this.patterns = patterns;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    const parts = [];
    parts.push('(case ' + this.word.toSexp());
    for (let i = 0; i < this.patterns.length; i++) {
      parts.push(this.patterns[i].toSexp());
    }
    const base = parts.join(' ') + ')';
    if (this.redirects.length > 0) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      return base + ' ' + redirectParts.join(' ');
    }
    return base;
  }
}

// ============================================================================
// CasePattern Node
// ============================================================================

function _consumeSingleQuote(s, start) {
  const chars = ["'"];
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

function _consumeDoubleQuote(s, start) {
  const chars = ['"'];
  let i = start + 1;
  while (i < s.length && s[i] !== '"') {
    if (s[i] === '\\' && i + 1 < s.length) {
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
  let i = start;
  while (i < s.length) {
    if (s[i] === ']') {
      return true;
    }
    if ((s[i] === '|' || s[i] === ')') && depth === 0) {
      return false;
    }
    i += 1;
  }
  return false;
}

function _consumeBracketClass(s, start, depth) {
  let scanPos = start + 1;
  if (scanPos < s.length && (s[scanPos] === '!' || s[scanPos] === '^')) {
    scanPos += 1;
  }
  if (scanPos < s.length && s[scanPos] === ']') {
    if (_hasBracketClose(s, scanPos + 1, depth)) {
      scanPos += 1;
    }
  }
  let isBracket = false;
  while (scanPos < s.length) {
    if (s[scanPos] === ']') {
      isBracket = true;
      break;
    }
    if (s[scanPos] === ')' && depth === 0) {
      break;
    }
    scanPos += 1;
  }
  if (!isBracket) {
    return [start + 1, ['['], false];
  }
  const chars = ['['];
  let i = start + 1;
  if (i < s.length && (s[i] === '!' || s[i] === '^')) {
    chars.push(s[i]);
    i += 1;
  }
  if (i < s.length && s[i] === ']') {
    if (_hasBracketClose(s, i + 1, depth)) {
      chars.push(s[i]);
      i += 1;
    }
  }
  while (i < s.length && s[i] !== ']') {
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
  constructor(pattern, body, terminator = ';;') {
    super();
    this.kind = 'pattern';
    this.pattern = pattern;
    this.body = body;
    this.terminator = terminator;
  }

  toSexp() {
    const alternatives = [];
    let current = [];
    let i = 0;
    let depth = 0;
    while (i < this.pattern.length) {
      const ch = this.pattern[i];
      if (ch === '\\' && i + 1 < this.pattern.length) {
        current.push(_substring(this.pattern, i, i + 2));
        i += 2;
      } else if ((ch === '@' || ch === '?' || ch === '*' || ch === '+' || ch === '!') &&
                 i + 1 < this.pattern.length && this.pattern[i + 1] === '(') {
        current.push(ch);
        current.push('(');
        depth += 1;
        i += 2;
      } else if (ch === '$' && i + 1 < this.pattern.length && this.pattern[i + 1] === '(') {
        current.push(ch);
        current.push('(');
        depth += 1;
        i += 2;
      } else if (ch === '(' && depth > 0) {
        current.push(ch);
        depth += 1;
        i += 1;
      } else if (ch === ')' && depth > 0) {
        current.push(ch);
        depth -= 1;
        i += 1;
      } else if (ch === '[') {
        const result = _consumeBracketClass(this.pattern, i, depth);
        i = result[0];
        for (let k = 0; k < result[1].length; k++) {
          current.push(result[1][k]);
        }
      } else if (ch === "'" && depth === 0) {
        const result = _consumeSingleQuote(this.pattern, i);
        i = result[0];
        for (let k = 0; k < result[1].length; k++) {
          current.push(result[1][k]);
        }
      } else if (ch === '"' && depth === 0) {
        const result = _consumeDoubleQuote(this.pattern, i);
        i = result[0];
        for (let k = 0; k < result[1].length; k++) {
          current.push(result[1][k]);
        }
      } else if (ch === '|' && depth === 0) {
        alternatives.push(current.join(''));
        current = [];
        i += 1;
      } else {
        current.push(ch);
        i += 1;
      }
    }
    alternatives.push(current.join(''));
    const wordList = [];
    for (let idx = 0; idx < alternatives.length; idx++) {
      wordList.push(new Word(alternatives[idx]).toSexp());
    }
    const patternStr = wordList.join(' ');
    const parts = ['(pattern (' + patternStr + ')'];
    if (this.body) {
      parts.push(' ' + this.body.toSexp());
    } else {
      parts.push(' ()');
    }
    parts.push(')');
    return parts.join('');
  }
}

// ============================================================================
// Function Node
// ============================================================================

class Function extends Node {
  constructor(name, body) {
    super();
    this.kind = 'function';
    this.name = name;
    this.body = body;
  }

  toSexp() {
    return '(function "' + this.name + '" ' + this.body.toSexp() + ')';
  }
}

// ============================================================================
// ParamExpansion Node
// ============================================================================

class ParamExpansion extends Node {
  constructor(param, op = null, arg = null) {
    super();
    this.kind = 'param';
    this.param = param;
    this.op = op;
    this.arg = arg;
  }

  toSexp() {
    const escapedParam = this.param.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    if (this.op !== null) {
      const escapedOp = this.op.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
      let argVal;
      if (this.arg !== null) {
        argVal = this.arg;
      } else {
        argVal = '';
      }
      const escapedArg = argVal.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
      return '(param "' + escapedParam + '" "' + escapedOp + '" "' + escapedArg + '")';
    }
    return '(param "' + escapedParam + '")';
  }
}

// ============================================================================
// ParamLength Node
// ============================================================================

class ParamLength extends Node {
  constructor(param) {
    super();
    this.kind = 'param-len';
    this.param = param;
  }

  toSexp() {
    const escaped = this.param.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    return '(param-len "' + escaped + '")';
  }
}

// ============================================================================
// ParamIndirect Node
// ============================================================================

class ParamIndirect extends Node {
  constructor(param, op = null, arg = null) {
    super();
    this.kind = 'param-indirect';
    this.param = param;
    this.op = op;
    this.arg = arg;
  }

  toSexp() {
    const escaped = this.param.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
    if (this.op !== null) {
      const escapedOp = this.op.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
      let argVal;
      if (this.arg !== null) {
        argVal = this.arg;
      } else {
        argVal = '';
      }
      const escapedArg = argVal.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
      return '(param-indirect "' + escaped + '" "' + escapedOp + '" "' + escapedArg + '")';
    }
    return '(param-indirect "' + escaped + '")';
  }
}

// ============================================================================
// CommandSubstitution Node
// ============================================================================

class CommandSubstitution extends Node {
  constructor(command) {
    super();
    this.kind = 'cmdsub';
    this.command = command;
  }

  toSexp() {
    return '(cmdsub ' + this.command.toSexp() + ')';
  }
}

// ============================================================================
// ArithmeticExpansion Node
// ============================================================================

class ArithmeticExpansion extends Node {
  constructor(expression) {
    super();
    this.kind = 'arith';
    this.expression = expression;
  }

  toSexp() {
    if (this.expression === null) {
      return '(arith)';
    }
    return '(arith ' + this.expression.toSexp() + ')';
  }
}

// ============================================================================
// ArithmeticCommand Node
// ============================================================================

class ArithmeticCommand extends Node {
  constructor(expression, redirects = null, rawContent = '') {
    super();
    this.kind = 'arith-cmd';
    this.expression = expression;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
    this.rawContent = rawContent;
  }

  toSexp() {
    let content = this.expression;
    if (this.rawContent) {
      content = this.rawContent;
    }
    const escaped = content.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
    let result = '(arith (word "' + escaped + '"))';
    if (this.redirects.length > 0) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      const redirectSexps = redirectParts.join(' ');
      return result + ' ' + redirectSexps;
    }
    return result;
  }
}

// ============================================================================
// Arithmetic Expression Nodes
// ============================================================================

class ArithNumber extends Node {
  constructor(value) {
    super();
    this.kind = 'number';
    this.value = value;
  }

  toSexp() {
    return '(number "' + this.value + '")';
  }
}

class ArithVar extends Node {
  constructor(name) {
    super();
    this.kind = 'var';
    this.name = name;
  }

  toSexp() {
    return '(var "' + this.name + '")';
  }
}

class ArithBinaryOp extends Node {
  constructor(op, left, right) {
    super();
    this.kind = 'binary-op';
    this.op = op;
    this.left = left;
    this.right = right;
  }

  toSexp() {
    return '(binary-op "' + this.op + '" ' + this.left.toSexp() + ' ' + this.right.toSexp() + ')';
  }
}

class ArithUnaryOp extends Node {
  constructor(op, operand) {
    super();
    this.kind = 'unary-op';
    this.op = op;
    this.operand = operand;
  }

  toSexp() {
    return '(unary-op "' + this.op + '" ' + this.operand.toSexp() + ')';
  }
}

class ArithPreIncr extends Node {
  constructor(operand) {
    super();
    this.kind = 'pre-incr';
    this.operand = operand;
  }

  toSexp() {
    return '(pre-incr ' + this.operand.toSexp() + ')';
  }
}

class ArithPostIncr extends Node {
  constructor(operand) {
    super();
    this.kind = 'post-incr';
    this.operand = operand;
  }

  toSexp() {
    return '(post-incr ' + this.operand.toSexp() + ')';
  }
}

class ArithPreDecr extends Node {
  constructor(operand) {
    super();
    this.kind = 'pre-decr';
    this.operand = operand;
  }

  toSexp() {
    return '(pre-decr ' + this.operand.toSexp() + ')';
  }
}

class ArithPostDecr extends Node {
  constructor(operand) {
    super();
    this.kind = 'post-decr';
    this.operand = operand;
  }

  toSexp() {
    return '(post-decr ' + this.operand.toSexp() + ')';
  }
}

class ArithAssign extends Node {
  constructor(op, target, value) {
    super();
    this.kind = 'assign';
    this.op = op;
    this.target = target;
    this.value = value;
  }

  toSexp() {
    return '(assign "' + this.op + '" ' + this.target.toSexp() + ' ' + this.value.toSexp() + ')';
  }
}

class ArithTernary extends Node {
  constructor(condition, ifTrue, ifFalse) {
    super();
    this.kind = 'ternary';
    this.condition = condition;
    this.ifTrue = ifTrue;
    this.ifFalse = ifFalse;
  }

  toSexp() {
    return '(ternary ' + this.condition.toSexp() + ' ' + this.ifTrue.toSexp() + ' ' + this.ifFalse.toSexp() + ')';
  }
}

class ArithComma extends Node {
  constructor(left, right) {
    super();
    this.kind = 'comma';
    this.left = left;
    this.right = right;
  }

  toSexp() {
    return '(comma ' + this.left.toSexp() + ' ' + this.right.toSexp() + ')';
  }
}

class ArithSubscript extends Node {
  constructor(array, index) {
    super();
    this.kind = 'subscript';
    this.array = array;
    this.index = index;
  }

  toSexp() {
    return '(subscript "' + this.array + '" ' + this.index.toSexp() + ')';
  }
}

class ArithEscape extends Node {
  constructor(char) {
    super();
    this.kind = 'escape';
    this.char = char;
  }

  toSexp() {
    return '(escape "' + this.char + '")';
  }
}

class ArithDeprecated extends Node {
  constructor(expression) {
    super();
    this.kind = 'arith-deprecated';
    this.expression = expression;
  }

  toSexp() {
    const escaped = this.expression.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
    return '(arith-deprecated "' + escaped + '")';
  }
}

// ============================================================================
// Other Nodes
// ============================================================================

class AnsiCQuote extends Node {
  constructor(content) {
    super();
    this.kind = 'ansi-c';
    this.content = content;
  }

  toSexp() {
    const escaped = this.content.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
    return '(ansi-c "' + escaped + '")';
  }
}

class LocaleString extends Node {
  constructor(content) {
    super();
    this.kind = 'locale';
    this.content = content;
  }

  toSexp() {
    const escaped = this.content.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
    return '(locale "' + escaped + '")';
  }
}

class ProcessSubstitution extends Node {
  constructor(direction, command) {
    super();
    this.kind = 'procsub';
    this.direction = direction;
    this.command = command;
  }

  toSexp() {
    return '(procsub "' + this.direction + '" ' + this.command.toSexp() + ')';
  }
}

class Negation extends Node {
  constructor(pipeline) {
    super();
    this.kind = 'negation';
    this.pipeline = pipeline;
  }

  toSexp() {
    if (this.pipeline === null) {
      return '(negation (command))';
    }
    return '(negation ' + this.pipeline.toSexp() + ')';
  }
}

class Time extends Node {
  constructor(pipeline, posix = false) {
    super();
    this.kind = 'time';
    this.pipeline = pipeline;
    this.posix = posix;
  }

  toSexp() {
    if (this.pipeline === null) {
      if (this.posix) {
        return '(time -p (command))';
      } else {
        return '(time (command))';
      }
    }
    if (this.posix) {
      return '(time -p ' + this.pipeline.toSexp() + ')';
    }
    return '(time ' + this.pipeline.toSexp() + ')';
  }
}

class ConditionalExpr extends Node {
  constructor(body, redirects = null) {
    super();
    this.kind = 'cond-expr';
    this.body = body;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    const bodyKind = this.body && this.body.kind ? this.body.kind : null;
    let result;
    if (bodyKind === null) {
      const escaped = this.body.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n');
      result = '(cond "' + escaped + '")';
    } else {
      result = '(cond ' + this.body.toSexp() + ')';
    }
    if (this.redirects.length > 0) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      const redirectSexps = redirectParts.join(' ');
      return result + ' ' + redirectSexps;
    }
    return result;
  }
}

class UnaryTest extends Node {
  constructor(op, operand) {
    super();
    this.kind = 'unary-test';
    this.op = op;
    this.operand = operand;
  }

  toSexp() {
    return '(cond-unary "' + this.op + '" ' + this._formatOperand(this.operand) + ')';
  }

  _formatOperand(word) {
    const value = word.getCondFormattedValue();
    const escaped = value.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\t/g, '\\t');
    return '(cond-term "' + escaped + '")';
  }
}

class BinaryTest extends Node {
  constructor(op, left, right) {
    super();
    this.kind = 'binary-test';
    this.op = op;
    this.left = left;
    this.right = right;
  }

  toSexp() {
    return '(cond-binary "' + this.op + '" ' + this._formatOperand(this.left) + ' ' + this._formatOperand(this.right) + ')';
  }

  _formatOperand(word) {
    const value = word.getCondFormattedValue();
    const escaped = value.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\t/g, '\\t');
    return '(cond-term "' + escaped + '")';
  }
}

class CondAnd extends Node {
  constructor(left, right) {
    super();
    this.kind = 'cond-and';
    this.left = left;
    this.right = right;
  }

  toSexp() {
    return '(cond-and ' + this.left.toSexp() + ' ' + this.right.toSexp() + ')';
  }
}

class CondOr extends Node {
  constructor(left, right) {
    super();
    this.kind = 'cond-or';
    this.left = left;
    this.right = right;
  }

  toSexp() {
    return '(cond-or ' + this.left.toSexp() + ' ' + this.right.toSexp() + ')';
  }
}

class CondNot extends Node {
  constructor(operand) {
    super();
    this.kind = 'cond-not';
    this.operand = operand;
  }

  toSexp() {
    return '(cond-not ' + this.operand.toSexp() + ')';
  }
}

class Coproc extends Node {
  constructor(command, name = null) {
    super();
    this.kind = 'coproc';
    this.command = command;
    this.name = name;
  }

  toSexp() {
    if (this.name !== null) {
      return '(coproc (word "' + this.name + '") ' + this.command.toSexp() + ')';
    }
    return '(coproc ' + this.command.toSexp() + ')';
  }
}

class TestCommand extends Node {
  constructor(body, redirects = null) {
    super();
    this.kind = 'test-cmd';
    this.body = body;
    if (redirects === null) {
      redirects = [];
    }
    this.redirects = redirects;
  }

  toSexp() {
    const parts = ['(test'];
    if (this.body) {
      parts.push(' ' + this.body.toSexp());
    }
    parts.push(')');
    if (this.redirects.length > 0) {
      const redirectParts = [];
      for (let i = 0; i < this.redirects.length; i++) {
        redirectParts.push(this.redirects[i].toSexp());
      }
      parts.push(' ' + redirectParts.join(' '));
    }
    return parts.join('');
  }
}

// ============================================================================
// Helper Functions for Formatting
// ============================================================================

function _findCmdsubEnd(value, start) {
  let i = start;
  let depth = 1;
  while (i < value.length && depth > 0) {
    const ch = value[i];
    if (ch === '(') {
      depth += 1;
      i += 1;
    } else if (ch === ')') {
      depth -= 1;
      i += 1;
    } else if (ch === '"') {
      i += 1;
      while (i < value.length && value[i] !== '"') {
        if (value[i] === '\\' && i + 1 < value.length) {
          i += 2;
        } else {
          i += 1;
        }
      }
      if (i < value.length) {
        i += 1;
      }
    } else if (ch === "'") {
      i += 1;
      while (i < value.length && value[i] !== "'") {
        i += 1;
      }
      if (i < value.length) {
        i += 1;
      }
    } else if (ch === '\\' && i + 1 < value.length) {
      i += 2;
    } else {
      i += 1;
    }
  }
  return i;
}

function _formatCmdsubNode(node, inProcsub = false) {
  if (!node) {
    return '';
  }
  const kind = node.kind;
  if (kind === 'command') {
    const parts = [];
    for (let i = 0; i < node.words.length; i++) {
      const w = node.words[i];
      let val = w.value;
      val = new Word(val)._expandAllAnsiCQuotes(val);
      val = val.replace(/\$"/g, '"');
      parts.push(val);
    }
    for (let i = 0; i < node.redirects.length; i++) {
      parts.push(_formatRedirect(node.redirects[i]));
    }
    return parts.join(' ');
  } else if (kind === 'pipeline') {
    const parts = [];
    for (let i = 0; i < node.commands.length; i++) {
      const cmd = node.commands[i];
      if (cmd.kind === 'pipe-both') {
        parts.push('|&');
      } else {
        parts.push(_formatCmdsubNode(cmd, inProcsub));
      }
    }
    return parts.join(' | ').replace(/\| \|&/g, '|&');
  } else if (kind === 'list') {
    const parts = [];
    for (let i = 0; i < node.parts.length; i++) {
      const p = node.parts[i];
      if (p.kind === 'operator') {
        if (p.op === '\n') {
          parts.push(';');
        } else {
          parts.push(p.op);
        }
      } else {
        parts.push(_formatCmdsubNode(p, inProcsub));
      }
    }
    return parts.join(' ');
  } else if (kind === 'subshell') {
    const bodyStr = _formatCmdsubNode(node.body, inProcsub);
    let base;
    if (inProcsub) {
      base = '( ' + bodyStr + ')';
    } else {
      base = '(' + bodyStr + ')';
    }
    if (node.redirects) {
      const redirectParts = [];
      for (let i = 0; i < node.redirects.length; i++) {
        redirectParts.push(_formatRedirect(node.redirects[i]));
      }
      return base + ' ' + redirectParts.join(' ');
    }
    return base;
  } else if (kind === 'brace-group') {
    const bodyStr = _formatCmdsubNode(node.body, inProcsub);
    let base = '{ ' + bodyStr + '; }';
    if (node.redirects) {
      const redirectParts = [];
      for (let i = 0; i < node.redirects.length; i++) {
        redirectParts.push(_formatRedirect(node.redirects[i]));
      }
      return base + ' ' + redirectParts.join(' ');
    }
    return base;
  }
  // For other node types, return a placeholder
  return '<' + kind + '>';
}

function _formatRedirect(r) {
  if (r.kind === 'heredoc') {
    let op;
    if (r.stripTabs) {
      op = '<<-';
    } else {
      op = '<<';
    }
    return op + r.delimiter;
  }
  let targetVal = r.target.value;
  targetVal = new Word(targetVal)._expandAllAnsiCQuotes(targetVal);
  targetVal = targetVal.replace(/\$"/g, '"');
  return r.op + targetVal;
}

function _normalizeFdRedirects(s) {
  // Basic implementation - just return as-is for now
  return s;
}

// ============================================================================
// Parser Class (Stub - Full implementation would be very long)
// ============================================================================

class Parser {
  constructor(source) {
    this.source = source;
    this.pos = 0;
    this.length = source.length;
    this._pendingHeredocEnd = null;
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
    if (this.atEnd()) {
      return null;
    }
    const ch = this.source[this.pos];
    this.pos += 1;
    return ch;
  }

  skipWhitespace() {
    while (!this.atEnd()) {
      const ch = this.peek();
      if (_isWhitespaceNoNewline(ch)) {
        this.advance();
      } else if (ch === '#') {
        while (!this.atEnd() && this.peek() !== '\n') {
          this.advance();
        }
      } else if (ch === '\\' && this.pos + 1 < this.length && this.source[this.pos + 1] === '\n') {
        this.advance();
        this.advance();
      } else {
        break;
      }
    }
  }

  skipWhitespaceAndNewlines() {
    while (!this.atEnd()) {
      const ch = this.peek();
      if (_isWhitespace(ch)) {
        this.advance();
        if (ch === '\n') {
          if (this._pendingHeredocEnd !== null && this._pendingHeredocEnd > this.pos) {
            this.pos = this._pendingHeredocEnd;
            this._pendingHeredocEnd = null;
          }
        }
      } else if (ch === '#') {
        while (!this.atEnd() && this.peek() !== '\n') {
          this.advance();
        }
      } else if (ch === '\\' && this.pos + 1 < this.length && this.source[this.pos + 1] === '\n') {
        this.advance();
        this.advance();
      } else {
        break;
      }
    }
  }

  peekWord() {
    const savedPos = this.pos;
    this.skipWhitespace();
    if (this.atEnd() || _isMetachar(this.peek())) {
      this.pos = savedPos;
      return null;
    }
    const chars = [];
    while (!this.atEnd() && !_isMetachar(this.peek())) {
      const ch = this.peek();
      if (_isQuote(ch)) {
        break;
      }
      chars.push(this.advance());
    }
    let word;
    if (chars.length > 0) {
      word = chars.join('');
    } else {
      word = null;
    }
    this.pos = savedPos;
    return word;
  }

  consumeWord(expected) {
    const savedPos = this.pos;
    this.skipWhitespace();
    const word = this.peekWord();
    if (word !== expected) {
      this.pos = savedPos;
      return false;
    }
    this.skipWhitespace();
    for (let i = 0; i < expected.length; i++) {
      this.advance();
    }
    return true;
  }

  // -------------------------------------------------------------------------
  // Parameter Expansion Parsing
  // -------------------------------------------------------------------------

  _parseParamExpansion() {
    if (this.atEnd() || this.peek() !== '$') {
      return [null, ''];
    }
    const start = this.pos;
    this.advance(); // consume $
    if (this.atEnd()) {
      this.pos = start;
      return [null, ''];
    }
    const ch = this.peek();
    // Braced expansion ${...}
    if (ch === '{') {
      this.advance(); // consume {
      return this._parseBracedParam(start);
    }
    // Simple expansion $var or $special
    if (_isSpecialParamOrDigit(ch) || ch === '#') {
      this.advance();
      const text = _substring(this.source, start, this.pos);
      return [new ParamExpansion(ch), text];
    }
    // Variable name [a-zA-Z_][a-zA-Z0-9_]*
    if ((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || ch === '_') {
      const nameStart = this.pos;
      while (!this.atEnd()) {
        const c = this.peek();
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c === '_') {
          this.advance();
        } else {
          break;
        }
      }
      const name = _substring(this.source, nameStart, this.pos);
      const text = _substring(this.source, start, this.pos);
      return [new ParamExpansion(name), text];
    }
    // Not a valid expansion, restore position
    this.pos = start;
    return [null, ''];
  }

  _parseBracedParam(start) {
    if (this.atEnd()) {
      this.pos = start;
      return [null, ''];
    }
    let ch = this.peek();
    // ${#param} - length
    if (ch === '#') {
      this.advance();
      const param = this._consumeParamName();
      if (param && !this.atEnd() && this.peek() === '}') {
        this.advance();
        const text = _substring(this.source, start, this.pos);
        return [new ParamLength(param), text];
      }
      this.pos = start;
      return [null, ''];
    }
    // ${!param} - indirect
    if (ch === '!') {
      this.advance();
      const param = this._consumeParamName();
      if (param) {
        while (!this.atEnd() && _isWhitespaceNoNewline(this.peek())) {
          this.advance();
        }
        if (!this.atEnd() && this.peek() === '}') {
          this.advance();
          const text = _substring(this.source, start, this.pos);
          return [new ParamIndirect(param), text];
        }
        // ${!prefix@} and ${!prefix*}
        if (!this.atEnd() && _isAtOrStar(this.peek())) {
          const suffix = this.advance();
          while (!this.atEnd() && _isWhitespaceNoNewline(this.peek())) {
            this.advance();
          }
          if (!this.atEnd() && this.peek() === '}') {
            this.advance();
            const text = _substring(this.source, start, this.pos);
            return [new ParamIndirect(param + suffix), text];
          }
          this.pos = start;
          return [null, ''];
        }
        // Check for operator
        const op = this._consumeParamOperator();
        if (op !== null) {
          const argChars = [];
          let depth = 1;
          while (!this.atEnd() && depth > 0) {
            const c = this.peek();
            if (c === '$' && this.pos + 1 < this.length && this.source[this.pos + 1] === '{') {
              depth += 1;
              argChars.push(this.advance());
              argChars.push(this.advance());
            } else if (c === '}') {
              depth -= 1;
              if (depth > 0) {
                argChars.push(this.advance());
              }
            } else if (c === '\\') {
              argChars.push(this.advance());
              if (!this.atEnd()) {
                argChars.push(this.advance());
              }
            } else {
              argChars.push(this.advance());
            }
          }
          if (depth === 0) {
            this.advance(); // consume final }
            const arg = argChars.join('');
            const text = _substring(this.source, start, this.pos);
            return [new ParamIndirect(param, op, arg), text];
          }
        }
      }
      this.pos = start;
      return [null, ''];
    }
    // ${param} or ${param<op><arg>}
    let param = this._consumeParamName();
    if (!param) {
      // Unknown syntax - consume until matching }
      let depth = 1;
      const contentStart = this.pos;
      while (!this.atEnd() && depth > 0) {
        const c = this.peek();
        if (c === '{') {
          depth += 1;
          this.advance();
        } else if (c === '}') {
          depth -= 1;
          if (depth === 0) {
            break;
          }
          this.advance();
        } else if (c === '\\') {
          this.advance();
          if (!this.atEnd()) {
            this.advance();
          }
        } else {
          this.advance();
        }
      }
      if (depth === 0) {
        const content = _substring(this.source, contentStart, this.pos);
        this.advance(); // consume final }
        const text = _substring(this.source, start, this.pos);
        return [new ParamExpansion(content), text];
      }
      this.pos = start;
      return [null, ''];
    }
    if (this.atEnd()) {
      this.pos = start;
      return [null, ''];
    }
    // Check for closing brace (simple expansion)
    if (this.peek() === '}') {
      this.advance();
      const text = _substring(this.source, start, this.pos);
      return [new ParamExpansion(param), text];
    }
    // Parse operator
    let op = this._consumeParamOperator();
    if (op === null) {
      op = this.advance();
    }
    // Parse argument (everything until closing brace)
    const argChars = [];
    let depth = 1;
    let inSingleQuote = false;
    let inDoubleQuote = false;
    while (!this.atEnd() && depth > 0) {
      const c = this.peek();
      if (c === "'" && !inDoubleQuote) {
        if (inSingleQuote) {
          inSingleQuote = false;
        } else {
          inSingleQuote = true;
        }
        argChars.push(this.advance());
      } else if (c === '"' && !inSingleQuote) {
        inDoubleQuote = !inDoubleQuote;
        argChars.push(this.advance());
      } else if (c === '\\' && !inSingleQuote) {
        if (this.pos + 1 < this.length && this.source[this.pos + 1] === '\n') {
          this.advance();
          this.advance();
        } else {
          argChars.push(this.advance());
          if (!this.atEnd()) {
            argChars.push(this.advance());
          }
        }
      } else if (c === '$' && !inSingleQuote && this.pos + 1 < this.length && this.source[this.pos + 1] === '{') {
        depth += 1;
        argChars.push(this.advance());
        argChars.push(this.advance());
      } else if (c === '$' && !inSingleQuote && this.pos + 1 < this.length && this.source[this.pos + 1] === '(') {
        argChars.push(this.advance());
        argChars.push(this.advance());
        let parenDepth = 1;
        while (!this.atEnd() && parenDepth > 0) {
          const pc = this.peek();
          if (pc === '(') {
            parenDepth += 1;
          } else if (pc === ')') {
            parenDepth -= 1;
          } else if (pc === '\\') {
            argChars.push(this.advance());
            if (!this.atEnd()) {
              argChars.push(this.advance());
            }
            continue;
          }
          argChars.push(this.advance());
        }
      } else if (c === '`' && !inSingleQuote) {
        argChars.push(this.advance());
        while (!this.atEnd() && this.peek() !== '`') {
          const bc = this.peek();
          if (bc === '\\' && this.pos + 1 < this.length) {
            const nextC = this.source[this.pos + 1];
            if (_isEscapeCharInDquote(nextC)) {
              argChars.push(this.advance());
            }
          }
          argChars.push(this.advance());
        }
        if (!this.atEnd()) {
          argChars.push(this.advance());
        }
      } else if (c === '}') {
        if (inSingleQuote) {
          argChars.push(this.advance());
        } else if (inDoubleQuote) {
          if (depth > 1) {
            depth -= 1;
            argChars.push(this.advance());
          } else {
            argChars.push(this.advance());
          }
        } else {
          depth -= 1;
          if (depth > 0) {
            argChars.push(this.advance());
          }
        }
      } else {
        argChars.push(this.advance());
      }
    }
    if (depth !== 0) {
      this.pos = start;
      return [null, ''];
    }
    this.advance(); // consume final }
    const arg = argChars.join('');
    const text = '${' + param + op + arg + '}';
    return [new ParamExpansion(param, op, arg), text];
  }

  _consumeParamName() {
    if (this.atEnd()) {
      return null;
    }
    const ch = this.peek();
    // Special parameters
    if (_isSpecialParam(ch)) {
      this.advance();
      return ch;
    }
    // Digits (positional params)
    if (_isDigit(ch)) {
      const nameChars = [];
      while (!this.atEnd() && _isDigit(this.peek())) {
        nameChars.push(this.advance());
      }
      return nameChars.join('');
    }
    // Variable name
    if ((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || ch === '_') {
      const nameChars = [];
      while (!this.atEnd()) {
        const c = this.peek();
        if ((c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c === '_') {
          nameChars.push(this.advance());
        } else if (c === '[') {
          nameChars.push(this.advance());
          let bracketDepth = 1;
          while (!this.atEnd() && bracketDepth > 0) {
            const sc = this.peek();
            if (sc === '[') {
              bracketDepth += 1;
            } else if (sc === ']') {
              bracketDepth -= 1;
              if (bracketDepth === 0) {
                break;
              }
            }
            nameChars.push(this.advance());
          }
          if (!this.atEnd() && this.peek() === ']') {
            nameChars.push(this.advance());
          }
          break;
        } else {
          break;
        }
      }
      if (nameChars.length > 0) {
        return nameChars.join('');
      }
      return null;
    }
    return null;
  }

  _consumeParamOperator() {
    if (this.atEnd()) {
      return null;
    }
    const ch = this.peek();
    if (ch === ':') {
      this.advance();
      if (this.atEnd()) {
        return ':';
      }
      const nextCh = this.peek();
      if (_isSimpleParamOp(nextCh)) {
        this.advance();
        return ':' + nextCh;
      }
      return ':';
    }
    if (_isSimpleParamOp(ch)) {
      this.advance();
      return ch;
    }
    if (ch === '#') {
      this.advance();
      if (!this.atEnd() && this.peek() === '#') {
        this.advance();
        return '##';
      }
      return '#';
    }
    if (ch === '%') {
      this.advance();
      if (!this.atEnd() && this.peek() === '%') {
        this.advance();
        return '%%';
      }
      return '%';
    }
    if (ch === '/') {
      this.advance();
      if (!this.atEnd()) {
        const nextCh = this.peek();
        if (nextCh === '/') {
          this.advance();
          return '//';
        } else if (nextCh === '#') {
          this.advance();
          return '/#';
        } else if (nextCh === '%') {
          this.advance();
          return '/%';
        }
      }
      return '/';
    }
    if (ch === '^') {
      this.advance();
      if (!this.atEnd() && this.peek() === '^') {
        this.advance();
        return '^^';
      }
      return '^';
    }
    if (ch === ',') {
      this.advance();
      if (!this.atEnd() && this.peek() === ',') {
        this.advance();
        return ',,';
      }
      return ',';
    }
    if (ch === '@') {
      this.advance();
      return '@';
    }
    return null;
  }

  // -------------------------------------------------------------------------
  // Command Substitution Parsing
  // -------------------------------------------------------------------------

  _parseCommandSubstitution() {
    if (this.atEnd() || this.peek() !== '$') {
      return [null, ''];
    }
    if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== '(') {
      return [null, ''];
    }
    const start = this.pos;
    this.advance(); // consume $
    this.advance(); // consume (
    // Find matching ) - track nested parens
    const contentStart = this.pos;
    let depth = 1;
    while (!this.atEnd() && depth > 0) {
      const c = this.peek();
      if (c === '(') {
        depth += 1;
        this.advance();
      } else if (c === ')') {
        depth -= 1;
        if (depth === 0) {
          break;
        }
        this.advance();
      } else if (c === '\\') {
        this.advance();
        if (!this.atEnd()) {
          this.advance();
        }
      } else if (c === '"') {
        this.advance();
        while (!this.atEnd() && this.peek() !== '"') {
          if (this.peek() === '\\' && this.pos + 1 < this.length) {
            this.advance();
          }
          this.advance();
        }
        if (!this.atEnd()) {
          this.advance();
        }
      } else if (c === "'") {
        this.advance();
        while (!this.atEnd() && this.peek() !== "'") {
          this.advance();
        }
        if (!this.atEnd()) {
          this.advance();
        }
      } else {
        this.advance();
      }
    }
    if (depth !== 0) {
      this.pos = start;
      return [null, ''];
    }
    const content = _substring(this.source, contentStart, this.pos);
    this.advance(); // consume )
    const text = _substring(this.source, start, this.pos);
    // Parse the command inside
    const savedPos = this.pos;
    const savedSrc = this.source;
    const savedLen = this.length;
    this.source = content;
    this.pos = 0;
    this.length = content.length;
    const cmd = this.parseList();
    this.source = savedSrc;
    this.pos = savedPos;
    this.length = savedLen;
    return [new CommandSubstitution(cmd), text];
  }

  _parseBacktickSubstitution() {
    if (this.atEnd() || this.peek() !== '`') {
      return [null, ''];
    }
    const start = this.pos;
    this.advance(); // consume opening `
    const contentStart = this.pos;
    while (!this.atEnd() && this.peek() !== '`') {
      const c = this.peek();
      if (c === '\\' && this.pos + 1 < this.length) {
        this.advance();
        this.advance();
      } else {
        this.advance();
      }
    }
    if (this.atEnd()) {
      this.pos = start;
      return [null, ''];
    }
    const content = _substring(this.source, contentStart, this.pos);
    this.advance(); // consume closing `
    const text = _substring(this.source, start, this.pos);
    // Parse the command inside
    const savedPos = this.pos;
    const savedSrc = this.source;
    const savedLen = this.length;
    this.source = content;
    this.pos = 0;
    this.length = content.length;
    const cmd = this.parseList();
    this.source = savedSrc;
    this.pos = savedPos;
    this.length = savedLen;
    return [new CommandSubstitution(cmd), text];
  }

  _parseProcessSubstitution() {
    if (this.atEnd()) {
      return [null, ''];
    }
    const ch = this.peek();
    if (!_isRedirectChar(ch)) {
      return [null, ''];
    }
    if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== '(') {
      return [null, ''];
    }
    const start = this.pos;
    const direction = this.advance(); // < or >
    this.advance(); // consume (
    const contentStart = this.pos;
    let depth = 1;
    while (!this.atEnd() && depth > 0) {
      const c = this.peek();
      if (c === '(') {
        depth += 1;
        this.advance();
      } else if (c === ')') {
        depth -= 1;
        if (depth === 0) {
          break;
        }
        this.advance();
      } else {
        this.advance();
      }
    }
    if (depth !== 0) {
      this.pos = start;
      return [null, ''];
    }
    const content = _substring(this.source, contentStart, this.pos);
    this.advance(); // consume )
    const text = _substring(this.source, start, this.pos);
    // Parse the command inside
    const savedPos = this.pos;
    const savedSrc = this.source;
    const savedLen = this.length;
    this.source = content;
    this.pos = 0;
    this.length = content.length;
    const cmd = this.parseList();
    this.source = savedSrc;
    this.pos = savedPos;
    this.length = savedLen;
    return [new ProcessSubstitution(direction, cmd), text];
  }

  // Stub for remaining methods - to be continued
  parseList() {
    return this._parseListImpl(true);
  }

  _parseListImpl(newlineAsSeparator) {
    if (newlineAsSeparator) {
      this.skipWhitespaceAndNewlines();
    } else {
      this.skipWhitespace();
    }
    const pipeline = this.parsePipeline();
    if (pipeline === null) {
      return null;
    }
    const parts = [pipeline];
    while (true) {
      this.skipWhitespace();
      let hasNewline = false;
      while (!this.atEnd() && this.peek() === '\n') {
        hasNewline = true;
        if (!newlineAsSeparator) {
          break;
        }
        this.advance();
        if (this._pendingHeredocEnd !== null && this._pendingHeredocEnd > this.pos) {
          this.pos = this._pendingHeredocEnd;
          this._pendingHeredocEnd = null;
        }
        this.skipWhitespace();
      }
      if (hasNewline && !newlineAsSeparator) {
        break;
      }
      let op = this.parseListOperator();
      if (op === null && hasNewline) {
        if (!this.atEnd() && !_isRightBracket(this.peek())) {
          op = '\n';
        }
      }
      if (op === null) {
        break;
      }
      if (!(op === ';' && parts.length > 0 && parts[parts.length - 1].kind === 'operator' && parts[parts.length - 1].op === ';')) {
        parts.push(new Operator(op));
      }
      if (op === '&') {
        this.skipWhitespace();
        if (this.atEnd() || _isRightBracket(this.peek())) {
          break;
        }
        if (this.peek() === '\n') {
          if (newlineAsSeparator) {
            this.skipWhitespaceAndNewlines();
            if (this.atEnd() || _isRightBracket(this.peek())) {
              break;
            }
          } else {
            break;
          }
        }
      }
      if (op === ';') {
        this.skipWhitespace();
        const peekCh = this.peek();
        if (this.atEnd() || _isRightBracket(peekCh) || peekCh === '}' || peekCh === ')') {
          break;
        }
        if (peekCh === '\n') {
          continue;
        }
      }
      if (op === '&&' || op === '||') {
        this.skipWhitespaceAndNewlines();
      }
      const nextPipeline = this.parsePipeline();
      if (nextPipeline === null) {
        throw new ParseError('Expected command after ' + op, this.pos);
      }
      parts.push(nextPipeline);
    }
    if (parts.length === 1) {
      return parts[0];
    }
    return new List(parts);
  }

  parseListOperator() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    const ch = this.peek();
    if (ch === '&') {
      if (this.pos + 1 < this.length && this.source[this.pos + 1] === '>') {
        return null;
      }
      this.advance();
      if (!this.atEnd() && this.peek() === '&') {
        this.advance();
        return '&&';
      }
      return '&';
    }
    if (ch === '|') {
      if (this.pos + 1 < this.length && this.source[this.pos + 1] === '|') {
        this.advance();
        this.advance();
        return '||';
      }
      return null;
    }
    if (ch === ';') {
      if (this.pos + 1 < this.length && _isSemicolonOrAmp(this.source[this.pos + 1])) {
        return null;
      }
      this.advance();
      return ';';
    }
    return null;
  }

  parsePipeline() {
    this.skipWhitespace();
    let prefixOrder = null;
    let timePosix = false;
    if (this.peekWord() === 'time') {
      this.consumeWord('time');
      prefixOrder = 'time';
      this.skipWhitespace();
      if (!this.atEnd() && this.peek() === '-') {
        const saved = this.pos;
        this.advance();
        if (!this.atEnd() && this.peek() === 'p') {
          this.advance();
          if (this.atEnd() || _isWhitespace(this.peek())) {
            timePosix = true;
          } else {
            this.pos = saved;
          }
        } else {
          this.pos = saved;
        }
      }
      this.skipWhitespace();
      if (!this.atEnd() && _startsWithAt(this.source, this.pos, '--')) {
        if (this.pos + 2 >= this.length || _isWhitespace(this.source[this.pos + 2])) {
          this.advance();
          this.advance();
          timePosix = true;
          this.skipWhitespace();
        }
      }
      while (this.peekWord() === 'time') {
        this.consumeWord('time');
        this.skipWhitespace();
        if (!this.atEnd() && this.peek() === '-') {
          const saved = this.pos;
          this.advance();
          if (!this.atEnd() && this.peek() === 'p') {
            this.advance();
            if (this.atEnd() || _isWhitespace(this.peek())) {
              timePosix = true;
            } else {
              this.pos = saved;
            }
          } else {
            this.pos = saved;
          }
        }
        this.skipWhitespace();
      }
      if (!this.atEnd() && this.peek() === '!') {
        if (this.pos + 1 >= this.length || _isWhitespace(this.source[this.pos + 1])) {
          this.advance();
          prefixOrder = 'time_negation';
          this.skipWhitespace();
        }
      }
    } else if (!this.atEnd() && this.peek() === '!') {
      if (this.pos + 1 >= this.length || _isWhitespace(this.source[this.pos + 1])) {
        this.advance();
        this.skipWhitespace();
        const inner = this.parsePipeline();
        if (inner !== null && inner.kind === 'negation') {
          if (inner.pipeline !== null) {
            return inner.pipeline;
          }
          return new Command([]);
        }
        return new Negation(inner);
      }
    }
    let result = this._parseSimplePipeline();
    if (prefixOrder === 'time') {
      result = new Time(result, timePosix);
    } else if (prefixOrder === 'negation') {
      result = new Negation(result);
    } else if (prefixOrder === 'time_negation') {
      result = new Time(result, timePosix);
      result = new Negation(result);
    } else if (prefixOrder === 'negation_time') {
      result = new Time(result, timePosix);
      result = new Negation(result);
    } else if (result === null) {
      return null;
    }
    return result;
  }

  _parseSimplePipeline() {
    const cmd = this.parseCompoundCommand();
    if (cmd === null) {
      return null;
    }
    const commands = [cmd];
    while (true) {
      this.skipWhitespace();
      if (this.atEnd() || this.peek() !== '|') {
        break;
      }
      if (this.pos + 1 < this.length && this.source[this.pos + 1] === '|') {
        break;
      }
      this.advance(); // consume |
      let isPipeBoth = false;
      if (!this.atEnd() && this.peek() === '&') {
        this.advance();
        isPipeBoth = true;
      }
      this.skipWhitespaceAndNewlines();
      if (isPipeBoth) {
        commands.push(new PipeBoth());
      }
      const nextCmd = this.parseCompoundCommand();
      if (nextCmd === null) {
        throw new ParseError('Expected command after |', this.pos);
      }
      commands.push(nextCmd);
    }
    if (commands.length === 1) {
      return commands[0];
    }
    return new Pipeline(commands);
  }

  parseCompoundCommand() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    const ch = this.peek();
    if (ch === '(' && this.pos + 1 < this.length && this.source[this.pos + 1] === '(') {
      const result = this.parseArithmeticCommand();
      if (result !== null) {
        return result;
      }
    }
    if (ch === '(') {
      return this.parseSubshell();
    }
    if (ch === '{') {
      const result = this.parseBraceGroup();
      if (result !== null) {
        return result;
      }
    }
    if (ch === '[' && this.pos + 1 < this.length && this.source[this.pos + 1] === '[') {
      return this.parseConditionalExpr();
    }
    const word = this.peekWord();
    if (word === 'if') {
      return this.parseIf();
    }
    if (word === 'while') {
      return this.parseWhile();
    }
    if (word === 'until') {
      return this.parseUntil();
    }
    if (word === 'for') {
      return this.parseFor();
    }
    if (word === 'select') {
      return this.parseSelect();
    }
    if (word === 'case') {
      return this.parseCase();
    }
    if (word === 'function') {
      return this.parseFunction();
    }
    if (word === 'coproc') {
      return this.parseCoproc();
    }
    const func = this.parseFunction();
    if (func !== null) {
      return func;
    }
    return this.parseCommand();
  }

  // Placeholder implementations for compound commands
  parseSubshell() {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== '(') {
      return null;
    }
    this.advance(); // consume (
    const body = this.parseList();
    if (body === null) {
      throw new ParseError('Expected command in subshell', this.pos);
    }
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== ')') {
      throw new ParseError('Expected ) to close subshell', this.pos);
    }
    this.advance(); // consume )
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    if (redirects.length > 0) {
      return new Subshell(body, redirects);
    }
    return new Subshell(body, null);
  }

  parseBraceGroup() {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== '{') {
      return null;
    }
    if (this.pos + 1 < this.length && !_isWhitespace(this.source[this.pos + 1])) {
      return null;
    }
    this.advance(); // consume {
    this.skipWhitespaceAndNewlines();
    const body = this.parseList();
    if (body === null) {
      throw new ParseError('Expected command in brace group', this.pos);
    }
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== '}') {
      throw new ParseError('Expected } to close brace group', this.pos);
    }
    this.advance(); // consume }
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new BraceGroup(body, redirArg);
  }

  parseArithmeticCommand() {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== '(') {
      return null;
    }
    if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== '(') {
      return null;
    }
    const start = this.pos;
    this.advance(); // (
    this.advance(); // (
    const contentStart = this.pos;
    let depth = 1;
    while (!this.atEnd() && depth > 0) {
      const c = this.peek();
      if (c === '(') {
        depth += 1;
        this.advance();
      } else if (c === ')') {
        if (depth === 1 && this.pos + 1 < this.length && this.source[this.pos + 1] === ')') {
          break;
        }
        depth -= 1;
        this.advance();
      } else {
        this.advance();
      }
    }
    if (this.atEnd() || depth !== 1) {
      this.pos = start;
      return null;
    }
    const content = _substring(this.source, contentStart, this.pos);
    this.advance(); // )
    this.advance(); // )
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new ArithmeticCommand(content, redirArg);
  }

  parseConditionalExpr() {
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== '[') {
      return null;
    }
    if (this.pos + 1 >= this.length || this.source[this.pos + 1] !== '[') {
      return null;
    }
    this.advance(); // [
    this.advance(); // [
    this.skipWhitespace();
    const expr = this._parseCondExpr();
    this.skipWhitespaceAndNewlines();
    if (this.atEnd() || this.peek() !== ']') {
      throw new ParseError("Expected ]] to close conditional", this.pos);
    }
    this.advance(); // ]
    if (this.atEnd() || this.peek() !== ']') {
      throw new ParseError("Expected ]] to close conditional", this.pos);
    }
    this.advance(); // ]
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new ConditionalExpr(expr, redirArg);
  }

  _parseCondExpr() {
    return this._parseCondOr();
  }

  _parseCondOr() {
    let left = this._parseCondAnd();
    while (true) {
      this.skipWhitespace();
      if (this.atEnd()) {
        break;
      }
      if (this.peek() === '|' && this.pos + 1 < this.length && this.source[this.pos + 1] === '|') {
        this.advance();
        this.advance();
        this.skipWhitespace();
        const right = this._parseCondAnd();
        left = new CondOr(left, right);
      } else {
        break;
      }
    }
    return left;
  }

  _parseCondAnd() {
    let left = this._parseCondNot();
    while (true) {
      this.skipWhitespace();
      if (this.atEnd()) {
        break;
      }
      if (this.peek() === '&' && this.pos + 1 < this.length && this.source[this.pos + 1] === '&') {
        this.advance();
        this.advance();
        this.skipWhitespace();
        const right = this._parseCondNot();
        left = new CondAnd(left, right);
      } else {
        break;
      }
    }
    return left;
  }

  _parseCondNot() {
    this.skipWhitespace();
    if (!this.atEnd() && this.peek() === '!') {
      this.advance();
      this.skipWhitespace();
      const expr = this._parseCondNot();
      return new CondNot(expr);
    }
    return this._parseCondPrimary();
  }

  _parseCondPrimary() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    // Parenthesized expression
    if (this.peek() === '(') {
      this.advance();
      this.skipWhitespace();
      const expr = this._parseCondExpr();
      this.skipWhitespace();
      if (!this.atEnd() && this.peek() === ')') {
        this.advance();
      }
      return expr;
    }
    // Check for unary operator
    const word = this._parseCondWord();
    if (word === null) {
      return null;
    }
    if (COND_UNARY_OPS.has(word.value)) {
      this.skipWhitespace();
      const arg = this._parseCondWord();
      return new UnaryTest(word.value, arg);
    }
    // Check for binary operator
    this.skipWhitespace();
    const opWord = this._parseCondWord();
    if (opWord !== null && COND_BINARY_OPS.has(opWord.value)) {
      this.skipWhitespace();
      const right = this._parseCondWord();
      return new BinaryTest(word, opWord.value, right);
    }
    // Single word (true if non-empty)
    if (opWord !== null) {
      // Put opWord back by reparsing
      this.skipWhitespace();
      // Check if there's a binary op after
      const savedPos = this.pos;
      const potentialOp = this._parseCondWord();
      if (potentialOp !== null && COND_BINARY_OPS.has(potentialOp.value)) {
        this.skipWhitespace();
        const right = this._parseCondWord();
        return new BinaryTest(word, potentialOp.value, right);
      }
      this.pos = savedPos;
    }
    return new UnaryTest('-n', word);
  }

  _parseCondWord() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    const ch = this.peek();
    if (ch === ']' || ch === ')' || ch === '&' || ch === '|') {
      return null;
    }
    return this.parseWord();
  }

  parseIf() {
    this.skipWhitespace();
    if (this.peekWord() !== 'if') {
      return null;
    }
    this.consumeWord('if');
    const condition = this.parseListUntil(new Set(['then']));
    if (condition === null) {
      throw new ParseError("Expected condition after 'if'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('then')) {
      throw new ParseError("Expected 'then' after if condition", this.pos);
    }
    const thenBody = this.parseListUntil(new Set(['elif', 'else', 'fi']));
    if (thenBody === null) {
      throw new ParseError("Expected commands after 'then'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    let nextWord = this.peekWord();
    let elseBody = null;
    if (nextWord === 'elif') {
      elseBody = this._parseElifChain();
    } else if (nextWord === 'else') {
      this.consumeWord('else');
      elseBody = this.parseListUntil(new Set(['fi']));
      if (elseBody === null) {
        throw new ParseError("Expected commands after 'else'", this.pos);
      }
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('fi')) {
      throw new ParseError("Expected 'fi' to close if statement", this.pos);
    }
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new If(condition, thenBody, elseBody, redirArg);
  }

  _parseElifChain() {
    this.consumeWord('elif');
    const condition = this.parseListUntil(new Set(['then']));
    if (condition === null) {
      throw new ParseError("Expected condition after 'elif'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('then')) {
      throw new ParseError("Expected 'then' after elif condition", this.pos);
    }
    const thenBody = this.parseListUntil(new Set(['elif', 'else', 'fi']));
    if (thenBody === null) {
      throw new ParseError("Expected commands after 'then'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    const nextWord = this.peekWord();
    let elseBody = null;
    if (nextWord === 'elif') {
      elseBody = this._parseElifChain();
    } else if (nextWord === 'else') {
      this.consumeWord('else');
      elseBody = this.parseListUntil(new Set(['fi']));
      if (elseBody === null) {
        throw new ParseError("Expected commands after 'else'", this.pos);
      }
    }
    return new If(condition, thenBody, elseBody);
  }

  parseWhile() {
    this.skipWhitespace();
    if (this.peekWord() !== 'while') {
      return null;
    }
    this.consumeWord('while');
    const condition = this.parseListUntil(new Set(['do']));
    if (condition === null) {
      throw new ParseError("Expected condition after 'while'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('do')) {
      throw new ParseError("Expected 'do' after while condition", this.pos);
    }
    const body = this.parseListUntil(new Set(['done']));
    if (body === null) {
      throw new ParseError("Expected commands after 'do'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('done')) {
      throw new ParseError("Expected 'done' to close while loop", this.pos);
    }
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new While(condition, body, redirArg);
  }

  parseUntil() {
    this.skipWhitespace();
    if (this.peekWord() !== 'until') {
      return null;
    }
    this.consumeWord('until');
    const condition = this.parseListUntil(new Set(['do']));
    if (condition === null) {
      throw new ParseError("Expected condition after 'until'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('do')) {
      throw new ParseError("Expected 'do' after until condition", this.pos);
    }
    const body = this.parseListUntil(new Set(['done']));
    if (body === null) {
      throw new ParseError("Expected commands after 'do'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('done')) {
      throw new ParseError("Expected 'done' to close until loop", this.pos);
    }
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new Until(condition, body, redirArg);
  }

  parseFor() {
    this.skipWhitespace();
    if (this.peekWord() !== 'for') {
      return null;
    }
    this.consumeWord('for');
    this.skipWhitespace();
    // Check for C-style for loop: for ((init; cond; incr))
    if (this.peek() === '(' && this.pos + 1 < this.length && this.source[this.pos + 1] === '(') {
      return this._parseForArith();
    }
    const varName = this.peekWord();
    if (varName === null) {
      throw new ParseError("Expected variable name after 'for'", this.pos);
    }
    this.consumeWord(varName);
    this.skipWhitespace();
    if (this.peek() === ';') {
      this.advance();
    }
    this.skipWhitespaceAndNewlines();
    let words = null;
    if (this.peekWord() === 'in') {
      this.consumeWord('in');
      this.skipWhitespaceAndNewlines();
      words = [];
      while (true) {
        this.skipWhitespace();
        if (this.atEnd()) {
          break;
        }
        if (_isSemicolonOrNewline(this.peek())) {
          if (this.peek() === ';') {
            this.advance();
          }
          break;
        }
        if (this.peekWord() === 'do') {
          break;
        }
        const word = this.parseWord();
        if (word === null) {
          break;
        }
        words.push(word);
      }
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('do')) {
      throw new ParseError("Expected 'do' in for loop", this.pos);
    }
    const body = this.parseListUntil(new Set(['done']));
    if (body === null) {
      throw new ParseError("Expected commands after 'do'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('done')) {
      throw new ParseError("Expected 'done' to close for loop", this.pos);
    }
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new For(varName, words, body, redirArg);
  }

  _parseForArith() {
    this.advance(); // (
    this.advance(); // (
    const parts = [];
    let current = [];
    let parenDepth = 0;
    while (!this.atEnd()) {
      const ch = this.peek();
      if (ch === '(') {
        parenDepth += 1;
        current.push(this.advance());
      } else if (ch === ')') {
        if (parenDepth > 0) {
          parenDepth -= 1;
          current.push(this.advance());
        } else {
          if (this.pos + 1 < this.length && this.source[this.pos + 1] === ')') {
            parts.push(current.join('').trim());
            this.advance(); // )
            this.advance(); // )
            break;
          }
          current.push(this.advance());
        }
      } else if (ch === ';' && parenDepth === 0) {
        parts.push(current.join('').trim());
        current = [];
        this.advance();
      } else {
        current.push(this.advance());
      }
    }
    if (parts.length !== 3) {
      throw new ParseError("Expected three expressions in for ((;;))", this.pos);
    }
    const init = parts[0];
    const cond = parts[1];
    const incr = parts[2];
    this.skipWhitespace();
    if (!this.atEnd() && this.peek() === ';') {
      this.advance();
    }
    this.skipWhitespaceAndNewlines();
    let body;
    if (this.peek() === '{') {
      const brace = this.parseBraceGroup();
      if (brace === null) {
        throw new ParseError("Expected brace group body in for loop", this.pos);
      }
      body = brace.body;
    } else if (this.consumeWord('do')) {
      body = this.parseListUntil(new Set(['done']));
      if (body === null) {
        throw new ParseError("Expected commands after 'do'", this.pos);
      }
      this.skipWhitespaceAndNewlines();
      if (!this.consumeWord('done')) {
        throw new ParseError("Expected 'done' to close for loop", this.pos);
      }
    } else {
      throw new ParseError("Expected 'do' or '{' in for loop", this.pos);
    }
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new ForArith(init, cond, incr, body, redirArg);
  }

  parseSelect() {
    this.skipWhitespace();
    if (this.peekWord() !== 'select') {
      return null;
    }
    this.consumeWord('select');
    this.skipWhitespace();
    const varName = this.peekWord();
    if (varName === null) {
      throw new ParseError("Expected variable name after 'select'", this.pos);
    }
    this.consumeWord(varName);
    this.skipWhitespace();
    if (this.peek() === ';') {
      this.advance();
    }
    this.skipWhitespaceAndNewlines();
    let words = null;
    if (this.peekWord() === 'in') {
      this.consumeWord('in');
      this.skipWhitespaceAndNewlines();
      words = [];
      while (true) {
        this.skipWhitespace();
        if (this.atEnd()) {
          break;
        }
        if (_isSemicolonNewlineBrace(this.peek())) {
          if (this.peek() === ';') {
            this.advance();
          }
          break;
        }
        if (this.peekWord() === 'do') {
          break;
        }
        const word = this.parseWord();
        if (word === null) {
          break;
        }
        words.push(word);
      }
    }
    this.skipWhitespaceAndNewlines();
    let body;
    if (this.peek() === '{') {
      const brace = this.parseBraceGroup();
      if (brace === null) {
        throw new ParseError("Expected brace group body in select", this.pos);
      }
      body = brace.body;
    } else if (this.consumeWord('do')) {
      body = this.parseListUntil(new Set(['done']));
      if (body === null) {
        throw new ParseError("Expected commands after 'do'", this.pos);
      }
      this.skipWhitespaceAndNewlines();
      if (!this.consumeWord('done')) {
        throw new ParseError("Expected 'done' to close select", this.pos);
      }
    } else {
      throw new ParseError("Expected 'do' or '{' in select", this.pos);
    }
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new Select(varName, words, body, redirArg);
  }

  parseCase() {
    this.skipWhitespace();
    if (this.peekWord() !== 'case') {
      return null;
    }
    this.consumeWord('case');
    this.skipWhitespace();
    const word = this.parseWord();
    if (word === null) {
      throw new ParseError("Expected word after 'case'", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('in')) {
      throw new ParseError("Expected 'in' after case word", this.pos);
    }
    this.skipWhitespaceAndNewlines();
    const patterns = [];
    while (true) {
      this.skipWhitespaceAndNewlines();
      if (this.peekWord() === 'esac') {
        break;
      }
      // Skip optional leading (
      this.skipWhitespaceAndNewlines();
      if (!this.atEnd() && this.peek() === '(') {
        this.advance();
        this.skipWhitespaceAndNewlines();
      }
      // Parse pattern
      const patternChars = [];
      while (!this.atEnd()) {
        const ch = this.peek();
        if (ch === ')') {
          this.advance();
          break;
        } else if (ch === '\\') {
          patternChars.push(this.advance());
          if (!this.atEnd()) {
            patternChars.push(this.advance());
          }
        } else if (ch === "'" || ch === '"') {
          patternChars.push(this.advance());
          while (!this.atEnd() && this.peek() !== ch) {
            patternChars.push(this.advance());
          }
          if (!this.atEnd()) {
            patternChars.push(this.advance());
          }
        } else if (_isWhitespace(ch)) {
          this.advance();
        } else {
          patternChars.push(this.advance());
        }
      }
      const pattern = patternChars.join('');
      if (!pattern) {
        throw new ParseError("Expected pattern in case statement", this.pos);
      }
      this.skipWhitespace();
      let body = null;
      const isEmptyBody = this._isCaseTerminator();
      if (!isEmptyBody) {
        this.skipWhitespaceAndNewlines();
        if (!this.atEnd() && this.peekWord() !== 'esac') {
          const isAtTerminator = this._isCaseTerminator();
          if (!isAtTerminator) {
            body = this.parseListUntil(new Set(['esac']));
            this.skipWhitespace();
          }
        }
      }
      const terminator = this._consumeCaseTerminator();
      this.skipWhitespaceAndNewlines();
      patterns.push(new CasePattern(pattern, body, terminator));
    }
    this.skipWhitespaceAndNewlines();
    if (!this.consumeWord('esac')) {
      throw new ParseError("Expected 'esac' to close case statement", this.pos);
    }
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      const redirect = this.parseRedirect();
      if (redirect === null) {
        break;
      }
      redirects.push(redirect);
    }
    let redirArg = null;
    if (redirects.length > 0) {
      redirArg = redirects;
    }
    return new Case(word, patterns, redirArg);
  }

  _isCaseTerminator() {
    if (this.atEnd() || this.peek() !== ';') {
      return false;
    }
    if (this.pos + 1 >= this.length) {
      return false;
    }
    const nextCh = this.source[this.pos + 1];
    return _isSemicolonOrAmp(nextCh);
  }

  _consumeCaseTerminator() {
    if (this.atEnd() || this.peek() !== ';') {
      return ';;';
    }
    this.advance(); // ;
    if (this.atEnd()) {
      return ';;';
    }
    const ch = this.peek();
    if (ch === ';') {
      this.advance();
      if (!this.atEnd() && this.peek() === '&') {
        this.advance();
        return ';;&';
      }
      return ';;';
    } else if (ch === '&') {
      this.advance();
      return ';&';
    }
    return ';;';
  }

  parseFunction() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    const savedPos = this.pos;
    if (this.peekWord() === 'function') {
      this.consumeWord('function');
      this.skipWhitespace();
      const name = this.peekWord();
      if (name === null) {
        this.pos = savedPos;
        return null;
      }
      this.consumeWord(name);
      this.skipWhitespace();
      if (!this.atEnd() && this.peek() === '(') {
        if (this.pos + 1 < this.length && this.source[this.pos + 1] === ')') {
          this.advance();
          this.advance();
        }
      }
      this.skipWhitespaceAndNewlines();
      const body = this._parseCompoundCommand();
      if (body === null) {
        throw new ParseError("Expected function body", this.pos);
      }
      return new Function(name, body);
    }
    const name = this.peekWord();
    if (name === null || RESERVED_WORDS.has(name)) {
      return null;
    }
    if (name.indexOf('=') !== -1) {
      return null;
    }
    this.skipWhitespace();
    const nameStart = this.pos;
    while (!this.atEnd() && !_isMetachar(this.peek()) && !_isQuote(this.peek()) && !_isParen(this.peek())) {
      this.advance();
    }
    const funcName = _substring(this.source, nameStart, this.pos);
    if (!funcName) {
      this.pos = savedPos;
      return null;
    }
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== '(') {
      this.pos = savedPos;
      return null;
    }
    this.advance(); // (
    this.skipWhitespace();
    if (this.atEnd() || this.peek() !== ')') {
      this.pos = savedPos;
      return null;
    }
    this.advance(); // )
    this.skipWhitespaceAndNewlines();
    const body = this._parseCompoundCommand();
    if (body === null) {
      throw new ParseError("Expected function body", this.pos);
    }
    return new Function(funcName, body);
  }

  _parseCompoundCommand() {
    let result = this.parseBraceGroup();
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

  parseCoproc() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    if (this.peekWord() !== 'coproc') {
      return null;
    }
    this.consumeWord('coproc');
    this.skipWhitespace();
    let name = null;
    let ch = null;
    if (!this.atEnd()) {
      ch = this.peek();
    }
    if (ch === '{') {
      const body = this.parseBraceGroup();
      if (body !== null) {
        return new Coproc(body, name);
      }
    }
    if (ch === '(') {
      if (this.pos + 1 < this.length && this.source[this.pos + 1] === '(') {
        const body = this.parseArithmeticCommand();
        if (body !== null) {
          return new Coproc(body, name);
        }
      }
      const body = this.parseSubshell();
      if (body !== null) {
        return new Coproc(body, name);
      }
    }
    const nextWord = this.peekWord();
    if (COMPOUND_KEYWORDS.has(nextWord)) {
      const body = this.parseCompoundCommand();
      if (body !== null) {
        return new Coproc(body, name);
      }
    }
    const wordStart = this.pos;
    const potentialName = this.peekWord();
    if (potentialName) {
      while (!this.atEnd() && !_isMetachar(this.peek()) && !_isQuote(this.peek())) {
        this.advance();
      }
      this.skipWhitespace();
      ch = null;
      if (!this.atEnd()) {
        ch = this.peek();
      }
      const nextW = this.peekWord();
      if (ch === '{') {
        name = potentialName;
        const body = this.parseBraceGroup();
        if (body !== null) {
          return new Coproc(body, name);
        }
      } else if (ch === '(') {
        name = potentialName;
        if (this.pos + 1 < this.length && this.source[this.pos + 1] === '(') {
          const body = this.parseArithmeticCommand();
          if (body !== null) {
            return new Coproc(body, name);
          }
        } else {
          const body = this.parseSubshell();
          if (body !== null) {
            return new Coproc(body, name);
          }
        }
      } else if (COMPOUND_KEYWORDS.has(nextW)) {
        name = potentialName;
        const body = this.parseCompoundCommand();
        if (body !== null) {
          return new Coproc(body, name);
        }
      }
      this.pos = wordStart;
    }
    const body = this.parseCommand();
    if (body !== null) {
      return new Coproc(body, name);
    }
    throw new ParseError("Expected command after coproc", this.pos);
  }

  parseListUntil(stopWords) {
    this.skipWhitespaceAndNewlines();
    if (stopWords.has(this.peekWord())) {
      return null;
    }
    const pipeline = this.parsePipeline();
    if (pipeline === null) {
      return null;
    }
    const parts = [pipeline];
    while (true) {
      this.skipWhitespace();
      let hasNewline = false;
      while (!this.atEnd() && this.peek() === '\n') {
        hasNewline = true;
        this.advance();
        if (this._pendingHeredocEnd !== null && this._pendingHeredocEnd > this.pos) {
          this.pos = this._pendingHeredocEnd;
          this._pendingHeredocEnd = null;
        }
        this.skipWhitespace();
      }
      let op = this.parseListOperator();
      if (op === null && hasNewline) {
        if (!this.atEnd() && !stopWords.has(this.peekWord()) && !_isRightBracket(this.peek())) {
          op = '\n';
        }
      }
      if (op === null) {
        break;
      }
      if (op === '&') {
        parts.push(new Operator(op));
        this.skipWhitespaceAndNewlines();
        if (this.atEnd() || stopWords.has(this.peekWord()) || _isNewlineOrRightBracket(this.peek())) {
          break;
        }
      }
      if (op === ';') {
        this.skipWhitespaceAndNewlines();
        const atCaseTerminator = this.peek() === ';' && this.pos + 1 < this.length && _isSemicolonOrAmp(this.source[this.pos + 1]);
        if (this.atEnd() || stopWords.has(this.peekWord()) || _isNewlineOrRightBracket(this.peek()) || atCaseTerminator) {
          break;
        }
        parts.push(new Operator(op));
      } else if (op !== '&') {
        parts.push(new Operator(op));
      }
      this.skipWhitespaceAndNewlines();
      if (stopWords.has(this.peekWord())) {
        break;
      }
      if (this.peek() === ';' && this.pos + 1 < this.length && _isSemicolonOrAmp(this.source[this.pos + 1])) {
        break;
      }
      const nextPipeline = this.parsePipeline();
      if (nextPipeline === null) {
        throw new ParseError('Expected command after ' + op, this.pos);
      }
      parts.push(nextPipeline);
    }
    if (parts.length === 1) {
      return parts[0];
    }
    return new List(parts);
  }

  parseCommand() {
    const words = [];
    const redirects = [];
    while (true) {
      this.skipWhitespace();
      if (this.atEnd()) {
        break;
      }
      const ch = this.peek();
      if (_isListTerminator(ch)) {
        break;
      }
      if (ch === '&' && !(this.pos + 1 < this.length && this.source[this.pos + 1] === '>')) {
        break;
      }
      if (this.peek() === '}' && words.length === 0) {
        const nextPos = this.pos + 1;
        if (nextPos >= this.length || _isWordEndContext(this.source[nextPos])) {
          break;
        }
      }
      const redirect = this.parseRedirect();
      if (redirect !== null) {
        redirects.push(redirect);
        continue;
      }
      let allAssignments = true;
      for (let i = 0; i < words.length; i++) {
        if (!this._isAssignmentWord(words[i])) {
          allAssignments = false;
          break;
        }
      }
      const word = this.parseWord(words.length === 0 || allAssignments);
      if (word === null) {
        break;
      }
      words.push(word);
    }
    if (words.length === 0 && redirects.length === 0) {
      return null;
    }
    return new Command(words, redirects);
  }

  _isAssignmentWord(word) {
    const val = word.value;
    const eqIdx = val.indexOf('=');
    if (eqIdx === -1) {
      return false;
    }
    const name = val.slice(0, eqIdx);
    if (name.length === 0) {
      return false;
    }
    const firstCh = name[0];
    if (!((firstCh >= 'a' && firstCh <= 'z') || (firstCh >= 'A' && firstCh <= 'Z') || firstCh === '_')) {
      return false;
    }
    return true;
  }

  parseRedirect() {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    const start = this.pos;
    let fd = null;
    let varfd = null;
    // Check for variable fd {varname}
    if (this.peek() === '{') {
      const saved = this.pos;
      this.advance();
      const varnameChars = [];
      while (!this.atEnd() && this.peek() !== '}' && !_isRedirectChar(this.peek())) {
        const ch = this.peek();
        if ((ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9') || ch === '_' || ch === '[' || ch === ']') {
          varnameChars.push(this.advance());
        } else {
          break;
        }
      }
      if (!this.atEnd() && this.peek() === '}' && varnameChars.length > 0) {
        this.advance();
        varfd = varnameChars.join('');
      } else {
        this.pos = saved;
      }
    }
    // Check for optional fd number
    if (varfd === null && this.peek() && _isDigit(this.peek())) {
      const fdChars = [];
      while (!this.atEnd() && _isDigit(this.peek())) {
        fdChars.push(this.advance());
      }
      fd = parseInt(fdChars.join(''), 10);
    }
    const ch = this.peek();
    // Handle &> and &>>
    if (ch === '&' && this.pos + 1 < this.length && this.source[this.pos + 1] === '>') {
      if (fd !== null) {
        this.pos = start;
        return null;
      }
      this.advance();
      this.advance();
      let op;
      if (!this.atEnd() && this.peek() === '>') {
        this.advance();
        op = '&>>';
      } else {
        op = '&>';
      }
      this.skipWhitespace();
      const target = this.parseWord();
      if (target === null) {
        throw new ParseError('Expected target for redirect ' + op, this.pos);
      }
      return new Redirect(op, target);
    }
    if (ch === null || !_isRedirectChar(ch)) {
      this.pos = start;
      return null;
    }
    // Check for process substitution
    if (fd === null && this.pos + 1 < this.length && this.source[this.pos + 1] === '(') {
      this.pos = start;
      return null;
    }
    let op = this.advance();
    // Check for multi-char operators
    if (!this.atEnd()) {
      const nextCh = this.peek();
      if (op === '>' && nextCh === '>') {
        this.advance();
        op = '>>';
      } else if (op === '<' && nextCh === '<') {
        this.advance();
        if (!this.atEnd() && this.peek() === '<') {
          this.advance();
          op = '<<<';
        } else if (!this.atEnd() && this.peek() === '-') {
          this.advance();
          op = '<<';
          // strip tabs flag handled in heredoc parsing
        } else {
          op = '<<';
        }
      } else if (op === '<' && nextCh === '>') {
        this.advance();
        op = '<>';
      } else if (op === '>' && nextCh === '|') {
        this.advance();
        op = '>|';
      } else if (fd === null && varfd === null && op === '>' && nextCh === '&') {
        if (this.pos + 1 >= this.length || !_isDigitOrDash(this.source[this.pos + 1])) {
          this.advance();
          op = '>&';
        }
      } else if (fd === null && varfd === null && op === '<' && nextCh === '&') {
        if (this.pos + 1 >= this.length || !_isDigitOrDash(this.source[this.pos + 1])) {
          this.advance();
          op = '<&';
        }
      }
    }
    // Handle heredoc (simplified - just parse delimiter and return)
    if (op === '<<') {
      // For now, just get the delimiter word and return a HereDoc stub
      this.skipWhitespace();
      const delimChars = [];
      while (!this.atEnd() && !_isMetachar(this.peek())) {
        const c = this.peek();
        if (c === '"' || c === "'") {
          this.advance();
          while (!this.atEnd() && this.peek() !== c) {
            delimChars.push(this.advance());
          }
          if (!this.atEnd()) {
            this.advance();
          }
        } else if (c === '\\') {
          this.advance();
          if (!this.atEnd()) {
            delimChars.push(this.advance());
          }
        } else {
          delimChars.push(this.advance());
        }
      }
      const delimiter = delimChars.join('');
      return new HereDoc(delimiter, '', false, false, fd);
    }
    // Combine fd or varfd with operator
    if (varfd !== null) {
      op = '{' + varfd + '}' + op;
    } else if (fd !== null) {
      op = String(fd) + op;
    }
    this.skipWhitespace();
    // Handle fd duplication targets like &1, &2, &-
    if (!this.atEnd() && this.peek() === '&') {
      this.advance();
      if (!this.atEnd() && (_isDigit(this.peek()) || this.peek() === '-')) {
        const fdChars = [];
        while (!this.atEnd() && _isDigit(this.peek())) {
          fdChars.push(this.advance());
        }
        let fdTarget;
        if (fdChars.length > 0) {
          fdTarget = fdChars.join('');
        } else {
          fdTarget = '';
        }
        if (!this.atEnd() && this.peek() === '-') {
          fdTarget += this.advance();
        }
        const target = new Word('&' + fdTarget);
        return new Redirect(op, target);
      } else {
        const innerWord = this.parseWord();
        if (innerWord !== null) {
          const target = new Word('&' + innerWord.value);
          target.parts = innerWord.parts;
          return new Redirect(op, target);
        }
        throw new ParseError('Expected target for redirect ' + op, this.pos);
      }
    }
    const target = this.parseWord();
    if (target === null) {
      throw new ParseError('Expected target for redirect ' + op, this.pos);
    }
    return new Redirect(op, target);
  }

  parseWord(atCommandStart = false) {
    this.skipWhitespace();
    if (this.atEnd()) {
      return null;
    }
    let ch = this.peek();
    // Check for metacharacters that end words
    if (_isMetachar(ch)) {
      return null;
    }
    const chars = [];
    const parts = [];
    while (!this.atEnd()) {
      ch = this.peek();
      // End of word
      if (_isMetachar(ch)) {
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
          throw new ParseError('Unterminated single quote', this.pos);
        }
        chars.push(this.advance());
        continue;
      }
      // Double-quoted string
      if (ch === '"') {
        this.advance();
        chars.push('"');
        while (!this.atEnd() && this.peek() !== '"') {
          const c = this.peek();
          if (c === '\\' && this.pos + 1 < this.length) {
            const nextC = this.source[this.pos + 1];
            if (nextC === '\n') {
              this.advance();
              this.advance();
            } else {
              chars.push(this.advance());
              chars.push(this.advance());
            }
          } else if (c === '$') {
            if (this.pos + 2 < this.length && this.source[this.pos + 1] === '(' && this.source[this.pos + 2] === '(') {
              const arithResult = this._parseArithmeticExpansion();
              if (arithResult[0]) {
                parts.push(arithResult[0]);
                chars.push(arithResult[1]);
              } else {
                const cmdsubResult = this._parseCommandSubstitution();
                if (cmdsubResult[0]) {
                  parts.push(cmdsubResult[0]);
                  chars.push(cmdsubResult[1]);
                } else {
                  chars.push(this.advance());
                }
              }
            } else if (this.pos + 1 < this.length && this.source[this.pos + 1] === '(') {
              const cmdsubResult = this._parseCommandSubstitution();
              if (cmdsubResult[0]) {
                parts.push(cmdsubResult[0]);
                chars.push(cmdsubResult[1]);
              } else {
                chars.push(this.advance());
              }
            } else {
              const paramResult = this._parseParamExpansion();
              if (paramResult[0]) {
                parts.push(paramResult[0]);
                chars.push(paramResult[1]);
              } else {
                chars.push(this.advance());
              }
            }
          } else if (c === '`') {
            const cmdsubResult = this._parseBacktickSubstitution();
            if (cmdsubResult[0]) {
              parts.push(cmdsubResult[0]);
              chars.push(cmdsubResult[1]);
            } else {
              chars.push(this.advance());
            }
          } else {
            chars.push(this.advance());
          }
        }
        if (this.atEnd()) {
          throw new ParseError('Unterminated double quote', this.pos);
        }
        chars.push(this.advance());
        continue;
      }
      // Escape
      if (ch === '\\' && this.pos + 1 < this.length) {
        const nextCh = this.source[this.pos + 1];
        if (nextCh === '\n') {
          this.advance();
          this.advance();
          continue;
        }
        chars.push(this.advance());
        chars.push(this.advance());
        continue;
      }
      // Arithmetic expansion $((...))
      if (ch === '$' && this.pos + 2 < this.length && this.source[this.pos + 1] === '(' && this.source[this.pos + 2] === '(') {
        const arithResult = this._parseArithmeticExpansion();
        if (arithResult[0]) {
          parts.push(arithResult[0]);
          chars.push(arithResult[1]);
        } else {
          const cmdsubResult = this._parseCommandSubstitution();
          if (cmdsubResult[0]) {
            parts.push(cmdsubResult[0]);
            chars.push(cmdsubResult[1]);
          } else {
            chars.push(this.advance());
          }
        }
        continue;
      }
      // Command substitution $(...)
      if (ch === '$' && this.pos + 1 < this.length && this.source[this.pos + 1] === '(') {
        const cmdsubResult = this._parseCommandSubstitution();
        if (cmdsubResult[0]) {
          parts.push(cmdsubResult[0]);
          chars.push(cmdsubResult[1]);
        } else {
          chars.push(this.advance());
        }
        continue;
      }
      // Parameter expansion $var or ${...}
      if (ch === '$') {
        const paramResult = this._parseParamExpansion();
        if (paramResult[0]) {
          parts.push(paramResult[0]);
          chars.push(paramResult[1]);
        } else {
          chars.push(this.advance());
        }
        continue;
      }
      // Backtick command substitution
      if (ch === '`') {
        const cmdsubResult = this._parseBacktickSubstitution();
        if (cmdsubResult[0]) {
          parts.push(cmdsubResult[0]);
          chars.push(cmdsubResult[1]);
        } else {
          chars.push(this.advance());
        }
        continue;
      }
      // Process substitution <(...) or >(...)
      if (_isRedirectChar(ch) && this.pos + 1 < this.length && this.source[this.pos + 1] === '(') {
        const procsubResult = this._parseProcessSubstitution();
        if (procsubResult[0]) {
          parts.push(procsubResult[0]);
          chars.push(procsubResult[1]);
        } else {
          chars.push(this.advance());
        }
        continue;
      }
      // Regular character
      chars.push(this.advance());
    }
    if (chars.length === 0) {
      return null;
    }
    let partsArg = null;
    if (parts.length > 0) {
      partsArg = parts;
    }
    return new Word(chars.join(''), partsArg);
  }

  _parseArithmeticExpansion() {
    if (this.atEnd() || this.peek() !== '$') {
      return [null, ''];
    }
    if (this.pos + 2 >= this.length || this.source[this.pos + 1] !== '(' || this.source[this.pos + 2] !== '(') {
      return [null, ''];
    }
    const start = this.pos;
    this.advance(); // $
    this.advance(); // (
    this.advance(); // (
    const contentStart = this.pos;
    let depth = 1;
    while (!this.atEnd() && depth > 0) {
      const c = this.peek();
      if (c === '(') {
        depth += 1;
        this.advance();
      } else if (c === ')') {
        if (depth === 1 && this.pos + 1 < this.length && this.source[this.pos + 1] === ')') {
          break;
        }
        depth -= 1;
        this.advance();
      } else {
        this.advance();
      }
    }
    if (this.atEnd() || depth !== 1) {
      this.pos = start;
      return [null, ''];
    }
    const content = _substring(this.source, contentStart, this.pos);
    this.advance(); // )
    this.advance(); // )
    const text = _substring(this.source, start, this.pos);
    return [new ArithmeticExpansion(content), text];
  }

  parse() {
    const source = this.source.trim();
    if (!source) {
      return [new Empty()];
    }
    const results = [];
    while (true) {
      this.skipWhitespace();
      while (!this.atEnd() && this.peek() === '\n') {
        this.advance();
      }
      if (this.atEnd()) {
        break;
      }
      const comment = this.parseComment();
      if (!comment) {
        break;
      }
    }
    while (!this.atEnd()) {
      const result = this._parseListImpl(false);
      if (result !== null) {
        results.push(result);
      }
      this.skipWhitespace();
      let foundNewline = false;
      while (!this.atEnd() && this.peek() === '\n') {
        foundNewline = true;
        this.advance();
        if (this._pendingHeredocEnd !== null && this._pendingHeredocEnd > this.pos) {
          this.pos = this._pendingHeredocEnd;
          this._pendingHeredocEnd = null;
        }
        this.skipWhitespace();
      }
      if (!foundNewline && !this.atEnd()) {
        throw new ParseError('Parser not fully implemented yet', this.pos);
      }
    }
    if (results.length === 0) {
      return [new Empty()];
    }
    return results;
  }

  parseComment() {
    if (this.atEnd() || this.peek() !== '#') {
      return null;
    }
    const start = this.pos;
    while (!this.atEnd() && this.peek() !== '\n') {
      this.advance();
    }
    const text = _substring(this.source, start, this.pos);
    return new Comment(text);
  }
}

// ============================================================================
// Entry Point
// ============================================================================

function parse(source) {
  const parser = new Parser(source);
  const results = [];

  parser.skipWhitespaceAndNewlines();

  while (!parser.atEnd()) {
    const node = parser.parseList();
    if (node === null) {
      break;
    }
    results.push(node);
    parser.skipWhitespaceAndNewlines();
  }

  if (results.length === 0 && source.trim() === '') {
    return [new Empty()];
  }

  return results;
}

// ============================================================================
// Exports
// ============================================================================

module.exports = {
  parse,
  ParseError,
  Node,
  Word,
  Command,
  Pipeline,
  List,
  Operator,
  PipeBoth,
  Empty,
  Comment,
  Redirect,
  HereDoc,
  Subshell,
  BraceGroup,
  If,
  While,
  Until,
  For,
  ForArith,
  Select,
  Case,
  CasePattern,
  Function,
  ParamExpansion,
  ParamLength,
  ParamIndirect,
  CommandSubstitution,
  ArithmeticExpansion,
  ArithmeticCommand,
  ArithNumber,
  ArithVar,
  ArithBinaryOp,
  ArithUnaryOp,
  ArithPreIncr,
  ArithPostIncr,
  ArithPreDecr,
  ArithPostDecr,
  ArithAssign,
  ArithTernary,
  ArithComma,
  ArithSubscript,
  ArithEscape,
  ArithDeprecated,
  AnsiCQuote,
  LocaleString,
  ProcessSubstitution,
  Negation,
  Time,
  ConditionalExpr,
  UnaryTest,
  BinaryTest,
  CondAnd,
  CondOr,
  CondNot,
  Coproc,
  TestCommand,
  Parser
};
