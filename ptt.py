import sys, paramiko, re, time, base64

class Ptt(object):

    def __init__(self):
        # SSH client object
        self.client = paramiko.SSHClient()
        # loop delay interval
        self.delay = 0.5
        # timeout for responses
        self.timeout = 5.0
        # screen size
        self.width = 80
        self.height = 24
        # screen buffer
        self.screen = ''
        self.buf_size = self.width * self.height

    def __enter__(self):
        self.client.load_system_host_keys()
        self.client.set_missing_host_key_policy(paramiko.WarningPolicy())
        return self

    # establish the actual SSH connection
    def __establish(self):
        try:
            self.client.connect('ptt.cc', username = 'bbsu', password = '')
        except paramiko.AuthenticationException:
            print('... Authentication failed')
            sys.exit(1)
        except Exception as e:
            print('... Connection failed:', str(e))
            sys.exit(1)

        try:
            self.channel = self.client.invoke_shell(width = self.width,
                                                    height = self.height)
        except paramiko.SSHException:
            print('... Cannot open interactive channel')
            sys.exit(1)

        # set channel timeout to 1 second
        self.channel.settimeout(self.timeout)

    # set timeout for server response
    def set_timeout(t):
        if t >= 0:
            self.timeout = t
        else:
            print('... Timeout needs to be positive')

    # set emulated terminal size, default to 80x24
    def set_screen_size(width = None, heigth = None):
        if width != None:
            self.width = width
        if height != None:
            self.height = height

    # provide username and password to the server
    def connect(self, username, password, use_b64 = True):
        self.__establish()

        # dummy read
        self.get_screen()
        # send the username and password
        self.send(username)
        if use_b64:
            password = base64.b64decode(password).decode('utf-8')
        self.send(password)

        # send CR to get into the directory
        self.send('')

    # send raw commands to the server
    def send(self, cmd = None, newline = True, debug = False):
        while not self.channel.send_ready():
            time.sleep(self.delay)
        if cmd == None:
            cmd = ' '
        if newline:
            cmd += '\r'
        if debug:
            print('send [', cmd, ']')
        self.channel.send(cmd)

    # retrieve cleaned screen from the server
    def get_screen(self, wait = True, debug = False):
        if wait:
            time.sleep(self.timeout)

        screen = self.__wait_str()
        while self.channel.recv_ready():
            screen += self.__recv_str(self.buf_size)

        if debug:
            print('=== Received ===')
            print(screen)
            print('================')
        screen = self.__clean_up(screen)

        return screen

    # wait for response from the server to trigger continuous retrieval
    def __wait_str(self):
        ch = ''
        while True:
            ch = self.channel.recv(1)
            if ch:
                break
        return self.__dec_bytes(ch)

    # retrieve designated length of string from the byte buffer
    def __recv_str(self, buf_size = 1920):
        return self.__dec_bytes(self.channel.recv(buf_size))

    # decode byte array to UTF-8 string
    def __dec_bytes(self, bytes):
        return bytes.decode('utf-8', errors = 'ignore')

    # clean up the control code in the raw screen
    def __clean_up(self, screen,
                   nocolor = True, nocr = True, noesc = True):
        if not screen:
            return screen
        if nocolor:
            # remove color codes
            screen = re.sub('\[[\d+;]*[mH]', '', screen)
        if nocr:
            # remove carriage return
            screen = re.sub(r'[\r]', '', screen)
        if noesc:
            # remove escape cahracters, capabale of partial replace
            screen = re.sub(r'[\x00-\x08]', '', screen)
            screen = re.sub(r'[\x0b\x0c]', '', screen)
            screen = re.sub(r'[\x0e-\x1f]', '', screen)
            screen = re.sub(r'[\x7f-\xff]', '', screen)
        return screen

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self, 'channel'):
            self.channel.close()
        self.client.close()
