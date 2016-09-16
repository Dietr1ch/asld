#!/bin/python
"""
Wrapper for basic command-line color escape sequences
"""

from enum import Enum


class Color(Enum):
    """Term color codes"""
    BLACK   = '\033[90m'
    RED     = '\033[91m'
    GREEN   = '\033[92m'
    YELLOW  = '\033[93m'
    BLUE    = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN    = '\033[96m'
    WHITE   = '\033[97m'

    END    = '\033[0m'

    def __call__(self, s: str) -> str:
        """Returns colored string"""
        return "%s%s%s" % (self, s, Color.END)

    def __str__(self):
        return self.value

    def print(self, s:str) -> None:
        """Prints to stdout"""
        print(self(s))


def color_test():
    """
    Showoff
    """
    Color.BLACK  .print("BLACK  ")
    Color.RED    .print("RED    ")
    Color.GREEN  .print("GREEN  ")
    Color.YELLOW .print("YELLOW ")
    Color.BLUE   .print("BLUE   ")
    Color.MAGENTA.print("MAGENTA")
    Color.CYAN   .print("CYAN   ")
    Color.WHITE  .print("WHITE  ")


if __name__=='__main__':
    color_test()
