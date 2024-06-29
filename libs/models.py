import struct
from collections.abc import Buffer


class MPKFileInfo:
    _flag: bool
    _index: int
    _offset: int
    _size: int
    _unknown: int
    _name: str

    def __init__(self, flag: bool = False, index: int = 0, offset: int = 0, size: int = 0, name: str = ""):
        self._flag = flag
        self._index = index
        self._offset = offset
        self._size = size
        self._name = name

    @property
    def flag(self) -> bool:
        return self._flag

    @flag.setter
    def flag(self, value: bool):
        self._flag = value

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, value: int):
        self._index = value

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def offset(self) -> int:
        return self._offset

    @offset.setter
    def offset(self, value: int):
        self._offset = value

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value: int):
        self._size = value

    @staticmethod
    def unpack(buffer: Buffer) -> "MPKFileInfo":
        unpacked = struct.unpack("?I3Q224s", buffer)
        return MPKFileInfo(
            flag=unpacked[0],
            index=unpacked[1],
            offset=unpacked[2],
            size=unpacked[3],
            # unpacked[4]
            name=unpacked[5].decode("shift_jis").strip("\x00")
        )
