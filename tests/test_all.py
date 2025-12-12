import pytest
from config_tool.parser import Parser, evaluate
from config_tool.toml_writer import to_toml
from config_tool.errors import ConfigError


def run(text: str):
    program = Parser(text).parse_program()
    env = evaluate(program)
    return env, to_toml(env)


def test_numbers_and_assign():
    env, toml = run("def A := 0\ndef B := -12\ndef C := +7\n")
    assert env["A"] == 0
    assert env["B"] == -12
    assert env["C"] == 7
    assert "A = 0" in toml


def test_string():
    env, toml = run('def MSG := @"Привет"\n')
    assert env["MSG"] == "Привет"
    assert 'MSG = "Привет"' in toml


def test_list_simple():
    env, _ = run("def ARR := (list 1 2 3)\n")
    assert env["ARR"] == [1, 2, 3]


def test_list_nested():
    env, _ = run("def X := (list 1 (list 2 3) 4)\n")
    assert env["X"] == [1, [2, 3], 4]


def test_constref():
    env, _ = run("def A := 10\ndef B := (list #{A} #{A} 5)\n")
    assert env["B"] == [10, 10, 5]


def test_comments_single_line():
    env, _ = run("% comment\n def A := 1 % tail\n def B := 2\n")
    assert env["A"] == 1 and env["B"] == 2


def test_comments_multiline():
    text = """{{!--
multi
line
--}}
def A := 1
"""
    env, _ = run(text)
    assert env["A"] == 1


def test_error_bad_identifier():
    with pytest.raises(ConfigError):
        run("def AbC := 1\n")  # must be [A-Z]+


def test_error_undefined_const():
    with pytest.raises(ConfigError):
        run("def B := #{A}\n")


def test_error_unterminated_string():
    with pytest.raises(ConfigError):
        run('def A := @"oops\n')


def test_error_unterminated_list():
    with pytest.raises(ConfigError):
        run("def A := (list 1 2\n")


def test_error_unterminated_multiline_comment():
    with pytest.raises(ConfigError):
        run("{{!-- no end\n def A := 1\n")
