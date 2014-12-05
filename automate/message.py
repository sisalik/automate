import re

from PyQt4 import QtCore, QtGui


class Message(QtGui.QWidget):
    """Shows a message box in the middle of the screen that fades out after a certain amount of time.

    Attributes:
        message: Text to be shown in the window.
        title: Title of the message window.
        timeout: Time in milliseconds to show the window for.

    The message and title arguments are passed to a simple BBCode parser to resolve some formatting tags.
    Available tags:
        [b]bolded text[/b]
        [i]italicized text[/i]
        [u]underlined text[/u]
        [s]strikethrough text[/s]
        [style size="15px"]Large Text[/style]
        [style color="red"]Red Text[/style]
        [url]http://example.org[/url]
        [url=http://example.com]Example[/url]
        [img]http://example.com/image.png[/img]
    """

    main_gui = None

    def __init__(self, message, title="", timeout=5000):
        flags = QtCore.Qt.Tool | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
        super(Message, self).__init__(None, flags)

        self.message = unicode(message)
        self.title = unicode(title)
        self.timeout = timeout

        self.init_ui()
        self.show()
        self.center()
        self.fade()

    def init_ui(self):
        # self.resize(*self.default_size)
        self.setWindowOpacity(self.default_alpha)
        self.setStyleSheet(self.stylesheet)

        # Set mouse pressed event handler
        self.mousePressEvent = self.on_timeout  # The window will be faded out when clicked

        # Vertical box layout
        self.vbox = QtGui.QVBoxLayout(self)

        # Title label
        if self.title:
            self.title_label = QtGui.QLabel(self.parse_bbcode(self.title), self)
            self.title_label.setObjectName("title")
            self.title_label.setOpenExternalLinks(True)
            self.vbox.addWidget(self.title_label)

        # Message label
        self.message_label = QtGui.QLabel(self.parse_bbcode(self.message), self)
        self.message_label.setWordWrap(True)
        self.message_label.setObjectName("message")
        self.message_label.setOpenExternalLinks(True)
        # sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        # self.message.setSizePolicy(sizePolicy)
        self.vbox.addWidget(self.message_label)

    def center(self):
        frame_geom = self.frameGeometry()
        center_point = QtGui.QDesktopWidget().screenGeometry().center()
        frame_geom.moveCenter(center_point)
        self.move(frame_geom.topLeft())

    def fade(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timeout)
        self.timer.start(self.timeout)

    def on_timeout(self, event=None):
        self.timer.stop()
        self.fade_anim = QtCore.QPropertyAnimation(self, "windowOpacity")
        self.fade_anim.setDuration(self.fade_duration)
        self.fade_anim.finished.connect(self.on_fade_finished)
        self.fade_anim.setEndValue(0)
        self.fade_anim.start()

    def on_fade_finished(self):
        self.deleteLater()
        if __name__ == "__main__":
            app.quit()

    def parse_bbcode(self, text):
        text = ''.join("<p>%s</p>" % p for p in text.split('\n'))
        subs = 1
        while subs:
            subs = 0
            # Bold, italic, underline, strikethrough
            text, n = re.subn(r"\[([bius])\](.*?)\[\/\1\]", r"<\1>\2</\1>", text)
            subs += n
            # Size
            text, n = re.subn(r'\[style size="(.*?)"\](.*?)\[\/style\]', r'<span style="font-size:\1">\2</span>', text)
            subs += n
            # Colour
            text, n = re.subn(r'\[style color="(.*?)"\](.*?)\[\/style\]', r'<span style="color:\1">\2</span>', text)
            subs += n
            # Hyperlinks
            text, n = re.subn(r"\[url\](.*?)\[\/url\]", r'<a href="\1">\1</a>', text)
            subs += n
            text, n = re.subn(r"\[url=(.*?)\](.*?)\[\/url\]", r'<a href="\1">\2</a>', text)
            subs += n
            # Images
            text, n = re.subn(r"\[img\](.*?)\[\/img\]", r'<img src="\1" />', text)
            subs += n
        return "<html><head/><body>%s</body></html>" % text


def message(message, title="", timeout=2000):
    """Sends a signal to the main GUI to create a Message widget. This is necessary while the program is running, because
    in PyQt4, most operations need to be done in the main thread."""
    Message.main_gui.message_signal.emit(message, title, timeout)

if __name__ == "__main__":
    app = QtGui.QApplication([])
    Message.default_alpha = 0.9  # Default window transparency (0..1)
    Message.fade_duration = 250  # Fade animation duration (ms)
    Message.stylesheet = """
                         Message, QLabel#title, QLabel#message {
                             color: white;
                             background: black;
                             selection-background-color: red;
                             border: none;
                             margin: 10px;
                             max-width: 800px;
                         }

                         QLabel#title {
                             font: 40pt Trebuchet MS;
                             margin-bottom: 0px;
                         }

                         QLabel#message {
                             color: #aaa;
                             font: 20pt Trebuchet MS;
                         }
                         """
    # msg = Message("Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the " +
    #               "industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and " +
    #               "scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap " +
    #               "into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the " +
    #               "release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing " +
    #               "software like Aldus PageMaker including versions of Lorem Ipsum.", "Message from the program")
    # msg = Message("Lorem Ipsum is simply dummy text of the printing and typesetting industry.", "Message")
    # msg = Message("Something went wrong. This could be because:\n- You are clumsy\n- The program isn't very good", "Error")
    # msg = Message('<html><head/><body><p>This is <span style="color:red;">red</span>!</p></body></html>', "Title")
    # msg = Message(r'<html><head/><body><p>This is a picture: <img src="C:/Windows/System32/PerfCenterCpl.ico" ' +
                  # 'height=25/></p></body></html>', "Title")
    # msg = Message("Test message")
    msg = Message('Normal\n[b]bold [i]italic [style size="50px"]huge [style color="red"]red[/style][/style][/i][/b]\n' +
                  '[url=C:/windows/notepad.exe][img]E:/Pictures/End button.png[/img][/url]', "Title", 5000)
    # message("Test")
    app.exec_()
