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

sub new ($class, $message=undef, $pos_=undef, $line=undef) {
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

sub new ($class, $type=undef, $value=undef, $pos_=undef, $parts=undef, $word=undef) {
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
    if ((scalar(@{($self->{parts} // [])}) > 0)) {
        return sprintf("Token(%s, %s, %s, parts=%s)", $self->{type}, $self->{value}, $self->{pos_}, scalar(@{$self->{parts}}));
    }
    return sprintf("Token(%s, %s, %s)", $self->{type}, $self->{value}, $self->{pos_});
}

1;




package SavedParserState;

sub new ($class, $parser_state=undef, $dolbrace_state=undef, $pending_heredocs=undef, $ctx_stack=undef, $eof_token=undef) {
    return bless { parser_state => $parser_state, dolbrace_state => $dolbrace_state, pending_heredocs => $pending_heredocs, ctx_stack => $ctx_stack, eof_token => $eof_token }, $class;
}

sub parser_state ($self) { $self->{parser_state} }
sub dolbrace_state ($self) { $self->{dolbrace_state} }
sub pending_heredocs ($self) { $self->{pending_heredocs} }
sub ctx_stack ($self) { $self->{ctx_stack} }
sub eof_token ($self) { $self->{eof_token} }

1;

package QuoteState;

sub new ($class, $single=undef, $double=undef, $stack=undef) {
    return bless { single => $single, double => $double, stack => $stack }, $class;
}

sub single ($self) { $self->{single} }
sub double ($self) { $self->{double} }
sub stack ($self) { $self->{stack} }

sub push_ ($self) {
    push(@{$self->{stack}}, [$self->{single}, $self->{double}]);
    $self->{single} = 0;
    $self->{double} = 0;
}

sub pop_ ($self) {
    if ((scalar(@{($self->{stack} // [])}) > 0)) {
        ($self->{single}, $self->{double}) = @{pop(@{$self->{stack}})};
    }
}

sub in_quotes ($self) {
    return $self->{single} || $self->{double};
}

sub copy ($self) {
    my $qs = main::new_quote_state();
    $qs->{single} = $self->{single};
    $qs->{double} = $self->{double};
    $qs->{stack} = [@{$self->{stack}}];
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

sub new ($class, $kind=undef, $paren_depth=undef, $brace_depth=undef, $bracket_depth=undef, $case_depth=undef, $arith_depth=undef, $arith_paren_depth=undef, $quote=undef) {
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
    my $ctx = main::new_parse_context($self->{kind});
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

sub new ($class, $stack=undef) {
    return bless { stack => $stack }, $class;
}

sub stack ($self) { $self->{stack} }

sub get_current ($self) {
    return $self->{stack}->[-1];
}

sub push_ ($self, $kind) {
    push(@{$self->{stack}}, main::new_parse_context($kind));
}

sub pop_ ($self) {
    if (scalar(@{$self->{stack}}) > 1) {
        return pop(@{$self->{stack}});
    }
    return $self->{stack}->[0];
}

sub copy_stack ($self) {
    my $result = [];
    for my $ctx (@{($self->{stack} // [])}) {
        push(@{$result}, $ctx->copy());
    }
    return $result;
}

sub restore_from ($self, $saved_stack) {
    my $result = [];
    for my $ctx (@{$saved_stack}) {
        push(@{$result}, $ctx->copy());
    }
    $self->{stack} = $result;
}

1;

package Lexer;

sub new ($class, $reserved_words=undef, $source=undef, $pos_=undef, $length_=undef, $quote=undef, $token_cache=undef, $parser_state=undef, $dolbrace_state=undef, $pending_heredocs=undef, $extglob=undef, $parser=undef, $eof_token=undef, $last_read_token=undef, $word_context=undef, $at_command_start=undef, $in_array_literal=undef, $in_assign_builtin=undef, $post_read_pos=undef, $cached_word_context=undef, $cached_at_command_start=undef, $cached_in_array_literal=undef, $cached_in_assign_builtin=undef) {
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
    return substr($self->{source}, $self->{pos_}, 1);
}

sub advance ($self) {
    if ($self->{pos_} >= $self->{length_}) {
        return "";
    }
    my $c = substr($self->{source}, $self->{pos_}, 1);
    $self->{pos_} += 1;
    return $c;
}

sub at_end ($self) {
    return $self->{pos_} >= $self->{length_};
}

sub lookahead ($self, $n) {
    return main::substring($self->{source}, $self->{pos_}, $self->{pos_} + $n);
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
        return Token->new(main::TOKENTYPE_SEMI_SEMI_AMP(), $three, $start, undef, undef);
    }
    if ($three eq "<<-") {
        $self->{pos_} += 3;
        return Token->new(main::TOKENTYPE_LESS_LESS_MINUS(), $three, $start, undef, undef);
    }
    if ($three eq "<<<") {
        $self->{pos_} += 3;
        return Token->new(main::TOKENTYPE_LESS_LESS_LESS(), $three, $start, undef, undef);
    }
    if ($three eq "&>>") {
        $self->{pos_} += 3;
        return Token->new(main::TOKENTYPE_AMP_GREATER_GREATER(), $three, $start, undef, undef);
    }
    if ($two eq "&&") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_AND_AND(), $two, $start, undef, undef);
    }
    if ($two eq "||") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_OR_OR(), $two, $start, undef, undef);
    }
    if ($two eq ";;") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_SEMI_SEMI(), $two, $start, undef, undef);
    }
    if ($two eq ";&") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_SEMI_AMP(), $two, $start, undef, undef);
    }
    if ($two eq "<<") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_LESS_LESS(), $two, $start, undef, undef);
    }
    if ($two eq ">>") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_GREATER_GREATER(), $two, $start, undef, undef);
    }
    if ($two eq "<&") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_LESS_AMP(), $two, $start, undef, undef);
    }
    if ($two eq ">&") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_GREATER_AMP(), $two, $start, undef, undef);
    }
    if ($two eq "<>") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_LESS_GREATER(), $two, $start, undef, undef);
    }
    if ($two eq ">|") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_GREATER_PIPE(), $two, $start, undef, undef);
    }
    if ($two eq "&>") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_AMP_GREATER(), $two, $start, undef, undef);
    }
    if ($two eq "|&") {
        $self->{pos_} += 2;
        return Token->new(main::TOKENTYPE_PIPE_AMP(), $two, $start, undef, undef);
    }
    if ($c eq ";") {
        $self->{pos_} += 1;
        return Token->new(main::TOKENTYPE_SEMI(), $c, $start, undef, undef);
    }
    if ($c eq "|") {
        $self->{pos_} += 1;
        return Token->new(main::TOKENTYPE_PIPE(), $c, $start, undef, undef);
    }
    if ($c eq "&") {
        $self->{pos_} += 1;
        return Token->new(main::TOKENTYPE_AMP(), $c, $start, undef, undef);
    }
    if ($c eq "(") {
        if ($self->{word_context} == main::WORD_CTX_REGEX()) {
            return undef;
        }
        $self->{pos_} += 1;
        return Token->new(main::TOKENTYPE_LPAREN(), $c, $start, undef, undef);
    }
    if ($c eq ")") {
        if ($self->{word_context} == main::WORD_CTX_REGEX()) {
            return undef;
        }
        $self->{pos_} += 1;
        return Token->new(main::TOKENTYPE_RPAREN(), $c, $start, undef, undef);
    }
    if ($c eq "<") {
        if ($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
            return undef;
        }
        $self->{pos_} += 1;
        return Token->new(main::TOKENTYPE_LESS(), $c, $start, undef, undef);
    }
    if ($c eq ">") {
        if ($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
            return undef;
        }
        $self->{pos_} += 1;
        return Token->new(main::TOKENTYPE_GREATER(), $c, $start, undef, undef);
    }
    if ($c eq "\n") {
        $self->{pos_} += 1;
        return Token->new(main::TOKENTYPE_NEWLINE(), $c, $start, undef, undef);
    }
    return undef;
}

sub skip_blanks ($self) {
    my $c;
    while ($self->{pos_} < $self->{length_}) {
        $c = substr($self->{source}, $self->{pos_}, 1);
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
    if (substr($self->{source}, $self->{pos_}, 1) ne "#") {
        return 0;
    }
    if ($self->{quote}->in_quotes()) {
        return 0;
    }
    if ($self->{pos_} > 0) {
        $prev = substr($self->{source}, $self->{pos_} - 1, 1);
        if ((index(" \t\n;|&(){}", $prev) == -1)) {
            return 0;
        }
    }
    while ($self->{pos_} < $self->{length_} && substr($self->{source}, $self->{pos_}, 1) ne "\n") {
        $self->{pos_} += 1;
    }
    return 1;
}

sub read_single_quote ($self, $start) {
    my $c;
    my $chars = ["'"];
    my $saw_newline = 0;
    while ($self->{pos_} < $self->{length_}) {
        $c = substr($self->{source}, $self->{pos_}, 1);
        if ($c eq "\n") {
            $saw_newline = 1;
        }
        push(@{$chars}, $c);
        $self->{pos_} += 1;
        if ($c eq "'") {
            return [join("", @{$chars}), $saw_newline];
        }
    }
    die "Unterminated single quote";
}

sub is_word_terminator ($self, $ctx, $ch, $bracket_depth, $paren_depth) {
    if ($ctx == main::WORD_CTX_REGEX()) {
        if ($ch eq "]" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "]") {
            return 1;
        }
        if ($ch eq "&" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "&") {
            return 1;
        }
        if ($ch eq ")" && $paren_depth == 0) {
            return 1;
        }
        return main::is_whitespace($ch) && $paren_depth == 0;
    }
    if ($ctx == main::WORD_CTX_COND()) {
        if ($ch eq "]" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "]") {
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
        if (main::is_redirect_char($ch) && !($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(")) {
            return 1;
        }
        return main::is_whitespace($ch);
    }
    if (($self->{parser_state} & main::PARSERSTATEFLAGS_PST_EOFTOKEN() ? 1 : 0) && $self->{eof_token} ne "" && $ch eq $self->{eof_token} && $bracket_depth == 0) {
        return 1;
    }
    if (main::is_redirect_char($ch) && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
        return 0;
    }
    return main::is_metachar($ch) && $bracket_depth == 0;
}

sub read_bracket_expression ($self, $chars, $parts, $for_regex, $paren_depth) {
    my $bracket_will_close;
    my $c;
    my $next_ch;
    my $sc;
    my $scan;
    if ($for_regex) {
        $scan = $self->{pos_} + 1;
        if ($scan < $self->{length_} && substr($self->{source}, $scan, 1) eq "^") {
            $scan += 1;
        }
        if ($scan < $self->{length_} && substr($self->{source}, $scan, 1) eq "]") {
            $scan += 1;
        }
        $bracket_will_close = 0;
        while ($scan < $self->{length_}) {
            $sc = substr($self->{source}, $scan, 1);
            if ($sc eq "]" && $scan + 1 < $self->{length_} && substr($self->{source}, $scan + 1, 1) eq "]") {
                last;
            }
            if ($sc eq ")" && $paren_depth > 0) {
                last;
            }
            if ($sc eq "&" && $scan + 1 < $self->{length_} && substr($self->{source}, $scan + 1, 1) eq "&") {
                last;
            }
            if ($sc eq "]") {
                $bracket_will_close = 1;
                last;
            }
            if ($sc eq "[" && $scan + 1 < $self->{length_} && substr($self->{source}, $scan + 1, 1) eq ":") {
                $scan += 2;
                while ($scan < $self->{length_} && !(substr($self->{source}, $scan, 1) eq ":" && $scan + 1 < $self->{length_} && substr($self->{source}, $scan + 1, 1) eq "]")) {
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
        $next_ch = substr($self->{source}, $self->{pos_} + 1, 1);
        if (main::is_whitespace_no_newline($next_ch) || $next_ch eq "&" || $next_ch eq "|") {
            return 0;
        }
    }
    push(@{$chars}, $self->advance());
    if (!$self->at_end() && $self->peek() eq "^") {
        push(@{$chars}, $self->advance());
    }
    if (!$self->at_end() && $self->peek() eq "]") {
        push(@{$chars}, $self->advance());
    }
    while (!$self->at_end()) {
        $c = $self->peek();
        if ($c eq "]") {
            push(@{$chars}, $self->advance());
            last;
        }
        if ($c eq "[" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq ":") {
            push(@{$chars}, $self->advance());
            push(@{$chars}, $self->advance());
            while (!$self->at_end() && !($self->peek() eq ":" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "]")) {
                push(@{$chars}, $self->advance());
            }
            if (!$self->at_end()) {
                push(@{$chars}, $self->advance());
                push(@{$chars}, $self->advance());
            }
        } elsif (!$for_regex && $c eq "[" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "=") {
            push(@{$chars}, $self->advance());
            push(@{$chars}, $self->advance());
            while (!$self->at_end() && !($self->peek() eq "=" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "]")) {
                push(@{$chars}, $self->advance());
            }
            if (!$self->at_end()) {
                push(@{$chars}, $self->advance());
                push(@{$chars}, $self->advance());
            }
        } elsif (!$for_regex && $c eq "[" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq ".") {
            push(@{$chars}, $self->advance());
            push(@{$chars}, $self->advance());
            while (!$self->at_end() && !($self->peek() eq "." && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "]")) {
                push(@{$chars}, $self->advance());
            }
            if (!$self->at_end()) {
                push(@{$chars}, $self->advance());
                push(@{$chars}, $self->advance());
            }
        } elsif ($for_regex && $c eq "\$") {
            $self->sync_to_parser();
            if (!$self->{parser}->parse_dollar_expansion($chars, $parts, 0)) {
                $self->sync_from_parser();
                push(@{$chars}, $self->advance());
            } else {
                $self->sync_from_parser();
            }
        } else {
            push(@{$chars}, $self->advance());
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
        if (($flags & main::MATCHEDPAIRFLAGS_DOLBRACE() ? 1 : 0) && $self->{dolbrace_state} == main::DOLBRACESTATE_OP()) {
            if ((index("#%^,~:-=?+/", $ch) == -1)) {
                $self->{dolbrace_state} = main::DOLBRACESTATE_WORD();
            }
        }
        if ($pass_next) {
            $pass_next = 0;
            push(@{$chars}, $ch);
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
            if ($ch eq "\\" && ($flags & main::MATCHEDPAIRFLAGS_ALLOWESC() ? 1 : 0)) {
                $pass_next = 1;
            }
            push(@{$chars}, $ch);
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
            push(@{$chars}, $ch);
            $was_dollar = 0;
            $was_gtlt = 0;
            next;
        }
        if ($ch eq $close_char) {
            $count -= 1;
            if ($count == 0) {
                last;
            }
            push(@{$chars}, $ch);
            $was_dollar = 0;
            $was_gtlt = (index("<>", $ch) >= 0);
            next;
        }
        if ($ch eq $open_char && $open_char ne $close_char) {
            if (!(($flags & main::MATCHEDPAIRFLAGS_DOLBRACE() ? 1 : 0) && $open_char eq "{")) {
                $count += 1;
            }
            push(@{$chars}, $ch);
            $was_dollar = 0;
            $was_gtlt = (index("<>", $ch) >= 0);
            next;
        }
        if (((index("'\"`", $ch) >= 0)) && $open_char ne $close_char) {
            my $nested = "";
            if ($ch eq "'") {
                push(@{$chars}, $ch);
                $quote_flags = ($was_dollar ? $flags | main::MATCHEDPAIRFLAGS_ALLOWESC() : $flags);
                $nested = $self->parse_matched_pair("'", "'", $quote_flags, 0);
                push(@{$chars}, $nested);
                push(@{$chars}, "'");
                $was_dollar = 0;
                $was_gtlt = 0;
                next;
            } elsif ($ch eq "\"") {
                push(@{$chars}, $ch);
                $nested = $self->parse_matched_pair("\"", "\"", $flags | main::MATCHEDPAIRFLAGS_DQUOTE(), 0);
                push(@{$chars}, $nested);
                push(@{$chars}, "\"");
                $was_dollar = 0;
                $was_gtlt = 0;
                next;
            } elsif ($ch eq "`") {
                push(@{$chars}, $ch);
                $nested = $self->parse_matched_pair("`", "`", $flags, 0);
                push(@{$chars}, $nested);
                push(@{$chars}, "`");
                $was_dollar = 0;
                $was_gtlt = 0;
                next;
            }
        }
        if ($ch eq "\$" && !$self->at_end() && !($flags & main::MATCHEDPAIRFLAGS_EXTGLOB() ? 1 : 0)) {
            $next_ch = $self->peek();
            if ($was_dollar) {
                push(@{$chars}, $ch);
                $was_dollar = 0;
                $was_gtlt = 0;
                next;
            }
            if ($next_ch eq "{") {
                if (($flags & main::MATCHEDPAIRFLAGS_ARITH() ? 1 : 0)) {
                    $after_brace_pos = $self->{pos_} + 1;
                    if ($after_brace_pos >= $self->{length_} || !main::is_funsub_char(substr($self->{source}, $after_brace_pos, 1))) {
                        push(@{$chars}, $ch);
                        $was_dollar = 1;
                        $was_gtlt = 0;
                        next;
                    }
                }
                $self->{pos_} -= 1;
                $self->sync_to_parser();
                $in_dquote = ($flags & main::MATCHEDPAIRFLAGS_DQUOTE()) != 0;
                ($param_node, $param_text) = @{$self->{parser}->parse_param_expansion($in_dquote)};
                $self->sync_from_parser();
                if (defined($param_node)) {
                    push(@{$chars}, $param_text);
                    $was_dollar = 0;
                    $was_gtlt = 0;
                } else {
                    push(@{$chars}, $self->advance());
                    $was_dollar = 1;
                    $was_gtlt = 0;
                }
                next;
            } elsif ($next_ch eq "(") {
                $self->{pos_} -= 1;
                $self->sync_to_parser();
                my $cmd_node = undef;
                my $cmd_text = "";
                if ($self->{pos_} + 2 < $self->{length_} && substr($self->{source}, $self->{pos_} + 2, 1) eq "(") {
                    ($arith_node, $arith_text) = @{$self->{parser}->parse_arithmetic_expansion()};
                    $self->sync_from_parser();
                    if (defined($arith_node)) {
                        push(@{$chars}, $arith_text);
                        $was_dollar = 0;
                        $was_gtlt = 0;
                    } else {
                        $self->sync_to_parser();
                        ($cmd_node, $cmd_text) = @{$self->{parser}->parse_command_substitution()};
                        $self->sync_from_parser();
                        if (defined($cmd_node)) {
                            push(@{$chars}, $cmd_text);
                            $was_dollar = 0;
                            $was_gtlt = 0;
                        } else {
                            push(@{$chars}, $self->advance());
                            push(@{$chars}, $self->advance());
                            $was_dollar = 0;
                            $was_gtlt = 0;
                        }
                    }
                } else {
                    ($cmd_node, $cmd_text) = @{$self->{parser}->parse_command_substitution()};
                    $self->sync_from_parser();
                    if (defined($cmd_node)) {
                        push(@{$chars}, $cmd_text);
                        $was_dollar = 0;
                        $was_gtlt = 0;
                    } else {
                        push(@{$chars}, $self->advance());
                        push(@{$chars}, $self->advance());
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
                    push(@{$chars}, $arith_text);
                    $was_dollar = 0;
                    $was_gtlt = 0;
                } else {
                    push(@{$chars}, $self->advance());
                    $was_dollar = 1;
                    $was_gtlt = 0;
                }
                next;
            }
        }
        if ($ch eq "(" && $was_gtlt && ($flags & main::MATCHEDPAIRFLAGS_DOLBRACE() | main::MATCHEDPAIRFLAGS_ARRAYSUB() ? 1 : 0)) {
            $direction = $chars->[-1];
            $chars = [@{$chars}[0 .. scalar(@{$chars}) - 1 - 1]];
            $self->{pos_} -= 1;
            $self->sync_to_parser();
            ($procsub_node, $procsub_text) = @{$self->{parser}->parse_process_substitution()};
            $self->sync_from_parser();
            if (defined($procsub_node)) {
                push(@{$chars}, $procsub_text);
                $was_dollar = 0;
                $was_gtlt = 0;
            } else {
                push(@{$chars}, $direction);
                push(@{$chars}, $self->advance());
                $was_dollar = 0;
                $was_gtlt = 0;
            }
            next;
        }
        push(@{$chars}, $ch);
        $was_dollar = $ch eq "\$";
        $was_gtlt = (index("<>", $ch) >= 0);
    }
    return join("", @{$chars});
}

sub collect_param_argument ($self, $flags, $was_dollar) {
    return $self->parse_matched_pair("{", "}", $flags | main::MATCHEDPAIRFLAGS_DOLBRACE(), $was_dollar);
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
        if ($ctx == main::WORD_CTX_REGEX()) {
            if ($ch eq "\\" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "\n") {
                $self->advance();
                $self->advance();
                next;
            }
        }
        if ($ctx != main::WORD_CTX_NORMAL() && $self->is_word_terminator($ctx, $ch, $bracket_depth, $paren_depth)) {
            last;
        }
        if ($ctx == main::WORD_CTX_NORMAL() && $ch eq "[") {
            if ($bracket_depth > 0) {
                $bracket_depth += 1;
                push(@{$chars}, $self->advance());
                next;
            }
            if ((scalar(@{($chars // [])}) > 0) && $at_command_start && !$seen_equals && main::is_array_assignment_prefix($chars)) {
                $prev_char = $chars->[-1];
                if (($prev_char =~ /^[a-zA-Z0-9]$/) || $prev_char eq "_") {
                    $bracket_start_pos = $self->{pos_};
                    $bracket_depth += 1;
                    push(@{$chars}, $self->advance());
                    next;
                }
            }
            if (!(scalar(@{($chars // [])}) > 0) && !$seen_equals && $in_array_literal) {
                $bracket_start_pos = $self->{pos_};
                $bracket_depth += 1;
                push(@{$chars}, $self->advance());
                next;
            }
        }
        if ($ctx == main::WORD_CTX_NORMAL() && $ch eq "]" && $bracket_depth > 0) {
            $bracket_depth -= 1;
            push(@{$chars}, $self->advance());
            next;
        }
        if ($ctx == main::WORD_CTX_NORMAL() && $ch eq "=" && $bracket_depth == 0) {
            $seen_equals = 1;
        }
        if ($ctx == main::WORD_CTX_REGEX() && $ch eq "(") {
            $paren_depth += 1;
            push(@{$chars}, $self->advance());
            next;
        }
        if ($ctx == main::WORD_CTX_REGEX() && $ch eq ")") {
            if ($paren_depth > 0) {
                $paren_depth -= 1;
                push(@{$chars}, $self->advance());
                next;
            }
            last;
        }
        if (($ctx == main::WORD_CTX_COND() || $ctx == main::WORD_CTX_REGEX()) && $ch eq "[") {
            $for_regex = $ctx == main::WORD_CTX_REGEX();
            if ($self->read_bracket_expression($chars, $parts, $for_regex, $paren_depth)) {
                next;
            }
            push(@{$chars}, $self->advance());
            next;
        }
        my $content = "";
        if ($ctx == main::WORD_CTX_COND() && $ch eq "(") {
            if ($self->{extglob} && (scalar(@{($chars // [])}) > 0) && main::is_extglob_prefix($chars->[-1])) {
                push(@{$chars}, $self->advance());
                $content = $self->parse_matched_pair("(", ")", main::MATCHEDPAIRFLAGS_EXTGLOB(), 0);
                push(@{$chars}, $content);
                push(@{$chars}, ")");
                next;
            } else {
                last;
            }
        }
        if ($ctx == main::WORD_CTX_REGEX() && main::is_whitespace($ch) && $paren_depth > 0) {
            push(@{$chars}, $self->advance());
            next;
        }
        if ($ch eq "'") {
            $self->advance();
            $track_newline = $ctx == main::WORD_CTX_NORMAL();
            ($content, $saw_newline) = @{$self->read_single_quote($start)};
            push(@{$chars}, $content);
            if ($track_newline && $saw_newline && defined($self->{parser})) {
                $self->{parser}->{saw_newline_in_single_quote} = 1;
            }
            next;
        }
        my $cmdsub_result0 = undef;
        my $cmdsub_result1 = "";
        if ($ch eq "\"") {
            $self->advance();
            if ($ctx == main::WORD_CTX_NORMAL()) {
                push(@{$chars}, "\"");
                $in_single_in_dquote = 0;
                while (!$self->at_end() && ($in_single_in_dquote || $self->peek() ne "\"")) {
                    $c = $self->peek();
                    if ($in_single_in_dquote) {
                        push(@{$chars}, $self->advance());
                        if ($c eq "'") {
                            $in_single_in_dquote = 0;
                        }
                        next;
                    }
                    if ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        $next_c = substr($self->{source}, $self->{pos_} + 1, 1);
                        if ($next_c eq "\n") {
                            $self->advance();
                            $self->advance();
                        } else {
                            push(@{$chars}, $self->advance());
                            push(@{$chars}, $self->advance());
                        }
                    } elsif ($c eq "\$") {
                        $self->sync_to_parser();
                        if (!$self->{parser}->parse_dollar_expansion($chars, $parts, 1)) {
                            $self->sync_from_parser();
                            push(@{$chars}, $self->advance());
                        } else {
                            $self->sync_from_parser();
                        }
                    } elsif ($c eq "`") {
                        $self->sync_to_parser();
                        ($cmdsub_result0, $cmdsub_result1) = @{$self->{parser}->parse_backtick_substitution()};
                        $self->sync_from_parser();
                        if (defined($cmdsub_result0)) {
                            push(@{$parts}, $cmdsub_result0);
                            push(@{$chars}, $cmdsub_result1);
                        } else {
                            push(@{$chars}, $self->advance());
                        }
                    } else {
                        push(@{$chars}, $self->advance());
                    }
                }
                if ($self->at_end()) {
                    die "Unterminated double quote";
                }
                push(@{$chars}, $self->advance());
            } else {
                $handle_line_continuation = $ctx == main::WORD_CTX_COND();
                $self->sync_to_parser();
                $self->{parser}->scan_double_quote($chars, $parts, $start, $handle_line_continuation);
                $self->sync_from_parser();
            }
            next;
        }
        if ($ch eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $next_ch = substr($self->{source}, $self->{pos_} + 1, 1);
            if ($ctx != main::WORD_CTX_REGEX() && $next_ch eq "\n") {
                $self->advance();
                $self->advance();
            } else {
                push(@{$chars}, $self->advance());
                push(@{$chars}, $self->advance());
            }
            next;
        }
        if ($ctx != main::WORD_CTX_REGEX() && $ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "'") {
            ($ansi_result0, $ansi_result1) = @{$self->read_ansi_c_quote()};
            if (defined($ansi_result0)) {
                push(@{$parts}, $ansi_result0);
                push(@{$chars}, $ansi_result1);
            } else {
                push(@{$chars}, $self->advance());
            }
            next;
        }
        if ($ctx != main::WORD_CTX_REGEX() && $ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "\"") {
            ($locale_result0, $locale_result1, $locale_result2) = @{$self->read_locale_string()};
            if (defined($locale_result0)) {
                push(@{$parts}, $locale_result0);
                push(@{$parts}, @{$locale_result2});
                push(@{$chars}, $locale_result1);
            } else {
                push(@{$chars}, $self->advance());
            }
            next;
        }
        if ($ch eq "\$") {
            $self->sync_to_parser();
            if (!$self->{parser}->parse_dollar_expansion($chars, $parts, 0)) {
                $self->sync_from_parser();
                push(@{$chars}, $self->advance());
            } else {
                $self->sync_from_parser();
                if ($self->{extglob} && $ctx == main::WORD_CTX_NORMAL() && (scalar(@{($chars // [])}) > 0) && length($chars->[-1]) == 2 && substr($chars->[-1], 0, 1) eq "\$" && ((index("?*\@", substr($chars->[-1], 1, 1)) >= 0)) && !$self->at_end() && $self->peek() eq "(") {
                    push(@{$chars}, $self->advance());
                    $content = $self->parse_matched_pair("(", ")", main::MATCHEDPAIRFLAGS_EXTGLOB(), 0);
                    push(@{$chars}, $content);
                    push(@{$chars}, ")");
                }
            }
            next;
        }
        if ($ctx != main::WORD_CTX_REGEX() && $ch eq "`") {
            $self->sync_to_parser();
            ($cmdsub_result0, $cmdsub_result1) = @{$self->{parser}->parse_backtick_substitution()};
            $self->sync_from_parser();
            if (defined($cmdsub_result0)) {
                push(@{$parts}, $cmdsub_result0);
                push(@{$chars}, $cmdsub_result1);
            } else {
                push(@{$chars}, $self->advance());
            }
            next;
        }
        if ($ctx != main::WORD_CTX_REGEX() && main::is_redirect_char($ch) && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
            $self->sync_to_parser();
            ($procsub_result0, $procsub_result1) = @{$self->{parser}->parse_process_substitution()};
            $self->sync_from_parser();
            if (defined($procsub_result0)) {
                push(@{$parts}, $procsub_result0);
                push(@{$chars}, $procsub_result1);
            } elsif ((length($procsub_result1) > 0)) {
                push(@{$chars}, $procsub_result1);
            } else {
                push(@{$chars}, $self->advance());
                if ($ctx == main::WORD_CTX_NORMAL()) {
                    push(@{$chars}, $self->advance());
                }
            }
            next;
        }
        if ($ctx == main::WORD_CTX_NORMAL() && $ch eq "(" && (scalar(@{($chars // [])}) > 0) && $bracket_depth == 0) {
            $is_array_assign = 0;
            if (scalar(@{$chars}) >= 3 && $chars->[-2] eq "+" && $chars->[-1] eq "=") {
                $is_array_assign = main::is_array_assignment_prefix([@{$chars}[0 .. scalar(@{$chars}) - 2 - 1]]);
            } elsif ($chars->[-1] eq "=" && scalar(@{$chars}) >= 2) {
                $is_array_assign = main::is_array_assignment_prefix([@{$chars}[0 .. scalar(@{$chars}) - 1 - 1]]);
            }
            if ($is_array_assign && ($at_command_start || $in_assign_builtin)) {
                $self->sync_to_parser();
                ($array_result0, $array_result1) = @{$self->{parser}->parse_array_literal()};
                $self->sync_from_parser();
                if (defined($array_result0)) {
                    push(@{$parts}, $array_result0);
                    push(@{$chars}, $array_result1);
                } else {
                    last;
                }
                next;
            }
        }
        if ($self->{extglob} && $ctx == main::WORD_CTX_NORMAL() && main::is_extglob_prefix($ch) && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
            push(@{$chars}, $self->advance());
            push(@{$chars}, $self->advance());
            $content = $self->parse_matched_pair("(", ")", main::MATCHEDPAIRFLAGS_EXTGLOB(), 0);
            push(@{$chars}, $content);
            push(@{$chars}, ")");
            next;
        }
        if ($ctx == main::WORD_CTX_NORMAL() && ($self->{parser_state} & main::PARSERSTATEFLAGS_PST_EOFTOKEN() ? 1 : 0) && $self->{eof_token} ne "" && $ch eq $self->{eof_token} && $bracket_depth == 0) {
            if (!(scalar(@{($chars // [])}) > 0)) {
                push(@{$chars}, $self->advance());
            }
            last;
        }
        if ($ctx == main::WORD_CTX_NORMAL() && main::is_metachar($ch) && $bracket_depth == 0) {
            last;
        }
        push(@{$chars}, $self->advance());
    }
    if ($bracket_depth > 0 && $bracket_start_pos != -1 && $self->at_end()) {
        die "unexpected EOF looking for `]'";
    }
    if (!(scalar(@{($chars // [])}) > 0)) {
        return undef;
    }
    if ((scalar(@{($parts // [])}) > 0)) {
        return Word->new(join("", @{$chars}), $parts, "word");
    }
    return Word->new(join("", @{$chars}), undef, "word");
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
    my $is_procsub = ($c eq "<" || $c eq ">") && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(";
    my $is_regex_paren = $self->{word_context} == main::WORD_CTX_REGEX() && ($c eq "(" || $c eq ")");
    if ($self->is_metachar($c) && !$is_procsub && !$is_regex_paren) {
        return undef;
    }
    my $word = $self->read_word_internal($self->{word_context}, $self->{at_command_start}, $self->{in_array_literal}, $self->{in_assign_builtin});
    if (!defined($word)) {
        return undef;
    }
    return Token->new(main::TOKENTYPE_WORD(), $word->{value}, $start, [], $word);
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
        $tok = Token->new(main::TOKENTYPE_EOF(), "", $self->{pos_}, undef, undef);
        $self->{last_read_token} = $tok;
        return $tok;
    }
    if ($self->{eof_token} ne "" && $self->peek() eq $self->{eof_token} && !($self->{parser_state} & main::PARSERSTATEFLAGS_PST_CASEPAT() ? 1 : 0) && !($self->{parser_state} & main::PARSERSTATEFLAGS_PST_EOFTOKEN() ? 1 : 0)) {
        $tok = Token->new(main::TOKENTYPE_EOF(), "", $self->{pos_}, undef, undef);
        $self->{last_read_token} = $tok;
        return $tok;
    }
    while ($self->skip_comment()) {
        $self->skip_blanks();
        if ($self->at_end()) {
            $tok = Token->new(main::TOKENTYPE_EOF(), "", $self->{pos_}, undef, undef);
            $self->{last_read_token} = $tok;
            return $tok;
        }
        if ($self->{eof_token} ne "" && $self->peek() eq $self->{eof_token} && !($self->{parser_state} & main::PARSERSTATEFLAGS_PST_CASEPAT() ? 1 : 0) && !($self->{parser_state} & main::PARSERSTATEFLAGS_PST_EOFTOKEN() ? 1 : 0)) {
            $tok = Token->new(main::TOKENTYPE_EOF(), "", $self->{pos_}, undef, undef);
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
    $tok = Token->new(main::TOKENTYPE_EOF(), "", $self->{pos_}, undef, undef);
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
    if ($self->{pos_} + 1 >= $self->{length_} || substr($self->{source}, $self->{pos_} + 1, 1) ne "'") {
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
            push(@{$content_chars}, $self->advance());
            if (!$self->at_end()) {
                push(@{$content_chars}, $self->advance());
            }
        } else {
            push(@{$content_chars}, $self->advance());
        }
    }
    if (!$found_close) {
        die "unexpected EOF while looking for matching `''";
    }
    my $text = main::substring($self->{source}, $start, $self->{pos_});
    my $content = join("", @{$content_chars});
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
    if ($self->{pos_} + 1 >= $self->{length_} || substr($self->{source}, $self->{pos_} + 1, 1) ne "\"") {
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
            $next_ch = substr($self->{source}, $self->{pos_} + 1, 1);
            if ($next_ch eq "\n") {
                $self->advance();
                $self->advance();
            } else {
                push(@{$content_chars}, $self->advance());
                push(@{$content_chars}, $self->advance());
            }
        } elsif ($ch eq "\$" && $self->{pos_} + 2 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(" && substr($self->{source}, $self->{pos_} + 2, 1) eq "(") {
            $self->sync_to_parser();
            ($arith_node, $arith_text) = @{$self->{parser}->parse_arithmetic_expansion()};
            $self->sync_from_parser();
            if (defined($arith_node)) {
                push(@{$inner_parts}, $arith_node);
                push(@{$content_chars}, $arith_text);
            } else {
                $self->sync_to_parser();
                ($cmdsub_node, $cmdsub_text) = @{$self->{parser}->parse_command_substitution()};
                $self->sync_from_parser();
                if (defined($cmdsub_node)) {
                    push(@{$inner_parts}, $cmdsub_node);
                    push(@{$content_chars}, $cmdsub_text);
                } else {
                    push(@{$content_chars}, $self->advance());
                }
            }
        } elsif (main::is_expansion_start($self->{source}, $self->{pos_}, "\$(")) {
            $self->sync_to_parser();
            ($cmdsub_node, $cmdsub_text) = @{$self->{parser}->parse_command_substitution()};
            $self->sync_from_parser();
            if (defined($cmdsub_node)) {
                push(@{$inner_parts}, $cmdsub_node);
                push(@{$content_chars}, $cmdsub_text);
            } else {
                push(@{$content_chars}, $self->advance());
            }
        } elsif ($ch eq "\$") {
            $self->sync_to_parser();
            ($param_node, $param_text) = @{$self->{parser}->parse_param_expansion(0)};
            $self->sync_from_parser();
            if (defined($param_node)) {
                push(@{$inner_parts}, $param_node);
                push(@{$content_chars}, $param_text);
            } else {
                push(@{$content_chars}, $self->advance());
            }
        } elsif ($ch eq "`") {
            $self->sync_to_parser();
            ($cmdsub_node, $cmdsub_text) = @{$self->{parser}->parse_backtick_substitution()};
            $self->sync_from_parser();
            if (defined($cmdsub_node)) {
                push(@{$inner_parts}, $cmdsub_node);
                push(@{$content_chars}, $cmdsub_text);
            } else {
                push(@{$content_chars}, $self->advance());
            }
        } else {
            push(@{$content_chars}, $self->advance());
        }
    }
    if (!$found_close) {
        $self->{pos_} = $start;
        return [undef, "", []];
    }
    my $content = join("", @{$content_chars});
    my $text = "\$\"" . $content . "\"";
    return [LocaleString->new($content, "locale"), $text, $inner_parts];
}

sub update_dolbrace_for_op ($self, $op, $has_param) {
    if ($self->{dolbrace_state} == main::DOLBRACESTATE_NONE()) {
        return;
    }
    if ($op eq "" || length($op) == 0) {
        return;
    }
    my $first_char = substr($op, 0, 1);
    if ($self->{dolbrace_state} == main::DOLBRACESTATE_PARAM() && $has_param) {
        if ((index("%#^,", $first_char) >= 0)) {
            $self->{dolbrace_state} = main::DOLBRACESTATE_QUOTE();
            return;
        }
        if ($first_char eq "/") {
            $self->{dolbrace_state} = main::DOLBRACESTATE_QUOTE2();
            return;
        }
    }
    if ($self->{dolbrace_state} == main::DOLBRACESTATE_PARAM()) {
        if ((index("#%^,~:-=?+/", $first_char) >= 0)) {
            $self->{dolbrace_state} = main::DOLBRACESTATE_OP();
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
        if (main::is_simple_param_op($next_ch)) {
            $self->advance();
            return ":" . $next_ch;
        }
        return ":";
    }
    if (main::is_simple_param_op($ch)) {
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
    my $quote = main::new_quote_state();
    while ($i < $self->{length_}) {
        $c = substr($self->{source}, $i, 1);
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
    if (main::is_special_param($ch)) {
        if ($ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && ((index("{'\"", substr($self->{source}, $self->{pos_} + 1, 1)) >= 0))) {
            return "";
        }
        $self->advance();
        return $ch;
    }
    if (($ch =~ /^\d$/)) {
        my $name_chars = [];
        while (!$self->at_end() && ($self->peek() =~ /^\d$/)) {
            push(@{$name_chars}, $self->advance());
        }
        return join("", @{$name_chars});
    }
    if (($ch =~ /^[a-zA-Z]$/) || $ch eq "_") {
        $name_chars = [];
        while (!$self->at_end()) {
            $c = $self->peek();
            if (($c =~ /^[a-zA-Z0-9]$/) || $c eq "_") {
                push(@{$name_chars}, $self->advance());
            } elsif ($c eq "[") {
                if (!$self->param_subscript_has_close($self->{pos_})) {
                    last;
                }
                push(@{$name_chars}, $self->advance());
                $content = $self->parse_matched_pair("[", "]", main::MATCHEDPAIRFLAGS_ARRAYSUB(), 0);
                push(@{$name_chars}, $content);
                push(@{$name_chars}, "]");
                last;
            } else {
                last;
            }
        }
        if ((scalar(@{($name_chars // [])}) > 0)) {
            return join("", @{$name_chars});
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
    if (main::is_special_param_unbraced($ch) || main::is_digit($ch) || $ch eq "#") {
        $self->advance();
        $text = main::substring($self->{source}, $start, $self->{pos_});
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
        $name = main::substring($self->{source}, $name_start, $self->{pos_});
        $text = main::substring($self->{source}, $start, $self->{pos_});
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
    $self->{dolbrace_state} = main::DOLBRACESTATE_PARAM();
    my $ch = $self->peek();
    if (main::is_funsub_char($ch)) {
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
            $text = main::substring($self->{source}, $start, $self->{pos_});
            $self->{dolbrace_state} = $saved_dolbrace;
            return [ParamLength->new($param, "param-len"), $text];
        }
        $self->{pos_} = $start + 2;
    }
    my $op = "";
    my $arg = "";
    if ($ch eq "!") {
        $self->advance();
        while (!$self->at_end() && main::is_whitespace_no_newline($self->peek())) {
            $self->advance();
        }
        $param = $self->consume_param_name();
        if ((length($param) > 0)) {
            while (!$self->at_end() && main::is_whitespace_no_newline($self->peek())) {
                $self->advance();
            }
            if (!$self->at_end() && $self->peek() eq "}") {
                $self->advance();
                $text = main::substring($self->{source}, $start, $self->{pos_});
                $self->{dolbrace_state} = $saved_dolbrace;
                return [ParamIndirect->new($param, "param-indirect"), $text];
            }
            if (!$self->at_end() && main::is_at_or_star($self->peek())) {
                $suffix = $self->advance();
                $trailing = $self->parse_matched_pair("{", "}", main::MATCHEDPAIRFLAGS_DOLBRACE(), 0);
                $text = main::substring($self->{source}, $start, $self->{pos_});
                $self->{dolbrace_state} = $saved_dolbrace;
                return [ParamIndirect->new($param . $suffix . $trailing, "param-indirect"), $text];
            }
            $op = $self->consume_param_operator();
            if ($op eq "" && !$self->at_end() && ((index("}\"'`", $self->peek()) == -1))) {
                $op = $self->advance();
            }
            if ($op ne "" && ((index("\"'`", $op) == -1))) {
                $arg = $self->parse_matched_pair("{", "}", main::MATCHEDPAIRFLAGS_DOLBRACE(), 0);
                $text = main::substring($self->{source}, $start, $self->{pos_});
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
        if (!$self->at_end() && (((index("-=+?", $self->peek()) >= 0)) || $self->peek() eq ":" && $self->{pos_} + 1 < $self->{length_} && main::is_simple_param_op(substr($self->{source}, $self->{pos_} + 1, 1)))) {
            $param = "";
        } else {
            $content = $self->parse_matched_pair("{", "}", main::MATCHEDPAIRFLAGS_DOLBRACE(), 0);
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
        $text = main::substring($self->{source}, $start, $self->{pos_});
        $self->{dolbrace_state} = $saved_dolbrace;
        return [ParamExpansion->new($param, "param"), $text];
    }
    $op = $self->consume_param_operator();
    if ($op eq "") {
        if (!$self->at_end() && $self->peek() eq "\$" && $self->{pos_} + 1 < $self->{length_} && (substr($self->{source}, $self->{pos_} + 1, 1) eq "\"" || substr($self->{source}, $self->{pos_} + 1, 1) eq "'")) {
            $dollar_count = 1 + main::count_consecutive_dollars_before($self->{source}, $self->{pos_});
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
                    $next_c = substr($self->{source}, $self->{pos_} + 1, 1);
                    if (main::is_escape_char_in_backtick($next_c)) {
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
        } elsif (!$self->at_end() && $self->peek() eq "\$" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "{") {
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
        $flags = ($in_dquote ? main::MATCHEDPAIRFLAGS_DQUOTE() : main::MATCHEDPAIRFLAGS_NONE());
        $param_ends_with_dollar = $param ne "" && (substr($param, -length("\$")) eq "\$");
        $arg = $self->collect_param_argument($flags, $param_ends_with_dollar);
    };
    if (my $e = $@) {
        $self->{dolbrace_state} = $saved_dolbrace;
        die $e;
    }
    if (($op eq "<" || $op eq ">") && (index($arg, "(") == 0) && (substr($arg, -length(")")) eq ")")) {
        $inner = substr($arg, 1, length($arg) - 1 - 1);
        eval {
            $sub_parser = main::new_parser($inner, 1, $self->{parser}->{extglob});
            $parsed = $sub_parser->parse_list(1);
            if (defined($parsed) && $sub_parser->at_end()) {
                $formatted = main::format_cmdsub_node($parsed, 0, 1, 0, 1);
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

sub new ($class, $value=undef, $parts=undef, $kind=undef) {
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
    $value = ($value =~ s/\x{7f}/\x{01}\x{7f}/gr);
    $value = ($value =~ s/\\/\\\\/gr);
    if ((substr($value, -length("\\\\")) eq "\\\\") && !(substr($value, -length("\\\\\\\\")) eq "\\\\\\\\")) {
        $value = $value . "\\\\";
    }
    my $escaped = ((($value =~ s/"/\\"/gr) =~ s/\n/\\n/gr) =~ s/\t/\\t/gr);
    return "(word \"" . $escaped . "\")";
}

sub append_with_ctlesc ($self, $result, $byte_val) {
    push(@{$result}, $byte_val);
}

sub double_ctlesc_smart ($self, $value) {
    my $bs_count;
    my $result = [];
    my $quote = main::new_quote_state();
    for my $c (split(//, $value)) {
        if ($c eq "'" && !$quote->{double}) {
            $quote->{single} = !$quote->{single};
        } elsif ($c eq "\"" && !$quote->{single}) {
            $quote->{double} = !$quote->{double};
        }
        push(@{$result}, $c);
        if ($c eq "") {
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
                    push(@{$result}, "");
                }
            } else {
                push(@{$result}, "");
            }
        }
    }
    return join("", @{$result});
}

sub normalize_param_expansion_newlines ($self, $value) {
    my $c;
    my $ch;
    my $depth;
    my $had_leading_newline;
    my $result = [];
    my $i = 0;
    my $quote = main::new_quote_state();
    while ($i < length($value)) {
        $c = substr($value, $i, 1);
        if ($c eq "'" && !$quote->{double}) {
            $quote->{single} = !$quote->{single};
            push(@{$result}, $c);
            $i += 1;
        } elsif ($c eq "\"" && !$quote->{single}) {
            $quote->{double} = !$quote->{double};
            push(@{$result}, $c);
            $i += 1;
        } elsif (main::is_expansion_start($value, $i, "\${") && !$quote->{single}) {
            push(@{$result}, "\$");
            push(@{$result}, "{");
            $i += 2;
            $had_leading_newline = $i < length($value) && substr($value, $i, 1) eq "\n";
            if ($had_leading_newline) {
                push(@{$result}, " ");
                $i += 1;
            }
            $depth = 1;
            while ($i < length($value) && $depth > 0) {
                $ch = substr($value, $i, 1);
                if ($ch eq "\\" && $i + 1 < length($value) && !$quote->{single}) {
                    if (substr($value, $i + 1, 1) eq "\n") {
                        $i += 2;
                        next;
                    }
                    push(@{$result}, $ch);
                    push(@{$result}, substr($value, $i + 1, 1));
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
                                push(@{$result}, " ");
                            }
                            push(@{$result}, $ch);
                            $i += 1;
                            last;
                        }
                    }
                }
                push(@{$result}, $ch);
                $i += 1;
            }
        } else {
            push(@{$result}, $c);
            $i += 1;
        }
    }
    return join("", @{$result});
}

sub sh_single_quote ($self, $s_) {
    if (!(length($s_) > 0)) {
        return "''";
    }
    if ($s_ eq "'") {
        return "\\'";
    }
    my $result = ["'"];
    for my $c (split(//, $s_)) {
        if ($c eq "'") {
            push(@{$result}, "'\\''");
        } else {
            push(@{$result}, $c);
        }
    }
    push(@{$result}, "'");
    return join("", @{$result});
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
        if (substr($inner, $i, 1) eq "\\" && $i + 1 < length($inner)) {
            $c = substr($inner, $i + 1, 1);
            $simple = main::get_ansi_escape($c);
            if ($simple >= 0) {
                push(@{$result}, $simple);
                $i += 2;
            } elsif ($c eq "'") {
                push(@{$result}, 39);
                $i += 2;
            } elsif ($c eq "x") {
                if ($i + 2 < length($inner) && substr($inner, $i + 2, 1) eq "{") {
                    $j = $i + 3;
                    while ($j < length($inner) && main::is_hex_digit(substr($inner, $j, 1))) {
                        $j += 1;
                    }
                    $hex_str = main::substring($inner, $i + 3, $j);
                    if ($j < length($inner) && substr($inner, $j, 1) eq "}") {
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
                    while ($j < length($inner) && $j < $i + 4 && main::is_hex_digit(substr($inner, $j, 1))) {
                        $j += 1;
                    }
                    if ($j > $i + 2) {
                        $byte_val = hex(main::substring($inner, $i + 2, $j));
                        if ($byte_val == 0) {
                            return $result;
                        }
                        $self->append_with_ctlesc($result, $byte_val);
                        $i = $j;
                    } else {
                        push(@{$result}, ord(substr(substr($inner, $i, 1), 0, 1)));
                        $i += 1;
                    }
                }
            } elsif ($c eq "u") {
                $j = $i + 2;
                while ($j < length($inner) && $j < $i + 6 && main::is_hex_digit(substr($inner, $j, 1))) {
                    $j += 1;
                }
                if ($j > $i + 2) {
                    $codepoint = hex(main::substring($inner, $i + 2, $j));
                    if ($codepoint == 0) {
                        return $result;
                    }
                    push(@{$result}, @{[unpack('C*', chr($codepoint))]});
                    $i = $j;
                } else {
                    push(@{$result}, ord(substr(substr($inner, $i, 1), 0, 1)));
                    $i += 1;
                }
            } elsif ($c eq "U") {
                $j = $i + 2;
                while ($j < length($inner) && $j < $i + 10 && main::is_hex_digit(substr($inner, $j, 1))) {
                    $j += 1;
                }
                if ($j > $i + 2) {
                    $codepoint = hex(main::substring($inner, $i + 2, $j));
                    if ($codepoint == 0) {
                        return $result;
                    }
                    push(@{$result}, @{[unpack('C*', chr($codepoint))]});
                    $i = $j;
                } else {
                    push(@{$result}, ord(substr(substr($inner, $i, 1), 0, 1)));
                    $i += 1;
                }
            } elsif ($c eq "c") {
                if ($i + 3 <= length($inner)) {
                    $ctrl_char = substr($inner, $i + 2, 1);
                    $skip_extra = 0;
                    if ($ctrl_char eq "\\" && $i + 4 <= length($inner) && substr($inner, $i + 3, 1) eq "\\") {
                        $skip_extra = 1;
                    }
                    $ctrl_val = ord(substr($ctrl_char, 0, 1)) & 31;
                    if ($ctrl_val == 0) {
                        return $result;
                    }
                    $self->append_with_ctlesc($result, $ctrl_val);
                    $i += 3 + $skip_extra;
                } else {
                    push(@{$result}, ord(substr(substr($inner, $i, 1), 0, 1)));
                    $i += 1;
                }
            } elsif ($c eq "0") {
                $j = $i + 2;
                while ($j < length($inner) && $j < $i + 4 && main::is_octal_digit(substr($inner, $j, 1))) {
                    $j += 1;
                }
                if ($j > $i + 2) {
                    $byte_val = oct(main::substring($inner, $i + 1, $j)) & 255;
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
                while ($j < length($inner) && $j < $i + 4 && main::is_octal_digit(substr($inner, $j, 1))) {
                    $j += 1;
                }
                $byte_val = oct(main::substring($inner, $i + 1, $j)) & 255;
                if ($byte_val == 0) {
                    return $result;
                }
                $self->append_with_ctlesc($result, $byte_val);
                $i = $j;
            } else {
                push(@{$result}, 92);
                push(@{$result}, ord(substr($c, 0, 1)));
                $i += 2;
            }
        } else {
            push(@{$result}, @{[unpack('C*', substr($inner, $i, 1))]});
            $i += 1;
        }
    }
    return $result;
}

sub expand_ansi_c_escapes ($self, $value) {
    if (!((index($value, "'") == 0) && (substr($value, -length("'")) eq "'"))) {
        return $value;
    }
    my $inner = main::substring($value, 1, length($value) - 1);
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
    my $quote = main::new_quote_state();
    my $in_backtick = 0;
    my $brace_depth = 0;
    while ($i < length($value)) {
        $ch = substr($value, $i, 1);
        if ($ch eq "`" && !$quote->{single}) {
            $in_backtick = !$in_backtick;
            push(@{$result}, $ch);
            $i += 1;
            next;
        }
        if ($in_backtick) {
            if ($ch eq "\\" && $i + 1 < length($value)) {
                push(@{$result}, $ch);
                push(@{$result}, substr($value, $i + 1, 1));
                $i += 2;
            } else {
                push(@{$result}, $ch);
                $i += 1;
            }
            next;
        }
        if (!$quote->{single}) {
            if (main::is_expansion_start($value, $i, "\${")) {
                $brace_depth += 1;
                $quote->push_();
                push(@{$result}, "\${");
                $i += 2;
                next;
            } elsif ($ch eq "}" && $brace_depth > 0 && !$quote->{double}) {
                $brace_depth -= 1;
                push(@{$result}, $ch);
                $quote->pop_();
                $i += 1;
                next;
            }
        }
        $effective_in_dquote = $quote->{double};
        if ($ch eq "'" && !$effective_in_dquote) {
            $is_ansi_c = !$quote->{single} && $i > 0 && substr($value, $i - 1, 1) eq "\$" && main::count_consecutive_dollars_before($value, $i - 1) % 2 == 0;
            if (!$is_ansi_c) {
                $quote->{single} = !$quote->{single};
            }
            push(@{$result}, $ch);
            $i += 1;
        } elsif ($ch eq "\"" && !$quote->{single}) {
            $quote->{double} = !$quote->{double};
            push(@{$result}, $ch);
            $i += 1;
        } elsif ($ch eq "\\" && $i + 1 < length($value) && !$quote->{single}) {
            push(@{$result}, $ch);
            push(@{$result}, substr($value, $i + 1, 1));
            $i += 2;
        } elsif (main::starts_with_at($value, $i, "\$'") && !$quote->{single} && !$effective_in_dquote && main::count_consecutive_dollars_before($value, $i) % 2 == 0) {
            $j = $i + 2;
            while ($j < length($value)) {
                if (substr($value, $j, 1) eq "\\" && $j + 1 < length($value)) {
                    $j += 2;
                } elsif (substr($value, $j, 1) eq "'") {
                    $j += 1;
                    last;
                } else {
                    $j += 1;
                }
            }
            $ansi_str = main::substring($value, $i, $j);
            $expanded = $self->expand_ansi_c_escapes(main::substring($ansi_str, 1, length($ansi_str)));
            $outer_in_dquote = $quote->outer_double();
            if ($brace_depth > 0 && $outer_in_dquote && (index($expanded, "'") == 0) && (substr($expanded, -length("'")) eq "'")) {
                $inner = main::substring($expanded, 1, length($expanded) - 1);
                if (index($inner, "") == -1) {
                    $result_str = join("", @{$result});
                    $in_pattern = 0;
                    $last_brace_idx = rindex($result_str, "\${");
                    if ($last_brace_idx >= 0) {
                        $after_brace = substr($result_str, $last_brace_idx + 2);
                        $var_name_len = 0;
                        if ((length($after_brace) > 0)) {
                            if ((index("\@*#?-\$!0123456789_", substr($after_brace, 0, 1)) >= 0)) {
                                $var_name_len = 1;
                            } elsif ((substr($after_brace, 0, 1) =~ /^[a-zA-Z]$/) || substr($after_brace, 0, 1) eq "_") {
                                while ($var_name_len < length($after_brace)) {
                                    $c = substr($after_brace, $var_name_len, 1);
                                    if (!(($c =~ /^[a-zA-Z0-9]$/) || $c eq "_")) {
                                        last;
                                    }
                                    $var_name_len += 1;
                                }
                            }
                        }
                        if ($var_name_len > 0 && $var_name_len < length($after_brace) && ((index("#?-", substr($after_brace, 0, 1)) == -1))) {
                            $op_start = substr($after_brace, $var_name_len);
                            if ((index($op_start, "\@") == 0) && length($op_start) > 1) {
                                $op_start = substr($op_start, 1);
                            }
                            for my $op (@{["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]}) {
                                if ((index($op_start, $op) == 0)) {
                                    $in_pattern = 1;
                                    last;
                                }
                            }
                            if (!$in_pattern && (length($op_start) > 0) && ((index("%#/^,~:+-=?", substr($op_start, 0, 1)) == -1))) {
                                for my $op (@{["//", "%%", "##", "/", "%", "#", "^", "^^", ",", ",,"]}) {
                                    if ((index($op_start, $op) >= 0)) {
                                        $in_pattern = 1;
                                        last;
                                    }
                                }
                            }
                        } elsif ($var_name_len == 0 && length($after_brace) > 1) {
                            $first_char = substr($after_brace, 0, 1);
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
            push(@{$result}, $expanded);
            $i = $j;
        } else {
            push(@{$result}, $ch);
            $i += 1;
        }
    }
    return join("", @{$result});
}

sub strip_locale_string_dollars ($self, $value) {
    my $ch;
    my $dollar_count;
    my $result = [];
    my $i = 0;
    my $brace_depth = 0;
    my $bracket_depth = 0;
    my $quote = main::new_quote_state();
    my $brace_quote = main::new_quote_state();
    my $bracket_in_double_quote = 0;
    while ($i < length($value)) {
        $ch = substr($value, $i, 1);
        if ($ch eq "\\" && $i + 1 < length($value) && !$quote->{single} && !$brace_quote->{single}) {
            push(@{$result}, $ch);
            push(@{$result}, substr($value, $i + 1, 1));
            $i += 2;
        } elsif (main::starts_with_at($value, $i, "\${") && !$quote->{single} && !$brace_quote->{single} && ($i == 0 || substr($value, $i - 1, 1) ne "\$")) {
            $brace_depth += 1;
            $brace_quote->{double} = 0;
            $brace_quote->{single} = 0;
            push(@{$result}, "\$");
            push(@{$result}, "{");
            $i += 2;
        } elsif ($ch eq "}" && $brace_depth > 0 && !$quote->{single} && !$brace_quote->{double} && !$brace_quote->{single}) {
            $brace_depth -= 1;
            push(@{$result}, $ch);
            $i += 1;
        } elsif ($ch eq "[" && $brace_depth > 0 && !$quote->{single} && !$brace_quote->{double}) {
            $bracket_depth += 1;
            $bracket_in_double_quote = 0;
            push(@{$result}, $ch);
            $i += 1;
        } elsif ($ch eq "]" && $bracket_depth > 0 && !$quote->{single} && !$bracket_in_double_quote) {
            $bracket_depth -= 1;
            push(@{$result}, $ch);
            $i += 1;
        } elsif ($ch eq "'" && !$quote->{double} && $brace_depth == 0) {
            $quote->{single} = !$quote->{single};
            push(@{$result}, $ch);
            $i += 1;
        } elsif ($ch eq "\"" && !$quote->{single} && $brace_depth == 0) {
            $quote->{double} = !$quote->{double};
            push(@{$result}, $ch);
            $i += 1;
        } elsif ($ch eq "\"" && !$quote->{single} && $bracket_depth > 0) {
            $bracket_in_double_quote = !$bracket_in_double_quote;
            push(@{$result}, $ch);
            $i += 1;
        } elsif ($ch eq "\"" && !$quote->{single} && !$brace_quote->{single} && $brace_depth > 0) {
            $brace_quote->{double} = !$brace_quote->{double};
            push(@{$result}, $ch);
            $i += 1;
        } elsif ($ch eq "'" && !$quote->{double} && !$brace_quote->{double} && $brace_depth > 0) {
            $brace_quote->{single} = !$brace_quote->{single};
            push(@{$result}, $ch);
            $i += 1;
        } elsif (main::starts_with_at($value, $i, "\$\"") && !$quote->{single} && !$brace_quote->{single} && ($brace_depth > 0 || $bracket_depth > 0 || !$quote->{double}) && !$brace_quote->{double} && !$bracket_in_double_quote) {
            $dollar_count = 1 + main::count_consecutive_dollars_before($value, $i);
            if ($dollar_count % 2 == 1) {
                push(@{$result}, "\"");
                if ($bracket_depth > 0) {
                    $bracket_in_double_quote = 1;
                } elsif ($brace_depth > 0) {
                    $brace_quote->{double} = 1;
                } else {
                    $quote->{double} = 1;
                }
                $i += 2;
            } else {
                push(@{$result}, $ch);
                $i += 1;
            }
        } else {
            push(@{$result}, $ch);
            $i += 1;
        }
    }
    return join("", @{$result});
}

sub normalize_array_whitespace ($self, $value) {
    my $close_paren_pos;
    my $depth;
    my $i = 0;
    if (!($i < length($value) && ((substr($value, $i, 1) =~ /^[a-zA-Z]$/) || substr($value, $i, 1) eq "_"))) {
        return $value;
    }
    $i += 1;
    while ($i < length($value) && ((substr($value, $i, 1) =~ /^[a-zA-Z0-9]$/) || substr($value, $i, 1) eq "_")) {
        $i += 1;
    }
    while ($i < length($value) && substr($value, $i, 1) eq "[") {
        $depth = 1;
        $i += 1;
        while ($i < length($value) && $depth > 0) {
            if (substr($value, $i, 1) eq "[") {
                $depth += 1;
            } elsif (substr($value, $i, 1) eq "]") {
                $depth -= 1;
            }
            $i += 1;
        }
        if ($depth != 0) {
            return $value;
        }
    }
    if ($i < length($value) && substr($value, $i, 1) eq "+") {
        $i += 1;
    }
    if (!($i + 1 < length($value) && substr($value, $i, 1) eq "=" && substr($value, $i + 1, 1) eq "(")) {
        return $value;
    }
    my $prefix = main::substring($value, 0, $i + 1);
    my $open_paren_pos = $i + 1;
    my $close_paren_pos = 0;
    if ((substr($value, -length(")")) eq ")")) {
        $close_paren_pos = length($value) - 1;
    } else {
        $close_paren_pos = $self->find_matching_paren($value, $open_paren_pos);
        if ($close_paren_pos < 0) {
            return $value;
        }
    }
    my $inner = main::substring($value, $open_paren_pos + 1, $close_paren_pos);
    my $suffix = main::substring($value, $close_paren_pos + 1, length($value));
    my $result = $self->normalize_array_inner($inner);
    return $prefix . "(" . $result . ")" . $suffix;
}

sub find_matching_paren ($self, $value, $open_pos) {
    my $ch;
    if ($open_pos >= length($value) || substr($value, $open_pos, 1) ne "(") {
        return -1;
    }
    my $i = $open_pos + 1;
    my $depth = 1;
    my $quote = main::new_quote_state();
    while ($i < length($value) && $depth > 0) {
        $ch = substr($value, $i, 1);
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
            while ($i < length($value) && substr($value, $i, 1) ne "\n") {
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
        $ch = substr($inner, $i, 1);
        if (main::is_whitespace($ch)) {
            if (!$in_whitespace && (scalar(@{($normalized // [])}) > 0) && $brace_depth == 0 && $bracket_depth == 0) {
                push(@{$normalized}, " ");
                $in_whitespace = 1;
            }
            if ($brace_depth > 0 || $bracket_depth > 0) {
                push(@{$normalized}, $ch);
            }
            $i += 1;
        } elsif ($ch eq "'") {
            $in_whitespace = 0;
            $j = $i + 1;
            while ($j < length($inner) && substr($inner, $j, 1) ne "'") {
                $j += 1;
            }
            push(@{$normalized}, main::substring($inner, $i, $j + 1));
            $i = $j + 1;
        } elsif ($ch eq "\"") {
            $in_whitespace = 0;
            $j = $i + 1;
            $dq_content = ["\""];
            $dq_brace_depth = 0;
            while ($j < length($inner)) {
                if (substr($inner, $j, 1) eq "\\" && $j + 1 < length($inner)) {
                    if (substr($inner, $j + 1, 1) eq "\n") {
                        $j += 2;
                    } else {
                        push(@{$dq_content}, substr($inner, $j, 1));
                        push(@{$dq_content}, substr($inner, $j + 1, 1));
                        $j += 2;
                    }
                } elsif (main::is_expansion_start($inner, $j, "\${")) {
                    push(@{$dq_content}, "\${");
                    $dq_brace_depth += 1;
                    $j += 2;
                } elsif (substr($inner, $j, 1) eq "}" && $dq_brace_depth > 0) {
                    push(@{$dq_content}, "}");
                    $dq_brace_depth -= 1;
                    $j += 1;
                } elsif (substr($inner, $j, 1) eq "\"" && $dq_brace_depth == 0) {
                    push(@{$dq_content}, "\"");
                    $j += 1;
                    last;
                } else {
                    push(@{$dq_content}, substr($inner, $j, 1));
                    $j += 1;
                }
            }
            push(@{$normalized}, join("", @{$dq_content}));
            $i = $j;
        } elsif ($ch eq "\\" && $i + 1 < length($inner)) {
            if (substr($inner, $i + 1, 1) eq "\n") {
                $i += 2;
            } else {
                $in_whitespace = 0;
                push(@{$normalized}, main::substring($inner, $i, $i + 2));
                $i += 2;
            }
        } elsif (main::is_expansion_start($inner, $i, "\$((")) {
            $in_whitespace = 0;
            $j = $i + 3;
            $depth = 1;
            while ($j < length($inner) && $depth > 0) {
                if ($j + 1 < length($inner) && substr($inner, $j, 1) eq "(" && substr($inner, $j + 1, 1) eq "(") {
                    $depth += 1;
                    $j += 2;
                } elsif ($j + 1 < length($inner) && substr($inner, $j, 1) eq ")" && substr($inner, $j + 1, 1) eq ")") {
                    $depth -= 1;
                    $j += 2;
                } else {
                    $j += 1;
                }
            }
            push(@{$normalized}, main::substring($inner, $i, $j));
            $i = $j;
        } elsif (main::is_expansion_start($inner, $i, "\$(")) {
            $in_whitespace = 0;
            $j = $i + 2;
            $depth = 1;
            while ($j < length($inner) && $depth > 0) {
                if (substr($inner, $j, 1) eq "(" && $j > 0 && substr($inner, $j - 1, 1) eq "\$") {
                    $depth += 1;
                } elsif (substr($inner, $j, 1) eq ")") {
                    $depth -= 1;
                } elsif (substr($inner, $j, 1) eq "'") {
                    $j += 1;
                    while ($j < length($inner) && substr($inner, $j, 1) ne "'") {
                        $j += 1;
                    }
                } elsif (substr($inner, $j, 1) eq "\"") {
                    $j += 1;
                    while ($j < length($inner)) {
                        if (substr($inner, $j, 1) eq "\\" && $j + 1 < length($inner)) {
                            $j += 2;
                            next;
                        }
                        if (substr($inner, $j, 1) eq "\"") {
                            last;
                        }
                        $j += 1;
                    }
                }
                $j += 1;
            }
            push(@{$normalized}, main::substring($inner, $i, $j));
            $i = $j;
        } elsif (($ch eq "<" || $ch eq ">") && $i + 1 < length($inner) && substr($inner, $i + 1, 1) eq "(") {
            $in_whitespace = 0;
            $j = $i + 2;
            $depth = 1;
            while ($j < length($inner) && $depth > 0) {
                if (substr($inner, $j, 1) eq "(") {
                    $depth += 1;
                } elsif (substr($inner, $j, 1) eq ")") {
                    $depth -= 1;
                } elsif (substr($inner, $j, 1) eq "'") {
                    $j += 1;
                    while ($j < length($inner) && substr($inner, $j, 1) ne "'") {
                        $j += 1;
                    }
                } elsif (substr($inner, $j, 1) eq "\"") {
                    $j += 1;
                    while ($j < length($inner)) {
                        if (substr($inner, $j, 1) eq "\\" && $j + 1 < length($inner)) {
                            $j += 2;
                            next;
                        }
                        if (substr($inner, $j, 1) eq "\"") {
                            last;
                        }
                        $j += 1;
                    }
                }
                $j += 1;
            }
            push(@{$normalized}, main::substring($inner, $i, $j));
            $i = $j;
        } elsif (main::is_expansion_start($inner, $i, "\${")) {
            $in_whitespace = 0;
            push(@{$normalized}, "\${");
            $brace_depth += 1;
            $i += 2;
        } elsif ($ch eq "{" && $brace_depth > 0) {
            push(@{$normalized}, $ch);
            $brace_depth += 1;
            $i += 1;
        } elsif ($ch eq "}" && $brace_depth > 0) {
            push(@{$normalized}, $ch);
            $brace_depth -= 1;
            $i += 1;
        } elsif ($ch eq "#" && $brace_depth == 0 && $in_whitespace) {
            while ($i < length($inner) && substr($inner, $i, 1) ne "\n") {
                $i += 1;
            }
        } elsif ($ch eq "[") {
            if ($in_whitespace || $bracket_depth > 0) {
                $bracket_depth += 1;
            }
            $in_whitespace = 0;
            push(@{$normalized}, $ch);
            $i += 1;
        } elsif ($ch eq "]" && $bracket_depth > 0) {
            push(@{$normalized}, $ch);
            $bracket_depth -= 1;
            $i += 1;
        } else {
            $in_whitespace = 0;
            push(@{$normalized}, $ch);
            $i += 1;
        }
    }
    return (join("", @{$normalized}) =~ s/\s+$//r);
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
        if (main::is_expansion_start($value, $i, "\$((")) {
            $start = $i;
            $i += 3;
            $depth = 2;
            $arith_content = [];
            my $first_close_idx = -1;
            while ($i < length($value) && $depth > 0) {
                if (substr($value, $i, 1) eq "(") {
                    push(@{$arith_content}, "(");
                    $depth += 1;
                    $i += 1;
                    if ($depth > 1) {
                        $first_close_idx = -1;
                    }
                } elsif (substr($value, $i, 1) eq ")") {
                    if ($depth == 2) {
                        $first_close_idx = scalar(@{$arith_content});
                    }
                    $depth -= 1;
                    if ($depth > 0) {
                        push(@{$arith_content}, ")");
                    }
                    $i += 1;
                } elsif (substr($value, $i, 1) eq "\\" && $i + 1 < length($value) && substr($value, $i + 1, 1) eq "\n") {
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
                        push(@{$arith_content}, "\\");
                        push(@{$arith_content}, "\n");
                        $i += 2;
                    } else {
                        $i += 2;
                    }
                    if ($depth == 1) {
                        $first_close_idx = -1;
                    }
                } else {
                    push(@{$arith_content}, substr($value, $i, 1));
                    $i += 1;
                    if ($depth == 1) {
                        $first_close_idx = -1;
                    }
                }
            }
            if ($depth == 0 || $depth == 1 && $first_close_idx != -1) {
                $content = join("", @{$arith_content});
                if ($first_close_idx != -1) {
                    $content = substr($content, 0, $first_close_idx - 0);
                    $closing = ($depth == 0 ? "))" : ")");
                    push(@{$result}, "\$((" . $content . $closing);
                } else {
                    push(@{$result}, "\$((" . $content . ")");
                }
            } else {
                push(@{$result}, main::substring($value, $start, $i));
            }
        } else {
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
        }
    }
    return join("", @{$result});
}

sub collect_cmdsubs ($self, $node) {
    my $result = [];
    if (ref($node) eq 'CommandSubstitution') {
        my $node = $node;
        push(@{$result}, $node);
    } elsif (ref($node) eq 'Array') {
        my $node = $node;
        for my $elem (@{($node->{elements} // [])}) {
            for my $p (@{($elem->{parts} // [])}) {
                if (ref($p) eq 'CommandSubstitution') {
                    my $p = $p;
                    push(@{$result}, $p);
                } else {
                    push(@{$result}, @{$self->collect_cmdsubs($p)});
                }
            }
        }
    } elsif (ref($node) eq 'ArithmeticExpansion') {
        my $node = $node;
        if (defined($node->{expression})) {
            push(@{$result}, @{$self->collect_cmdsubs($node->{expression})});
        }
    } elsif (ref($node) eq 'ArithBinaryOp') {
        my $node = $node;
        push(@{$result}, @{$self->collect_cmdsubs($node->{left})});
        push(@{$result}, @{$self->collect_cmdsubs($node->{right})});
    } elsif (ref($node) eq 'ArithComma') {
        my $node = $node;
        push(@{$result}, @{$self->collect_cmdsubs($node->{left})});
        push(@{$result}, @{$self->collect_cmdsubs($node->{right})});
    } elsif (ref($node) eq 'ArithUnaryOp') {
        my $node = $node;
        push(@{$result}, @{$self->collect_cmdsubs($node->{operand})});
    } elsif (ref($node) eq 'ArithPreIncr') {
        my $node = $node;
        push(@{$result}, @{$self->collect_cmdsubs($node->{operand})});
    } elsif (ref($node) eq 'ArithPostIncr') {
        my $node = $node;
        push(@{$result}, @{$self->collect_cmdsubs($node->{operand})});
    } elsif (ref($node) eq 'ArithPreDecr') {
        my $node = $node;
        push(@{$result}, @{$self->collect_cmdsubs($node->{operand})});
    } elsif (ref($node) eq 'ArithPostDecr') {
        my $node = $node;
        push(@{$result}, @{$self->collect_cmdsubs($node->{operand})});
    } elsif (ref($node) eq 'ArithTernary') {
        my $node = $node;
        push(@{$result}, @{$self->collect_cmdsubs($node->{condition})});
        push(@{$result}, @{$self->collect_cmdsubs($node->{if_true})});
        push(@{$result}, @{$self->collect_cmdsubs($node->{if_false})});
    } elsif (ref($node) eq 'ArithAssign') {
        my $node = $node;
        push(@{$result}, @{$self->collect_cmdsubs($node->{target})});
        push(@{$result}, @{$self->collect_cmdsubs($node->{value})});
    }
    return $result;
}

sub collect_procsubs ($self, $node) {
    my $result = [];
    if (ref($node) eq 'ProcessSubstitution') {
        my $node = $node;
        push(@{$result}, $node);
    } elsif (ref($node) eq 'Array') {
        my $node = $node;
        for my $elem (@{($node->{elements} // [])}) {
            for my $p (@{($elem->{parts} // [])}) {
                if (ref($p) eq 'ProcessSubstitution') {
                    my $p = $p;
                    push(@{$result}, $p);
                } else {
                    push(@{$result}, @{$self->collect_procsubs($p)});
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
            push(@{$cmdsub_parts}, $p);
        } elsif (ref($p) eq 'ProcessSubstitution') {
            my $p = $p;
            push(@{$procsub_parts}, $p);
        } elsif (ref($p) eq 'ArithmeticExpansion') {
            my $p = $p;
            $has_arith = 1;
        } else {
            push(@{$cmdsub_parts}, @{$self->collect_cmdsubs($p)});
            push(@{$procsub_parts}, @{$self->collect_procsubs($p)});
        }
    }
    my $has_brace_cmdsub = index($value, "\${ ") != -1 || index($value, "\${\t") != -1 || index($value, "\${\n") != -1 || index($value, "\${|") != -1;
    my $has_untracked_cmdsub = 0;
    my $has_untracked_procsub = 0;
    my $idx = 0;
    my $scan_quote = main::new_quote_state();
    while ($idx < length($value)) {
        if (substr($value, $idx, 1) eq "\"") {
            $scan_quote->{double} = !$scan_quote->{double};
            $idx += 1;
        } elsif (substr($value, $idx, 1) eq "'" && !$scan_quote->{double}) {
            $idx += 1;
            while ($idx < length($value) && substr($value, $idx, 1) ne "'") {
                $idx += 1;
            }
            if ($idx < length($value)) {
                $idx += 1;
            }
        } elsif (main::starts_with_at($value, $idx, "\$(") && !main::starts_with_at($value, $idx, "\$((") && !main::is_backslash_escaped($value, $idx) && !main::is_dollar_dollar_paren($value, $idx)) {
            $has_untracked_cmdsub = 1;
            last;
        } elsif ((main::starts_with_at($value, $idx, "<(") || main::starts_with_at($value, $idx, ">(")) && !$scan_quote->{double}) {
            if ($idx == 0 || !(substr($value, $idx - 1, 1) =~ /^[a-zA-Z0-9]$/) && ((index("\"'", substr($value, $idx - 1, 1)) == -1))) {
                $has_untracked_procsub = 1;
                last;
            }
            $idx += 1;
        } else {
            $idx += 1;
        }
    }
    my $has_param_with_procsub_pattern = ((index($value, "\${") >= 0)) && (((index($value, "<(") >= 0)) || ((index($value, ">(") >= 0)));
    if (!(scalar(@{($cmdsub_parts // [])}) > 0) && !(scalar(@{($procsub_parts // [])}) > 0) && !$has_brace_cmdsub && !$has_untracked_cmdsub && !$has_untracked_procsub && !$has_param_with_procsub_pattern) {
        return $value;
    }
    my $result = [];
    my $i = 0;
    my $cmdsub_idx = 0;
    my $procsub_idx = 0;
    my $main_quote = main::new_quote_state();
    my $extglob_depth = 0;
    my $deprecated_arith_depth = 0;
    my $arith_depth = 0;
    my $arith_paren_depth = 0;
    while ($i < length($value)) {
        if ($i > 0 && main::is_extglob_prefix(substr($value, $i - 1, 1)) && substr($value, $i, 1) eq "(" && !main::is_backslash_escaped($value, $i - 1)) {
            $extglob_depth += 1;
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
            next;
        }
        if (substr($value, $i, 1) eq ")" && $extglob_depth > 0) {
            $extglob_depth -= 1;
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
            next;
        }
        if (main::starts_with_at($value, $i, "\$[") && !main::is_backslash_escaped($value, $i)) {
            $deprecated_arith_depth += 1;
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
            next;
        }
        if (substr($value, $i, 1) eq "]" && $deprecated_arith_depth > 0) {
            $deprecated_arith_depth -= 1;
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
            next;
        }
        if (main::is_expansion_start($value, $i, "\$((") && !main::is_backslash_escaped($value, $i) && $has_arith) {
            $arith_depth += 1;
            $arith_paren_depth += 2;
            push(@{$result}, "\$((");
            $i += 3;
            next;
        }
        if ($arith_depth > 0 && $arith_paren_depth == 2 && main::starts_with_at($value, $i, "))")) {
            $arith_depth -= 1;
            $arith_paren_depth -= 2;
            push(@{$result}, "))");
            $i += 2;
            next;
        }
        if ($arith_depth > 0) {
            if (substr($value, $i, 1) eq "(") {
                $arith_paren_depth += 1;
                push(@{$result}, substr($value, $i, 1));
                $i += 1;
                next;
            } elsif (substr($value, $i, 1) eq ")") {
                $arith_paren_depth -= 1;
                push(@{$result}, substr($value, $i, 1));
                $i += 1;
                next;
            }
        }
        my $j = 0;
        if (main::is_expansion_start($value, $i, "\$((") && !$has_arith) {
            $j = main::find_cmdsub_end($value, $i + 2);
            push(@{$result}, main::substring($value, $i, $j));
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
        if (main::starts_with_at($value, $i, "\$(") && !main::starts_with_at($value, $i, "\$((") && !main::is_backslash_escaped($value, $i) && !main::is_dollar_dollar_paren($value, $i)) {
            $j = main::find_cmdsub_end($value, $i + 2);
            if ($extglob_depth > 0) {
                push(@{$result}, main::substring($value, $i, $j));
                if ($cmdsub_idx < scalar(@{$cmdsub_parts})) {
                    $cmdsub_idx += 1;
                }
                $i = $j;
                next;
            }
            $inner = main::substring($value, $i + 2, $j - 1);
            if ($cmdsub_idx < scalar(@{$cmdsub_parts})) {
                $node = $cmdsub_parts->[$cmdsub_idx];
                $formatted = main::format_cmdsub_node($node->{command}, 0, 0, 0, 0);
                $cmdsub_idx += 1;
            } else {
                eval {
                    $parser = main::new_parser($inner, 0, 0);
                    $parsed = $parser->parse_list(1);
                    $formatted = (defined($parsed) ? main::format_cmdsub_node($parsed, 0, 0, 0, 0) : "");
                };
                if (my $_e = $@) {
                    $formatted = $inner;
                }
            }
            if ((index($formatted, "(") == 0)) {
                push(@{$result}, "\$( " . $formatted . ")");
            } else {
                push(@{$result}, "\$(" . $formatted . ")");
            }
            $i = $j;
        } elsif (substr($value, $i, 1) eq "`" && $cmdsub_idx < scalar(@{$cmdsub_parts})) {
            $j = $i + 1;
            while ($j < length($value)) {
                if (substr($value, $j, 1) eq "\\" && $j + 1 < length($value)) {
                    $j += 2;
                    next;
                }
                if (substr($value, $j, 1) eq "`") {
                    $j += 1;
                    last;
                }
                $j += 1;
            }
            push(@{$result}, main::substring($value, $i, $j));
            $cmdsub_idx += 1;
            $i = $j;
        } elsif (main::is_expansion_start($value, $i, "\${") && $i + 2 < length($value) && main::is_funsub_char(substr($value, $i + 2, 1)) && !main::is_backslash_escaped($value, $i)) {
            $j = main::find_funsub_end($value, $i + 2);
            $cmdsub_node = ($cmdsub_idx < scalar(@{$cmdsub_parts}) ? $cmdsub_parts->[$cmdsub_idx] : undef);
            if ((ref($cmdsub_node) eq 'CommandSubstitution') && $cmdsub_node->{brace}) {
                $node = $cmdsub_node;
                $formatted = main::format_cmdsub_node($node->{command}, 0, 0, 0, 0);
                $has_pipe = substr($value, $i + 2, 1) eq "|";
                $prefix = ($has_pipe ? "\${|" : "\${ ");
                $orig_inner = main::substring($value, $i + 2, $j - 1);
                $ends_with_newline = (substr($orig_inner, -length("\n")) eq "\n");
                my $suffix = "";
                if (!(length($formatted) > 0) || ($formatted =~ /^\s$/)) {
                    $suffix = "}";
                } elsif ((substr($formatted, -length("&")) eq "&") || (substr($formatted, -length("& ")) eq "& ")) {
                    $suffix = ((substr($formatted, -length("&")) eq "&") ? " }" : "}");
                } elsif ($ends_with_newline) {
                    $suffix = "\n }";
                } else {
                    $suffix = "; }";
                }
                push(@{$result}, $prefix . $formatted . $suffix);
                $cmdsub_idx += 1;
            } else {
                push(@{$result}, main::substring($value, $i, $j));
            }
            $i = $j;
        } elsif ((main::starts_with_at($value, $i, ">(") || main::starts_with_at($value, $i, "<(")) && !$main_quote->{double} && $deprecated_arith_depth == 0 && $arith_depth == 0) {
            $is_procsub = $i == 0 || !(substr($value, $i - 1, 1) =~ /^[a-zA-Z0-9]$/) && ((index("\"'", substr($value, $i - 1, 1)) == -1));
            if ($extglob_depth > 0) {
                $j = main::find_cmdsub_end($value, $i + 2);
                push(@{$result}, main::substring($value, $i, $j));
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
                $direction = substr($value, $i, 1);
                $j = main::find_cmdsub_end($value, $i + 2);
                $node = $procsub_parts->[$procsub_idx];
                $compact = main::starts_with_subshell($node->{command});
                $formatted = main::format_cmdsub_node($node->{command}, 0, 1, $compact, 1);
                $raw_content = main::substring($value, $i + 2, $j - 1);
                if ($node->{command}->{kind} eq "subshell") {
                    $leading_ws_end = 0;
                    while ($leading_ws_end < length($raw_content) && ((index(" \t\n", substr($raw_content, $leading_ws_end, 1)) >= 0))) {
                        $leading_ws_end += 1;
                    }
                    $leading_ws = substr($raw_content, 0, $leading_ws_end - 0);
                    $stripped = substr($raw_content, $leading_ws_end);
                    if ((index($stripped, "(") == 0)) {
                        if ((length($leading_ws) > 0)) {
                            $normalized_ws = (($leading_ws =~ s/\n/ /gr) =~ s/\t/ /gr);
                            $spaced = main::format_cmdsub_node($node->{command}, 0, 0, 0, 0);
                            push(@{$result}, $direction . "(" . $normalized_ws . $spaced . ")");
                        } else {
                            $raw_content = ($raw_content =~ s/\\\n//gr);
                            push(@{$result}, $direction . "(" . $raw_content . ")");
                        }
                        $procsub_idx += 1;
                        $i = $j;
                        next;
                    }
                }
                $raw_content = main::substring($value, $i + 2, $j - 1);
                $raw_stripped = ($raw_content =~ s/\\\n//gr);
                if (main::starts_with_subshell($node->{command}) && $formatted ne $raw_stripped) {
                    push(@{$result}, $direction . "(" . $raw_stripped . ")");
                } else {
                    $final_output = $direction . "(" . $formatted . ")";
                    push(@{$result}, $final_output);
                }
                $procsub_idx += 1;
                $i = $j;
            } elsif ($is_procsub && (scalar(@{$self->{parts}}) ? 1 : 0)) {
                $direction = substr($value, $i, 1);
                $j = main::find_cmdsub_end($value, $i + 2);
                if ($j > length($value) || $j > 0 && $j <= length($value) && substr($value, $j - 1, 1) ne ")") {
                    push(@{$result}, substr($value, $i, 1));
                    $i += 1;
                    next;
                }
                $inner = main::substring($value, $i + 2, $j - 1);
                eval {
                    $parser = main::new_parser($inner, 0, 0);
                    $parsed = $parser->parse_list(1);
                    if (defined($parsed) && $parser->{pos_} == length($inner) && ((index($inner, "\n") == -1))) {
                        $compact = main::starts_with_subshell($parsed);
                        $formatted = main::format_cmdsub_node($parsed, 0, 1, $compact, 1);
                    } else {
                        $formatted = $inner;
                    }
                };
                if (my $_e = $@) {
                    $formatted = $inner;
                }
                push(@{$result}, $direction . "(" . $formatted . ")");
                $i = $j;
            } elsif ($is_procsub) {
                $direction = substr($value, $i, 1);
                $j = main::find_cmdsub_end($value, $i + 2);
                if ($j > length($value) || $j > 0 && $j <= length($value) && substr($value, $j - 1, 1) ne ")") {
                    push(@{$result}, substr($value, $i, 1));
                    $i += 1;
                    next;
                }
                $inner = main::substring($value, $i + 2, $j - 1);
                if ($in_arith) {
                    push(@{$result}, $direction . "(" . $inner . ")");
                } elsif ((length(($inner =~ s/^\s+|\s+$//gr)) > 0)) {
                    $stripped = ($inner =~ s/^[ \t]+//r);
                    push(@{$result}, $direction . "(" . $stripped . ")");
                } else {
                    push(@{$result}, $direction . "(" . $inner . ")");
                }
                $i = $j;
            } else {
                push(@{$result}, substr($value, $i, 1));
                $i += 1;
            }
        } elsif ((main::is_expansion_start($value, $i, "\${ ") || main::is_expansion_start($value, $i, "\${\t") || main::is_expansion_start($value, $i, "\${\n") || main::is_expansion_start($value, $i, "\${|")) && !main::is_backslash_escaped($value, $i)) {
            $prefix = ((main::substring($value, $i, $i + 3) =~ s/\t/ /gr) =~ s/\n/ /gr);
            $j = $i + 3;
            $depth = 1;
            while ($j < length($value) && $depth > 0) {
                if (substr($value, $j, 1) eq "{") {
                    $depth += 1;
                } elsif (substr($value, $j, 1) eq "}") {
                    $depth -= 1;
                }
                $j += 1;
            }
            $inner = main::substring($value, $i + 2, $j - 1);
            if (($inner =~ s/^\s+|\s+$//gr) eq "") {
                push(@{$result}, "\${ }");
            } else {
                eval {
                    $parser = main::new_parser(($inner =~ s/^[ \t\n|]+//r), 0, 0);
                    $parsed = $parser->parse_list(1);
                    if (defined($parsed)) {
                        $formatted = main::format_cmdsub_node($parsed, 0, 0, 0, 0);
                        $formatted = ($formatted =~ s/[;]+$//r);
                        my $terminator = "";
                        if ((substr(($inner =~ s/[ \t]+$//r), -length("\n")) eq "\n")) {
                            $terminator = "\n }";
                        } elsif ((substr($formatted, -length(" &")) eq " &")) {
                            $terminator = " }";
                        } else {
                            $terminator = "; }";
                        }
                        push(@{$result}, $prefix . $formatted . $terminator);
                    } else {
                        push(@{$result}, "\${ }");
                    }
                };
                if (my $_e = $@) {
                    push(@{$result}, main::substring($value, $i, $j));
                }
            }
            $i = $j;
        } elsif (main::is_expansion_start($value, $i, "\${") && !main::is_backslash_escaped($value, $i)) {
            $j = $i + 2;
            $depth = 1;
            $brace_quote = main::new_quote_state();
            while ($j < length($value) && $depth > 0) {
                $c = substr($value, $j, 1);
                if ($c eq "\\" && $j + 1 < length($value) && !$brace_quote->{single}) {
                    $j += 2;
                    next;
                }
                if ($c eq "'" && !$brace_quote->{double}) {
                    $brace_quote->{single} = !$brace_quote->{single};
                } elsif ($c eq "\"" && !$brace_quote->{single}) {
                    $brace_quote->{double} = !$brace_quote->{double};
                } elsif (!$brace_quote->in_quotes()) {
                    if (main::is_expansion_start($value, $j, "\$(") && !main::starts_with_at($value, $j, "\$((")) {
                        $j = main::find_cmdsub_end($value, $j + 2);
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
                $inner = main::substring($value, $i + 2, $j);
            } else {
                $inner = main::substring($value, $i + 2, $j - 1);
            }
            $formatted_inner = $self->format_command_substitutions($inner, 0);
            $formatted_inner = $self->normalize_extglob_whitespace($formatted_inner);
            if ($depth == 0) {
                push(@{$result}, "\${" . $formatted_inner . "}");
            } else {
                push(@{$result}, "\${" . $formatted_inner);
            }
            $i = $j;
        } elsif (substr($value, $i, 1) eq "\"") {
            $main_quote->{double} = !$main_quote->{double};
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
        } elsif (substr($value, $i, 1) eq "'" && !$main_quote->{double}) {
            $j = $i + 1;
            while ($j < length($value) && substr($value, $j, 1) ne "'") {
                $j += 1;
            }
            if ($j < length($value)) {
                $j += 1;
            }
            push(@{$result}, main::substring($value, $i, $j));
            $i = $j;
        } else {
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
        }
    }
    return join("", @{$result});
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
    my $extglob_quote = main::new_quote_state();
    my $deprecated_arith_depth = 0;
    while ($i < length($value)) {
        if (substr($value, $i, 1) eq "\"") {
            $extglob_quote->{double} = !$extglob_quote->{double};
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
            next;
        }
        if (main::starts_with_at($value, $i, "\$[") && !main::is_backslash_escaped($value, $i)) {
            $deprecated_arith_depth += 1;
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
            next;
        }
        if (substr($value, $i, 1) eq "]" && $deprecated_arith_depth > 0) {
            $deprecated_arith_depth -= 1;
            push(@{$result}, substr($value, $i, 1));
            $i += 1;
            next;
        }
        if ($i + 1 < length($value) && substr($value, $i + 1, 1) eq "(") {
            $prefix_char = substr($value, $i, 1);
            if (((index("><", $prefix_char) >= 0)) && !$extglob_quote->{double} && $deprecated_arith_depth == 0) {
                push(@{$result}, $prefix_char);
                push(@{$result}, "(");
                $i += 2;
                $depth = 1;
                $pattern_parts = [];
                $current_part = [];
                $has_pipe = 0;
                while ($i < length($value) && $depth > 0) {
                    if (substr($value, $i, 1) eq "\\" && $i + 1 < length($value)) {
                        push(@{$current_part}, substr($value, $i, $i + 2 - $i));
                        $i += 2;
                        next;
                    } elsif (substr($value, $i, 1) eq "(") {
                        $depth += 1;
                        push(@{$current_part}, substr($value, $i, 1));
                        $i += 1;
                    } elsif (substr($value, $i, 1) eq ")") {
                        $depth -= 1;
                        if ($depth == 0) {
                            $part_content = join("", @{$current_part});
                            if ((index($part_content, "<<") >= 0)) {
                                push(@{$pattern_parts}, $part_content);
                            } elsif ($has_pipe) {
                                push(@{$pattern_parts}, ($part_content =~ s/^\s+|\s+$//gr));
                            } else {
                                push(@{$pattern_parts}, $part_content);
                            }
                            last;
                        }
                        push(@{$current_part}, substr($value, $i, 1));
                        $i += 1;
                    } elsif (substr($value, $i, 1) eq "|" && $depth == 1) {
                        if ($i + 1 < length($value) && substr($value, $i + 1, 1) eq "|") {
                            push(@{$current_part}, "||");
                            $i += 2;
                        } else {
                            $has_pipe = 1;
                            $part_content = join("", @{$current_part});
                            if ((index($part_content, "<<") >= 0)) {
                                push(@{$pattern_parts}, $part_content);
                            } else {
                                push(@{$pattern_parts}, ($part_content =~ s/^\s+|\s+$//gr));
                            }
                            $current_part = [];
                            $i += 1;
                        }
                    } else {
                        push(@{$current_part}, substr($value, $i, 1));
                        $i += 1;
                    }
                }
                push(@{$result}, join(" | ", @{$pattern_parts}));
                if ($depth == 0) {
                    push(@{$result}, ")");
                    $i += 1;
                }
                next;
            }
        }
        push(@{$result}, substr($value, $i, 1));
        $i += 1;
    }
    return join("", @{$result});
}

sub get_cond_formatted_value ($self) {
    my $value = $self->expand_all_ansi_c_quotes($self->{value});
    $value = $self->strip_locale_string_dollars($value);
    $value = $self->format_command_substitutions($value, 0);
    $value = $self->normalize_extglob_whitespace($value);
    $value = ($value =~ s/\x{01}/\x{01}\x{01}/gr);
    return ($value =~ s/[\n]+$//r);
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Command;

sub new ($class, $words=undef, $redirects=undef, $kind=undef) {
    return bless { words => $words, redirects => $redirects, kind => $kind }, $class;
}

sub words ($self) { $self->{words} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $parts = [];
    for my $w (@{($self->{words} // [])}) {
        push(@{$parts}, $w->to_sexp());
    }
    for my $r (@{($self->{redirects} // [])}) {
        push(@{$parts}, $r->to_sexp());
    }
    my $inner = join(" ", @{$parts});
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

sub new ($class, $commands=undef, $kind=undef) {
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
        $needs_redirect = $i + 1 < scalar(@{$self->{commands}}) && $self->{commands}->[$i + 1]->{kind} eq "pipe-both";
        push(@{$cmds}, [$cmd, $needs_redirect]);
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
        if ($needs && $cmd->{kind} ne "command") {
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
            push(@{$parts}, $w->to_sexp());
        }
        for my $r (@{($cmd->{redirects} // [])}) {
            push(@{$parts}, $r->to_sexp());
        }
        push(@{$parts}, "(redirect \">&\" 1)");
        return "(command " . join(" ", @{$parts}) . ")";
    }
    return $cmd->to_sexp();
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package List;

sub new ($class, $parts=undef, $kind=undef) {
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
    my $parts = [@{$self->{parts}}];
    my $op_names = {"&&" => "and", "||" => "or", ";" => "semi", "\n" => "semi", "&" => "background"};
    while (scalar(@{$parts}) > 1 && $parts->[-1]->{kind} eq "operator" && ($parts->[-1]->{op} eq ";" || $parts->[-1]->{op} eq "\n")) {
        $parts = main::sublist($parts, 0, scalar(@{$parts}) - 1);
    }
    if (scalar(@{$parts}) == 1) {
        return $parts->[0]->to_sexp();
    }
    if ($parts->[-1]->{kind} eq "operator" && $parts->[-1]->{op} eq "&") {
        for (my $i = scalar(@{$parts}) - 3; $i > 0; $i += -2) {
            if ($parts->[$i]->{kind} eq "operator" && ($parts->[$i]->{op} eq ";" || $parts->[$i]->{op} eq "\n")) {
                $left = main::sublist($parts, 0, $i);
                $right = main::sublist($parts, $i + 1, scalar(@{$parts}) - 1);
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
        $inner_parts = main::sublist($parts, 0, scalar(@{$parts}) - 1);
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
        if ($parts->[$i]->{kind} eq "operator" && ($parts->[$i]->{op} eq ";" || $parts->[$i]->{op} eq "\n")) {
            push(@{$semi_positions}, $i);
        }
    }
    if ((scalar(@{($semi_positions // [])}) > 0)) {
        $segments = [];
        $start = 0;
        my $seg = undef;
        for my $pos_ (@{$semi_positions}) {
            $seg = main::sublist($parts, $start, $pos_);
            if ((scalar(@{($seg // [])}) > 0) && $seg->[0]->{kind} ne "operator") {
                push(@{$segments}, $seg);
            }
            $start = $pos_ + 1;
        }
        $seg = main::sublist($parts, $start, scalar(@{$parts}));
        if ((scalar(@{($seg // [])}) > 0) && $seg->[0]->{kind} ne "operator") {
            push(@{$segments}, $seg);
        }
        if (!(scalar(@{($segments // [])}) > 0)) {
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
        if ($parts->[$i]->{kind} eq "operator" && $parts->[$i]->{op} eq "&") {
            push(@{$amp_positions}, $i);
        }
    }
    if ((scalar(@{($amp_positions // [])}) > 0)) {
        $segments = [];
        $start = 0;
        for my $pos_ (@{$amp_positions}) {
            push(@{$segments}, main::sublist($parts, $start, $pos_));
            $start = $pos_ + 1;
        }
        push(@{$segments}, main::sublist($parts, $start, scalar(@{$parts})));
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
        $op_name = ($op_names->{$op->{op}} // $op->{op});
        $result = "(" . $op_name . " " . $result . " " . $cmd->to_sexp() . ")";
    }
    return $result;
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Operator;

sub new ($class, $op=undef, $kind=undef) {
    return bless { op => $op, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $names = {"&&" => "and", "||" => "or", ";" => "semi", "&" => "bg", "|" => "pipe"};
    return "(" . ($names->{$self->{op}} // $self->{op}) . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package PipeBoth;

sub new ($class, $kind=undef) {
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

sub new ($class, $kind=undef) {
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

sub new ($class, $text=undef, $kind=undef) {
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

sub new ($class, $op=undef, $target=undef, $fd=undef, $kind=undef) {
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
    my $op = ($self->{op} =~ s/^[0123456789]+//r);
    if ((index($op, "{") == 0)) {
        $j = 1;
        if ($j < length($op) && ((substr($op, $j, 1) =~ /^[a-zA-Z]$/) || substr($op, $j, 1) eq "_")) {
            $j += 1;
            while ($j < length($op) && ((substr($op, $j, 1) =~ /^[a-zA-Z0-9]$/) || substr($op, $j, 1) eq "_")) {
                $j += 1;
            }
            if ($j < length($op) && substr($op, $j, 1) eq "[") {
                $j += 1;
                while ($j < length($op) && substr($op, $j, 1) ne "]") {
                    $j += 1;
                }
                if ($j < length($op) && substr($op, $j, 1) eq "]") {
                    $j += 1;
                }
            }
            if ($j < length($op) && substr($op, $j, 1) eq "}") {
                $op = main::substring($op, $j + 1, length($op));
            }
        }
    }
    my $target_val = $self->{target}->{value};
    $target_val = $self->{target}->expand_all_ansi_c_quotes($target_val);
    $target_val = $self->{target}->strip_locale_string_dollars($target_val);
    $target_val = $self->{target}->format_command_substitutions($target_val, 0);
    $target_val = $self->{target}->strip_arith_line_continuations($target_val);
    if ((substr($target_val, -length("\\")) eq "\\") && !(substr($target_val, -length("\\\\")) eq "\\\\")) {
        $target_val = $target_val . "\\";
    }
    if ((index($target_val, "&") == 0)) {
        if ($op eq ">") {
            $op = ">&";
        } elsif ($op eq "<") {
            $op = "<&";
        }
        $raw = main::substring($target_val, 1, length($target_val));
        if (($raw =~ /^\d$/) && int($raw) <= 2147483647) {
            return "(redirect \"" . $op . "\" " . ("" . int($raw)) . ")";
        }
        if ((substr($raw, -length("-")) eq "-") && (substr($raw, 0, length($raw) - 1 - 0) =~ /^\d$/) && int(substr($raw, 0, length($raw) - 1 - 0)) <= 2147483647) {
            return "(redirect \"" . $op . "\" " . ("" . int(substr($raw, 0, length($raw) - 1 - 0))) . ")";
        }
        if ($target_val eq "&-") {
            return "(redirect \">&-\" 0)";
        }
        $fd_target = ((substr($raw, -length("-")) eq "-") ? substr($raw, 0, length($raw) - 1 - 0) : $raw);
        return "(redirect \"" . $op . "\" \"" . $fd_target . "\")";
    }
    if ($op eq ">&" || $op eq "<&") {
        if (($target_val =~ /^\d$/) && int($target_val) <= 2147483647) {
            return "(redirect \"" . $op . "\" " . ("" . int($target_val)) . ")";
        }
        if ($target_val eq "-") {
            return "(redirect \">&-\" 0)";
        }
        if ((substr($target_val, -length("-")) eq "-") && (substr($target_val, 0, length($target_val) - 1 - 0) =~ /^\d$/) && int(substr($target_val, 0, length($target_val) - 1 - 0)) <= 2147483647) {
            return "(redirect \"" . $op . "\" " . ("" . int(substr($target_val, 0, length($target_val) - 1 - 0))) . ")";
        }
        $out_val = ((substr($target_val, -length("-")) eq "-") ? substr($target_val, 0, length($target_val) - 1 - 0) : $target_val);
        return "(redirect \"" . $op . "\" \"" . $out_val . "\")";
    }
    return "(redirect \"" . $op . "\" \"" . $target_val . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package HereDoc;

sub new ($class, $delimiter=undef, $content=undef, $strip_tabs=undef, $quoted=undef, $fd=undef, $complete=undef, $start_pos=undef, $kind=undef) {
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
    if ((substr($content, -length("\\")) eq "\\") && !(substr($content, -length("\\\\")) eq "\\\\")) {
        $content = $content . "\\";
    }
    return sprintf("(redirect \"%s\" \"%s\")", $op, $content);
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Subshell;

sub new ($class, $body=undef, $redirects=undef, $kind=undef) {
    return bless { body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $base = "(subshell " . $self->{body}->to_sexp() . ")";
    return main::append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package BraceGroup;

sub new ($class, $body=undef, $redirects=undef, $kind=undef) {
    return bless { body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $base = "(brace-group " . $self->{body}->to_sexp() . ")";
    return main::append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package If;

sub new ($class, $condition=undef, $then_body=undef, $else_body=undef, $redirects=undef, $kind=undef) {
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

sub new ($class, $condition=undef, $body=undef, $redirects=undef, $kind=undef) {
    return bless { condition => $condition, body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub condition ($self) { $self->{condition} }
sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $base = "(while " . $self->{condition}->to_sexp() . " " . $self->{body}->to_sexp() . ")";
    return main::append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Until;

sub new ($class, $condition=undef, $body=undef, $redirects=undef, $kind=undef) {
    return bless { condition => $condition, body => $body, redirects => $redirects, kind => $kind }, $class;
}

sub condition ($self) { $self->{condition} }
sub body ($self) { $self->{body} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $base = "(until " . $self->{condition}->to_sexp() . " " . $self->{body}->to_sexp() . ")";
    return main::append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package For;

sub new ($class, $var=undef, $words=undef, $body=undef, $redirects=undef, $kind=undef) {
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
    if ((scalar(@{($self->{redirects} // [])}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            push(@{$redirect_parts}, $r->to_sexp());
        }
        $suffix = " " . join(" ", @{$redirect_parts});
    }
    my $temp_word = Word->new($self->{var}, [], "word");
    my $var_formatted = $temp_word->format_command_substitutions($self->{var}, 0);
    my $var_escaped = (($var_formatted =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
    if (!defined($self->{words})) {
        return "(for (word \"" . $var_escaped . "\") (in (word \"\\\"\$\@\\\"\")) " . $self->{body}->to_sexp() . ")" . $suffix;
    } elsif (scalar(@{$self->{words}}) == 0) {
        return "(for (word \"" . $var_escaped . "\") (in) " . $self->{body}->to_sexp() . ")" . $suffix;
    } else {
        $word_parts = [];
        for my $w (@{($self->{words} // [])}) {
            push(@{$word_parts}, $w->to_sexp());
        }
        $word_strs = join(" ", @{$word_parts});
        return "(for (word \"" . $var_escaped . "\") (in " . $word_strs . ") " . $self->{body}->to_sexp() . ")" . $suffix;
    }
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ForArith;

sub new ($class, $init=undef, $cond=undef, $incr=undef, $body=undef, $redirects=undef, $kind=undef) {
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
    if ((scalar(@{($self->{redirects} // [])}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            push(@{$redirect_parts}, $r->to_sexp());
        }
        $suffix = " " . join(" ", @{$redirect_parts});
    }
    my $init_val = ((length($self->{init}) > 0) ? $self->{init} : "1");
    my $cond_val = ((length($self->{cond}) > 0) ? $self->{cond} : "1");
    my $incr_val = ((length($self->{incr}) > 0) ? $self->{incr} : "1");
    my $init_str = main::format_arith_val($init_val);
    my $cond_str = main::format_arith_val($cond_val);
    my $incr_str = main::format_arith_val($incr_val);
    my $body_str = $self->{body}->to_sexp();
    return sprintf("(arith-for (init (word \"%s\")) (test (word \"%s\")) (step (word \"%s\")) %s)%s", $init_str, $cond_str, $incr_str, $body_str, $suffix);
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Select;

sub new ($class, $var=undef, $words=undef, $body=undef, $redirects=undef, $kind=undef) {
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
    if ((scalar(@{($self->{redirects} // [])}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            push(@{$redirect_parts}, $r->to_sexp());
        }
        $suffix = " " . join(" ", @{$redirect_parts});
    }
    my $var_escaped = (($self->{var} =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
    my $in_clause = "";
    if (defined($self->{words})) {
        $word_parts = [];
        for my $w (@{($self->{words} // [])}) {
            push(@{$word_parts}, $w->to_sexp());
        }
        $word_strs = join(" ", @{$word_parts});
        if ((scalar(@{($self->{words} // [])}) > 0)) {
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

sub new ($class, $word=undef, $patterns=undef, $redirects=undef, $kind=undef) {
    return bless { word => $word, patterns => $patterns, redirects => $redirects, kind => $kind }, $class;
}

sub word ($self) { $self->{word} }
sub patterns ($self) { $self->{patterns} }
sub redirects ($self) { $self->{redirects} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $parts = [];
    push(@{$parts}, "(case " . $self->{word}->to_sexp());
    for my $p (@{($self->{patterns} // [])}) {
        push(@{$parts}, $p->to_sexp());
    }
    my $base = join(" ", @{$parts}) . ")";
    return main::append_redirects($base, $self->{redirects});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package CasePattern;

sub new ($class, $pattern=undef, $body=undef, $terminator=undef, $kind=undef) {
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
        $ch = substr($self->{pattern}, $i, 1);
        if ($ch eq "\\" && $i + 1 < length($self->{pattern})) {
            push(@{$current}, main::substring($self->{pattern}, $i, $i + 2));
            $i += 2;
        } elsif (($ch eq "\@" || $ch eq "?" || $ch eq "*" || $ch eq "+" || $ch eq "!") && $i + 1 < length($self->{pattern}) && substr($self->{pattern}, $i + 1, 1) eq "(") {
            push(@{$current}, $ch);
            push(@{$current}, "(");
            $depth += 1;
            $i += 2;
        } elsif (main::is_expansion_start($self->{pattern}, $i, "\$(")) {
            push(@{$current}, $ch);
            push(@{$current}, "(");
            $depth += 1;
            $i += 2;
        } elsif ($ch eq "(" && $depth > 0) {
            push(@{$current}, $ch);
            $depth += 1;
            $i += 1;
        } elsif ($ch eq ")" && $depth > 0) {
            push(@{$current}, $ch);
            $depth -= 1;
            $i += 1;
        } elsif ($ch eq "[") {
            ($result0, $result1, $result2) = @{main::consume_bracket_class($self->{pattern}, $i, $depth)};
            $i = $result0;
            push(@{$current}, @{$result1});
        } elsif ($ch eq "'" && $depth == 0) {
            ($result0, $result1) = @{main::consume_single_quote($self->{pattern}, $i)};
            $i = $result0;
            push(@{$current}, @{$result1});
        } elsif ($ch eq "\"" && $depth == 0) {
            ($result0, $result1) = @{main::consume_double_quote($self->{pattern}, $i)};
            $i = $result0;
            push(@{$current}, @{$result1});
        } elsif ($ch eq "|" && $depth == 0) {
            push(@{$alternatives}, join("", @{$current}));
            $current = [];
            $i += 1;
        } else {
            push(@{$current}, $ch);
            $i += 1;
        }
    }
    push(@{$alternatives}, join("", @{$current}));
    my $word_list = [];
    for my $alt (@{$alternatives}) {
        push(@{$word_list}, Word->new($alt, undef, "word")->to_sexp());
    }
    my $pattern_str = join(" ", @{$word_list});
    my $parts = ["(pattern (" . $pattern_str . ")"];
    if (defined($self->{body})) {
        push(@{$parts}, " " . $self->{body}->to_sexp());
    } else {
        push(@{$parts}, " ()");
    }
    push(@{$parts}, ")");
    return join("", @{$parts});
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Function;

sub new ($class, $name=undef, $body=undef, $kind=undef) {
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

sub new ($class, $param=undef, $op=undef, $arg=undef, $kind=undef) {
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
    my $escaped_param = (($self->{param} =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
    if ($self->{op} ne "") {
        $escaped_op = (($self->{op} =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
        my $arg_val = "";
        if ($self->{arg} ne "") {
            $arg_val = $self->{arg};
        } else {
            $arg_val = "";
        }
        $escaped_arg = (($arg_val =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
        return "(param \"" . $escaped_param . "\" \"" . $escaped_op . "\" \"" . $escaped_arg . "\")";
    }
    return "(param \"" . $escaped_param . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ParamLength;

sub new ($class, $param=undef, $kind=undef) {
    return bless { param => $param, kind => $kind }, $class;
}

sub param ($self) { $self->{param} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $escaped = (($self->{param} =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
    return "(param-len \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ParamIndirect;

sub new ($class, $param=undef, $op=undef, $arg=undef, $kind=undef) {
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
    my $escaped = (($self->{param} =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
    if ($self->{op} ne "") {
        $escaped_op = (($self->{op} =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
        my $arg_val = "";
        if ($self->{arg} ne "") {
            $arg_val = $self->{arg};
        } else {
            $arg_val = "";
        }
        $escaped_arg = (($arg_val =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
        return "(param-indirect \"" . $escaped . "\" \"" . $escaped_op . "\" \"" . $escaped_arg . "\")";
    }
    return "(param-indirect \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package CommandSubstitution;

sub new ($class, $command=undef, $brace=undef, $kind=undef) {
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

sub new ($class, $expression=undef, $kind=undef) {
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

sub new ($class, $expression=undef, $redirects=undef, $raw_content=undef, $kind=undef) {
    return bless { expression => $expression, redirects => $redirects, raw_content => $raw_content, kind => $kind }, $class;
}

sub expression ($self) { $self->{expression} }
sub redirects ($self) { $self->{redirects} }
sub raw_content ($self) { $self->{raw_content} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $redirect_parts;
    my $redirect_sexps;
    my $formatted = Word->new($self->{raw_content}, undef, "word")->format_command_substitutions($self->{raw_content}, 1);
    my $escaped = (((($formatted =~ s/\\/\\\\/gr) =~ s/"/\\"/gr) =~ s/\n/\\n/gr) =~ s/\t/\\t/gr);
    my $result = "(arith (word \"" . $escaped . "\"))";
    if ((scalar(@{($self->{redirects} // [])}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            push(@{$redirect_parts}, $r->to_sexp());
        }
        $redirect_sexps = join(" ", @{$redirect_parts});
        return $result . " " . $redirect_sexps;
    }
    return $result;
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithNumber;

sub new ($class, $value=undef, $kind=undef) {
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

sub new ($class, $kind=undef) {
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

sub new ($class, $name=undef, $kind=undef) {
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

sub new ($class, $op=undef, $left=undef, $right=undef, $kind=undef) {
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

sub new ($class, $op=undef, $operand=undef, $kind=undef) {
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

sub new ($class, $operand=undef, $kind=undef) {
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

sub new ($class, $operand=undef, $kind=undef) {
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

sub new ($class, $operand=undef, $kind=undef) {
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

sub new ($class, $operand=undef, $kind=undef) {
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

sub new ($class, $op=undef, $target=undef, $value=undef, $kind=undef) {
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

sub new ($class, $condition=undef, $if_true=undef, $if_false=undef, $kind=undef) {
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

sub new ($class, $left=undef, $right=undef, $kind=undef) {
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

sub new ($class, $array=undef, $index_=undef, $kind=undef) {
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

sub new ($class, $char=undef, $kind=undef) {
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

sub new ($class, $expression=undef, $kind=undef) {
    return bless { expression => $expression, kind => $kind }, $class;
}

sub expression ($self) { $self->{expression} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $escaped = ((($self->{expression} =~ s/\\/\\\\/gr) =~ s/"/\\"/gr) =~ s/\n/\\n/gr);
    return "(arith-deprecated \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ArithConcat;

sub new ($class, $parts=undef, $kind=undef) {
    return bless { parts => $parts, kind => $kind }, $class;
}

sub parts ($self) { $self->{parts} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $sexps = [];
    for my $p (@{($self->{parts} // [])}) {
        push(@{$sexps}, $p->to_sexp());
    }
    return "(arith-concat " . join(" ", @{$sexps}) . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package AnsiCQuote;

sub new ($class, $content=undef, $kind=undef) {
    return bless { content => $content, kind => $kind }, $class;
}

sub content ($self) { $self->{content} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $escaped = ((($self->{content} =~ s/\\/\\\\/gr) =~ s/"/\\"/gr) =~ s/\n/\\n/gr);
    return "(ansi-c \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package LocaleString;

sub new ($class, $content=undef, $kind=undef) {
    return bless { content => $content, kind => $kind }, $class;
}

sub content ($self) { $self->{content} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $escaped = ((($self->{content} =~ s/\\/\\\\/gr) =~ s/"/\\"/gr) =~ s/\n/\\n/gr);
    return "(locale \"" . $escaped . "\")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package ProcessSubstitution;

sub new ($class, $direction=undef, $command=undef, $kind=undef) {
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

sub new ($class, $pipeline=undef, $kind=undef) {
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

sub new ($class, $pipeline=undef, $posix=undef, $kind=undef) {
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

sub new ($class, $body=undef, $redirects=undef, $kind=undef) {
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
        $escaped = ((($body =~ s/\\/\\\\/gr) =~ s/"/\\"/gr) =~ s/\n/\\n/gr);
        $result = "(cond \"" . $escaped . "\")";
    } else {
        $result = "(cond " . $body->to_sexp() . ")";
    }
    if ((scalar(@{($self->{redirects} // [])}) > 0)) {
        $redirect_parts = [];
        for my $r (@{($self->{redirects} // [])}) {
            push(@{$redirect_parts}, $r->to_sexp());
        }
        $redirect_sexps = join(" ", @{$redirect_parts});
        return $result . " " . $redirect_sexps;
    }
    return $result;
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package UnaryTest;

sub new ($class, $op=undef, $operand=undef, $kind=undef) {
    return bless { op => $op, operand => $operand, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub operand ($self) { $self->{operand} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $operand_val = $self->{operand}->get_cond_formatted_value();
    return "(cond-unary \"" . $self->{op} . "\" (cond-term \"" . $operand_val . "\"))";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package BinaryTest;

sub new ($class, $op=undef, $left=undef, $right=undef, $kind=undef) {
    return bless { op => $op, left => $left, right => $right, kind => $kind }, $class;
}

sub op ($self) { $self->{op} }
sub left ($self) { $self->{left} }
sub right ($self) { $self->{right} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    my $left_val = $self->{left}->get_cond_formatted_value();
    my $right_val = $self->{right}->get_cond_formatted_value();
    return "(cond-binary \"" . $self->{op} . "\" (cond-term \"" . $left_val . "\") (cond-term \"" . $right_val . "\"))";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package CondAnd;

sub new ($class, $left=undef, $right=undef, $kind=undef) {
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

sub new ($class, $left=undef, $right=undef, $kind=undef) {
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

sub new ($class, $operand=undef, $kind=undef) {
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

sub new ($class, $inner=undef, $kind=undef) {
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

sub new ($class, $elements=undef, $kind=undef) {
    return bless { elements => $elements, kind => $kind }, $class;
}

sub elements ($self) { $self->{elements} }
sub kind ($self) { $self->{kind} }

sub to_sexp ($self) {
    if (!(scalar(@{($self->{elements} // [])}) > 0)) {
        return "(array)";
    }
    my $parts = [];
    for my $e (@{($self->{elements} // [])}) {
        push(@{$parts}, $e->to_sexp());
    }
    my $inner = join(" ", @{$parts});
    return "(array " . $inner . ")";
}

sub get_kind ($self) {
    return $self->{kind};
}

1;

package Coproc;

sub new ($class, $command=undef, $name=undef, $kind=undef) {
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

sub new ($class, $source=undef, $pos_=undef, $length_=undef, $pending_heredocs=undef, $cmdsub_heredoc_end=undef, $saw_newline_in_single_quote=undef, $in_process_sub=undef, $extglob=undef, $ctx=undef, $lexer=undef, $token_history=undef, $parser_state=undef, $dolbrace_state=undef, $eof_token=undef, $word_context=undef, $at_command_start=undef, $in_array_literal=undef, $in_assign_builtin=undef, $arith_src=undef, $arith_pos=undef, $arith_len=undef) {
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
    if ($self->{dolbrace_state} == main::DOLBRACESTATE_NONE()) {
        return;
    }
    if ($op eq "" || length($op) == 0) {
        return;
    }
    my $first_char = substr($op, 0, 1);
    if ($self->{dolbrace_state} == main::DOLBRACESTATE_PARAM() && $has_param) {
        if ((index("%#^,", $first_char) >= 0)) {
            $self->{dolbrace_state} = main::DOLBRACESTATE_QUOTE();
            return;
        }
        if ($first_char eq "/") {
            $self->{dolbrace_state} = main::DOLBRACESTATE_QUOTE2();
            return;
        }
    }
    if ($self->{dolbrace_state} == main::DOLBRACESTATE_PARAM()) {
        if ((index("#%^,~:-=?+/", $first_char) >= 0)) {
            $self->{dolbrace_state} = main::DOLBRACESTATE_OP();
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
    return $t == main::TOKENTYPE_EOF() || $t == main::TOKENTYPE_NEWLINE() || $t == main::TOKENTYPE_PIPE() || $t == main::TOKENTYPE_SEMI() || $t == main::TOKENTYPE_LPAREN() || $t == main::TOKENTYPE_RPAREN() || $t == main::TOKENTYPE_AMP();
}

sub lex_peek_operator ($self) {
    my $tok = $self->lex_peek_token();
    my $t = $tok->{type};
    if ($t >= main::TOKENTYPE_SEMI() && $t <= main::TOKENTYPE_GREATER() || $t >= main::TOKENTYPE_AND_AND() && $t <= main::TOKENTYPE_PIPE_AMP()) {
        return [$t, $tok->{value}];
    }
    return [0, ""];
}

sub lex_peek_reserved_word ($self) {
    my $tok = $self->lex_peek_token();
    if ($tok->{type} != main::TOKENTYPE_WORD()) {
        return "";
    }
    my $word = $tok->{value};
    if ((substr($word, -length("\\\n")) eq "\\\n")) {
        $word = substr($word, 0, length($word) - 2 - 0);
    }
    if ((exists(main::RESERVED_WORDS()->{$word})) || $word eq "{" || $word eq "}" || $word eq "[[" || $word eq "]]" || $word eq "!" || $word eq "time") {
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
    if ($tok->{type} != main::TOKENTYPE_WORD()) {
        return 0;
    }
    my $word = $tok->{value};
    if ((substr($word, -length("\\\n")) eq "\\\n")) {
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
    if ($t == main::TOKENTYPE_SEMI_SEMI()) {
        return ";;";
    }
    if ($t == main::TOKENTYPE_SEMI_AMP()) {
        return ";&";
    }
    if ($t == main::TOKENTYPE_SEMI_SEMI_AMP()) {
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
    return substr($self->{source}, $self->{pos_}, 1);
}

sub advance ($self) {
    if ($self->at_end()) {
        return "";
    }
    my $ch = substr($self->{source}, $self->{pos_}, 1);
    $self->{pos_} += 1;
    return $ch;
}

sub peek_at ($self, $offset) {
    my $pos_ = $self->{pos_} + $offset;
    if ($pos_ < 0 || $pos_ >= $self->{length_}) {
        return "";
    }
    return substr($self->{source}, $pos_, 1);
}

sub lookahead ($self, $n) {
    return main::substring($self->{source}, $self->{pos_}, $self->{pos_} + $n);
}

sub is_bang_followed_by_procsub ($self) {
    if ($self->{pos_} + 2 >= $self->{length_}) {
        return 0;
    }
    my $next_char = substr($self->{source}, $self->{pos_} + 1, 1);
    if ($next_char ne ">" && $next_char ne "<") {
        return 0;
    }
    return substr($self->{source}, $self->{pos_} + 2, 1) eq "(";
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
        if (main::is_whitespace($ch)) {
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
        return main::is_word_end_context(substr($self->{source}, $next_pos, 1));
    }
    return 0;
}

sub at_eof_token ($self) {
    if ($self->{eof_token} eq "") {
        return 0;
    }
    my $tok = $self->lex_peek_token();
    if ($self->{eof_token} eq ")") {
        return $tok->{type} == main::TOKENTYPE_RPAREN();
    }
    if ($self->{eof_token} eq "}") {
        return $tok->{type} == main::TOKENTYPE_WORD() && $tok->{value} eq "}";
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
        push(@{$redirects}, $redirect);
    }
    return ((scalar(@{($redirects // [])}) > 0) ? $redirects : undef);
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
    if ($self->at_end() || main::is_metachar($self->peek())) {
        $self->{pos_} = $saved_pos;
        return "";
    }
    my $chars = [];
    while (!$self->at_end() && !main::is_metachar($self->peek())) {
        $ch = $self->peek();
        if (main::is_quote($ch)) {
            last;
        }
        if ($ch eq "\\" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "\n") {
            last;
        }
        if ($ch eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            push(@{$chars}, $self->advance());
            push(@{$chars}, $self->advance());
            next;
        }
        push(@{$chars}, $self->advance());
    }
    my $word = "";
    if ((scalar(@{($chars // [])}) > 0)) {
        $word = join("", @{$chars});
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
    if ($word ne "" && $self->{in_process_sub} && length($word) > 1 && substr($word, 0, 1) eq "}") {
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
    for (split(//, $expected)) {
        $self->advance();
    }
    while ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "\n") {
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
    push(@{$chars}, "\"");
    while (!$self->at_end() && $self->peek() ne "\"") {
        $c = $self->peek();
        if ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $next_c = substr($self->{source}, $self->{pos_} + 1, 1);
            if ($handle_line_continuation && $next_c eq "\n") {
                $self->advance();
                $self->advance();
            } else {
                push(@{$chars}, $self->advance());
                push(@{$chars}, $self->advance());
            }
        } elsif ($c eq "\$") {
            if (!$self->parse_dollar_expansion($chars, $parts, 1)) {
                push(@{$chars}, $self->advance());
            }
        } else {
            push(@{$chars}, $self->advance());
        }
    }
    if ($self->at_end()) {
        die "Unterminated double quote";
    }
    push(@{$chars}, $self->advance());
}

sub parse_dollar_expansion ($self, $chars, $parts, $in_dquote) {
    my $result0;
    my $result1;
    my $result0 = undef;
    my $result1 = "";
    if ($self->{pos_} + 2 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(" && substr($self->{source}, $self->{pos_} + 2, 1) eq "(") {
        ($result0, $result1) = @{$self->parse_arithmetic_expansion()};
        if (defined($result0)) {
            push(@{$parts}, $result0);
            push(@{$chars}, $result1);
            return 1;
        }
        ($result0, $result1) = @{$self->parse_command_substitution()};
        if (defined($result0)) {
            push(@{$parts}, $result0);
            push(@{$chars}, $result1);
            return 1;
        }
        return 0;
    }
    if ($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "[") {
        ($result0, $result1) = @{$self->parse_deprecated_arithmetic()};
        if (defined($result0)) {
            push(@{$parts}, $result0);
            push(@{$chars}, $result1);
            return 1;
        }
        return 0;
    }
    if ($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
        ($result0, $result1) = @{$self->parse_command_substitution()};
        if (defined($result0)) {
            push(@{$parts}, $result0);
            push(@{$chars}, $result1);
            return 1;
        }
        return 0;
    }
    ($result0, $result1) = @{$self->parse_param_expansion($in_dquote)};
    if (defined($result0)) {
        push(@{$parts}, $result0);
        push(@{$chars}, $result1);
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
    if ($tok->{type} != main::TOKENTYPE_WORD()) {
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
    $self->set_state(main::PARSERSTATEFLAGS_PST_CMDSUBST() | main::PARSERSTATEFLAGS_PST_EOFTOKEN());
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
    my $text = main::substring($self->{source}, $start, $text_end);
    $self->restore_parser_state($saved);
    return [CommandSubstitution->new($cmd, 0, "cmdsub"), $text];
}

sub parse_funsub ($self, $start) {
    $self->sync_parser();
    if (!$self->at_end() && $self->peek() eq "|") {
        $self->advance();
    }
    my $saved = $self->save_parser_state();
    $self->set_state(main::PARSERSTATEFLAGS_PST_CMDSUBST() | main::PARSERSTATEFLAGS_PST_EOFTOKEN());
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
    my $text = main::substring($self->{source}, $start, $self->{pos_});
    $self->restore_parser_state($saved);
    $self->sync_lexer();
    return [CommandSubstitution->new($cmd, 1, "cmdsub"), $text];
}

sub is_assignment_word ($self, $word) {
    return main::assignment($word->{value}, 0) != -1;
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
    my $ch = "";
    while (!$self->at_end() && ($in_heredoc_body || $self->peek() ne "`")) {
        if ($in_heredoc_body) {
            $line_start = $self->{pos_};
            $line_end = $line_start;
            while ($line_end < $self->{length_} && substr($self->{source}, $line_end, 1) ne "\n") {
                $line_end += 1;
            }
            $line = main::substring($self->{source}, $line_start, $line_end);
            $check_line = ($current_heredoc_strip ? ($line =~ s/^[\t]+//r) : $line);
            if ($check_line eq $current_heredoc_delim) {
                for my $ch (split(//, $line)) {
                    push(@{$content_chars}, $ch);
                    push(@{$text_chars}, $ch);
                }
                $self->{pos_} = $line_end;
                if ($self->{pos_} < $self->{length_} && substr($self->{source}, $self->{pos_}, 1) eq "\n") {
                    push(@{$content_chars}, "\n");
                    push(@{$text_chars}, "\n");
                    $self->advance();
                }
                $in_heredoc_body = 0;
                if (scalar(@{$pending_heredocs}) > 0) {
                    ($current_heredoc_delim, $current_heredoc_strip) = @{pop(@{$pending_heredocs})};
                    $in_heredoc_body = 1;
                }
            } elsif ((index($check_line, $current_heredoc_delim) == 0) && length($check_line) > length($current_heredoc_delim)) {
                $tabs_stripped = length($line) - length($check_line);
                $end_pos = $tabs_stripped + length($current_heredoc_delim);
                for (my $i = 0; $i < $end_pos; $i += 1) {
                    push(@{$content_chars}, substr($line, $i, 1));
                    push(@{$text_chars}, substr($line, $i, 1));
                }
                $self->{pos_} = $line_start + $end_pos;
                $in_heredoc_body = 0;
                if (scalar(@{$pending_heredocs}) > 0) {
                    ($current_heredoc_delim, $current_heredoc_strip) = @{pop(@{$pending_heredocs})};
                    $in_heredoc_body = 1;
                }
            } else {
                for my $ch (split(//, $line)) {
                    push(@{$content_chars}, $ch);
                    push(@{$text_chars}, $ch);
                }
                $self->{pos_} = $line_end;
                if ($self->{pos_} < $self->{length_} && substr($self->{source}, $self->{pos_}, 1) eq "\n") {
                    push(@{$content_chars}, "\n");
                    push(@{$text_chars}, "\n");
                    $self->advance();
                }
            }
            next;
        }
        $c = $self->peek();
        if ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
            $next_c = substr($self->{source}, $self->{pos_} + 1, 1);
            if ($next_c eq "\n") {
                $self->advance();
                $self->advance();
            } elsif (main::is_escape_char_in_backtick($next_c)) {
                $self->advance();
                $escaped = $self->advance();
                push(@{$content_chars}, $escaped);
                push(@{$text_chars}, "\\");
                push(@{$text_chars}, $escaped);
            } else {
                $ch = $self->advance();
                push(@{$content_chars}, $ch);
                push(@{$text_chars}, $ch);
            }
            next;
        }
        if ($c eq "<" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "<") {
            my $quote = "";
            if ($self->{pos_} + 2 < $self->{length_} && substr($self->{source}, $self->{pos_} + 2, 1) eq "<") {
                push(@{$content_chars}, $self->advance());
                push(@{$text_chars}, "<");
                push(@{$content_chars}, $self->advance());
                push(@{$text_chars}, "<");
                push(@{$content_chars}, $self->advance());
                push(@{$text_chars}, "<");
                while (!$self->at_end() && main::is_whitespace_no_newline($self->peek())) {
                    $ch = $self->advance();
                    push(@{$content_chars}, $ch);
                    push(@{$text_chars}, $ch);
                }
                while (!$self->at_end() && !main::is_whitespace($self->peek()) && ((index("()", $self->peek()) == -1))) {
                    if ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        $ch = $self->advance();
                        push(@{$content_chars}, $ch);
                        push(@{$text_chars}, $ch);
                        $ch = $self->advance();
                        push(@{$content_chars}, $ch);
                        push(@{$text_chars}, $ch);
                    } elsif ((index("\"'", $self->peek()) >= 0)) {
                        $quote = $self->peek();
                        $ch = $self->advance();
                        push(@{$content_chars}, $ch);
                        push(@{$text_chars}, $ch);
                        while (!$self->at_end() && $self->peek() ne $quote) {
                            if ($quote eq "\"" && $self->peek() eq "\\") {
                                $ch = $self->advance();
                                push(@{$content_chars}, $ch);
                                push(@{$text_chars}, $ch);
                            }
                            $ch = $self->advance();
                            push(@{$content_chars}, $ch);
                            push(@{$text_chars}, $ch);
                        }
                        if (!$self->at_end()) {
                            $ch = $self->advance();
                            push(@{$content_chars}, $ch);
                            push(@{$text_chars}, $ch);
                        }
                    } else {
                        $ch = $self->advance();
                        push(@{$content_chars}, $ch);
                        push(@{$text_chars}, $ch);
                    }
                }
                next;
            }
            push(@{$content_chars}, $self->advance());
            push(@{$text_chars}, "<");
            push(@{$content_chars}, $self->advance());
            push(@{$text_chars}, "<");
            $strip_tabs = 0;
            if (!$self->at_end() && $self->peek() eq "-") {
                $strip_tabs = 1;
                push(@{$content_chars}, $self->advance());
                push(@{$text_chars}, "-");
            }
            while (!$self->at_end() && main::is_whitespace_no_newline($self->peek())) {
                $ch = $self->advance();
                push(@{$content_chars}, $ch);
                push(@{$text_chars}, $ch);
            }
            my $delimiter_chars = [];
            if (!$self->at_end()) {
                $ch = $self->peek();
                my $dch = "";
                my $closing = "";
                if (main::is_quote($ch)) {
                    $quote = $self->advance();
                    push(@{$content_chars}, $quote);
                    push(@{$text_chars}, $quote);
                    while (!$self->at_end() && $self->peek() ne $quote) {
                        $dch = $self->advance();
                        push(@{$content_chars}, $dch);
                        push(@{$text_chars}, $dch);
                        push(@{$delimiter_chars}, $dch);
                    }
                    if (!$self->at_end()) {
                        $closing = $self->advance();
                        push(@{$content_chars}, $closing);
                        push(@{$text_chars}, $closing);
                    }
                } elsif ($ch eq "\\") {
                    $esc = $self->advance();
                    push(@{$content_chars}, $esc);
                    push(@{$text_chars}, $esc);
                    if (!$self->at_end()) {
                        $dch = $self->advance();
                        push(@{$content_chars}, $dch);
                        push(@{$text_chars}, $dch);
                        push(@{$delimiter_chars}, $dch);
                    }
                    while (!$self->at_end() && !main::is_metachar($self->peek())) {
                        $dch = $self->advance();
                        push(@{$content_chars}, $dch);
                        push(@{$text_chars}, $dch);
                        push(@{$delimiter_chars}, $dch);
                    }
                } else {
                    while (!$self->at_end() && !main::is_metachar($self->peek()) && $self->peek() ne "`") {
                        $ch = $self->peek();
                        if (main::is_quote($ch)) {
                            $quote = $self->advance();
                            push(@{$content_chars}, $quote);
                            push(@{$text_chars}, $quote);
                            while (!$self->at_end() && $self->peek() ne $quote) {
                                $dch = $self->advance();
                                push(@{$content_chars}, $dch);
                                push(@{$text_chars}, $dch);
                                push(@{$delimiter_chars}, $dch);
                            }
                            if (!$self->at_end()) {
                                $closing = $self->advance();
                                push(@{$content_chars}, $closing);
                                push(@{$text_chars}, $closing);
                            }
                        } elsif ($ch eq "\\") {
                            $esc = $self->advance();
                            push(@{$content_chars}, $esc);
                            push(@{$text_chars}, $esc);
                            if (!$self->at_end()) {
                                $dch = $self->advance();
                                push(@{$content_chars}, $dch);
                                push(@{$text_chars}, $dch);
                                push(@{$delimiter_chars}, $dch);
                            }
                        } else {
                            $dch = $self->advance();
                            push(@{$content_chars}, $dch);
                            push(@{$text_chars}, $dch);
                            push(@{$delimiter_chars}, $dch);
                        }
                    }
                }
            }
            $delimiter = join("", @{$delimiter_chars});
            if ((length($delimiter) > 0)) {
                push(@{$pending_heredocs}, [$delimiter, $strip_tabs]);
            }
            next;
        }
        if ($c eq "\n") {
            $ch = $self->advance();
            push(@{$content_chars}, $ch);
            push(@{$text_chars}, $ch);
            if (scalar(@{$pending_heredocs}) > 0) {
                ($current_heredoc_delim, $current_heredoc_strip) = @{pop(@{$pending_heredocs})};
                $in_heredoc_body = 1;
            }
            next;
        }
        $ch = $self->advance();
        push(@{$content_chars}, $ch);
        push(@{$text_chars}, $ch);
    }
    if ($self->at_end()) {
        die "Unterminated backtick";
    }
    $self->advance();
    push(@{$text_chars}, "`");
    my $text = join("", @{$text_chars});
    my $content = join("", @{$content_chars});
    if (scalar(@{$pending_heredocs}) > 0) {
        ($heredoc_start, $heredoc_end) = @{main::find_heredoc_content_end($self->{source}, $self->{pos_}, $pending_heredocs)};
        if ($heredoc_end > $heredoc_start) {
            $content = $content . main::substring($self->{source}, $heredoc_start, $heredoc_end);
            if ($self->{cmdsub_heredoc_end} == -1) {
                $self->{cmdsub_heredoc_end} = $heredoc_end;
            } else {
                $self->{cmdsub_heredoc_end} = ($self->{cmdsub_heredoc_end} > $heredoc_end ? $self->{cmdsub_heredoc_end} : $heredoc_end);
            }
        }
    }
    my $sub_parser = main::new_parser($content, 0, $self->{extglob});
    my $cmd = $sub_parser->parse_list(1);
    if (!defined($cmd)) {
        $cmd = Empty->new("empty");
    }
    return [CommandSubstitution->new($cmd, 0, "cmdsub"), $text];
}

sub parse_process_substitution ($self) {
    my $cmd;
    my $content_start_char;
    my $text;
    my $text_end;
    if ($self->at_end() || !main::is_redirect_char($self->peek())) {
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
    $self->set_state(main::PARSERSTATEFLAGS_PST_EOFTOKEN());
    $self->{eof_token} = ")";
    my $_try_result;
    my $_try_returned = 0;
    eval {
        TRYBLOCK: for (1) {
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
            $text = main::substring($self->{source}, $start, $text_end);
            $text = main::strip_line_continuations_comment_aware($text);
            $self->restore_parser_state($saved);
            $self->{in_process_sub} = $old_in_process_sub;
            $_try_result = [ProcessSubstitution->new($direction, $cmd, "procsub"), $text];
            $_try_returned = 1;
            last TRYBLOCK;
        }
    };
    if (my $e = $@) {
        $self->restore_parser_state($saved);
        $self->{in_process_sub} = $old_in_process_sub;
        $content_start_char = ($start + 2 < $self->{length_} ? substr($self->{source}, $start + 2, 1) : "");
        if ((index(" \t\n", $content_start_char) >= 0)) {
            die $e;
        }
        $self->{pos_} = $start + 2;
        $self->{lexer}->{pos_} = $self->{pos_};
        $self->{lexer}->parse_matched_pair("(", ")", 0, 0);
        $self->{pos_} = $self->{lexer}->{pos_};
        $text = main::substring($self->{source}, $start, $self->{pos_});
        $text = main::strip_line_continuations_comment_aware($text);
        return [undef, $text];
    }
    return $_try_result if $_try_returned;
}

sub parse_array_literal ($self) {
    my $word;
    if ($self->at_end() || $self->peek() ne "(") {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    $self->advance();
    $self->set_state(main::PARSERSTATEFLAGS_PST_COMPASSIGN());
    my $elements = [];
    while (1) {
        $self->skip_whitespace_and_newlines();
        if ($self->at_end()) {
            $self->clear_state(main::PARSERSTATEFLAGS_PST_COMPASSIGN());
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
            $self->clear_state(main::PARSERSTATEFLAGS_PST_COMPASSIGN());
            die "Expected word in array literal";
        }
        push(@{$elements}, $word);
    }
    if ($self->at_end() || $self->peek() ne ")") {
        $self->clear_state(main::PARSERSTATEFLAGS_PST_COMPASSIGN());
        die "Expected ) to close array literal";
    }
    $self->advance();
    my $text = main::substring($self->{source}, $start, $self->{pos_});
    $self->clear_state(main::PARSERSTATEFLAGS_PST_COMPASSIGN());
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
    if ($self->{pos_} + 2 >= $self->{length_} || substr($self->{source}, $self->{pos_} + 1, 1) ne "(" || substr($self->{source}, $self->{pos_} + 2, 1) ne "(") {
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
        $content = main::substring($self->{source}, $content_start, $first_close_pos);
    } else {
        $content = main::substring($self->{source}, $content_start, $self->{pos_});
    }
    $self->advance();
    my $text = main::substring($self->{source}, $start, $self->{pos_});
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
    $self->set_state(main::PARSERSTATEFLAGS_PST_ARITH());
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
    return substr($self->{arith_src}, $pos_, 1);
}

sub arith_advance ($self) {
    if ($self->arith_at_end()) {
        return "";
    }
    my $c = substr($self->{arith_src}, $self->{arith_pos}, 1);
    $self->{arith_pos} += 1;
    return $c;
}

sub arith_skip_ws ($self) {
    my $c;
    while (!$self->arith_at_end()) {
        $c = substr($self->{arith_src}, $self->{arith_pos}, 1);
        if (main::is_whitespace($c)) {
            $self->{arith_pos} += 1;
        } elsif ($c eq "\\" && $self->{arith_pos} + 1 < $self->{arith_len} && substr($self->{arith_src}, $self->{arith_pos} + 1, 1) eq "\n") {
            $self->{arith_pos} += 2;
        } else {
            last;
        }
    }
}

sub arith_match ($self, $s_) {
    return main::starts_with_at($self->{arith_src}, $self->{arith_pos}, $s_);
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
            if ($op eq "=" && $self->arith_peek(1) eq "=") {
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
    my $left = $parsefn->();
    while (1) {
        $self->arith_skip_ws();
        $matched = 0;
        for my $op (@{$ops}) {
            if ($self->arith_match($op)) {
                $self->arith_consume($op);
                $self->arith_skip_ws();
                $left = ArithBinaryOp->new($op, $left, $parsefn->(), "binary-op");
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
            push(@{$name_chars}, $self->arith_advance());
        } elsif ((main::is_special_param_or_digit($ch) || $ch eq "#") && !(scalar(@{($name_chars // [])}) > 0)) {
            push(@{$name_chars}, $self->arith_advance());
            last;
        } else {
            last;
        }
    }
    if (!(scalar(@{($name_chars // [])}) > 0)) {
        die "Expected variable name after \$";
    }
    return ParamExpansion->new(join("", @{$name_chars}), "", "", "param");
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
        $content = main::substring($self->{arith_src}, $content_start, $self->{arith_pos});
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
    $content = main::substring($self->{arith_src}, $content_start, $self->{arith_pos});
    $self->arith_advance();
    my $sub_parser = main::new_parser($content, 0, $self->{extglob});
    my $cmd = $sub_parser->parse_list(1);
    return CommandSubstitution->new($cmd, 0, "cmdsub");
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
            push(@{$name_chars}, $self->arith_advance());
        }
        $self->arith_consume("}");
        return ParamIndirect->new(join("", @{$name_chars}), "", "", "param-indirect");
    }
    if ($self->arith_peek(0) eq "#") {
        $self->arith_advance();
        $name_chars = [];
        while (!$self->arith_at_end() && $self->arith_peek(0) ne "}") {
            push(@{$name_chars}, $self->arith_advance());
        }
        $self->arith_consume("}");
        return ParamLength->new(join("", @{$name_chars}), "param-len");
    }
    $name_chars = [];
    my $ch = "";
    while (!$self->arith_at_end()) {
        $ch = $self->arith_peek(0);
        if ($ch eq "}") {
            $self->arith_advance();
            return ParamExpansion->new(join("", @{$name_chars}), "", "", "param");
        }
        if (main::is_param_expansion_op($ch)) {
            last;
        }
        push(@{$name_chars}, $self->arith_advance());
    }
    my $name = join("", @{$name_chars});
    my $op_chars = [];
    my $depth = 1;
    while (!$self->arith_at_end() && $depth > 0) {
        $ch = $self->arith_peek(0);
        if ($ch eq "{") {
            $depth += 1;
            push(@{$op_chars}, $self->arith_advance());
        } elsif ($ch eq "}") {
            $depth -= 1;
            if ($depth == 0) {
                last;
            }
            push(@{$op_chars}, $self->arith_advance());
        } else {
            push(@{$op_chars}, $self->arith_advance());
        }
    }
    $self->arith_consume("}");
    my $op_str = join("", @{$op_chars});
    if ((index($op_str, ":-") == 0)) {
        return ParamExpansion->new($name, ":-", main::substring($op_str, 2, length($op_str)), "param");
    }
    if ((index($op_str, ":=") == 0)) {
        return ParamExpansion->new($name, ":=", main::substring($op_str, 2, length($op_str)), "param");
    }
    if ((index($op_str, ":+") == 0)) {
        return ParamExpansion->new($name, ":+", main::substring($op_str, 2, length($op_str)), "param");
    }
    if ((index($op_str, ":?") == 0)) {
        return ParamExpansion->new($name, ":?", main::substring($op_str, 2, length($op_str)), "param");
    }
    if ((index($op_str, ":") == 0)) {
        return ParamExpansion->new($name, ":", main::substring($op_str, 1, length($op_str)), "param");
    }
    if ((index($op_str, "##") == 0)) {
        return ParamExpansion->new($name, "##", main::substring($op_str, 2, length($op_str)), "param");
    }
    if ((index($op_str, "#") == 0)) {
        return ParamExpansion->new($name, "#", main::substring($op_str, 1, length($op_str)), "param");
    }
    if ((index($op_str, "%%") == 0)) {
        return ParamExpansion->new($name, "%%", main::substring($op_str, 2, length($op_str)), "param");
    }
    if ((index($op_str, "%") == 0)) {
        return ParamExpansion->new($name, "%", main::substring($op_str, 1, length($op_str)), "param");
    }
    if ((index($op_str, "//") == 0)) {
        return ParamExpansion->new($name, "//", main::substring($op_str, 2, length($op_str)), "param");
    }
    if ((index($op_str, "/") == 0)) {
        return ParamExpansion->new($name, "/", main::substring($op_str, 1, length($op_str)), "param");
    }
    return ParamExpansion->new($name, "", $op_str, "param");
}

sub arith_parse_single_quote ($self) {
    $self->arith_advance();
    my $content_start = $self->{arith_pos};
    while (!$self->arith_at_end() && $self->arith_peek(0) ne "'") {
        $self->arith_advance();
    }
    my $content = main::substring($self->{arith_src}, $content_start, $self->{arith_pos});
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
    my $content = main::substring($self->{arith_src}, $content_start, $self->{arith_pos});
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
    my $content = main::substring($self->{arith_src}, $content_start, $self->{arith_pos});
    if (!$self->arith_consume("`")) {
        die "Unterminated backtick in arithmetic";
    }
    my $sub_parser = main::new_parser($content, 0, $self->{extglob});
    my $cmd = $sub_parser->parse_list(1);
    return CommandSubstitution->new($cmd, 0, "cmdsub");
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
                push(@{$chars}, $self->arith_advance());
            } else {
                last;
            }
        }
        $prefix = join("", @{$chars});
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
                push(@{$chars}, $self->arith_advance());
            } else {
                last;
            }
        }
        return ArithVar->new(join("", @{$chars}), "var");
    }
    die "Unexpected character '" . $c . "' in arithmetic expression";
}

sub parse_deprecated_arithmetic ($self) {
    if ($self->at_end() || $self->peek() ne "\$") {
        return [undef, ""];
    }
    my $start = $self->{pos_};
    if ($self->{pos_} + 1 >= $self->{length_} || substr($self->{source}, $self->{pos_} + 1, 1) ne "[") {
        return [undef, ""];
    }
    $self->advance();
    $self->advance();
    $self->{lexer}->{pos_} = $self->{pos_};
    my $content = $self->{lexer}->parse_matched_pair("[", "]", main::MATCHEDPAIRFLAGS_ARITH(), 0);
    $self->{pos_} = $self->{lexer}->{pos_};
    my $text = main::substring($self->{source}, $start, $self->{pos_});
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
        while (!$self->at_end() && !main::is_redirect_char($self->peek())) {
            $ch = $self->peek();
            if ($ch eq "}" && !$in_bracket) {
                last;
            } elsif ($ch eq "[") {
                $in_bracket = 1;
                push(@{$varname_chars}, $self->advance());
            } elsif ($ch eq "]") {
                $in_bracket = 0;
                push(@{$varname_chars}, $self->advance());
            } elsif (($ch =~ /^[a-zA-Z0-9]$/) || $ch eq "_") {
                push(@{$varname_chars}, $self->advance());
            } elsif ($in_bracket && !main::is_metachar($ch)) {
                push(@{$varname_chars}, $self->advance());
            } else {
                last;
            }
        }
        $varname = join("", @{$varname_chars});
        $is_valid_varfd = 0;
        if ((length($varname) > 0)) {
            if ((substr($varname, 0, 1) =~ /^[a-zA-Z]$/) || substr($varname, 0, 1) eq "_") {
                if (((index($varname, "[") >= 0)) || ((index($varname, "]") >= 0))) {
                    $left = index($varname, "[");
                    $right = rindex($varname, "]");
                    if ($left != -1 && $right == length($varname) - 1 && $right > $left + 1) {
                        $base = substr($varname, 0, $left - 0);
                        if ((length($base) > 0) && ((substr($base, 0, 1) =~ /^[a-zA-Z]$/) || substr($base, 0, 1) eq "_")) {
                            $is_valid_varfd = 1;
                            for my $c (split(//, substr($base, 1))) {
                                if (!(($c =~ /^[a-zA-Z0-9]$/) || $c eq "_")) {
                                    $is_valid_varfd = 0;
                                    last;
                                }
                            }
                        }
                    }
                } else {
                    $is_valid_varfd = 1;
                    for my $c (split(//, substr($varname, 1))) {
                        if (!(($c =~ /^[a-zA-Z0-9]$/) || $c eq "_")) {
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
            push(@{$fd_chars}, $self->advance());
        }
        $fd = int(join("", @{$fd_chars}));
    }
    $ch = $self->peek();
    my $op = "";
    my $target = undef;
    if ($ch eq "&" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq ">") {
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
        return Redirect->new($op, $target, undef, "redirect");
    }
    if ($ch eq "" || !main::is_redirect_char($ch)) {
        $self->{pos_} = $start;
        return undef;
    }
    if ($fd == -1 && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
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
            if ($self->{pos_} + 1 >= $self->{length_} || !main::is_digit_or_dash(substr($self->{source}, $self->{pos_} + 1, 1))) {
                $self->advance();
                $op = ">&";
            }
        } elsif ($fd == -1 && $varfd eq "" && $op eq "<" && $next_ch eq "&") {
            if ($self->{pos_} + 1 >= $self->{length_} || !main::is_digit_or_dash(substr($self->{source}, $self->{pos_} + 1, 1))) {
                $self->advance();
                $op = "<&";
            }
        }
    }
    if ($op eq "<<") {
        return $self->parse_heredoc($fd, $strip_tabs);
    }
    if ($varfd ne "") {
        $op = "{" . $varfd . "}" . $op;
    } elsif ($fd != -1) {
        $op = ("" . $fd) . $op;
    }
    if (!$self->at_end() && $self->peek() eq "&") {
        $self->advance();
        $self->skip_whitespace();
        if (!$self->at_end() && $self->peek() eq "-") {
            if ($self->{pos_} + 1 < $self->{length_} && !main::is_metachar(substr($self->{source}, $self->{pos_} + 1, 1))) {
                $self->advance();
                $target = Word->new("&-", undef, "word");
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
                    push(@{$fd_chars}, $self->advance());
                }
                my $fd_target = "";
                if ((scalar(@{($fd_chars // [])}) > 0)) {
                    $fd_target = join("", @{$fd_chars});
                } else {
                    $fd_target = "";
                }
                if (!$self->at_end() && $self->peek() eq "-") {
                    $fd_target .= $self->advance();
                }
                if ($fd_target ne "-" && !$self->at_end() && !main::is_metachar($self->peek())) {
                    $self->{pos_} = $word_start;
                    $inner_word = $self->parse_word(0, 0, 0);
                    if (defined($inner_word)) {
                        $target = Word->new("&" . $inner_word->{value}, undef, "word");
                        $target->{parts} = $inner_word->{parts};
                    } else {
                        die "Expected target for redirect " . $op;
                    }
                } else {
                    $target = Word->new("&" . $fd_target, undef, "word");
                }
            } else {
                $inner_word = $self->parse_word(0, 0, 0);
                if (defined($inner_word)) {
                    $target = Word->new("&" . $inner_word->{value}, undef, "word");
                    $target->{parts} = $inner_word->{parts};
                } else {
                    die "Expected target for redirect " . $op;
                }
            }
        }
    } else {
        $self->skip_whitespace();
        if (($op eq ">&" || $op eq "<&") && !$self->at_end() && $self->peek() eq "-") {
            if ($self->{pos_} + 1 < $self->{length_} && !main::is_metachar(substr($self->{source}, $self->{pos_} + 1, 1))) {
                $self->advance();
                $target = Word->new("&-", undef, "word");
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
    return Redirect->new($op, $target, undef, "redirect");
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
        while (!$self->at_end() && !main::is_metachar($self->peek())) {
            $ch = $self->peek();
            if ($ch eq "\"") {
                $quoted = 1;
                $self->advance();
                while (!$self->at_end() && $self->peek() ne "\"") {
                    push(@{$delimiter_chars}, $self->advance());
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
                    push(@{$delimiter_chars}, $c);
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
                        push(@{$delimiter_chars}, $self->advance());
                    }
                }
            } elsif ($ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "'") {
                $quoted = 1;
                $self->advance();
                $self->advance();
                while (!$self->at_end() && $self->peek() ne "'") {
                    $c = $self->peek();
                    if ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        $self->advance();
                        $esc = $self->peek();
                        $esc_val = main::get_ansi_escape($esc);
                        if ($esc_val >= 0) {
                            push(@{$delimiter_chars}, chr($esc_val));
                            $self->advance();
                        } elsif ($esc eq "'") {
                            push(@{$delimiter_chars}, $self->advance());
                        } else {
                            push(@{$delimiter_chars}, $self->advance());
                        }
                    } else {
                        push(@{$delimiter_chars}, $self->advance());
                    }
                }
                if (!$self->at_end()) {
                    $self->advance();
                }
            } elsif (main::is_expansion_start($self->{source}, $self->{pos_}, "\$(")) {
                push(@{$delimiter_chars}, $self->advance());
                push(@{$delimiter_chars}, $self->advance());
                $depth = 1;
                while (!$self->at_end() && $depth > 0) {
                    $c = $self->peek();
                    if ($c eq "(") {
                        $depth += 1;
                    } elsif ($c eq ")") {
                        $depth -= 1;
                    }
                    push(@{$delimiter_chars}, $self->advance());
                }
            } elsif ($ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "{") {
                $dollar_count = 0;
                $j = $self->{pos_} - 1;
                while ($j >= 0 && substr($self->{source}, $j, 1) eq "\$") {
                    $dollar_count += 1;
                    $j -= 1;
                }
                if ($j >= 0 && substr($self->{source}, $j, 1) eq "\\") {
                    $dollar_count -= 1;
                }
                if ($dollar_count % 2 == 1) {
                    push(@{$delimiter_chars}, $self->advance());
                } else {
                    push(@{$delimiter_chars}, $self->advance());
                    push(@{$delimiter_chars}, $self->advance());
                    $depth = 0;
                    while (!$self->at_end()) {
                        $c = $self->peek();
                        if ($c eq "{") {
                            $depth += 1;
                        } elsif ($c eq "}") {
                            push(@{$delimiter_chars}, $self->advance());
                            if ($depth == 0) {
                                last;
                            }
                            $depth -= 1;
                            if ($depth == 0 && !$self->at_end() && main::is_metachar($self->peek())) {
                                last;
                            }
                            next;
                        }
                        push(@{$delimiter_chars}, $self->advance());
                    }
                }
            } elsif ($ch eq "\$" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "[") {
                $dollar_count = 0;
                $j = $self->{pos_} - 1;
                while ($j >= 0 && substr($self->{source}, $j, 1) eq "\$") {
                    $dollar_count += 1;
                    $j -= 1;
                }
                if ($j >= 0 && substr($self->{source}, $j, 1) eq "\\") {
                    $dollar_count -= 1;
                }
                if ($dollar_count % 2 == 1) {
                    push(@{$delimiter_chars}, $self->advance());
                } else {
                    push(@{$delimiter_chars}, $self->advance());
                    push(@{$delimiter_chars}, $self->advance());
                    $depth = 1;
                    while (!$self->at_end() && $depth > 0) {
                        $c = $self->peek();
                        if ($c eq "[") {
                            $depth += 1;
                        } elsif ($c eq "]") {
                            $depth -= 1;
                        }
                        push(@{$delimiter_chars}, $self->advance());
                    }
                }
            } elsif ($ch eq "`") {
                push(@{$delimiter_chars}, $self->advance());
                while (!$self->at_end() && $self->peek() ne "`") {
                    $c = $self->peek();
                    if ($c eq "'") {
                        push(@{$delimiter_chars}, $self->advance());
                        while (!$self->at_end() && $self->peek() ne "'" && $self->peek() ne "`") {
                            push(@{$delimiter_chars}, $self->advance());
                        }
                        if (!$self->at_end() && $self->peek() eq "'") {
                            push(@{$delimiter_chars}, $self->advance());
                        }
                    } elsif ($c eq "\"") {
                        push(@{$delimiter_chars}, $self->advance());
                        while (!$self->at_end() && $self->peek() ne "\"" && $self->peek() ne "`") {
                            if ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                                push(@{$delimiter_chars}, $self->advance());
                            }
                            push(@{$delimiter_chars}, $self->advance());
                        }
                        if (!$self->at_end() && $self->peek() eq "\"") {
                            push(@{$delimiter_chars}, $self->advance());
                        }
                    } elsif ($c eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        push(@{$delimiter_chars}, $self->advance());
                        push(@{$delimiter_chars}, $self->advance());
                    } else {
                        push(@{$delimiter_chars}, $self->advance());
                    }
                }
                if (!$self->at_end()) {
                    push(@{$delimiter_chars}, $self->advance());
                }
            } else {
                push(@{$delimiter_chars}, $self->advance());
            }
        }
        if (!$self->at_end() && ((index("<>", $self->peek()) >= 0)) && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
            push(@{$delimiter_chars}, $self->advance());
            push(@{$delimiter_chars}, $self->advance());
            $depth = 1;
            while (!$self->at_end() && $depth > 0) {
                $c = $self->peek();
                if ($c eq "(") {
                    $depth += 1;
                } elsif ($c eq ")") {
                    $depth -= 1;
                }
                push(@{$delimiter_chars}, $self->advance());
            }
            next;
        }
        last;
    }
    return [join("", @{$delimiter_chars}), $quoted];
}

sub read_heredoc_line ($self, $quoted) {
    my $next_line_start;
    my $trailing_bs;
    my $line_start = $self->{pos_};
    my $line_end = $self->{pos_};
    while ($line_end < $self->{length_} && substr($self->{source}, $line_end, 1) ne "\n") {
        $line_end += 1;
    }
    my $line = main::substring($self->{source}, $line_start, $line_end);
    if (!$quoted) {
        while ($line_end < $self->{length_}) {
            $trailing_bs = main::count_trailing_backslashes($line);
            if ($trailing_bs % 2 == 0) {
                last;
            }
            $line = main::substring($line, 0, length($line) - 1);
            $line_end += 1;
            $next_line_start = $line_end;
            while ($line_end < $self->{length_} && substr($self->{source}, $line_end, 1) ne "\n") {
                $line_end += 1;
            }
            $line = $line . main::substring($self->{source}, $next_line_start, $line_end);
        }
    }
    return [$line, $line_end];
}

sub line_matches_delimiter ($self, $line, $delimiter, $strip_tabs) {
    my $check_line = ($strip_tabs ? ($line =~ s/^[\t]+//r) : $line);
    my $normalized_check = main::normalize_heredoc_delimiter($check_line);
    my $normalized_delim = main::normalize_heredoc_delimiter($delimiter);
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
            $normalized_check = main::normalize_heredoc_delimiter($check_line);
            $normalized_delim = main::normalize_heredoc_delimiter($heredoc->{delimiter});
            my $tabs_stripped = 0;
            if ($self->{eof_token} eq ")" && (index($normalized_check, $normalized_delim) == 0)) {
                $tabs_stripped = length($line) - length($check_line);
                $self->{pos_} = $line_start + $tabs_stripped + length($heredoc->{delimiter});
                last;
            }
            if ($line_end >= $self->{length_} && (index($normalized_check, $normalized_delim) == 0) && $self->{in_process_sub}) {
                $tabs_stripped = length($line) - length($check_line);
                $self->{pos_} = $line_start + $tabs_stripped + length($heredoc->{delimiter});
                last;
            }
            if ($heredoc->{strip_tabs}) {
                $line = ($line =~ s/^[\t]+//r);
            }
            if ($line_end < $self->{length_}) {
                push(@{$content_lines}, $line . "\n");
                $self->{pos_} = $line_end + 1;
            } else {
                $add_newline = 1;
                if (!$heredoc->{quoted} && main::count_trailing_backslashes($line) % 2 == 1) {
                    $add_newline = 0;
                }
                push(@{$content_lines}, $line . (($add_newline ? "\n" : "")));
                $self->{pos_} = $self->{length_};
            }
        }
        $heredoc->{content} = join("", @{$content_lines});
    }
    $self->{pending_heredocs} = [];
}

sub parse_heredoc ($self, $fd, $strip_tabs) {
    my $start_pos = $self->{pos_};
    $self->set_state(main::PARSERSTATEFLAGS_PST_HEREDOC());
    my ($delimiter, $quoted) = @{$self->parse_heredoc_delimiter()};
    for my $existing (@{($self->{pending_heredocs} // [])}) {
        if ($existing->{start_pos} == $start_pos && $existing->{delimiter} eq $delimiter) {
            $self->clear_state(main::PARSERSTATEFLAGS_PST_HEREDOC());
            return $existing;
        }
    }
    my $heredoc = HereDoc->new($delimiter, "", $strip_tabs, $quoted, $fd, 0, 0, "heredoc");
    $heredoc->{start_pos} = $start_pos;
    push(@{$self->{pending_heredocs}}, $heredoc);
    $self->clear_state(main::PARSERSTATEFLAGS_PST_HEREDOC());
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
            push(@{$redirects}, $redirect);
            next;
        }
        $all_assignments = 1;
        for my $w (@{$words}) {
            if (!$self->is_assignment_word($w)) {
                $all_assignments = 0;
                last;
            }
        }
        $in_assign_builtin = scalar(@{$words}) > 0 && (exists(main::ASSIGNMENT_BUILTINS()->{$words->[0]->{value}}));
        $word = $self->parse_word(!(scalar(@{($words // [])}) > 0) || $all_assignments && scalar(@{$redirects}) == 0, 0, $in_assign_builtin);
        if (!defined($word)) {
            last;
        }
        push(@{$words}, $word);
    }
    if (!(scalar(@{($words // [])}) > 0) && !(scalar(@{($redirects // [])}) > 0)) {
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
    $self->set_state(main::PARSERSTATEFLAGS_PST_SUBSHELL());
    my $body = $self->parse_list(1);
    if (!defined($body)) {
        $self->clear_state(main::PARSERSTATEFLAGS_PST_SUBSHELL());
        die "Expected command in subshell";
    }
    $self->skip_whitespace();
    if ($self->at_end() || $self->peek() ne ")") {
        $self->clear_state(main::PARSERSTATEFLAGS_PST_SUBSHELL());
        die "Expected ) to close subshell";
    }
    $self->advance();
    $self->clear_state(main::PARSERSTATEFLAGS_PST_SUBSHELL());
    return Subshell->new($body, $self->collect_redirects(), "subshell");
}

sub parse_arithmetic_command ($self) {
    my $c;
    $self->skip_whitespace();
    if ($self->at_end() || $self->peek() ne "(" || $self->{pos_} + 1 >= $self->{length_} || substr($self->{source}, $self->{pos_} + 1, 1) ne "(") {
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
            if ($depth == 1 && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq ")") {
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
    my $content = main::substring($self->{source}, $content_start, $self->{pos_});
    $content = ($content =~ s/\\\n//gr);
    $self->advance();
    $self->advance();
    my $expr = $self->parse_arith_expr($content);
    return ArithmeticCommand->new($expr, $self->collect_redirects(), $content, "arith-cmd");
}

sub parse_conditional_expr ($self) {
    $self->skip_whitespace();
    if ($self->at_end() || $self->peek() ne "[" || $self->{pos_} + 1 >= $self->{length_} || substr($self->{source}, $self->{pos_} + 1, 1) ne "[") {
        return undef;
    }
    my $next_pos = $self->{pos_} + 2;
    if ($next_pos < $self->{length_} && !(main::is_whitespace(substr($self->{source}, $next_pos, 1)) || substr($self->{source}, $next_pos, 1) eq "\\" && $next_pos + 1 < $self->{length_} && substr($self->{source}, $next_pos + 1, 1) eq "\n")) {
        return undef;
    }
    $self->advance();
    $self->advance();
    $self->set_state(main::PARSERSTATEFLAGS_PST_CONDEXPR());
    $self->{word_context} = main::WORD_CTX_COND();
    my $body = $self->parse_cond_or();
    while (!$self->at_end() && main::is_whitespace_no_newline($self->peek())) {
        $self->advance();
    }
    if ($self->at_end() || $self->peek() ne "]" || $self->{pos_} + 1 >= $self->{length_} || substr($self->{source}, $self->{pos_} + 1, 1) ne "]") {
        $self->clear_state(main::PARSERSTATEFLAGS_PST_CONDEXPR());
        $self->{word_context} = main::WORD_CTX_NORMAL();
        die "Expected ]] to close conditional expression";
    }
    $self->advance();
    $self->advance();
    $self->clear_state(main::PARSERSTATEFLAGS_PST_CONDEXPR());
    $self->{word_context} = main::WORD_CTX_NORMAL();
    return ConditionalExpr->new($body, $self->collect_redirects(), "cond-expr");
}

sub cond_skip_whitespace ($self) {
    while (!$self->at_end()) {
        if (main::is_whitespace_no_newline($self->peek())) {
            $self->advance();
        } elsif ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "\n") {
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
    return $self->at_end() || $self->peek() eq "]" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "]";
}

sub parse_cond_or ($self) {
    my $right;
    $self->cond_skip_whitespace();
    my $left = $self->parse_cond_and();
    $self->cond_skip_whitespace();
    if (!$self->cond_at_end() && $self->peek() eq "|" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "|") {
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
    if (!$self->cond_at_end() && $self->peek() eq "&" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "&") {
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
        if ($self->{pos_} + 1 < $self->{length_} && !main::is_whitespace_no_newline(substr($self->{source}, $self->{pos_} + 1, 1))) {
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
    if (exists(main::COND_UNARY_OPS()->{$word1->{value}})) {
        $operand = $self->parse_cond_word();
        if (!defined($operand)) {
            die "Expected operand after " . $word1->{value};
        }
        return UnaryTest->new($word1->{value}, $operand, "unary-test");
    }
    if (!$self->cond_at_end() && $self->peek() ne "&" && $self->peek() ne "|" && $self->peek() ne ")") {
        my $word2 = undef;
        if (main::is_redirect_char($self->peek()) && !($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(")) {
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
        if (defined($op_word) && (exists(main::COND_BINARY_OPS()->{$op_word->{value}}))) {
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
    if (main::is_paren($c)) {
        return undef;
    }
    if ($c eq "&" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "&") {
        return undef;
    }
    if ($c eq "|" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "|") {
        return undef;
    }
    return $self->parse_word_internal(main::WORD_CTX_COND(), 0, 0);
}

sub parse_cond_regex_word ($self) {
    $self->cond_skip_whitespace();
    if ($self->cond_at_end()) {
        return undef;
    }
    $self->set_state(main::PARSERSTATEFLAGS_PST_REGEXP());
    my $result = $self->parse_word_internal(main::WORD_CTX_REGEX(), 0, 0);
    $self->clear_state(main::PARSERSTATEFLAGS_PST_REGEXP());
    $self->{word_context} = main::WORD_CTX_COND();
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
        $else_body = If->new($elif_condition, $elif_then_body, $inner_else, undef, "if");
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
    return If->new($condition, $then_body, $else_body, undef, "if");
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
    if ($self->peek() eq "(" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
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
        $saw_delimiter = main::is_semicolon_or_newline($self->peek());
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
            if (main::is_semicolon_or_newline($self->peek())) {
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
            push(@{$words}, $word);
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
            push(@{$current}, $self->advance());
        } elsif ($ch eq ")") {
            if ($paren_depth > 0) {
                $paren_depth -= 1;
                push(@{$current}, $self->advance());
            } elsif ($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq ")") {
                push(@{$parts}, (join("", @{$current}) =~ s/^[ \t]+//r));
                $self->advance();
                $self->advance();
                last;
            } else {
                push(@{$current}, $self->advance());
            }
        } elsif ($ch eq ";" && $paren_depth == 0) {
            push(@{$parts}, (join("", @{$current}) =~ s/^[ \t]+//r));
            $current = [];
            $self->advance();
        } else {
            push(@{$current}, $self->advance());
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
            if (main::is_semicolon_newline_brace($self->peek())) {
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
            push(@{$words}, $word);
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
    $self->set_state(main::PARSERSTATEFLAGS_PST_CASESTMT());
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
    $self->set_state(main::PARSERSTATEFLAGS_PST_CASEPAT());
    while (1) {
        $self->skip_whitespace_and_newlines();
        if ($self->lex_is_at_reserved_word("esac")) {
            $saved = $self->{pos_};
            $self->skip_whitespace();
            while (!$self->at_end() && !main::is_metachar($self->peek()) && !main::is_quote($self->peek())) {
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
                        } elsif (!main::is_newline_or_right_paren($next_ch)) {
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
                    push(@{$pattern_chars}, $self->advance());
                    $extglob_depth -= 1;
                } else {
                    $self->advance();
                    last;
                }
            } elsif ($ch eq "\\") {
                if ($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "\n") {
                    $self->advance();
                    $self->advance();
                } else {
                    push(@{$pattern_chars}, $self->advance());
                    if (!$self->at_end()) {
                        push(@{$pattern_chars}, $self->advance());
                    }
                }
            } elsif (main::is_expansion_start($self->{source}, $self->{pos_}, "\$(")) {
                push(@{$pattern_chars}, $self->advance());
                push(@{$pattern_chars}, $self->advance());
                if (!$self->at_end() && $self->peek() eq "(") {
                    push(@{$pattern_chars}, $self->advance());
                    $paren_depth = 2;
                    while (!$self->at_end() && $paren_depth > 0) {
                        $c = $self->peek();
                        if ($c eq "(") {
                            $paren_depth += 1;
                        } elsif ($c eq ")") {
                            $paren_depth -= 1;
                        }
                        push(@{$pattern_chars}, $self->advance());
                    }
                } else {
                    $extglob_depth += 1;
                }
            } elsif ($ch eq "(" && $extglob_depth > 0) {
                push(@{$pattern_chars}, $self->advance());
                $extglob_depth += 1;
            } elsif ($self->{extglob} && main::is_extglob_prefix($ch) && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
                push(@{$pattern_chars}, $self->advance());
                push(@{$pattern_chars}, $self->advance());
                $extglob_depth += 1;
            } elsif ($ch eq "[") {
                $is_char_class = 0;
                $scan_pos = $self->{pos_} + 1;
                $scan_depth = 0;
                $has_first_bracket_literal = 0;
                if ($scan_pos < $self->{length_} && main::is_caret_or_bang(substr($self->{source}, $scan_pos, 1))) {
                    $scan_pos += 1;
                }
                if ($scan_pos < $self->{length_} && substr($self->{source}, $scan_pos, 1) eq "]") {
                    if (index($self->{source}, "]", $scan_pos + 1) != -1) {
                        $scan_pos += 1;
                        $has_first_bracket_literal = 1;
                    }
                }
                while ($scan_pos < $self->{length_}) {
                    $sc = substr($self->{source}, $scan_pos, 1);
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
                    push(@{$pattern_chars}, $self->advance());
                    if (!$self->at_end() && main::is_caret_or_bang($self->peek())) {
                        push(@{$pattern_chars}, $self->advance());
                    }
                    if ($has_first_bracket_literal && !$self->at_end() && $self->peek() eq "]") {
                        push(@{$pattern_chars}, $self->advance());
                    }
                    while (!$self->at_end() && $self->peek() ne "]") {
                        push(@{$pattern_chars}, $self->advance());
                    }
                    if (!$self->at_end()) {
                        push(@{$pattern_chars}, $self->advance());
                    }
                } else {
                    push(@{$pattern_chars}, $self->advance());
                }
            } elsif ($ch eq "'") {
                push(@{$pattern_chars}, $self->advance());
                while (!$self->at_end() && $self->peek() ne "'") {
                    push(@{$pattern_chars}, $self->advance());
                }
                if (!$self->at_end()) {
                    push(@{$pattern_chars}, $self->advance());
                }
            } elsif ($ch eq "\"") {
                push(@{$pattern_chars}, $self->advance());
                while (!$self->at_end() && $self->peek() ne "\"") {
                    if ($self->peek() eq "\\" && $self->{pos_} + 1 < $self->{length_}) {
                        push(@{$pattern_chars}, $self->advance());
                    }
                    push(@{$pattern_chars}, $self->advance());
                }
                if (!$self->at_end()) {
                    push(@{$pattern_chars}, $self->advance());
                }
            } elsif (main::is_whitespace($ch)) {
                if ($extglob_depth > 0) {
                    push(@{$pattern_chars}, $self->advance());
                } else {
                    $self->advance();
                }
            } else {
                push(@{$pattern_chars}, $self->advance());
            }
        }
        $pattern = join("", @{$pattern_chars});
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
        push(@{$patterns}, CasePattern->new($pattern, $body, $terminator, "pattern"));
    }
    $self->clear_state(main::PARSERSTATEFLAGS_PST_CASEPAT());
    $self->skip_whitespace_and_newlines();
    if (!$self->lex_consume_word("esac")) {
        $self->clear_state(main::PARSERSTATEFLAGS_PST_CASESTMT());
        die "Expected 'esac' to close case statement";
    }
    $self->clear_state(main::PARSERSTATEFLAGS_PST_CASESTMT());
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
        if ($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
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
    if ($next_word ne "" && (exists(main::COMPOUND_KEYWORDS()->{$next_word}))) {
        $body = $self->parse_compound_command();
        if (defined($body)) {
            return Coproc->new($body, $name, "coproc");
        }
    }
    my $word_start = $self->{pos_};
    my $potential_name = $self->peek_word();
    if ((length($potential_name) > 0)) {
        while (!$self->at_end() && !main::is_metachar($self->peek()) && !main::is_quote($self->peek())) {
            $self->advance();
        }
        $self->skip_whitespace();
        $ch = "";
        if (!$self->at_end()) {
            $ch = $self->peek();
        }
        $next_word = $self->lex_peek_reserved_word();
        if (main::is_valid_identifier($potential_name)) {
            if ($ch eq "{") {
                $name = $potential_name;
                $body = $self->parse_brace_group();
                if (defined($body)) {
                    return Coproc->new($body, $name, "coproc");
                }
            } elsif ($ch eq "(") {
                $name = $potential_name;
                if ($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
                    $body = $self->parse_arithmetic_command();
                } else {
                    $body = $self->parse_subshell();
                }
                if (defined($body)) {
                    return Coproc->new($body, $name, "coproc");
                }
            } elsif ($next_word ne "" && (exists(main::COMPOUND_KEYWORDS()->{$next_word}))) {
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
            if ($self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq ")") {
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
    if ($name eq "" || (exists(main::RESERVED_WORDS()->{$name}))) {
        return undef;
    }
    if (main::looks_like_assignment($name)) {
        return undef;
    }
    $self->skip_whitespace();
    my $name_start = $self->{pos_};
    while (!$self->at_end() && !main::is_metachar($self->peek()) && !main::is_quote($self->peek()) && !main::is_paren($self->peek())) {
        $self->advance();
    }
    $name = main::substring($self->{source}, $name_start, $self->{pos_});
    if (!(length($name) > 0)) {
        $self->{pos_} = $saved_pos;
        return undef;
    }
    my $brace_depth = 0;
    my $i = 0;
    while ($i < length($name)) {
        if (main::is_expansion_start($name, $i, "\${")) {
            $brace_depth += 1;
            $i += 2;
            next;
        }
        if (substr($name, $i, 1) eq "}") {
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
    if (!$has_whitespace && (length($name) > 0) && ((index("*?\@+!\$", substr($name, length($name) - 1, 1)) >= 0))) {
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
    if (!$self->at_end() && $self->peek() eq "(" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
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
        if ($next_pos >= $self->{length_} || main::is_word_end_context(substr($self->{source}, $next_pos, 1))) {
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
            push(@{$parts}, Operator->new($op, "operator"));
        } elsif ($op eq "&") {
            push(@{$parts}, Operator->new($op, "operator"));
            $self->skip_whitespace_and_newlines();
            if ($self->at_list_until_terminator($stop_words)) {
                last;
            }
        } elsif ($op eq "&&" || $op eq "||") {
            push(@{$parts}, Operator->new($op, "operator"));
            $self->skip_whitespace_and_newlines();
        } else {
            push(@{$parts}, Operator->new($op, "operator"));
        }
        if ($self->at_list_until_terminator($stop_words)) {
            last;
        }
        $pipeline = $self->parse_pipeline();
        if (!defined($pipeline)) {
            die "Expected command after " . $op;
        }
        push(@{$parts}, $pipeline);
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
    if ($ch eq "(" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "(") {
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
    if ($ch eq "[" && $self->{pos_} + 1 < $self->{length_} && substr($self->{source}, $self->{pos_} + 1, 1) eq "[") {
        $result = $self->parse_conditional_expr();
        if (defined($result)) {
            return $result;
        }
    }
    my $reserved = $self->lex_peek_reserved_word();
    if ($reserved eq "" && $self->{in_process_sub}) {
        $word = $self->peek_word();
        if ($word ne "" && length($word) > 1 && substr($word, 0, 1) eq "}") {
            $keyword_word = substr($word, 1);
            if ((exists(main::RESERVED_WORDS()->{$keyword_word})) || $keyword_word eq "{" || $keyword_word eq "}" || $keyword_word eq "[[" || $keyword_word eq "]]" || $keyword_word eq "!" || $keyword_word eq "time") {
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
                if ($self->at_end() || main::is_metachar($self->peek())) {
                    $time_posix = 1;
                } else {
                    $self->{pos_} = $saved;
                }
            } else {
                $self->{pos_} = $saved;
            }
        }
        $self->skip_whitespace();
        if (!$self->at_end() && main::starts_with_at($self->{source}, $self->{pos_}, "--")) {
            if ($self->{pos_} + 2 >= $self->{length_} || main::is_whitespace(substr($self->{source}, $self->{pos_} + 2, 1))) {
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
                    if ($self->at_end() || main::is_metachar($self->peek())) {
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
            if (($self->{pos_} + 1 >= $self->{length_} || main::is_negation_boundary(substr($self->{source}, $self->{pos_} + 1, 1))) && !$self->is_bang_followed_by_procsub()) {
                $self->advance();
                $prefix_order = "time_negation";
                $self->skip_whitespace();
            }
        }
    } elsif (!$self->at_end() && $self->peek() eq "!") {
        if (($self->{pos_} + 1 >= $self->{length_} || main::is_negation_boundary(substr($self->{source}, $self->{pos_} + 1, 1))) && !$self->is_bang_followed_by_procsub()) {
            $self->advance();
            $self->skip_whitespace();
            $inner = $self->parse_pipeline();
            if (defined($inner) && $inner->{kind} eq "negation") {
                if (defined($inner->{pipeline})) {
                    return $inner->{pipeline};
                } else {
                    return Command->new([], undef, "command");
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
        if ($token_type != main::TOKENTYPE_PIPE() && $token_type != main::TOKENTYPE_PIPE_AMP()) {
            last;
        }
        $self->lex_next_token();
        $is_pipe_both = $token_type == main::TOKENTYPE_PIPE_AMP();
        $self->skip_whitespace_and_newlines();
        if ($is_pipe_both) {
            push(@{$commands}, PipeBoth->new("pipe-both"));
        }
        $cmd = $self->parse_compound_command();
        if (!defined($cmd)) {
            die "Expected command after |";
        }
        push(@{$commands}, $cmd);
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
    if ($token_type == main::TOKENTYPE_AND_AND()) {
        $self->lex_next_token();
        return "&&";
    }
    if ($token_type == main::TOKENTYPE_OR_OR()) {
        $self->lex_next_token();
        return "||";
    }
    if ($token_type == main::TOKENTYPE_SEMI()) {
        $self->lex_next_token();
        return ";";
    }
    if ($token_type == main::TOKENTYPE_AMP()) {
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
    if ($self->in_state(main::PARSERSTATEFLAGS_PST_EOFTOKEN()) && $self->at_eof_token()) {
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
        push(@{$parts}, Operator->new($op, "operator"));
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
        push(@{$parts}, $pipeline);
        if ($self->in_state(main::PARSERSTATEFLAGS_PST_EOFTOKEN()) && $self->at_eof_token()) {
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
    my $text = main::substring($self->{source}, $start, $self->{pos_});
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
            push(@{$results}, $result);
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
    if (!(scalar(@{($results // [])}) > 0)) {
        return [Empty->new("empty")];
    }
    if ($self->{saw_newline_in_single_quote} && (length($self->{source}) > 0) && substr($self->{source}, length($self->{source}) - 1, 1) eq "\\" && !(length($self->{source}) >= 3 && substr($self->{source}, length($self->{source}) - 3, length($self->{source}) - 1 - length($self->{source}) - 3) eq "\\\n")) {
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
    if (!(scalar(@{($nodes // [])}) > 0)) {
        return;
    }
    my $last_node = $nodes->[-1];
    my $last_word = $self->find_last_word($last_node);
    if (defined($last_word) && (substr($last_word->{value}, -length("\\")) eq "\\")) {
        $last_word->{value} = main::substring($last_word->{value}, 0, length($last_word->{value}) - 1);
        if (!(length($last_word->{value}) > 0) && (ref($last_node) eq 'Command') && (scalar(@{($last_node->{words} // [])}) > 0)) {
            pop(@{$last_node->{words}});
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
        if ((scalar(@{($node->{words} // [])}) > 0)) {
            $last_word = $node->{words}->[-1];
            if ((substr($last_word->{value}, -length("\\")) eq "\\")) {
                return $last_word;
            }
        }
        if ((scalar(@{($node->{redirects} // [])}) > 0)) {
            $last_redirect = $node->{redirects}->[-1];
            if (ref($last_redirect) eq 'Redirect') {
                my $last_redirect = $last_redirect;
                return $last_redirect->{target};
            }
        }
        if ((scalar(@{($node->{words} // [])}) > 0)) {
            return $node->{words}->[-1];
        }
    }
    if (ref($node) eq 'Pipeline') {
        my $node = $node;
        if ((scalar(@{($node->{commands} // [])}) > 0)) {
            return $self->find_last_word($node->{commands}->[-1]);
        }
    }
    if (ref($node) eq 'List') {
        my $node = $node;
        if ((scalar(@{($node->{parts} // [])}) > 0)) {
            return $self->find_last_word($node->{parts}->[-1]);
        }
    }
    return undef;
}

1;

package main;

sub is_hex_digit ($c) {
    return $c ge "0" && $c le "9" || $c ge "a" && $c le "f" || $c ge "A" && $c le "F";
}

sub is_octal_digit ($c) {
    return $c ge "0" && $c le "7";
}

sub get_ansi_escape ($c) {
    return (ANSI_C_ESCAPES()->{$c} // -1);
}

sub is_whitespace ($c) {
    return $c eq " " || $c eq "\t" || $c eq "\n";
}

sub string_to_bytes ($s_) {
    return [@{[unpack('C*', $s_)]}];
}

sub is_whitespace_no_newline ($c) {
    return $c eq " " || $c eq "\t";
}

sub substring ($s_, $start, $end) {
    return substr($s_, $start, $end - $start);
}

sub starts_with_at ($s_, $pos_, $prefix) {
    return (index($s_, $prefix, $pos_) == $pos_);
}

sub count_consecutive_dollars_before ($s_, $pos_) {
    my $bs_count;
    my $j;
    my $count = 0;
    my $k = $pos_ - 1;
    while ($k >= 0 && substr($s_, $k, 1) eq "\$") {
        $bs_count = 0;
        $j = $k - 1;
        while ($j >= 0 && substr($s_, $j, 1) eq "\\") {
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
        push(@{$result}, $s_);
        $i += 1;
    }
    return join("", @{$result});
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
        $c = substr($text, $i, 1);
        if ($c eq "\\" && $i + 1 < length($text) && substr($text, $i + 1, 1) eq "\n") {
            $num_preceding_backslashes = 0;
            $j = $i - 1;
            while ($j >= 0 && substr($text, $j, 1) eq "\\") {
                $num_preceding_backslashes += 1;
                $j -= 1;
            }
            if ($num_preceding_backslashes % 2 == 0) {
                if ($in_comment) {
                    push(@{$result}, "\n");
                }
                $i += 2;
                $in_comment = 0;
                next;
            }
        }
        if ($c eq "\n") {
            $in_comment = 0;
            push(@{$result}, $c);
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
        push(@{$result}, $c);
        $i += 1;
    }
    return join("", @{$result});
}

sub append_redirects ($base, $redirects) {
    my $parts;
    if ((scalar(@{($redirects // [])}) > 0)) {
        $parts = [];
        for my $r (@{$redirects}) {
            push(@{$parts}, $r->to_sexp());
        }
        return $base . " " . join(" ", @{$parts});
    }
    return $base;
}

sub format_arith_val ($s_) {
    my $w = Word->new($s_, [], "word");
    my $val = $w->expand_all_ansi_c_quotes($s_);
    $val = $w->strip_locale_string_dollars($val);
    $val = $w->format_command_substitutions($val, 0);
    $val = (($val =~ s/\\/\\\\/gr) =~ s/"/\\"/gr);
    $val = (($val =~ s/\n/\\n/gr) =~ s/\t/\\t/gr);
    return $val;
}

sub consume_single_quote ($s_, $start) {
    my $chars = ["'"];
    my $i = $start + 1;
    while ($i < length($s_) && substr($s_, $i, 1) ne "'") {
        push(@{$chars}, substr($s_, $i, 1));
        $i += 1;
    }
    if ($i < length($s_)) {
        push(@{$chars}, substr($s_, $i, 1));
        $i += 1;
    }
    return [$i, $chars];
}

sub consume_double_quote ($s_, $start) {
    my $chars = ["\""];
    my $i = $start + 1;
    while ($i < length($s_) && substr($s_, $i, 1) ne "\"") {
        if (substr($s_, $i, 1) eq "\\" && $i + 1 < length($s_)) {
            push(@{$chars}, substr($s_, $i, 1));
            $i += 1;
        }
        push(@{$chars}, substr($s_, $i, 1));
        $i += 1;
    }
    if ($i < length($s_)) {
        push(@{$chars}, substr($s_, $i, 1));
        $i += 1;
    }
    return [$i, $chars];
}

sub has_bracket_close ($s_, $start, $depth) {
    my $i = $start;
    while ($i < length($s_)) {
        if (substr($s_, $i, 1) eq "]") {
            return 1;
        }
        if ((substr($s_, $i, 1) eq "|" || substr($s_, $i, 1) eq ")") && $depth == 0) {
            return 0;
        }
        $i += 1;
    }
    return 0;
}

sub consume_bracket_class ($s_, $start, $depth) {
    my $scan_pos = $start + 1;
    if ($scan_pos < length($s_) && (substr($s_, $scan_pos, 1) eq "!" || substr($s_, $scan_pos, 1) eq "^")) {
        $scan_pos += 1;
    }
    if ($scan_pos < length($s_) && substr($s_, $scan_pos, 1) eq "]") {
        if (has_bracket_close($s_, $scan_pos + 1, $depth)) {
            $scan_pos += 1;
        }
    }
    my $is_bracket = 0;
    while ($scan_pos < length($s_)) {
        if (substr($s_, $scan_pos, 1) eq "]") {
            $is_bracket = 1;
            last;
        }
        if (substr($s_, $scan_pos, 1) eq ")" && $depth == 0) {
            last;
        }
        if (substr($s_, $scan_pos, 1) eq "|" && $depth == 0) {
            last;
        }
        $scan_pos += 1;
    }
    if (!$is_bracket) {
        return [$start + 1, ["["], 0];
    }
    my $chars = ["["];
    my $i = $start + 1;
    if ($i < length($s_) && (substr($s_, $i, 1) eq "!" || substr($s_, $i, 1) eq "^")) {
        push(@{$chars}, substr($s_, $i, 1));
        $i += 1;
    }
    if ($i < length($s_) && substr($s_, $i, 1) eq "]") {
        if (has_bracket_close($s_, $i + 1, $depth)) {
            push(@{$chars}, substr($s_, $i, 1));
            $i += 1;
        }
    }
    while ($i < length($s_) && substr($s_, $i, 1) ne "]") {
        push(@{$chars}, substr($s_, $i, 1));
        $i += 1;
    }
    if ($i < length($s_)) {
        push(@{$chars}, substr($s_, $i, 1));
        $i += 1;
    }
    return [$i, $chars, 1];
}

sub format_cond_body ($node) {
    my $left_val;
    my $operand_val;
    my $right_val;
    my $kind = $node->{kind};
    if ($kind eq "unary-test") {
        $operand_val = $node->{operand}->get_cond_formatted_value();
        return $node->{op} . " " . $operand_val;
    }
    if ($kind eq "binary-test") {
        $left_val = $node->{left}->get_cond_formatted_value();
        $right_val = $node->{right}->get_cond_formatted_value();
        return $left_val . " " . $node->{op} . " " . $right_val;
    }
    if ($kind eq "cond-and") {
        return format_cond_body($node->{left}) . " && " . format_cond_body($node->{right});
    }
    if ($kind eq "cond-or") {
        return format_cond_body($node->{left}) . " || " . format_cond_body($node->{right});
    }
    if ($kind eq "cond-not") {
        return "! " . format_cond_body($node->{operand});
    }
    if ($kind eq "cond-paren") {
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
            if ($p->{kind} ne "operator") {
                return starts_with_subshell($p);
            }
        }
        return 0;
    }
    if (ref($node) eq 'Pipeline') {
        my $node = $node;
        if ((scalar(@{($node->{commands} // [])}) > 0)) {
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
            push(@{$parts}, $val);
        }
        $heredocs = [];
        for my $r (@{($node->{redirects} // [])}) {
            if (ref($r) eq 'HereDoc') {
                my $r = $r;
                push(@{$heredocs}, $r);
            }
        }
        for my $r (@{($node->{redirects} // [])}) {
            push(@{$parts}, format_redirect($r, $compact_redirects, 1));
        }
        my $result = "";
        if ($compact_redirects && (scalar(@{($node->{words} // [])}) > 0) && (scalar(@{($node->{redirects} // [])}) > 0)) {
            $word_parts = [@{$parts}[0 .. scalar(@{$node->{words}}) - 1]];
            $redirect_parts = [@{$parts}[scalar(@{$node->{words}}) .. $#{$parts}]];
            $result = join(" ", @{$word_parts}) . join("", @{$redirect_parts});
        } else {
            $result = join(" ", @{$parts});
        }
        for my $h (@{$heredocs}) {
            $result = $result . format_heredoc_body($h);
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
            $needs_redirect = $i + 1 < scalar(@{$node->{commands}}) && $node->{commands}->[$i + 1]->{kind} eq "pipe-both";
            push(@{$cmds}, [$cmd, $needs_redirect]);
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
            if ($cmd->{kind} eq "command" && (scalar(@{($cmd->{redirects} // [])}) > 0)) {
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
                    $first_nl = index($formatted, "\n");
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
                $first_nl = index($formatted, "\n");
                if ($first_nl != -1) {
                    $formatted = substr($formatted, 0, $first_nl - 0) . " |" . substr($formatted, $first_nl);
                }
                push(@{$result_parts}, $formatted);
            } else {
                push(@{$result_parts}, $formatted);
            }
            $idx += 1;
        }
        $compact_pipe = $in_procsub && (scalar(@{($cmds // [])}) > 0) && $cmds->[0]->[0]->{kind} eq "subshell";
        $result = "";
        $idx = 0;
        while ($idx < scalar(@{$result_parts})) {
            $part = $result_parts->[$idx];
            if ($idx > 0) {
                if ((substr($result, -length("\n")) eq "\n")) {
                    $result = $result . "  " . $part;
                } elsif ($compact_pipe) {
                    $result = $result . "|" . $part;
                } else {
                    $result = $result . " | " . $part;
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
            if ($p->{kind} eq "command" && (scalar(@{($p->{redirects} // [])}) > 0)) {
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
                        if ($cmd->{kind} eq "command" && (scalar(@{($cmd->{redirects} // [])}) > 0)) {
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
                    if ((scalar(@{($result // [])}) > 0) && (substr($result->[-1], -length("\n")) eq "\n")) {
                        $skipped_semi = 1;
                        next;
                    }
                    if (scalar(@{$result}) >= 3 && $result->[-2] eq "\n" && (substr($result->[-3], -length("\n")) eq "\n")) {
                        $skipped_semi = 1;
                        next;
                    }
                    push(@{$result}, ";");
                    $skipped_semi = 0;
                } elsif ($p->{op} eq "\n") {
                    if ((scalar(@{($result // [])}) > 0) && $result->[-1] eq ";") {
                        $skipped_semi = 0;
                        next;
                    }
                    if ((scalar(@{($result // [])}) > 0) && (substr($result->[-1], -length("\n")) eq "\n")) {
                        push(@{$result}, ($skipped_semi ? " " : "\n"));
                        $skipped_semi = 0;
                        next;
                    }
                    push(@{$result}, "\n");
                    $skipped_semi = 0;
                } elsif ($p->{op} eq "&") {
                    if ((scalar(@{($result // [])}) > 0) && ((index($result->[-1], "<<") >= 0)) && ((index($result->[-1], "\n") >= 0))) {
                        $last_ = $result->[-1];
                        if (((index($last_, " |") >= 0)) || (index($last_, "|") == 0)) {
                            $result->[-1] = $last_ . " &";
                        } else {
                            $first_nl = index($last_, "\n");
                            $result->[-1] = substr($last_, 0, $first_nl - 0) . " &" . substr($last_, $first_nl);
                        }
                    } else {
                        push(@{$result}, " &");
                    }
                } elsif ((scalar(@{($result // [])}) > 0) && ((index($result->[-1], "<<") >= 0)) && ((index($result->[-1], "\n") >= 0))) {
                    $last_ = $result->[-1];
                    $first_nl = index($last_, "\n");
                    $result->[-1] = substr($last_, 0, $first_nl - 0) . " " . $p->{op} . " " . substr($last_, $first_nl);
                } else {
                    push(@{$result}, " " . $p->{op});
                }
            } else {
                if ((scalar(@{($result // [])}) > 0) && !(substr($result->[-1], -length([" ", "\n"])) eq [" ", "\n"])) {
                    push(@{$result}, " ");
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
                push(@{$result}, $formatted_cmd);
                $cmd_count += 1;
            }
        }
        $s_ = join("", @{$result});
        if (((index($s_, " &\n") >= 0)) && (substr($s_, -length("\n")) eq "\n")) {
            return $s_ . " ";
        }
        while ((substr($s_, -length(";")) eq ";")) {
            $s_ = substring($s_, 0, length($s_) - 1);
        }
        if (!$has_heredoc) {
            while ((substr($s_, -length("\n")) eq "\n")) {
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
            $result = $result . "\n" . $sp . "else\n" . $inner_sp . $else_body . ";";
        }
        $result = $result . "\n" . $sp . "fi";
        return $result;
    }
    if (ref($node) eq 'While') {
        my $node = $node;
        $cond = format_cmdsub_node($node->{condition}, $indent, 0, 0, 0);
        $body = format_cmdsub_node($node->{body}, $indent + 4, 0, 0, 0);
        $result = "while " . $cond . "; do\n" . $inner_sp . $body . ";\n" . $sp . "done";
        if ((scalar(@{($node->{redirects} // [])}) > 0)) {
            for my $r (@{($node->{redirects} // [])}) {
                $result = $result . " " . format_redirect($r, 0, 0);
            }
        }
        return $result;
    }
    if (ref($node) eq 'Until') {
        my $node = $node;
        $cond = format_cmdsub_node($node->{condition}, $indent, 0, 0, 0);
        $body = format_cmdsub_node($node->{body}, $indent + 4, 0, 0, 0);
        $result = "until " . $cond . "; do\n" . $inner_sp . $body . ";\n" . $sp . "done";
        if ((scalar(@{($node->{redirects} // [])}) > 0)) {
            for my $r (@{($node->{redirects} // [])}) {
                $result = $result . " " . format_redirect($r, 0, 0);
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
                push(@{$word_vals}, $w->{value});
            }
            $words = join(" ", @{$word_vals});
            if ((length($words) > 0)) {
                $result = "for " . $var . " in " . $words . ";\n" . $sp . "do\n" . $inner_sp . $body . ";\n" . $sp . "done";
            } else {
                $result = "for " . $var . " in ;\n" . $sp . "do\n" . $inner_sp . $body . ";\n" . $sp . "done";
            }
        } else {
            $result = "for " . $var . " in \"\$\@\";\n" . $sp . "do\n" . $inner_sp . $body . ";\n" . $sp . "done";
        }
        if ((scalar(@{($node->{redirects} // [])}) > 0)) {
            for my $r (@{($node->{redirects} // [])}) {
                $result = $result . " " . format_redirect($r, 0, 0);
            }
        }
        return $result;
    }
    if (ref($node) eq 'ForArith') {
        my $node = $node;
        $body = format_cmdsub_node($node->{body}, $indent + 4, 0, 0, 0);
        $result = "for ((" . $node->{init} . "; " . $node->{cond} . "; " . $node->{incr} . "))\ndo\n" . $inner_sp . $body . ";\n" . $sp . "done";
        if ((scalar(@{($node->{redirects} // [])}) > 0)) {
            for my $r (@{($node->{redirects} // [])}) {
                $result = $result . " " . format_redirect($r, 0, 0);
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
            $pat = ($p->{pattern} =~ s/\|/ | /gr);
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
                push(@{$patterns}, " " . $pat . ")\n" . $body_part . $term_indent . $term);
            } else {
                push(@{$patterns}, $pat . ")\n" . $body_part . $term_indent . $term);
            }
            $i += 1;
        }
        $pattern_str = join(("\n" . repeat_str(" ", $indent + 4)), @{$patterns});
        $redirects = "";
        if ((scalar(@{($node->{redirects} // [])}) > 0)) {
            $redirect_parts = [];
            for my $r (@{($node->{redirects} // [])}) {
                $redirect_parts->append(format_redirect($r, 0, 0));
            }
            $redirects = " " . join(" ", @{$redirect_parts});
        }
        return "case " . $word . " in" . $pattern_str . "\n" . $sp . "esac" . $redirects;
    }
    if (ref($node) eq 'Function') {
        my $node = $node;
        $name = $node->{name};
        $inner_body = ($node->{body}->{kind} eq "brace-group" ? $node->{body}->{body} : $node->{body});
        $body = (format_cmdsub_node($inner_body, $indent + 4, 0, 0, 0) =~ s/[;]+$//r);
        return sprintf("function %s () 
{ 
%s%s
}", $name, $inner_sp, $body);
    }
    if (ref($node) eq 'Subshell') {
        my $node = $node;
        $body = format_cmdsub_node($node->{body}, $indent, $in_procsub, $compact_redirects, 0);
        $redirects = "";
        if ((scalar(@{($node->{redirects} // [])}) > 0)) {
            $redirect_parts = [];
            for my $r (@{($node->{redirects} // [])}) {
                $redirect_parts->append(format_redirect($r, 0, 0));
            }
            $redirects = join(" ", @{$redirect_parts});
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
        $body = ($body =~ s/[;]+$//r);
        $terminator = ((substr($body, -length(" &")) eq " &") ? " }" : "; }");
        $redirects = "";
        if ((scalar(@{($node->{redirects} // [])}) > 0)) {
            $redirect_parts = [];
            for my $r (@{($node->{redirects} // [])}) {
                $redirect_parts->append(format_redirect($r, 0, 0));
            }
            $redirects = join(" ", @{$redirect_parts});
        }
        if ((length($redirects) > 0)) {
            return "{ " . $body . $terminator . " " . $redirects;
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
    my $op = "";
    if (ref($r) eq 'HereDoc') {
        my $r = $r;
        if ($r->{strip_tabs}) {
            $op = "<<-";
        } else {
            $op = "<<";
        }
        if (defined($r->{fd}) && $r->{fd} > 0) {
            $op = ("" . $r->{fd}) . $op;
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
    if ((index($target, "&") == 0)) {
        $was_input_close = 0;
        if ($target eq "&-" && (substr($op, -length("<")) eq "<")) {
            $was_input_close = 1;
            $op = substring($op, 0, length($op) - 1) . ">";
        }
        $after_amp = substring($target, 1, length($target));
        $is_literal_fd = $after_amp eq "-" || length($after_amp) > 0 && (substr($after_amp, 0, 1) =~ /^\d$/);
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
    if ((substr($op, -length("&")) eq "&")) {
        return $op . $target;
    }
    if ($compact) {
        return $op . $target;
    }
    return $op . " " . $target;
}

sub format_heredoc_body ($r) {
    return "\n" . $r->{content} . $r->{delimiter} . "\n";
}

sub lookahead_for_esac ($value, $start, $case_depth) {
    my $c;
    my $i = $start;
    my $depth = $case_depth;
    my $quote = new_quote_state();
    while ($i < length($value)) {
        $c = substr($value, $i, 1);
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
    while ($i < length($value) && substr($value, $i, 1) ne "`") {
        if (substr($value, $i, 1) eq "\\" && $i + 1 < length($value)) {
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
    while ($i < length($s_) && substr($s_, $i, 1) ne "'") {
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
        $c = substr($s_, $i, 1);
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
            if (substr($s_, $i + 1, 1) eq "(") {
                $i = find_cmdsub_end($s_, $i + 2);
                next;
            }
            if (substr($s_, $i + 1, 1) eq "{") {
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
        $scan_c = substr($value, $scan_i, 1);
        if (is_expansion_start($value, $scan_i, "\$(")) {
            $scan_i = find_cmdsub_end($value, $scan_i + 2);
            next;
        }
        if ($scan_c eq "(") {
            $scan_paren += 1;
        } elsif ($scan_c eq ")") {
            if ($scan_paren > 0) {
                $scan_paren -= 1;
            } elsif ($scan_i + 1 < length($value) && substr($value, $scan_i + 1, 1) eq ")") {
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
        $c = substr($value, $i, 1);
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
        $c = substr($value, $i, 1);
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
        if ($c eq "#" && $arith_depth == 0 && ($i == $start || substr($value, $i - 1, 1) eq " " || substr($value, $i - 1, 1) eq "\t" || substr($value, $i - 1, 1) eq "\n" || substr($value, $i - 1, 1) eq ";" || substr($value, $i - 1, 1) eq "|" || substr($value, $i - 1, 1) eq "&" || substr($value, $i - 1, 1) eq "(" || substr($value, $i - 1, 1) eq ")")) {
            while ($i < length($value) && substr($value, $i, 1) ne "\n") {
                $i += 1;
            }
            next;
        }
        if (starts_with_at($value, $i, "<<<")) {
            $i += 3;
            while ($i < length($value) && (substr($value, $i, 1) eq " " || substr($value, $i, 1) eq "\t")) {
                $i += 1;
            }
            if ($i < length($value) && substr($value, $i, 1) eq "\"") {
                $i += 1;
                while ($i < length($value) && substr($value, $i, 1) ne "\"") {
                    if (substr($value, $i, 1) eq "\\" && $i + 1 < length($value)) {
                        $i += 2;
                    } else {
                        $i += 1;
                    }
                }
                if ($i < length($value)) {
                    $i += 1;
                }
            } elsif ($i < length($value) && substr($value, $i, 1) eq "'") {
                $i += 1;
                while ($i < length($value) && substr($value, $i, 1) ne "'") {
                    $i += 1;
                }
                if ($i < length($value)) {
                    $i += 1;
                }
            } else {
                while ($i < length($value) && ((index(" \t\n;|&<>()", substr($value, $i, 1)) == -1))) {
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
        $c = substr($value, $i, 1);
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
        if (($c eq "<" || $c eq ">") && $i + 1 < length($value) && substr($value, $i + 1, 1) eq "(") {
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
    if ($i < length($value) && substr($value, $i, 1) eq "-") {
        $i += 1;
    }
    while ($i < length($value) && is_whitespace_no_newline(substr($value, $i, 1))) {
        $i += 1;
    }
    my $delim_start = $i;
    my $quote_char = undef;
    my $delimiter = "";
    if ($i < length($value) && (substr($value, $i, 1) eq "\"" || substr($value, $i, 1) eq "'")) {
        $quote_char = substr($value, $i, 1);
        $i += 1;
        $delim_start = $i;
        while ($i < length($value) && substr($value, $i, 1) ne $quote_char) {
            $i += 1;
        }
        $delimiter = substring($value, $delim_start, $i);
        if ($i < length($value)) {
            $i += 1;
        }
    } elsif ($i < length($value) && substr($value, $i, 1) eq "\\") {
        $i += 1;
        $delim_start = $i;
        if ($i < length($value)) {
            $i += 1;
        }
        while ($i < length($value) && !is_metachar(substr($value, $i, 1))) {
            $i += 1;
        }
        $delimiter = substring($value, $delim_start, $i);
    } else {
        while ($i < length($value) && !is_metachar(substr($value, $i, 1))) {
            $i += 1;
        }
        $delimiter = substring($value, $delim_start, $i);
    }
    my $paren_depth = 0;
    my $quote = new_quote_state();
    my $in_backtick = 0;
    while ($i < length($value) && substr($value, $i, 1) ne "\n") {
        $c = substr($value, $i, 1);
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
    if ($i < length($value) && substr($value, $i, 1) eq ")") {
        return $i;
    }
    if ($i < length($value) && substr($value, $i, 1) eq "\n") {
        $i += 1;
    }
    while ($i < length($value)) {
        $line_start = $i;
        $line_end = $i;
        while ($line_end < length($value) && substr($value, $line_end, 1) ne "\n") {
            $line_end += 1;
        }
        $line = substring($value, $line_start, $line_end);
        while ($line_end < length($value)) {
            $trailing_bs = 0;
            for (my $j = length($line) - 1; $j > -1; $j += -1) {
                if (substr($line, $j, 1) eq "\\") {
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
            while ($line_end < length($value) && substr($value, $line_end, 1) ne "\n") {
                $line_end += 1;
            }
            $line = $line . substring($value, $next_line_start, $line_end);
        }
        my $stripped = "";
        if ($start + 2 < length($value) && substr($value, $start + 2, 1) eq "-") {
            $stripped = ($line =~ s/^[\t]+//r);
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
        if ((index($stripped, $delimiter) == 0) && length($stripped) > length($delimiter)) {
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
    if (!(scalar(@{($delimiters // [])}) > 0)) {
        return [$start, $start];
    }
    my $pos_ = $start;
    while ($pos_ < length($source) && substr($source, $pos_, 1) ne "\n") {
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
            while ($line_end < length($source) && substr($source, $line_end, 1) ne "\n") {
                $line_end += 1;
            }
            $line = substring($source, $line_start, $line_end);
            while ($line_end < length($source)) {
                $trailing_bs = 0;
                for (my $j = length($line) - 1; $j > -1; $j += -1) {
                    if (substr($line, $j, 1) eq "\\") {
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
                while ($line_end < length($source) && substr($source, $line_end, 1) ne "\n") {
                    $line_end += 1;
                }
                $line = $line . substring($source, $next_line_start, $line_end);
            }
            my $line_stripped = "";
            if ($strip_tabs) {
                $line_stripped = ($line =~ s/^[\t]+//r);
            } else {
                $line_stripped = $line;
            }
            if ($line_stripped eq $delimiter) {
                $pos_ = ($line_end < length($source) ? $line_end + 1 : $line_end);
                last;
            }
            if ((index($line_stripped, $delimiter) == 0) && length($line_stripped) > length($delimiter)) {
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
        $prev = substr($s_, $pos_ - 1, 1);
        if (($prev =~ /^[a-zA-Z0-9]$/) || $prev eq "_") {
            return 0;
        }
        if ((index("{}!", $prev) >= 0)) {
            return 0;
        }
    }
    my $end = $pos_ + $word_len;
    if ($end < length($s_) && ((substr($s_, $end, 1) =~ /^[a-zA-Z0-9]$/) || substr($s_, $end, 1) eq "_")) {
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
    for my $c (split(//, $s_)) {
        if ($c eq " " || $c eq "\t") {
            if (!$prev_was_ws) {
                push(@{$result}, " ");
            }
            $prev_was_ws = 1;
        } else {
            push(@{$result}, $c);
            $prev_was_ws = 0;
        }
    }
    my $joined = join("", @{$result});
    return ($joined =~ s/^[ \t]+|[ \t]+$//gr);
}

sub count_trailing_backslashes ($s_) {
    my $count = 0;
    for (my $i = length($s_) - 1; $i > -1; $i += -1) {
        if (substr($s_, $i, 1) eq "\\") {
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
            push(@{$result}, "\$(");
            $i += 2;
            $depth = 1;
            $inner = [];
            while ($i < length($delimiter) && $depth > 0) {
                if (substr($delimiter, $i, 1) eq "(") {
                    $depth += 1;
                    push(@{$inner}, substr($delimiter, $i, 1));
                } elsif (substr($delimiter, $i, 1) eq ")") {
                    $depth -= 1;
                    if ($depth == 0) {
                        $inner_str = join("", @{$inner});
                        $inner_str = collapse_whitespace($inner_str);
                        push(@{$result}, $inner_str);
                        push(@{$result}, ")");
                    } else {
                        push(@{$inner}, substr($delimiter, $i, 1));
                    }
                } else {
                    push(@{$inner}, substr($delimiter, $i, 1));
                }
                $i += 1;
            }
        } elsif ($i + 1 < length($delimiter) && substr($delimiter, $i, $i + 2 - $i) eq "\${") {
            push(@{$result}, "\${");
            $i += 2;
            $depth = 1;
            $inner = [];
            while ($i < length($delimiter) && $depth > 0) {
                if (substr($delimiter, $i, 1) eq "{") {
                    $depth += 1;
                    push(@{$inner}, substr($delimiter, $i, 1));
                } elsif (substr($delimiter, $i, 1) eq "}") {
                    $depth -= 1;
                    if ($depth == 0) {
                        $inner_str = join("", @{$inner});
                        $inner_str = collapse_whitespace($inner_str);
                        push(@{$result}, $inner_str);
                        push(@{$result}, "}");
                    } else {
                        push(@{$inner}, substr($delimiter, $i, 1));
                    }
                } else {
                    push(@{$inner}, substr($delimiter, $i, 1));
                }
                $i += 1;
            }
        } elsif ($i + 1 < length($delimiter) && ((index("<>", substr($delimiter, $i, 1)) >= 0)) && substr($delimiter, $i + 1, 1) eq "(") {
            push(@{$result}, substr($delimiter, $i, 1));
            push(@{$result}, "(");
            $i += 2;
            $depth = 1;
            $inner = [];
            while ($i < length($delimiter) && $depth > 0) {
                if (substr($delimiter, $i, 1) eq "(") {
                    $depth += 1;
                    push(@{$inner}, substr($delimiter, $i, 1));
                } elsif (substr($delimiter, $i, 1) eq ")") {
                    $depth -= 1;
                    if ($depth == 0) {
                        $inner_str = join("", @{$inner});
                        $inner_str = collapse_whitespace($inner_str);
                        push(@{$result}, $inner_str);
                        push(@{$result}, ")");
                    } else {
                        push(@{$inner}, substr($delimiter, $i, 1));
                    }
                } else {
                    push(@{$inner}, substr($delimiter, $i, 1));
                }
                $i += 1;
            }
        } else {
            push(@{$result}, substr($delimiter, $i, 1));
            $i += 1;
        }
    }
    return join("", @{$result});
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
        if ($start >= $n || substr($s_, $start, 1) ne $open_) {
            return -1;
        }
        $i = $start + 1;
    }
    my $depth = 1;
    my $pass_next = 0;
    my $backq = 0;
    while ($i < $n && $depth > 0) {
        $c = substr($s_, $i, 1);
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
    if (!((substr($s_, 0, 1) =~ /^[a-zA-Z]$/) || substr($s_, 0, 1) eq "_")) {
        return -1;
    }
    my $i = 1;
    while ($i < length($s_)) {
        $c = substr($s_, $i, 1);
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
            if ($i < length($s_) && substr($s_, $i, 1) eq "+") {
                $i += 1;
            }
            if ($i < length($s_) && substr($s_, $i, 1) eq "=") {
                return $i;
            }
            return -1;
        }
        if ($c eq "+") {
            if ($i + 1 < length($s_) && substr($s_, $i + 1, 1) eq "=") {
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
    if (!(scalar(@{($chars // [])}) > 0)) {
        return 0;
    }
    if (!(($chars->[0] =~ /^[a-zA-Z]$/) || $chars->[0] eq "_")) {
        return 0;
    }
    my $s_ = join("", @{$chars});
    my $i = 1;
    while ($i < length($s_) && ((substr($s_, $i, 1) =~ /^[a-zA-Z0-9]$/) || substr($s_, $i, 1) eq "_")) {
        $i += 1;
    }
    while ($i < length($s_)) {
        if (substr($s_, $i, 1) ne "[") {
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
    while ($j >= 0 && substr($value, $j, 1) eq "\\") {
        $bs_count += 1;
        $j -= 1;
    }
    return $bs_count % 2 == 1;
}

sub is_dollar_dollar_paren ($value, $idx) {
    my $dollar_count = 0;
    my $j = $idx - 1;
    while ($j >= 0 && substr($value, $j, 1) eq "\$") {
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
    if (!((substr($name, 0, 1) =~ /^[a-zA-Z]$/) || substr($name, 0, 1) eq "_")) {
        return 0;
    }
    for my $c (split(//, substr($name, 1))) {
        if (!(($c =~ /^[a-zA-Z0-9]$/) || $c eq "_")) {
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
    my $self = ParseError->new("", 0, 0);
    $self->{message} = $message;
    $self->{pos_} = $pos_;
    $self->{line} = $line;
    return $self;
}

sub new_matched_pair_error ($message, $pos_, $line) {
    return MatchedPairError->new();
}

sub new_quote_state () {
    my $self = QuoteState->new(0, 0, undef);
    $self->{single} = 0;
    $self->{double} = 0;
    $self->{stack} = [];
    return $self;
}

sub new_parse_context ($kind) {
    my $self = ParseContext->new(0, 0, 0, 0, 0, 0, 0, undef);
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
    my $self = ContextStack->new(undef);
    $self->{stack} = [new_parse_context(0)];
    return $self;
}

sub new_lexer ($source, $extglob) {
    my $self = Lexer->new(undef, "", 0, 0, undef, undef, 0, 0, undef, 0, undef, "", undef, 0, 0, 0, 0, 0, 0, 0, 0, 0);
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
    my $self = Parser->new("", 0, 0, undef, 0, 0, 0, 0, undef, undef, undef, 0, 0, "", 0, 0, 0, 0, "", 0, 0);
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

1;
