use strict;
use warnings;
use feature 'signatures';
no warnings 'experimental::signatures';

use constant ANSI_C_ESCAPES => {"a" => 7, "b" => 8, "e" => 27, "E" => 27, "f" => 12, "n" => 10, "r" => 13, "t" => 9, "v" => 11, "\\" => 92, "\"" => 34, "?" => 63};
use constant TOKENTYPE_EOF => 0;
use constant TOKENTYPE_WORD => 1;
use constant TOKENTYPE_NEWLINE => 2;
use constant TOKENTYPE_SEMI => 10;
use constant TOKENTYPE_PIPE => 11;
use constant TOKENTYPE_AMP => 12;
use constant TOKENTYPE_LPAREN => 13;
use constant TOKENTYPE_RPAREN => 14;
use constant TOKENTYPE_LBRACE => 15;
use constant TOKENTYPE_RBRACE => 16;
use constant TOKENTYPE_LESS => 17;
use constant TOKENTYPE_GREATER => 18;
use constant TOKENTYPE_AND_AND => 30;
use constant TOKENTYPE_OR_OR => 31;
use constant TOKENTYPE_SEMI_SEMI => 32;
use constant TOKENTYPE_SEMI_AMP => 33;
use constant TOKENTYPE_SEMI_SEMI_AMP => 34;
use constant TOKENTYPE_LESS_LESS => 35;
use constant TOKENTYPE_GREATER_GREATER => 36;
use constant TOKENTYPE_LESS_AMP => 37;
use constant TOKENTYPE_GREATER_AMP => 38;
use constant TOKENTYPE_LESS_GREATER => 39;
use constant TOKENTYPE_GREATER_PIPE => 40;
use constant TOKENTYPE_LESS_LESS_MINUS => 41;
use constant TOKENTYPE_LESS_LESS_LESS => 42;
use constant TOKENTYPE_AMP_GREATER => 43;
use constant TOKENTYPE_AMP_GREATER_GREATER => 44;
use constant TOKENTYPE_PIPE_AMP => 45;
use constant TOKENTYPE_IF => 50;
use constant TOKENTYPE_THEN => 51;
use constant TOKENTYPE_ELSE => 52;
use constant TOKENTYPE_ELIF => 53;
use constant TOKENTYPE_FI => 54;
use constant TOKENTYPE_CASE => 55;
use constant TOKENTYPE_ESAC => 56;
use constant TOKENTYPE_FOR => 57;
use constant TOKENTYPE_WHILE => 58;
use constant TOKENTYPE_UNTIL => 59;
use constant TOKENTYPE_DO => 60;
use constant TOKENTYPE_DONE => 61;
use constant TOKENTYPE_IN => 62;
use constant TOKENTYPE_FUNCTION => 63;
use constant TOKENTYPE_SELECT => 64;
use constant TOKENTYPE_COPROC => 65;
use constant TOKENTYPE_TIME => 66;
use constant TOKENTYPE_BANG => 67;
use constant TOKENTYPE_LBRACKET_LBRACKET => 68;
use constant TOKENTYPE_RBRACKET_RBRACKET => 69;
use constant TOKENTYPE_ASSIGNMENT_WORD => 80;
use constant TOKENTYPE_NUMBER => 81;
use constant PARSERSTATEFLAGS_NONE => 0;
use constant PARSERSTATEFLAGS_PST_CASEPAT => 1;
use constant PARSERSTATEFLAGS_PST_CMDSUBST => 2;
use constant PARSERSTATEFLAGS_PST_CASESTMT => 4;
use constant PARSERSTATEFLAGS_PST_CONDEXPR => 8;
use constant PARSERSTATEFLAGS_PST_COMPASSIGN => 16;
use constant PARSERSTATEFLAGS_PST_ARITH => 32;
use constant PARSERSTATEFLAGS_PST_HEREDOC => 64;
use constant PARSERSTATEFLAGS_PST_REGEXP => 128;
use constant PARSERSTATEFLAGS_PST_EXTPAT => 256;
use constant PARSERSTATEFLAGS_PST_SUBSHELL => 512;
use constant PARSERSTATEFLAGS_PST_REDIRLIST => 1024;
use constant PARSERSTATEFLAGS_PST_COMMENT => 2048;
use constant PARSERSTATEFLAGS_PST_EOFTOKEN => 4096;
use constant DOLBRACESTATE_NONE => 0;
use constant DOLBRACESTATE_PARAM => 1;
use constant DOLBRACESTATE_OP => 2;
use constant DOLBRACESTATE_WORD => 4;
use constant DOLBRACESTATE_QUOTE => 64;
use constant DOLBRACESTATE_QUOTE2 => 128;
use constant MATCHEDPAIRFLAGS_NONE => 0;
use constant MATCHEDPAIRFLAGS_DQUOTE => 1;
use constant MATCHEDPAIRFLAGS_DOLBRACE => 2;
use constant MATCHEDPAIRFLAGS_COMMAND => 4;
use constant MATCHEDPAIRFLAGS_ARITH => 8;
use constant MATCHEDPAIRFLAGS_ALLOWESC => 16;
use constant MATCHEDPAIRFLAGS_EXTGLOB => 32;
use constant MATCHEDPAIRFLAGS_FIRSTCLOSE => 64;
use constant MATCHEDPAIRFLAGS_ARRAYSUB => 128;
use constant MATCHEDPAIRFLAGS_BACKQUOTE => 256;
use constant PARSECONTEXT_NORMAL => 0;
use constant PARSECONTEXT_COMMAND_SUB => 1;
use constant PARSECONTEXT_ARITHMETIC => 2;
use constant PARSECONTEXT_CASE_PATTERN => 3;
use constant PARSECONTEXT_BRACE_EXPANSION => 4;
use constant RESERVED_WORDS => {"if" => 1, "then" => 1, "elif" => 1, "else" => 1, "fi" => 1, "while" => 1, "until" => 1, "for" => 1, "select" => 1, "do" => 1, "done" => 1, "case" => 1, "esac" => 1, "in" => 1, "function" => 1, "coproc" => 1};
use constant COND_UNARY_OPS => {"-a" => 1, "-b" => 1, "-c" => 1, "-d" => 1, "-e" => 1, "-f" => 1, "-g" => 1, "-h" => 1, "-k" => 1, "-p" => 1, "-r" => 1, "-s" => 1, "-t" => 1, "-u" => 1, "-w" => 1, "-x" => 1, "-G" => 1, "-L" => 1, "-N" => 1, "-O" => 1, "-S" => 1, "-z" => 1, "-n" => 1, "-o" => 1, "-v" => 1, "-R" => 1};
use constant COND_BINARY_OPS => {"==" => 1, "!=" => 1, "=~" => 1, "=" => 1, "<" => 1, ">" => 1, "-eq" => 1, "-ne" => 1, "-lt" => 1, "-le" => 1, "-gt" => 1, "-ge" => 1, "-nt" => 1, "-ot" => 1, "-ef" => 1};
use constant COMPOUND_KEYWORDS => {"while" => 1, "until" => 1, "for" => 1, "if" => 1, "case" => 1, "select" => 1};
use constant ASSIGNMENT_BUILTINS => {"alias" => 1, "declare" => 1, "typeset" => 1, "local" => 1, "export" => 1, "readonly" => 1, "eval" => 1, "let" => 1};
use constant _SMP_LITERAL => 1;
use constant _SMP_PAST_OPEN => 2;
use constant WORD_CTX_NORMAL => 0;
use constant WORD_CTX_COND => 1;
use constant WORD_CTX_REGEX => 2;

# Interface: Node
#   GetKind()
#   ToSexp()

package ParseError;
use parent -norequire, 'Exception';

sub new ($class, $message, $pos_, $line) {
    return bless { message => $message, pos_ => $pos_, line => $line }, $class;
}

sub message ($self) { $self->{message} }
sub pos_ ($self) { $self->{pos_} }
sub line ($self) { $self->{line} }

sub format_message ($self) {
    if ($self->{line} != 0 && $self->{pos_} != 0) {
        return sprintf("Parse error at line %s, position %s: %s", $self->{line}, $self->{pos_}, $self->{message});
    } elsif ($self->{pos_} != 0) {
        return sprintf("Parse error at position %s: %s", $self->{pos_}, $self->{message});
    }
    return sprintf("Parse error: %s", $self->{message});
}

1;

package MatchedPairError;
use parent -norequire, 'Exception';

1;


package Token;

sub new ($class, $type, $value, $pos_, $parts, $word) {
    return bless { type => $type, value => $value, pos_ => $pos_, parts => $parts, word => $word }, $class;
}

sub type ($self) { $self->{type} }
sub value ($self) { $self->{value} }
sub pos_ ($self) { $self->{pos_} }
sub parts ($self) { $self->{parts} }
sub word ($self) { $self->{word} }

sub _repr__ ($self) {
    if (defined($self->{word})) {
        return sprintf("Token(%s, %s, %s, word=%s)", $self->{type}, $self->{value}, $self->{pos_}, $self->{word});
    }
    if ((scalar(@{$self->{parts}}) > 0)) {
        return sprintf("Token(%s, %s, %s, parts=%s)", $self->{type}, $self->{value}, $self->{pos_}, scalar(@{$self->{parts}}));
    }
    return sprintf("Token(%s, %s, %s)", $self->{type}, $self->{value}, $self->{pos_});
}

1;




package SavedParserState;

sub new ($class, $parser_state, $dolbrace_state, $pending_heredocs, $ctx_stack, $eof_token) {
    return bless { parser_state => $parser_state, dolbrace_state => $dolbrace_state, pending_heredocs => $pending_heredocs, ctx_stack => $ctx_stack, eof_token => $eof_token }, $class;
}

sub parser_state ($self) { $self->{parser_state} }
sub dolbrace_state ($self) { $self->{dolbrace_state} }
sub pending_heredocs ($self) { $self->{pending_heredocs} }
sub ctx_stack ($self) { $self->{ctx_stack} }
sub eof_token ($self) { $self->{eof_token} }

1;

package QuoteState;

sub new ($class, $single, $double, $stack) {
    return bless { single => $single, double => $double, stack => $stack }, $class;
}

sub single ($self) { $self->{single} }
sub double ($self) { $self->{double} }
sub stack ($self) { $self->{stack} }

sub push_ ($self) {
    $self->{stack}->push([$self->{single}, $self->{double}]);
    $self->{single} = 0;
    $self->{double} = 0;
}

sub pop_ ($self) {
    if ((scalar(@{$self->{stack}}) > 0)) {
        ($self->{single}, $self->{double}) = @{$self->{stack}->pop_()};
    }
}

sub in_quotes ($self) {
    return $self->{single} || $self->{double};
}

sub copy ($self) {
    my $qs = new_quote_state();
    $qs->{single} = $self->{single};
    $qs->{double} = $self->{double};
    $qs->{stack} = $self->{stack}->copy();
    return $qs;
}

sub outer_double ($self) {
    if (scalar(@{$self->{stack}}) == 0) {
        return 0;
    }
    return $self->{stack}->[-1]->[1];
}

1;

package ParseContext;

sub new ($class, $kind, $paren_depth, $brace_depth, $bracket_depth, $case_depth, $arith_depth, $arith_paren_depth, $quote) {
    return bless { kind => $kind, paren_depth => $paren_depth, brace_depth => $brace_depth, bracket_depth => $bracket_depth, case_depth => $case_depth, arith_depth => $arith_depth, arith_paren_depth => $arith_paren_depth, quote => $quote }, $class;
}

sub kind ($self) { $self->{kind} }
sub paren_depth ($self) { $self->{paren_depth} }
sub brace_depth ($self) { $self->{brace_depth} }
sub bracket_depth ($self) { $self->{bracket_depth} }
sub case_depth ($self) { $self->{case_depth} }
sub arith_depth ($self) { $self->{arith_depth} }
sub arith_paren_depth ($self) { $self->{arith_paren_depth} }
sub quote ($self) { $self->{quote} }

sub copy ($self) {
    my $ctx = new_parse_context($self->{kind});
    $ctx->{paren_depth} = $self->{paren_depth};
    $ctx->{brace_depth} = $self->{brace_depth};
    $ctx->{bracket_depth} = $self->{bracket_depth};
    $ctx->{case_depth} = $self->{case_depth};
    $ctx->{arith_depth} = $self->{arith_depth};
    $ctx->{arith_paren_depth} = $self->{arith_paren_depth};
    $ctx->{quote} = $self->{quote}->copy();
    return $ctx;
}

1;

package ContextStack;

sub new ($class, $stack) {
    return bless { stack => $stack }, $class;
}

sub stack ($self) { $self->{stack} }

sub get_current ($self) {
    return $self->{stack}->[-1];
}

sub push_ ($self, $kind) {
    $self->{stack}->push(new_parse_context($kind));
}

sub pop_ ($self) {
    if (scalar(@{$self->{stack}}) > 1) {
        return $self->{stack}->pop_();
    }
    return $self->{stack}->[0];
}

sub copy_stack ($self) {
    my $result = [];
    for my $ctx (@{($self->{stack} // [])}) {
        $result->push($ctx->copy());
    }
    return $result;
}

sub restore_from ($self, $saved_stack) {
    my $result = [];
    for my $ctx (@{$saved_stack}) {
        $result->push($ctx->copy());
    }
    $self->{stack} = $result;
}

1;

package Lexer;

sub new ($class, $reserved_words, $source, $pos_, $length_, $quote, $token_cache, $parser_state, $dolbrace_state, $pending_heredocs, $extglob, $parser, $eof_token, $last_read_token, $word_context, $at_command_start, $in_array_literal, $in_assign_builtin, $post_read_pos, $cached_word_context, $cached_at_command_start, $cached_in_array_literal, $cached_in_assign_builtin) {
    return bless { reserved_words => $reserved_words, source => $source, pos_ => $pos_, length_ => $length_, quote => $quote, token_cache => $token_cache, parser_state => $parser_state, dolbrace_state => $dolbrace_state, pending_heredocs => $pending_heredocs, extglob => $extglob, parser => $parser, eof_token => $eof_token, last_read_token => $last_read_token, word_context => $word_context, at_command_start => $at_command_start, in_array_literal => $in_array_literal, in_assign_builtin => $in_assign_builtin, post_read_pos => $post_read_pos, cached_word_context => $cached_word_context, cached_at_command_start => $cached_at_command_start, cached_in_array_literal => $cached_in_array_literal, cached_in_assign_builtin => $cached_in_assign_builtin }, $class;
}

sub reserved_words ($self) { $self->{reserved_words} }
sub source ($self) { $self->{source} }
sub pos_ ($self) { $self->{pos_} }
sub length_ ($self) { $self->{length_} }
sub quote ($self) { $self->{quote} }
sub token_cache ($self) { $self->{token_cache} }
sub parser_state ($self) { $self->{parser_state} }
sub dolbrace_state ($self) { $self->{dolbrace_state} }
sub pending_heredocs ($self) { $self->{pending_heredocs} }
sub extglob ($self) { $self->{extglob} }
sub parser ($self) { $self->{parser} }
sub eof_token ($self) { $self->{eof_token} }
sub last_read_token ($self) { $self->{last_read_token} }
sub word_context ($self) { $self->{word_context} }
sub at_command_start ($self) { $self->{at_command_start} }
sub in_array_literal ($self) { $self->{in_array_literal} }
sub in_assign_builtin ($self) { $self->{in_assign_builtin} }
sub post_read_pos ($self) { $self->{post_read_pos} }
sub cached_word_context ($self) { $self->{cached_word_context} }
sub cached_at_command_start ($self) { $self->{cached_at_command_start} }
sub cached_in_array_literal ($self) { $self->{cached_in_array_literal} }
sub cached_in_assign_builtin ($self) { $self->{cached_in_assign_builtin} }

sub peek ($self) {
    if ($self->{pos_} >= $self->{length_}) {
        return "";
    }
    return $self->{source}->[$self->{pos_}];
}

sub advance ($self) {
    if ($self->{pos_} >= $self->{length_}) {
        return "";
    }
    my $c = $self->{source}->[$self->{pos_}];
    $self->{pos_} += 1;
    return $c;
}

sub at_end ($self) {
    return $self->{pos_} >= $self->{length_};
}

sub lookahead ($self, $n) {
    return substring($self->{source}, $self->{pos_}, $self->{pos_} + $n);
}

sub is_metachar ($self, $c) {
    return (index("|&;()<> \t\n", $c) >= 0);
}

sub read_operator ($self) {
    my $start = $self->{pos_};
    my $c = $self->peek();
    if ($c eq "") {
        return undef;
    }
    my $two = $self->lookahead(2);
    my $three = $self->lookahead(3);
    if ($three eq ";;&") {
        $self->{pos_} += 3;
        return Token->new(TOKENTYPE_SEMI_SEMI_AMP(), $three, $start);
    }
    if ($three eq "<<-") {
        $self->{pos_} += 3;
        return Token->new(TOKENTYPE_LESS_LESS_MINUS(), $three, $start);
    }
    if ($three eq "<<<") {
        $self->{pos_} += 3;
        return Token->new(TOKENTYPE_LESS_LESS_LESS(), $three, $start);
    }
    if ($three eq "&>>") {
        $self->{pos_} += 3;
        return Token->new(TOKENTYPE_AMP_GREATER_GREATER(), $three, $start);
    }
    if ($two eq "&&") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_AND_AND(), $two, $start);
    }
    if ($two eq "||") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_OR_OR(), $two, $start);
    }
    if ($two eq ";;") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_SEMI_SEMI(), $two, $start);
    }
    if ($two eq ";&") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_SEMI_AMP(), $two, $start);
    }
    if ($two eq "<<") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_LESS_LESS(), $two, $start);
    }
    if ($two eq ">>") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_GREATER_GREATER(), $two, $start);
    }
    if ($two eq "<&") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_LESS_AMP(), $two, $start);
    }
    if ($two eq ">&") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_GREATER_AMP(), $two, $start);
    }
    if ($two eq "<>") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_LESS_GREATER(), $two, $start);
    }
    if ($two eq ">|") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_GREATER_PIPE(), $two, $start);
    }
    if ($two eq "&>") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_AMP_GREATER(), $two, $start);
    }
    if ($two eq "|&") {
        $self->{pos_} += 2;
        return Token->new(TOKENTYPE_PIPE_AMP(), $two, $start);
    }
    if ($c eq ";") {
        $self->{pos_} += 1;
        return Token->new(TOKENTYPE_SEMI(), $c, $start);
    }
    if ($c eq "|") {
        $self->{pos_} += 1;
        return Token->new(TOKENTYPE_PIPE(), $c, $start);
    }
    if ($c eq "&") {
        $self->{pos_} += 1;
        return Token->new(TOKENTYPE_AMP(), $c, $start);
    }
    if ($c eq "(") {
        if ($self->{word_context} == WORD_CTX_REGEX()) {
            return undef;
        }
        $self->{pos_} += 1;
        return Token->new(TOKENTYPE_LPAREN(), $c, $start);
    }
    if ($c eq ")") {
        if ($self->{word_context} == WORD_CTX_REGEX()) {
            return undef;
        }
        $self->{pos_} += 1;
        return Token->new(TOKENTYPE_RPAREN(), $c, $start);
    }
    if ($c eq "<") {
        if ($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
            return undef;
        }
        $self->{pos_} += 1;
        return Token->new(TOKENTYPE_LESS(), $c, $start);
    }
    if ($c eq ">") {
        if ($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
            return undef;
        }
        $self->{pos_} += 1;
        return Token->new(TOKENTYPE_GREATER(), $c, $start);
    }
    if ($c eq "\n") {
        $self->{pos_} += 1;
        return Token->new(TOKENTYPE_NEWLINE(), $c, $start);
    }
    return undef;
}

sub skip_blanks ($self) {
    my $c;
    while ($self->{pos_} < $self->{length_}) {
        $c = $self->{source}->[$self->{pos_}];
        if ($c ne " " && $c ne "\t") {
            last;
        }
        $self->{pos_} += 1;
    }
}

sub skip_comment ($self) {
    my $prev;
    if ($self->{pos_} >= $self->{length_}) {
        return 0;
    }
    if ($self->{source}->[$self->{pos_}] ne "#") {
        return 0;
    }
    if ($self->{quote}->in_quotes()) {
        return 0;
    }
    if ($self->{pos_} > 0) {
        $prev = $self->{source}->[$self->{pos_} - 1];
        if ((index(" \t\n;|&(){}", $prev) == -1)) {
            return 0;
        }
    }
    while ($self->{pos_} < $self->{length_} && $self->{source}->[$self->{pos_}] ne "\n") {
        $self->{pos_} += 1;
    }
    return 1;
}

sub read_single_quote ($self, $start) {
    my $c;
    my $chars = ["'"];
    my $saw_newline = 0;
    while ($self->{pos_} < $self->{length_}) {
        $c = $self->{source}->[$self->{pos_}];
        if ($c eq "\n") {
            $saw_newline = 1;
        }
        $chars->push($c);
        $self->{pos_} += 1;
        if ($c eq "'") {
            return [""->join_($chars), $saw_newline];
        }
    }
    die "Unterminated single quote";
}

sub is_word_terminator ($self, $ctx, $ch, $bracket_depth, $paren_depth) {
    if ($ctx == WORD_CTX_REGEX()) {
        if ($ch eq "]" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "]") {
            return 1;
        }
        if ($ch eq "&" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "&") {
            return 1;
        }
        if ($ch eq ")" && $paren_depth == 0) {
            return 1;
        }
        return is_whitespace($ch) && $paren_depth == 0;
    }
    if ($ctx == WORD_CTX_COND()) {
        if ($ch eq "]" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "]") {
            return 1;
        }
        if ($ch eq ")") {
            return 1;
        }
        if ($ch eq "&") {
            return 1;
        }
        if ($ch eq "|") {
            return 1;
        }
        if ($ch eq ";") {
            return 1;
        }
        if (is_redirect_char($ch) && !($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(")) {
            return 1;
        }
        return is_whitespace($ch);
    }
    if (($self->{parser_state} & PARSERSTATEFLAGS_PST_EOFTOKEN() ? 1 : 0) && $self->{eof_token} ne "" && $ch eq $self->{eof_token} && $bracket_depth == 0) {
        return 1;
    }
    if (is_redirect_char($ch) && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
        return 0;
    }
    return is_metachar($ch) && $bracket_depth == 0;
}

sub read_bracket_expression ($self, $chars, $parts, $for_regex, $paren_depth) {
    my $bracket_will_close;
    my $c;
    my $next_ch;
    my $sc;
    my $scan;
    if ($for_regex) {
        $scan = $self->{pos_} + 1;
        if ($scan < $self->{length_} && $self->{source}->[$scan] eq "^") {
            $scan += 1;
        }
        if ($scan < $self->{length_} && $self->{source}->[$scan] eq "]") {
            $scan += 1;
        }
        $bracket_will_close = 0;
        while ($scan < $self->{length_}) {
            $sc = $self->{source}->[$scan];
            if ($sc eq "]" && $scan + 1 < $self->{length_} && $self->{source}->[$scan + 1] eq "]") {
                last;
            }
            if ($sc eq ")" && $paren_depth > 0) {
                last;
            }
            if ($sc eq "&" && $scan + 1 < $self->{length_} && $self->{source}->[$scan + 1] eq "&") {
                last;
            }
            if ($sc eq "]") {
                $bracket_will_close = 1;
                last;
            }
            if ($sc eq "[" && $scan + 1 < $self->{length_} && $self->{source}->[$scan + 1] eq ":") {
                $scan += 2;
                while ($scan < $self->{length_} && !($self->{source}->[$scan] eq ":" && $scan + 1 < $self->{length_} && $self->{source}->[$scan + 1] eq "]")) {
                    $scan += 1;
                }
                if ($scan < $self->{length_}) {
                    $scan += 2;
                }
                next;
            }
            $scan += 1;
        }
        if (!$bracket_will_close) {
            return 0;
        }
    } else {
        if ($self->{pos_} + 1 >= $self->{length_}) {
            return 0;
        }
        $next_ch = $self->{source}->[$self->{pos_} + 1];
        if (is_whitespace_no_newline($next_ch) || $next_ch eq "&" || $next_ch eq "|") {
            return 0;
        }
    }
    $chars->append($self->advance());
    if (!$self->at_end() && $self->peek() eq "^") {
        $chars->append($self->advance());
    }
    if (!$self->at_end() && $self->peek() eq "]") {
        $chars->append($self->advance());
    }
    while (!$self->at_end()) {
        $c = $self->peek();
        if ($c eq "]") {
            $chars->append($self->advance());
            last;
        }
        if ($c eq "[" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq ":") {
            $chars->append($self->advance());
            $chars->append($self->advance());
            while (!$self->at_end() && !($self->peek() eq ":" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "]")) {
                $chars->append($self->advance());
            }
            if (!$self->at_end()) {
                $chars->append($self->advance());
                $chars->append($self->advance());
            }
        } elsif (!$for_regex && $c eq "[" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "=") {
            $chars->append($self->advance());
            $chars->append($self->advance());
            while (!$self->at_end() && !($self->peek() eq "=" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "]")) {
                $chars->append($self->advance());
            }
            if (!$self->at_end()) {
                $chars->append($self->advance());
                $chars->append($self->advance());
            }
        } elsif (!$for_regex && $c eq "[" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq ".") {
            $chars->append($self->advance());
            $chars->append($self->advance());
            while (!$self->at_end() && !($self->peek() eq "." && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "]")) {
                $chars->append($self->advance());
            }
            if (!$self->at_end()) {
                $chars->append($self->advance());
                $chars->append($self->advance());
            }
        } elsif ($for_regex && $c eq "\$") {
            $self->sync_to_parser();
            if (!$self->{parser}->parse_dollar_expansion($chars, $parts, 0)) {
                $self->sync_from_parser();
                $chars->append($self->advance());
            } else {
                $self->sync_from_parser();
            }
        } else {
            $chars->append($self->advance());
        }
    }
    return 1;
}

sub parse_matched_pair ($self, $open_char, $close_char, $flags, $initial_was_dollar) {
    my $after_brace_pos;
    my $arith_node;
    my $arith_text;
    my $ch;
    my $cmd_node;
    my $cmd_text;
    my $direction;
    my $in_dquote;
    my $nested;
    my $next_ch;
    my $param_node;
    my $param_text;
    my $procsub_node;
    my $procsub_text;
    my $quote_flags;
    my $start = $self->{pos_};
    my $count = 1;
    my $chars = [];
    my $pass_next = 0;
    my $was_dollar = $initial_was_dollar;
    my $was_gtlt = 0;
    while ($count > 0) {
        if ($self->at_end()) {
            die sprintf("unexpected EOF while looking for matching `%s'", $close_char);
        }
        $ch = $self->advance();
        if (($flags & MATCHEDPAIRFLAGS_DOLBRACE() ? 1 : 0) && $self->{dolbrace_state} == DOLBRACESTATE_OP()) {
            if ((index("#%^,~:-=?+/", $ch) == -1)) {
                $self->{dolbrace_state} = DOLBRACESTATE_WORD();
            }
        }
        if ($pass_next) {
            $pass_next = 0;
            $chars->push($ch);
            $was_dollar = $ch eq "\$";
            $was_gtlt = (index("<>", $ch) >= 0);
            next;
        }
        if ($open_char eq "'") {
            if ($ch eq $close_char) {
                $count -= 1;
                if ($count == 0) {
                    last;
                }
            }
            if ($ch eq "\\" && ($flags & MATCHEDPAIRFLAGS_ALLOWESC() ? 1 : 0)) {
                $pass_next = 1;
            }
            $chars->push($ch);
            $was_dollar = 0;
            $was_gtlt = 0;
            next;
        }
        if ($ch eq "\\") {
            if (!$self->at_end() && $self->peek() eq "\n") {
                $self->advance();
                $was_dollar = 0;
                $was_gtlt = 0;
                next;
            }
            $pass_next = 1;
            $chars->push($ch);
            $was_dollar = 0;
            $was_gtlt = 0;
            next;
        }
        if ($ch eq $close_char) {
            $count -= 1;
            if ($count == 0) {
                last;
            }
            $chars->push($ch);
            $was_dollar = 0;
            $was_gtlt = (index("<>", $ch) >= 0);
            next;
        }
        if ($ch eq $open_char && $open_char ne $close_char) {
            if (!(($flags & MATCHEDPAIRFLAGS_DOLBRACE() ? 1 : 0) && $open_char eq "{")) {
                $count += 1;
            }
            $chars->push($ch);
            $was_dollar = 0;
            $was_gtlt = (index("<>", $ch) >= 0);
            next;
        }
        if (((index("'\"`", $ch) >= 0)) && $open_char ne $close_char) {
            my $nested = "";
            if ($ch eq "'") {
                $chars->push($ch);
                $quote_flags = ($was_dollar ? $flags | MATCHEDPAIRFLAGS_ALLOWESC() : $flags);
                $nested = $self->parse_matched_pair("'", "'", $quote_flags, 0);
                $chars->push($nested);
                $chars->push("'");
                $was_dollar = 0;
                $was_gtlt = 0;
                next;
            } elsif ($ch eq "\"") {
                $chars->push($ch);
                $nested = $self->parse_matched_pair("\"", "\"", $flags | MATCHEDPAIRFLAGS_DQUOTE(), 0);
                $chars->push($nested);
                $chars->push("\"");
                $was_dollar = 0;
                $was_gtlt = 0;
                next;
            } elsif ($ch eq "`") {
                $chars->push($ch);
                $nested = $self->parse_matched_pair("`", "`", $flags, 0);
                $chars->push($nested);
                $chars->push("`");
                $was_dollar = 0;
                $was_gtlt = 0;
                next;
            }
        }
        if ($ch eq "\$" && !$self->at_end() && !($flags & MATCHEDPAIRFLAGS_EXTGLOB() ? 1 : 0)) {
            $next_ch = $self->peek();
            if ($was_dollar) {
                $chars->push($ch);
                $was_dollar = 0;
                $was_gtlt = 0;
                next;
            }
            if ($next_ch eq "{") {
                if (($flags & MATCHEDPAIRFLAGS_ARITH() ? 1 : 0)) {
                    $after_brace_pos = $self->{pos_} + 1;
                    if ($after_brace_pos >= $self->{length_} || !is_funsub_char($self->{source}->[$after_brace_pos])) {
                        $chars->push($ch);
                        $was_dollar = 1;
                        $was_gtlt = 0;
                        next;
                    }
                }
                $self->{pos_} -= 1;
                $self->sync_to_parser();
                $in_dquote = ($flags & MATCHEDPAIRFLAGS_DQUOTE()) != 0;
                ($param_node, $param_text) = @{$self->{parser}->parse_param_expansion($in_dquote)};
                $self->sync_from_parser();
                if (defined($param_node)) {
                    $chars->push($param_text);
                    $was_dollar = 0;
                    $was_gtlt = 0;
                } else {
                    $chars->push($self->advance());
                    $was_dollar = 1;
                    $was_gtlt = 0;
                }
                next;
            } elsif ($next_ch eq "(") {
                $self->{pos_} -= 1;
                $self->sync_to_parser();
                my $cmd_node = undef;
                my $cmd_text = "";
                if ($self->{pos_} + 2 < $self->{length_} && $self->{source}->[$self->{pos_} + 2] eq "(") {
                    ($arith_node, $arith_text) = @{$self->{parser}->parse_arithmetic_expansion()};
                    $self->sync_from_parser();
                    if (defined($arith_node)) {
                        $chars->push($arith_text);
                        $was_dollar = 0;
                        $was_gtlt = 0;
                    } else {
                        $self->sync_to_parser();
                        ($cmd_node, $cmd_text) = @{$self->{parser}->parse_command_substitution()};
                        $self->sync_from_parser();
                        if (defined($cmd_node)) {
                            $chars->push($cmd_text);
                            $was_dollar = 0;
                            $was_gtlt = 0;
                        } else {
                            $chars->push($self->advance());
                            $chars->push($self->advance());
                            $was_dollar = 0;
                            $was_gtlt = 0;
                        }
                    }
                } else {
                    ($cmd_node, $cmd_text) = @{$self->{parser}->parse_command_substitution()};
                    $self->sync_from_parser();
                    if (defined($cmd_node)) {
                        $chars->push($cmd_text);
                        $was_dollar = 0;
                        $was_gtlt = 0;
                    } else {
                        $chars->push($self->advance());
                        $chars->push($self->advance());
                        $was_dollar = 0;
                        $was_gtlt = 0;
                    }
                }
                next;
            } elsif ($next_ch eq "[") {
                $self->{pos_} -= 1;
                $self->sync_to_parser();
                ($arith_node, $arith_text) = @{$self->{parser}->parse_deprecated_arithmetic()};
                $self->sync_from_parser();
                if (defined($arith_node)) {
                    $chars->push($arith_text);
                    $was_dollar = 0;
                    $was_gtlt = 0;
                } else {
                    $chars->push($self->advance());
                    $was_dollar = 1;
                    $was_gtlt = 0;
                }
                next;
            }
        }
        if ($ch eq "(" && $was_gtlt && ($flags & MATCHEDPAIRFLAGS_DOLBRACE() | MATCHEDPAIRFLAGS_ARRAYSUB() ? 1 : 0)) {
            $direction = $chars->[-1];
            $chars = [@{$chars}[0 .. scalar(@{$chars}) - 1 - 1]];
            $self->{pos_} -= 1;
            $self->sync_to_parser();
            ($procsub_node, $procsub_text) = @{$self->{parser}->parse_process_substitution()};
            $self->sync_from_parser();
            if (defined($procsub_node)) {
                $chars->push($procsub_text);
                $was_dollar = 0;
                $was_gtlt = 0;
            } else {
                $chars->push($direction);
                $chars->push($self->advance());
                $was_dollar = 0;
                $was_gtlt = 0;
            }
            next;
        }
        $chars->push($ch);
        $was_dollar = $ch eq "\$";
        $was_gtlt = (index("<>", $ch) >= 0);
    }
    return ""->join_($chars);
}

sub collect_param_argument ($self, $flags, $was_dollar) {
    return $self->parse_matched_pair("{", "}", $flags | MATCHEDPAIRFLAGS_DOLBRACE(), $was_dollar);
}

sub read_word_internal ($self, $ctx, $at_command_start, $in_array_literal, $in_assign_builtin) {
    my $ansi_result0;
    my $ansi_result1;
    my $array_result0;
    my $array_result1;
    my $c;
    my $ch;
    my $cmdsub_result0;
    my $cmdsub_result1;
    my $content;
    my $for_regex;
    my $handle_line_continuation;
    my $in_single_in_dquote;
    my $is_array_assign;
    my $locale_result0;
    my $locale_result1;
    my $locale_result2;
    my $next_c;
    my $next_ch;
    my $prev_char;
    my $procsub_result0;
    my $procsub_result1;
    my $saw_newline;
    my $track_newline;
    my $start = $self->{pos_};
    my $chars = [];
    my $parts = [];
    my $bracket_depth = 0;
    my $bracket_start_pos = -1;
    my $seen_equals = 0;
    my $paren_depth = 0;
    while (!$self->at_end()) {
        $ch = $self->peek();
        if ($ctx == WORD_CTX_REGEX()) {
            if ($ch eq "\\" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "\n") {
                $self->advance();
                $self->advance();
                next;
            }
        }
        if ($ctx != WORD_CTX_NORMAL() && $self->is_word_terminator($ctx, $ch, $bracket_depth, $paren_depth)) {
            last;
        }
        if ($ctx == WORD_CTX_NORMAL() && $ch eq "[") {
            if ($bracket_depth > 0) {
                $bracket_depth += 1;
                $chars->push($self->advance());
                next;
            }
            if ((scalar(@{$chars}) > 0) && $at_command_start && !$seen_equals && is_array_assignment_prefix($chars)) {
                $prev_char = $chars->[-1];
                if (($prev_char =~ /^[a-zA-Z0-9]$/) || $prev_char eq "_") {
                    $bracket_start_pos = $self->{pos_};
                    $bracket_depth += 1;
                    $chars->push($self->advance());
                    next;
                }
            }
            if (!(scalar(@{$chars}) > 0) && !$seen_equals && $in_array_literal) {
                $bracket_start_pos = $self->{pos_};
                $bracket_depth += 1;
                $chars->push($self->advance());
                next;
            }
        }
        if ($ctx == WORD_CTX_NORMAL() && $ch eq "]" && $bracket_depth > 0) {
            $bracket_depth -= 1;
            $chars->push($self->advance());
            next;
        }
        if ($ctx == WORD_CTX_NORMAL() && $ch eq "=" && $bracket_depth == 0) {
            $seen_equals = 1;
        }
        if ($ctx == WORD_CTX_REGEX() && $ch eq "(") {
            $paren_depth += 1;
            $chars->push($self->advance());
            next;
        }
        if ($ctx == WORD_CTX_REGEX() && $ch eq ")") {
            if ($paren_depth > 0) {
                $paren_depth -= 1;
                $chars->push($self->advance());
                next;
            }
            last;
        }
        if (($ctx == WORD_CTX_COND() || $ctx == WORD_CTX_REGEX()) && $ch eq "[") {
            $for_regex = $ctx == WORD_CTX_REGEX();
            if ($self->read_bracket_expression($chars, $parts, $for_regex, $paren_depth)) {
                next;
            }
            $chars->push($self->advance());
            next;
        }
        my $content = "";
        if ($ctx == WORD_CTX_COND() && $ch eq "(") {
            if ($self->{extglob} && (scalar(@{$chars}) > 0) && is_extglob_prefix($chars->[-1])) {
                $chars->push($self->advance());
                $content = $self->parse_matched_pair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB(), 0);
                $chars->push($content);
                $chars->push(")");
                next;
            } else {
                last;
            }
        }
        if ($ctx == WORD_CTX_REGEX() && is_whitespace($ch) && $paren_depth > 0) {
            $chars->push($self->advance());
            next;
        }
        if ($ch eq "'") {
            $self->advance();
            $track_newline = $ctx == WORD_CTX_NORMAL();
            ($content, $saw_newline) = @{$self->read_single_quote($start)};
            $chars->push($content);
            if ($track_newline && $saw_newline && defined($self->{parser})) {
                $self->{parser}->{saw_newline_in_single_quote} = 1;
            }
            next;
        }
        my $cmdsub_result0 = undef;
        my $cmdsub_result1 = "";
        if ($ch eq "\"") {
            $self->advance();
            if ($ctx == WORD_CTX_NORMAL()) {
                $chars->push("\"");
                $in_single_in_dquote = 0;
                while (!$self->at_end() && ($in_single_in_dquote || $self->peek() ne "\"")) {
                    $c = $self->peek();
                    if ($in_single_in_dquote) {
                        $chars->push($self->advance());
                        if ($c eq "'") {
                            $in_single_in_dquote = 0;
                        }
                        next;
                    }
                    if ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        $next_c = $self->{source}->[$self->{pos_} + 1];
                        if ($next_c eq "\n") {
                            $self->advance();
                            $self->advance();
                        } else {
                            $chars->push($self->advance());
                            $chars->push($self->advance());
                        }
                    } elsif ($c eq "\$") {
                        $self->sync_to_parser();
                        if (!$self->{parser}->parse_dollar_expansion($chars, $parts, 1)) {
                            $self->sync_from_parser();
                            $chars->push($self->advance());
                        } else {
                            $self->sync_from_parser();
                        }
                    } elsif ($c eq "`") {
                        $self->sync_to_parser();
                        ($cmdsub_result0, $cmdsub_result1) = @{$self->{parser}->parse_backtick_substitution()};
                        $self->sync_from_parser();
                        if (defined($cmdsub_result0)) {
                            $parts->push($cmdsub_result0);
                            $chars->push($cmdsub_result1);
                        } else {
                            $chars->push($self->advance());
                        }
                    } else {
                        $chars->push($self->advance());
                    }
                }
                if ($self->at_end()) {
                    die "Unterminated double quote";
                }
                $chars->push($self->advance());
            } else {
                $handle_line_continuation = $ctx == WORD_CTX_COND();
                $self->sync_to_parser();
                $self->{parser}->scan_double_quote($chars, $parts, $start, $handle_line_continuation);
                $self->sync_from_parser();
            }
            next;
        }
        if ($ch eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $next_ch = $self->{source}->[$self->{pos_} + 1];
            if ($ctx != WORD_CTX_REGEX() && $next_ch eq "\n") {
                $self->advance();
                $self->advance();
            } else {
                $chars->push($self->advance());
                $chars->push($self->advance());
            }
            next;
        }
        if ($ctx != WORD_CTX_REGEX() && $ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "'") {
            ($ansi_result0, $ansi_result1) = @{$self->read_ansi_c_quote()};
            if (defined($ansi_result0)) {
                $parts->push($ansi_result0);
                $chars->push($ansi_result1);
            } else {
                $chars->push($self->advance());
            }
            next;
        }
        if ($ctx != WORD_CTX_REGEX() && $ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "\"") {
            ($locale_result0, $locale_result1, $locale_result2) = @{$self->read_locale_string()};
            if (defined($locale_result0)) {
                $parts->push($locale_result0);
                $parts->extend($locale_result2);
                $chars->push($locale_result1);
            } else {
                $chars->push($self->advance());
            }
            next;
        }
        if ($ch eq "\$") {
            $self->sync_to_parser();
            if (!$self->{parser}->parse_dollar_expansion($chars, $parts, 0)) {
                $self->sync_from_parser();
                $chars->push($self->advance());
            } else {
                $self->sync_from_parser();
                if ($self->{extglob} && $ctx == WORD_CTX_NORMAL() && (scalar(@{$chars}) > 0) && length($chars->[-1]) == 2 && $chars->[-1]->[0] eq "\$" && ((index("?*\@", $chars->[-1]->[1]) >= 0)) && !$self->at_end() && $self->peek() eq "(") {
                    $chars->push($self->advance());
                    $content = $self->parse_matched_pair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB(), 0);
                    $chars->push($content);
                    $chars->push(")");
                }
            }
            next;
        }
        if ($ctx != WORD_CTX_REGEX() && $ch eq "`") {
            $self->sync_to_parser();
            ($cmdsub_result0, $cmdsub_result1) = @{$self->{parser}->parse_backtick_substitution()};
            $self->sync_from_parser();
            if (defined($cmdsub_result0)) {
                $parts->push($cmdsub_result0);
                $chars->push($cmdsub_result1);
            } else {
                $chars->push($self->advance());
            }
            next;
        }
        if ($ctx != WORD_CTX_REGEX() && is_redirect_char($ch) && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
            $self->sync_to_parser();
            ($procsub_result0, $procsub_result1) = @{$self->{parser}->parse_process_substitution()};
            $self->sync_from_parser();
            if (defined($procsub_result0)) {
                $parts->push($procsub_result0);
                $chars->push($procsub_result1);
            } elsif ((length($procsub_result1) > 0)) {
                $chars->push($procsub_result1);
            } else {
                $chars->push($self->advance());
                if ($ctx == WORD_CTX_NORMAL()) {
                    $chars->push($self->advance());
                }
            }
            next;
        }
        if ($ctx == WORD_CTX_NORMAL() && $ch eq "(" && (scalar(@{$chars}) > 0) && $bracket_depth == 0) {
            $is_array_assign = 0;
            if (scalar(@{$chars}) >= 3 && $chars->[-2] eq "+" && $chars->[-1] eq "=") {
                $is_array_assign = is_array_assignment_prefix([@{$chars}[0 .. scalar(@{$chars}) - 2 - 1]]);
            } elsif ($chars->[-1] eq "=" && scalar(@{$chars}) >= 2) {
                $is_array_assign = is_array_assignment_prefix([@{$chars}[0 .. scalar(@{$chars}) - 1 - 1]]);
            }
            if ($is_array_assign && ($at_command_start || $in_assign_builtin)) {
                $self->sync_to_parser();
                ($array_result0, $array_result1) = @{$self->{parser}->parse_array_literal()};
                $self->sync_from_parser();
                if (defined($array_result0)) {
                    $parts->push($array_result0);
                    $chars->push($array_result1);
                } else {
                    last;
                }
                next;
            }
        }
        if ($self->{extglob} && $ctx == WORD_CTX_NORMAL() && is_extglob_prefix($ch) && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
            $chars->push($self->advance());
            $chars->push($self->advance());
            $content = $self->parse_matched_pair("(", ")", MATCHEDPAIRFLAGS_EXTGLOB(), 0);
            $chars->push($content);
            $chars->push(")");
            next;
        }
        if ($ctx == WORD_CTX_NORMAL() && ($self->{parser_state} & PARSERSTATEFLAGS_PST_EOFTOKEN() ? 1 : 0) && $self->{eof_token} ne "" && $ch eq $self->{eof_token} && $bracket_depth == 0) {
            if (!(scalar(@{$chars}) > 0)) {
                $chars->push($self->advance());
            }
            last;
        }
        if ($ctx == WORD_CTX_NORMAL() && is_metachar($ch) && $bracket_depth == 0) {
            last;
        }
        $chars->push($self->advance());
    }
    if ($bracket_depth > 0 && $bracket_start_pos != -1 && $self->at_end()) {
        die "unexpected EOF looking for `]'";
    }
    if (!(scalar(@{$chars}) > 0)) {
        return undef;
    }
    if ((scalar(@{$parts}) > 0)) {
        return Word->new(""->join_($chars), $parts, "word");
    }
    return Word->new(""->join_($chars), "word");
}

sub read_word ($self) {
    my $start = $self->{pos_};
    if ($self->{pos_} >= $self->{length_}) {
        return undef;
    }
    my $c = $self->peek();
    if ($c eq "") {
        return undef;
    }
    my $is_procsub = ($c eq "<" || $c eq ">") && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(";
    my $is_regex_paren = $self->{word_context} == WORD_CTX_REGEX() && ($c eq "(" || $c eq ")");
    if ($self->is_metachar($c) && !$is_procsub && !$is_regex_paren) {
        return undef;
    }
    my $word = $self->read_word_internal($self->{word_context}, $self->{at_command_start}, $self->{in_array_literal}, $self->{in_assign_builtin});
    if (!defined($word)) {
        return undef;
    }
    return Token->new(TOKENTYPE_WORD(), $word->{value}, $start, $word);
}

sub next_token ($self) {
    my $tok;
    my $tok = undef;
    if (defined($self->{token_cache})) {
        $tok = $self->{token_cache};
        $self->{token_cache} = undef;
        $self->{last_read_token} = $tok;
        return $tok;
    }
    $self->skip_blanks();
    if ($self->at_end()) {
        $tok = Token->new(TOKENTYPE_EOF(), "", $self->{pos_});
        $self->{last_read_token} = $tok;
        return $tok;
    }
    if ($self->{eof_token} ne "" && $self->peek() eq $self->{eof_token} && !($self->{parser_state} & PARSERSTATEFLAGS_PST_CASEPAT() ? 1 : 0) && !($self->{parser_state} & PARSERSTATEFLAGS_PST_EOFTOKEN() ? 1 : 0)) {
        $tok = Token->new(TOKENTYPE_EOF(), "", $self->{pos_});
        $self->{last_read_token} = $tok;
        return $tok;
    }
    while ($self->skip_comment()) {
        $self->skip_blanks();
        if ($self->at_end()) {
            $tok = Token->new(TOKENTYPE_EOF(), "", $self->{pos_});
            $self->{last_read_token} = $tok;
            return $tok;
        }
        if ($self->{eof_token} ne "" && $self->peek() eq $self->{eof_token} && !($self->{parser_state} & PARSERSTATEFLAGS_PST_CASEPAT() ? 1 : 0) && !($self->{parser_state} & PARSERSTATEFLAGS_PST_EOFTOKEN() ? 1 : 0)) {
            $tok = Token->new(TOKENTYPE_EOF(), "", $self->{pos_});
            $self->{last_read_token} = $tok;
            return $tok;
        }
    }
    $tok = $self->read_operator();
    if (defined($tok)) {
        $self->{last_read_token} = $tok;
        return $tok;
    }
    $tok = $self->read_word();
    if (defined($tok)) {
        $self->{last_read_token} = $tok;
        return $tok;
    }
    $tok = Token->new(TOKENTYPE_EOF(), "", $self->{pos_});
    $self->{last_read_token} = $tok;
    return $tok;
}

sub peek_token ($self) {
    my $saved_last;
    if (!defined($self->{token_cache})) {
        $saved_last = $self->{last_read_token};
        $self->{token_cache} = $self->next_token();
        $self->{last_read_token} = $saved_last;
    }
    return $self->{token_cache};
}

sub read_ansi_c_quote ($self) {
    my $ch;
    if ($self->at_end() || $self->peek() ne "\$") {
        return [undef, ""];
    }
    if ($self->{pos_} + 1 >= $self->{length_} || $self->{source}->[$self->{pos_} + 1] ne "'") {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    $self->advance();
    $self->advance();
    my $content_chars = [];
    my $found_close = 0;
    while (!$self->at_end()) {
        $ch = $self->peek();
        if ($ch eq "'") {
            $self->advance();
            $found_close = 1;
            last;
        } elsif ($ch eq "\\") {
            $content_chars->push($self->advance());
            if (!$self->at_end()) {
                $content_chars->push($self->advance());
            }
        } else {
            $content_chars->push($self->advance());
        }
    }
    if (!$found_close) {
        die "unexpected EOF while looking for matching `''";
    }
    my $text = substring($self->{source}, $start, $self->{pos_});
    my $content = ""->join_($content_chars);
    my $node = AnsiCQuote->new($content, "ansi-c");
    return [$node, $text];
}

sub sync_to_parser ($self) {
    if (defined($self->{parser})) {
        $self->{parser}->{pos_} = $self->{pos_};
    }
}

sub sync_from_parser ($self) {
    if (defined($self->{parser})) {
        $self->{pos_} = $self->{parser}->{pos_};
    }
}

sub read_locale_string ($self) {
    my $arith_node;
    my $arith_text;
    my $ch;
    my $cmdsub_node;
    my $cmdsub_text;
    my $next_ch;
    my $param_node;
    my $param_text;
    if ($self->at_end() || $self->peek() ne "\$") {
        return [undef, "", []];
    }
    if ($self->{pos_} + 1 >= $self->{length_} || $self->{source}->[$self->{pos_} + 1] ne "\"") {
        return [undef, "", []];
    }
    my $start = $self->{pos_};
    $self->advance();
    $self->advance();
    my $content_chars = [];
    my $inner_parts = [];
    my $found_close = 0;
    while (!$self->at_end()) {
        $ch = $self->peek();
        if ($ch eq "\"") {
            $self->advance();
            $found_close = 1;
            last;
        } elsif ($ch eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $next_ch = $self->{source}->[$self->{pos_} + 1];
            if ($next_ch eq "\n") {
                $self->advance();
                $self->advance();
            } else {
                $content_chars->push($self->advance());
                $content_chars->push($self->advance());
            }
        } elsif ($ch eq "\$" && $self->{pos_} + 2 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(" && $self->{source}->[$self->{pos_} + 2] eq "(") {
            $self->sync_to_parser();
            ($arith_node, $arith_text) = @{$self->{parser}->parse_arithmetic_expansion()};
            $self->sync_from_parser();
            if (defined($arith_node)) {
                $inner_parts->push($arith_node);
                $content_chars->push($arith_text);
            } else {
                $self->sync_to_parser();
                ($cmdsub_node, $cmdsub_text) = @{$self->{parser}->parse_command_substitution()};
                $self->sync_from_parser();
                if (defined($cmdsub_node)) {
                    $inner_parts->push($cmdsub_node);
                    $content_chars->push($cmdsub_text);
                } else {
                    $content_chars->push($self->advance());
                }
            }
        } elsif (is_expansion_start($self->{source}, $self->{pos_}, "\$(")) {
            $self->sync_to_parser();
            ($cmdsub_node, $cmdsub_text) = @{$self->{parser}->parse_command_substitution()};
            $self->sync_from_parser();
            if (defined($cmdsub_node)) {
                $inner_parts->push($cmdsub_node);
                $content_chars->push($cmdsub_text);
            } else {
                $content_chars->push($self->advance());
            }
        } elsif ($ch eq "\$") {
            $self->sync_to_parser();
            ($param_node, $param_text) = @{$self->{parser}->parse_param_expansion(0)};
            $self->sync_from_parser();
            if (defined($param_node)) {
                $inner_parts->push($param_node);
                $content_chars->push($param_text);
            } else {
                $content_chars->push($self->advance());
            }
        } elsif ($ch eq "`") {
            $self->sync_to_parser();
            ($cmdsub_node, $cmdsub_text) = @{$self->{parser}->parse_backtick_substitution()};
            $self->sync_from_parser();
            if (defined($cmdsub_node)) {
                $inner_parts->push($cmdsub_node);
                $content_chars->push($cmdsub_text);
            } else {
                $content_chars->push($self->advance());
            }
        } else {
            $content_chars->push($self->advance());
        }
    }
    if (!$found_close) {
        $self->{pos_} = $start;
        return [undef, "", []];
    }
    my $content = ""->join_($content_chars);
    my $text = "\$\"" . $content . "\"";
    return [LocaleString->new($content, "locale"), $text, $inner_parts];
}

sub update_dolbrace_for_op ($self, $op, $has_param) {
    if ($self->{dolbrace_state} == DOLBRACESTATE_NONE()) {
        return;
    }
    if ($op eq "" || length($op) == 0) {
        return;
    }
    my $first_char = $op->[0];
    if ($self->{dolbrace_state} == DOLBRACESTATE_PARAM() && $has_param) {
        if ((index("%#^,", $first_char) >= 0)) {
            $self->{dolbrace_state} = DOLBRACESTATE_QUOTE();
            return;
        }
        if ($first_char eq "/") {
            $self->{dolbrace_state} = DOLBRACESTATE_QUOTE2();
            return;
        }
    }
    if ($self->{dolbrace_state} == DOLBRACESTATE_PARAM()) {
        if ((index("#%^,~:-=?+/", $first_char) >= 0)) {
            $self->{dolbrace_state} = DOLBRACESTATE_OP();
        }
    }
}

sub consume_param_operator ($self) {
    my $next_ch;
    if ($self->at_end()) {
        return "";
    }
    my $ch = $self->peek();
    my $next_ch = "";
    if ($ch eq ":") {
        $self->advance();
        if ($self->at_end()) {
            return ":";
        }
        $next_ch = $self->peek();
        if (is_simple_param_op($next_ch)) {
            $self->advance();
            return ":" . $next_ch;
        }
        return ":";
    }
    if (is_simple_param_op($ch)) {
        $self->advance();
        return $ch;
    }
    if ($ch eq "#") {
        $self->advance();
        if (!$self->at_end() && $self->peek() eq "#") {
            $self->advance();
            return "##";
        }
        return "#";
    }
    if ($ch eq "%") {
        $self->advance();
        if (!$self->at_end() && $self->peek() eq "%") {
            $self->advance();
            return "%%";
        }
        return "%";
    }
    if ($ch eq "/") {
        $self->advance();
        if (!$self->at_end()) {
            $next_ch = $self->peek();
            if ($next_ch eq "/") {
                $self->advance();
                return "//";
            } elsif ($next_ch eq "#") {
                $self->advance();
                return "/#";
            } elsif ($next_ch eq "%") {
                $self->advance();
                return "/%";
            }
        }
        return "/";
    }
    if ($ch eq "^") {
        $self->advance();
        if (!$self->at_end() && $self->peek() eq "^") {
            $self->advance();
            return "^^";
        }
        return "^";
    }
    if ($ch eq ",") {
        $self->advance();
        if (!$self->at_end() && $self->peek() eq ",") {
            $self->advance();
            return ",,";
        }
        return ",";
    }
    if ($ch eq "\@") {
        $self->advance();
        return "\@";
    }
    return "";
}

sub param_subscript_has_close ($self, $start_pos) {
    my $c;
    my $depth = 1;
    my $i = $start_pos + 1;
    my $quote = new_quote_state();
    while ($i < $self->{length_}) {
        $c = $self->{source}->[$i];
        if ($quote->{single}) {
            if ($c eq "'") {
                $quote->{single} = 0;
            }
            $i += 1;
            next;
        }
        if ($quote->{double}) {
            if ($c eq "\\" && $i + 1 < $self->{length_}) {
                $i += 2;
                next;
            }
            if ($c eq "\"") {
                $quote->{double} = 0;
            }
            $i += 1;
            next;
        }
        if ($c eq "'") {
            $quote->{single} = 1;
            $i += 1;
            next;
        }
        if ($c eq "\"") {
            $quote->{double} = 1;
            $i += 1;
            next;
        }
        if ($c eq "\\") {
            $i += 2;
            next;
        }
        if ($c eq "}") {
            return 0;
        }
        if ($c eq "[") {
            $depth += 1;
        } elsif ($c eq "]") {
            $depth -= 1;
            if ($depth == 0) {
                return 1;
            }
        }
        $i += 1;
    }
    return 0;
}

sub consume_param_name ($self) {
    my $c;
    my $content;
    my $name_chars;
    if ($self->at_end()) {
        return "";
    }
    my $ch = $self->peek();
    if (is_special_param($ch)) {
        if ($ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && ((index("{'\"", $self->{source}->[$self->{pos_} + 1]) >= 0))) {
            return "";
        }
        $self->advance();
        return $ch;
    }
    if (($ch =~ /^\d$/)) {
        my $name_chars = [];
        while (!$self->at_end() && ($self->peek() =~ /^\d$/)) {
            $name_chars->push($self->advance());
        }
        return ""->join_($name_chars);
    }
    if (($ch =~ /^[a-zA-Z]$/) || $ch eq "_") {
        $name_chars = [];
        while (!$self->at_end()) {
            $c = $self->peek();
            if (($c =~ /^[a-zA-Z0-9]$/) || $c eq "_") {
                $name_chars->push($self->advance());
            } elsif ($c eq "[") {
                if (!$self->param_subscript_has_close($self->{pos_})) {
                    last;
                }
                $name_chars->push($self->advance());
                $content = $self->parse_matched_pair("[", "]", MATCHEDPAIRFLAGS_ARRAYSUB(), 0);
                $name_chars->push($content);
                $name_chars->push("]");
                last;
            } else {
                last;
            }
        }
        if ((scalar(@{$name_chars}) > 0)) {
            return ""->join_($name_chars);
        } else {
            return "";
        }
    }
    return "";
}

sub read_param_expansion ($self, $in_dquote) {
    my $c;
    my $name;
    my $name_start;
    my $text;
    if ($self->at_end() || $self->peek() ne "\$") {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    $self->advance();
    if ($self->at_end()) {
        $self->{pos_} = $start;
        return [undef, ""];
    }
    my $ch = $self->peek();
    if ($ch eq "{") {
        $self->advance();
        return $self->read_braced_param($start, $in_dquote);
    }
    my $text = "";
    if (is_special_param_unbraced($ch) || is_digit($ch) || $ch eq "#") {
        $self->advance();
        $text = substring($self->{source}, $start, $self->{pos_});
        return [ParamExpansion->new($ch, "param"), $text];
    }
    if (($ch =~ /^[a-zA-Z]$/) || $ch eq "_") {
        $name_start = $self->{pos_};
        while (!$self->at_end()) {
            $c = $self->peek();
            if (($c =~ /^[a-zA-Z0-9]$/) || $c eq "_") {
                $self->advance();
            } else {
                last;
            }
        }
        $name = substring($self->{source}, $name_start, $self->{pos_});
        $text = substring($self->{source}, $start, $self->{pos_});
        return [ParamExpansion->new($name, "param"), $text];
    }
    $self->{pos_} = $start;
    return [undef, ""];
}

sub read_braced_param ($self, $start, $in_dquote) {
    my $arg;
    my $backtick_pos;
    my $bc;
    my $content;
    my $dollar_count;
    my $flags;
    my $formatted;
    my $inner;
    my $next_c;
    my $op;
    my $param;
    my $param_ends_with_dollar;
    my $parsed;
    my $sub_parser;
    my $suffix;
    my $text;
    my $trailing;
    if ($self->at_end()) {
        die "unexpected EOF looking for `}'";
    }
    my $saved_dolbrace = $self->{dolbrace_state};
    $self->{dolbrace_state} = DOLBRACESTATE_PARAM();
    my $ch = $self->peek();
    if (is_funsub_char($ch)) {
        $self->{dolbrace_state} = $saved_dolbrace;
        return $self->read_funsub($start);
    }
    my $param = "";
    my $text = "";
    if ($ch eq "#") {
        $self->advance();
        $param = $self->consume_param_name();
        if ((length($param) > 0) && !$self->at_end() && $self->peek() eq "}") {
            $self->advance();
            $text = substring($self->{source}, $start, $self->{pos_});
            $self->{dolbrace_state} = $saved_dolbrace;
            return [ParamLength->new($param, "param-len"), $text];
        }
        $self->{pos_} = $start + 2;
    }
    my $op = "";
    my $arg = "";
    if ($ch eq "!") {
        $self->advance();
        while (!$self->at_end() && is_whitespace_no_newline($self->peek())) {
            $self->advance();
        }
        $param = $self->consume_param_name();
        if ((length($param) > 0)) {
            while (!$self->at_end() && is_whitespace_no_newline($self->peek())) {
                $self->advance();
            }
            if (!$self->at_end() && $self->peek() eq "}") {
                $self->advance();
                $text = substring($self->{source}, $start, $self->{pos_});
                $self->{dolbrace_state} = $saved_dolbrace;
                return [ParamIndirect->new($param, "param-indirect"), $text];
            }
            if (!$self->at_end() && is_at_or_star($self->peek())) {
                $suffix = $self->advance();
                $trailing = $self->parse_matched_pair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE(), 0);
                $text = substring($self->{source}, $start, $self->{pos_});
                $self->{dolbrace_state} = $saved_dolbrace;
                return [ParamIndirect->new($param . $suffix . $trailing, "param-indirect"), $text];
            }
            $op = $self->consume_param_operator();
            if ($op eq "" && !$self->at_end() && ((index("}\"'`", $self->peek()) == -1))) {
                $op = $self->advance();
            }
            if ($op ne "" && ((index("\"'`", $op) == -1))) {
                $arg = $self->parse_matched_pair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE(), 0);
                $text = substring($self->{source}, $start, $self->{pos_});
                $self->{dolbrace_state} = $saved_dolbrace;
                return [ParamIndirect->new($param, $op, $arg, "param-indirect"), $text];
            }
            if ($self->at_end()) {
                $self->{dolbrace_state} = $saved_dolbrace;
                die "unexpected EOF looking for `}'";
            }
            $self->{pos_} = $start + 2;
        } else {
            $self->{pos_} = $start + 2;
        }
    }
    $param = $self->consume_param_name();
    if (!(length($param) > 0)) {
        if (!$self->at_end() && (((index("-=+?", $self->peek()) >= 0)) || $self->peek() eq ":" && $self->{pos_} + 1 < $self->{length_} && is_simple_param_op($self->{source}->[$self->{pos_} + 1]))) {
            $param = "";
        } else {
            $content = $self->parse_matched_pair("{", "}", MATCHEDPAIRFLAGS_DOLBRACE(), 0);
            $text = "\${" . $content . "}";
            $self->{dolbrace_state} = $saved_dolbrace;
            return [ParamExpansion->new($content, "param"), $text];
        }
    }
    if ($self->at_end()) {
        $self->{dolbrace_state} = $saved_dolbrace;
        die "unexpected EOF looking for `}'";
    }
    if ($self->peek() eq "}") {
        $self->advance();
        $text = substring($self->{source}, $start, $self->{pos_});
        $self->{dolbrace_state} = $saved_dolbrace;
        return [ParamExpansion->new($param, "param"), $text];
    }
    $op = $self->consume_param_operator();
    if ($op eq "") {
        if (!$self->at_end() && $self->peek() eq "\$" && $self->{pos_} + 1 < $self->{length_} && ($self->{source}->[$self->{pos_} + 1] eq "\"" || $self->{source}->[$self->{pos_} + 1] eq "'")) {
            $dollar_count = 1 + count_consecutive_dollars_before($self->{source}, $self->{pos_});
            if ($dollar_count % 2 == 1) {
                $op = "";
            } else {
                $op = $self->advance();
            }
        } elsif (!$self->at_end() && $self->peek() eq "`") {
            $backtick_pos = $self->{pos_};
            $self->advance();
            while (!$self->at_end() && $self->peek() ne "`") {
                $bc = $self->peek();
                if ($bc eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                    $next_c = $self->{source}->[$self->{pos_} + 1];
                    if (is_escape_char_in_backtick($next_c)) {
                        $self->advance();
                    }
                }
                $self->advance();
            }
            if ($self->at_end()) {
                $self->{dolbrace_state} = $saved_dolbrace;
                die "Unterminated backtick";
            }
            $self->advance();
            $op = "`";
        } elsif (!$self->at_end() && $self->peek() eq "\$" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "{") {
            $op = "";
        } elsif (!$self->at_end() && ($self->peek() eq "'" || $self->peek() eq "\"")) {
            $op = "";
        } elsif (!$self->at_end() && $self->peek() eq "\\") {
            $op = $self->advance();
            if (!$self->at_end()) {
                $op .= $self->advance();
            }
        } else {
            $op = $self->advance();
        }
    }
    $self->update_dolbrace_for_op($op, length($param) > 0);
    eval {
        $flags = ($in_dquote ? MATCHEDPAIRFLAGS_DQUOTE() : MATCHEDPAIRFLAGS_NONE());
        $param_ends_with_dollar = $param ne "" && $param->endswith("\$");
        $arg = $self->collect_param_argument($flags, $param_ends_with_dollar);
    };
    if (my $e = $@) {
        $self->{dolbrace_state} = $saved_dolbrace;
        die $e;
    }
    if (($op eq "<" || $op eq ">") && $arg->startswith("(") && $arg->endswith(")")) {
        $inner = substr($arg, 1, length($arg) - 1 - 1);
        eval {
            $sub_parser = new_parser($inner, 1, $self->{parser}->{extglob});
            $parsed = $sub_parser->parse_list(1);
            if (defined($parsed) && $sub_parser->at_end()) {
                $formatted = format_cmdsub_node($parsed, 0, 1, 0, 1);
                $arg = "(" . $formatted . ")";
            }
        };
        if (my $_e = $@) {
        }
    }
    $text = "\${" . $param . $op . $arg . "}";
    $self->{dolbrace_state} = $saved_dolbrace;
    return [ParamExpansion->new($param, $op, $arg, "param"), $text];
}

sub read_funsub ($self, $start) {
    return $self->{parser}->parse_funsub($start);
}

1;

package Word;

sub new ($class, $value, $parts, $kind) {
    return bless { value => $value, parts => $parts, kind => $kind }, $class;
}

sub value ($self) { $self->{value} }
sub parts ($self) { $self->{parts} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $value = $self->{value};
    $value = $self->expand_all_ansi_c_quotes($value);
    $value = $self->strip_locale_string_dollars($value);
    $value = $self->normalize_array_whitespace($value);
    $value = $self->format_command_substitutions($value, 0);
    $value = $self->normalize_param_expansion_newlines($value);
    $value = $self->strip_arith_line_continuations($value);
    $value = $self->double_ctlesc_smart($value);
    $value = $value->replace("", "");
    $value = $value->replace("\\", "\\\\");
    if ($value->endswith("\\\\") && !$value->endswith("\\\\\\\\")) {
        $value = $value . "\\\\";
    }
    my $escaped = $value->replace("\"", "\\\"")->replace("\n", "\\n")->replace("\t", "\\t");
    return "(word \"" . $escaped . "\")";
}

sub append_with_ctlesc ($self, $result, $byte_val) {
    $result->append($byte_val);
}

sub double_ctlesc_smart ($self, $value) {
    my $bs_count;
    my $result = [];
    my $quote = new_quote_state();
    for my $c (@{$value}) {
        if ($c == "'" && !$quote->{double}) {
            $quote->{single} = !$quote->{single};
        } elsif ($c == "\"" && !$quote->{single}) {
            $quote->{double} = !$quote->{double};
        }
        $result->push($c);
        if ($c == "") {
            if ($quote->{double}) {
                $bs_count = 0;
                for (my $j = scalar(@{$result}) - 2; $j > -1; $j += -1) {
                    if ($result->[$j] eq "\\") {
                        $bs_count += 1;
                    } else {
                        last;
                    }
                }
                if ($bs_count % 2 == 0) {
                    $result->push("");
                }
            } else {
                $result->push("");
            }
        }
    }
    return ""->join_($result);
}

sub normalize_param_expansion_newlines ($self, $value) {
    my $c;
    my $ch;
    my $depth;
    my $had_leading_newline;
    my $result = [];
    my $i = 0;
    my $quote = new_quote_state();
    while ($i < length($value)) {
        $c = $value->[$i];
        if ($c eq "'" && !$quote->{double}) {
            $quote->{single} = !$quote->{single};
            $result->push($c);
            $i += 1;
        } elsif ($c eq "\"" && !$quote->{single}) {
            $quote->{double} = !$quote->{double};
            $result->push($c);
            $i += 1;
        } elsif (is_expansion_start($value, $i, "\${") && !$quote->{single}) {
            $result->push("\$");
            $result->push("{");
            $i += 2;
            $had_leading_newline = $i < length($value) && $value->[$i] eq "\n";
            if ($had_leading_newline) {
                $result->push(" ");
                $i += 1;
            }
            $depth = 1;
            while ($i < length($value) && $depth > 0) {
                $ch = $value->[$i];
                if ($ch eq "\\" && $i + 1 < length($value) && !$quote->{single}) {
                    if ($value->[$i + 1] eq "\n") {
                        $i += 2;
                        next;
                    }
                    $result->push($ch);
                    $result->push($value->[$i + 1]);
                    $i += 2;
                    next;
                }
                if ($ch eq "'" && !$quote->{double}) {
                    $quote->{single} = !$quote->{single};
                } elsif ($ch eq "\"" && !$quote->{single}) {
                    $quote->{double} = !$quote->{double};
                } elsif (!$quote->in_quotes()) {
                    if ($ch eq "{") {
                        $depth += 1;
                    } elsif ($ch eq "}") {
                        $depth -= 1;
                        if ($depth == 0) {
                            if ($had_leading_newline) {
                                $result->push(" ");
                            }
                            $result->push($ch);
                            $i += 1;
                            last;
                        }
                    }
                }
                $result->push($ch);
                $i += 1;
            }
        } else {
            $result->push($c);
            $i += 1;
        }
    }
    return ""->join_($result);
}

sub sh_single_quote ($self, $s_) {
    if (!(length($s_) > 0)) {
        return "''";
    }
    if ($s_ eq "'") {
        return "\\'";
    }
    my $result = ["'"];
    for my $c (@{$s_}) {
        if ($c == "'") {
            $result->push("'\\''");
        } else {
            $result->push($c);
        }
    }
    $result->push("'");
    return ""->join_($result);
}

sub ansi_c_to_bytes ($self, $inner) {
    my $byte_val;
    my $c;
    my $codepoint;
    my $ctrl_char;
    my $ctrl_val;
    my $hex_str;
    my $j;
    my $simple;
    my $skip_extra;
    my $result = [];
    my $i = 0;
    while ($i < length($inner)) {
        if ($inner->[$i] eq "\\" && $i + 1 < length($inner)) {
            $c = $inner->[$i + 1];
            $simple = get_ansi_escape($c);
            if ($simple >= 0) {
                $result->push($simple);
                $i += 2;
            } elsif ($c eq "'") {
                $result->push(39);
                $i += 2;
            } elsif ($c eq "x") {
                if ($i + 2 < length($inner) && $inner->[$i + 2] eq "{") {
                    $j = $i + 3;
                    while ($j < length($inner) && is_hex_digit($inner->[$j])) {
                        $j += 1;
                    }
                    $hex_str = substring($inner, $i + 3, $j);
                    if ($j < length($inner) && $inner->[$j] eq "}") {
                        $j += 1;
                    }
                    if (!(length($hex_str) > 0)) {
                        return $result;
                    }
                    $byte_val = hex($hex_str) & 255;
                    if ($byte_val == 0) {
                        return $result;
                    }
                    $self->append_with_ctlesc($result, $byte_val);
                    $i = $j;
                } else {
                    $j = $i + 2;
                    while ($j < length($inner) && $j < $i + 4 && is_hex_digit($inner->[$j])) {
                        $j += 1;
                    }
                    if ($j > $i + 2) {
                        $byte_val = hex(substring($inner, $i + 2, $j));
                        if ($byte_val == 0) {
                            return $result;
                        }
                        $self->append_with_ctlesc($result, $byte_val);
                        $i = $j;
                    } else {
                        $result->push(ord($inner->[$i]->[0]));
                        $i += 1;
                    }
                }
            } elsif ($c eq "u") {
                $j = $i + 2;
                while ($j < length($inner) && $j < $i + 6 && is_hex_digit($inner->[$j])) {
                    $j += 1;
                }
                if ($j > $i + 2) {
                    $codepoint = hex(substring($inner, $i + 2, $j));
                    if ($codepoint == 0) {
                        return $result;
                    }
                    $result->extend([unpack('C*', chr($codepoint))]);
                    $i = $j;
                } else {
                    $result->push(ord($inner->[$i]->[0]));
                    $i += 1;
                }
            } elsif ($c eq "U") {
                $j = $i + 2;
                while ($j < length($inner) && $j < $i + 10 && is_hex_digit($inner->[$j])) {
                    $j += 1;
                }
                if ($j > $i + 2) {
                    $codepoint = hex(substring($inner, $i + 2, $j));
                    if ($codepoint == 0) {
                        return $result;
                    }
                    $result->extend([unpack('C*', chr($codepoint))]);
                    $i = $j;
                } else {
                    $result->push(ord($inner->[$i]->[0]));
                    $i += 1;
                }
            } elsif ($c eq "c") {
                if ($i + 3 <= length($inner)) {
                    $ctrl_char = $inner->[$i + 2];
                    $skip_extra = 0;
                    if ($ctrl_char eq "\\" && $i + 4 <= length($inner) && $inner->[$i + 3] eq "\\") {
                        $skip_extra = 1;
                    }
                    $ctrl_val = ord($ctrl_char->[0]) & 31;
                    if ($ctrl_val == 0) {
                        return $result;
                    }
                    $self->append_with_ctlesc($result, $ctrl_val);
                    $i += 3 + $skip_extra;
                } else {
                    $result->push(ord($inner->[$i]->[0]));
                    $i += 1;
                }
            } elsif ($c eq "0") {
                $j = $i + 2;
                while ($j < length($inner) && $j < $i + 4 && is_octal_digit($inner->[$j])) {
                    $j += 1;
                }
                if ($j > $i + 2) {
                    $byte_val = oct(substring($inner, $i + 1, $j)) & 255;
                    if ($byte_val == 0) {
                        return $result;
                    }
                    $self->append_with_ctlesc($result, $byte_val);
                    $i = $j;
                } else {
                    return $result;
                }
            } elsif ($c ge "1" && $c le "7") {
                $j = $i + 1;
                while ($j < length($inner) && $j < $i + 4 && is_octal_digit($inner->[$j])) {
                    $j += 1;
                }
                $byte_val = oct(substring($inner, $i + 1, $j)) & 255;
                if ($byte_val == 0) {
                    return $result;
                }
                $self->append_with_ctlesc($result, $byte_val);
                $i = $j;
            } else {
                $result->push(92);
                $result->push(ord($c->[0]));
                $i += 2;
            }
        } else {
            $result->extend([unpack('C*', $inner->[$i])]);
            $i += 1;
        }
    }
    return $result;
}

sub expand_ansi_c_escapes ($self, $value) {
    if (!($value->startswith("'") && $value->endswith("'"))) {
        return $value;
    }
    my $inner = substring($value, 1, length($value) - 1);
    my $literal_bytes = $self->ansi_c_to_bytes($inner);
    my $literal_str = pack("C*", @{$literal_bytes});
    return $self->sh_single_quote($literal_str);
}

sub expand_all_ansi_c_quotes ($self, $value) {
    my $after_brace;
    my $ansi_str;
    my $c;
    my $ch;
    my $effective_in_dquote;
    my $expanded;
    my $first_char;
    my $in_pattern;
    my $inner;
    my $is_ansi_c;
    my $j;
    my $last_brace_idx;
    my $op_start;
    my $outer_in_dquote;
    my $rest;
    my $result_str;
    my $var_name_len;
    my $result = [];
    my $i = 0;
    my $quote = new_quote_state();
    my $in_backtick = 0;
    my $brace_depth = 0;
    while ($i < length($value)) {
        $ch = $value->[$i];
        if ($ch eq "`" && !$quote->{single}) {
            $in_backtick = !$in_backtick;
            $result->push($ch);
            $i += 1;
            next;
        }
        if ($in_backtick) {
            if ($ch eq "\\" && $i + 1 < length($value)) {
                $result->push($ch);
                $result->push($value->[$i + 1]);
                $i += 2;
            } else {
                $result->push($ch);
                $i += 1;
            }
            next;
        }
        if (!$quote->{single}) {
            if (is_expansion_start($value, $i, "\${")) {
                $brace_depth += 1;
                $quote->push_();
                $result->push("\${");
                $i += 2;
                next;
            } elsif ($ch eq "}" && $brace_depth > 0 && !$quote->{double}) {
                $brace_depth -= 1;
                $result->push($ch);
                $quote->pop_();
                $i += 1;
                next;
            }
        }
        $effective_in_dquote = $quote->{double};
        if ($ch eq "'" && !$effective_in_dquote) {
            $is_ansi_c = !$quote->{single} && $i > 0 && $value->[$i - 1] eq "\$" && count_consecutive_dollars_before($value, $i - 1) % 2 == 0;
            if (!$is_ansi_c) {
                $quote->{single} = !$quote->{single};
            }
            $result->push($ch);
            $i += 1;
        } elsif ($ch eq "\"" && !$quote->{single}) {
            $quote->{double} = !$quote->{double};
            $result->push($ch);
            $i += 1;
        } elsif ($ch eq "\\" && $i + 1 < length($value) && !$quote->{single}) {
            $result->push($ch);
            $result->push($value->[$i + 1]);
            $i += 2;
        } elsif (starts_with_at($value, $i, "\$'") && !$quote->{single} && !$effective_in_dquote && count_consecutive_dollars_before($value, $i) % 2 == 0) {
            $j = $i + 2;
            while ($j < length($value)) {
                if ($value->[$j] eq "\\" && $j + 1 < length($value)) {
                    $j += 2;
                } elsif ($value->[$j] eq "'") {
                    $j += 1;
                    last;
                } else {
                    $j += 1;
                }
            }
            $ansi_str = substring($value, $i, $j);
            $expanded = $self->expand_ansi_c_escapes(substring($ansi_str, 1, length($ansi_str)));
            $outer_in_dquote = $quote->outer_double();
            if ($brace_depth > 0 && $outer_in_dquote && $expanded->startswith("'") && $expanded->endswith("'")) {
                $inner = substring($expanded, 1, length($expanded) - 1);
                if ($inner->find("") == -1) {
                    $result_str = ""->join_($result);
                    $in_pattern = 0;
                    $last_brace_idx = $result_str->rfind("\${");
                    if ($last_brace_idx >= 0) {
                        $after_brace = substr($result_str, $last_brace_idx + 2);
                        $var_name_len = 0;
                        if ((length($after_brace) > 0)) {
                            if ((index("\@*#?-\$!0123456789_", $after_brace->[0]) >= 0)) {
                                $var_name_len = 1;
                            } elsif (($after_brace->[0] =~ /^[a-zA-Z]$/) || $after_brace->[0] eq "_") {
                                while ($var_name_len < length($after_brace)) {
                                    $c = $after_brace->[$var_name_len];
                                    if (!(($c =~ /^[a-zA-Z0-9]$/) || $c eq "_")) {
                                        last;
                                    }
                                    $var_name_len += 1;
                                }
                            }
                        }
                        if ($var_name_len > 0 && $var_name_len < length($after_brace) && ((index("#?-", $after_brace->[0]) == -1))) {
                            $op_start = substr($after_brace, $var_name_len);
                            if ($op_start->startswith("\@") && length($op_start) > 1) {
                                $op_start = substr($op_start, 1);
                            }
                            for my $op (@{["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]}) {
                                if ($op_start->startswith($op)) {
                                    $in_pattern = 1;
                                    last;
                                }
                            }
                            if (!$in_pattern && (length($op_start) > 0) && ((index("%#/^,~:+-=?", $op_start->[0]) == -1))) {
                                for my $op (@{["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]}) {
                                    if ((index($op_start, $op) >= 0)) {
                                        $in_pattern = 1;
                                        last;
                                    }
                                }
                            }
                        } elsif ($var_name_len == 0 && length($after_brace) > 1) {
                            $first_char = $after_brace->[0];
                            if ((index("%#/^,", $first_char) == -1)) {
                                $rest = substr($after_brace, 1);
                                for my $op (@{["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]}) {
                                    if ((index($rest, $op) >= 0)) {
                                        $in_pattern = 1;
                                        last;
                                    }
                                }
                            }
                        }
                    }
                    if (!$in_pattern) {
                        $expanded = $inner;
                    }
                }
            }
            $result->push($expanded);
            $i = $j;
        } else {
            $result->push($ch);
            $i += 1;
        }
    }
    return ""->join_($result);
}

sub strip_locale_string_dollars ($self, $value) {
    my $ch;
    my $dollar_count;
    my $result = [];
    my $i = 0;
    my $brace_depth = 0;
    my $bracket_depth = 0;
    my $quote = new_quote_state();
    my $brace_quote = new_quote_state();
    my $bracket_in_double_quote = 0;
    while ($i < length($value)) {
        $ch = $value->[$i];
        if ($ch eq "\\" && $i + 1 < length($value) && !$quote->{single} && !$brace_quote->{single}) {
            $result->push($ch);
            $result->push($value->[$i + 1]);
            $i += 2;
        } elsif (starts_with_at($value, $i, "\${") && !$quote->{single} && !$brace_quote->{single} && ($i == 0 || $value->[$i - 1] ne "\$")) {
            $brace_depth += 1;
            $brace_quote->{double} = 0;
            $brace_quote->{single} = 0;
            $result->push("\$");
            $result->push("{");
            $i += 2;
        } elsif ($ch eq "}" && $brace_depth > 0 && !$quote->{single} && !$brace_quote->{double} && !$brace_quote->{single}) {
            $brace_depth -= 1;
            $result->push($ch);
            $i += 1;
        } elsif ($ch eq "[" && $brace_depth > 0 && !$quote->{single} && !$brace_quote->{double}) {
            $bracket_depth += 1;
            $bracket_in_double_quote = 0;
            $result->push($ch);
            $i += 1;
        } elsif ($ch eq "]" && $bracket_depth > 0 && !$quote->{single} && !$bracket_in_double_quote) {
            $bracket_depth -= 1;
            $result->push($ch);
            $i += 1;
        } elsif ($ch eq "'" && !$quote->{double} && $brace_depth == 0) {
            $quote->{single} = !$quote->{single};
            $result->push($ch);
            $i += 1;
        } elsif ($ch eq "\"" && !$quote->{single} && $brace_depth == 0) {
            $quote->{double} = !$quote->{double};
            $result->push($ch);
            $i += 1;
        } elsif ($ch eq "\"" && !$quote->{single} && $bracket_depth > 0) {
            $bracket_in_double_quote = !$bracket_in_double_quote;
            $result->push($ch);
            $i += 1;
        } elsif ($ch eq "\"" && !$quote->{single} && !$brace_quote->{single} && $brace_depth > 0) {
            $brace_quote->{double} = !$brace_quote->{double};
            $result->push($ch);
            $i += 1;
        } elsif ($ch eq "'" && !$quote->{double} && !$brace_quote->{double} && $brace_depth > 0) {
            $brace_quote->{single} = !$brace_quote->{single};
            $result->push($ch);
            $i += 1;
        } elsif (starts_with_at($value, $i, "\$\"") && !$quote->{single} && !$brace_quote->{single} && ($brace_depth > 0 || $bracket_depth > 0 || !$quote->{double}) && !$brace_quote->{double} && !$bracket_in_double_quote) {
            $dollar_count = 1 + count_consecutive_dollars_before($value, $i);
            if ($dollar_count % 2 == 1) {
                $result->push("\"");
                if ($bracket_depth > 0) {
                    $bracket_in_double_quote = 1;
                } elsif ($brace_depth > 0) {
                    $brace_quote->{double} = 1;
                } else {
                    $quote->{double} = 1;
                }
                $i += 2;
            } else {
                $result->push($ch);
                $i += 1;
            }
        } else {
            $result->push($ch);
            $i += 1;
        }
    }
    return ""->join_($result);
}

sub normalize_array_whitespace ($self, $value) {
    my $close_paren_pos;
    my $depth;
    my $i = 0;
    if (!($i < length($value) && (($value->[$i] =~ /^[a-zA-Z]$/) || $value->[$i] eq "_"))) {
        return $value;
    }
    $i += 1;
    while ($i < length($value) && (($value->[$i] =~ /^[a-zA-Z0-9]$/) || $value->[$i] eq "_")) {
        $i += 1;
    }
    while ($i < length($value) && $value->[$i] eq "[") {
        $depth = 1;
        $i += 1;
        while ($i < length($value) && $depth > 0) {
            if ($value->[$i] eq "[") {
                $depth += 1;
            } elsif ($value->[$i] eq "]") {
                $depth -= 1;
            }
            $i += 1;
        }
        if ($depth != 0) {
            return $value;
        }
    }
    if ($i < length($value) && $value->[$i] eq "+") {
        $i += 1;
    }
    if (!($i + 1 < length($value) && $value->[$i] eq "=" && $value->[$i + 1] eq "(")) {
        return $value;
    }
    my $prefix = substring($value, 0, $i + 1);
    my $open_paren_pos = $i + 1;
    my $close_paren_pos = 0;
    if ($value->endswith(")")) {
        $close_paren_pos = length($value) - 1;
    } else {
        $close_paren_pos = $self->find_matching_paren($value, $open_paren_pos);
        if ($close_paren_pos < 0) {
            return $value;
        }
    }
    my $inner = substring($value, $open_paren_pos + 1, $close_paren_pos);
    my $suffix = substring($value, $close_paren_pos + 1, length($value));
    my $result = $self->normalize_array_inner($inner);
    return $prefix . "(" . $result . ")" . $suffix;
}

sub find_matching_paren ($self, $value, $open_pos) {
    my $ch;
    if ($open_pos >= length($value) || $value->[$open_pos] ne "(") {
        return -1;
    }
    my $i = $open_pos + 1;
    my $depth = 1;
    my $quote = new_quote_state();
    while ($i < length($value) && $depth > 0) {
        $ch = $value->[$i];
        if ($ch eq "\\" && $i + 1 < length($value) && !$quote->{single}) {
            $i += 2;
            next;
        }
        if ($ch eq "'" && !$quote->{double}) {
            $quote->{single} = !$quote->{single};
            $i += 1;
            next;
        }
        if ($ch eq "\"" && !$quote->{single}) {
            $quote->{double} = !$quote->{double};
            $i += 1;
            next;
        }
        if ($quote->{single} || $quote->{double}) {
            $i += 1;
            next;
        }
        if ($ch eq "#") {
            while ($i < length($value) && $value->[$i] ne "\n") {
                $i += 1;
            }
            next;
        }
        if ($ch eq "(") {
            $depth += 1;
        } elsif ($ch eq ")") {
            $depth -= 1;
            if ($depth == 0) {
                return $i;
            }
        }
        $i += 1;
    }
    return -1;
}

sub normalize_array_inner ($self, $inner) {
    my $ch;
    my $depth;
    my $dq_brace_depth;
    my $dq_content;
    my $j;
    my $normalized = [];
    my $i = 0;
    my $in_whitespace = 1;
    my $brace_depth = 0;
    my $bracket_depth = 0;
    while ($i < length($inner)) {
        $ch = $inner->[$i];
        if (is_whitespace($ch)) {
            if (!$in_whitespace && (scalar(@{$normalized}) > 0) && $brace_depth == 0 && $bracket_depth == 0) {
                $normalized->push(" ");
                $in_whitespace = 1;
            }
            if ($brace_depth > 0 || $bracket_depth > 0) {
                $normalized->push($ch);
            }
            $i += 1;
        } elsif ($ch eq "'") {
            $in_whitespace = 0;
            $j = $i + 1;
            while ($j < length($inner) && $inner->[$j] ne "'") {
                $j += 1;
            }
            $normalized->push(substring($inner, $i, $j + 1));
            $i = $j + 1;
        } elsif ($ch eq "\"") {
            $in_whitespace = 0;
            $j = $i + 1;
            $dq_content = ["\""];
            $dq_brace_depth = 0;
            while ($j < length($inner)) {
                if ($inner->[$j] eq "\\" && $j + 1 < length($inner)) {
                    if ($inner->[$j + 1] eq "\n") {
                        $j += 2;
                    } else {
                        $dq_content->push($inner->[$j]);
                        $dq_content->push($inner->[$j + 1]);
                        $j += 2;
                    }
                } elsif (is_expansion_start($inner, $j, "\${")) {
                    $dq_content->push("\${");
                    $dq_brace_depth += 1;
                    $j += 2;
                } elsif ($inner->[$j] eq "}" && $dq_brace_depth > 0) {
                    $dq_content->push("}");
                    $dq_brace_depth -= 1;
                    $j += 1;
                } elsif ($inner->[$j] eq "\"" && $dq_brace_depth == 0) {
                    $dq_content->push("\"");
                    $j += 1;
                    last;
                } else {
                    $dq_content->push($inner->[$j]);
                    $j += 1;
                }
            }
            $normalized->push(""->join_($dq_content));
            $i = $j;
        } elsif ($ch eq "\\" && $i + 1 < length($inner)) {
            if ($inner->[$i + 1] eq "\n") {
                $i += 2;
            } else {
                $in_whitespace = 0;
                $normalized->push(substring($inner, $i, $i + 2));
                $i += 2;
            }
        } elsif (is_expansion_start($inner, $i, "\$((")) {
            $in_whitespace = 0;
            $j = $i + 3;
            $depth = 1;
            while ($j < length($inner) && $depth > 0) {
                if ($j + 1 < length($inner) && $inner->[$j] eq "(" && $inner->[$j + 1] eq "(") {
                    $depth += 1;
                    $j += 2;
                } elsif ($j + 1 < length($inner) && $inner->[$j] eq ")" && $inner->[$j + 1] eq ")") {
                    $depth -= 1;
                    $j += 2;
                } else {
                    $j += 1;
                }
            }
            $normalized->push(substring($inner, $i, $j));
            $i = $j;
        } elsif (is_expansion_start($inner, $i, "\$(")) {
            $in_whitespace = 0;
            $j = $i + 2;
            $depth = 1;
            while ($j < length($inner) && $depth > 0) {
                if ($inner->[$j] eq "(" && $j > 0 && $inner->[$j - 1] eq "\$") {
                    $depth += 1;
                } elsif ($inner->[$j] eq ")") {
                    $depth -= 1;
                } elsif ($inner->[$j] eq "'") {
                    $j += 1;
                    while ($j < length($inner) && $inner->[$j] ne "'") {
                        $j += 1;
                    }
                } elsif ($inner->[$j] eq "\"") {
                    $j += 1;
                    while ($j < length($inner)) {
                        if ($inner->[$j] eq "\\" && $j + 1 < length($inner)) {
                            $j += 2;
                            next;
                        }
                        if ($inner->[$j] eq "\"") {
                            last;
                        }
                        $j += 1;
                    }
                }
                $j += 1;
            }
            $normalized->push(substring($inner, $i, $j));
            $i = $j;
        } elsif (($ch eq "<" || $ch eq ">") && $i + 1 < length($inner) && $inner->[$i + 1] eq "(") {
            $in_whitespace = 0;
            $j = $i + 2;
            $depth = 1;
            while ($j < length($inner) && $depth > 0) {
                if ($inner->[$j] eq "(") {
                    $depth += 1;
                } elsif ($inner->[$j] eq ")") {
                    $depth -= 1;
                } elsif ($inner->[$j] eq "'") {
                    $j += 1;
                    while ($j < length($inner) && $inner->[$j] ne "'") {
                        $j += 1;
                    }
                } elsif ($inner->[$j] eq "\"") {
                    $j += 1;
                    while ($j < length($inner)) {
                        if ($inner->[$j] eq "\\" && $j + 1 < length($inner)) {
                            $j += 2;
                            next;
                        }
                        if ($inner->[$j] eq "\"") {
                            last;
                        }
                        $j += 1;
                    }
                }
                $j += 1;
            }
            $normalized->push(substring($inner, $i, $j));
            $i = $j;
        } elsif (is_expansion_start($inner, $i, "\${")) {
            $in_whitespace = 0;
            $normalized->push("\${");
            $brace_depth += 1;
            $i += 2;
        } elsif ($ch eq "{" && $brace_depth > 0) {
            $normalized->push($ch);
            $brace_depth += 1;
            $i += 1;
        } elsif ($ch eq "}" && $brace_depth > 0) {
            $normalized->push($ch);
            $brace_depth -= 1;
            $i += 1;
        } elsif ($ch eq "#" && $brace_depth == 0 && $in_whitespace) {
            while ($i < length($inner) && $inner->[$i] ne "\n") {
                $i += 1;
            }
        } elsif ($ch eq "[") {
            if ($in_whitespace || $bracket_depth > 0) {
                $bracket_depth += 1;
            }
            $in_whitespace = 0;
            $normalized->push($ch);
            $i += 1;
        } elsif ($ch eq "]" && $bracket_depth > 0) {
            $normalized->push($ch);
            $bracket_depth -= 1;
            $i += 1;
        } else {
            $in_whitespace = 0;
            $normalized->push($ch);
            $i += 1;
        }
    }
    return (""->join_($normalized) =~ s/\s+$//r);
}

sub strip_arith_line_continuations ($self, $value) {
    my $arith_content;
    my $closing;
    my $content;
    my $depth;
    my $first_close_idx;
    my $j;
    my $num_backslashes;
    my $start;
    my $result = [];
    my $i = 0;
    while ($i < length($value)) {
        if (is_expansion_start($value, $i, "\$((")) {
            $start = $i;
            $i += 3;
            $depth = 2;
            $arith_content = [];
            my $first_close_idx = -1;
            while ($i < length($value) && $depth > 0) {
                if ($value->[$i] eq "(") {
                    $arith_content->push("(");
                    $depth += 1;
                    $i += 1;
                    if ($depth > 1) {
                        $first_close_idx = -1;
                    }
                } elsif ($value->[$i] eq ")") {
                    if ($depth == 2) {
                        $first_close_idx = scalar(@{$arith_content});
                    }
                    $depth -= 1;
                    if ($depth > 0) {
                        $arith_content->push(")");
                    }
                    $i += 1;
                } elsif ($value->[$i] eq "\\" && $i + 1 < length($value) && $value->[$i + 1] eq "\n") {
                    $num_backslashes = 0;
                    $j = scalar(@{$arith_content}) - 1;
                    while ($j >= 0 && $arith_content->[$j] eq "\n") {
                        $j -= 1;
                    }
                    while ($j >= 0 && $arith_content->[$j] eq "\\") {
                        $num_backslashes += 1;
                        $j -= 1;
                    }
                    if ($num_backslashes % 2 == 1) {
                        $arith_content->push("\\");
                        $arith_content->push("\n");
                        $i += 2;
                    } else {
                        $i += 2;
                    }
                    if ($depth == 1) {
                        $first_close_idx = -1;
                    }
                } else {
                    $arith_content->push($value->[$i]);
                    $i += 1;
                    if ($depth == 1) {
                        $first_close_idx = -1;
                    }
                }
            }
            if ($depth == 0 || $depth == 1 && $first_close_idx != -1) {
                $content = ""->join_($arith_content);
                if ($first_close_idx != -1) {
                    $content = substr($content, 0, $first_close_idx - 0);
                    $closing = ($depth == 0 ? "))" : ")");
                    $result->push("\$((" . $content . $closing);
                } else {
                    $result->push("\$((" . $content . ")");
                }
            } else {
                $result->push(substring($value, $start, $i));
            }
        } else {
            $result->push($value->[$i]);
            $i += 1;
        }
    }
    return ""->join_($result);
}

sub collect_cmdsubs ($self, $node) {
    my $result = [];
    if (ref($node) eq 'CommandSubstitution') {
        my $node = $node;
        $result->push($node);
    } elsif (ref($node) eq 'Array') {
        my $node = $node;
        for my $elem (@{($node->{elements} // [])}) {
            for my $p (@{($elem->{parts} // [])}) {
                if (ref($p) eq 'CommandSubstitution') {
                    my $p = $p;
                    $result->push($p);
                } else {
                    $result->extend($self->collect_cmdsubs($p));
                }
            }
        }
    } elsif (ref($node) eq 'ArithmeticExpansion') {
        my $node = $node;
        if (defined($node->{expression})) {
            $result->extend($self->collect_cmdsubs($node->{expression}));
        }
    } elsif (ref($node) eq 'ArithBinaryOp') {
        my $node = $node;
        $result->extend($self->collect_cmdsubs($node->{left}));
        $result->extend($self->collect_cmdsubs($node->{right}));
    } elsif (ref($node) eq 'ArithComma') {
        my $node = $node;
        $result->extend($self->collect_cmdsubs($node->{left}));
        $result->extend($self->collect_cmdsubs($node->{right}));
    } elsif (ref($node) eq 'ArithUnaryOp') {
        my $node = $node;
        $result->extend($self->collect_cmdsubs($node->{operand}));
    } elsif (ref($node) eq 'ArithPreIncr') {
        my $node = $node;
        $result->extend($self->collect_cmdsubs($node->{operand}));
    } elsif (ref($node) eq 'ArithPostIncr') {
        my $node = $node;
        $result->extend($self->collect_cmdsubs($node->{operand}));
    } elsif (ref($node) eq 'ArithPreDecr') {
        my $node = $node;
        $result->extend($self->collect_cmdsubs($node->{operand}));
    } elsif (ref($node) eq 'ArithPostDecr') {
        my $node = $node;
        $result->extend($self->collect_cmdsubs($node->{operand}));
    } elsif (ref($node) eq 'ArithTernary') {
        my $node = $node;
        $result->extend($self->collect_cmdsubs($node->{condition}));
        $result->extend($self->collect_cmdsubs($node->{if_true}));
        $result->extend($self->collect_cmdsubs($node->{if_false}));
    } elsif (ref($node) eq 'ArithAssign') {
        my $node = $node;
        $result->extend($self->collect_cmdsubs($node->{target}));
        $result->extend($self->collect_cmdsubs($node->{value}));
    }
    return $result;
}

sub collect_procsubs ($self, $node) {
    my $result = [];
    if (ref($node) eq 'ProcessSubstitution') {
        my $node = $node;
        $result->push($node);
    } elsif (ref($node) eq 'Array') {
        my $node = $node;
        for my $elem (@{($node->{elements} // [])}) {
            for my $p (@{($elem->{parts} // [])}) {
                if (ref($p) eq 'ProcessSubstitution') {
                    my $p = $p;
                    $result->push($p);
                } else {
                    $result->extend($self->collect_procsubs($p));
                }
            }
        }
    }
    return $result;
}

sub format_command_substitutions ($self, $value, $in_arith) {
    my $brace_quote;
    my $c;
    my $cmdsub_node;
    my $compact;
    my $depth;
    my $direction;
    my $ends_with_newline;
    my $final_output;
    my $formatted;
    my $formatted_inner;
    my $has_pipe;
    my $inner;
    my $is_procsub;
    my $j;
    my $leading_ws;
    my $leading_ws_end;
    my $node;
    my $normalized_ws;
    my $orig_inner;
    my $parsed;
    my $parser;
    my $prefix;
    my $raw_content;
    my $raw_stripped;
    my $spaced;
    my $stripped;
    my $suffix;
    my $terminator;
    my $cmdsub_parts = [];
    my $procsub_parts = [];
    my $has_arith = 0;
    for my $p (@{($self->{parts} // [])}) {
        if (ref($p) eq 'CommandSubstitution') {
            my $p = $p;
            $cmdsub_parts->push($p);
        } elsif (ref($p) eq 'ProcessSubstitution') {
            my $p = $p;
            $procsub_parts->push($p);
        } elsif (ref($p) eq 'ArithmeticExpansion') {
            my $p = $p;
            $has_arith = 1;
        } else {
            $cmdsub_parts->extend($self->collect_cmdsubs($p));
            $procsub_parts->extend($self->collect_procsubs($p));
        }
    }
    my $has_brace_cmdsub = $value->find("\${ ") != -1 || $value->find("\${\t") != -1 || $value->find("\${\n") != -1 || $value->find("\${|") != -1;
    my $has_untracked_cmdsub = 0;
    my $has_untracked_procsub = 0;
    my $idx = 0;
    my $scan_quote = new_quote_state();
    while ($idx < length($value)) {
        if ($value->[$idx] eq "\"") {
            $scan_quote->{double} = !$scan_quote->{double};
            $idx += 1;
        } elsif ($value->[$idx] eq "'" && !$scan_quote->{double}) {
            $idx += 1;
            while ($idx < length($value) && $value->[$idx] ne "'") {
                $idx += 1;
            }
            if ($idx < length($value)) {
                $idx += 1;
            }
        } elsif (starts_with_at($value, $idx, "\$(") && !starts_with_at($value, $idx, "\$((") && !is_backslash_escaped($value, $idx) && !is_dollar_dollar_paren($value, $idx)) {
            $has_untracked_cmdsub = 1;
            last;
        } elsif ((starts_with_at($value, $idx, "<(") || starts_with_at($value, $idx, ">(")) && !$scan_quote->{double}) {
            if ($idx == 0 || !($value->[$idx - 1] =~ /^[a-zA-Z0-9]$/) && ((index("\"'", $value->[$idx - 1]) == -1))) {
                $has_untracked_procsub = 1;
                last;
            }
            $idx += 1;
        } else {
            $idx += 1;
        }
    }
    my $has_param_with_procsub_pattern = ((index($value, "\${") >= 0)) && (((index($value, "<(") >= 0)) || ((index($value, ">(") >= 0)));
    if (!(scalar(@{$cmdsub_parts}) > 0) && !(scalar(@{$procsub_parts}) > 0) && !$has_brace_cmdsub && !$has_untracked_cmdsub && !$has_untracked_procsub && !$has_param_with_procsub_pattern) {
        return $value;
    }
    my $result = [];
    my $i = 0;
    my $cmdsub_idx = 0;
    my $procsub_idx = 0;
    my $main_quote = new_quote_state();
    my $extglob_depth = 0;
    my $deprecated_arith_depth = 0;
    my $arith_depth = 0;
    my $arith_paren_depth = 0;
    while ($i < length($value)) {
        if ($i > 0 && is_extglob_prefix($value->[$i - 1]) && $value->[$i] eq "(" && !is_backslash_escaped($value, $i - 1)) {
            $extglob_depth += 1;
            $result->push($value->[$i]);
            $i += 1;
            next;
        }
        if ($value->[$i] eq ")" && $extglob_depth > 0) {
            $extglob_depth -= 1;
            $result->push($value->[$i]);
            $i += 1;
            next;
        }
        if (starts_with_at($value, $i, "\$[") && !is_backslash_escaped($value, $i)) {
            $deprecated_arith_depth += 1;
            $result->push($value->[$i]);
            $i += 1;
            next;
        }
        if ($value->[$i] eq "]" && $deprecated_arith_depth > 0) {
            $deprecated_arith_depth -= 1;
            $result->push($value->[$i]);
            $i += 1;
            next;
        }
        if (is_expansion_start($value, $i, "\$((") && !is_backslash_escaped($value, $i) && $has_arith) {
            $arith_depth += 1;
            $arith_paren_depth += 2;
            $result->push("\$((");
            $i += 3;
            next;
        }
        if ($arith_depth > 0 && $arith_paren_depth == 2 && starts_with_at($value, $i, "))")) {
            $arith_depth -= 1;
            $arith_paren_depth -= 2;
            $result->push("))");
            $i += 2;
            next;
        }
        if ($arith_depth > 0) {
            if ($value->[$i] eq "(") {
                $arith_paren_depth += 1;
                $result->push($value->[$i]);
                $i += 1;
                next;
            } elsif ($value->[$i] eq ")") {
                $arith_paren_depth -= 1;
                $result->push($value->[$i]);
                $i += 1;
                next;
            }
        }
        my $j = 0;
        if (is_expansion_start($value, $i, "\$((") && !$has_arith) {
            $j = find_cmdsub_end($value, $i + 2);
            $result->push(substring($value, $i, $j));
            if ($cmdsub_idx < scalar(@{$cmdsub_parts})) {
                $cmdsub_idx += 1;
            }
            $i = $j;
            next;
        }
        my $inner = "";
        my $node = undef;
        my $formatted = "";
        my $parser = undef;
        my $parsed = undef;
        if (starts_with_at($value, $i, "\$(") && !starts_with_at($value, $i, "\$((") && !is_backslash_escaped($value, $i) && !is_dollar_dollar_paren($value, $i)) {
            $j = find_cmdsub_end($value, $i + 2);
            if ($extglob_depth > 0) {
                $result->push(substring($value, $i, $j));
                if ($cmdsub_idx < scalar(@{$cmdsub_parts})) {
                    $cmdsub_idx += 1;
                }
                $i = $j;
                next;
            }
            $inner = substring($value, $i + 2, $j - 1);
            if ($cmdsub_idx < scalar(@{$cmdsub_parts})) {
                $node = $cmdsub_parts->[$cmdsub_idx];
                $formatted = format_cmdsub_node($node->{command}, 0, 0, 0, 0);
                $cmdsub_idx += 1;
            } else {
                eval {
                    $parser = new_parser($inner, 0, 0);
                    $parsed = $parser->parse_list(1);
                    $formatted = (defined($parsed) ? format_cmdsub_node($parsed, 0, 0, 0, 0) : "");
                };
                if (my $_e = $@) {
                    $formatted = $inner;
                }
            }
            if ($formatted->startswith("(")) {
                $result->push("\$( " . $formatted . ")");
            } else {
                $result->push("\$(" . $formatted . ")");
            }
            $i = $j;
        } elsif ($value->[$i] eq "`" && $cmdsub_idx < scalar(@{$cmdsub_parts})) {
            $j = $i + 1;
            while ($j < length($value)) {
                if ($value->[$j] eq "\\" && $j + 1 < length($value)) {
                    $j += 2;
                    next;
                }
                if ($value->[$j] eq "`") {
                    $j += 1;
                    last;
                }
                $j += 1;
            }
            $result->push(substring($value, $i, $j));
            $cmdsub_idx += 1;
            $i = $j;
        } elsif (is_expansion_start($value, $i, "\${") && $i + 2 < length($value) && is_funsub_char($value->[$i + 2]) && !is_backslash_escaped($value, $i)) {
            $j = find_funsub_end($value, $i + 2);
            $cmdsub_node = ($cmdsub_idx < scalar(@{$cmdsub_parts}) ? $cmdsub_parts->[$cmdsub_idx] : undef);
            if ((ref($cmdsub_node) eq 'CommandSubstitution') && $cmdsub_node->{brace}) {
                $node = $cmdsub_node;
                $formatted = format_cmdsub_node($node->{command}, 0, 0, 0, 0);
                $has_pipe = $value->[$i + 2] eq "|";
                $prefix = ($has_pipe ? "\${|" : "\${ ");
                $orig_inner = substring($value, $i + 2, $j - 1);
                $ends_with_newline = $orig_inner->endswith("\n");
                my $suffix = "";
                if (!(length($formatted) > 0) || ($formatted =~ /^\s$/)) {
                    $suffix = "}";
                } elsif ($formatted->endswith("&") || $formatted->endswith("& ")) {
                    $suffix = ($formatted->endswith("&") ? " }" : "}");
                } elsif ($ends_with_newline) {
                    $suffix = "\n }";
                } else {
                    $suffix = "; }";
                }
                $result->push($prefix . $formatted . $suffix);
                $cmdsub_idx += 1;
            } else {
                $result->push(substring($value, $i, $j));
            }
            $i = $j;
        } elsif ((starts_with_at($value, $i, ">(") || starts_with_at($value, $i, "<(")) && !$main_quote->{double} && $deprecated_arith_depth == 0 && $arith_depth == 0) {
            $is_procsub = $i == 0 || !($value->[$i - 1] =~ /^[a-zA-Z0-9]$/) && ((index("\"'", $value->[$i - 1]) == -1));
            if ($extglob_depth > 0) {
                $j = find_cmdsub_end($value, $i + 2);
                $result->push(substring($value, $i, $j));
                if ($procsub_idx < scalar(@{$procsub_parts})) {
                    $procsub_idx += 1;
                }
                $i = $j;
                next;
            }
            my $direction = "";
            my $compact = 0;
            my $stripped = "";
            if ($procsub_idx < scalar(@{$procsub_parts})) {
                $direction = $value->[$i];
                $j = find_cmdsub_end($value, $i + 2);
                $node = $procsub_parts->[$procsub_idx];
                $compact = starts_with_subshell($node->{command});
                $formatted = format_cmdsub_node($node->{command}, 0, 1, $compact, 1);
                $raw_content = substring($value, $i + 2, $j - 1);
                if ($node->{command}->{kind} == "subshell") {
                    $leading_ws_end = 0;
                    while ($leading_ws_end < length($raw_content) && ((index(" \t\n", $raw_content->[$leading_ws_end]) >= 0))) {
                        $leading_ws_end += 1;
                    }
                    $leading_ws = substr($raw_content, 0, $leading_ws_end - 0);
                    $stripped = substr($raw_content, $leading_ws_end);
                    if ($stripped->startswith("(")) {
                        if ((length($leading_ws) > 0)) {
                            $normalized_ws = $leading_ws->replace("\n", " ")->replace("\t", " ");
                            $spaced = format_cmdsub_node($node->{command}, 0, 0, 0, 0);
                            $result->push($direction . "(" . $normalized_ws . $spaced . ")");
                        } else {
                            $raw_content = $raw_content->replace("\\\n", "");
                            $result->push($direction . "(" . $raw_content . ")");
                        }
                        $procsub_idx += 1;
                        $i = $j;
                        next;
                    }
                }
                $raw_content = substring($value, $i + 2, $j - 1);
                $raw_stripped = $raw_content->replace("\\\n", "");
                if (starts_with_subshell($node->{command}) && $formatted ne $raw_stripped) {
                    $result->push($direction . "(" . $raw_stripped . ")");
                } else {
                    $final_output = $direction . "(" . $formatted . ")";
                    $result->push($final_output);
                }
                $procsub_idx += 1;
                $i = $j;
            } elsif ($is_procsub && (scalar(@{$self->{parts}}) ? 1 : 0)) {
                $direction = $value->[$i];
                $j = find_cmdsub_end($value, $i + 2);
                if ($j > length($value) || $j > 0 && $j <= length($value) && $value->[$j - 1] ne ")") {
                    $result->push($value->[$i]);
                    $i += 1;
                    next;
                }
                $inner = substring($value, $i + 2, $j - 1);
                eval {
                    $parser = new_parser($inner, 0, 0);
                    $parsed = $parser->parse_list(1);
                    if (defined($parsed) && $parser->{pos_} == length($inner) && ((index($inner, "\n") == -1))) {
                        $compact = starts_with_subshell($parsed);
                        $formatted = format_cmdsub_node($parsed, 0, 1, $compact, 1);
                    } else {
                        $formatted = $inner;
                    }
                };
                if (my $_e = $@) {
                    $formatted = $inner;
                }
                $result->push($direction . "(" . $formatted . ")");
                $i = $j;
            } elsif ($is_procsub) {
                $direction = $value->[$i];
                $j = find_cmdsub_end($value, $i + 2);
                if ($j > length($value) || $j > 0 && $j <= length($value) && $value->[$j - 1] ne ")") {
                    $result->push($value->[$i]);
                    $i += 1;
                    next;
                }
                $inner = substring($value, $i + 2, $j - 1);
                if ($in_arith) {
                    $result->push($direction . "(" . $inner . ")");
                } elsif ((length(($inner =~ s/^\s+|\s+$//gr)) > 0)) {
                    $stripped = ($inner =~ s/^[" \t"]+//r);
                    $result->push($direction . "(" . $stripped . ")");
                } else {
                    $result->push($direction . "(" . $inner . ")");
                }
                $i = $j;
            } else {
                $result->push($value->[$i]);
                $i += 1;
            }
        } elsif ((is_expansion_start($value, $i, "\${ ") || is_expansion_start($value, $i, "\${\t") || is_expansion_start($value, $i, "\${\n") || is_expansion_start($value, $i, "\${|")) && !is_backslash_escaped($value, $i)) {
            $prefix = substring($value, $i, $i + 3)->replace("\t", " ")->replace("\n", " ");
            $j = $i + 3;
            $depth = 1;
            while ($j < length($value) && $depth > 0) {
                if ($value->[$j] eq "{") {
                    $depth += 1;
                } elsif ($value->[$j] eq "}") {
                    $depth -= 1;
                }
                $j += 1;
            }
            $inner = substring($value, $i + 2, $j - 1);
            if (($inner =~ s/^\s+|\s+$//gr) eq "") {
                $result->push("\${ }");
            } else {
                eval {
                    $parser = new_parser(($inner =~ s/^[" \t\n|"]+//r), 0, 0);
                    $parsed = $parser->parse_list(1);
                    if (defined($parsed)) {
                        $formatted = format_cmdsub_node($parsed, 0, 0, 0, 0);
                        $formatted = ($formatted =~ s/[";"]+$//r);
                        my $terminator = "";
                        if (($inner =~ s/[" \t"]+$//r)->endswith("\n")) {
                            $terminator = "\n }";
                        } elsif ($formatted->endswith(" &")) {
                            $terminator = " }";
                        } else {
                            $terminator = "; }";
                        }
                        $result->push($prefix . $formatted . $terminator);
                    } else {
                        $result->push("\${ }");
                    }
                };
                if (my $_e = $@) {
                    $result->push(substring($value, $i, $j));
                }
            }
            $i = $j;
        } elsif (is_expansion_start($value, $i, "\${") && !is_backslash_escaped($value, $i)) {
            $j = $i + 2;
            $depth = 1;
            $brace_quote = new_quote_state();
            while ($j < length($value) && $depth > 0) {
                $c = $value->[$j];
                if ($c eq "\\" && $j + 1 < length($value) && !$brace_quote->{single}) {
                    $j += 2;
                    next;
                }
                if ($c eq "'" && !$brace_quote->{double}) {
                    $brace_quote->{single} = !$brace_quote->{single};
                } elsif ($c eq "\"" && !$brace_quote->{single}) {
                    $brace_quote->{double} = !$brace_quote->{double};
                } elsif (!$brace_quote->in_quotes()) {
                    if (is_expansion_start($value, $j, "\$(") && !starts_with_at($value, $j, "\$((")) {
                        $j = find_cmdsub_end($value, $j + 2);
                        next;
                    }
                    if ($c eq "{") {
                        $depth += 1;
                    } elsif ($c eq "}") {
                        $depth -= 1;
                    }
                }
                $j += 1;
            }
            if ($depth > 0) {
                $inner = substring($value, $i + 2, $j);
            } else {
                $inner = substring($value, $i + 2, $j - 1);
            }
            $formatted_inner = $self->format_command_substitutions($inner, 0);
            $formatted_inner = $self->normalize_extglob_whitespace($formatted_inner);
            if ($depth == 0) {
                $result->push("\${" . $formatted_inner . "}");
            } else {
                $result->push("\${" . $formatted_inner);
            }
            $i = $j;
        } elsif ($value->[$i] eq "\"") {
            $main_quote->{double} = !$main_quote->{double};
            $result->push($value->[$i]);
            $i += 1;
        } elsif ($value->[$i] eq "'" && !$main_quote->{double}) {
            $j = $i + 1;
            while ($j < length($value) && $value->[$j] ne "'") {
                $j += 1;
            }
            if ($j < length($value)) {
                $j += 1;
            }
            $result->push(substring($value, $i, $j));
            $i = $j;
        } else {
            $result->push($value->[$i]);
            $i += 1;
        }
    }
    return ""->join_($result);
}

sub normalize_extglob_whitespace ($self, $value) {
    my $current_part;
    my $depth;
    my $has_pipe;
    my $part_content;
    my $pattern_parts;
    my $prefix_char;
    my $result = [];
    my $i = 0;
    my $extglob_quote = new_quote_state();
    my $deprecated_arith_depth = 0;
    while ($i < length($value)) {
        if ($value->[$i] eq "\"") {
            $extglob_quote->{double} = !$extglob_quote->{double};
            $result->push($value->[$i]);
            $i += 1;
            next;
        }
        if (starts_with_at($value, $i, "\$[") && !is_backslash_escaped($value, $i)) {
            $deprecated_arith_depth += 1;
            $result->push($value->[$i]);
            $i += 1;
            next;
        }
        if ($value->[$i] eq "]" && $deprecated_arith_depth > 0) {
            $deprecated_arith_depth -= 1;
            $result->push($value->[$i]);
            $i += 1;
            next;
        }
        if ($i + 1 < length($value) && $value->[$i + 1] eq "(") {
            $prefix_char = $value->[$i];
            if (((index("><", $prefix_char) >= 0)) && !$extglob_quote->{double} && $deprecated_arith_depth == 0) {
                $result->push($prefix_char);
                $result->push("(");
                $i += 2;
                $depth = 1;
                $pattern_parts = [];
                $current_part = [];
                $has_pipe = 0;
                while ($i < length($value) && $depth > 0) {
                    if ($value->[$i] eq "\\" && $i + 1 < length($value)) {
                        $current_part->push(substr($value, $i, $i + 2 - $i));
                        $i += 2;
                        next;
                    } elsif ($value->[$i] eq "(") {
                        $depth += 1;
                        $current_part->push($value->[$i]);
                        $i += 1;
                    } elsif ($value->[$i] eq ")") {
                        $depth -= 1;
                        if ($depth == 0) {
                            $part_content = ""->join_($current_part);
                            if ((index($part_content, "<<") >= 0)) {
                                $pattern_parts->push($part_content);
                            } elsif ($has_pipe) {
                                $pattern_parts->push(($part_content =~ s/^\s+|\s+$//gr));
                            } else {
                                $pattern_parts->push($part_content);
                            }
                            last;
                        }
                        $current_part->push($value->[$i]);
                        $i += 1;
                    } elsif ($value->[$i] eq "|" && $depth == 1) {
                        if ($i + 1 < length($value) && $value->[$i + 1] eq "|") {
                            $current_part->push("||");
                            $i += 2;
                        } else {
                            $has_pipe = 1;
                            $part_content = ""->join_($current_part);
                            if ((index($part_content, "<<") >= 0)) {
                                $pattern_parts->push($part_content);
                            } else {
                                $pattern_parts->push(($part_content =~ s/^\s+|\s+$//gr));
                            }
                            $current_part = [];
                            $i += 1;
                        }
                    } else {
                        $current_part->push($value->[$i]);
                        $i += 1;
                    }
                }
                $result->push(" | "->join_($pattern_parts));
                if ($depth == 0) {
                    $result->push(")");
                    $i += 1;
                }
                next;
            }
        }
        $result->push($value->[$i]);
        $i += 1;
    }
    return ""->join_($result);
}

sub get_cond_formatted_value ($self) {
    my $value = $self->expand_all_ansi_c_quotes($self->{value});
    $value = $self->strip_locale_string_dollars($value);
    $value = $self->format_command_substitutions($value, 0);
    $value = $self->normalize_extglob_whitespace($value);
    $value = $value->replace("", "");
    return ($value =~ s/["\n"]+$//r);
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Command;

sub new ($class, $words, $redirects, $kind) {
    return bless { words => $words, redirects => $redirects, kind => $kind }, $class;
}

sub words ($self) { $self->{words} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $parts = [];
    for my $w (@{($self->{words} // [])}) {
        $parts->push($w->to_sexp());
    }
    for my $r (@{($self->{redirects} // [])}) {
        $parts->push($r->to_sexp());
    }
    my $inner = " "->join_($parts);
    if (!(length($inner) > 0)) {
        return "(command)";
    }
    return "(command " . $inner . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Pipeline;

sub new ($class, $commands, $kind) {
    return bless { commands => $commands, kind => $kind }, $class;
}

sub commands ($self) { $self->{commands} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $cmd;
    my $needs;
    my $needs_redirect;
    my $pair;
    if (scalar(@{$self->{commands}}) == 1) {
        return $self->{commands}->[0]->to_sexp();
    }
    my $cmds = [];
    my $i = 0;
    my $cmd = undef;
    while ($i < scalar(@{$self->{commands}})) {
        $cmd = $self->{commands}->[$i];
        if (ref($cmd) eq 'PipeBoth') {
            my $cmd = $cmd;
            $i += 1;
            next;
        }
        $needs_redirect = $i + 1 < scalar(@{$self->{commands}}) && $self->{commands}->[$i + 1]->{kind} == "pipe-both";
        $cmds->push([$cmd, $needs_redirect]);
        $i += 1;
    }
    my $pair = undef;
    my $needs = 0;
    if (scalar(@{$cmds}) == 1) {
        $pair = $cmds->[0];
        $cmd = $pair->[0];
        $needs = $pair->[1];
        return $self->cmd_sexp($cmd, $needs);
    }
    my $last_pair = $cmds->[-1];
    my $last_cmd = $last_pair->[0];
    my $last_needs = $last_pair->[1];
    my $result = $self->cmd_sexp($last_cmd, $last_needs);
    my $j = scalar(@{$cmds}) - 2;
    while ($j >= 0) {
        $pair = $cmds->[$j];
        $cmd = $pair->[0];
        $needs = $pair->[1];
        if ($needs && $cmd->{kind} != "command") {
            $result = "(pipe " . $cmd->to_sexp() . " (redirect \">&\" 1) " . $result . ")";
        } else {
            $result = "(pipe " . $self->cmd_sexp($cmd, $needs) . " " . $result . ")";
        }
        $j -= 1;
    }
    return $result;
}

sub cmd_sexp ($self, $cmd, $needs_redirect) {
    my $parts;
    if (!$needs_redirect) {
        return $cmd->to_sexp();
    }
    if (ref($cmd) eq 'Command') {
        my $cmd = $cmd;
        $parts = [];
        for my $w (@{($cmd->{words} // [])}) {
            $parts->push($w->to_sexp());
        }
        for my $r (@{($cmd->{redirects} // [])}) {
            $parts->push($r->to_sexp());
        }
        $parts->push("(redirect \">&\" 1)");
        return "(command " . " "->join_($parts) . ")";
    }
    return $cmd->to_sexp();
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package List;

sub new ($class, $parts, $kind) {
    return bless { parts => $parts, kind => $kind }, $class;
}

sub parts ($self) { $self->{parts} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $inner_list;
    my $inner_parts;
    my $left;
    my $left_sexp;
    my $right;
    my $right_sexp;
    my $parts = $self->{parts}->copy();
    my $op_names = {"&&" => "and", "||" => "or", ";" => "semi", "\n" => "semi", "&" => "background"};
    while (scalar(@{$parts}) > 1 && $parts->[-1]->{kind} == "operator" && ($parts->[-1]->{op} eq ";" || $parts->[-1]->{op} eq "\n")) {
        $parts = sublist($parts, 0, scalar(@{$parts}) - 1);
    }
    if (scalar(@{$parts}) == 1) {
        return $parts->[0]->to_sexp();
    }
    if ($parts->[-1]->{kind} == "operator" && $parts->[-1]->{op} eq "&") {
        for (my $i = scalar(@{$parts}) - 3; $i > 0; $i += -2) {
            if ($parts->[$i]->{kind} == "operator" && ($parts->[$i]->{op} eq ";" || $parts->[$i]->{op} eq "\n")) {
                $left = sublist($parts, 0, $i);
                $right = sublist($parts, $i + 1, scalar(@{$parts}) - 1);
                my $left_sexp = "";
                if (scalar(@{$left}) > 1) {
                    $left_sexp = List->new($left, "list")->to_sexp();
                } else {
                    $left_sexp = $left->[0]->to_sexp();
                }
                my $right_sexp = "";
                if (scalar(@{$right}) > 1) {
                    $right_sexp = List->new($right, "list")->to_sexp();
                } else {
                    $right_sexp = $right->[0]->to_sexp();
                }
                return "(semi " . $left_sexp . " (background " . $right_sexp . "))";
            }
        }
        $inner_parts = sublist($parts, 0, scalar(@{$parts}) - 1);
        if (scalar(@{$inner_parts}) == 1) {
            return "(background " . $inner_parts->[0]->to_sexp() . ")";
        }
        $inner_list = List->new($inner_parts, "list");
        return "(background " . $inner_list->to_sexp() . ")";
    }
    return $self->to_sexp_with_precedence($parts, $op_names);
}

sub to_sexp_with_precedence ($self, $parts, $op_names) {
    my $result;
    my $seg;
    my $segments;
    my $start;
    my $semi_positions = [];
    for my $i (0 .. scalar(@{$parts}) - 1) {
        if ($parts->[$i]->{kind} == "operator" && ($parts->[$i]->{op} eq ";" || $parts->[$i]->{op} eq "\n")) {
            $semi_positions->push($i);
        }
    }
    if ((scalar(@{$semi_positions}) > 0)) {
        $segments = [];
        $start = 0;
        my $seg = undef;
        for my $pos_ (@{$semi_positions}) {
            $seg = sublist($parts, $start, $pos_);
            if ((scalar(@{$seg}) > 0) && $seg->[0]->{kind} != "operator") {
                $segments->push($seg);
            }
            $start = $pos_ + 1;
        }
        $seg = sublist($parts, $start, scalar(@{$parts}));
        if ((scalar(@{$seg}) > 0) && $seg->[0]->{kind} != "operator") {
            $segments->push($seg);
        }
        if (!(scalar(@{$segments}) > 0)) {
            return "()";
        }
        $result = $self->to_sexp_amp_and_higher($segments->[0], $op_names);
        for (my $i = 1; $i < scalar(@{$segments}); $i += 1) {
            $result = "(semi " . $result . " " . $self->to_sexp_amp_and_higher($segments->[$i], $op_names) . ")";
        }
        return $result;
    }
    return $self->to_sexp_amp_and_higher($parts, $op_names);
}

sub to_sexp_amp_and_higher ($self, $parts, $op_names) {
    my $result;
    my $segments;
    my $start;
    if (scalar(@{$parts}) == 1) {
        return $parts->[0]->to_sexp();
    }
    my $amp_positions = [];
    for (my $i = 1; $i < scalar(@{$parts}) - 1; $i += 2) {
        if ($parts->[$i]->{kind} == "operator" && $parts->[$i]->{op} eq "&") {
            $amp_positions->push($i);
        }
    }
    if ((scalar(@{$amp_positions}) > 0)) {
        $segments = [];
        $start = 0;
        for my $pos_ (@{$amp_positions}) {
            $segments->push(sublist($parts, $start, $pos_));
            $start = $pos_ + 1;
        }
        $segments->push(sublist($parts, $start, scalar(@{$parts})));
        $result = $self->to_sexp_and_or($segments->[0], $op_names);
        for (my $i = 1; $i < scalar(@{$segments}); $i += 1) {
            $result = "(background " . $result . " " . $self->to_sexp_and_or($segments->[$i], $op_names) . ")";
        }
        return $result;
    }
    return $self->to_sexp_and_or($parts, $op_names);
}

sub to_sexp_and_or ($self, $parts, $op_names) {
    my $cmd;
    my $op;
    my $op_name;
    if (scalar(@{$parts}) == 1) {
        return $parts->[0]->to_sexp();
    }
    my $result = $parts->[0]->to_sexp();
    for (my $i = 1; $i < scalar(@{$parts}) - 1; $i += 2) {
        $op = $parts->[$i];
        $cmd = $parts->[$i + 1];
        $op_name = $op_names->get($op->{op}, $op->{op});
        $result = "(" . $op_name . " " . $result + " " . $cmd->to_sexp() + ")";
    }
    return $result;
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Operator;

sub new ($class, $op, $kind) {
    return bless { op => $op, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $names = {"&&" => "and", "||" => "or", ";" => "semi", "&" => "bg", "|" => "pipe"};
    return "(" . $names->get($self->{op}, $self->{op}) . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package PipeBoth;

sub new ($class, $kind) {
    return bless { kind => $kind }, $class;
}

sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(pipe-both)";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Empty;

sub new ($class, $kind) {
    return bless { kind => $kind }, $class;
}

sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Comment;

sub new ($class, $text, $kind) {
    return bless { text => $text, kind => $kind }, $class;
}

sub text ($self) { $self->{text} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Redirect;

sub new ($class, $op, $target, $fd, $kind) {
    return bless { op => $op, target => $target, fd => $fd, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub target ($self) { $self->{target} }
sub fd ($self) { $self->{fd} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $fd_target;
    my $j;
    my $out_val;
    my $raw;
    my $op = ($self->{op} =~ s/^["0123456789"]+//r);
    if ($op->startswith("{")) {
        $j = 1;
        if ($j < length($op) && (($op->[$j] =~ /^[a-zA-Z]$/) || $op->[$j] eq "_")) {
            $j += 1;
            while ($j < length($op) && (($op->[$j] =~ /^[a-zA-Z0-9]$/) || $op->[$j] eq "_")) {
                $j += 1;
            }
            if ($j < length($op) && $op->[$j] eq "[") {
                $j += 1;
                while ($j < length($op) && $op->[$j] ne "]") {
                    $j += 1;
                }
                if ($j < length($op) && $op->[$j] eq "]") {
                    $j += 1;
                }
            }
            if ($j < length($op) && $op->[$j] eq "}") {
                $op = substring($op, $j + 1, length($op));
            }
        }
    }
    my $target_val = $self->{target}->{value};
    $target_val = $self->{target}->expand_all_ansi_c_quotes($target_val);
    $target_val = $self->{target}->strip_locale_string_dollars($target_val);
    $target_val = $self->{target}->format_command_substitutions($target_val, 0);
    $target_val = $self->{target}->strip_arith_line_continuations($target_val);
    if ($target_val->endswith("\\") && !$target_val->endswith("\\\\")) {
        $target_val = $target_val . "\\";
    }
    if ($target_val->startswith("&")) {
        if ($op eq ">") {
            $op = ">&";
        } elsif ($op eq "<") {
            $op = "<&";
        }
        $raw = substring($target_val, 1, length($target_val));
        if (($raw =~ /^\d$/) && int($raw) <= 2147483647) {
            return "(redirect \"" . $op . "\" " . "int($raw)" . ")";
        }
        if ($raw->endswith("-") && (substr($raw, 0, length($raw) - 1 - 0) =~ /^\d$/) && int(substr($raw, 0, length($raw) - 1 - 0)) <= 2147483647) {
            return "(redirect \"" . $op . "\" " . "int(substr($raw, 0, length($raw) - 1 - 0))" . ")";
        }
        if ($target_val eq "&-") {
            return "(redirect \">&-\" 0)";
        }
        $fd_target = ($raw->endswith("-") ? substr($raw, 0, length($raw) - 1 - 0) : $raw);
        return "(redirect \"" . $op . "\" \"" . $fd_target + "\")";
    }
    if ($op eq ">&" || $op eq "<&") {
        if (($target_val =~ /^\d$/) && int($target_val) <= 2147483647) {
            return "(redirect \"" . $op . "\" " . "int($target_val)" . ")";
        }
        if ($target_val eq "-") {
            return "(redirect \">&-\" 0)";
        }
        if ($target_val->endswith("-") && (substr($target_val, 0, length($target_val) - 1 - 0) =~ /^\d$/) && int(substr($target_val, 0, length($target_val) - 1 - 0)) <= 2147483647) {
            return "(redirect \"" . $op . "\" " . "int(substr($target_val, 0, length($target_val) - 1 - 0))" . ")";
        }
        $out_val = ($target_val->endswith("-") ? substr($target_val, 0, length($target_val) - 1 - 0) : $target_val);
        return "(redirect \"" . $op . "\" \"" . $out_val + "\")";
    }
    return "(redirect \"" . $op . "\" \"" . $target_val . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package HereDoc;

sub new ($class, $delimiter, $content, $strip_tabs, $quoted, $fd, $complete, $start_pos, $kind) {
    return bless { delimiter => $delimiter, content => $content, strip_tabs => $strip_tabs, quoted => $quoted, fd => $fd, complete => $complete, start_pos => $start_pos, kind => $kind }, $class;
}

sub delimiter ($self) { $self->{delimiter} }
sub content ($self) { $self->{content} }
sub strip_tabs ($self) { $self->{strip_tabs} }
sub quoted ($self) { $self->{quoted} }
sub fd ($self) { $self->{fd} }
sub complete ($self) { $self->{complete} }
sub start_pos ($self) { $self->{start_pos} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $op = ($self->{strip_tabs} ? "<<-" : "<<");
    my $content = $self->{content};
    if ($content->endswith("\\") && !$content->endswith("\\\\")) {
        $content = $content . "\\";
    }
    return sprintf("(redirect \"%s\" \"%s\")", $op, $content);
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Subshell;

sub new ($class, $body, $redirects, $kind) {
    return bless { body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $base = "(subshell " . $self->{body}->to_sexp() . ")";
    return append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package BraceGroup;

sub new ($class, $body, $redirects, $kind) {
    return bless { body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $base = "(brace-group " . $self->{body}->to_sexp() . ")";
    return append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package If;

sub new ($class, $condition, $then_body, $else_body, $redirects, $kind) {
    return bless { condition => $condition, then_body => $then_body, else_body => $else_body, redirects => $redirects, kind => $kind }, $class;
}

sub condition ($self) { $self->{condition} }
sub then_body ($self) { $self->{then_body} }
sub else_body ($self) { $self->{else_body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $result = "(if " . $self->{condition}->to_sexp() . " " . $self->{then_body}->to_sexp();
    if (defined($self->{else_body})) {
        $result = $result . " " . $self->{else_body}->to_sexp();
    }
    $result = $result . ")";
    for my $r (@{($self->{redirects} // [])}) {
        $result = $result . " " . $r->to_sexp();
    }
    return $result;
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package While;

sub new ($class, $condition, $body, $redirects, $kind) {
    return bless { condition => $condition, body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub condition ($self) { $self->{condition} }
sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $base = "(while " . $self->{condition}->to_sexp() . " " . $self->{body}->to_sexp() . ")";
    return append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Until;

sub new ($class, $condition, $body, $redirects, $kind) {
    return bless { condition => $condition, body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub condition ($self) { $self->{condition} }
sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $base = "(until " . $self->{condition}->to_sexp() . " " . $self->{body}->to_sexp() . ")";
    return append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package For;

sub new ($class, $var, $words, $body, $redirects, $kind) {
    return bless { var => $var, words => $words, body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub var ($self) { $self->{var} }
sub words ($self) { $self->{words} }
sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $redirect_parts;
    my $word_parts;
    my $word_strs;
    my $suffix = "";
    if ((scalar(@{$self->{redirects}}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            $redirect_parts->push($r->to_sexp());
        }
        $suffix = " " . " "->join_($redirect_parts);
    }
    my $temp_word = Word->new($self->{var}, [], "word");
    my $var_formatted = $temp_word->format_command_substitutions($self->{var}, 0);
    my $var_escaped = $var_formatted->replace("\\", "\\\\")->replace("\"", "\\\"");
    if (!defined($self->{words})) {
        return "(for (word \"" . $var_escaped . "\") (in (word \"\\\"\$\@\\\"\")) " . $self->{body}->to_sexp() . ")" . $suffix;
    } elsif (scalar(@{$self->{words}}) == 0) {
        return "(for (word \"" . $var_escaped . "\") (in) " . $self->{body}->to_sexp() . ")" . $suffix;
    } else {
        $word_parts = [];
        for my $w (@{($self->{words} // [])}) {
            $word_parts->push($w->to_sexp());
        }
        $word_strs = " "->join_($word_parts);
        return "(for (word \"" . $var_escaped . "\") (in " . $word_strs . ") " . $self->{body}->to_sexp() . ")" . $suffix;
    }
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ForArith;

sub new ($class, $init, $cond, $incr, $body, $redirects, $kind) {
    return bless { init => $init, cond => $cond, incr => $incr, body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub init ($self) { $self->{init} }
sub cond ($self) { $self->{cond} }
sub incr ($self) { $self->{incr} }
sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $redirect_parts;
    my $suffix = "";
    if ((scalar(@{$self->{redirects}}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            $redirect_parts->push($r->to_sexp());
        }
        $suffix = " " . " "->join_($redirect_parts);
    }
    my $init_val = ((length($self->{init}) > 0) ? $self->{init} : "1");
    my $cond_val = ((length($self->{cond}) > 0) ? $self->{cond} : "1");
    my $incr_val = ((length($self->{incr}) > 0) ? $self->{incr} : "1");
    my $init_str = format_arith_val($init_val);
    my $cond_str = format_arith_val($cond_val);
    my $incr_str = format_arith_val($incr_val);
    my $body_str = $self->{body}->to_sexp();
    return sprintf("(arith-for (init (word \"%s\")) (test (word \"%s\")) (step (word \"%s\")) %s)%s", $init_str, $cond_str, $incr_str, $body_str, $suffix);
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Select;

sub new ($class, $var, $words, $body, $redirects, $kind) {
    return bless { var => $var, words => $words, body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub var ($self) { $self->{var} }
sub words ($self) { $self->{words} }
sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $in_clause;
    my $redirect_parts;
    my $word_parts;
    my $word_strs;
    my $suffix = "";
    if ((scalar(@{$self->{redirects}}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            $redirect_parts->push($r->to_sexp());
        }
        $suffix = " " . " "->join_($redirect_parts);
    }
    my $var_escaped = $self->{var}->replace("\\", "\\\\")->replace("\"", "\\\"");
    my $in_clause = "";
    if (defined($self->{words})) {
        $word_parts = [];
        for my $w (@{($self->{words} // [])}) {
            $word_parts->push($w->to_sexp());
        }
        $word_strs = " "->join_($word_parts);
        if (defined($self->{words})) {
            $in_clause = "(in " . $word_strs . ")";
        } else {
            $in_clause = "(in)";
        }
    } else {
        $in_clause = "(in (word \"\\\"\$\@\\\"\"))";
    }
    return "(select (word \"" . $var_escaped . "\") " . $in_clause . " " . $self->{body}->to_sexp() . ")" . $suffix;
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Case;

sub new ($class, $word, $patterns, $redirects, $kind) {
    return bless { word => $word, patterns => $patterns, redirects => $redirects, kind => $kind }, $class;
}

sub word ($self) { $self->{word} }
sub patterns ($self) { $self->{patterns} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $parts = [];
    $parts->push("(case " . $self->{word}->to_sexp());
    for my $p (@{($self->{patterns} // [])}) {
        $parts->push($p->to_sexp());
    }
    my $base = " "->join_($parts) . ")";
    return append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package CasePattern;

sub new ($class, $pattern, $body, $terminator, $kind) {
    return bless { pattern => $pattern, body => $body, terminator => $terminator, kind => $kind }, $class;
}

sub pattern ($self) { $self->{pattern} }
sub body ($self) { $self->{body} }
sub terminator ($self) { $self->{terminator} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $ch;
    my $result0;
    my $result1;
    my $result2;
    my $alternatives = [];
    my $current = [];
    my $i = 0;
    my $depth = 0;
    while ($i < length($self->{pattern})) {
        $ch = $self->{pattern}->[$i];
        if ($ch eq "\\" && $i + 1 < length($self->{pattern})) {
            $current->push(substring($self->{pattern}, $i, $i + 2));
            $i += 2;
        } elsif (($ch eq "\@" || $ch eq "?" || $ch eq "*" || $ch eq "+" || $ch eq "!") && $i + 1 < length($self->{pattern}) && $self->{pattern}->[$i + 1] eq "(") {
            $current->push($ch);
            $current->push("(");
            $depth += 1;
            $i += 2;
        } elsif (is_expansion_start($self->{pattern}, $i, "\$(")) {
            $current->push($ch);
            $current->push("(");
            $depth += 1;
            $i += 2;
        } elsif ($ch eq "(" && $depth > 0) {
            $current->push($ch);
            $depth += 1;
            $i += 1;
        } elsif ($ch eq ")" && $depth > 0) {
            $current->push($ch);
            $depth -= 1;
            $i += 1;
        } elsif ($ch eq "[") {
            ($result0, $result1, $result2) = @{consume_bracket_class($self->{pattern}, $i, $depth)};
            $i = $result0;
            $current->extend($result1);
        } elsif ($ch eq "'" && $depth == 0) {
            ($result0, $result1) = @{consume_single_quote($self->{pattern}, $i)};
            $i = $result0;
            $current->extend($result1);
        } elsif ($ch eq "\"" && $depth == 0) {
            ($result0, $result1) = @{consume_double_quote($self->{pattern}, $i)};
            $i = $result0;
            $current->extend($result1);
        } elsif ($ch eq "|" && $depth == 0) {
            $alternatives->push(""->join_($current));
            $current = [];
            $i += 1;
        } else {
            $current->push($ch);
            $i += 1;
        }
    }
    $alternatives->push(""->join_($current));
    my $word_list = [];
    for my $alt (@{$alternatives}) {
        $word_list->push(Word->new($alt, "word")->to_sexp());
    }
    my $pattern_str = " "->join_($word_list);
    my $parts = ["(pattern (" . $pattern_str . ")"];
    if (defined($self->{body})) {
        $parts->push(" " . $self->{body}->to_sexp());
    } else {
        $parts->push(" ()");
    }
    $parts->push(")");
    return ""->join_($parts);
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Function;

sub new ($class, $name, $body, $kind) {
    return bless { name => $name, body => $body, kind => $kind }, $class;
}

sub name ($self) { $self->{name} }
sub body ($self) { $self->{body} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(function \"" . $self->{name} . "\" " . $self->{body}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ParamExpansion;

sub new ($class, $param, $op, $arg, $kind) {
    return bless { param => $param, op => $op, arg => $arg, kind => $kind }, $class;
}

sub param ($self) { $self->{param} }
sub op ($self) { $self->{op} }
sub arg ($self) { $self->{arg} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $arg_val;
    my $escaped_arg;
    my $escaped_op;
    my $escaped_param = $self->{param}->replace("\\", "\\\\")->replace("\"", "\\\"");
    if ($self->{op} ne "") {
        $escaped_op = $self->{op}->replace("\\", "\\\\")->replace("\"", "\\\"");
        my $arg_val = "";
        if ($self->{arg} ne "") {
            $arg_val = $self->{arg};
        } else {
            $arg_val = "";
        }
        $escaped_arg = $arg_val->replace("\\", "\\\\")->replace("\"", "\\\"");
        return "(param \"" . $escaped_param . "\" \"" . $escaped_op + "\" \"" . $escaped_arg + "\")";
    }
    return "(param \"" . $escaped_param . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ParamLength;

sub new ($class, $param, $kind) {
    return bless { param => $param, kind => $kind }, $class;
}

sub param ($self) { $self->{param} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $escaped = $self->{param}->replace("\\", "\\\\")->replace("\"", "\\\"");
    return "(param-len \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ParamIndirect;

sub new ($class, $param, $op, $arg, $kind) {
    return bless { param => $param, op => $op, arg => $arg, kind => $kind }, $class;
}

sub param ($self) { $self->{param} }
sub op ($self) { $self->{op} }
sub arg ($self) { $self->{arg} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $arg_val;
    my $escaped_arg;
    my $escaped_op;
    my $escaped = $self->{param}->replace("\\", "\\\\")->replace("\"", "\\\"");
    if ($self->{op} ne "") {
        $escaped_op = $self->{op}->replace("\\", "\\\\")->replace("\"", "\\\"");
        my $arg_val = "";
        if ($self->{arg} ne "") {
            $arg_val = $self->{arg};
        } else {
            $arg_val = "";
        }
        $escaped_arg = $arg_val->replace("\\", "\\\\")->replace("\"", "\\\"");
        return "(param-indirect \"" . $escaped . "\" \"" . $escaped_op + "\" \"" . $escaped_arg + "\")";
    }
    return "(param-indirect \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package CommandSubstitution;

sub new ($class, $command, $brace, $kind) {
    return bless { command => $command, brace => $brace, kind => $kind }, $class;
}

sub command ($self) { $self->{command} }
sub brace ($self) { $self->{brace} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    if ($self->{brace}) {
        return "(funsub " . $self->{command}->to_sexp() . ")";
    }
    return "(cmdsub " . $self->{command}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithmeticExpansion;

sub new ($class, $expression, $kind) {
    return bless { expression => $expression, kind => $kind }, $class;
}

sub expression ($self) { $self->{expression} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    if (!defined($self->{expression})) {
        return "(arith)";
    }
    return "(arith " . $self->{expression}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithmeticCommand;

sub new ($class, $expression, $redirects, $raw_content, $kind) {
    return bless { expression => $expression, redirects => $redirects, raw_content => $raw_content, kind => $kind }, $class;
}

sub expression ($self) { $self->{expression} }
sub redirects ($self) { $self->{redirects} }
sub raw_content ($self) { $self->{raw_content} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $redirect_parts;
    my $redirect_sexps;
    my $formatted = Word->new($self->{raw_content}, "word")->format_command_substitutions($self->{raw_content}, 1);
    my $escaped = $formatted->replace("\\", "\\\\")->replace("\"", "\\\"")->replace("\n", "\\n")->replace("\t", "\\t");
    my $result = "(arith (word \"" . $escaped . "\"))";
    if ((scalar(@{$self->{redirects}}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            $redirect_parts->push($r->to_sexp());
        }
        $redirect_sexps = " "->join_($redirect_parts);
        return $result . " " . $redirect_sexps;
    }
    return $result;
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithNumber;

sub new ($class, $value, $kind) {
    return bless { value => $value, kind => $kind }, $class;
}

sub value ($self) { $self->{value} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(number \"" . $self->{value} . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithEmpty;

sub new ($class, $kind) {
    return bless { kind => $kind }, $class;
}

sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(empty)";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithVar;

sub new ($class, $name, $kind) {
    return bless { name => $name, kind => $kind }, $class;
}

sub name ($self) { $self->{name} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(var \"" . $self->{name} . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithBinaryOp;

sub new ($class, $op, $left, $right, $kind) {
    return bless { op => $op, left => $left, right => $right, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub left ($self) { $self->{left} }
sub right ($self) { $self->{right} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(binary-op \"" . $self->{op} . "\" " . $self->{left}->to_sexp() . " " . $self->{right}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithUnaryOp;

sub new ($class, $op, $operand, $kind) {
    return bless { op => $op, operand => $operand, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub operand ($self) { $self->{operand} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(unary-op \"" . $self->{op} . "\" " . $self->{operand}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithPreIncr;

sub new ($class, $operand, $kind) {
    return bless { operand => $operand, kind => $kind }, $class;
}

sub operand ($self) { $self->{operand} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(pre-incr " . $self->{operand}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithPostIncr;

sub new ($class, $operand, $kind) {
    return bless { operand => $operand, kind => $kind }, $class;
}

sub operand ($self) { $self->{operand} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(post-incr " . $self->{operand}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithPreDecr;

sub new ($class, $operand, $kind) {
    return bless { operand => $operand, kind => $kind }, $class;
}

sub operand ($self) { $self->{operand} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(pre-decr " . $self->{operand}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithPostDecr;

sub new ($class, $operand, $kind) {
    return bless { operand => $operand, kind => $kind }, $class;
}

sub operand ($self) { $self->{operand} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(post-decr " . $self->{operand}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithAssign;

sub new ($class, $op, $target, $value, $kind) {
    return bless { op => $op, target => $target, value => $value, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub target ($self) { $self->{target} }
sub value ($self) { $self->{value} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(assign \"" . $self->{op} . "\" " . $self->{target}->to_sexp() . " " . $self->{value}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithTernary;

sub new ($class, $condition, $if_true, $if_false, $kind) {
    return bless { condition => $condition, if_true => $if_true, if_false => $if_false, kind => $kind }, $class;
}

sub condition ($self) { $self->{condition} }
sub if_true ($self) { $self->{if_true} }
sub if_false ($self) { $self->{if_false} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(ternary " . $self->{condition}->to_sexp() . " " . $self->{if_true}->to_sexp() . " " . $self->{if_false}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithComma;

sub new ($class, $left, $right, $kind) {
    return bless { left => $left, right => $right, kind => $kind }, $class;
}

sub left ($self) { $self->{left} }
sub right ($self) { $self->{right} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(comma " . $self->{left}->to_sexp() . " " . $self->{right}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithSubscript;

sub new ($class, $array, $index_, $kind) {
    return bless { array => $array, index_ => $index_, kind => $kind }, $class;
}

sub array ($self) { $self->{array} }
sub index_ ($self) { $self->{index_} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(subscript \"" . $self->{array} . "\" " . $self->{index_}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithEscape;

sub new ($class, $char, $kind) {
    return bless { char => $char, kind => $kind }, $class;
}

sub char ($self) { $self->{char} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(escape \"" . $self->{char} . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithDeprecated;

sub new ($class, $expression, $kind) {
    return bless { expression => $expression, kind => $kind }, $class;
}

sub expression ($self) { $self->{expression} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $escaped = $self->{expression}->replace("\\", "\\\\")->replace("\"", "\\\"")->replace("\n", "\\n");
    return "(arith-deprecated \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithConcat;

sub new ($class, $parts, $kind) {
    return bless { parts => $parts, kind => $kind }, $class;
}

sub parts ($self) { $self->{parts} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $sexps = [];
    for my $p (@{($self->{parts} // [])}) {
        $sexps->push($p->to_sexp());
    }
    return "(arith-concat " . " "->join_($sexps) . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package AnsiCQuote;

sub new ($class, $content, $kind) {
    return bless { content => $content, kind => $kind }, $class;
}

sub content ($self) { $self->{content} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $escaped = $self->{content}->replace("\\", "\\\\")->replace("\"", "\\\"")->replace("\n", "\\n");
    return "(ansi-c \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package LocaleString;

sub new ($class, $content, $kind) {
    return bless { content => $content, kind => $kind }, $class;
}

sub content ($self) { $self->{content} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $escaped = $self->{content}->replace("\\", "\\\\")->replace("\"", "\\\"")->replace("\n", "\\n");
    return "(locale \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ProcessSubstitution;

sub new ($class, $direction, $command, $kind) {
    return bless { direction => $direction, command => $command, kind => $kind }, $class;
}

sub direction ($self) { $self->{direction} }
sub command ($self) { $self->{command} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(procsub \"" . $self->{direction} . "\" " . $self->{command}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Negation;

sub new ($class, $pipeline, $kind) {
    return bless { pipeline => $pipeline, kind => $kind }, $class;
}

sub pipeline ($self) { $self->{pipeline} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    if (!defined($self->{pipeline})) {
        return "(negation (command))";
    }
    return "(negation " . $self->{pipeline}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Time;

sub new ($class, $pipeline, $posix, $kind) {
    return bless { pipeline => $pipeline, posix => $posix, kind => $kind }, $class;
}

sub pipeline ($self) { $self->{pipeline} }
sub posix ($self) { $self->{posix} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    if (!defined($self->{pipeline})) {
        if ($self->{posix}) {
            return "(time -p (command))";
        } else {
            return "(time (command))";
        }
    }
    if ($self->{posix}) {
        return "(time -p " . $self->{pipeline}->to_sexp() . ")";
    }
    return "(time " . $self->{pipeline}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ConditionalExpr;

sub new ($class, $body, $redirects, $kind) {
    return bless { body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $escaped;
    my $redirect_parts;
    my $redirect_sexps;
    my $result;
    my $body = $self->{body};
    my $result = "";
    if (ref($body) eq 'string') {
        my $body = $body;
        $escaped = $body->replace("\\", "\\\\")->replace("\"", "\\\"")->replace("\n", "\\n");
        $result = "(cond \"" . $escaped . "\")";
    } else {
        $result = "(cond " . $body->to_sexp() . ")";
    }
    if ((scalar(@{$self->{redirects}}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            $redirect_parts->push($r->to_sexp());
        }
        $redirect_sexps = " "->join_($redirect_parts);
        return $result . " " . $redirect_sexps;
    }
    return $result;
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package UnaryTest;

sub new ($class, $op, $operand, $kind) {
    return bless { op => $op, operand => $operand, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub operand ($self) { $self->{operand} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $operand_val = $self->{operand}->get_cond_formatted_value();
    return "(cond-unary \"" . $self->{op} . "\" (cond-term \"" . $operand_val + "\"))";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package BinaryTest;

sub new ($class, $op, $left, $right, $kind) {
    return bless { op => $op, left => $left, right => $right, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub left ($self) { $self->{left} }
sub right ($self) { $self->{right} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $left_val = $self->{left}->get_cond_formatted_value();
    my $right_val = $self->{right}->get_cond_formatted_value();
    return "(cond-binary \"" . $self->{op} . "\" (cond-term \"" . $left_val + "\") (cond-term \"" . $right_val + "\"))";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package CondAnd;

sub new ($class, $left, $right, $kind) {
    return bless { left => $left, right => $right, kind => $kind }, $class;
}

sub left ($self) { $self->{left} }
sub right ($self) { $self->{right} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(cond-and " . $self->{left}->to_sexp() . " " . $self->{right}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package CondOr;

sub new ($class, $left, $right, $kind) {
    return bless { left => $left, right => $right, kind => $kind }, $class;
}

sub left ($self) { $self->{left} }
sub right ($self) { $self->{right} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(cond-or " . $self->{left}->to_sexp() . " " . $self->{right}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package CondNot;

sub new ($class, $operand, $kind) {
    return bless { operand => $operand, kind => $kind }, $class;
}

sub operand ($self) { $self->{operand} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return $self->{operand}->to_sexp();
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package CondParen;

sub new ($class, $inner, $kind) {
    return bless { inner => $inner, kind => $kind }, $class;
}

sub inner ($self) { $self->{inner} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    return "(cond-expr " . $self->{inner}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Array;

sub new ($class, $elements, $kind) {
    return bless { elements => $elements, kind => $kind }, $class;
}

sub elements ($self) { $self->{elements} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    if (!(scalar(@{$self->{elements}}) > 0)) {
        return "(array)";
    }
    my $parts = [];
    for my $e (@{($self->{elements} // [])}) {
        $parts->push($e->to_sexp());
    }
    my $inner = " "->join_($parts);
    return "(array " . $inner . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Coproc;

sub new ($class, $command, $name, $kind) {
    return bless { command => $command, name => $name, kind => $kind }, $class;
}

sub command ($self) { $self->{command} }
sub name ($self) { $self->{name} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $name;
    my $name = "";
    if ((length($self->{name}) > 0)) {
        $name = $self->{name};
    } else {
        $name = "COPROC";
    }
    return "(coproc \"" . $name . "\" " . $self->{command}->to_sexp() . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Parser;

sub new ($class, $source, $pos_, $length_, $pending_heredocs, $cmdsub_heredoc_end, $saw_newline_in_single_quote, $in_process_sub, $extglob, $ctx, $lexer, $token_history, $parser_state, $dolbrace_state, $eof_token, $word_context, $at_command_start, $in_array_literal, $in_assign_builtin, $arith_src, $arith_pos, $arith_len) {
    return bless { source => $source, pos_ => $pos_, length_ => $length_, pending_heredocs => $pending_heredocs, cmdsub_heredoc_end => $cmdsub_heredoc_end, saw_newline_in_single_quote => $saw_newline_in_single_quote, in_process_sub => $in_process_sub, extglob => $extglob, ctx => $ctx, lexer => $lexer, token_history => $token_history, parser_state => $parser_state, dolbrace_state => $dolbrace_state, eof_token => $eof_token, word_context => $word_context, at_command_start => $at_command_start, in_array_literal => $in_array_literal, in_assign_builtin => $in_assign_builtin, arith_src => $arith_src, arith_pos => $arith_pos, arith_len => $arith_len }, $class;
}

sub source ($self) { $self->{source} }
sub pos_ ($self) { $self->{pos_} }
sub length_ ($self) { $self->{length_} }
sub pending_heredocs ($self) { $self->{pending_heredocs} }
sub cmdsub_heredoc_end ($self) { $self->{cmdsub_heredoc_end} }
sub saw_newline_in_single_quote ($self) { $self->{saw_newline_in_single_quote} }
sub in_process_sub ($self) { $self->{in_process_sub} }
sub extglob ($self) { $self->{extglob} }
sub ctx ($self) { $self->{ctx} }
sub lexer ($self) { $self->{lexer} }
sub token_history ($self) { $self->{token_history} }
sub parser_state ($self) { $self->{parser_state} }
sub dolbrace_state ($self) { $self->{dolbrace_state} }
sub eof_token ($self) { $self->{eof_token} }
sub word_context ($self) { $self->{word_context} }
sub at_command_start ($self) { $self->{at_command_start} }
sub in_array_literal ($self) { $self->{in_array_literal} }
sub in_assign_builtin ($self) { $self->{in_assign_builtin} }
sub arith_src ($self) { $self->{arith_src} }
sub arith_pos ($self) { $self->{arith_pos} }
sub arith_len ($self) { $self->{arith_len} }

sub set_state ($self, $flag) {
    $self->{parser_state} = $self->{parser_state} | $flag;
}

sub clear_state ($self, $flag) {
    $self->{parser_state} = $self->{parser_state} & ~$flag;
}

sub in_state ($self, $flag) {
    return ($self->{parser_state} & $flag) != 0;
}

sub save_parser_state ($self) {
    return SavedParserState->new($self->{parser_state}, $self->{dolbrace_state}, $self->{pending_heredocs}, $self->{ctx}->copy_stack(), $self->{eof_token});
}

sub restore_parser_state ($self, $saved) {
    $self->{parser_state} = $saved->{parser_state};
    $self->{dolbrace_state} = $saved->{dolbrace_state};
    $self->{eof_token} = $saved->{eof_token};
    $self->{ctx}->restore_from($saved->{ctx_stack});
}

sub record_token ($self, $tok) {
    $self->{token_history} = [$tok, $self->{token_history}->[0], $self->{token_history}->[1], $self->{token_history}->[2]];
}

sub update_dolbrace_for_op ($self, $op, $has_param) {
    if ($self->{dolbrace_state} == DOLBRACESTATE_NONE()) {
        return;
    }
    if ($op eq "" || length($op) == 0) {
        return;
    }
    my $first_char = $op->[0];
    if ($self->{dolbrace_state} == DOLBRACESTATE_PARAM() && $has_param) {
        if ((index("%#^,", $first_char) >= 0)) {
            $self->{dolbrace_state} = DOLBRACESTATE_QUOTE();
            return;
        }
        if ($first_char eq "/") {
            $self->{dolbrace_state} = DOLBRACESTATE_QUOTE2();
            return;
        }
    }
    if ($self->{dolbrace_state} == DOLBRACESTATE_PARAM()) {
        if ((index("#%^,~:-=?+/", $first_char) >= 0)) {
            $self->{dolbrace_state} = DOLBRACESTATE_OP();
        }
    }
}

sub sync_lexer ($self) {
    if (defined($self->{lexer}->{token_cache})) {
        if ($self->{lexer}->{token_cache}->{pos_} != $self->{pos_} || $self->{lexer}->{cached_word_context} != $self->{word_context} || $self->{lexer}->{cached_at_command_start} != $self->{at_command_start} || $self->{lexer}->{cached_in_array_literal} != $self->{in_array_literal} || $self->{lexer}->{cached_in_assign_builtin} != $self->{in_assign_builtin}) {
            $self->{lexer}->{token_cache} = undef;
        }
    }
    if ($self->{lexer}->{pos_} != $self->{pos_}) {
        $self->{lexer}->{pos_} = $self->{pos_};
    }
    $self->{lexer}->{eof_token} = $self->{eof_token};
    $self->{lexer}->{parser_state} = $self->{parser_state};
    $self->{lexer}->{last_read_token} = $self->{token_history}->[0];
    $self->{lexer}->{word_context} = $self->{word_context};
    $self->{lexer}->{at_command_start} = $self->{at_command_start};
    $self->{lexer}->{in_array_literal} = $self->{in_array_literal};
    $self->{lexer}->{in_assign_builtin} = $self->{in_assign_builtin};
}

sub sync_parser ($self) {
    $self->{pos_} = $self->{lexer}->{pos_};
}

sub lex_peek_token ($self) {
    if (defined($self->{lexer}->{token_cache}) && $self->{lexer}->{token_cache}->{pos_} == $self->{pos_} && $self->{lexer}->{cached_word_context} == $self->{word_context} && $self->{lexer}->{cached_at_command_start} == $self->{at_command_start} && $self->{lexer}->{cached_in_array_literal} == $self->{in_array_literal} && $self->{lexer}->{cached_in_assign_builtin} == $self->{in_assign_builtin}) {
        return $self->{lexer}->{token_cache};
    }
    my $saved_pos = $self->{pos_};
    $self->sync_lexer();
    my $result = $self->{lexer}->peek_token();
    $self->{lexer}->{cached_word_context} = $self->{word_context};
    $self->{lexer}->{cached_at_command_start} = $self->{at_command_start};
    $self->{lexer}->{cached_in_array_literal} = $self->{in_array_literal};
    $self->{lexer}->{cached_in_assign_builtin} = $self->{in_assign_builtin};
    $self->{lexer}->{post_read_pos} = $self->{lexer}->{pos_};
    $self->{pos_} = $saved_pos;
    return $result;
}

sub lex_next_token ($self) {
    my $tok;
    my $tok = undef;
    if (defined($self->{lexer}->{token_cache}) && $self->{lexer}->{token_cache}->{pos_} == $self->{pos_} && $self->{lexer}->{cached_word_context} == $self->{word_context} && $self->{lexer}->{cached_at_command_start} == $self->{at_command_start} && $self->{lexer}->{cached_in_array_literal} == $self->{in_array_literal} && $self->{lexer}->{cached_in_assign_builtin} == $self->{in_assign_builtin}) {
        $tok = $self->{lexer}->next_token();
        $self->{pos_} = $self->{lexer}->{post_read_pos};
        $self->{lexer}->{pos_} = $self->{lexer}->{post_read_pos};
    } else {
        $self->sync_lexer();
        $tok = $self->{lexer}->next_token();
        $self->{lexer}->{cached_word_context} = $self->{word_context};
        $self->{lexer}->{cached_at_command_start} = $self->{at_command_start};
        $self->{lexer}->{cached_in_array_literal} = $self->{in_array_literal};
        $self->{lexer}->{cached_in_assign_builtin} = $self->{in_assign_builtin};
        $self->sync_parser();
    }
    $self->record_token($tok);
    return $tok;
}

sub lex_skip_blanks ($self) {
    $self->sync_lexer();
    $self->{lexer}->skip_blanks();
    $self->sync_parser();
}

sub lex_skip_comment ($self) {
    $self->sync_lexer();
    my $result = $self->{lexer}->skip_comment();
    $self->sync_parser();
    return $result;
}

sub lex_is_command_terminator ($self) {
    my $tok = $self->lex_peek_token();
    my $t = $tok->{type};
    return $t == TOKENTYPE_EOF() || $t == TOKENTYPE_NEWLINE() || $t == TOKENTYPE_PIPE() || $t == TOKENTYPE_SEMI() || $t == TOKENTYPE_LPAREN() || $t == TOKENTYPE_RPAREN() || $t == TOKENTYPE_AMP();
}

sub lex_peek_operator ($self) {
    my $tok = $self->lex_peek_token();
    my $t = $tok->{type};
    if ($t >= TOKENTYPE_SEMI() && $t <= TOKENTYPE_GREATER() || $t >= TOKENTYPE_AND_AND() && $t <= TOKENTYPE_PIPE_AMP()) {
        return [$t, $tok->{value}];
    }
    return [0, ""];
}

sub lex_peek_reserved_word ($self) {
    my $tok = $self->lex_peek_token();
    if ($tok->{type} != TOKENTYPE_WORD()) {
        return "";
    }
    my $word = $tok->{value};
    if ($word->endswith("\\\n")) {
        $word = substr($word, 0, length($word) - 2 - 0);
    }
    if ((exists(RESERVED_WORDS()->{$word})) || $word eq "{" || $word eq "}" || $word eq "[[" || $word eq "]]" || $word eq "!" || $word eq "time") {
        return $word;
    }
    return "";
}

sub lex_is_at_reserved_word ($self, $word) {
    my $reserved = $self->lex_peek_reserved_word();
    return $reserved eq $word;
}

sub lex_consume_word ($self, $expected) {
    my $tok = $self->lex_peek_token();
    if ($tok->{type} != TOKENTYPE_WORD()) {
        return 0;
    }
    my $word = $tok->{value};
    if ($word->endswith("\\\n")) {
        $word = substr($word, 0, length($word) - 2 - 0);
    }
    if ($word eq $expected) {
        $self->lex_next_token();
        return 1;
    }
    return 0;
}

sub lex_peek_case_terminator ($self) {
    my $tok = $self->lex_peek_token();
    my $t = $tok->{type};
    if ($t == TOKENTYPE_SEMI_SEMI()) {
        return ";;";
    }
    if ($t == TOKENTYPE_SEMI_AMP()) {
        return ";&";
    }
    if ($t == TOKENTYPE_SEMI_SEMI_AMP()) {
        return ";;&";
    }
    return "";
}

sub at_end ($self) {
    return $self->{pos_} >= $self->{length_};
}

sub peek ($self) {
    if ($self->at_end()) {
        return "";
    }
    return $self->{source}->[$self->{pos_}];
}

sub advance ($self) {
    if ($self->at_end()) {
        return "";
    }
    my $ch = $self->{source}->[$self->{pos_}];
    $self->{pos_} += 1;
    return $ch;
}

sub peek_at ($self, $offset) {
    my $pos_ = $self->{pos_} + $offset;
    if ($pos_ < 0 || $pos_ >= $self->{length_}) {
        return "";
    }
    return $self->{source}->[$pos_];
}

sub lookahead ($self, $n) {
    return substring($self->{source}, $self->{pos_}, $self->{pos_} + $n);
}

sub is_bang_followed_by_procsub ($self) {
    if ($self->{pos_} + 2 >= $self->{length_}) {
        return 0;
    }
    my $next_char = $self->{source}->[$self->{pos_} + 1];
    if ($next_char ne ">" && $next_char ne "<") {
        return 0;
    }
    return $self->{source}->[$self->{pos_} + 2] eq "(";
}

sub skip_whitespace ($self) {
    my $ch;
    while (!$self->at_end()) {
        $self->lex_skip_blanks();
        if ($self->at_end()) {
            last;
        }
        $ch = $self->peek();
        if ($ch eq "#") {
            $self->lex_skip_comment();
        } elsif ($ch eq "\\" && $self->peek_at(1) eq "\n") {
            $self->advance();
            $self->advance();
        } else {
            last;
        }
    }
}

sub skip_whitespace_and_newlines ($self) {
    my $ch;
    while (!$self->at_end()) {
        $ch = $self->peek();
        if (is_whitespace($ch)) {
            $self->advance();
            if ($ch eq "\n") {
                $self->gather_heredoc_bodies();
                if ($self->{cmdsub_heredoc_end} != -1 && $self->{cmdsub_heredoc_end} > $self->{pos_}) {
                    $self->{pos_} = $self->{cmdsub_heredoc_end};
                    $self->{cmdsub_heredoc_end} = -1;
                }
            }
        } elsif ($ch eq "#") {
            while (!$self->at_end() && $self->peek() ne "\n") {
                $self->advance();
            }
        } elsif ($ch eq "\\" && $self->peek_at(1) eq "\n") {
            $self->advance();
            $self->advance();
        } else {
            last;
        }
    }
}

sub at_list_terminating_bracket ($self) {
    my $next_pos;
    if ($self->at_end()) {
        return 0;
    }
    my $ch = $self->peek();
    if ($self->{eof_token} ne "" && $ch eq $self->{eof_token}) {
        return 1;
    }
    if ($ch eq ")") {
        return 1;
    }
    if ($ch eq "}") {
        $next_pos = $self->{pos_} + 1;
        if ($next_pos >= $self->{length_}) {
            return 1;
        }
        return is_word_end_context($self->{source}->[$next_pos]);
    }
    return 0;
}

sub at_eof_token ($self) {
    if ($self->{eof_token} eq "") {
        return 0;
    }
    my $tok = $self->lex_peek_token();
    if ($self->{eof_token} eq ")") {
        return $tok->{type} == TOKENTYPE_RPAREN();
    }
    if ($self->{eof_token} eq "}") {
        return $tok->{type} == TOKENTYPE_WORD() && $tok->{value} eq "}";
    }
    return 0;
}

sub collect_redirects ($self) {
    my $redirect;
    my $redirects = [];
    while (1) {
        $self->skip_whitespace();
        $redirect = $self->parse_redirect();
        if (!defined($redirect)) {
            last;
        }
        $redirects->push($redirect);
    }
    return ((scalar(@{$redirects}) > 0) ? $redirects : undef);
}

sub parse_loop_body ($self, $context) {
    my $body;
    my $brace;
    if ($self->peek() eq "{") {
        $brace = $self->parse_brace_group();
        if (!defined($brace)) {
            die sprintf("Expected brace group body in %s", $context);
        }
        return $brace->{body};
    }
    if ($self->lex_consume_word("do")) {
        $body = $self->parse_list_until({"done" => 1});
        if (!defined($body)) {
            die "Expected commands after 'do'";
        }
        $self->skip_whitespace_and_newlines();
        if (!$self->lex_consume_word("done")) {
            die sprintf("Expected 'done' to close %s", $context);
        }
        return $body;
    }
    die sprintf("Expected 'do' or '{' in %s", $context);
}

sub peek_word ($self) {
    my $ch;
    my $word;
    my $saved_pos = $self->{pos_};
    $self->skip_whitespace();
    if ($self->at_end() || is_metachar($self->peek())) {
        $self->{pos_} = $saved_pos;
        return "";
    }
    my $chars = [];
    while (!$self->at_end() && !is_metachar($self->peek())) {
        $ch = $self->peek();
        if (is_quote($ch)) {
            last;
        }
        if ($ch eq "\\" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "\n") {
            last;
        }
        if ($ch eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $chars->push($self->advance());
            $chars->push($self->advance());
            next;
        }
        $chars->push($self->advance());
    }
    my $word = "";
    if ((scalar(@{$chars}) > 0)) {
        $word = ""->join_($chars);
    } else {
        $word = "";
    }
    $self->{pos_} = $saved_pos;
    return $word;
}

sub consume_word ($self, $expected) {
    my $saved_pos = $self->{pos_};
    $self->skip_whitespace();
    my $word = $self->peek_word();
    my $keyword_word = $word;
    my $has_leading_brace = 0;
    if ($word ne "" && $self->{in_process_sub} && length($word) > 1 && $word->[0] eq "}") {
        $keyword_word = substr($word, 1);
        $has_leading_brace = 1;
    }
    if ($keyword_word ne $expected) {
        $self->{pos_} = $saved_pos;
        return 0;
    }
    $self->skip_whitespace();
    if ($has_leading_brace) {
        $self->advance();
    }
    for (@{$expected}) {
        $self->advance();
    }
    while ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "\n") {
        $self->advance();
        $self->advance();
    }
    return 1;
}

sub is_word_terminator ($self, $ctx, $ch, $bracket_depth, $paren_depth) {
    $self->sync_lexer();
    return $self->{lexer}->is_word_terminator($ctx, $ch, $bracket_depth, $paren_depth);
}

sub scan_double_quote ($self, $chars, $parts, $start, $handle_line_continuation) {
    my $c;
    my $next_c;
    $chars->append("\"");
    while (!$self->at_end() && $self->peek() ne "\"") {
        $c = $self->peek();
        if ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $next_c = $self->{source}->[$self->{pos_} + 1];
            if ($handle_line_continuation && $next_c eq "\n") {
                $self->advance();
                $self->advance();
            } else {
                $chars->append($self->advance());
                $chars->append($self->advance());
            }
        } elsif ($c eq "\$") {
            if (!$self->parse_dollar_expansion($chars, $parts, 1)) {
                $chars->append($self->advance());
            }
        } else {
            $chars->append($self->advance());
        }
    }
    if ($self->at_end()) {
        die "Unterminated double quote";
    }
    $chars->append($self->advance());
}

sub parse_dollar_expansion ($self, $chars, $parts, $in_dquote) {
    my $result0;
    my $result1;
    my $result0 = undef;
    my $result1 = "";
    if ($self->{pos_} + 2 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(" && $self->{source}->[$self->{pos_} + 2] eq "(") {
        ($result0, $result1) = @{$self->parse_arithmetic_expansion()};
        if (defined($result0)) {
            $parts->append($result0);
            $chars->append($result1);
            return 1;
        }
        ($result0, $result1) = @{$self->parse_command_substitution()};
        if (defined($result0)) {
            $parts->append($result0);
            $chars->append($result1);
            return 1;
        }
        return 0;
    }
    if ($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "[") {
        ($result0, $result1) = @{$self->parse_deprecated_arithmetic()};
        if (defined($result0)) {
            $parts->append($result0);
            $chars->append($result1);
            return 1;
        }
        return 0;
    }
    if ($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
        ($result0, $result1) = @{$self->parse_command_substitution()};
        if (defined($result0)) {
            $parts->append($result0);
            $chars->append($result1);
            return 1;
        }
        return 0;
    }
    ($result0, $result1) = @{$self->parse_param_expansion($in_dquote)};
    if (defined($result0)) {
        $parts->append($result0);
        $chars->append($result1);
        return 1;
    }
    return 0;
}

sub parse_word_internal ($self, $ctx, $at_command_start, $in_array_literal) {
    $self->{word_context} = $ctx;
    return $self->parse_word($at_command_start, $in_array_literal, 0);
}

sub parse_word ($self, $at_command_start, $in_array_literal, $in_assign_builtin) {
    $self->skip_whitespace();
    if ($self->at_end()) {
        return undef;
    }
    $self->{at_command_start} = $at_command_start;
    $self->{in_array_literal} = $in_array_literal;
    $self->{in_assign_builtin} = $in_assign_builtin;
    my $tok = $self->lex_peek_token();
    if ($tok->{type} != TOKENTYPE_WORD()) {
        $self->{at_command_start} = 0;
        $self->{in_array_literal} = 0;
        $self->{in_assign_builtin} = 0;
        return undef;
    }
    $self->lex_next_token();
    $self->{at_command_start} = 0;
    $self->{in_array_literal} = 0;
    $self->{in_assign_builtin} = 0;
    return $tok->{word};
}

sub parse_command_substitution ($self) {
    if ($self->at_end() || $self->peek() ne "\$") {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    $self->advance();
    if ($self->at_end() || $self->peek() ne "(") {
        $self->{pos_} = $start;
        return [undef, ""];
    }
    $self->advance();
    my $saved = $self->save_parser_state();
    $self->set_state(PARSERSTATEFLAGS_PST_CMDSUBST() | PARSERSTATEFLAGS_PST_EOFTOKEN());
    $self->{eof_token} = ")";
    my $cmd = $self->parse_list(1);
    if (!defined($cmd)) {
        $cmd = Empty->new("empty");
    }
    $self->skip_whitespace_and_newlines();
    if ($self->at_end() || $self->peek() ne ")") {
        $self->restore_parser_state($saved);
        $self->{pos_} = $start;
        return [undef, ""];
    }
    $self->advance();
    my $text_end = $self->{pos_};
    my $text = substring($self->{source}, $start, $text_end);
    $self->restore_parser_state($saved);
    return [CommandSubstitution->new($cmd, "cmdsub"), $text];
}

sub parse_funsub ($self, $start) {
    $self->sync_parser();
    if (!$self->at_end() && $self->peek() eq "|") {
        $self->advance();
    }
    my $saved = $self->save_parser_state();
    $self->set_state(PARSERSTATEFLAGS_PST_CMDSUBST() | PARSERSTATEFLAGS_PST_EOFTOKEN());
    $self->{eof_token} = "}";
    my $cmd = $self->parse_list(1);
    if (!defined($cmd)) {
        $cmd = Empty->new("empty");
    }
    $self->skip_whitespace_and_newlines();
    if ($self->at_end() || $self->peek() ne "}") {
        $self->restore_parser_state($saved);
        die "unexpected EOF looking for `}'";
    }
    $self->advance();
    my $text = substring($self->{source}, $start, $self->{pos_});
    $self->restore_parser_state($saved);
    $self->sync_lexer();
    return [CommandSubstitution->new($cmd, 1, "cmdsub"), $text];
}

sub is_assignment_word ($self, $word) {
    return assignment($word->{value}, 0) != -1;
}

sub parse_backtick_substitution ($self) {
    my $c;
    my $ch;
    my $check_line;
    my $closing;
    my $dch;
    my $delimiter;
    my $end_pos;
    my $esc;
    my $escaped;
    my $heredoc_end;
    my $heredoc_start;
    my $line;
    my $line_end;
    my $line_start;
    my $next_c;
    my $quote;
    my $strip_tabs;
    my $tabs_stripped;
    if ($self->at_end() || $self->peek() ne "`") {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    $self->advance();
    my $content_chars = [];
    my $text_chars = ["`"];
    my $pending_heredocs = [];
    my $in_heredoc_body = 0;
    my $current_heredoc_delim = "";
    my $current_heredoc_strip = 0;
    while (!$self->at_end() && ($in_heredoc_body || $self->peek() ne "`")) {
        if ($in_heredoc_body) {
            $line_start = $self->{pos_};
            $line_end = $line_start;
            while ($line_end < $self->{length_} && $self->{source}->[$line_end] ne "\n") {
                $line_end += 1;
            }
            $line = substring($self->{source}, $line_start, $line_end);
            $check_line = ($current_heredoc_strip ? ($line =~ s/^["\t"]+//r) : $line);
            if ($check_line eq $current_heredoc_delim) {
                for my $ch (@{$line}) {
                    $content_chars->push($ch);
                    $text_chars->push($ch);
                }
                $self->{pos_} = $line_end;
                if ($self->{pos_} < $self->{length_} && $self->{source}->[$self->{pos_}] eq "\n") {
                    $content_chars->push("\n");
                    $text_chars->push("\n");
                    $self->advance();
                }
                $in_heredoc_body = 0;
                if (scalar(@{$pending_heredocs}) > 0) {
                    ($current_heredoc_delim, $current_heredoc_strip) = @{$pending_heredocs->pop_(0)};
                    $in_heredoc_body = 1;
                }
            } elsif ($check_line->startswith($current_heredoc_delim) && length($check_line) > length($current_heredoc_delim)) {
                $tabs_stripped = length($line) - length($check_line);
                $end_pos = $tabs_stripped + length($current_heredoc_delim);
                for (my $i = 0; $i < $end_pos; $i += 1) {
                    $content_chars->push($line->[$i]);
                    $text_chars->push($line->[$i]);
                }
                $self->{pos_} = $line_start + $end_pos;
                $in_heredoc_body = 0;
                if (scalar(@{$pending_heredocs}) > 0) {
                    ($current_heredoc_delim, $current_heredoc_strip) = @{$pending_heredocs->pop_(0)};
                    $in_heredoc_body = 1;
                }
            } else {
                for my $ch (@{$line}) {
                    $content_chars->push($ch);
                    $text_chars->push($ch);
                }
                $self->{pos_} = $line_end;
                if ($self->{pos_} < $self->{length_} && $self->{source}->[$self->{pos_}] eq "\n") {
                    $content_chars->push("\n");
                    $text_chars->push("\n");
                    $self->advance();
                }
            }
            next;
        }
        $c = $self->peek();
        my $ch = "";
        if ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $next_c = $self->{source}->[$self->{pos_} + 1];
            if ($next_c eq "\n") {
                $self->advance();
                $self->advance();
            } elsif (is_escape_char_in_backtick($next_c)) {
                $self->advance();
                $escaped = $self->advance();
                $content_chars->push($escaped);
                $text_chars->push("\\");
                $text_chars->push($escaped);
            } else {
                $ch = $self->advance();
                $content_chars->push($ch);
                $text_chars->push($ch);
            }
            next;
        }
        if ($c eq "<" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "<") {
            my $quote = "";
            if ($self->{pos_} + 2 < $self->{length_} && $self->{source}->[$self->{pos_} + 2] eq "<") {
                $content_chars->push($self->advance());
                $text_chars->push("<");
                $content_chars->push($self->advance());
                $text_chars->push("<");
                $content_chars->push($self->advance());
                $text_chars->push("<");
                while (!$self->at_end() && is_whitespace_no_newline($self->peek())) {
                    $ch = $self->advance();
                    $content_chars->push($ch);
                    $text_chars->push($ch);
                }
                while (!$self->at_end() && !is_whitespace($self->peek()) && ((index("()", $self->peek()) == -1))) {
                    if ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        $ch = $self->advance();
                        $content_chars->push($ch);
                        $text_chars->push($ch);
                        $ch = $self->advance();
                        $content_chars->push($ch);
                        $text_chars->push($ch);
                    } elsif ((index("\"'", $self->peek()) >= 0)) {
                        $quote = $self->peek();
                        $ch = $self->advance();
                        $content_chars->push($ch);
                        $text_chars->push($ch);
                        while (!$self->at_end() && $self->peek() ne $quote) {
                            if ($quote eq "\"" && $self->peek() eq "\\") {
                                $ch = $self->advance();
                                $content_chars->push($ch);
                                $text_chars->push($ch);
                            }
                            $ch = $self->advance();
                            $content_chars->push($ch);
                            $text_chars->push($ch);
                        }
                        if (!$self->at_end()) {
                            $ch = $self->advance();
                            $content_chars->push($ch);
                            $text_chars->push($ch);
                        }
                    } else {
                        $ch = $self->advance();
                        $content_chars->push($ch);
                        $text_chars->push($ch);
                    }
                }
                next;
            }
            $content_chars->push($self->advance());
            $text_chars->push("<");
            $content_chars->push($self->advance());
            $text_chars->push("<");
            $strip_tabs = 0;
            if (!$self->at_end() && $self->peek() eq "-") {
                $strip_tabs = 1;
                $content_chars->push($self->advance());
                $text_chars->push("-");
            }
            while (!$self->at_end() && is_whitespace_no_newline($self->peek())) {
                $ch = $self->advance();
                $content_chars->push($ch);
                $text_chars->push($ch);
            }
            my $delimiter_chars = [];
            if (!$self->at_end()) {
                $ch = $self->peek();
                my $dch = "";
                my $closing = "";
                if (is_quote($ch)) {
                    $quote = $self->advance();
                    $content_chars->push($quote);
                    $text_chars->push($quote);
                    while (!$self->at_end() && $self->peek() ne $quote) {
                        $dch = $self->advance();
                        $content_chars->push($dch);
                        $text_chars->push($dch);
                        $delimiter_chars->push($dch);
                    }
                    if (!$self->at_end()) {
                        $closing = $self->advance();
                        $content_chars->push($closing);
                        $text_chars->push($closing);
                    }
                } elsif ($ch eq "\\") {
                    $esc = $self->advance();
                    $content_chars->push($esc);
                    $text_chars->push($esc);
                    if (!$self->at_end()) {
                        $dch = $self->advance();
                        $content_chars->push($dch);
                        $text_chars->push($dch);
                        $delimiter_chars->push($dch);
                    }
                    while (!$self->at_end() && !is_metachar($self->peek())) {
                        $dch = $self->advance();
                        $content_chars->push($dch);
                        $text_chars->push($dch);
                        $delimiter_chars->push($dch);
                    }
                } else {
                    while (!$self->at_end() && !is_metachar($self->peek()) && $self->peek() ne "`") {
                        $ch = $self->peek();
                        if (is_quote($ch)) {
                            $quote = $self->advance();
                            $content_chars->push($quote);
                            $text_chars->push($quote);
                            while (!$self->at_end() && $self->peek() ne $quote) {
                                $dch = $self->advance();
                                $content_chars->push($dch);
                                $text_chars->push($dch);
                                $delimiter_chars->push($dch);
                            }
                            if (!$self->at_end()) {
                                $closing = $self->advance();
                                $content_chars->push($closing);
                                $text_chars->push($closing);
                            }
                        } elsif ($ch eq "\\") {
                            $esc = $self->advance();
                            $content_chars->push($esc);
                            $text_chars->push($esc);
                            if (!$self->at_end()) {
                                $dch = $self->advance();
                                $content_chars->push($dch);
                                $text_chars->push($dch);
                                $delimiter_chars->push($dch);
                            }
                        } else {
                            $dch = $self->advance();
                            $content_chars->push($dch);
                            $text_chars->push($dch);
                            $delimiter_chars->push($dch);
                        }
                    }
                }
            }
            $delimiter = ""->join_($delimiter_chars);
            if ((length($delimiter) > 0)) {
                $pending_heredocs->push([$delimiter, $strip_tabs]);
            }
            next;
        }
        if ($c eq "\n") {
            $ch = $self->advance();
            $content_chars->push($ch);
            $text_chars->push($ch);
            if (scalar(@{$pending_heredocs}) > 0) {
                ($current_heredoc_delim, $current_heredoc_strip) = @{$pending_heredocs->pop_(0)};
                $in_heredoc_body = 1;
            }
            next;
        }
        $ch = $self->advance();
        $content_chars->push($ch);
        $text_chars->push($ch);
    }
    if ($self->at_end()) {
        die "Unterminated backtick";
    }
    $self->advance();
    $text_chars->push("`");
    my $text = ""->join_($text_chars);
    my $content = ""->join_($content_chars);
    if (scalar(@{$pending_heredocs}) > 0) {
        ($heredoc_start, $heredoc_end) = @{find_heredoc_content_end($self->{source}, $self->{pos_}, $pending_heredocs)};
        if ($heredoc_end > $heredoc_start) {
            $content = $content . substring($self->{source}, $heredoc_start, $heredoc_end);
            if ($self->{cmdsub_heredoc_end} == -1) {
                $self->{cmdsub_heredoc_end} = $heredoc_end;
            } else {
                $self->{cmdsub_heredoc_end} = ($self->{cmdsub_heredoc_end} > $heredoc_end ? $self->{cmdsub_heredoc_end} : $heredoc_end);
            }
        }
    }
    my $sub_parser = new_parser($content, 0, $self->{extglob});
    my $cmd = $sub_parser->parse_list(1);
    if (!defined($cmd)) {
        $cmd = Empty->new("empty");
    }
    return [CommandSubstitution->new($cmd, "cmdsub"), $text];
}

sub parse_process_substitution ($self) {
    my $cmd;
    my $content_start_char;
    my $text;
    my $text_end;
    if ($self->at_end() || !is_redirect_char($self->peek())) {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    my $direction = $self->advance();
    if ($self->at_end() || $self->peek() ne "(") {
        $self->{pos_} = $start;
        return [undef, ""];
    }
    $self->advance();
    my $saved = $self->save_parser_state();
    my $old_in_process_sub = $self->{in_process_sub};
    $self->{in_process_sub} = 1;
    $self->set_state(PARSERSTATEFLAGS_PST_EOFTOKEN());
    $self->{eof_token} = ")";
    eval {
        $cmd = $self->parse_list(1);
        if (!defined($cmd)) {
            $cmd = Empty->new("empty");
        }
        $self->skip_whitespace_and_newlines();
        if ($self->at_end() || $self->peek() ne ")") {
            die "Invalid process substitution";
        }
        $self->advance();
        $text_end = $self->{pos_};
        $text = substring($self->{source}, $start, $text_end);
        $text = strip_line_continuations_comment_aware($text);
        $self->restore_parser_state($saved);
        $self->{in_process_sub} = $old_in_process_sub;
        return [ProcessSubstitution->new($direction, $cmd, "procsub"), $text];
    };
    if (my $e = $@) {
        $self->restore_parser_state($saved);
        $self->{in_process_sub} = $old_in_process_sub;
        $content_start_char = ($start + 2 < $self->{length_} ? $self->{source}->[$start + 2] : "");
        if ((index(" \t\n", $content_start_char) >= 0)) {
            die $e;
        }
        $self->{pos_} = $start + 2;
        $self->{lexer}->{pos_} = $self->{pos_};
        $self->{lexer}->parse_matched_pair("(", ")", 0, 0);
        $self->{pos_} = $self->{lexer}->{pos_};
        $text = substring($self->{source}, $start, $self->{pos_});
        $text = strip_line_continuations_comment_aware($text);
        return [undef, $text];
    }
}

sub parse_array_literal ($self) {
    my $word;
    if ($self->at_end() || $self->peek() ne "(") {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    $self->advance();
    $self->set_state(PARSERSTATEFLAGS_PST_COMPASSIGN());
    my $elements = [];
    while (1) {
        $self->skip_whitespace_and_newlines();
        if ($self->at_end()) {
            $self->clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN());
            die "Unterminated array literal";
        }
        if ($self->peek() eq ")") {
            last;
        }
        $word = $self->parse_word(0, 1, 0);
        if (!defined($word)) {
            if ($self->peek() eq ")") {
                last;
            }
            $self->clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN());
            die "Expected word in array literal";
        }
        $elements->push($word);
    }
    if ($self->at_end() || $self->peek() ne ")") {
        $self->clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN());
        die "Expected ) to close array literal";
    }
    $self->advance();
    my $text = substring($self->{source}, $start, $self->{pos_});
    $self->clear_state(PARSERSTATEFLAGS_PST_COMPASSIGN());
    return [Array->new($elements, "array"), $text];
}

sub parse_arithmetic_expansion ($self) {
    my $c;
    my $content;
    my $expr;
    if ($self->at_end() || $self->peek() ne "\$") {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    if ($self->{pos_} + 2 >= $self->{length_} || $self->{source}->[$self->{pos_} + 1] ne "(" || $self->{source}->[$self->{pos_} + 2] ne "(") {
        return [undef, ""];
    }
    $self->advance();
    $self->advance();
    $self->advance();
    my $content_start = $self->{pos_};
    my $depth = 2;
    my $first_close_pos = -1;
    while (!$self->at_end() && $depth > 0) {
        $c = $self->peek();
        if ($c eq "'") {
            $self->advance();
            while (!$self->at_end() && $self->peek() ne "'") {
                $self->advance();
            }
            if (!$self->at_end()) {
                $self->advance();
            }
        } elsif ($c eq "\"") {
            $self->advance();
            while (!$self->at_end()) {
                if ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                    $self->advance();
                    $self->advance();
                } elsif ($self->peek() eq "\"") {
                    $self->advance();
                    last;
                } else {
                    $self->advance();
                }
            }
        } elsif ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $self->advance();
            $self->advance();
        } elsif ($c eq "(") {
            $depth += 1;
            $self->advance();
        } elsif ($c eq ")") {
            if ($depth == 2) {
                $first_close_pos = $self->{pos_};
            }
            $depth -= 1;
            if ($depth == 0) {
                last;
            }
            $self->advance();
        } else {
            if ($depth == 1) {
                $first_close_pos = -1;
            }
            $self->advance();
        }
    }
    if ($depth != 0) {
        if ($self->at_end()) {
            die "unexpected EOF looking for `))'";
        }
        $self->{pos_} = $start;
        return [undef, ""];
    }
    my $content = "";
    if ($first_close_pos != -1) {
        $content = substring($self->{source}, $content_start, $first_close_pos);
    } else {
        $content = substring($self->{source}, $content_start, $self->{pos_});
    }
    $self->advance();
    my $text = substring($self->{source}, $start, $self->{pos_});
    my $expr = undef;
    eval {
        $expr = $self->parse_arith_expr($content);
    };
    if (my $_e = $@) {
        $self->{pos_} = $start;
        return [undef, ""];
    }
    return [ArithmeticExpansion->new($expr, "arith"), $text];
}

sub parse_arith_expr ($self, $content) {
    my $result;
    my $saved_arith_src = $self->{arith_src};
    my $saved_arith_pos = $self->{arith_pos};
    my $saved_arith_len = $self->{arith_len};
    my $saved_parser_state = $self->{parser_state};
    $self->set_state(PARSERSTATEFLAGS_PST_ARITH());
    $self->{arith_src} = $content;
    $self->{arith_pos} = 0;
    $self->{arith_len} = length($content);
    $self->arith_skip_ws();
    my $result = undef;
    if ($self->arith_at_end()) {
        $result = undef;
    } else {
        $result = $self->arith_parse_comma();
    }
    $self->{parser_state} = $saved_parser_state;
    if ($saved_arith_src ne "") {
        $self->{arith_src} = $saved_arith_src;
        $self->{arith_pos} = $saved_arith_pos;
        $self->{arith_len} = $saved_arith_len;
    }
    return $result;
}

sub arith_at_end ($self) {
    return $self->{arith_pos} >= $self->{arith_len};
}

sub arith_peek ($self, $offset) {
    my $pos_ = $self->{arith_pos} + $offset;
    if ($pos_ >= $self->{arith_len}) {
        return "";
    }
    return $self->{arith_src}->[$pos_];
}

sub arith_advance ($self) {
    if ($self->arith_at_end()) {
        return "";
    }
    my $c = $self->{arith_src}->[$self->{arith_pos}];
    $self->{arith_pos} += 1;
    return $c;
}

sub arith_skip_ws ($self) {
    my $c;
    while (!$self->arith_at_end()) {
        $c = $self->{arith_src}->[$self->{arith_pos}];
        if (is_whitespace($c)) {
            $self->{arith_pos} += 1;
        } elsif ($c eq "\\" && $self->{arith_pos} + 1 < $self->{arith_len} && $self->{arith_src}->[$self->{arith_pos} + 1] eq "\n") {
            $self->{arith_pos} += 2;
        } else {
            last;
        }
    }
}

sub arith_match ($self, $s_) {
    return starts_with_at($self->{arith_src}, $self->{arith_pos}, $s_);
}

sub arith_consume ($self, $s_) {
    if ($self->arith_match($s_)) {
        $self->{arith_pos} += length($s_);
        return 1;
    }
    return 0;
}

sub arith_parse_comma ($self) {
    my $right;
    my $left = $self->arith_parse_assign();
    while (1) {
        $self->arith_skip_ws();
        if ($self->arith_consume(",")) {
            $self->arith_skip_ws();
            $right = $self->arith_parse_assign();
            $left = ArithComma->new($left, $right, "comma");
        } else {
            last;
        }
    }
    return $left;
}

sub arith_parse_assign ($self) {
    my $right;
    my $left = $self->arith_parse_ternary();
    $self->arith_skip_ws();
    my $assign_ops = ["<<=", ">>=", "+=", "-=", "*=", "/=", "%=", "&=", "^=", "|=", "="];
    for my $op (@{$assign_ops}) {
        if ($self->arith_match($op)) {
            if ($op == "=" && $self->arith_peek(1) eq "=") {
                last;
            }
            $self->arith_consume($op);
            $self->arith_skip_ws();
            $right = $self->arith_parse_assign();
            return ArithAssign->new($op, $left, $right, "assign");
        }
    }
    return $left;
}

sub arith_parse_ternary ($self) {
    my $if_false;
    my $if_true;
    my $cond = $self->arith_parse_logical_or();
    $self->arith_skip_ws();
    if ($self->arith_consume("?")) {
        $self->arith_skip_ws();
        my $if_true = undef;
        if ($self->arith_match(":")) {
            $if_true = undef;
        } else {
            $if_true = $self->arith_parse_assign();
        }
        $self->arith_skip_ws();
        my $if_false = undef;
        if ($self->arith_consume(":")) {
            $self->arith_skip_ws();
            if ($self->arith_at_end() || $self->arith_peek(0) eq ")") {
                $if_false = undef;
            } else {
                $if_false = $self->arith_parse_ternary();
            }
        } else {
            $if_false = undef;
        }
        return ArithTernary->new($cond, $if_true, $if_false, "ternary");
    }
    return $cond;
}

sub arith_parse_left_assoc ($self, $ops, $parsefn) {
    my $matched;
    my $left = parsefn();
    while (1) {
        $self->arith_skip_ws();
        $matched = 0;
        for my $op (@{$ops}) {
            if ($self->arith_match($op)) {
                $self->arith_consume($op);
                $self->arith_skip_ws();
                $left = ArithBinaryOp->new($op, $left, parsefn(), "binary-op");
                $matched = 1;
                last;
            }
        }
        if (!$matched) {
            last;
        }
    }
    return $left;
}

sub arith_parse_logical_or ($self) {
    return $self->arith_parse_left_assoc(["||"], sub { $self->arith_parse_logical_and(@_) });
}

sub arith_parse_logical_and ($self) {
    return $self->arith_parse_left_assoc(["&&"], sub { $self->arith_parse_bitwise_or(@_) });
}

sub arith_parse_bitwise_or ($self) {
    my $right;
    my $left = $self->arith_parse_bitwise_xor();
    while (1) {
        $self->arith_skip_ws();
        if ($self->arith_peek(0) eq "|" && $self->arith_peek(1) ne "|" && $self->arith_peek(1) ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_bitwise_xor();
            $left = ArithBinaryOp->new("|", $left, $right, "binary-op");
        } else {
            last;
        }
    }
    return $left;
}

sub arith_parse_bitwise_xor ($self) {
    my $right;
    my $left = $self->arith_parse_bitwise_and();
    while (1) {
        $self->arith_skip_ws();
        if ($self->arith_peek(0) eq "^" && $self->arith_peek(1) ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_bitwise_and();
            $left = ArithBinaryOp->new("^", $left, $right, "binary-op");
        } else {
            last;
        }
    }
    return $left;
}

sub arith_parse_bitwise_and ($self) {
    my $right;
    my $left = $self->arith_parse_equality();
    while (1) {
        $self->arith_skip_ws();
        if ($self->arith_peek(0) eq "&" && $self->arith_peek(1) ne "&" && $self->arith_peek(1) ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_equality();
            $left = ArithBinaryOp->new("&", $left, $right, "binary-op");
        } else {
            last;
        }
    }
    return $left;
}

sub arith_parse_equality ($self) {
    return $self->arith_parse_left_assoc(["==", "!="], sub { $self->arith_parse_comparison(@_) });
}

sub arith_parse_comparison ($self) {
    my $right;
    my $left = $self->arith_parse_shift();
    while (1) {
        $self->arith_skip_ws();
        my $right = undef;
        if ($self->arith_match("<=")) {
            $self->arith_consume("<=");
            $self->arith_skip_ws();
            $right = $self->arith_parse_shift();
            $left = ArithBinaryOp->new("<=", $left, $right, "binary-op");
        } elsif ($self->arith_match(">=")) {
            $self->arith_consume(">=");
            $self->arith_skip_ws();
            $right = $self->arith_parse_shift();
            $left = ArithBinaryOp->new(">=", $left, $right, "binary-op");
        } elsif ($self->arith_peek(0) eq "<" && $self->arith_peek(1) ne "<" && $self->arith_peek(1) ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_shift();
            $left = ArithBinaryOp->new("<", $left, $right, "binary-op");
        } elsif ($self->arith_peek(0) eq ">" && $self->arith_peek(1) ne ">" && $self->arith_peek(1) ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_shift();
            $left = ArithBinaryOp->new(">", $left, $right, "binary-op");
        } else {
            last;
        }
    }
    return $left;
}

sub arith_parse_shift ($self) {
    my $right;
    my $left = $self->arith_parse_additive();
    while (1) {
        $self->arith_skip_ws();
        if ($self->arith_match("<<=")) {
            last;
        }
        if ($self->arith_match(">>=")) {
            last;
        }
        my $right = undef;
        if ($self->arith_match("<<")) {
            $self->arith_consume("<<");
            $self->arith_skip_ws();
            $right = $self->arith_parse_additive();
            $left = ArithBinaryOp->new("<<", $left, $right, "binary-op");
        } elsif ($self->arith_match(">>")) {
            $self->arith_consume(">>");
            $self->arith_skip_ws();
            $right = $self->arith_parse_additive();
            $left = ArithBinaryOp->new(">>", $left, $right, "binary-op");
        } else {
            last;
        }
    }
    return $left;
}

sub arith_parse_additive ($self) {
    my $c;
    my $c2;
    my $right;
    my $left = $self->arith_parse_multiplicative();
    while (1) {
        $self->arith_skip_ws();
        $c = $self->arith_peek(0);
        $c2 = $self->arith_peek(1);
        my $right = undef;
        if ($c eq "+" && $c2 ne "+" && $c2 ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_multiplicative();
            $left = ArithBinaryOp->new("+", $left, $right, "binary-op");
        } elsif ($c eq "-" && $c2 ne "-" && $c2 ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_multiplicative();
            $left = ArithBinaryOp->new("-", $left, $right, "binary-op");
        } else {
            last;
        }
    }
    return $left;
}

sub arith_parse_multiplicative ($self) {
    my $c;
    my $c2;
    my $right;
    my $left = $self->arith_parse_exponentiation();
    while (1) {
        $self->arith_skip_ws();
        $c = $self->arith_peek(0);
        $c2 = $self->arith_peek(1);
        my $right = undef;
        if ($c eq "*" && $c2 ne "*" && $c2 ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_exponentiation();
            $left = ArithBinaryOp->new("*", $left, $right, "binary-op");
        } elsif ($c eq "/" && $c2 ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_exponentiation();
            $left = ArithBinaryOp->new("/", $left, $right, "binary-op");
        } elsif ($c eq "%" && $c2 ne "=") {
            $self->arith_advance();
            $self->arith_skip_ws();
            $right = $self->arith_parse_exponentiation();
            $left = ArithBinaryOp->new("%", $left, $right, "binary-op");
        } else {
            last;
        }
    }
    return $left;
}

sub arith_parse_exponentiation ($self) {
    my $right;
    my $left = $self->arith_parse_unary();
    $self->arith_skip_ws();
    if ($self->arith_match("**")) {
        $self->arith_consume("**");
        $self->arith_skip_ws();
        $right = $self->arith_parse_exponentiation();
        return ArithBinaryOp->new("**", $left, $right, "binary-op");
    }
    return $left;
}

sub arith_parse_unary ($self) {
    my $operand;
    $self->arith_skip_ws();
    my $operand = undef;
    if ($self->arith_match("++")) {
        $self->arith_consume("++");
        $self->arith_skip_ws();
        $operand = $self->arith_parse_unary();
        return ArithPreIncr->new($operand, "pre-incr");
    }
    if ($self->arith_match("--")) {
        $self->arith_consume("--");
        $self->arith_skip_ws();
        $operand = $self->arith_parse_unary();
        return ArithPreDecr->new($operand, "pre-decr");
    }
    my $c = $self->arith_peek(0);
    if ($c eq "!") {
        $self->arith_advance();
        $self->arith_skip_ws();
        $operand = $self->arith_parse_unary();
        return ArithUnaryOp->new("!", $operand, "unary-op");
    }
    if ($c eq "~") {
        $self->arith_advance();
        $self->arith_skip_ws();
        $operand = $self->arith_parse_unary();
        return ArithUnaryOp->new("~", $operand, "unary-op");
    }
    if ($c eq "+" && $self->arith_peek(1) ne "+") {
        $self->arith_advance();
        $self->arith_skip_ws();
        $operand = $self->arith_parse_unary();
        return ArithUnaryOp->new("+", $operand, "unary-op");
    }
    if ($c eq "-" && $self->arith_peek(1) ne "-") {
        $self->arith_advance();
        $self->arith_skip_ws();
        $operand = $self->arith_parse_unary();
        return ArithUnaryOp->new("-", $operand, "unary-op");
    }
    return $self->arith_parse_postfix();
}

sub arith_parse_postfix ($self) {
    my $index_;
    my $left = $self->arith_parse_primary();
    while (1) {
        $self->arith_skip_ws();
        if ($self->arith_match("++")) {
            $self->arith_consume("++");
            $left = ArithPostIncr->new($left, "post-incr");
        } elsif ($self->arith_match("--")) {
            $self->arith_consume("--");
            $left = ArithPostDecr->new($left, "post-decr");
        } elsif ($self->arith_peek(0) eq "[") {
            if (ref($left) eq 'ArithVar') {
                my $left = $left;
                $self->arith_advance();
                $self->arith_skip_ws();
                $index_ = $self->arith_parse_comma();
                $self->arith_skip_ws();
                if (!$self->arith_consume("]")) {
                    die "Expected ']' in array subscript";
                }
                $left = ArithSubscript->new($left->{name}, $index_, "subscript");
            } else {
                last;
            }
        } else {
            last;
        }
    }
    return $left;
}

sub arith_parse_primary ($self) {
    my $escaped_char;
    my $expr;
    $self->arith_skip_ws();
    my $c = $self->arith_peek(0);
    if ($c eq "(") {
        $self->arith_advance();
        $self->arith_skip_ws();
        $expr = $self->arith_parse_comma();
        $self->arith_skip_ws();
        if (!$self->arith_consume(")")) {
            die "Expected ')' in arithmetic expression";
        }
        return $expr;
    }
    if ($c eq "#" && $self->arith_peek(1) eq "\$") {
        $self->arith_advance();
        return $self->arith_parse_expansion();
    }
    if ($c eq "\$") {
        return $self->arith_parse_expansion();
    }
    if ($c eq "'") {
        return $self->arith_parse_single_quote();
    }
    if ($c eq "\"") {
        return $self->arith_parse_double_quote();
    }
    if ($c eq "`") {
        return $self->arith_parse_backtick();
    }
    if ($c eq "\\") {
        $self->arith_advance();
        if ($self->arith_at_end()) {
            die "Unexpected end after backslash in arithmetic";
        }
        $escaped_char = $self->arith_advance();
        return ArithEscape->new($escaped_char, "escape");
    }
    if ($self->arith_at_end() || ((index(")]:,;?|&<>=!+-*/%^~#{}", $c) >= 0))) {
        return ArithEmpty->new("empty");
    }
    return $self->arith_parse_number_or_var();
}

sub arith_parse_expansion ($self) {
    my $ch;
    if (!$self->arith_consume("\$")) {
        die "Expected '\$'";
    }
    my $c = $self->arith_peek(0);
    if ($c eq "(") {
        return $self->arith_parse_cmdsub();
    }
    if ($c eq "{") {
        return $self->arith_parse_braced_param();
    }
    my $name_chars = [];
    while (!$self->arith_at_end()) {
        $ch = $self->arith_peek(0);
        if (($ch =~ /^[a-zA-Z0-9]$/) || $ch eq "_") {
            $name_chars->push($self->arith_advance());
        } elsif ((is_special_param_or_digit($ch) || $ch eq "#") && !(scalar(@{$name_chars}) > 0)) {
            $name_chars->push($self->arith_advance());
            last;
        } else {
            last;
        }
    }
    if (!(scalar(@{$name_chars}) > 0)) {
        die "Expected variable name after \$";
    }
    return ParamExpansion->new(""->join_($name_chars), "param");
}

sub arith_parse_cmdsub ($self) {
    my $ch;
    my $content;
    my $content_start;
    my $depth;
    my $inner_expr;
    $self->arith_advance();
    my $depth = 0;
    my $content_start = 0;
    my $ch = "";
    my $content = "";
    if ($self->arith_peek(0) eq "(") {
        $self->arith_advance();
        $depth = 1;
        $content_start = $self->{arith_pos};
        while (!$self->arith_at_end() && $depth > 0) {
            $ch = $self->arith_peek(0);
            if ($ch eq "(") {
                $depth += 1;
                $self->arith_advance();
            } elsif ($ch eq ")") {
                if ($depth == 1 && $self->arith_peek(1) eq ")") {
                    last;
                }
                $depth -= 1;
                $self->arith_advance();
            } else {
                $self->arith_advance();
            }
        }
        $content = substring($self->{arith_src}, $content_start, $self->{arith_pos});
        $self->arith_advance();
        $self->arith_advance();
        $inner_expr = $self->parse_arith_expr($content);
        return ArithmeticExpansion->new($inner_expr, "arith");
    }
    $depth = 1;
    $content_start = $self->{arith_pos};
    while (!$self->arith_at_end() && $depth > 0) {
        $ch = $self->arith_peek(0);
        if ($ch eq "(") {
            $depth += 1;
            $self->arith_advance();
        } elsif ($ch eq ")") {
            $depth -= 1;
            if ($depth == 0) {
                last;
            }
            $self->arith_advance();
        } else {
            $self->arith_advance();
        }
    }
    $content = substring($self->{arith_src}, $content_start, $self->{arith_pos});
    $self->arith_advance();
    my $sub_parser = new_parser($content, 0, $self->{extglob});
    my $cmd = $sub_parser->parse_list(1);
    return CommandSubstitution->new($cmd, "cmdsub");
}

sub arith_parse_braced_param ($self) {
    my $ch;
    my $name_chars;
    $self->arith_advance();
    my $name_chars = undef;
    if ($self->arith_peek(0) eq "!") {
        $self->arith_advance();
        $name_chars = [];
        while (!$self->arith_at_end() && $self->arith_peek(0) ne "}") {
            $name_chars->push($self->arith_advance());
        }
        $self->arith_consume("}");
        return ParamIndirect->new(""->join_($name_chars), "param-indirect");
    }
    if ($self->arith_peek(0) eq "#") {
        $self->arith_advance();
        $name_chars = [];
        while (!$self->arith_at_end() && $self->arith_peek(0) ne "}") {
            $name_chars->push($self->arith_advance());
        }
        $self->arith_consume("}");
        return ParamLength->new(""->join_($name_chars), "param-len");
    }
    $name_chars = [];
    my $ch = "";
    while (!$self->arith_at_end()) {
        $ch = $self->arith_peek(0);
        if ($ch eq "}") {
            $self->arith_advance();
            return ParamExpansion->new(""->join_($name_chars), "param");
        }
        if (is_param_expansion_op($ch)) {
            last;
        }
        $name_chars->push($self->arith_advance());
    }
    my $name = ""->join_($name_chars);
    my $op_chars = [];
    my $depth = 1;
    while (!$self->arith_at_end() && $depth > 0) {
        $ch = $self->arith_peek(0);
        if ($ch eq "{") {
            $depth += 1;
            $op_chars->push($self->arith_advance());
        } elsif ($ch eq "}") {
            $depth -= 1;
            if ($depth == 0) {
                last;
            }
            $op_chars->push($self->arith_advance());
        } else {
            $op_chars->push($self->arith_advance());
        }
    }
    $self->arith_consume("}");
    my $op_str = ""->join_($op_chars);
    if ($op_str->startswith(":-")) {
        return ParamExpansion->new($name, ":-", substring($op_str, 2, length($op_str)), "param");
    }
    if ($op_str->startswith(":=")) {
        return ParamExpansion->new($name, ":=", substring($op_str, 2, length($op_str)), "param");
    }
    if ($op_str->startswith(":+")) {
        return ParamExpansion->new($name, ":+", substring($op_str, 2, length($op_str)), "param");
    }
    if ($op_str->startswith(":?")) {
        return ParamExpansion->new($name, ":?", substring($op_str, 2, length($op_str)), "param");
    }
    if ($op_str->startswith(":")) {
        return ParamExpansion->new($name, ":", substring($op_str, 1, length($op_str)), "param");
    }
    if ($op_str->startswith("##")) {
        return ParamExpansion->new($name, "##", substring($op_str, 2, length($op_str)), "param");
    }
    if ($op_str->startswith("#")) {
        return ParamExpansion->new($name, "#", substring($op_str, 1, length($op_str)), "param");
    }
    if ($op_str->startswith("%%")) {
        return ParamExpansion->new($name, "%%", substring($op_str, 2, length($op_str)), "param");
    }
    if ($op_str->startswith("%")) {
        return ParamExpansion->new($name, "%", substring($op_str, 1, length($op_str)), "param");
    }
    if ($op_str->startswith("//")) {
        return ParamExpansion->new($name, "//", substring($op_str, 2, length($op_str)), "param");
    }
    if ($op_str->startswith("/")) {
        return ParamExpansion->new($name, "/", substring($op_str, 1, length($op_str)), "param");
    }
    return ParamExpansion->new($name, "", $op_str, "param");
}

sub arith_parse_single_quote ($self) {
    $self->arith_advance();
    my $content_start = $self->{arith_pos};
    while (!$self->arith_at_end() && $self->arith_peek(0) ne "'") {
        $self->arith_advance();
    }
    my $content = substring($self->{arith_src}, $content_start, $self->{arith_pos});
    if (!$self->arith_consume("'")) {
        die "Unterminated single quote in arithmetic";
    }
    return ArithNumber->new($content, "number");
}

sub arith_parse_double_quote ($self) {
    my $c;
    $self->arith_advance();
    my $content_start = $self->{arith_pos};
    while (!$self->arith_at_end() && $self->arith_peek(0) ne "\"") {
        $c = $self->arith_peek(0);
        if ($c eq "\\" && !$self->arith_at_end()) {
            $self->arith_advance();
            $self->arith_advance();
        } else {
            $self->arith_advance();
        }
    }
    my $content = substring($self->{arith_src}, $content_start, $self->{arith_pos});
    if (!$self->arith_consume("\"")) {
        die "Unterminated double quote in arithmetic";
    }
    return ArithNumber->new($content, "number");
}

sub arith_parse_backtick ($self) {
    my $c;
    $self->arith_advance();
    my $content_start = $self->{arith_pos};
    while (!$self->arith_at_end() && $self->arith_peek(0) ne "`") {
        $c = $self->arith_peek(0);
        if ($c eq "\\" && !$self->arith_at_end()) {
            $self->arith_advance();
            $self->arith_advance();
        } else {
            $self->arith_advance();
        }
    }
    my $content = substring($self->{arith_src}, $content_start, $self->{arith_pos});
    if (!$self->arith_consume("`")) {
        die "Unterminated backtick in arithmetic";
    }
    my $sub_parser = new_parser($content, 0, $self->{extglob});
    my $cmd = $sub_parser->parse_list(1);
    return CommandSubstitution->new($cmd, "cmdsub");
}

sub arith_parse_number_or_var ($self) {
    my $ch;
    my $expansion;
    my $prefix;
    $self->arith_skip_ws();
    my $chars = [];
    my $c = $self->arith_peek(0);
    my $ch = "";
    if (($c =~ /^\d$/)) {
        while (!$self->arith_at_end()) {
            $ch = $self->arith_peek(0);
            if (($ch =~ /^[a-zA-Z0-9]$/) || $ch eq "#" || $ch eq "_") {
                $chars->push($self->arith_advance());
            } else {
                last;
            }
        }
        $prefix = ""->join_($chars);
        if (!$self->arith_at_end() && $self->arith_peek(0) eq "\$") {
            $expansion = $self->arith_parse_expansion();
            return ArithConcat->new([ArithNumber->new($prefix, "number"), $expansion], "arith-concat");
        }
        return ArithNumber->new($prefix, "number");
    }
    if (($c =~ /^[a-zA-Z]$/) || $c eq "_") {
        while (!$self->arith_at_end()) {
            $ch = $self->arith_peek(0);
            if (($ch =~ /^[a-zA-Z0-9]$/) || $ch eq "_") {
                $chars->push($self->arith_advance());
            } else {
                last;
            }
        }
        return ArithVar->new(""->join_($chars), "var");
    }
    die "Unexpected character '" . $c . "' in arithmetic expression";
}

sub parse_deprecated_arithmetic ($self) {
    if ($self->at_end() || $self->peek() ne "\$") {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    if ($self->{pos_} + 1 >= $self->{length_} || $self->{source}->[$self->{pos_} + 1] ne "[") {
        return [undef, ""];
    }
    $self->advance();
    $self->advance();
    $self->{lexer}->{pos_} = $self->{pos_};
    my $content = $self->{lexer}->parse_matched_pair("[", "]", MATCHEDPAIRFLAGS_ARITH(), 0);
    $self->{pos_} = $self->{lexer}->{pos_};
    my $text = substring($self->{source}, $start, $self->{pos_});
    return [ArithDeprecated->new($content, "arith-deprecated"), $text];
}

sub parse_param_expansion ($self, $in_dquote) {
    $self->sync_lexer();
    my ($result0, $result1) = @{$self->{lexer}->read_param_expansion($in_dquote)};
    $self->sync_parser();
    return [$result0, $result1];
}

sub parse_redirect ($self) {
    my $base;
    my $ch;
    my $fd_chars;
    my $fd_target;
    my $in_bracket;
    my $inner_word;
    my $is_valid_varfd;
    my $left;
    my $next_ch;
    my $op;
    my $right;
    my $saved;
    my $target;
    my $varname;
    my $varname_chars;
    my $word_start;
    $self->skip_whitespace();
    if ($self->at_end()) {
        return undef;
    }
    my $start = $self->{pos_};
    my $fd = -1;
    my $varfd = "";
    my $ch = "";
    if ($self->peek() eq "{") {
        $saved = $self->{pos_};
        $self->advance();
        $varname_chars = [];
        $in_bracket = 0;
        while (!$self->at_end() && !is_redirect_char($self->peek())) {
            $ch = $self->peek();
            if ($ch eq "}" && !$in_bracket) {
                last;
            } elsif ($ch eq "[") {
                $in_bracket = 1;
                $varname_chars->push($self->advance());
            } elsif ($ch eq "]") {
                $in_bracket = 0;
                $varname_chars->push($self->advance());
            } elsif (($ch =~ /^[a-zA-Z0-9]$/) || $ch eq "_") {
                $varname_chars->push($self->advance());
            } elsif ($in_bracket && !is_metachar($ch)) {
                $varname_chars->push($self->advance());
            } else {
                last;
            }
        }
        $varname = ""->join_($varname_chars);
        $is_valid_varfd = 0;
        if ((length($varname) > 0)) {
            if (($varname->[0] =~ /^[a-zA-Z]$/) || $varname->[0] eq "_") {
                if (((index($varname, "[") >= 0)) || ((index($varname, "]") >= 0))) {
                    $left = $varname->find("[");
                    $right = $varname->rfind("]");
                    if ($left != -1 && $right == length($varname) - 1 && $right > $left + 1) {
                        $base = substr($varname, 0, $left - 0);
                        if ((length($base) > 0) && (($base->[0] =~ /^[a-zA-Z]$/) || $base->[0] eq "_")) {
                            $is_valid_varfd = 1;
                            for my $c (@{substr($base, 1)}) {
                                if (!(($c =~ /^[a-zA-Z0-9]$/) || $c == "_")) {
                                    $is_valid_varfd = 0;
                                    last;
                                }
                            }
                        }
                    }
                } else {
                    $is_valid_varfd = 1;
                    for my $c (@{substr($varname, 1)}) {
                        if (!(($c =~ /^[a-zA-Z0-9]$/) || $c == "_")) {
                            $is_valid_varfd = 0;
                            last;
                        }
                    }
                }
            }
        }
        if (!$self->at_end() && $self->peek() eq "}" && $is_valid_varfd) {
            $self->advance();
            $varfd = $varname;
        } else {
            $self->{pos_} = $saved;
        }
    }
    my $fd_chars = undef;
    if ($varfd eq "" && (length($self->peek()) > 0) && ($self->peek() =~ /^\d$/)) {
        $fd_chars = [];
        while (!$self->at_end() && ($self->peek() =~ /^\d$/)) {
            $fd_chars->push($self->advance());
        }
        $fd = int(""->join_($fd_chars));
    }
    $ch = $self->peek();
    my $op = "";
    my $target = undef;
    if ($ch eq "&" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq ">") {
        if ($fd != -1 || $varfd ne "") {
            $self->{pos_} = $start;
            return undef;
        }
        $self->advance();
        $self->advance();
        if (!$self->at_end() && $self->peek() eq ">") {
            $self->advance();
            $op = "&>>";
        } else {
            $op = "&>";
        }
        $self->skip_whitespace();
        $target = $self->parse_word(0, 0, 0);
        if (!defined($target)) {
            die "Expected target for redirect " . $op;
        }
        return Redirect->new($op, $target, "redirect");
    }
    if ($ch eq "" || !is_redirect_char($ch)) {
        $self->{pos_} = $start;
        return undef;
    }
    if ($fd == -1 && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
        $self->{pos_} = $start;
        return undef;
    }
    $op = $self->advance();
    my $strip_tabs = 0;
    if (!$self->at_end()) {
        $next_ch = $self->peek();
        if ($op eq ">" && $next_ch eq ">") {
            $self->advance();
            $op = ">>";
        } elsif ($op eq "<" && $next_ch eq "<") {
            $self->advance();
            if (!$self->at_end() && $self->peek() eq "<") {
                $self->advance();
                $op = "<<<";
            } elsif (!$self->at_end() && $self->peek() eq "-") {
                $self->advance();
                $op = "<<";
                $strip_tabs = 1;
            } else {
                $op = "<<";
            }
        } elsif ($op eq "<" && $next_ch eq ">") {
            $self->advance();
            $op = "<>";
        } elsif ($op eq ">" && $next_ch eq "|") {
            $self->advance();
            $op = ">|";
        } elsif ($fd == -1 && $varfd eq "" && $op eq ">" && $next_ch eq "&") {
            if ($self->{pos_} + 1 >= $self->{length_} || !is_digit_or_dash($self->{source}->[$self->{pos_} + 1])) {
                $self->advance();
                $op = ">&";
            }
        } elsif ($fd == -1 && $varfd eq "" && $op eq "<" && $next_ch eq "&") {
            if ($self->{pos_} + 1 >= $self->{length_} || !is_digit_or_dash($self->{source}->[$self->{pos_} + 1])) {
                $self->advance();
                $op = "<&";
            }
        }
    }
    if ($op eq "<<") {
        return $self->parse_heredoc(int_ptr($fd), $strip_tabs);
    }
    if ($varfd ne "") {
        $op = "{" . $varfd . "}" . $op;
    } elsif ($fd != -1) {
        $op = "$fd" . $op;
    }
    if (!$self->at_end() && $self->peek() eq "&") {
        $self->advance();
        $self->skip_whitespace();
        if (!$self->at_end() && $self->peek() eq "-") {
            if ($self->{pos_} + 1 < $self->{length_} && !is_metachar($self->{source}->[$self->{pos_} + 1])) {
                $self->advance();
                $target = Word->new("&-", "word");
            } else {
                $target = undef;
            }
        } else {
            $target = undef;
        }
        if (!defined($target)) {
            my $inner_word = undef;
            if (!$self->at_end() && (($self->peek() =~ /^\d$/) || $self->peek() eq "-")) {
                $word_start = $self->{pos_};
                $fd_chars = [];
                while (!$self->at_end() && ($self->peek() =~ /^\d$/)) {
                    $fd_chars->push($self->advance());
                }
                my $fd_target = "";
                if ((scalar(@{$fd_chars}) > 0)) {
                    $fd_target = ""->join_($fd_chars);
                } else {
                    $fd_target = "";
                }
                if (!$self->at_end() && $self->peek() eq "-") {
                    $fd_target .= $self->advance();
                }
                if ($fd_target ne "-" && !$self->at_end() && !is_metachar($self->peek())) {
                    $self->{pos_} = $word_start;
                    $inner_word = $self->parse_word(0, 0, 0);
                    if (defined($inner_word)) {
                        $target = Word->new("&" . $inner_word->{value}, "word");
                        $target->{parts} = $inner_word->{parts};
                    } else {
                        die "Expected target for redirect " . $op;
                    }
                } else {
                    $target = Word->new("&" . $fd_target, "word");
                }
            } else {
                $inner_word = $self->parse_word(0, 0, 0);
                if (defined($inner_word)) {
                    $target = Word->new("&" . $inner_word->{value}, "word");
                    $target->{parts} = $inner_word->{parts};
                } else {
                    die "Expected target for redirect " . $op;
                }
            }
        }
    } else {
        $self->skip_whitespace();
        if (($op eq ">&" || $op eq "<&") && !$self->at_end() && $self->peek() eq "-") {
            if ($self->{pos_} + 1 < $self->{length_} && !is_metachar($self->{source}->[$self->{pos_} + 1])) {
                $self->advance();
                $target = Word->new("&-", "word");
            } else {
                $target = $self->parse_word(0, 0, 0);
            }
        } else {
            $target = $self->parse_word(0, 0, 0);
        }
    }
    if (!defined($target)) {
        die "Expected target for redirect " . $op;
    }
    return Redirect->new($op, $target, "redirect");
}

sub parse_heredoc_delimiter ($self) {
    my $c;
    my $ch;
    my $depth;
    my $dollar_count;
    my $esc;
    my $esc_val;
    my $j;
    my $next_ch;
    $self->skip_whitespace();
    my $quoted = 0;
    my $delimiter_chars = [];
    while (1) {
        my $c = "";
        my $depth = 0;
        while (!$self->at_end() && !is_metachar($self->peek())) {
            $ch = $self->peek();
            if ($ch eq "\"") {
                $quoted = 1;
                $self->advance();
                while (!$self->at_end() && $self->peek() ne "\"") {
                    $delimiter_chars->push($self->advance());
                }
                if (!$self->at_end()) {
                    $self->advance();
                }
            } elsif ($ch eq "'") {
                $quoted = 1;
                $self->advance();
                while (!$self->at_end() && $self->peek() ne "'") {
                    $c = $self->advance();
                    if ($c eq "\n") {
                        $self->{saw_newline_in_single_quote} = 1;
                    }
                    $delimiter_chars->push($c);
                }
                if (!$self->at_end()) {
                    $self->advance();
                }
            } elsif ($ch eq "\\") {
                $self->advance();
                if (!$self->at_end()) {
                    $next_ch = $self->peek();
                    if ($next_ch eq "\n") {
                        $self->advance();
                    } else {
                        $quoted = 1;
                        $delimiter_chars->push($self->advance());
                    }
                }
            } elsif ($ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "'") {
                $quoted = 1;
                $self->advance();
                $self->advance();
                while (!$self->at_end() && $self->peek() ne "'") {
                    $c = $self->peek();
                    if ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        $self->advance();
                        $esc = $self->peek();
                        $esc_val = get_ansi_escape($esc);
                        if ($esc_val >= 0) {
                            $delimiter_chars->push(chr($esc_val));
                            $self->advance();
                        } elsif ($esc eq "'") {
                            $delimiter_chars->push($self->advance());
                        } else {
                            $delimiter_chars->push($self->advance());
                        }
                    } else {
                        $delimiter_chars->push($self->advance());
                    }
                }
                if (!$self->at_end()) {
                    $self->advance();
                }
            } elsif (is_expansion_start($self->{source}, $self->{pos_}, "\$(")) {
                $delimiter_chars->push($self->advance());
                $delimiter_chars->push($self->advance());
                $depth = 1;
                while (!$self->at_end() && $depth > 0) {
                    $c = $self->peek();
                    if ($c eq "(") {
                        $depth += 1;
                    } elsif ($c eq ")") {
                        $depth -= 1;
                    }
                    $delimiter_chars->push($self->advance());
                }
            } elsif ($ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "{") {
                $dollar_count = 0;
                $j = $self->{pos_} - 1;
                while ($j >= 0 && $self->{source}->[$j] eq "\$") {
                    $dollar_count += 1;
                    $j -= 1;
                }
                if ($j >= 0 && $self->{source}->[$j] eq "\\") {
                    $dollar_count -= 1;
                }
                if ($dollar_count % 2 == 1) {
                    $delimiter_chars->push($self->advance());
                } else {
                    $delimiter_chars->push($self->advance());
                    $delimiter_chars->push($self->advance());
                    $depth = 0;
                    while (!$self->at_end()) {
                        $c = $self->peek();
                        if ($c eq "{") {
                            $depth += 1;
                        } elsif ($c eq "}") {
                            $delimiter_chars->push($self->advance());
                            if ($depth == 0) {
                                last;
                            }
                            $depth -= 1;
                            if ($depth == 0 && !$self->at_end() && is_metachar($self->peek())) {
                                last;
                            }
                            next;
                        }
                        $delimiter_chars->push($self->advance());
                    }
                }
            } elsif ($ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "[") {
                $dollar_count = 0;
                $j = $self->{pos_} - 1;
                while ($j >= 0 && $self->{source}->[$j] eq "\$") {
                    $dollar_count += 1;
                    $j -= 1;
                }
                if ($j >= 0 && $self->{source}->[$j] eq "\\") {
                    $dollar_count -= 1;
                }
                if ($dollar_count % 2 == 1) {
                    $delimiter_chars->push($self->advance());
                } else {
                    $delimiter_chars->push($self->advance());
                    $delimiter_chars->push($self->advance());
                    $depth = 1;
                    while (!$self->at_end() && $depth > 0) {
                        $c = $self->peek();
                        if ($c eq "[") {
                            $depth += 1;
                        } elsif ($c eq "]") {
                            $depth -= 1;
                        }
                        $delimiter_chars->push($self->advance());
                    }
                }
            } elsif ($ch eq "`") {
                $delimiter_chars->push($self->advance());
                while (!$self->at_end() && $self->peek() ne "`") {
                    $c = $self->peek();
                    if ($c eq "'") {
                        $delimiter_chars->push($self->advance());
                        while (!$self->at_end() && $self->peek() ne "'" && $self->peek() ne "`") {
                            $delimiter_chars->push($self->advance());
                        }
                        if (!$self->at_end() && $self->peek() eq "'") {
                            $delimiter_chars->push($self->advance());
                        }
                    } elsif ($c eq "\"") {
                        $delimiter_chars->push($self->advance());
                        while (!$self->at_end() && $self->peek() ne "\"" && $self->peek() ne "`") {
                            if ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                                $delimiter_chars->push($self->advance());
                            }
                            $delimiter_chars->push($self->advance());
                        }
                        if (!$self->at_end() && $self->peek() eq "\"") {
                            $delimiter_chars->push($self->advance());
                        }
                    } elsif ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        $delimiter_chars->push($self->advance());
                        $delimiter_chars->push($self->advance());
                    } else {
                        $delimiter_chars->push($self->advance());
                    }
                }
                if (!$self->at_end()) {
                    $delimiter_chars->push($self->advance());
                }
            } else {
                $delimiter_chars->push($self->advance());
            }
        }
        if (!$self->at_end() && ((index("<>", $self->peek()) >= 0)) && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
            $delimiter_chars->push($self->advance());
            $delimiter_chars->push($self->advance());
            $depth = 1;
            while (!$self->at_end() && $depth > 0) {
                $c = $self->peek();
                if ($c eq "(") {
                    $depth += 1;
                } elsif ($c eq ")") {
                    $depth -= 1;
                }
                $delimiter_chars->push($self->advance());
            }
            next;
        }
        last;
    }
    return [""->join_($delimiter_chars), $quoted];
}

sub read_heredoc_line ($self, $quoted) {
    my $next_line_start;
    my $trailing_bs;
    my $line_start = $self->{pos_};
    my $line_end = $self->{pos_};
    while ($line_end < $self->{length_} && $self->{source}->[$line_end] ne "\n") {
        $line_end += 1;
    }
    my $line = substring($self->{source}, $line_start, $line_end);
    if (!$quoted) {
        while ($line_end < $self->{length_}) {
            $trailing_bs = count_trailing_backslashes($line);
            if ($trailing_bs % 2 == 0) {
                last;
            }
            $line = substring($line, 0, length($line) - 1);
            $line_end += 1;
            $next_line_start = $line_end;
            while ($line_end < $self->{length_} && $self->{source}->[$line_end] ne "\n") {
                $line_end += 1;
            }
            $line = $line . substring($self->{source}, $next_line_start, $line_end);
        }
    }
    return [$line, $line_end];
}

sub line_matches_delimiter ($self, $line, $delimiter, $strip_tabs) {
    my $check_line = ($strip_tabs ? ($line =~ s/^["\t"]+//r) : $line);
    my $normalized_check = normalize_heredoc_delimiter($check_line);
    my $normalized_delim = normalize_heredoc_delimiter($delimiter);
    return [$normalized_check eq $normalized_delim, $check_line];
}

sub gather_heredoc_bodies ($self) {
    my $add_newline;
    my $check_line;
    my $line;
    my $line_end;
    my $line_start;
    my $matches;
    my $normalized_check;
    my $normalized_delim;
    my $tabs_stripped;
    for my $heredoc (@{($self->{pending_heredocs} // [])}) {
        my $content_lines = [];
        $line_start = $self->{pos_};
        while ($self->{pos_} < $self->{length_}) {
            $line_start = $self->{pos_};
            ($line, $line_end) = @{$self->read_heredoc_line($heredoc->{quoted})};
            ($matches, $check_line) = @{$self->line_matches_delimiter($line, $heredoc->{delimiter}, $heredoc->{strip_tabs})};
            if ($matches) {
                $self->{pos_} = ($line_end < $self->{length_} ? $line_end + 1 : $line_end);
                last;
            }
            $normalized_check = normalize_heredoc_delimiter($check_line);
            $normalized_delim = normalize_heredoc_delimiter($heredoc->{delimiter});
            my $tabs_stripped = 0;
            if ($self->{eof_token} eq ")" && $normalized_check->startswith($normalized_delim)) {
                $tabs_stripped = length($line) - length($check_line);
                $self->{pos_} = $line_start + $tabs_stripped + length($heredoc->{delimiter});
                last;
            }
            if ($line_end >= $self->{length_} && $normalized_check->startswith($normalized_delim) && $self->{in_process_sub}) {
                $tabs_stripped = length($line) - length($check_line);
                $self->{pos_} = $line_start + $tabs_stripped + length($heredoc->{delimiter});
                last;
            }
            if ($heredoc->{strip_tabs}) {
                $line = ($line =~ s/^["\t"]+//r);
            }
            if ($line_end < $self->{length_}) {
                $content_lines->push($line . "\n");
                $self->{pos_} = $line_end + 1;
            } else {
                $add_newline = 1;
                if (!$heredoc->{quoted} && count_trailing_backslashes($line) % 2 == 1) {
                    $add_newline = 0;
                }
                $content_lines->push($line . (($add_newline ? "\n" : "")));
                $self->{pos_} = $self->{length_};
            }
        }
        $heredoc->{content} = ""->join_($content_lines);
    }
    $self->{pending_heredocs} = [];
}

sub parse_heredoc ($self, $fd, $strip_tabs) {
    my $start_pos = $self->{pos_};
    $self->set_state(PARSERSTATEFLAGS_PST_HEREDOC());
    my ($delimiter, $quoted) = @{$self->parse_heredoc_delimiter()};
    for my $existing (@{($self->{pending_heredocs} // [])}) {
        if ($existing->{start_pos} == $start_pos && $existing->{delimiter} eq $delimiter) {
            $self->clear_state(PARSERSTATEFLAGS_PST_HEREDOC());
            return $existing;
        }
    }
    my $heredoc = HereDoc->new($delimiter, "", $strip_tabs, $quoted, $fd, 0, "heredoc");
    $heredoc->{start_pos} = $start_pos;
    $self->{pending_heredocs}->push($heredoc);
    $self->clear_state(PARSERSTATEFLAGS_PST_HEREDOC());
    return $heredoc;
}

sub parse_command ($self) {
    my $all_assignments;
    my $in_assign_builtin;
    my $redirect;
    my $reserved;
    my $word;
    my $words = [];
    my $redirects = [];
    while (1) {
        $self->skip_whitespace();
        if ($self->lex_is_command_terminator()) {
            last;
        }
        if (scalar(@{$words}) == 0) {
            $reserved = $self->lex_peek_reserved_word();
            if ($reserved eq "}" || $reserved eq "]]") {
                last;
            }
        }
        $redirect = $self->parse_redirect();
        if (defined($redirect)) {
            $redirects->push($redirect);
            next;
        }
        $all_assignments = 1;
        for my $w (@{$words}) {
            if (!$self->is_assignment_word($w)) {
                $all_assignments = 0;
                last;
            }
        }
        $in_assign_builtin = scalar(@{$words}) > 0 && (exists(ASSIGNMENT_BUILTINS()->{$words->[0]->{value}}));
        $word = $self->parse_word(!(scalar(@{$words}) > 0) || $all_assignments && scalar(@{$redirects}) == 0, 0, $in_assign_builtin);
        if (!defined($word)) {
            last;
        }
        $words->push($word);
    }
    if (!(scalar(@{$words}) > 0) && !(scalar(@{$redirects}) > 0)) {
        return undef;
    }
    return Command->new($words, $redirects, "command");
}

sub parse_subshell ($self) {
    $self->skip_whitespace();
    if ($self->at_end() || $self->peek() ne "(") {
        return undef;
    }
    $self->advance();
    $self->set_state(PARSERSTATEFLAGS_PST_SUBSHELL());
    my $body = $self->parse_list(1);
    if (!defined($body)) {
        $self->clear_state(PARSERSTATEFLAGS_PST_SUBSHELL());
        die "Expected command in subshell";
    }
    $self->skip_whitespace();
    if ($self->at_end() || $self->peek() ne ")") {
        $self->clear_state(PARSERSTATEFLAGS_PST_SUBSHELL());
        die "Expected ) to close subshell";
    }
    $self->advance();
    $self->clear_state(PARSERSTATEFLAGS_PST_SUBSHELL());
    return Subshell->new($body, $self->collect_redirects(), "subshell");
}

sub parse_arithmetic_command ($self) {
    my $c;
    $self->skip_whitespace();
    if ($self->at_end() || $self->peek() ne "(" || $self->{pos_} + 1 >= $self->{length_} || $self->{source}->[$self->{pos_} + 1] ne "(") {
        return undef;
    }
    my $saved_pos = $self->{pos_};
    $self->advance();
    $self->advance();
    my $content_start = $self->{pos_};
    my $depth = 1;
    while (!$self->at_end() && $depth > 0) {
        $c = $self->peek();
        if ($c eq "'") {
            $self->advance();
            while (!$self->at_end() && $self->peek() ne "'") {
                $self->advance();
            }
            if (!$self->at_end()) {
                $self->advance();
            }
        } elsif ($c eq "\"") {
            $self->advance();
            while (!$self->at_end()) {
                if ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                    $self->advance();
                    $self->advance();
                } elsif ($self->peek() eq "\"") {
                    $self->advance();
                    last;
                } else {
                    $self->advance();
                }
            }
        } elsif ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $self->advance();
            $self->advance();
        } elsif ($c eq "(") {
            $depth += 1;
            $self->advance();
        } elsif ($c eq ")") {
            if ($depth == 1 && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq ")") {
                last;
            }
            $depth -= 1;
            if ($depth == 0) {
                $self->{pos_} = $saved_pos;
                return undef;
            }
            $self->advance();
        } else {
            $self->advance();
        }
    }
    if ($self->at_end()) {
        die "unexpected EOF looking for `))'";
    }
    if ($depth != 1) {
        $self->{pos_} = $saved_pos;
        return undef;
    }
    my $content = substring($self->{source}, $content_start, $self->{pos_});
    $content = $content->replace("\\\n", "");
    $self->advance();
    $self->advance();
    my $expr = $self->parse_arith_expr($content);
    return ArithmeticCommand->new($expr, $self->collect_redirects(), $content, "arith-cmd");
}

sub parse_conditional_expr ($self) {
    $self->skip_whitespace();
    if ($self->at_end() || $self->peek() ne "[" || $self->{pos_} + 1 >= $self->{length_} || $self->{source}->[$self->{pos_} + 1] ne "[") {
        return undef;
    }
    my $next_pos = $self->{pos_} + 2;
    if ($next_pos < $self->{length_} && !(is_whitespace($self->{source}->[$next_pos]) || $self->{source}->[$next_pos] eq "\\" && $next_pos + 1 < $self->{length_} && $self->{source}->[$next_pos + 1] eq "\n")) {
        return undef;
    }
    $self->advance();
    $self->advance();
    $self->set_state(PARSERSTATEFLAGS_PST_CONDEXPR());
    $self->{word_context} = WORD_CTX_COND();
    my $body = $self->parse_cond_or();
    while (!$self->at_end() && is_whitespace_no_newline($self->peek())) {
        $self->advance();
    }
    if ($self->at_end() || $self->peek() ne "]" || $self->{pos_} + 1 >= $self->{length_} || $self->{source}->[$self->{pos_} + 1] ne "]") {
        $self->clear_state(PARSERSTATEFLAGS_PST_CONDEXPR());
        $self->{word_context} = WORD_CTX_NORMAL();
        die "Expected ]] to close conditional expression";
    }
    $self->advance();
    $self->advance();
    $self->clear_state(PARSERSTATEFLAGS_PST_CONDEXPR());
    $self->{word_context} = WORD_CTX_NORMAL();
    return ConditionalExpr->new($body, $self->collect_redirects(), "cond-expr");
}

sub cond_skip_whitespace ($self) {
    while (!$self->at_end()) {
        if (is_whitespace_no_newline($self->peek())) {
            $self->advance();
        } elsif ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "\n") {
            $self->advance();
            $self->advance();
        } elsif ($self->peek() eq "\n") {
            $self->advance();
        } else {
            last;
        }
    }
}

sub cond_at_end ($self) {
    return $self->at_end() || $self->peek() eq "]" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "]";
}

sub parse_cond_or ($self) {
    my $right;
    $self->cond_skip_whitespace();
    my $left = $self->parse_cond_and();
    $self->cond_skip_whitespace();
    if (!$self->cond_at_end() && $self->peek() eq "|" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "|") {
        $self->advance();
        $self->advance();
        $right = $self->parse_cond_or();
        return CondOr->new($left, $right, "cond-or");
    }
    return $left;
}

sub parse_cond_and ($self) {
    my $right;
    $self->cond_skip_whitespace();
    my $left = $self->parse_cond_term();
    $self->cond_skip_whitespace();
    if (!$self->cond_at_end() && $self->peek() eq "&" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "&") {
        $self->advance();
        $self->advance();
        $right = $self->parse_cond_and();
        return CondAnd->new($left, $right, "cond-and");
    }
    return $left;
}

sub parse_cond_term ($self) {
    my $inner;
    my $op;
    my $op_word;
    my $operand;
    my $saved_pos;
    my $word2;
    $self->cond_skip_whitespace();
    if ($self->cond_at_end()) {
        die "Unexpected end of conditional expression";
    }
    my $operand = undef;
    if ($self->peek() eq "!") {
        if ($self->{pos_} + 1 < $self->{length_} && !is_whitespace_no_newline($self->{source}->[$self->{pos_} + 1])) {
        } else {
            $self->advance();
            $operand = $self->parse_cond_term();
            return CondNot->new($operand, "cond-not");
        }
    }
    if ($self->peek() eq "(") {
        $self->advance();
        $inner = $self->parse_cond_or();
        $self->cond_skip_whitespace();
        if ($self->at_end() || $self->peek() ne ")") {
            die "Expected ) in conditional expression";
        }
        $self->advance();
        return CondParen->new($inner, "cond-paren");
    }
    my $word1 = $self->parse_cond_word();
    if (!defined($word1)) {
        die "Expected word in conditional expression";
    }
    $self->cond_skip_whitespace();
    if (exists(COND_UNARY_OPS()->{$word1->{value}})) {
        $operand = $self->parse_cond_word();
        if (!defined($operand)) {
            die "Expected operand after " . $word1->{value};
        }
        return UnaryTest->new($word1->{value}, $operand, "unary-test");
    }
    if (!$self->cond_at_end() && $self->peek() ne "&" && $self->peek() ne "|" && $self->peek() ne ")") {
        my $word2 = undef;
        if (is_redirect_char($self->peek()) && !($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(")) {
            $op = $self->advance();
            $self->cond_skip_whitespace();
            $word2 = $self->parse_cond_word();
            if (!defined($word2)) {
                die "Expected operand after " . $op;
            }
            return BinaryTest->new($op, $word1, $word2, "binary-test");
        }
        $saved_pos = $self->{pos_};
        $op_word = $self->parse_cond_word();
        if (defined($op_word) && (exists(COND_BINARY_OPS()->{$op_word->{value}}))) {
            $self->cond_skip_whitespace();
            if ($op_word->{value} eq "=~") {
                $word2 = $self->parse_cond_regex_word();
            } else {
                $word2 = $self->parse_cond_word();
            }
            if (!defined($word2)) {
                die "Expected operand after " . $op_word->{value};
            }
            return BinaryTest->new($op_word->{value}, $word1, $word2, "binary-test");
        } else {
            $self->{pos_} = $saved_pos;
        }
    }
    return UnaryTest->new("-n", $word1, "unary-test");
}

sub parse_cond_word ($self) {
    $self->cond_skip_whitespace();
    if ($self->cond_at_end()) {
        return undef;
    }
    my $c = $self->peek();
    if (is_paren($c)) {
        return undef;
    }
    if ($c eq "&" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "&") {
        return undef;
    }
    if ($c eq "|" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "|") {
        return undef;
    }
    return $self->parse_word_internal(WORD_CTX_COND(), 0, 0);
}

sub parse_cond_regex_word ($self) {
    $self->cond_skip_whitespace();
    if ($self->cond_at_end()) {
        return undef;
    }
    $self->set_state(PARSERSTATEFLAGS_PST_REGEXP());
    my $result = $self->parse_word_internal(WORD_CTX_REGEX(), 0, 0);
    $self->clear_state(PARSERSTATEFLAGS_PST_REGEXP());
    $self->{word_context} = WORD_CTX_COND();
    return $result;
}

sub parse_brace_group ($self) {
    $self->skip_whitespace();
    if (!$self->lex_consume_word("{")) {
        return undef;
    }
    $self->skip_whitespace_and_newlines();
    my $body = $self->parse_list(1);
    if (!defined($body)) {
        die "Expected command in brace group";
    }
    $self->skip_whitespace();
    if (!$self->lex_consume_word("}")) {
        die "Expected } to close brace group";
    }
    return BraceGroup->new($body, $self->collect_redirects(), "brace-group");
}

sub parse_if ($self) {
    my $elif_condition;
    my $elif_then_body;
    my $inner_else;
    $self->skip_whitespace();
    if (!$self->lex_consume_word("if")) {
        return undef;
    }
    my $condition = $self->parse_list_until({"then" => 1});
    if (!defined($condition)) {
        die "Expected condition after 'if'";
    }
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("then")) {
        die "Expected 'then' after if condition";
    }
    my $then_body = $self->parse_list_until({"elif" => 1, "else" => 1, "fi" => 1});
    if (!defined($then_body)) {
        die "Expected commands after 'then'";
    }
    $self->skip_whitespace_and_newlines();
    my $else_body = undef;
    if ($self->lex_is_at_reserved_word("elif")) {
        $self->lex_consume_word("elif");
        $elif_condition = $self->parse_list_until({"then" => 1});
        if (!defined($elif_condition)) {
            die "Expected condition after 'elif'";
        }
        $self->skip_whitespace_and_newlines();
        if (!$self->lex_consume_word("then")) {
            die "Expected 'then' after elif condition";
        }
        $elif_then_body = $self->parse_list_until({"elif" => 1, "else" => 1, "fi" => 1});
        if (!defined($elif_then_body)) {
            die "Expected commands after 'then'";
        }
        $self->skip_whitespace_and_newlines();
        $inner_else = undef;
        if ($self->lex_is_at_reserved_word("elif")) {
            $inner_else = $self->parse_elif_chain();
        } elsif ($self->lex_is_at_reserved_word("else")) {
            $self->lex_consume_word("else");
            $inner_else = $self->parse_list_until({"fi" => 1});
            if (!defined($inner_else)) {
                die "Expected commands after 'else'";
            }
        }
        $else_body = If->new($elif_condition, $elif_then_body, $inner_else, "if");
    } elsif ($self->lex_is_at_reserved_word("else")) {
        $self->lex_consume_word("else");
        $else_body = $self->parse_list_until({"fi" => 1});
        if (!defined($else_body)) {
            die "Expected commands after 'else'";
        }
    }
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("fi")) {
        die "Expected 'fi' to close if statement";
    }
    return If->new($condition, $then_body, $else_body, $self->collect_redirects(), "if");
}

sub parse_elif_chain ($self) {
    $self->lex_consume_word("elif");
    my $condition = $self->parse_list_until({"then" => 1});
    if (!defined($condition)) {
        die "Expected condition after 'elif'";
    }
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("then")) {
        die "Expected 'then' after elif condition";
    }
    my $then_body = $self->parse_list_until({"elif" => 1, "else" => 1, "fi" => 1});
    if (!defined($then_body)) {
        die "Expected commands after 'then'";
    }
    $self->skip_whitespace_and_newlines();
    my $else_body = undef;
    if ($self->lex_is_at_reserved_word("elif")) {
        $else_body = $self->parse_elif_chain();
    } elsif ($self->lex_is_at_reserved_word("else")) {
        $self->lex_consume_word("else");
        $else_body = $self->parse_list_until({"fi" => 1});
        if (!defined($else_body)) {
            die "Expected commands after 'else'";
        }
    }
    return If->new($condition, $then_body, $else_body, "if");
}

sub parse_while ($self) {
    $self->skip_whitespace();
    if (!$self->lex_consume_word("while")) {
        return undef;
    }
    my $condition = $self->parse_list_until({"do" => 1});
    if (!defined($condition)) {
        die "Expected condition after 'while'";
    }
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("do")) {
        die "Expected 'do' after while condition";
    }
    my $body = $self->parse_list_until({"done" => 1});
    if (!defined($body)) {
        die "Expected commands after 'do'";
    }
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("done")) {
        die "Expected 'done' to close while loop";
    }
    return While->new($condition, $body, $self->collect_redirects(), "while");
}

sub parse_until ($self) {
    $self->skip_whitespace();
    if (!$self->lex_consume_word("until")) {
        return undef;
    }
    my $condition = $self->parse_list_until({"do" => 1});
    if (!defined($condition)) {
        die "Expected condition after 'until'";
    }
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("do")) {
        die "Expected 'do' after until condition";
    }
    my $body = $self->parse_list_until({"done" => 1});
    if (!defined($body)) {
        die "Expected commands after 'do'";
    }
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("done")) {
        die "Expected 'done' to close until loop";
    }
    return Until->new($condition, $body, $self->collect_redirects(), "until");
}

sub parse_for ($self) {
    my $brace_group;
    my $saw_delimiter;
    my $var_name;
    my $var_word;
    my $word;
    $self->skip_whitespace();
    if (!$self->lex_consume_word("for")) {
        return undef;
    }
    $self->skip_whitespace();
    if ($self->peek() eq "(" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
        return $self->parse_for_arith();
    }
    my $var_name = "";
    if ($self->peek() eq "\$") {
        $var_word = $self->parse_word(0, 0, 0);
        if (!defined($var_word)) {
            die "Expected variable name after 'for'";
        }
        $var_name = $var_word->{value};
    } else {
        $var_name = $self->peek_word();
        if ($var_name eq "") {
            die "Expected variable name after 'for'";
        }
        $self->consume_word($var_name);
    }
    $self->skip_whitespace();
    if ($self->peek() eq ";") {
        $self->advance();
    }
    $self->skip_whitespace_and_newlines();
    my $words = undef;
    if ($self->lex_is_at_reserved_word("in")) {
        $self->lex_consume_word("in");
        $self->skip_whitespace();
        $saw_delimiter = is_semicolon_or_newline($self->peek());
        if ($self->peek() eq ";") {
            $self->advance();
        }
        $self->skip_whitespace_and_newlines();
        $words = [];
        while (1) {
            $self->skip_whitespace();
            if ($self->at_end()) {
                last;
            }
            if (is_semicolon_or_newline($self->peek())) {
                $saw_delimiter = 1;
                if ($self->peek() eq ";") {
                    $self->advance();
                }
                last;
            }
            if ($self->lex_is_at_reserved_word("do")) {
                if ($saw_delimiter) {
                    last;
                }
                die "Expected ';' or newline before 'do'";
            }
            $word = $self->parse_word(0, 0, 0);
            if (!defined($word)) {
                last;
            }
            $words->push($word);
        }
    }
    $self->skip_whitespace_and_newlines();
    if ($self->peek() eq "{") {
        $brace_group = $self->parse_brace_group();
        if (!defined($brace_group)) {
            die "Expected brace group in for loop";
        }
        return For->new($var_name, $words, $brace_group->{body}, $self->collect_redirects(), "for");
    }
    if (!$self->lex_consume_word("do")) {
        die "Expected 'do' in for loop";
    }
    my $body = $self->parse_list_until({"done" => 1});
    if (!defined($body)) {
        die "Expected commands after 'do'";
    }
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("done")) {
        die "Expected 'done' to close for loop";
    }
    return For->new($var_name, $words, $body, $self->collect_redirects(), "for");
}

sub parse_for_arith ($self) {
    my $ch;
    $self->advance();
    $self->advance();
    my $parts = [];
    my $current = [];
    my $paren_depth = 0;
    while (!$self->at_end()) {
        $ch = $self->peek();
        if ($ch eq "(") {
            $paren_depth += 1;
            $current->push($self->advance());
        } elsif ($ch eq ")") {
            if ($paren_depth > 0) {
                $paren_depth -= 1;
                $current->push($self->advance());
            } elsif ($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq ")") {
                $parts->push((""->join_($current) =~ s/^[" \t"]+//r));
                $self->advance();
                $self->advance();
                last;
            } else {
                $current->push($self->advance());
            }
        } elsif ($ch eq ";" && $paren_depth == 0) {
            $parts->push((""->join_($current) =~ s/^[" \t"]+//r));
            $current = [];
            $self->advance();
        } else {
            $current->push($self->advance());
        }
    }
    if (scalar(@{$parts}) != 3) {
        die "Expected three expressions in for ((;;))";
    }
    my $init = $parts->[0];
    my $cond = $parts->[1];
    my $incr = $parts->[2];
    $self->skip_whitespace();
    if (!$self->at_end() && $self->peek() eq ";") {
        $self->advance();
    }
    $self->skip_whitespace_and_newlines();
    my $body = $self->parse_loop_body("for loop");
    return ForArith->new($init, $cond, $incr, $body, $self->collect_redirects(), "for-arith");
}

sub parse_select ($self) {
    my $word;
    $self->skip_whitespace();
    if (!$self->lex_consume_word("select")) {
        return undef;
    }
    $self->skip_whitespace();
    my $var_name = $self->peek_word();
    if ($var_name eq "") {
        die "Expected variable name after 'select'";
    }
    $self->consume_word($var_name);
    $self->skip_whitespace();
    if ($self->peek() eq ";") {
        $self->advance();
    }
    $self->skip_whitespace_and_newlines();
    my $words = undef;
    if ($self->lex_is_at_reserved_word("in")) {
        $self->lex_consume_word("in");
        $self->skip_whitespace_and_newlines();
        $words = [];
        while (1) {
            $self->skip_whitespace();
            if ($self->at_end()) {
                last;
            }
            if (is_semicolon_newline_brace($self->peek())) {
                if ($self->peek() eq ";") {
                    $self->advance();
                }
                last;
            }
            if ($self->lex_is_at_reserved_word("do")) {
                last;
            }
            $word = $self->parse_word(0, 0, 0);
            if (!defined($word)) {
                last;
            }
            $words->push($word);
        }
    }
    $self->skip_whitespace_and_newlines();
    my $body = $self->parse_loop_body("select");
    return Select->new($var_name, $words, $body, $self->collect_redirects(), "select");
}

sub consume_case_terminator ($self) {
    my $term = $self->lex_peek_case_terminator();
    if ($term ne "") {
        $self->lex_next_token();
        return $term;
    }
    return ";;";
}

sub parse_case ($self) {
    my $body;
    my $c;
    my $ch;
    my $extglob_depth;
    my $has_first_bracket_literal;
    my $is_at_terminator;
    my $is_char_class;
    my $is_empty_body;
    my $is_pattern;
    my $next_ch;
    my $paren_depth;
    my $pattern;
    my $pattern_chars;
    my $saved;
    my $sc;
    my $scan_depth;
    my $scan_pos;
    my $terminator;
    if (!$self->consume_word("case")) {
        return undef;
    }
    $self->set_state(PARSERSTATEFLAGS_PST_CASESTMT());
    $self->skip_whitespace();
    my $word = $self->parse_word(0, 0, 0);
    if (!defined($word)) {
        die "Expected word after 'case'";
    }
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("in")) {
        die "Expected 'in' after case word";
    }
    $self->skip_whitespace_and_newlines();
    my $patterns = [];
    $self->set_state(PARSERSTATEFLAGS_PST_CASEPAT());
    while (1) {
        $self->skip_whitespace_and_newlines();
        if ($self->lex_is_at_reserved_word("esac")) {
            $saved = $self->{pos_};
            $self->skip_whitespace();
            while (!$self->at_end() && !is_metachar($self->peek()) && !is_quote($self->peek())) {
                $self->advance();
            }
            $self->skip_whitespace();
            $is_pattern = 0;
            if (!$self->at_end() && $self->peek() eq ")") {
                if ($self->{eof_token} eq ")") {
                    $is_pattern = 0;
                } else {
                    $self->advance();
                    $self->skip_whitespace();
                    if (!$self->at_end()) {
                        $next_ch = $self->peek();
                        if ($next_ch eq ";") {
                            $is_pattern = 1;
                        } elsif (!is_newline_or_right_paren($next_ch)) {
                            $is_pattern = 1;
                        }
                    }
                }
            }
            $self->{pos_} = $saved;
            if (!$is_pattern) {
                last;
            }
        }
        $self->skip_whitespace_and_newlines();
        if (!$self->at_end() && $self->peek() eq "(") {
            $self->advance();
            $self->skip_whitespace_and_newlines();
        }
        $pattern_chars = [];
        $extglob_depth = 0;
        while (!$self->at_end()) {
            $ch = $self->peek();
            if ($ch eq ")") {
                if ($extglob_depth > 0) {
                    $pattern_chars->push($self->advance());
                    $extglob_depth -= 1;
                } else {
                    $self->advance();
                    last;
                }
            } elsif ($ch eq "\\") {
                if ($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "\n") {
                    $self->advance();
                    $self->advance();
                } else {
                    $pattern_chars->push($self->advance());
                    if (!$self->at_end()) {
                        $pattern_chars->push($self->advance());
                    }
                }
            } elsif (is_expansion_start($self->{source}, $self->{pos_}, "\$(")) {
                $pattern_chars->push($self->advance());
                $pattern_chars->push($self->advance());
                if (!$self->at_end() && $self->peek() eq "(") {
                    $pattern_chars->push($self->advance());
                    $paren_depth = 2;
                    while (!$self->at_end() && $paren_depth > 0) {
                        $c = $self->peek();
                        if ($c eq "(") {
                            $paren_depth += 1;
                        } elsif ($c eq ")") {
                            $paren_depth -= 1;
                        }
                        $pattern_chars->push($self->advance());
                    }
                } else {
                    $extglob_depth += 1;
                }
            } elsif ($ch eq "(" && $extglob_depth > 0) {
                $pattern_chars->push($self->advance());
                $extglob_depth += 1;
            } elsif ($self->{extglob} && is_extglob_prefix($ch) && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
                $pattern_chars->push($self->advance());
                $pattern_chars->push($self->advance());
                $extglob_depth += 1;
            } elsif ($ch eq "[") {
                $is_char_class = 0;
                $scan_pos = $self->{pos_} + 1;
                $scan_depth = 0;
                $has_first_bracket_literal = 0;
                if ($scan_pos < $self->{length_} && is_caret_or_bang($self->{source}->[$scan_pos])) {
                    $scan_pos += 1;
                }
                if ($scan_pos < $self->{length_} && $self->{source}->[$scan_pos] eq "]") {
                    if ($self->{source}->find("]", $scan_pos + 1) != -1) {
                        $scan_pos += 1;
                        $has_first_bracket_literal = 1;
                    }
                }
                while ($scan_pos < $self->{length_}) {
                    $sc = $self->{source}->[$scan_pos];
                    if ($sc eq "]" && $scan_depth == 0) {
                        $is_char_class = 1;
                        last;
                    } elsif ($sc eq "[") {
                        $scan_depth += 1;
                    } elsif ($sc eq ")" && $scan_depth == 0) {
                        last;
                    } elsif ($sc eq "|" && $scan_depth == 0) {
                        last;
                    }
                    $scan_pos += 1;
                }
                if ($is_char_class) {
                    $pattern_chars->push($self->advance());
                    if (!$self->at_end() && is_caret_or_bang($self->peek())) {
                        $pattern_chars->push($self->advance());
                    }
                    if ($has_first_bracket_literal && !$self->at_end() && $self->peek() eq "]") {
                        $pattern_chars->push($self->advance());
                    }
                    while (!$self->at_end() && $self->peek() ne "]") {
                        $pattern_chars->push($self->advance());
                    }
                    if (!$self->at_end()) {
                        $pattern_chars->push($self->advance());
                    }
                } else {
                    $pattern_chars->push($self->advance());
                }
            } elsif ($ch eq "'") {
                $pattern_chars->push($self->advance());
                while (!$self->at_end() && $self->peek() ne "'") {
                    $pattern_chars->push($self->advance());
                }
                if (!$self->at_end()) {
                    $pattern_chars->push($self->advance());
                }
            } elsif ($ch eq "\"") {
                $pattern_chars->push($self->advance());
                while (!$self->at_end() && $self->peek() ne "\"") {
                    if ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        $pattern_chars->push($self->advance());
                    }
                    $pattern_chars->push($self->advance());
                }
                if (!$self->at_end()) {
                    $pattern_chars->push($self->advance());
                }
            } elsif (is_whitespace($ch)) {
                if ($extglob_depth > 0) {
                    $pattern_chars->push($self->advance());
                } else {
                    $self->advance();
                }
            } else {
                $pattern_chars->push($self->advance());
            }
        }
        $pattern = ""->join_($pattern_chars);
        if (!(length($pattern) > 0)) {
            die "Expected pattern in case statement";
        }
        $self->skip_whitespace();
        $body = undef;
        $is_empty_body = $self->lex_peek_case_terminator() ne "";
        if (!$is_empty_body) {
            $self->skip_whitespace_and_newlines();
            if (!$self->at_end() && !$self->lex_is_at_reserved_word("esac")) {
                $is_at_terminator = $self->lex_peek_case_terminator() ne "";
                if (!$is_at_terminator) {
                    $body = $self->parse_list_until({"esac" => 1});
                    $self->skip_whitespace();
                }
            }
        }
        $terminator = $self->consume_case_terminator();
        $self->skip_whitespace_and_newlines();
        $patterns->push(CasePattern->new($pattern, $body, $terminator, "pattern"));
    }
    $self->clear_state(PARSERSTATEFLAGS_PST_CASEPAT());
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("esac")) {
        $self->clear_state(PARSERSTATEFLAGS_PST_CASESTMT());
        die "Expected 'esac' to close case statement";
    }
    $self->clear_state(PARSERSTATEFLAGS_PST_CASESTMT());
    return Case->new($word, $patterns, $self->collect_redirects(), "case");
}

sub parse_coproc ($self) {
    my $body;
    $self->skip_whitespace();
    if (!$self->lex_consume_word("coproc")) {
        return undef;
    }
    $self->skip_whitespace();
    my $name = "";
    my $ch = "";
    if (!$self->at_end()) {
        $ch = $self->peek();
    }
    my $body = undef;
    if ($ch eq "{") {
        $body = $self->parse_brace_group();
        if (defined($body)) {
            return Coproc->new($body, $name, "coproc");
        }
    }
    if ($ch eq "(") {
        if ($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
            $body = $self->parse_arithmetic_command();
            if (defined($body)) {
                return Coproc->new($body, $name, "coproc");
            }
        }
        $body = $self->parse_subshell();
        if (defined($body)) {
            return Coproc->new($body, $name, "coproc");
        }
    }
    my $next_word = $self->lex_peek_reserved_word();
    if ($next_word ne "" && (exists(COMPOUND_KEYWORDS()->{$next_word}))) {
        $body = $self->parse_compound_command();
        if (defined($body)) {
            return Coproc->new($body, $name, "coproc");
        }
    }
    my $word_start = $self->{pos_};
    my $potential_name = $self->peek_word();
    if ((length($potential_name) > 0)) {
        while (!$self->at_end() && !is_metachar($self->peek()) && !is_quote($self->peek())) {
            $self->advance();
        }
        $self->skip_whitespace();
        $ch = "";
        if (!$self->at_end()) {
            $ch = $self->peek();
        }
        $next_word = $self->lex_peek_reserved_word();
        if (is_valid_identifier($potential_name)) {
            if ($ch eq "{") {
                $name = $potential_name;
                $body = $self->parse_brace_group();
                if (defined($body)) {
                    return Coproc->new($body, $name, "coproc");
                }
            } elsif ($ch eq "(") {
                $name = $potential_name;
                if ($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
                    $body = $self->parse_arithmetic_command();
                } else {
                    $body = $self->parse_subshell();
                }
                if (defined($body)) {
                    return Coproc->new($body, $name, "coproc");
                }
            } elsif ($next_word ne "" && (exists(COMPOUND_KEYWORDS()->{$next_word}))) {
                $name = $potential_name;
                $body = $self->parse_compound_command();
                if (defined($body)) {
                    return Coproc->new($body, $name, "coproc");
                }
            }
        }
        $self->{pos_} = $word_start;
    }
    $body = $self->parse_command();
    if (defined($body)) {
        return Coproc->new($body, $name, "coproc");
    }
    die "Expected command after coproc";
}

sub parse_function ($self) {
    my $body;
    my $name;
    $self->skip_whitespace();
    if ($self->at_end()) {
        return undef;
    }
    my $saved_pos = $self->{pos_};
    my $name = "";
    my $body = undef;
    if ($self->lex_is_at_reserved_word("function")) {
        $self->lex_consume_word("function");
        $self->skip_whitespace();
        $name = $self->peek_word();
        if ($name eq "") {
            $self->{pos_} = $saved_pos;
            return undef;
        }
        $self->consume_word($name);
        $self->skip_whitespace();
        if (!$self->at_end() && $self->peek() eq "(") {
            if ($self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq ")") {
                $self->advance();
                $self->advance();
            }
        }
        $self->skip_whitespace_and_newlines();
        $body = $self->parse_compound_command();
        if (!defined($body)) {
            die "Expected function body";
        }
        return Function->new($name, $body, "function");
    }
    $name = $self->peek_word();
    if ($name eq "" || (exists(RESERVED_WORDS()->{$name}))) {
        return undef;
    }
    if (looks_like_assignment($name)) {
        return undef;
    }
    $self->skip_whitespace();
    my $name_start = $self->{pos_};
    while (!$self->at_end() && !is_metachar($self->peek()) && !is_quote($self->peek()) && !is_paren($self->peek())) {
        $self->advance();
    }
    $name = substring($self->{source}, $name_start, $self->{pos_});
    if (!(length($name) > 0)) {
        $self->{pos_} = $saved_pos;
        return undef;
    }
    my $brace_depth = 0;
    my $i = 0;
    while ($i < length($name)) {
        if (is_expansion_start($name, $i, "\${")) {
            $brace_depth += 1;
            $i += 2;
            next;
        }
        if ($name->[$i] eq "}") {
            $brace_depth -= 1;
        }
        $i += 1;
    }
    if ($brace_depth > 0) {
        $self->{pos_} = $saved_pos;
        return undef;
    }
    my $pos_after_name = $self->{pos_};
    $self->skip_whitespace();
    my $has_whitespace = $self->{pos_} > $pos_after_name;
    if (!$has_whitespace && (length($name) > 0) && ((index("*?\@+!\$", $name->[-1]) >= 0))) {
        $self->{pos_} = $saved_pos;
        return undef;
    }
    if ($self->at_end() || $self->peek() ne "(") {
        $self->{pos_} = $saved_pos;
        return undef;
    }
    $self->advance();
    $self->skip_whitespace();
    if ($self->at_end() || $self->peek() ne ")") {
        $self->{pos_} = $saved_pos;
        return undef;
    }
    $self->advance();
    $self->skip_whitespace_and_newlines();
    $body = $self->parse_compound_command();
    if (!defined($body)) {
        die "Expected function body";
    }
    return Function->new($name, $body, "function");
}

sub parse_compound_command ($self) {
    my $result = $self->parse_brace_group();
    if (defined($result)) {
        return $result;
    }
    if (!$self->at_end() && $self->peek() eq "(" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
        $result = $self->parse_arithmetic_command();
        if (defined($result)) {
            return $result;
        }
    }
    $result = $self->parse_subshell();
    if (defined($result)) {
        return $result;
    }
    $result = $self->parse_conditional_expr();
    if (defined($result)) {
        return $result;
    }
    $result = $self->parse_if();
    if (defined($result)) {
        return $result;
    }
    $result = $self->parse_while();
    if (defined($result)) {
        return $result;
    }
    $result = $self->parse_until();
    if (defined($result)) {
        return $result;
    }
    $result = $self->parse_for();
    if (defined($result)) {
        return $result;
    }
    $result = $self->parse_case();
    if (defined($result)) {
        return $result;
    }
    $result = $self->parse_select();
    if (defined($result)) {
        return $result;
    }
    return undef;
}

sub at_list_until_terminator ($self, $stop_words) {
    my $next_pos;
    if ($self->at_end()) {
        return 1;
    }
    if ($self->peek() eq ")") {
        return 1;
    }
    if ($self->peek() eq "}") {
        $next_pos = $self->{pos_} + 1;
        if ($next_pos >= $self->{length_} || is_word_end_context($self->{source}->[$next_pos])) {
            return 1;
        }
    }
    my $reserved = $self->lex_peek_reserved_word();
    if ($reserved ne "" && (exists($stop_words->{$reserved}))) {
        return 1;
    }
    if ($self->lex_peek_case_terminator() ne "") {
        return 1;
    }
    return 0;
}

sub parse_list_until ($self, $stop_words) {
    my $next_op;
    my $op;
    $self->skip_whitespace_and_newlines();
    my $reserved = $self->lex_peek_reserved_word();
    if ($reserved ne "" && (exists($stop_words->{$reserved}))) {
        return undef;
    }
    my $pipeline = $self->parse_pipeline();
    if (!defined($pipeline)) {
        return undef;
    }
    my $parts = [$pipeline];
    while (1) {
        $self->skip_whitespace();
        $op = $self->parse_list_operator();
        if ($op eq "") {
            if (!$self->at_end() && $self->peek() eq "\n") {
                $self->advance();
                $self->gather_heredoc_bodies();
                if ($self->{cmdsub_heredoc_end} != -1 && $self->{cmdsub_heredoc_end} > $self->{pos_}) {
                    $self->{pos_} = $self->{cmdsub_heredoc_end};
                    $self->{cmdsub_heredoc_end} = -1;
                }
                $self->skip_whitespace_and_newlines();
                if ($self->at_list_until_terminator($stop_words)) {
                    last;
                }
                $next_op = $self->peek_list_operator();
                if ($next_op eq "&" || $next_op eq ";") {
                    last;
                }
                $op = "\n";
            } else {
                last;
            }
        }
        if ($op eq "") {
            last;
        }
        if ($op eq ";") {
            $self->skip_whitespace_and_newlines();
            if ($self->at_list_until_terminator($stop_words)) {
                last;
            }
            $parts->push(Operator->new($op, "operator"));
        } elsif ($op eq "&") {
            $parts->push(Operator->new($op, "operator"));
            $self->skip_whitespace_and_newlines();
            if ($self->at_list_until_terminator($stop_words)) {
                last;
            }
        } elsif ($op eq "&&" || $op eq "||") {
            $parts->push(Operator->new($op, "operator"));
            $self->skip_whitespace_and_newlines();
        } else {
            $parts->push(Operator->new($op, "operator"));
        }
        if ($self->at_list_until_terminator($stop_words)) {
            last;
        }
        $pipeline = $self->parse_pipeline();
        if (!defined($pipeline)) {
            die "Expected command after " . $op;
        }
        $parts->push($pipeline);
    }
    if (scalar(@{$parts}) == 1) {
        return $parts->[0];
    }
    return List->new($parts, "list");
}

sub parse_compound_command ($self) {
    my $keyword_word;
    my $result;
    my $word;
    $self->skip_whitespace();
    if ($self->at_end()) {
        return undef;
    }
    my $ch = $self->peek();
    my $result = undef;
    if ($ch eq "(" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "(") {
        $result = $self->parse_arithmetic_command();
        if (defined($result)) {
            return $result;
        }
    }
    if ($ch eq "(") {
        return $self->parse_subshell();
    }
    if ($ch eq "{") {
        $result = $self->parse_brace_group();
        if (defined($result)) {
            return $result;
        }
    }
    if ($ch eq "[" && $self->{pos_} + 1 < $self->{length_} && $self->{source}->[$self->{pos_} + 1] eq "[") {
        $result = $self->parse_conditional_expr();
        if (defined($result)) {
            return $result;
        }
    }
    my $reserved = $self->lex_peek_reserved_word();
    if ($reserved eq "" && $self->{in_process_sub}) {
        $word = $self->peek_word();
        if ($word ne "" && length($word) > 1 && $word->[0] eq "}") {
            $keyword_word = substr($word, 1);
            if ((exists(RESERVED_WORDS()->{$keyword_word})) || $keyword_word eq "{" || $keyword_word eq "}" || $keyword_word eq "[[" || $keyword_word eq "]]" || $keyword_word eq "!" || $keyword_word eq "time") {
                $reserved = $keyword_word;
            }
        }
    }
    if ($reserved eq "fi" || $reserved eq "then" || $reserved eq "elif" || $reserved eq "else" || $reserved eq "done" || $reserved eq "esac" || $reserved eq "do" || $reserved eq "in") {
        die sprintf("Unexpected reserved word '%s'", $reserved);
    }
    if ($reserved eq "if") {
        return $self->parse_if();
    }
    if ($reserved eq "while") {
        return $self->parse_while();
    }
    if ($reserved eq "until") {
        return $self->parse_until();
    }
    if ($reserved eq "for") {
        return $self->parse_for();
    }
    if ($reserved eq "select") {
        return $self->parse_select();
    }
    if ($reserved eq "case") {
        return $self->parse_case();
    }
    if ($reserved eq "function") {
        return $self->parse_function();
    }
    if ($reserved eq "coproc") {
        return $self->parse_coproc();
    }
    my $func = $self->parse_function();
    if (defined($func)) {
        return $func;
    }
    return $self->parse_command();
}

sub parse_pipeline ($self) {
    my $inner;
    my $saved;
    $self->skip_whitespace();
    my $prefix_order = "";
    my $time_posix = 0;
    if ($self->lex_is_at_reserved_word("time")) {
        $self->lex_consume_word("time");
        $prefix_order = "time";
        $self->skip_whitespace();
        my $saved = 0;
        if (!$self->at_end() && $self->peek() eq "-") {
            $saved = $self->{pos_};
            $self->advance();
            if (!$self->at_end() && $self->peek() eq "p") {
                $self->advance();
                if ($self->at_end() || is_metachar($self->peek())) {
                    $time_posix = 1;
                } else {
                    $self->{pos_} = $saved;
                }
            } else {
                $self->{pos_} = $saved;
            }
        }
        $self->skip_whitespace();
        if (!$self->at_end() && starts_with_at($self->{source}, $self->{pos_}, "--")) {
            if ($self->{pos_} + 2 >= $self->{length_} || is_whitespace($self->{source}->[$self->{pos_} + 2])) {
                $self->advance();
                $self->advance();
                $time_posix = 1;
                $self->skip_whitespace();
            }
        }
        while ($self->lex_is_at_reserved_word("time")) {
            $self->lex_consume_word("time");
            $self->skip_whitespace();
            if (!$self->at_end() && $self->peek() eq "-") {
                $saved = $self->{pos_};
                $self->advance();
                if (!$self->at_end() && $self->peek() eq "p") {
                    $self->advance();
                    if ($self->at_end() || is_metachar($self->peek())) {
                        $time_posix = 1;
                    } else {
                        $self->{pos_} = $saved;
                    }
                } else {
                    $self->{pos_} = $saved;
                }
            }
        }
        $self->skip_whitespace();
        if (!$self->at_end() && $self->peek() eq "!") {
            if (($self->{pos_} + 1 >= $self->{length_} || is_negation_boundary($self->{source}->[$self->{pos_} + 1])) && !$self->is_bang_followed_by_procsub()) {
                $self->advance();
                $prefix_order = "time_negation";
                $self->skip_whitespace();
            }
        }
    } elsif (!$self->at_end() && $self->peek() eq "!") {
        if (($self->{pos_} + 1 >= $self->{length_} || is_negation_boundary($self->{source}->[$self->{pos_} + 1])) && !$self->is_bang_followed_by_procsub()) {
            $self->advance();
            $self->skip_whitespace();
            $inner = $self->parse_pipeline();
            if (defined($inner) && $inner->{kind} == "negation") {
                if (defined($inner->{pipeline})) {
                    return $inner->{pipeline};
                } else {
                    return Command->new([], "command");
                }
            }
            return Negation->new($inner, "negation");
        }
    }
    my $result = $self->parse_simple_pipeline();
    if ($prefix_order eq "time") {
        $result = Time->new($result, $time_posix, "time");
    } elsif ($prefix_order eq "negation") {
        $result = Negation->new($result, "negation");
    } elsif ($prefix_order eq "time_negation") {
        $result = Time->new($result, $time_posix, "time");
        $result = Negation->new($result, "negation");
    } elsif ($prefix_order eq "negation_time") {
        $result = Time->new($result, $time_posix, "time");
        $result = Negation->new($result, "negation");
    } elsif (!defined($result)) {
        return undef;
    }
    return $result;
}

sub parse_simple_pipeline ($self) {
    my $is_pipe_both;
    my $token_type;
    my $value;
    my $cmd = $self->parse_compound_command();
    if (!defined($cmd)) {
        return undef;
    }
    my $commands = [$cmd];
    while (1) {
        $self->skip_whitespace();
        ($token_type, $value) = @{$self->lex_peek_operator()};
        if ($token_type == 0) {
            last;
        }
        if ($token_type != TOKENTYPE_PIPE() && $token_type != TOKENTYPE_PIPE_AMP()) {
            last;
        }
        $self->lex_next_token();
        $is_pipe_both = $token_type == TOKENTYPE_PIPE_AMP();
        $self->skip_whitespace_and_newlines();
        if ($is_pipe_both) {
            $commands->push(PipeBoth->new("pipe-both"));
        }
        $cmd = $self->parse_compound_command();
        if (!defined($cmd)) {
            die "Expected command after |";
        }
        $commands->push($cmd);
    }
    if (scalar(@{$commands}) == 1) {
        return $commands->[0];
    }
    return Pipeline->new($commands, "pipeline");
}

sub parse_list_operator ($self) {
    $self->skip_whitespace();
    my ($token_type, $_unused) = @{$self->lex_peek_operator()};
    if ($token_type == 0) {
        return "";
    }
    if ($token_type == TOKENTYPE_AND_AND()) {
        $self->lex_next_token();
        return "&&";
    }
    if ($token_type == TOKENTYPE_OR_OR()) {
        $self->lex_next_token();
        return "||";
    }
    if ($token_type == TOKENTYPE_SEMI()) {
        $self->lex_next_token();
        return ";";
    }
    if ($token_type == TOKENTYPE_AMP()) {
        $self->lex_next_token();
        return "&";
    }
    return "";
}

sub peek_list_operator ($self) {
    my $saved_pos = $self->{pos_};
    my $op = $self->parse_list_operator();
    $self->{pos_} = $saved_pos;
    return $op;
}

sub parse_list ($self, $newline_as_separator) {
    my $next_op;
    my $op;
    if ($newline_as_separator) {
        $self->skip_whitespace_and_newlines();
    } else {
        $self->skip_whitespace();
    }
    my $pipeline = $self->parse_pipeline();
    if (!defined($pipeline)) {
        return undef;
    }
    my $parts = [$pipeline];
    if ($self->in_state(PARSERSTATEFLAGS_PST_EOFTOKEN()) && $self->at_eof_token()) {
        return (scalar(@{$parts}) == 1 ? $parts->[0] : List->new($parts, "list"));
    }
    while (1) {
        $self->skip_whitespace();
        $op = $self->parse_list_operator();
        if ($op eq "") {
            if (!$self->at_end() && $self->peek() eq "\n") {
                if (!$newline_as_separator) {
                    last;
                }
                $self->advance();
                $self->gather_heredoc_bodies();
                if ($self->{cmdsub_heredoc_end} != -1 && $self->{cmdsub_heredoc_end} > $self->{pos_}) {
                    $self->{pos_} = $self->{cmdsub_heredoc_end};
                    $self->{cmdsub_heredoc_end} = -1;
                }
                $self->skip_whitespace_and_newlines();
                if ($self->at_end() || $self->at_list_terminating_bracket()) {
                    last;
                }
                $next_op = $self->peek_list_operator();
                if ($next_op eq "&" || $next_op eq ";") {
                    last;
                }
                $op = "\n";
            } else {
                last;
            }
        }
        if ($op eq "") {
            last;
        }
        $parts->push(Operator->new($op, "operator"));
        if ($op eq "&&" || $op eq "||") {
            $self->skip_whitespace_and_newlines();
        } elsif ($op eq "&") {
            $self->skip_whitespace();
            if ($self->at_end() || $self->at_list_terminating_bracket()) {
                last;
            }
            if ($self->peek() eq "\n") {
                if ($newline_as_separator) {
                    $self->skip_whitespace_and_newlines();
                    if ($self->at_end() || $self->at_list_terminating_bracket()) {
                        last;
                    }
                } else {
                    last;
                }
            }
        } elsif ($op eq ";") {
            $self->skip_whitespace();
            if ($self->at_end() || $self->at_list_terminating_bracket()) {
                last;
            }
            if ($self->peek() eq "\n") {
                if ($newline_as_separator) {
                    $self->skip_whitespace_and_newlines();
                    if ($self->at_end() || $self->at_list_terminating_bracket()) {
                        last;
                    }
                } else {
                    last;
                }
            }
        }
        $pipeline = $self->parse_pipeline();
        if (!defined($pipeline)) {
            die "Expected command after " . $op;
        }
        $parts->push($pipeline);
        if ($self->in_state(PARSERSTATEFLAGS_PST_EOFTOKEN()) && $self->at_eof_token()) {
            last;
        }
    }
    if (scalar(@{$parts}) == 1) {
        return $parts->[0];
    }
    return List->new($parts, "list");
}

sub parse_comment ($self) {
    if ($self->at_end() || $self->peek() ne "#") {
        return undef;
    }
    my $start = $self->{pos_};
    while (!$self->at_end() && $self->peek() ne "\n") {
        $self->advance();
    }
    my $text = substring($self->{source}, $start, $self->{pos_});
    return Comment->new($text, "comment");
}

sub parse ($self) {
    my $comment;
    my $found_newline;
    my $result;
    my $source = ($self->{source} =~ s/^\s+|\s+$//gr);
    if (!(length($source) > 0)) {
        return [Empty->new("empty")];
    }
    my $results = [];
    while (1) {
        $self->skip_whitespace();
        while (!$self->at_end() && $self->peek() eq "\n") {
            $self->advance();
        }
        if ($self->at_end()) {
            last;
        }
        $comment = $self->parse_comment();
        if (!defined($comment)) {
            last;
        }
    }
    while (!$self->at_end()) {
        $result = $self->parse_list(0);
        if (defined($result)) {
            $results->push($result);
        }
        $self->skip_whitespace();
        $found_newline = 0;
        while (!$self->at_end() && $self->peek() eq "\n") {
            $found_newline = 1;
            $self->advance();
            $self->gather_heredoc_bodies();
            if ($self->{cmdsub_heredoc_end} != -1 && $self->{cmdsub_heredoc_end} > $self->{pos_}) {
                $self->{pos_} = $self->{cmdsub_heredoc_end};
                $self->{cmdsub_heredoc_end} = -1;
            }
            $self->skip_whitespace();
        }
        if (!$found_newline && !$self->at_end()) {
            die "Syntax error";
        }
    }
    if (!(scalar(@{$results}) > 0)) {
        return [Empty->new("empty")];
    }
    if ($self->{saw_newline_in_single_quote} && (length($self->{source}) > 0) && $self->{source}->[-1] eq "\\" && !(length($self->{source}) >= 3 && substr($self->{source}, length($self->{source}) - 3, length($self->{source}) - 1 - length($self->{source}) - 3) eq "\\\n")) {
        if (!$self->last_word_on_own_line($results)) {
            $self->strip_trailing_backslash_from_last_word($results);
        }
    }
    return $results;
}

sub last_word_on_own_line ($self, $nodes) {
    return scalar(@{$nodes}) >= 2;
}

sub strip_trailing_backslash_from_last_word ($self, $nodes) {
    if (!(scalar(@{$nodes}) > 0)) {
        return;
    }
    my $last_node = $nodes->[-1];
    my $last_word = $self->find_last_word($last_node);
    if (defined($last_word) && $last_word->{value}->endswith("\\")) {
        $last_word->{value} = substring($last_word->{value}, 0, length($last_word->{value}) - 1);
        if (!(length($last_word->{value}) > 0) && (ref($last_node) eq 'Command') && (scalar(@{$last_node->{words}}) > 0)) {
            $last_node->{words}->pop_();
        }
    }
}

sub find_last_word ($self, $node) {
    my $last_redirect;
    my $last_word;
    if (ref($node) eq 'Word') {
        my $node = $node;
        return $node;
    }
    if (ref($node) eq 'Command') {
        my $node = $node;
        if ((scalar(@{$node->{words}}) > 0)) {
            $last_word = $node->{words}->[-1];
            if ($last_word->{value}->endswith("\\")) {
                return $last_word;
            }
        }
        if ((scalar(@{$node->{redirects}}) > 0)) {
            $last_redirect = $node->{redirects}->[-1];
            if (ref($last_redirect) eq 'Redirect') {
                my $last_redirect = $last_redirect;
                return $last_redirect->{target};
            }
        }
        if ((scalar(@{$node->{words}}) > 0)) {
            return $node->{words}->[-1];
        }
    }
    if (ref($node) eq 'Pipeline') {
        my $node = $node;
        if ((scalar(@{$node->{commands}}) > 0)) {
            return $self->find_last_word($node->{commands}->[-1]);
        }
    }
    if (ref($node) eq 'List') {
        my $node = $node;
        if ((scalar(@{$node->{parts}}) > 0)) {
            return $self->find_last_word($node->{parts}->[-1]);
        }
    }
    return undef;
}

1;

sub is_hex_digit ($c) {
    return $c ge "0" && $c le "9" || $c ge "a" && $c le "f" || $c ge "A" && $c le "F";
}

sub is_octal_digit ($c) {
    return $c ge "0" && $c le "7";
}

sub get_ansi_escape ($c) {
    return ANSI_C_ESCAPES()->get($c, -1);
}

sub is_whitespace ($c) {
    return $c eq " " || $c eq "\t" || $c eq "\n";
}

sub string_to_bytes ($s_) {
    return [unpack('C*', $s_)]->copy();
}

sub is_whitespace_no_newline ($c) {
    return $c eq " " || $c eq "\t";
}

sub substring ($s_, $start, $end) {
    return substr($s_, $start, $end - $start);
}

sub starts_with_at ($s_, $pos_, $prefix) {
    return $s_->startswith($prefix, $pos_);
}

sub count_consecutive_dollars_before ($s_, $pos_) {
    my $bs_count;
    my $j;
    my $count = 0;
    my $k = $pos_ - 1;
    while ($k >= 0 && $s_->[$k] eq "\$") {
        $bs_count = 0;
        $j = $k - 1;
        while ($j >= 0 && $s_->[$j] eq "\\") {
            $bs_count += 1;
            $j -= 1;
        }
        if ($bs_count % 2 == 1) {
            last;
        }
        $count += 1;
        $k -= 1;
    }
    return $count;
}

sub is_expansion_start ($s_, $pos_, $delimiter) {
    if (!starts_with_at($s_, $pos_, $delimiter)) {
        return 0;
    }
    return count_consecutive_dollars_before($s_, $pos_) % 2 == 0;
}

sub sublist ($lst, $start, $end) {
    return [@{$lst}[$start .. $end - 1]];
}

sub repeat_str ($s_, $n) {
    my $result = [];
    my $i = 0;
    while ($i < $n) {
        $result->push($s_);
        $i += 1;
    }
    return ""->join_($result);
}

sub strip_line_continuations_comment_aware ($text) {
    my $c;
    my $j;
    my $num_preceding_backslashes;
    my $result = [];
    my $i = 0;
    my $in_comment = 0;
    my $quote = new_quote_state();
    while ($i < length($text)) {
        $c = $text->[$i];
        if ($c eq "\\" && $i + 1 < length($text) && $text->[$i + 1] eq "\n") {
            $num_preceding_backslashes = 0;
            $j = $i - 1;
            while ($j >= 0 && $text->[$j] eq "\\") {
                $num_preceding_backslashes += 1;
                $j -= 1;
            }
            if ($num_preceding_backslashes % 2 == 0) {
                if ($in_comment) {
                    $result->push("\n");
                }
                $i += 2;
                $in_comment = 0;
                next;
            }
        }
        if ($c eq "\n") {
            $in_comment = 0;
            $result->push($c);
            $i += 1;
            next;
        }
        if ($c eq "'" && !$quote->{double} && !$in_comment) {
            $quote->{single} = !$quote->{single};
        } elsif ($c eq "\"" && !$quote->{single} && !$in_comment) {
            $quote->{double} = !$quote->{double};
        } elsif ($c eq "#" && !$quote->{single} && !$in_comment) {
            $in_comment = 1;
        }
        $result->push($c);
        $i += 1;
    }
    return ""->join_($result);
}

sub append_redirects ($base, $redirects) {
    my $parts;
    if ((scalar(@{$redirects}) > 0)) {
        $parts = [];
        for my $r (@{$redirects}) {
            $parts->push($r->to_sexp());
        }
        return $base . " " . " "->join_($parts);
    }
    return $base;
}

sub format_arith_val ($s_) {
    my $w = Word->new($s_, [], "word");
    my $val = $w->expand_all_ansi_c_quotes($s_);
    $val = $w->strip_locale_string_dollars($val);
    $val = $w->format_command_substitutions($val, 0);
    $val = $val->replace("\\", "\\\\")->replace("\"", "\\\"");
    $val = $val->replace("\n", "\\n")->replace("\t", "\\t");
    return $val;
}

sub consume_single_quote ($s_, $start) {
    my $chars = ["'"];
    my $i = $start + 1;
    while ($i < length($s_) && $s_->[$i] ne "'") {
        $chars->push($s_->[$i]);
        $i += 1;
    }
    if ($i < length($s_)) {
        $chars->push($s_->[$i]);
        $i += 1;
    }
    return [$i, $chars];
}

sub consume_double_quote ($s_, $start) {
    my $chars = ["\""];
    my $i = $start + 1;
    while ($i < length($s_) && $s_->[$i] ne "\"") {
        if ($s_->[$i] eq "\\" && $i + 1 < length($s_)) {
            $chars->push($s_->[$i]);
            $i += 1;
        }
        $chars->push($s_->[$i]);
        $i += 1;
    }
    if ($i < length($s_)) {
        $chars->push($s_->[$i]);
        $i += 1;
    }
    return [$i, $chars];
}

sub has_bracket_close ($s_, $start, $depth) {
    my $i = $start;
    while ($i < length($s_)) {
        if ($s_->[$i] eq "]") {
            return 1;
        }
        if (($s_->[$i] eq "|" || $s_->[$i] eq ")") && $depth == 0) {
            return 0;
        }
        $i += 1;
    }
    return 0;
}

sub consume_bracket_class ($s_, $start, $depth) {
    my $scan_pos = $start + 1;
    if ($scan_pos < length($s_) && ($s_->[$scan_pos] eq "!" || $s_->[$scan_pos] eq "^")) {
        $scan_pos += 1;
    }
    if ($scan_pos < length($s_) && $s_->[$scan_pos] eq "]") {
        if (has_bracket_close($s_, $scan_pos + 1, $depth)) {
            $scan_pos += 1;
        }
    }
    my $is_bracket = 0;
    while ($scan_pos < length($s_)) {
        if ($s_->[$scan_pos] eq "]") {
            $is_bracket = 1;
            last;
        }
        if ($s_->[$scan_pos] eq ")" && $depth == 0) {
            last;
        }
        if ($s_->[$scan_pos] eq "|" && $depth == 0) {
            last;
        }
        $scan_pos += 1;
    }
    if (!$is_bracket) {
        return [$start + 1, ["["], 0];
    }
    my $chars = ["["];
    my $i = $start + 1;
    if ($i < length($s_) && ($s_->[$i] eq "!" || $s_->[$i] eq "^")) {
        $chars->push($s_->[$i]);
        $i += 1;
    }
    if ($i < length($s_) && $s_->[$i] eq "]") {
        if (has_bracket_close($s_, $i + 1, $depth)) {
            $chars->push($s_->[$i]);
            $i += 1;
        }
    }
    while ($i < length($s_) && $s_->[$i] ne "]") {
        $chars->push($s_->[$i]);
        $i += 1;
    }
    if ($i < length($s_)) {
        $chars->push($s_->[$i]);
        $i += 1;
    }
    return [$i, $chars, 1];
}

sub format_cond_body ($node) {
    my $left_val;
    my $operand_val;
    my $right_val;
    my $kind = $node->{kind};
    if ($kind == "unary-test") {
        $operand_val = $node->{operand}->get_cond_formatted_value();
        return $node->{op} . " " . $operand_val;
    }
    if ($kind == "binary-test") {
        $left_val = $node->{left}->get_cond_formatted_value();
        $right_val = $node->{right}->get_cond_formatted_value();
        return $left_val . " " . $node->{op} . " " . $right_val;
    }
    if ($kind == "cond-and") {
        return format_cond_body($node->{left}) . " && " . format_cond_body($node->{right});
    }
    if ($kind == "cond-or") {
        return format_cond_body($node->{left}) . " || " . format_cond_body($node->{right});
    }
    if ($kind == "cond-not") {
        return "! " . format_cond_body($node->{operand});
    }
    if ($kind == "cond-paren") {
        return "( " . format_cond_body($node->{inner}) . " )";
    }
    return "";
}

sub starts_with_subshell ($node) {
    if (ref($node) eq 'Subshell') {
        my $node = $node;
        return 1;
    }
    if (ref($node) eq 'List') {
        my $node = $node;
        for my $p (@{($node->{parts} // [])}) {
            if ($p->{kind} != "operator") {
                return starts_with_subshell($p);
            }
        }
        return 0;
    }
    if (ref($node) eq 'Pipeline') {
        my $node = $node;
        if ((scalar(@{$node->{commands}}) > 0)) {
            return starts_with_subshell($node->{commands}->[0]);
        }
        return 0;
    }
    return 0;
}

sub format_cmdsub_node ($node, $indent, $in_procsub, $compact_redirects, $procsub_first) {
    my $body;
    my $body_part;
    my $cmd;
    my $cmd_count;
    my $cmds;
    my $compact_pipe;
    my $cond;
    my $else_body;
    my $first_nl;
    my $formatted;
    my $formatted_cmd;
    my $has_heredoc;
    my $heredocs;
    my $i;
    my $idx;
    my $inner_body;
    my $is_last;
    my $last_;
    my $name;
    my $needs_redirect;
    my $p;
    my $part;
    my $parts;
    my $pat;
    my $pat_indent;
    my $pattern_str;
    my $patterns;
    my $prefix;
    my $redirect_parts;
    my $redirects;
    my $result;
    my $result_parts;
    my $s_;
    my $skipped_semi;
    my $term;
    my $term_indent;
    my $terminator;
    my $then_body;
    my $val;
    my $var;
    my $word;
    my $word_parts;
    my $word_vals;
    my $words;
    if (!defined($node)) {
        return "";
    }
    my $sp = repeat_str(" ", $indent);
    my $inner_sp = repeat_str(" ", $indent + 4);
    if (ref($node) eq 'ArithEmpty') {
        my $node = $node;
        return "";
    }
    if (ref($node) eq 'Command') {
        my $node = $node;
        $parts = [];
        for my $w (@{($node->{words} // [])}) {
            $val = $w->expand_all_ansi_c_quotes($w->{value});
            $val = $w->strip_locale_string_dollars($val);
            $val = $w->normalize_array_whitespace($val);
            $val = $w->format_command_substitutions($val, 0);
            $parts->push($val);
        }
        $heredocs = [];
        for my $r (@{($node->{redirects} // [])}) {
            if (ref($r) eq 'HereDoc') {
                my $r = $r;
                $heredocs->push($r);
            }
        }
        for my $r (@{($node->{redirects} // [])}) {
            $parts->push(format_redirect($r, $compact_redirects, 1));
        }
        my $result = "";
        if ($compact_redirects && (scalar(@{$node->{words}}) > 0) && (scalar(@{$node->{redirects}}) > 0)) {
            $word_parts = [@{$parts}[0 .. scalar(@{$node->{words}}) - 1]];
            $redirect_parts = [@{$parts}[scalar(@{$node->{words}}) .. $#{$parts}]];
            $result = " "->join_($word_parts) . ""->join_($redirect_parts);
        } else {
            $result = " "->join_($parts);
        }
        for my $h (@{$heredocs}) {
            $result = $result + format_heredoc_body($h);
        }
        return $result;
    }
    if (ref($node) eq 'Pipeline') {
        my $node = $node;
        $cmds = [];
        $i = 0;
        my $cmd = undef;
        my $needs_redirect = 0;
        while ($i < scalar(@{$node->{commands}})) {
            $cmd = $node->{commands}->[$i];
            if (ref($cmd) eq 'PipeBoth') {
                my $cmd = $cmd;
                $i += 1;
                next;
            }
            $needs_redirect = $i + 1 < scalar(@{$node->{commands}}) && $node->{commands}->[$i + 1]->{kind} == "pipe-both";
            $cmds->push([$cmd, $needs_redirect]);
            $i += 1;
        }
        $result_parts = [];
        $idx = 0;
        while ($idx < scalar(@{$cmds})) {
            my $entry = $cmds->[$idx];
            $cmd = $entry->[0];
            $needs_redirect = $entry->[1];
            $formatted = format_cmdsub_node($cmd, $indent, $in_procsub, 0, $procsub_first && $idx == 0);
            $is_last = $idx == scalar(@{$cmds}) - 1;
            $has_heredoc = 0;
            if ($cmd->{kind} == "command" && (scalar(@{$cmd->{redirects}}) > 0)) {
                for my $r (@{($cmd->{redirects} // [])}) {
                    if (ref($r) eq 'HereDoc') {
                        my $r = $r;
                        $has_heredoc = 1;
                        last;
                    }
                }
            }
            my $first_nl = 0;
            if ($needs_redirect) {
                if ($has_heredoc) {
                    $first_nl = $formatted->find("\n");
                    if ($first_nl != -1) {
                        $formatted = substr($formatted, 0, $first_nl - 0) . " 2>&1" . substr($formatted, $first_nl);
                    } else {
                        $formatted = $formatted . " 2>&1";
                    }
                } else {
                    $formatted = $formatted . " 2>&1";
                }
            }
            if (!$is_last && $has_heredoc) {
                $first_nl = $formatted->find("\n");
                if ($first_nl != -1) {
                    $formatted = substr($formatted, 0, $first_nl - 0) . " |" . substr($formatted, $first_nl);
                }
                $result_parts->push($formatted);
            } else {
                $result_parts->push($formatted);
            }
            $idx += 1;
        }
        $compact_pipe = $in_procsub && (scalar(@{$cmds}) > 0) && $cmds->[0]->[0]->{kind} == "subshell";
        $result = "";
        $idx = 0;
        while ($idx < scalar(@{$result_parts})) {
            $part = $result_parts->[$idx];
            if ($idx > 0) {
                if ($result->endswith("\n")) {
                    $result = $result + "  " . $part;
                } elsif ($compact_pipe) {
                    $result = $result + "|" . $part;
                } else {
                    $result = $result + " | " . $part;
                }
            } else {
                $result = $part;
            }
            $idx += 1;
        }
        return $result;
    }
    if (ref($node) eq 'List') {
        my $node = $node;
        $has_heredoc = 0;
        for my $p (@{($node->{parts} // [])}) {
            if ($p->{kind} == "command" && (scalar(@{$p->{redirects}}) > 0)) {
                for my $r (@{($p->{redirects} // [])}) {
                    if (ref($r) eq 'HereDoc') {
                        my $r = $r;
                        $has_heredoc = 1;
                        last;
                    }
                }
            } else {
                if (ref($p) eq 'Pipeline') {
                    my $p = $p;
                    for my $cmd (@{($p->{commands} // [])}) {
                        if ($cmd->{kind} == "command" && (scalar(@{$cmd->{redirects}}) > 0)) {
                            for my $r (@{($cmd->{redirects} // [])}) {
                                if (ref($r) eq 'HereDoc') {
                                    my $r = $r;
                                    $has_heredoc = 1;
                                    last;
                                }
                            }
                        }
                        if ($has_heredoc) {
                            last;
                        }
                    }
                }
            }
        }
        $result = [];
        $skipped_semi = 0;
        $cmd_count = 0;
        for my $p (@{($node->{parts} // [])}) {
            if (ref($p) eq 'Operator') {
                my $p = $p;
                if ($p->{op} eq ";") {
                    if ((scalar(@{$result}) > 0) && $result->[-1]->endswith("\n")) {
                        $skipped_semi = 1;
                        next;
                    }
                    if (scalar(@{$result}) >= 3 && $result->[-2] eq "\n" && $result->[-3]->endswith("\n")) {
                        $skipped_semi = 1;
                        next;
                    }
                    $result->push(";");
                    $skipped_semi = 0;
                } elsif ($p->{op} eq "\n") {
                    if ((scalar(@{$result}) > 0) && $result->[-1] eq ";") {
                        $skipped_semi = 0;
                        next;
                    }
                    if ((scalar(@{$result}) > 0) && $result->[-1]->endswith("\n")) {
                        $result->push(($skipped_semi ? " " : "\n"));
                        $skipped_semi = 0;
                        next;
                    }
                    $result->push("\n");
                    $skipped_semi = 0;
                } elsif ($p->{op} eq "&") {
                    if ((scalar(@{$result}) > 0) && ((index($result->[-1], "<<") >= 0)) && ((index($result->[-1], "\n") >= 0))) {
                        $last_ = $result->[-1];
                        if (((index($last_, " |") >= 0)) || $last_->startswith("|")) {
                            $result->[-1] = $last_ . " &";
                        } else {
                            $first_nl = $last_->find("\n");
                            $result->[-1] = substr($last_, 0, $first_nl - 0) . " &" . substr($last_, $first_nl);
                        }
                    } else {
                        $result->push(" &");
                    }
                } elsif ((scalar(@{$result}) > 0) && ((index($result->[-1], "<<") >= 0)) && ((index($result->[-1], "\n") >= 0))) {
                    $last_ = $result->[-1];
                    $first_nl = $last_->find("\n");
                    $result->[-1] = substr($last_, 0, $first_nl - 0) . " " . $p->{op} . " " . substr($last_, $first_nl);
                } else {
                    $result->push(" " . $p->{op});
                }
            } else {
                if ((scalar(@{$result}) > 0) && !$result->[-1]->endswith([" ", "\n"])) {
                    $result->push(" ");
                }
                $formatted_cmd = format_cmdsub_node($p, $indent, $in_procsub, $compact_redirects, $procsub_first && $cmd_count == 0);
                if (scalar(@{$result}) > 0) {
                    $last_ = $result->[-1];
                    if (((index($last_, " || \n") >= 0)) || ((index($last_, " && \n") >= 0))) {
                        $formatted_cmd = " " . $formatted_cmd;
                    }
                }
                if ($skipped_semi) {
                    $formatted_cmd = " " . $formatted_cmd;
                    $skipped_semi = 0;
                }
                $result->push($formatted_cmd);
                $cmd_count += 1;
            }
        }
        $s_ = ""->join_($result);
        if (((index($s_, " &\n") >= 0)) && $s_->endswith("\n")) {
            return $s_ . " ";
        }
        while ($s_->endswith(";")) {
            $s_ = substring($s_, 0, length($s_) - 1);
        }
        if (!$has_heredoc) {
            while ($s_->endswith("\n")) {
                $s_ = substring($s_, 0, length($s_) - 1);
            }
        }
        return $s_;
    }
    if (ref($node) eq 'If') {
        my $node = $node;
        $cond = format_cmdsub_node($node->{condition}, $indent, 0, 0, 0);
        $then_body = format_cmdsub_node($node->{then_body}, $indent + 4, 0, 0, 0);
        $result = "if " . $cond . "; then\n" . $inner_sp . $then_body . ";";
        if (defined($node->{else_body})) {
            $else_body = format_cmdsub_node($node->{else_body}, $indent + 4, 0, 0, 0);
            $result = $result + "\n" . $sp . "else\n" . $inner_sp . $else_body . ";";
        }
        $result = $result + "\n" . $sp . "fi";
        return $result;
    }
    if (ref($node) eq 'While') {
        my $node = $node;
        $cond = format_cmdsub_node($node->{condition}, $indent, 0, 0, 0);
        $body = format_cmdsub_node($node->{body}, $indent + 4, 0, 0, 0);
        $result = "while " . $cond . "; do\n" . $inner_sp . $body . ";\n" . $sp . "done";
        if ((scalar(@{$node->{redirects}}) > 0)) {
            for my $r (@{($node->{redirects} // [])}) {
                $result = $result + " " . format_redirect($r, 0, 0);
            }
        }
        return $result;
    }
    if (ref($node) eq 'Until') {
        my $node = $node;
        $cond = format_cmdsub_node($node->{condition}, $indent, 0, 0, 0);
        $body = format_cmdsub_node($node->{body}, $indent + 4, 0, 0, 0);
        $result = "until " . $cond . "; do\n" . $inner_sp . $body . ";\n" . $sp . "done";
        if ((scalar(@{$node->{redirects}}) > 0)) {
            for my $r (@{($node->{redirects} // [])}) {
                $result = $result + " " . format_redirect($r, 0, 0);
            }
        }
        return $result;
    }
    if (ref($node) eq 'For') {
        my $node = $node;
        $var = $node->{var};
        $body = format_cmdsub_node($node->{body}, $indent + 4, 0, 0, 0);
        my $result = "";
        if (defined($node->{words})) {
            $word_vals = [];
            for my $w (@{($node->{words} // [])}) {
                $word_vals->push($w->{value});
            }
            $words = " "->join_($word_vals);
            if ((length($words) > 0)) {
                $result = "for " . $var . " in " . $words . ";\n" . $sp . "do\n" . $inner_sp . $body . ";\n" . $sp . "done";
            } else {
                $result = "for " . $var . " in ;\n" . $sp . "do\n" . $inner_sp . $body . ";\n" . $sp . "done";
            }
        } else {
            $result = "for " . $var . " in \"\$\@\";\n" . $sp . "do\n" . $inner_sp . $body . ";\n" . $sp . "done";
        }
        if ((scalar(@{$node->{redirects}}) > 0)) {
            for my $r (@{($node->{redirects} // [])}) {
                $result = $result + " " . format_redirect($r, 0, 0);
            }
        }
        return $result;
    }
    if (ref($node) eq 'ForArith') {
        my $node = $node;
        $body = format_cmdsub_node($node->{body}, $indent + 4, 0, 0, 0);
        $result = "for ((" . $node->{init} . "; " . $node->{cond} . "; " . $node->{incr} . "))\ndo\n" . $inner_sp . $body . ";\n" . $sp . "done";
        if ((scalar(@{$node->{redirects}}) > 0)) {
            for my $r (@{($node->{redirects} // [])}) {
                $result = $result + " " . format_redirect($r, 0, 0);
            }
        }
        return $result;
    }
    if (ref($node) eq 'Case') {
        my $node = $node;
        $word = $node->{word}->{value};
        $patterns = [];
        $i = 0;
        while ($i < scalar(@{$node->{patterns}})) {
            $p = $node->{patterns}->[$i];
            $pat = $p->{pattern}->replace("|", " | ");
            my $body = "";
            if (defined($p->{body})) {
                $body = format_cmdsub_node($p->{body}, $indent + 8, 0, 0, 0);
            } else {
                $body = "";
            }
            $term = $p->{terminator};
            $pat_indent = repeat_str(" ", $indent + 8);
            $term_indent = repeat_str(" ", $indent + 4);
            $body_part = ((length($body) > 0) ? $pat_indent . $body . "\n" : "\n");
            if ($i == 0) {
                $patterns->push(" " . $pat . ")\n" . $body_part + $term_indent . $term);
            } else {
                $patterns->push($pat . ")\n" . $body_part + $term_indent . $term);
            }
            $i += 1;
        }
        $pattern_str = ("\n" . repeat_str(" ", $indent + 4))->join_($patterns);
        $redirects = "";
        if ((scalar(@{$node->{redirects}}) > 0)) {
            $redirect_parts = [];
            for my $r (@{($node->{redirects} // [])}) {
                $redirect_parts->append(format_redirect($r, 0, 0));
            }
            $redirects = " " . " "->join_($redirect_parts);
        }
        return "case " . $word . " in" . $pattern_str + "\n" . $sp . "esac" . $redirects;
    }
    if (ref($node) eq 'Function') {
        my $node = $node;
        $name = $node->{name};
        $inner_body = ($node->{body}->{kind} == "brace-group" ? $node->{body}->{body} : $node->{body});
        $body = (format_cmdsub_node($inner_body, $indent + 4, 0, 0, 0) =~ s/[";"]+$//r);
        return sprintf("function %s () 
{ 
%s%s
}", $name, $inner_sp, $body);
    }
    if (ref($node) eq 'Subshell') {
        my $node = $node;
        $body = format_cmdsub_node($node->{body}, $indent, $in_procsub, $compact_redirects, 0);
        $redirects = "";
        if ((scalar(@{$node->{redirects}}) > 0)) {
            $redirect_parts = [];
            for my $r (@{($node->{redirects} // [])}) {
                $redirect_parts->append(format_redirect($r, 0, 0));
            }
            $redirects = " "->join_($redirect_parts);
        }
        if ($procsub_first) {
            if ((length($redirects) > 0)) {
                return "(" . $body . ") " . $redirects;
            }
            return "(" . $body . ")";
        }
        if ((length($redirects) > 0)) {
            return "( " . $body . " ) " . $redirects;
        }
        return "( " . $body . " )";
    }
    if (ref($node) eq 'BraceGroup') {
        my $node = $node;
        $body = format_cmdsub_node($node->{body}, $indent, 0, 0, 0);
        $body = ($body =~ s/[";"]+$//r);
        $terminator = ($body->endswith(" &") ? " }" : "; }");
        $redirects = "";
        if ((scalar(@{$node->{redirects}}) > 0)) {
            $redirect_parts = [];
            for my $r (@{($node->{redirects} // [])}) {
                $redirect_parts->append(format_redirect($r, 0, 0));
            }
            $redirects = " "->join_($redirect_parts);
        }
        if ((length($redirects) > 0)) {
            return "{ " . $body . $terminator + " " . $redirects;
        }
        return "{ " . $body . $terminator;
    }
    if (ref($node) eq 'ArithmeticCommand') {
        my $node = $node;
        return "((" . $node->{raw_content} . "))";
    }
    if (ref($node) eq 'ConditionalExpr') {
        my $node = $node;
        $body = format_cond_body($node->{body});
        return "[[ " . $body . " ]]";
    }
    if (ref($node) eq 'Negation') {
        my $node = $node;
        if (defined($node->{pipeline})) {
            return "! " . format_cmdsub_node($node->{pipeline}, $indent, 0, 0, 0);
        }
        return "! ";
    }
    if (ref($node) eq 'Time') {
        my $node = $node;
        $prefix = ($node->{posix} ? "time -p " : "time ");
        if (defined($node->{pipeline})) {
            return $prefix . format_cmdsub_node($node->{pipeline}, $indent, 0, 0, 0);
        }
        return $prefix;
    }
    return "";
}

sub format_redirect ($r, $compact, $heredoc_op_only) {
    my $after_amp;
    my $delim;
    my $is_literal_fd;
    my $op;
    my $was_input_close;
    if (ref($r) eq 'HereDoc') {
        my $r = $r;
        my $op = "";
        if ($r->{strip_tabs}) {
            $op = "<<-";
        } else {
            $op = "<<";
        }
        if (defined($r->{fd}) && $r->{fd} > 0) {
            $op = "$r->{fd}" . $op;
        }
        my $delim = "";
        if ($r->{quoted}) {
            $delim = "'" . $r->{delimiter} . "'";
        } else {
            $delim = $r->{delimiter};
        }
        if ($heredoc_op_only) {
            return $op . $delim;
        }
        return $op . $delim . "\n" . $r->{content} . $r->{delimiter} . "\n";
    }
    $op = $r->{op};
    if ($op eq "1>") {
        $op = ">";
    } elsif ($op eq "0<") {
        $op = "<";
    }
    my $target = $r->{target}->{value};
    $target = $r->{target}->expand_all_ansi_c_quotes($target);
    $target = $r->{target}->strip_locale_string_dollars($target);
    $target = $r->{target}->format_command_substitutions($target, 0);
    if ($target->startswith("&")) {
        $was_input_close = 0;
        if ($target eq "&-" && $op->endswith("<")) {
            $was_input_close = 1;
            $op = substring($op, 0, length($op) - 1) . ">";
        }
        $after_amp = substring($target, 1, length($target));
        $is_literal_fd = $after_amp eq "-" || length($after_amp) > 0 && ($after_amp->[0] =~ /^\d$/);
        if ($is_literal_fd) {
            if ($op eq ">" || $op eq ">&") {
                $op = ($was_input_close ? "0>" : "1>");
            } elsif ($op eq "<" || $op eq "<&") {
                $op = "0<";
            }
        } elsif ($op eq "1>") {
            $op = ">";
        } elsif ($op eq "0<") {
            $op = "<";
        }
        return $op . $target;
    }
    if ($op->endswith("&")) {
        return $op . $target;
    }
    if ($compact) {
        return $op . $target;
    }
    return $op . " " . $target;
}

sub format_heredoc_body ($r) {
    return "\n" . $r->{content} . $r->{delimiter} + "\n";
}

sub lookahead_for_esac ($value, $start, $case_depth) {
    my $c;
    my $i = $start;
    my $depth = $case_depth;
    my $quote = new_quote_state();
    while ($i < length($value)) {
        $c = $value->[$i];
        if ($c eq "\\" && $i + 1 < length($value) && $quote->{double}) {
            $i += 2;
            next;
        }
        if ($c eq "'" && !$quote->{double}) {
            $quote->{single} = !$quote->{single};
            $i += 1;
            next;
        }
        if ($c eq "\"" && !$quote->{single}) {
            $quote->{double} = !$quote->{double};
            $i += 1;
            next;
        }
        if ($quote->{single} || $quote->{double}) {
            $i += 1;
            next;
        }
        if (starts_with_at($value, $i, "case") && is_word_boundary($value, $i, 4)) {
            $depth += 1;
            $i += 4;
        } elsif (starts_with_at($value, $i, "esac") && is_word_boundary($value, $i, 4)) {
            $depth -= 1;
            if ($depth == 0) {
                return 1;
            }
            $i += 4;
        } elsif ($c eq "(") {
            $i += 1;
        } elsif ($c eq ")") {
            if ($depth > 0) {
                $i += 1;
            } else {
                last;
            }
        } else {
            $i += 1;
        }
    }
    return 0;
}

sub skip_backtick ($value, $start) {
    my $i = $start + 1;
    while ($i < length($value) && $value->[$i] ne "`") {
        if ($value->[$i] eq "\\" && $i + 1 < length($value)) {
            $i += 2;
        } else {
            $i += 1;
        }
    }
    if ($i < length($value)) {
        $i += 1;
    }
    return $i;
}

sub skip_single_quoted ($s_, $start) {
    my $i = $start;
    while ($i < length($s_) && $s_->[$i] ne "'") {
        $i += 1;
    }
    return ($i < length($s_) ? $i + 1 : $i);
}

sub skip_double_quoted ($s_, $start) {
    my $backq;
    my $c;
    my $i;
    my $pass_next;
    $i = $start;
    my $n = length($s_);
    $pass_next = 0;
    $backq = 0;
    while ($i < $n) {
        $c = $s_->[$i];
        if ($pass_next) {
            $pass_next = 0;
            $i += 1;
            next;
        }
        if ($c eq "\\") {
            $pass_next = 1;
            $i += 1;
            next;
        }
        if ($backq) {
            if ($c eq "`") {
                $backq = 0;
            }
            $i += 1;
            next;
        }
        if ($c eq "`") {
            $backq = 1;
            $i += 1;
            next;
        }
        if ($c eq "\$" && $i + 1 < $n) {
            if ($s_->[$i + 1] eq "(") {
                $i = find_cmdsub_end($s_, $i + 2);
                next;
            }
            if ($s_->[$i + 1] eq "{") {
                $i = find_braced_param_end($s_, $i + 2);
                next;
            }
        }
        if ($c eq "\"") {
            return $i + 1;
        }
        $i += 1;
    }
    return $i;
}

sub is_valid_arithmetic_start ($value, $start) {
    my $scan_c;
    my $scan_paren = 0;
    my $scan_i = $start + 3;
    while ($scan_i < length($value)) {
        $scan_c = $value->[$scan_i];
        if (is_expansion_start($value, $scan_i, "\$(")) {
            $scan_i = find_cmdsub_end($value, $scan_i + 2);
            next;
        }
        if ($scan_c eq "(") {
            $scan_paren += 1;
        } elsif ($scan_c eq ")") {
            if ($scan_paren > 0) {
                $scan_paren -= 1;
            } elsif ($scan_i + 1 < length($value) && $value->[$scan_i + 1] eq ")") {
                return 1;
            } else {
                return 0;
            }
        }
        $scan_i += 1;
    }
    return 0;
}

sub find_funsub_end ($value, $start) {
    my $c;
    my $depth = 1;
    my $i = $start;
    my $quote = new_quote_state();
    while ($i < length($value) && $depth > 0) {
        $c = $value->[$i];
        if ($c eq "\\" && $i + 1 < length($value) && !$quote->{single}) {
            $i += 2;
            next;
        }
        if ($c eq "'" && !$quote->{double}) {
            $quote->{single} = !$quote->{single};
            $i += 1;
            next;
        }
        if ($c eq "\"" && !$quote->{single}) {
            $quote->{double} = !$quote->{double};
            $i += 1;
            next;
        }
        if ($quote->{single} || $quote->{double}) {
            $i += 1;
            next;
        }
        if ($c eq "{") {
            $depth += 1;
        } elsif ($c eq "}") {
            $depth -= 1;
            if ($depth == 0) {
                return $i + 1;
            }
        }
        $i += 1;
    }
    return length($value);
}

sub find_cmdsub_end ($value, $start) {
    my $c;
    my $j;
    my $depth = 1;
    my $i = $start;
    my $case_depth = 0;
    my $in_case_patterns = 0;
    my $arith_depth = 0;
    my $arith_paren_depth = 0;
    while ($i < length($value) && $depth > 0) {
        $c = $value->[$i];
        if ($c eq "\\" && $i + 1 < length($value)) {
            $i += 2;
            next;
        }
        if ($c eq "'") {
            $i = skip_single_quoted($value, $i + 1);
            next;
        }
        if ($c eq "\"") {
            $i = skip_double_quoted($value, $i + 1);
            next;
        }
        if ($c eq "#" && $arith_depth == 0 && ($i == $start || $value->[$i - 1] eq " " || $value->[$i - 1] eq "\t" || $value->[$i - 1] eq "\n" || $value->[$i - 1] eq ";" || $value->[$i - 1] eq "|" || $value->[$i - 1] eq "&" || $value->[$i - 1] eq "(" || $value->[$i - 1] eq ")")) {
            while ($i < length($value) && $value->[$i] ne "\n") {
                $i += 1;
            }
            next;
        }
        if (starts_with_at($value, $i, "<<<")) {
            $i += 3;
            while ($i < length($value) && ($value->[$i] eq " " || $value->[$i] eq "\t")) {
                $i += 1;
            }
            if ($i < length($value) && $value->[$i] eq "\"") {
                $i += 1;
                while ($i < length($value) && $value->[$i] ne "\"") {
                    if ($value->[$i] eq "\\" && $i + 1 < length($value)) {
                        $i += 2;
                    } else {
                        $i += 1;
                    }
                }
                if ($i < length($value)) {
                    $i += 1;
                }
            } elsif ($i < length($value) && $value->[$i] eq "'") {
                $i += 1;
                while ($i < length($value) && $value->[$i] ne "'") {
                    $i += 1;
                }
                if ($i < length($value)) {
                    $i += 1;
                }
            } else {
                while ($i < length($value) && ((index(" \t\n;|&<>()", $value->[$i]) == -1))) {
                    $i += 1;
                }
            }
            next;
        }
        if (is_expansion_start($value, $i, "\$((")) {
            if (is_valid_arithmetic_start($value, $i)) {
                $arith_depth += 1;
                $i += 3;
                next;
            }
            $j = find_cmdsub_end($value, $i + 2);
            $i = $j;
            next;
        }
        if ($arith_depth > 0 && $arith_paren_depth == 0 && starts_with_at($value, $i, "))")) {
            $arith_depth -= 1;
            $i += 2;
            next;
        }
        if ($c eq "`") {
            $i = skip_backtick($value, $i);
            next;
        }
        if ($arith_depth == 0 && starts_with_at($value, $i, "<<")) {
            $i = skip_heredoc($value, $i);
            next;
        }
        if (starts_with_at($value, $i, "case") && is_word_boundary($value, $i, 4)) {
            $case_depth += 1;
            $in_case_patterns = 0;
            $i += 4;
            next;
        }
        if ($case_depth > 0 && starts_with_at($value, $i, "in") && is_word_boundary($value, $i, 2)) {
            $in_case_patterns = 1;
            $i += 2;
            next;
        }
        if (starts_with_at($value, $i, "esac") && is_word_boundary($value, $i, 4)) {
            if ($case_depth > 0) {
                $case_depth -= 1;
                $in_case_patterns = 0;
            }
            $i += 4;
            next;
        }
        if (starts_with_at($value, $i, ";;")) {
            $i += 2;
            next;
        }
        if ($c eq "(") {
            if (!($in_case_patterns && $case_depth > 0)) {
                if ($arith_depth > 0) {
                    $arith_paren_depth += 1;
                } else {
                    $depth += 1;
                }
            }
        } elsif ($c eq ")") {
            if ($in_case_patterns && $case_depth > 0) {
                if (!lookahead_for_esac($value, $i + 1, $case_depth)) {
                    $depth -= 1;
                }
            } elsif ($arith_depth > 0) {
                if ($arith_paren_depth > 0) {
                    $arith_paren_depth -= 1;
                }
            } else {
                $depth -= 1;
            }
        }
        $i += 1;
    }
    return $i;
}

sub find_braced_param_end ($value, $start) {
    my $c;
    my $end;
    my $depth = 1;
    my $i = $start;
    my $in_double = 0;
    my $dolbrace_state = DOLBRACESTATE_PARAM();
    while ($i < length($value) && $depth > 0) {
        $c = $value->[$i];
        if ($c eq "\\" && $i + 1 < length($value)) {
            $i += 2;
            next;
        }
        if ($c eq "'" && $dolbrace_state == DOLBRACESTATE_QUOTE() && !$in_double) {
            $i = skip_single_quoted($value, $i + 1);
            next;
        }
        if ($c eq "\"") {
            $in_double = !$in_double;
            $i += 1;
            next;
        }
        if ($in_double) {
            $i += 1;
            next;
        }
        if ($dolbrace_state == DOLBRACESTATE_PARAM() && ((index("%#^,", $c) >= 0))) {
            $dolbrace_state = DOLBRACESTATE_QUOTE();
        } elsif ($dolbrace_state == DOLBRACESTATE_PARAM() && ((index(":-=?+/", $c) >= 0))) {
            $dolbrace_state = DOLBRACESTATE_WORD();
        }
        if ($c eq "[" && $dolbrace_state == DOLBRACESTATE_PARAM() && !$in_double) {
            $end = skip_subscript($value, $i, 0);
            if ($end != -1) {
                $i = $end;
                next;
            }
        }
        if (($c eq "<" || $c eq ">") && $i + 1 < length($value) && $value->[$i + 1] eq "(") {
            $i = find_cmdsub_end($value, $i + 2);
            next;
        }
        if ($c eq "{") {
            $depth += 1;
        } elsif ($c eq "}") {
            $depth -= 1;
            if ($depth == 0) {
                return $i + 1;
            }
        }
        if (is_expansion_start($value, $i, "\$(")) {
            $i = find_cmdsub_end($value, $i + 2);
            next;
        }
        if (is_expansion_start($value, $i, "\${")) {
            $i = find_braced_param_end($value, $i + 2);
            next;
        }
        $i += 1;
    }
    return $i;
}

sub skip_heredoc ($value, $start) {
    my $c;
    my $delimiter;
    my $line;
    my $line_end;
    my $line_start;
    my $next_line_start;
    my $stripped;
    my $tabs_stripped;
    my $trailing_bs;
    my $i = $start + 2;
    if ($i < length($value) && $value->[$i] eq "-") {
        $i += 1;
    }
    while ($i < length($value) && is_whitespace_no_newline($value->[$i])) {
        $i += 1;
    }
    my $delim_start = $i;
    my $quote_char = undef;
    my $delimiter = "";
    if ($i < length($value) && ($value->[$i] eq "\"" || $value->[$i] eq "'")) {
        $quote_char = $value->[$i];
        $i += 1;
        $delim_start = $i;
        while ($i < length($value) && $value->[$i] ne $quote_char) {
            $i += 1;
        }
        $delimiter = substring($value, $delim_start, $i);
        if ($i < length($value)) {
            $i += 1;
        }
    } elsif ($i < length($value) && $value->[$i] eq "\\") {
        $i += 1;
        $delim_start = $i;
        if ($i < length($value)) {
            $i += 1;
        }
        while ($i < length($value) && !is_metachar($value->[$i])) {
            $i += 1;
        }
        $delimiter = substring($value, $delim_start, $i);
    } else {
        while ($i < length($value) && !is_metachar($value->[$i])) {
            $i += 1;
        }
        $delimiter = substring($value, $delim_start, $i);
    }
    my $paren_depth = 0;
    my $quote = new_quote_state();
    my $in_backtick = 0;
    while ($i < length($value) && $value->[$i] ne "\n") {
        $c = $value->[$i];
        if ($c eq "\\" && $i + 1 < length($value) && ($quote->{double} || $in_backtick)) {
            $i += 2;
            next;
        }
        if ($c eq "'" && !$quote->{double} && !$in_backtick) {
            $quote->{single} = !$quote->{single};
            $i += 1;
            next;
        }
        if ($c eq "\"" && !$quote->{single} && !$in_backtick) {
            $quote->{double} = !$quote->{double};
            $i += 1;
            next;
        }
        if ($c eq "`" && !$quote->{single}) {
            $in_backtick = !$in_backtick;
            $i += 1;
            next;
        }
        if ($quote->{single} || $quote->{double} || $in_backtick) {
            $i += 1;
            next;
        }
        if ($c eq "(") {
            $paren_depth += 1;
        } elsif ($c eq ")") {
            if ($paren_depth == 0) {
                last;
            }
            $paren_depth -= 1;
        }
        $i += 1;
    }
    if ($i < length($value) && $value->[$i] eq ")") {
        return $i;
    }
    if ($i < length($value) && $value->[$i] eq "\n") {
        $i += 1;
    }
    while ($i < length($value)) {
        $line_start = $i;
        $line_end = $i;
        while ($line_end < length($value) && $value->[$line_end] ne "\n") {
            $line_end += 1;
        }
        $line = substring($value, $line_start, $line_end);
        while ($line_end < length($value)) {
            $trailing_bs = 0;
            for (my $j = length($line) - 1; $j > -1; $j += -1) {
                if ($line->[$j] eq "\\") {
                    $trailing_bs += 1;
                } else {
                    last;
                }
            }
            if ($trailing_bs % 2 == 0) {
                last;
            }
            $line = substr($line, 0, length($line) - 1 - 0);
            $line_end += 1;
            $next_line_start = $line_end;
            while ($line_end < length($value) && $value->[$line_end] ne "\n") {
                $line_end += 1;
            }
            $line = $line . substring($value, $next_line_start, $line_end);
        }
        my $stripped = "";
        if ($start + 2 < length($value) && $value->[$start + 2] eq "-") {
            $stripped = ($line =~ s/^["\t"]+//r);
        } else {
            $stripped = $line;
        }
        if ($stripped eq $delimiter) {
            if ($line_end < length($value)) {
                return $line_end + 1;
            } else {
                return $line_end;
            }
        }
        if ($stripped->startswith($delimiter) && length($stripped) > length($delimiter)) {
            $tabs_stripped = length($line) - length($stripped);
            return $line_start + $tabs_stripped + length($delimiter);
        }
        if ($line_end < length($value)) {
            $i = $line_end + 1;
        } else {
            $i = $line_end;
        }
    }
    return $i;
}

sub find_heredoc_content_end ($source, $start, $delimiters) {
    my $delimiter;
    my $line;
    my $line_end;
    my $line_start;
    my $line_stripped;
    my $next_line_start;
    my $strip_tabs;
    my $tabs_stripped;
    my $trailing_bs;
    if (!(scalar(@{$delimiters}) > 0)) {
        return [$start, $start];
    }
    my $pos_ = $start;
    while ($pos_ < length($source) && $source->[$pos_] ne "\n") {
        $pos_ += 1;
    }
    if ($pos_ >= length($source)) {
        return [$start, $start];
    }
    my $content_start = $pos_;
    $pos_ += 1;
    for my $item (@{$delimiters}) {
        $delimiter = $item->[0];
        $strip_tabs = $item->[1];
        while ($pos_ < length($source)) {
            $line_start = $pos_;
            $line_end = $pos_;
            while ($line_end < length($source) && $source->[$line_end] ne "\n") {
                $line_end += 1;
            }
            $line = substring($source, $line_start, $line_end);
            while ($line_end < length($source)) {
                $trailing_bs = 0;
                for (my $j = length($line) - 1; $j > -1; $j += -1) {
                    if ($line->[$j] eq "\\") {
                        $trailing_bs += 1;
                    } else {
                        last;
                    }
                }
                if ($trailing_bs % 2 == 0) {
                    last;
                }
                $line = substr($line, 0, length($line) - 1 - 0);
                $line_end += 1;
                $next_line_start = $line_end;
                while ($line_end < length($source) && $source->[$line_end] ne "\n") {
                    $line_end += 1;
                }
                $line = $line . substring($source, $next_line_start, $line_end);
            }
            my $line_stripped = "";
            if ($strip_tabs) {
                $line_stripped = ($line =~ s/^["\t"]+//r);
            } else {
                $line_stripped = $line;
            }
            if ($line_stripped eq $delimiter) {
                $pos_ = ($line_end < length($source) ? $line_end + 1 : $line_end);
                last;
            }
            if ($line_stripped->startswith($delimiter) && length($line_stripped) > length($delimiter)) {
                $tabs_stripped = length($line) - length($line_stripped);
                $pos_ = $line_start + $tabs_stripped + length($delimiter);
                last;
            }
            $pos_ = ($line_end < length($source) ? $line_end + 1 : $line_end);
        }
    }
    return [$content_start, $pos_];
}

sub is_word_boundary ($s_, $pos_, $word_len) {
    my $prev;
    if ($pos_ > 0) {
        $prev = $s_->[$pos_ - 1];
        if (($prev =~ /^[a-zA-Z0-9]$/) || $prev eq "_") {
            return 0;
        }
        if ((index("{}!", $prev) >= 0)) {
            return 0;
        }
    }
    my $end = $pos_ + $word_len;
    if ($end < length($s_) && (($s_->[$end] =~ /^[a-zA-Z0-9]$/) || $s_->[$end] eq "_")) {
        return 0;
    }
    return 1;
}

sub is_quote ($c) {
    return $c eq "'" || $c eq "\"";
}

sub collapse_whitespace ($s_) {
    my $result = [];
    my $prev_was_ws = 0;
    for my $c (@{$s_}) {
        if ($c == " " || $c == "\t") {
            if (!$prev_was_ws) {
                $result->push(" ");
            }
            $prev_was_ws = 1;
        } else {
            $result->push($c);
            $prev_was_ws = 0;
        }
    }
    my $joined = ""->join_($result);
    return ($joined =~ s/^[" \t"]+|[" \t"]+$//gr);
}

sub count_trailing_backslashes ($s_) {
    my $count = 0;
    for (my $i = length($s_) - 1; $i > -1; $i += -1) {
        if ($s_->[$i] eq "\\") {
            $count += 1;
        } else {
            last;
        }
    }
    return $count;
}

sub normalize_heredoc_delimiter ($delimiter) {
    my $depth;
    my $inner;
    my $inner_str;
    my $result = [];
    my $i = 0;
    while ($i < length($delimiter)) {
        my $depth = 0;
        my $inner = undef;
        my $inner_str = "";
        if ($i + 1 < length($delimiter) && substr($delimiter, $i, $i + 2 - $i) eq "\$(") {
            $result->push("\$(");
            $i += 2;
            $depth = 1;
            $inner = [];
            while ($i < length($delimiter) && $depth > 0) {
                if ($delimiter->[$i] eq "(") {
                    $depth += 1;
                    $inner->push($delimiter->[$i]);
                } elsif ($delimiter->[$i] eq ")") {
                    $depth -= 1;
                    if ($depth == 0) {
                        $inner_str = ""->join_($inner);
                        $inner_str = collapse_whitespace($inner_str);
                        $result->push($inner_str);
                        $result->push(")");
                    } else {
                        $inner->push($delimiter->[$i]);
                    }
                } else {
                    $inner->push($delimiter->[$i]);
                }
                $i += 1;
            }
        } elsif ($i + 1 < length($delimiter) && substr($delimiter, $i, $i + 2 - $i) eq "\${") {
            $result->push("\${");
            $i += 2;
            $depth = 1;
            $inner = [];
            while ($i < length($delimiter) && $depth > 0) {
                if ($delimiter->[$i] eq "{") {
                    $depth += 1;
                    $inner->push($delimiter->[$i]);
                } elsif ($delimiter->[$i] eq "}") {
                    $depth -= 1;
                    if ($depth == 0) {
                        $inner_str = ""->join_($inner);
                        $inner_str = collapse_whitespace($inner_str);
                        $result->push($inner_str);
                        $result->push("}");
                    } else {
                        $inner->push($delimiter->[$i]);
                    }
                } else {
                    $inner->push($delimiter->[$i]);
                }
                $i += 1;
            }
        } elsif ($i + 1 < length($delimiter) && ((index("<>", $delimiter->[$i]) >= 0)) && $delimiter->[$i + 1] eq "(") {
            $result->push($delimiter->[$i]);
            $result->push("(");
            $i += 2;
            $depth = 1;
            $inner = [];
            while ($i < length($delimiter) && $depth > 0) {
                if ($delimiter->[$i] eq "(") {
                    $depth += 1;
                    $inner->push($delimiter->[$i]);
                } elsif ($delimiter->[$i] eq ")") {
                    $depth -= 1;
                    if ($depth == 0) {
                        $inner_str = ""->join_($inner);
                        $inner_str = collapse_whitespace($inner_str);
                        $result->push($inner_str);
                        $result->push(")");
                    } else {
                        $inner->push($delimiter->[$i]);
                    }
                } else {
                    $inner->push($delimiter->[$i]);
                }
                $i += 1;
            }
        } else {
            $result->push($delimiter->[$i]);
            $i += 1;
        }
    }
    return ""->join_($result);
}

sub is_metachar ($c) {
    return $c eq " " || $c eq "\t" || $c eq "\n" || $c eq "|" || $c eq "&" || $c eq ";" || $c eq "(" || $c eq ")" || $c eq "<" || $c eq ">";
}

sub is_funsub_char ($c) {
    return $c eq " " || $c eq "\t" || $c eq "\n" || $c eq "|";
}

sub is_extglob_prefix ($c) {
    return $c eq "\@" || $c eq "?" || $c eq "*" || $c eq "+" || $c eq "!";
}

sub is_redirect_char ($c) {
    return $c eq "<" || $c eq ">";
}

sub is_special_param ($c) {
    return $c eq "?" || $c eq "\$" || $c eq "!" || $c eq "#" || $c eq "\@" || $c eq "*" || $c eq "-" || $c eq "&";
}

sub is_special_param_unbraced ($c) {
    return $c eq "?" || $c eq "\$" || $c eq "!" || $c eq "#" || $c eq "\@" || $c eq "*" || $c eq "-";
}

sub is_digit ($c) {
    return $c ge "0" && $c le "9";
}

sub is_semicolon_or_newline ($c) {
    return $c eq ";" || $c eq "\n";
}

sub is_word_end_context ($c) {
    return $c eq " " || $c eq "\t" || $c eq "\n" || $c eq ";" || $c eq "|" || $c eq "&" || $c eq "<" || $c eq ">" || $c eq "(" || $c eq ")";
}

sub skip_matched_pair ($s_, $start, $open_, $close_, $flags) {
    my $c;
    my $i;
    my $literal;
    my $n = length($s_);
    my $i = 0;
    if (($flags & _SMP_PAST_OPEN() ? 1 : 0)) {
        $i = $start;
    } else {
        if ($start >= $n || $s_->[$start] ne $open_) {
            return -1;
        }
        $i = $start + 1;
    }
    my $depth = 1;
    my $pass_next = 0;
    my $backq = 0;
    while ($i < $n && $depth > 0) {
        $c = $s_->[$i];
        if ($pass_next) {
            $pass_next = 0;
            $i += 1;
            next;
        }
        $literal = $flags & _SMP_LITERAL();
        if (!($literal ? 1 : 0) && $c eq "\\") {
            $pass_next = 1;
            $i += 1;
            next;
        }
        if ($backq) {
            if ($c eq "`") {
                $backq = 0;
            }
            $i += 1;
            next;
        }
        if (!($literal ? 1 : 0) && $c eq "`") {
            $backq = 1;
            $i += 1;
            next;
        }
        if (!($literal ? 1 : 0) && $c eq "'") {
            $i = skip_single_quoted($s_, $i + 1);
            next;
        }
        if (!($literal ? 1 : 0) && $c eq "\"") {
            $i = skip_double_quoted($s_, $i + 1);
            next;
        }
        if (!($literal ? 1 : 0) && is_expansion_start($s_, $i, "\$(")) {
            $i = find_cmdsub_end($s_, $i + 2);
            next;
        }
        if (!($literal ? 1 : 0) && is_expansion_start($s_, $i, "\${")) {
            $i = find_braced_param_end($s_, $i + 2);
            next;
        }
        if (!($literal ? 1 : 0) && $c eq $open_) {
            $depth += 1;
        } elsif ($c eq $close_) {
            $depth -= 1;
        }
        $i += 1;
    }
    return ($depth == 0 ? $i : -1);
}

sub skip_subscript ($s_, $start, $flags) {
    return skip_matched_pair($s_, $start, "[", "]", $flags);
}

sub assignment ($s_, $flags) {
    my $c;
    my $end;
    my $sub_flags;
    if (!(length($s_) > 0)) {
        return -1;
    }
    if (!(($s_->[0] =~ /^[a-zA-Z]$/) || $s_->[0] eq "_")) {
        return -1;
    }
    my $i = 1;
    while ($i < length($s_)) {
        $c = $s_->[$i];
        if ($c eq "=") {
            return $i;
        }
        if ($c eq "[") {
            $sub_flags = (($flags & 2 ? 1 : 0) ? _SMP_LITERAL() : 0);
            $end = skip_subscript($s_, $i, $sub_flags);
            if ($end == -1) {
                return -1;
            }
            $i = $end;
            if ($i < length($s_) && $s_->[$i] eq "+") {
                $i += 1;
            }
            if ($i < length($s_) && $s_->[$i] eq "=") {
                return $i;
            }
            return -1;
        }
        if ($c eq "+") {
            if ($i + 1 < length($s_) && $s_->[$i + 1] eq "=") {
                return $i + 1;
            }
            return -1;
        }
        if (!(($c =~ /^[a-zA-Z0-9]$/) || $c eq "_")) {
            return -1;
        }
        $i += 1;
    }
    return -1;
}

sub is_array_assignment_prefix ($chars) {
    my $end;
    if (!(scalar(@{$chars}) > 0)) {
        return 0;
    }
    if (!(($chars->[0] =~ /^[a-zA-Z]$/) || $chars->[0] eq "_")) {
        return 0;
    }
    my $s_ = ""->join_($chars);
    my $i = 1;
    while ($i < length($s_) && (($s_->[$i] =~ /^[a-zA-Z0-9]$/) || $s_->[$i] eq "_")) {
        $i += 1;
    }
    while ($i < length($s_)) {
        if ($s_->[$i] ne "[") {
            return 0;
        }
        $end = skip_subscript($s_, $i, _SMP_LITERAL());
        if ($end == -1) {
            return 0;
        }
        $i = $end;
    }
    return 1;
}

sub is_special_param_or_digit ($c) {
    return is_special_param($c) || is_digit($c);
}

sub is_param_expansion_op ($c) {
    return $c eq ":" || $c eq "-" || $c eq "=" || $c eq "+" || $c eq "?" || $c eq "#" || $c eq "%" || $c eq "/" || $c eq "^" || $c eq "," || $c eq "\@" || $c eq "*" || $c eq "[";
}

sub is_simple_param_op ($c) {
    return $c eq "-" || $c eq "=" || $c eq "?" || $c eq "+";
}

sub is_escape_char_in_backtick ($c) {
    return $c eq "\$" || $c eq "`" || $c eq "\\";
}

sub is_negation_boundary ($c) {
    return is_whitespace($c) || $c eq ";" || $c eq "|" || $c eq ")" || $c eq "&" || $c eq ">" || $c eq "<";
}

sub is_backslash_escaped ($value, $idx) {
    my $bs_count = 0;
    my $j = $idx - 1;
    while ($j >= 0 && $value->[$j] eq "\\") {
        $bs_count += 1;
        $j -= 1;
    }
    return $bs_count % 2 == 1;
}

sub is_dollar_dollar_paren ($value, $idx) {
    my $dollar_count = 0;
    my $j = $idx - 1;
    while ($j >= 0 && $value->[$j] eq "\$") {
        $dollar_count += 1;
        $j -= 1;
    }
    return $dollar_count % 2 == 1;
}

sub is_paren ($c) {
    return $c eq "(" || $c eq ")";
}

sub is_caret_or_bang ($c) {
    return $c eq "!" || $c eq "^";
}

sub is_at_or_star ($c) {
    return $c eq "\@" || $c eq "*";
}

sub is_digit_or_dash ($c) {
    return is_digit($c) || $c eq "-";
}

sub is_newline_or_right_paren ($c) {
    return $c eq "\n" || $c eq ")";
}

sub is_semicolon_newline_brace ($c) {
    return $c eq ";" || $c eq "\n" || $c eq "{";
}

sub looks_like_assignment ($s_) {
    return assignment($s_, 0) != -1;
}

sub is_valid_identifier ($name) {
    if (!(length($name) > 0)) {
        return 0;
    }
    if (!(($name->[0] =~ /^[a-zA-Z]$/) || $name->[0] eq "_")) {
        return 0;
    }
    for my $c (@{substr($name, 1)}) {
        if (!(($c =~ /^[a-zA-Z0-9]$/) || $c == "_")) {
            return 0;
        }
    }
    return 1;
}

sub parse ($source, $extglob) {
    my $parser = new_parser($source, 0, $extglob);
    return $parser->parse();
}

sub new_parse_error ($message, $pos_, $line) {
    my $self = ParseError->new();
    $self->{message} = $message;
    $self->{pos_} = $pos_;
    $self->{line} = $line;
    return $self;
}

sub new_matched_pair_error ($message, $pos_, $line) {
    return MatchedPairError->new();
}

sub new_quote_state () {
    my $self = QuoteState->new();
    $self->{single} = 0;
    $self->{double} = 0;
    $self->{stack} = [];
    return $self;
}

sub new_parse_context ($kind) {
    my $self = ParseContext->new();
    $self->{kind} = $kind;
    $self->{paren_depth} = 0;
    $self->{brace_depth} = 0;
    $self->{bracket_depth} = 0;
    $self->{case_depth} = 0;
    $self->{arith_depth} = 0;
    $self->{arith_paren_depth} = 0;
    $self->{quote} = new_quote_state();
    return $self;
}

sub new_context_stack () {
    my $self = ContextStack->new();
    $self->{stack} = [new_parse_context(0)];
    return $self;
}

sub new_lexer ($source, $extglob) {
    my $self = Lexer->new();
    $self->{source} = $source;
    $self->{pos_} = 0;
    $self->{length_} = length($source);
    $self->{quote} = new_quote_state();
    $self->{token_cache} = undef;
    $self->{parser_state} = PARSERSTATEFLAGS_NONE();
    $self->{dolbrace_state} = DOLBRACESTATE_NONE();
    $self->{pending_heredocs} = [];
    $self->{extglob} = $extglob;
    $self->{parser} = undef;
    $self->{eof_token} = "";
    $self->{last_read_token} = undef;
    $self->{word_context} = WORD_CTX_NORMAL();
    $self->{at_command_start} = 0;
    $self->{in_array_literal} = 0;
    $self->{in_assign_builtin} = 0;
    $self->{post_read_pos} = 0;
    $self->{cached_word_context} = WORD_CTX_NORMAL();
    $self->{cached_at_command_start} = 0;
    $self->{cached_in_array_literal} = 0;
    $self->{cached_in_assign_builtin} = 0;
    return $self;
}

sub new_parser ($source, $in_process_sub, $extglob) {
    my $self = Parser->new();
    $self->{source} = $source;
    $self->{pos_} = 0;
    $self->{length_} = length($source);
    $self->{pending_heredocs} = [];
    $self->{cmdsub_heredoc_end} = -1;
    $self->{saw_newline_in_single_quote} = 0;
    $self->{in_process_sub} = $in_process_sub;
    $self->{extglob} = $extglob;
    $self->{ctx} = new_context_stack();
    $self->{lexer} = new_lexer($source, $extglob);
    $self->{lexer}->{parser} = $self;
    $self->{token_history} = [undef, undef, undef, undef];
    $self->{parser_state} = PARSERSTATEFLAGS_NONE();
    $self->{dolbrace_state} = DOLBRACESTATE_NONE();
    $self->{eof_token} = "";
    $self->{word_context} = WORD_CTX_NORMAL();
    $self->{at_command_start} = 0;
    $self->{in_array_literal} = 0;
    $self->{in_assign_builtin} = 0;
    $self->{arith_src} = "";
    $self->{arith_pos} = 0;
    $self->{arith_len} = 0;
    return $self;
}
