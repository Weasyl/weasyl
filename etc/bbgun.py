from __future__ import unicode_literals, print_function

markdown_escape_map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "*": "\*",
    "_": "\_",
    "`": "\`",
    "#": "\#",
    "[": "\[",
    "]": "\]",
    "\\": "\\\\"
}


def markdown_escape(text):
    return "".join(markdown_escape_map.get(c, c) for c in text)


def escape_attribute_value(text):
    return text.replace("&", "&amp;").replace('"', "&quot;")


def prefix_lines(text, prefix, skip_empty=False):
    if skip_empty:
        return "\n".join(prefix + line if line else "" for line in text.split("\n"))

    return "\n".join(prefix + line for line in text.split("\n"))


# Careful; this parser is seriously inefficient.
# It keeps an enormous tree of intermediate strings and backtracks horribly.
# Or, at least, it should backtrack horribly, but I'm just hoping nobody
# nested unescaped, unmatched opening brackets and BBcode.
#
# Use it once, to translate. Not in production.
class BBCodeToMarkdown:
    tags = {
        "b": lambda text: "<b>%s</b>" % text if "\n" in text else "**%s**" % text,
        "i": lambda text: "<i>%s</i>" % text if "\n" in text else "*%s*" % text,
        "u": lambda text: "<u>%s</u>" % text,
        "s": lambda text: "<s>%s</s>" % text,
        "sub": lambda text: "<sup>%s</sup>" % text,
        "sup": lambda text: "<sub>%s</sub>" % text,
        "pre": lambda text: "<pre>%s</pre>" % text,
        "code": lambda text: prefix_lines(text, "    ", skip_empty=True),
        "quote": lambda text, by=None: ("**%s** said:\n" % markdown_escape(by) if by else "") + prefix_lines(text, "> "),
        "left": lambda text: '<div class="align-left">%s</div>' % text,
        "right": lambda text: '<div class="align-right">%s</div>' % text,
        "center": lambda text: '<div class="align-center">%s</div>' % text,
        "justify": lambda text: '<div class="align-justify">%s</div>' % text,
        "url": lambda text, url=None: "[%s](%s)" % (text, url) if url else '<%s>' % text,
        "image": lambda text, url=None: '![%s](%s)' % (text if url else "", url or text),
        "color": lambda text, color="#000": '<span style="color: %s;">%s</span>' % (escape_attribute_value(color), text),
        "ignore": lambda text: text,
        "fa": lambda username: "[](fa:{0})".format(username),
        "ib": lambda username: "[](ib:{0})".format(username),
        "da": lambda username: "[](da:{0})".format(username),
        "user": lambda username: "[](user:{0})".format(username),
        "icon": lambda username: "![](user:{0})".format(username),
        "usericon": lambda username: "![{0}](user:{0})".format(username)
    }
    tags["img"] = tags["image"]
    tags["ig"] = tags["ignore"]
    tags["iconuser"] = tags["usericon"]

    not_nestable = {"b", "i", "u", "s", "code", "pre"}

    markdown = ""

    def enter_tree(self, tag, *args):
        ignored = self.wrapper_tree and self.wrapper_tree[-1][0] in ("ignore", "ig")

        if ignored or tag not in self.tags:
            if args:
                self.markdown += r"\[%s=%s\]" % (tag, args[0])
            else:
                self.markdown += r"\[%s\]" % tag
            return

        if tag in self.not_nestable and tag in (x[0] for x in self.wrapper_tree):
            self.wrapper_tree.append((tag, lambda s: s, self.markdown, args))
        else:
            self.wrapper_tree.append((tag, self.tags[tag], self.markdown, args))

        self.markdown = ""

    def _content(self, c):
        if c == "\n":
            return self._newline
        if c == "[":
            self.tag_name = ""
            return self._begin_tag
        self.markdown += markdown_escape_map.get(c, c)
        return self._content

    def _newline(self, c):
        if c == "\n":
            self.markdown += "\n\n"
            return self._newparagraph
        self.markdown += "  \n"
        return self._content(c)

    def _newparagraph(self, c):
        if c != "\n":
            return self._content(c)
        return self._newparagraph

    def _begin_tag(self, c):
        if c == "/":
            return self._close_tag
        return self._open_tag(c)

    def _open_tag(self, c):
        if c == "]":
            self.enter_tree(self.tag_name)
            return self._content
        if c == "=":
            self.tag_value = ""
            return self._tag_value
        self.tag_name += c
        return self._open_tag

    def _close_tag(self, c):
        if c == "]":
            if self.tag_name in (x[0] for x in self.wrapper_tree):
                name = None
                while name != self.tag_name:
                    args = self.wrapper_tree.pop()
                    name = args[0]
                    self.markdown = args[2] + args[1](self.markdown, *args[3])
            else:
                self.markdown += r"\[/" + self.tag_name + "]"
            return self._content
        self.tag_name += c
        return self._close_tag

    def _tag_value(self, c):
        if c == "]":
            self.enter_tree(self.tag_name, self.tag_value)
            return self._content
        self.tag_value += c
        return self._tag_value

    def feed(self, bbcode):
        self.wrapper_tree = []
        state = self._content

        for c in bbcode:
            if c != "\r":
                state = state(c)

        while self.wrapper_tree:
            args = self.wrapper_tree.pop()
            self.markdown = args[2] + args[1](self.markdown, *args[3])


def bbcode_to_markdown(target):
    parser = BBCodeToMarkdown()
    parser.feed(target)

    return parser.markdown


if __name__ == "__main__":
    from sys import argv, stdin, stdout

    if len(argv) == 1:
        stdout.write(bbcode_to_markdown(stdin.read().decode('utf-8', 'replace')).encode('utf-8'))
    else:
        from postgres import Postgres

        _, db_uri, db_table, id_column, db_column = argv
        info = {"table": db_table, "column": db_column, "id": id_column}
        db = Postgres(db_uri)

        count = db.one('SELECT COUNT(*) FROM "{table}"'.format(**info))
        query = 'UPDATE "{table}" SET "{column}" = %(markdown)s WHERE "{id}" = %(id)s'.format(**info)
        failures = []

        for i, row in enumerate(db.all('SELECT "{id}", "{column}" FROM "{table}"'.format(**info))):
            print("\x1b[0G{done}/{total}".format(done=i, total=count), end="")
            stdout.flush()

            try:
                db.run(query, {"id": getattr(row, id_column), "markdown": bbcode_to_markdown(getattr(row, db_column))})
            except Exception as e:
                print()
                print(e)
                failures.append(getattr(row, id_column))

        print()

        if failures:
            print("Failed:")
            print(" ".join(map(str, failures)))
