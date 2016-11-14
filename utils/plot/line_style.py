"""
Enum for Matplotlib line style strings
"""
from enum import Enum

class MPL_LineStyle(Enum):
    solid_line            = '-'
    dashed_line           = '--'
    dash_dot_line         = '-.'
    dotted_line           = ':'
    point                 = '.'
    pixel                 = ','
    circle                = 'o'
    triangle_down         = 'v'
    triangle_up           = '^'
    triangle_left         = '<'
    triangle_right        = '>'
    tri_down              = '1'
    tri_up                = '2'
    tri_left              = '3'
    tri_right             = '4'
    square                = 's'
    pentagon              = 'p'
    star                  = '*'
    hexagon1              = 'h'
    hexagon2              = 'H'
    plus                  = '+'
    x                     = 'x'
    diamond               = 'D'
    thin_diamond          = 'd'
    vline                 = '|'
    hline                 = '_'


class MPL_Color(Enum):
    blue    = 'b'
    green   = 'g'
    red     = 'r'
    cyan    = 'c'
    magenta = 'm'
    yellow  = 'y'
    black   = 'k'
    white   = 'w'
