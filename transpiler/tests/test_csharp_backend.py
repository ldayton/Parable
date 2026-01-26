"""Tests for C# backend."""

from src.backend.csharp import CSharpBackend
from tests.fixture import make_fixture

EXPECTED = """\
using System;
using System.Collections.Generic;
using System.Linq;

public static class Constants
{
    public const int Eof = -1;
}

public interface IScanner
{
    int Peek();
    void Advance();
}

public class Token
{
    public string Kind;
    public string Text;
    public int Pos;

    public Token(string kind, string text, int pos)
    {
        this.Kind = kind;
        this.Text = text;
        this.Pos = pos;
    }

    public bool IsWord()
    {
        return this.Kind == "word";
    }
}

public class Lexer
{
    public string Source;
    public int Pos;
    public Token Current;

    public Lexer(string source, int pos, Token current)
    {
        this.Source = source;
        this.Pos = pos;
        this.Current = current;
    }

    public int Peek()
    {
        if (this.Pos >= this.Source.Length)
        {
            return Constants.Eof;
        }
        return this.Source[this.Pos];
    }

    public void Advance()
    {
        this.Pos += 1;
    }

    public (Token, bool) ScanWord()
    {
        int start = this.Pos;
        while ((this.Peek() != Constants.Eof && !IsSpace(this.Peek())))
        {
            this.Advance();
        }
        if (this.Pos == start)
        {
            return (new Token(), false);
        }
        string text = this.Source.Substring(start, this.Pos - start);
        return (new Token("word", text, start), true);
    }
}

public static class FixtureFunctions
{
    public static bool IsSpace(int ch)
    {
        return (ch == 32 || ch == 10);
    }

    public static List<Token> Tokenize(string source)
    {
        Lexer lx = new Lexer(source, 0, null);
        List<Token> tokens = new List<Token>();
        while (lx.Peek() != Constants.Eof)
        {
            int ch = lx.Peek();
            if (IsSpace(ch))
            {
                lx.Advance();
                continue;
            }
            (Token, bool) result = lx.ScanWord();
            Token tok = result.Item1;
            bool ok = result.Item2;
            if (!ok)
            {
                throw new Exception("unexpected character");
            }
            tokens.Add(tok);
        }
        return tokens;
    }

    public static int CountWords(List<Token> tokens)
    {
        int count = 0;
        foreach (Token tok in tokens)
        {
            if (tok.Kind == "word")
            {
                count += 1;
            }
        }
        return count;
    }

    public static string FormatToken(Token tok)
    {
        return tok.Kind + ":" + tok.Text;
    }

    public static Token FindToken(List<Token> tokens, string kind)
    {
        foreach (Token tok in tokens)
        {
            if (tok.Kind == kind)
            {
                return tok;
            }
        }
        return null;
    }

    public static string ExampleNilCheck(List<Token> tokens)
    {
        Token tok = FindToken(tokens, "word");
        if (tok == null)
        {
            return "";
        }
        return tok.Text;
    }

    public static int SumPositions(List<Token> tokens)
    {
        int sum = 0;
        for (int i = 0; i < tokens.Count; i++)
        {
            sum = (sum + tokens[i].Pos);
        }
        return sum;
    }

    public static int FirstWordPos(List<Token> tokens)
    {
        int pos = -1;
        foreach (Token tok in tokens)
        {
            if (tok.Kind == "word")
            {
                pos = tok.Pos;
                break;
            }
        }
        return pos;
    }

    public static int MaxInt(int a, int b)
    {
        return (a > b ? a : b);
    }

    public static Dictionary<string, int> DefaultKinds()
    {
        return new Dictionary<string, int> { { "word", 1 }, { "num", 2 }, { "op", 3 } };
    }

    public static int ScopedWork(int x)
    {
        int result = 0;
        {
            int temp = (x * 2);
            result = (temp + 1);
        }
        return result;
    }

    public static int KindPriority(string kind)
    {
        switch (kind)
        {
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

    public static List<Token> SafeTokenize(string source)
    {
        List<Token> tokens = new List<Token>();
        try
        {
            tokens = Tokenize(source);
        }
        catch (Exception)
        {
            tokens = new List<Token>();
        }
        return tokens;
    }

    public static double Pi()
    {
        return 3.14159;
    }

    public static string DescribeToken(Token tok)
    {
        return $"Token({tok.Kind}, {tok.Text}, {tok.Pos})";
    }

    public static void SetFirstKind(List<Token> tokens, string kind)
    {
        if (tokens.Count > 0)
        {
            tokens[0] = new Token(kind, "", 0);
        }
    }

    public static List<int> MakeIntSlice(int n)
    {
        return new List<int>(n);
    }

    public static double IntToFloat(int n)
    {
        return (double)(n);
    }

    public static HashSet<string> KnownKinds()
    {
        return new HashSet<string> { "word", "num", "op" };
    }

    public static Token CallStatic()
    {
        return Token.Empty();
    }

    public static Dictionary<string, int> NewKindMap()
    {
        return new Dictionary<string, int>();
    }

    public static int GetArrayFirst(int[] arr)
    {
        return arr[0];
    }

    public static Token MaybeGet(List<Token> tokens, int idx)
    {
        if (idx >= tokens.Count)
        {
            return null;
        }
        return tokens[idx];
    }

    public static void SetViaPtr(int ptr, int val)
    {
        ptr = val;
    }

    public static string IdentityStr(string s)
    {
        return s;
    }

    public static bool AcceptUnion(object obj)
    {
        return true;
    }
}"""


def test_fixture_emits_correct_csharp() -> None:
    module = make_fixture()
    backend = CSharpBackend()
    output = backend.emit(module)
    assert output == EXPECTED
