from dataclasses import dataclass


@dataclass
class ConfigError(Exception):
    message: str
    line: int
    col: int
    snippet: str = ""

    def __str__(self) -> str:
        where = f"{self.line}:{self.col}"
        if self.snippet:
            return f"{where}: {self.message}\n{self.snippet}"
        return f"{where}: {self.message}"
