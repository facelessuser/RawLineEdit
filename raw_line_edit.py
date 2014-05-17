# -*- coding: utf-8 -*-

"""
Raw Line Edit
Licensed under MIT
Copyright (c) 2013 Isaac Muse <isaacmuse@gmail.com>
"""
from __future__ import unicode_literals
import sublime
import sublime_plugin
import codecs

import re

new_line = "¬"


def strip_newline_glyph(text):
    return re.sub(r"%s\n" % new_line, "\n", text)


def add_newline_glyph(text):
    return re.sub(r"\n", "%s\n" % new_line, text)


def strip_carriage_returns(text, glyph):
    new_line_glyph = new_line if glyph else ""
    return re.sub(r"\r*%s\n" % new_line_glyph, "%s\n" % new_line_glyph, text)


def add_carriage_returns(text, glyph):
    new_line_glyph = new_line if glyph else ""
    return re.sub(r"(?<!\r)%s\n" % new_line_glyph, "\r%s\n" % new_line_glyph, text)


def use_newline_glyph():
    return bool(sublime.load_settings("raw_line_edit.sublime-settings").get("use_newline_glyph", False))


def use_theme():
    return bool(sublime.load_settings("raw_line_edit.sublime-settings").get("use_raw_line_edit_theme", False))


def get_encoding(view):
    encoding = view.encoding()
    mapping = [
        ("with BOM", ""),
        ("Windows", "cp"),
        ("-", "_"),
        (" ", "")
    ]
    encoding = view.encoding()
    m = re.match(r'.+\((.*)\)', encoding)
    if m is not None:
        encoding = m.group(1)

    for item in mapping:
        encoding = encoding.replace(item[0], item[1])

    return "utf_8" if encoding in ["Undefined", "Hexidecimal"] else encoding


class ToggleRawLineEditCommand(sublime_plugin.TextCommand):
    def disable_rle(self, edit, file_name):
        if self.view.is_dirty():
            if sublime.ok_cancel_dialog("Raw Line Edit:\nFile has unsaved changes.  Save?"):
                self.view.run_command("save")
        self.view.set_scratch(True)
        file_name = self.view.settings().get("RawLineEditFilename")
        syntax = self.view.settings().get("RawLineEditSyntax")
        win = self.view.window()
        temp = None
        if len(win.views()) <= 1:
            temp = win.new_file()
        win.focus_view(self.view)
        win.run_command("close_file")
        new_view = win.open_file(file_name)
        if temp is not None:
            win.focus_view(temp)
            win.run_command("close_file")
        win.focus_view(new_view)
        new_view.set_syntax_file(syntax)

    def enable_rle(self, edit, file_name):
        if self.view.is_dirty():
            if sublime.ok_cancel_dialog("Raw Line Edit:\nFile has unsaved changes.  Save?"):
                self.view.run_command("save")
        encoding = get_encoding(self.view)
        try:
            self.show_rle(edit, file_name, encoding)
        except:
            self.show_rle(edit, file_name, "utf-8")

    def show_rle(self, edit, file_name, encoding):
        with codecs.open(file_name, "r", encoding) as f:
            use_glyph = use_newline_glyph()
            if use_glyph:
                self.view.replace(edit, sublime.Region(0, self.view.size()), add_newline_glyph(f.read()))
            else:
                self.view.replace(edit, sublime.Region(0, self.view.size()), f.read())
            self.view.set_line_endings("Unix")
            self.view.settings().set("RawLineEditGlyph", use_glyph)
            self.view.settings().set("RawLineEdit", True)
            self.view.settings().set("RawLineEditSyntax", self.view.settings().get('syntax'))
            self.view.settings().set("RawLineEditFilename", file_name)
            if use_theme():
                self.view.set_syntax_file("Packages/RawLineEdit/RawLineEdit.hidden-tmLanguage")
            self.view.set_scratch(True)
            self.view.set_read_only(True)

    def is_enabled(self):
        return not bool(sublime.load_settings("raw_line_edit.sublime-settings").get("view_only", False)) or self.view.settings().get("RawLineEdit", False)

    def run(self, edit):
        file_name = self.view.file_name()
        if (file_name is not None or self.view.settings().get("RawLineEdit", False)) and not self.view.settings().get('RawLineEditPopup', False):
            if self.view.settings().get("RawLineEdit", False):
                self.disable_rle(edit, file_name)
            else:
                self.enable_rle(edit, file_name)


class PopupRawLineEditCommand(sublime_plugin.TextCommand):
    def popup_rle(self, file_name):
        if self.view.is_dirty():
            if sublime.ok_cancel_dialog("Raw Line Edit:\nFile has unsaved changes.  Save?"):
                self.view.run_command("save")
        encoding = get_encoding(self.view)
        try:
            self.show_rle(file_name, encoding)
        except:
            self.show_rle(file_name, "utf-8")

    def show_rle(self, file_name, encoding):
        try:
            view = self.view.window().get_output_panel('raw_line_edit_view')
            with codecs.open(file_name, "r", encoding) as f:
                view.set_read_only(False)
                use_glyph = use_newline_glyph()
                RawLinesEditReplaceCommand.region = sublime.Region(0, view.size())
                if use_glyph:
                    RawLinesEditReplaceCommand.text = add_newline_glyph(f.read())
                else:
                    RawLinesEditReplaceCommand.text = f.read()
                view.run_command("raw_lines_edit_replace")
                view.sel().clear()
                view.set_syntax_file(self.view.settings().get('syntax') if not use_theme() else "Packages/RawLineEdit/RawLineEdit.hidden-tmLanguage")
                view.settings().set("RawLineEditSyntax", self.view.settings().get('syntax'))
                view.settings().set("RawLineEditGlyph", use_glyph)
                view.settings().set("RawLineEdit", True)
                view.settings().set("RawLineEditFilename", file_name)
                view.settings().set("RawLineEditPopup", True)
                self.view.set_scratch(True)
                view.set_read_only(True)
                self.view.window().run_command("show_panel", {"panel": "output.raw_line_edit_view"})
        except:
            self.view.window().run_command("hide_panel", {"panel": "output.raw_line_edit_view"})
            raise

    def is_enabled(self):
        return bool(sublime.load_settings("raw_line_edit.sublime-settings").get("view_only", False))

    def run(self, edit):
        file_name = self.view.file_name()
        if (file_name is not None or self.view.settings().get("RawLineEdit", False)) and not self.view.settings().get('RawLineEditPopup', False):
            self.popup_rle(file_name)


class RawLineInsertCommand(sublime_plugin.TextCommand):
    def run(self, edit, style="Unix"):
        self.view.set_scratch(False)
        self.view.set_read_only(False)
        use_glyph = self.view.settings().get("RawLineEditGlyph")
        for s in reversed(self.view.sel()):
            line_region = self.view.full_line(s)
            if style == "Unix":
                self.view.replace(edit, line_region, strip_carriage_returns(self.view.substr(line_region), use_glyph))
            else:
                self.view.replace(edit, line_region, add_carriage_returns(self.view.substr(line_region), use_glyph))
        self.view.set_read_only(True)


class RawLinesEditReplaceCommand(sublime_plugin.TextCommand):
    text = None
    region = None

    def run(self, edit):
        cls = RawLinesEditReplaceCommand
        if cls.text is not None and cls.region is not None:
            self.view.replace(edit, cls.region, cls.text)
        cls.text = None
        cls.region = None


class RawLineEditListener(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        if view.settings().get("RawLineEdit", False) and not view.settings().get('RawLineEditPopup', False):
            use_glyph = view.settings().get("RawLineEditGlyph")
            RawLinesEditReplaceCommand.region = sublime.Region(0, view.size())
            if use_glyph:
                RawLinesEditReplaceCommand.text = strip_newline_glyph(view.substr(RawLinesEditReplaceCommand.region))
            else:
                RawLinesEditReplaceCommand.text = view.substr(RawLinesEditReplaceCommand.region)
            view.set_read_only(False)
            view.run_command("raw_lines_edit_replace")
            view.set_read_only(True)

    def on_post_save(self, view):
        if view.settings().get("RawLineEdit", False) and not view.settings().get('RawLineEditPopup', False):
            use_glyph = view.settings().get("RawLineEditGlyph")
            RawLinesEditReplaceCommand.region = sublime.Region(0, view.size())
            if use_glyph:
                RawLinesEditReplaceCommand.text = add_newline_glyph(view.substr(RawLinesEditReplaceCommand.region))
            else:
                RawLinesEditReplaceCommand.text = view.substr(RawLinesEditReplaceCommand.region)
            view.set_read_only(False)
            view.run_command("raw_lines_edit_replace")
            view.set_scratch(True)
            view.set_read_only(True)
            view.set_syntax_file("Packages/RawLineEdit/RawLineEdit.hidden-tmLanguage")

    def on_query_context(self, view, key, operator, operand, match_all):
        handeled = False
        if view.settings().get("RawLineEdit", False) and key.startswith("raw_line_edit") and not view.settings().get('RawLineEditPopup', False):
            handeled = True
        return handeled
