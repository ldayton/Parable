"""Tests for Java backend."""

from src.backend.java import JavaBackend
from tests.fixture import make_fixture

EXPECTED = """\
import java.util.*;

final class Constants {
    public static final int EOF = -1;
}

interface Scanner {
    int peek();
    void advance();
}

class Token {
    String kind;
    String text;
    int pos;

    Token(String kind, String text, int pos) {
        this.kind = kind;
        this.text = text;
        this.pos = pos;
    }

    boolean isWord() {
        return this.kind.equals("word");
    }
}

class Lexer {
    String source;
    int pos;
    Token current;

    Lexer(String source, int pos, Token current) {
        this.source = source;
        this.pos = pos;
        this.current = current;
    }

    int peek() {
        if ((this.pos >= this.source.length())) {
            return Constants.EOF;
        }
        return this.source.charAt(this.pos);
    }

    void advance() {
        this.pos += 1;
    }

    Object[] scanWord() {
        int start = this.pos;
        while (((this.peek() != Constants.EOF) && !isSpace(this.peek()))) {
            this.advance();
        }
        if ((this.pos == start)) {
            return new Object[]{new Token(), false};
        }
        String text = this.source.substring(start, this.pos);
        return new Object[]{new Token("word", text, start), true};
    }
}

final class FixtureFunctions {
    private FixtureFunctions() {}

    static boolean isSpace(int ch) {
        return ((ch == 32) || (ch == 10));
    }

    static ArrayList<Token> tokenize(String source) {
        Lexer lx = new Lexer(source, 0, null);
        ArrayList<Token> tokens = new ArrayList<Token>();
        while ((lx.peek() != Constants.EOF)) {
            int ch = lx.peek();
            if (isSpace(ch)) {
                lx.advance();
                continue;
            }
            Object[] result = lx.scanWord();
            Token tok = result[0];
            boolean ok = result[1];
            if (!ok) {
                throw new RuntimeException("unexpected character");
            }
            tokens.add(tok);
        }
        return tokens;
    }

    static int countWords(ArrayList<Token> tokens) {
        int count = 0;
        for (Token tok : tokens) {
            if (tok.kind.equals("word")) {
                count += 1;
            }
        }
        return count;
    }

    static String formatToken(Token tok) {
        return tok.kind + ":" + tok.text;
    }

    static Token findToken(ArrayList<Token> tokens, String kind) {
        for (Token tok : tokens) {
            if (tok.kind.equals(kind)) {
                return tok;
            }
        }
        return null;
    }

    static String exampleNilCheck(ArrayList<Token> tokens) {
        Token tok = findToken(tokens, "word");
        if ((tok == null)) {
            return "";
        }
        return tok.text;
    }

    static int sumPositions(ArrayList<Token> tokens) {
        int sum = 0;
        for (int i = 0; (i < tokens.size()); i = (i + 1)) {
            sum = (sum + tokens.get(i).pos);
        }
        return sum;
    }

    static int firstWordPos(ArrayList<Token> tokens) {
        int pos = -1;
        for (Token tok : tokens) {
            if (tok.kind.equals("word")) {
                pos = tok.pos;
                break;
            }
        }
        return pos;
    }

    static int maxInt(int a, int b) {
        return ((a > b) ? a : b);
    }

    static HashMap<String, Integer> defaultKinds() {
        return new HashMap<String, Integer>(Map.of("word", 1, "num", 2, "op", 3));
    }

    static int scopedWork(int x) {
        int result = 0;
        {
            int temp = (x * 2);
            result = (temp + 1);
        }
        return result;
    }

    static int kindPriority(String kind) {
        switch (kind) {
            case "word":
                return 1;
            case "num":
            case "float":
                return 2;
            case "op":
                return 3;
            default:
                return 0;
        }
    }

    static ArrayList<Token> safeTokenize(String source) {
        ArrayList<Token> tokens = new ArrayList<Token>();
        try {
            tokens = tokenize(source);
        } catch (Exception e) {
            tokens = new ArrayList<Token>();
        }
        return tokens;
    }

    static double pi() {
        return 3.14159;
    }

    static String describeToken(Token tok) {
        return String.format("Token(%s, %s, %s)", tok.kind, tok.text, tok.pos);
    }

    static void setFirstKind(ArrayList<Token> tokens, String kind) {
        if ((tokens.size() > 0)) {
            tokens.set(0, new Token(kind, "", 0));
        }
    }

    static ArrayList<Integer> makeIntSlice(int n) {
        return new ArrayList<Integer>(n);
    }

    static double intToFloat(int n) {
        return (double) (n);
    }

    static HashSet<String> knownKinds() {
        return new HashSet<String>(Arrays.asList("word", "num", "op"));
    }

    static Token callStatic() {
        return Token.empty();
    }

    static HashMap<String, Integer> newKindMap() {
        return new HashMap<String, Integer>();
    }

    static int getArrayFirst(int[] arr) {
        return arr[0];
    }

    static Token maybeGet(ArrayList<Token> tokens, int idx) {
        if ((idx >= tokens.size())) {
            return null;
        }
        return tokens.get(idx);
    }

    static void setViaPtr(int ptr, int val) {
        ptr = val;
    }

    static String identityStr(String s) {
        return s;
    }

    static boolean acceptUnion(Object obj) {
        return true;
    }
}"""


def test_fixture_emits_correct_java() -> None:
    module = make_fixture()
    backend = JavaBackend()
    output = backend.emit(module)
    assert output == EXPECTED
