from enum import Enum

class BoardCmd(Enum):
    search = 's'
    prev = 'p'
    next = 'n'

    def __str__(self):
        return str(self.value)
