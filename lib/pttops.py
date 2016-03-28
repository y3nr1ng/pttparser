from . import Ptt
from .pttcmd import BoardCmd

class PttOps(object):

    def __init__(self, ptt_conn):
        self.ptt_conn = ptt_conn

    def to_board(self, board):
        self.ptt_conn.send(str(BoardCmd.search), newline = False)
        self.ptt_conn.send(board)
        self.ptt_conn.send()
