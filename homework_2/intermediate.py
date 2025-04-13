"""Intermediate level"""

#========Task await========
from typing import Awaitable

def run_async(arg: Awaitable[int]):
    ...

#========Task callable========

from typing import Callable

SingleStringInput = Callable[[str], None]

#========Task class-var========

from typing import ClassVar

class Foo:
	bar: ClassVar[int]

#========Task decorator========

from typing import Callable, TypeVar

T = TypeVar("T", bound=Callable)

def decorator(func: T) -> T:
    return func

#========Task empty-tuple========

def foo(x: tuple[()]):
    pass

#========Task generic========

from typing import TypeVar

T_1 = TypeVar("T_1")

def add(a: T_1, b: T_1) -> T_1:
    return a

#========Task generic2========

from typing import TypeVar

T_2 = TypeVar("T_2", str, int)


def add_2(a: T_2, b: T_2) -> T_2:
    return a

#========Task generic3========

from typing import TypeVar

T_3 = TypeVar("T_3", bound=int)

def add_3(a: T_3) -> T_3:
    return a

#========Task instance-var========

class Foo_2:
    bar: int

#========Task literal========

from typing import Literal

def foo_literal(direction: Literal['left', 'right']):
    ...


#========Task literalstring========

from typing import Iterable, LiteralString


def execute_query(sql: LiteralString, parameters: Iterable[str] = ...):
    pass

#========Task self========

from typing import Self


class Foo_self:
    def return_self(self) -> Self:
        return self

#========Task typed-dict========

from typing import TypedDict

class Student(TypedDict):
    name: str
    age: int
    school: str


#========Task typed-dict2========

from typing import TypedDict, NotRequired

class Student_2(TypedDict):
    name: str
    age: int
    school: NotRequired[str]

#========Task typed-dict3========

from typing import TypedDict, Required
class Person(TypedDict, total = False):
    name: Required[str]
    age: int
    gender: str
    address: str
    email: str

#========Task unpack========

from typing import TypedDict, Unpack


class Person_2(TypedDict):
    name: str
    age: int


def foo_unpack(**kwargs: Unpack[Person_2]):
    ...
