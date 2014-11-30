import re

from PyQt4 import QtCore, QtGui


class TipBox(object):

    def __init__(self, parent, (x0, y0), (w, h), max_rows):
        self.parent = parent
        self.max_rows = max_rows
        self.w = w
        self.h = h

        self.rows = 0
        self.selected = 0

        # Get the highlight colour from the master stylesheet
        self.highlight_colour = re.search(r"QLabel#tip_line[\S\s]*?selection-color:\s*(.*?)\s*;",
                                          self.parent.styleSheet()).group(1)

        # Create label widgets
        self.lines = []
        for i in xrange(self.max_rows):
            line = QtGui.QLabel(parent=self.parent)

            x = x0
            y = y0 + i * self.h
            line.setGeometry(QtCore.QRect(x, y, self.w, self.h))
            line.setObjectName("tip_line")
            line.mousePressEvent = lambda e, i=i: self.on_click(e, i)
            self.lines.append(line)

    def highlight(self, text, pattern):
        text = text.decode("utf-8")
        pattern = pattern.decode("utf-8")
        start = 0
        for c in pattern.lower():
            pos = text.lower().find(c, start)
            if pos != -1:
                highlighted = r'<span style="color:%s;">%s</span>' % (self.highlight_colour, text[pos])
                start = pos + len(highlighted)
                text = text[:pos] + highlighted + text[pos + 1:]
        return "<html><head/><body><p>%s</p></body></html>" % text
        # return r"""
        #     <html>
        #         <head/>
        #         <body>
        #             <table valign="middle">
        #                 <tr>
        #                     <td width=25><img src="C:\Windows\winsxs\amd64_microsoft-windows-dxp-deviceexperience_31bf3856ad364e35_6.1.7600.16385_none_a31a1d6b13784548\settings.ico" height="20"/></td>
        #                     <td>%s</td>
        #                 </tr>
        #             </table>
        #         </body>
        #     </html>""" % text

    def set_text(self, content, pattern=None):
        content = list(content)  # In case it's a generator
        self.content = content

        for line, text in zip(self.lines, content):
            if pattern:
                line.setText(self.highlight(text, pattern))
            else:
                line.setText(text.decode("utf-8"))

        self.selected = 0
        self.select(self.selected)
        self.rows = min(len(self.content), self.max_rows)

        self.parent.slide(self.h * self.rows)

    def get_selection(self):
        temp = QtGui.QTextDocument()
        temp.setHtml(self.lines[self.selected].text())
        text = temp.toPlainText()  # No icons
        # text = temp.toPlainText()[3:-1]
        return unicode(text).encode("utf-8")

    def select(self, index):
        for i, line in enumerate(self.lines):
            if i == index:
                line.setProperty("selected", True)
            else:
                line.setProperty("selected", False)
            line.setStyleSheet("")  # Update stylesheet

    def down(self,):
        if 0 <= self.selected < self.rows - 1:
            self.selected += 1
        else:
            self.selected = 0
        self.select(self.selected)

    def up(self):
        if 0 < self.selected < self.rows:
            self.selected -= 1
        else:
            self.selected = self.rows - 1
        self.select(self.selected)

    def on_click(self, event, index):
        self.selected = index
        self.parent.run_command()
