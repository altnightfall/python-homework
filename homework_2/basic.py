"""Basic level"""


#========Task any========

def any_foo(arg):
    """⬆️ Change me. No need to implement the function."""
    pass

#========Task dict========

def dict_foo(x: dict[str, str]):
    pass

#========Task final========
from typing import Final

my_list: Final[list] = []

#========Task kwargs========

def kwargs_foo(**kwargs: int | str):
    pass

#========Task kwargs========

def list_foo(x: list[str]):
    pass

#========Task optional========

def optional_foo(x: int | None = None):
    pass

#========Task parameter========

def parameter_foo(x: int):
    pass

#========Task return========

def return_foo() -> int:
    return 1

#========Task tuple========

def foo(x:tuple[str,int]):
    pass

#========Task typealias========

from typing import TypeAlias

Vector: TypeAlias = list[float]

#========Task union========

def union_foo(x: str | int):
    pass

#========Task variable========
a: int
