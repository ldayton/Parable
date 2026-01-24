/**
 * Parable.js - A recursive descent parser for bash.
 *
 * MIT License - https://github.com/ldayton/Parable
 *
 * @packageDocumentation
 */

// Error classes
export class ParseError extends Error {
	readonly message: string;
	readonly pos: number | null;
	readonly line: number | null;
}

// Base node interface
interface NodeBase {
	readonly kind: string;
	toSexp(): string;
}

// Structural nodes
export interface Word extends NodeBase {
	readonly kind: "word";
	readonly value: Node;
	readonly parts: Node[];
}

export interface Command extends NodeBase {
	readonly kind: "command";
	readonly words: Word[];
	readonly redirects: (Redirect | HereDoc)[];
}

export interface Pipeline extends NodeBase {
	readonly kind: "pipeline";
	readonly commands: Node[];
}

export interface List extends NodeBase {
	readonly kind: "list";
	readonly parts: Node[];
}

export interface Operator extends NodeBase {
	readonly kind: "operator";
	readonly op: string;
}

export interface PipeBoth extends NodeBase {
	readonly kind: "pipe-both";
}

export interface Empty extends NodeBase {
	readonly kind: "empty";
}

export interface Comment extends NodeBase {
	readonly kind: "comment";
	readonly text: string;
}

// Redirections
export interface Redirect extends NodeBase {
	readonly kind: "redirect";
	readonly op: string;
	readonly target: Word;
	readonly fd: number | null;
}

export interface HereDoc extends NodeBase {
	readonly kind: "heredoc";
	readonly delimiter: string;
	readonly content: string;
	readonly strip_tabs: boolean;
	readonly quoted: boolean;
	readonly fd: number | null;
	readonly complete: boolean;
}

// Compound commands
export interface Subshell extends NodeBase {
	readonly kind: "subshell";
	readonly body: Node;
	readonly redirects: (Redirect | HereDoc)[];
}

export interface BraceGroup extends NodeBase {
	readonly kind: "brace-group";
	readonly body: Node;
	readonly redirects: (Redirect | HereDoc)[];
}

export interface If extends NodeBase {
	readonly kind: "if";
	readonly condition: Node;
	readonly then_body: Node;
	readonly else_body: Node | null;
	readonly redirects: (Redirect | HereDoc)[];
}

export interface While extends NodeBase {
	readonly kind: "while";
	readonly condition: Node;
	readonly body: Node;
	readonly redirects: (Redirect | HereDoc)[];
}

export interface Until extends NodeBase {
	readonly kind: "until";
	readonly condition: Node;
	readonly body: Node;
	readonly redirects: (Redirect | HereDoc)[];
}

export interface For extends NodeBase {
	readonly kind: "for";
	readonly variable: string;
	readonly words: Word[];
	readonly body: Node;
	readonly redirects: (Redirect | HereDoc)[];
}

export interface ForArith extends NodeBase {
	readonly kind: "for-arith";
	readonly init: string | null;
	readonly cond: string | null;
	readonly incr: string | null;
	readonly body: Node;
	readonly redirects: (Redirect | HereDoc)[];
}

export interface Select extends NodeBase {
	readonly kind: "select";
	readonly variable: string;
	readonly words: Word[];
	readonly body: Node;
	readonly redirects: (Redirect | HereDoc)[];
}

export interface Case extends NodeBase {
	readonly kind: "case";
	readonly word: Word;
	readonly patterns: CasePattern[];
	readonly redirects: (Redirect | HereDoc)[];
}

export interface CasePattern extends NodeBase {
	readonly kind: "pattern";
	readonly pattern: string;
	readonly body: Node;
	readonly terminator: string;
}

export interface FunctionNode extends NodeBase {
	readonly kind: "function";
	readonly name: string;
	readonly body: Node;
}

// Expansions
export interface ParamExpansion extends NodeBase {
	readonly kind: "param";
	readonly param: string;
	readonly op: string | null;
	readonly arg: string | null;
}

export interface ParamLength extends NodeBase {
	readonly kind: "param-len";
	readonly param: string;
}

export interface ParamIndirect extends NodeBase {
	readonly kind: "param-indirect";
	readonly param: string;
	readonly op: string | null;
	readonly arg: string | null;
}

export interface CommandSubstitution extends NodeBase {
	readonly kind: "cmdsub";
	readonly command: Node;
	readonly brace: boolean;
}

export interface ArithmeticExpansion extends NodeBase {
	readonly kind: "arith";
	readonly expression: ArithNode | null;
}

export interface ProcessSubstitution extends NodeBase {
	readonly kind: "procsub";
	readonly direction: "<" | ">";
	readonly command: Node;
}

// Arithmetic expression nodes
export interface ArithNumber extends NodeBase {
	readonly kind: "number";
	readonly value: ArithNode;
}

export interface ArithEmpty extends NodeBase {
	readonly kind: "empty";
}

export interface ArithVar extends NodeBase {
	readonly kind: "var";
	readonly name: string;
}

export interface ArithBinaryOp extends NodeBase {
	readonly kind: "binary-op";
	readonly op: string;
	readonly left: ArithNode;
	readonly right: ArithNode;
}

export interface ArithUnaryOp extends NodeBase {
	readonly kind: "unary-op";
	readonly op: string;
	readonly operand: ArithNode;
}

export interface ArithPreIncr extends NodeBase {
	readonly kind: "pre-incr";
	readonly operand: ArithNode;
}

export interface ArithPostIncr extends NodeBase {
	readonly kind: "post-incr";
	readonly operand: ArithNode;
}

export interface ArithPreDecr extends NodeBase {
	readonly kind: "pre-decr";
	readonly operand: ArithNode;
}

export interface ArithPostDecr extends NodeBase {
	readonly kind: "post-decr";
	readonly operand: ArithNode;
}

export interface ArithAssign extends NodeBase {
	readonly kind: "assign";
	readonly op: string;
	readonly target: ArithNode;
	readonly value: ArithNode;
}

export interface ArithTernary extends NodeBase {
	readonly kind: "ternary";
	readonly condition: ArithNode;
	readonly if_true: ArithNode;
	readonly if_false: ArithNode;
}

export interface ArithComma extends NodeBase {
	readonly kind: "comma";
	readonly left: ArithNode;
	readonly right: ArithNode;
}

export interface ArithSubscript extends NodeBase {
	readonly kind: "subscript";
	readonly array: string;
	readonly index: ArithNode;
}

export interface ArithEscape extends NodeBase {
	readonly kind: "escape";
	readonly char: string;
}

export interface ArithDeprecated extends NodeBase {
	readonly kind: "arith-deprecated";
	readonly expression: string;
}

export interface ArithConcat extends NodeBase {
	readonly kind: "arith-concat";
	readonly parts: ArithNode[];
}

export interface ArithmeticCommand extends NodeBase {
	readonly kind: "arith-cmd";
	readonly expression: ArithNode | null;
	readonly redirects: (Redirect | HereDoc)[];
	readonly raw_content: string;
}

// Conditional expression nodes
export interface ConditionalExpr extends NodeBase {
	readonly kind: "cond-expr";
	readonly body: CondNode | string;
	readonly redirects: (Redirect | HereDoc)[];
}

export interface UnaryTest extends NodeBase {
	readonly kind: "unary-test";
	readonly op: string;
	readonly operand: Word;
}

export interface BinaryTest extends NodeBase {
	readonly kind: "binary-test";
	readonly op: string;
	readonly left: Word;
	readonly right: Word;
}

export interface CondAnd extends NodeBase {
	readonly kind: "cond-and";
	readonly left: CondNode;
	readonly right: CondNode;
}

export interface CondOr extends NodeBase {
	readonly kind: "cond-or";
	readonly left: CondNode;
	readonly right: CondNode;
}

export interface CondNot extends NodeBase {
	readonly kind: "cond-not";
	readonly operand: CondNode;
}

export interface CondParen extends NodeBase {
	readonly kind: "cond-paren";
	readonly inner: CondNode;
}

// Quote nodes
export interface AnsiCQuote extends NodeBase {
	readonly kind: "ansi-c";
	readonly content: string;
}

export interface LocaleString extends NodeBase {
	readonly kind: "locale";
	readonly content: string;
}

// Special nodes
export interface Negation extends NodeBase {
	readonly kind: "negation";
	readonly pipeline: Node | null;
}

export interface Time extends NodeBase {
	readonly kind: "time";
	readonly pipeline: Node | null;
	readonly posix: boolean;
}

export interface ArrayNode extends NodeBase {
	readonly kind: "array";
	readonly elements: Word[];
}

export interface Coproc extends NodeBase {
	readonly kind: "coproc";
	readonly command: Node;
	readonly name: string | null;
}

// Union type for arithmetic expression nodes
export type ArithNode =
	| ArithNumber
	| ArithEmpty
	| ArithVar
	| ArithBinaryOp
	| ArithUnaryOp
	| ArithPreIncr
	| ArithPostIncr
	| ArithPreDecr
	| ArithPostDecr
	| ArithAssign
	| ArithTernary
	| ArithComma
	| ArithSubscript
	| ArithEscape
	| ArithDeprecated
	| ArithConcat;

// Union type for conditional expression nodes
export type CondNode =
	| UnaryTest
	| BinaryTest
	| CondAnd
	| CondOr
	| CondNot
	| CondParen;

// Union type for all AST nodes
export type Node =
	| Word
	| Command
	| Pipeline
	| List
	| Operator
	| PipeBoth
	| Empty
	| Comment
	| Redirect
	| HereDoc
	| Subshell
	| BraceGroup
	| If
	| While
	| Until
	| For
	| ForArith
	| Select
	| Case
	| CasePattern
	| FunctionNode
	| ParamExpansion
	| ParamLength
	| ParamIndirect
	| CommandSubstitution
	| ArithmeticExpansion
	| ProcessSubstitution
	| ArithmeticCommand
	| ConditionalExpr
	| AnsiCQuote
	| LocaleString
	| Negation
	| Time
	| ArrayNode
	| Coproc;

/**
 * Parse bash source code into an AST.
 * @param source - The bash source code to parse
 * @param extglob - Enable extended glob patterns (default: false)
 * @returns An array of parsed AST nodes
 * @throws {ParseError} If the source contains syntax errors
 */
export function parse(source: string, extglob?: boolean): Node[];
