import argparse
import sys
from .parser import Parser, evaluate
from .toml_writer import to_toml
from .errors import ConfigError


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="config-tool", description="Translate учебный конфиг-язык -> TOML")
    p.add_argument("-i", "--input", required=True, help="Path to input config file")
    p.add_argument("-o", "--output", required=True, help="Path to output TOML file")
    args = p.parse_args(argv)

    try:
        text = open(args.input, "r", encoding="utf-8").read()
        program = Parser(text).parse_program()
        env = evaluate(program)
        out = to_toml(env)
        with open(args.output, "w", encoding="utf-8", newline="\n") as f:
            f.write(out)
        return 0
    except ConfigError as e:
        print(str(e), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
