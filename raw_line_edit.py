# -*- coding: utf-8 -*-
"""
Raw Line Edit.

Licensed under MIT
Copyright (c) 2013 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
from __future__ import unicode_literals
import sublime
import sublime_plugin
import codecs
import re
from os.path import exists
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except Exception:

    class Notify(object):
        """Fallback notify class."""

        @classmethod
        def is_ready(cls):
            """Disable SubNotify by returning False."""

            return False

USE_ST_SYNTAX = int(sublime.version()) >= 3092
ST_SYNTAX = "sublime-syntax" if USE_ST_SYNTAX else 'tmLanguage'

new_line = "¬"


def strip_newline_glyph(text):
    """Remove visible newline glyph."""

    return re.sub(r"%s\n" % new_line, "\n", text)


def add_newline_glyph(text):
    """Add new visible newline glyph."""

    return re.sub(r"\n", "%s\n" % new_line, text)


def strip_carriage_returns(text, glyph):
    """Strip visible carriage returns."""

    new_line_glyph = new_line if glyph else ""
    return re.sub(r"\r*%s\n" % new_line_glyph, "%s\n" % new_line_glyph, text)


def add_carriage_returns(text, glyph):
    """Add visible carriage returns."""

    new_line_glyph = new_line if glyph else ""
    return re.sub(r"(?<!\r)%s\n" % new_line_glyph, "\r%s\n" % new_line_glyph, text)


def strip_buffer_glyphs(text, glyph):
    """Strip all glyphs from buffer to load back into view."""

    new_line_glyph = new_line if glyph else ""
    return re.sub(r"\r*%s?\n|\r" % new_line_glyph, "\n", text)


def use_newline_glyph():
    """Use the newline glyph."""

    return bool(sublime.load_settings("raw_line_edit.sublime-settings").get("use_newline_glyph", False))


def use_theme():
    """Use the raw line theme to highlight line endings."""

    return bool(sublime.load_settings("raw_line_edit.sublime-settings").get("use_raw_line_edit_theme", False))


def convert_buffers():
    """Operate on unsaved buffers."""

    return bool(sublime.load_settings("raw_line_edit.sublime-settings").get("operate_on_unsaved_buffers", False))


def get_encoding(view):
    """Get the file encoding."""

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


def notify(msg):
    """Notify message."""

    settings = sublime.load_settings("raw_line_edit.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "RawLineEdit", "msg": msg})
    else:
        sublime.status_message(msg)


def error(msg):
    """Error message."""

    settings = sublime.load_settings("raw_line_edit.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "RawLineEdit", "msg": msg, "level": "error"})
    else:
        sublime.error_message("RawLineEdit:\n%s" % msg)


class RawLineTextBuffer(object):
    """Text buffer."""

    bfr = None
    syntax = None
    endings = None
    view = None

    @classmethod
    def set_buffer(cls, view, use_glyph):
        """Read buffer from view and strip new line glyphs."""

        cls.bfr = strip_buffer_glyphs(
            view.substr(sublime.Region(0, view.size())),
            use_glyph
        )

    @classmethod
    def clear_buffer(cls):
        """Clear the buffer object."""

        cls.bfr = None
        cls.view = None

    @classmethod
    def check_loading(cls, view):
        """Check if file is done loading yet before applying buffer."""

        cls.view = view
        sublime.set_timeout(cls.poll_loading, 300)

    @classmethod
    def poll_loading(cls):
        """Check if file is done loading, and if so, update view with buffer."""

        if cls.view.is_loading():
            sublime.set_timeout(cls.poll_loading, 300)
        else:
            cls.view.run_command("write_raw_line_text")


class WriteRawLineTextCommand(sublime_plugin.TextCommand):
    """Write buffer to view."""

    def run(self, edit):
        """Write the unsaved buffer to the view."""

        if RawLineTextBuffer.bfr is None:
            return
        self.view.replace(edit, sublime.Region(0, self.view.size()), RawLineTextBuffer.bfr)
        RawLineTextBuffer.clear_buffer()


class ToggleRawLineEditCommand(sublime_plugin.TextCommand):
    """Toggle raw line edit mode."""

    def disable_rle(self, edit):
        """Disable raw line ending mode."""

        # Save raw line ending changes
        if self.view.is_dirty():
            if sublime.ok_cancel_dialog("Raw Line Edit:\nFile has unsaved changes.  Save?", "Save"):
                self.view.run_command("save")

        # Get the settings
        settings = self.view.settings()
        file_name = settings.get("RawLineEditFilename")
        syntax = settings.get("RawLineEditSyntax")
        use_glyph = settings.get("RawLineEditGlyph")
        buffer_endings = settings.get("RawLineBuffer", None)

        # Strip the buffer of gyphs and prepare to write
        # the stripped buffer back to the view
        if buffer_endings is not None:
            RawLineTextBuffer.set_buffer(self.view, use_glyph)

        # Open temp view if only one view is open,
        # so not to close the window when we remove the view.
        window = self.view.window()
        temp = None
        if len(window.views()) <= 1:
            temp = window.new_file()

        # Close raw line view
        window.focus_view(self.view)
        window.run_command("close_file")

        # Open the file on disk
        new_view = window.open_file(file_name)

        # Close temp view if needed
        if temp is not None:
            window.focus_view(temp)
            window.run_command("close_file")

        # Set view settings
        window.focus_view(new_view)
        new_view.set_syntax_file(syntax)

        # Reapply unsaved buffer if needed
        if buffer_endings is not None:
            new_view.set_line_endings(buffer_endings)
            RawLineTextBuffer.check_loading(new_view)

    def enable_rle(self, edit, file_name):
        """Enable raw line ending mode."""

        if self.view.is_dirty():
            if convert_buffers():
                msg = (
                    "File has unsaved changes.  If you choose not to save, "
                    "the view buffer will be parsed as the source.\n\nSave?"
                )
            else:
                msg = (
                    "File has unsaved changes.  If you choose not to save, "
                    "changes will be discared and the file will be parsed from disk.\n\nSave?"
                )
            if sublime.ok_cancel_dialog(msg, "Save"):
                # Save the file
                self.view.run_command("save")
            else:
                # Convert the unsaved buffer
                if convert_buffers():
                    self.enable_buffer_rle(edit, file_name)
                    return
                else:
                    if file_name is None:
                        error("File must exist on disk!")
                        return
                    else:
                        notify("Changes discarded.")

        if file_name is None or not exists(file_name):
            if convert_buffers():
                self.enable_buffer_rle(edit)
            else:
                error("File must exist on disk!")
            return

        # Convert the file on disk to a raw line view
        encoding = get_encoding(self.view)
        try:
            self.show_rle(edit, file_name, encoding)
        except Exception:
            self.show_rle(edit, file_name, "utf-8")

    def show_rle(self, edit, file_name, encoding):
        """
        Read the file from disk converting actual lines to glyphs.

        Present the info in raw line view.
        """
        with codecs.open(file_name, "r", encoding) as f:
            use_glyph = use_newline_glyph()
            if use_glyph:
                self.view.replace(edit, sublime.Region(0, self.view.size()), add_newline_glyph(f.read()))
            else:
                self.view.replace(edit, sublime.Region(0, self.view.size()), f.read())
            self.view.set_line_endings("Unix")
            settings = self.view.settings()
            settings.set("RawLineEditGlyph", use_glyph)
            settings.set("RawLineEdit", True)
            settings.set("RawLineEditSyntax", settings.get('syntax'))
            settings.set("RawLineEditFilename", file_name)
            if use_theme():
                self.view.set_syntax_file("Packages/RawLineEdit/RawLineEdit.%s" % ST_SYNTAX)
            self.view.set_scratch(True)
            self.view.set_read_only(True)

    def read_buffer(self):
        """Read the unsaved buffer and replace with new line glyphs."""

        endings = {
            "Windows": "\r\n",
            "Unix": "\n",
            "CR": "\r"
        }
        line_ending = endings[self.view.line_endings()]
        bfr = []
        for line in self.view.split_by_newlines(sublime.Region(0, self.view.size())):
            bfr.append(self.view.substr(line) + line_ending)
        return "".join(bfr)

    def enable_buffer_rle(self, edit, file_name=None):
        """Enable the raw line mode on an unsaved buffer."""

        if self.view.is_read_only():
            self.view.set_read_only(False)
        use_glyph = use_newline_glyph()
        if use_glyph:
            self.view.replace(edit, sublime.Region(0, self.view.size()), add_newline_glyph(self.read_buffer()))
        else:
            self.view.replace(edit, sublime.Region(0, self.view.size()), self.read_buffer())
        settings = self.view.settings()
        settings.set("RawLineEditGlyph", use_glyph)
        settings.set("RawLineEdit", True)
        settings.set("RawLineEditSyntax", self.view.settings().get('syntax'))
        self.view.settings().set("RawLineBuffer", self.view.line_endings())
        if file_name is not None:
            settings.set("RawLineEditFilename", file_name)
        self.view.set_line_endings("Unix")
        if use_theme():
            self.view.set_syntax_file("Packages/RawLineEdit/RawLineEdit.hidden-tmLanguage")
        self.view.set_scratch(True)
        self.view.set_read_only(True)

    def disable_buffer_rle(self, edit):
        """Disable the raw line mode on an unsaved buffer."""

        if self.view.is_dirty():
            if sublime.ok_cancel_dialog("Raw Line Edit:\nFile has unsaved changes.  Save?", "Save"):
                self.view.run_command("save")
                self.disable_rle(edit)
                return
        win = self.view.window()
        new_view = win.new_file()
        settings = self.view.settings()
        syntax = settings.get("RawLineEditSyntax")
        use_glyph = settings.get("RawLineEditGlyph")
        line_endings = settings.get("RawLineBuffer")
        bfr = strip_buffer_glyphs(
            self.view.substr(sublime.Region(0, self.view.size())),
            use_glyph
        )
        new_view.replace(edit, sublime.Region(0, self.view.size()), bfr)
        new_view.set_line_endings(line_endings)
        new_view.set_syntax_file(syntax)
        win.focus_view(self.view)
        win.run_command("close_file")
        win.focus_view(new_view)

    def is_enabled(self):
        """Check if enabled."""

        p_settings = sublime.load_settings("raw_line_edit.sublime-settings")
        v_settings = self.view.settings()
        return not bool(p_settings.get("view_only", False)) or v_settings.get("RawLineEdit", False)

    def run(self, edit):
        """Toggle the raw line mode."""

        file_name = self.view.file_name()
        settings = self.view.settings()

        if (file_name is None or not exists(file_name)) and settings.get("RawLineEdit", False):
            self.disable_buffer_rle(edit)
        elif settings.get("RawLineEdit", False):
            self.disable_rle(edit)
        elif not settings.get("RawLineEdit", False):
            self.enable_rle(edit, file_name)


class PopupRawLineEditCommand(sublime_plugin.TextCommand):
    """Popup command."""

    def popup_rle(self, file_name):
        """Popup raw line edit view."""

        if self.view.is_dirty():
            if convert_buffers():
                msg = (
                    "Raw Line Edit:\nFile has unsaved changes.  If you choose not to save, "
                    "the view buffer will be parsed as the source.\n\nSave?"
                )
            else:
                msg = (
                    "Raw Line Edit:\nFile has unsaved changes.  If you choose not to save, "
                    "changes will be discared and the file will be parsed from disk.\n\nSave?"
                )
            if sublime.ok_cancel_dialog(msg, "Save"):
                self.view.run_command("save")
            else:
                # Convert the unsaved buffer
                if convert_buffers():
                    self.enable_buffer_rle(file_name)
                    return
                else:
                    if file_name is None:
                        error("File must exist on disk!")
                        return
                    else:
                        notify("Changes discarded.")

        if file_name is None or not exists(file_name):
            if convert_buffers():
                self.enable_buffer_rle()
            else:
                error("File must exist on disk!")
            return

        encoding = get_encoding(self.view)
        try:
            self.show_rle(file_name, encoding)
        except Exception:
            self.show_rle(file_name, "utf-8")

    def read_buffer(self):
        """Read the unsaved buffer and replace with new line glyphs."""

        endings = {
            "Windows": "\r\n",
            "Unix": "\n",
            "CR": "\r"
        }
        line_ending = endings[self.view.line_endings()]
        bfr = []
        for line in self.view.split_by_newlines(sublime.Region(0, self.view.size())):
            bfr.append(self.view.substr(line) + line_ending)
        return "".join(bfr)

    def enable_buffer_rle(self, file_name=None):
        """Enable the raw line mode on an unsaved buffer."""

        view = self.view.window().get_output_panel('raw_line_edit_view')
        view.set_line_endings("Unix")
        view.set_read_only(False)
        use_glyph = use_newline_glyph()
        RawLinesEditReplaceCommand.region = sublime.Region(0, view.size())
        if use_glyph:
            RawLinesEditReplaceCommand.text = add_newline_glyph(self.read_buffer())
        else:
            RawLinesEditReplaceCommand.text = self.read_buffer()
        view.run_command("raw_lines_edit_replace")
        view.sel().clear()
        settings = view.settings()
        settings.set("RawLineEditGlyph", use_glyph)
        settings.set("RawLineEdit", True)
        settings.set("RawLineEditSyntax", self.view.settings().get('syntax'))
        settings.set("RawLineEditPopup", True)
        settings.set("RawLineBuffer", self.view.line_endings())
        if file_name is not None:
            settings.set("RawLineEditFilename", file_name)
        if use_theme():
            view.set_syntax_file("Packages/RawLineEdit/RawLineEdit.hidden-tmLanguage")
        view.set_scratch(True)
        view.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": "output.raw_line_edit_view"})

    def show_rle(self, file_name, encoding):
        """Show the raw line view popup."""

        try:
            view = self.view.window().get_output_panel('raw_line_edit_view')
            view.set_line_endings("Unix")
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
                if not use_theme():
                    syntax_file = self.view.settings().get('syntax')
                else:
                    syntax_file = "Packages/RawLineEdit/RawLineEdit.hidden-tmLanguage"
                view.set_syntax_file(syntax_file)
                view.settings().set("RawLineEditSyntax", self.view.settings().get('syntax'))
                view.settings().set("RawLineEditGlyph", use_glyph)
                view.settings().set("RawLineEdit", True)
                view.settings().set("RawLineEditFilename", file_name)
                view.settings().set("RawLineEditPopup", True)
                view.set_scratch(True)
                view.set_read_only(True)
                self.view.window().run_command("show_panel", {"panel": "output.raw_line_edit_view"})
        except Exception:
            self.view.window().run_command("hide_panel", {"panel": "output.raw_line_edit_view"})
            raise

    def is_enabled(self):
        """Check if command is enabled."""

        return bool(sublime.load_settings("raw_line_edit.sublime-settings").get("view_only", False))

    def run(self, edit):
        """Popup panel with raw line view."""

        file_name = self.view.file_name()
        settings = self.view.settings()
        if (not settings.get("RawLineEdit", False)) and not settings.get('RawLineEditPopup', False):
            self.popup_rle(file_name)


class RawLineInsertCommand(sublime_plugin.TextCommand):
    """Insert text in view."""

    def run(self, edit, style="Unix"):
        """Insert text."""

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
    """Replace text in view."""

    text = None
    region = None

    def run(self, edit):
        """Replace text."""

        cls = RawLinesEditReplaceCommand
        if cls.text is not None and cls.region is not None:
            self.view.replace(edit, cls.region, cls.text)
        cls.text = None
        cls.region = None


class RawLineEditListener(sublime_plugin.EventListener):
    """RawLineEdit Listener."""

    def on_pre_save(self, view):
        """Convert raw line mode back to normal mode before save."""

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
        """Convert view back to raw line mode after save."""

        if view.settings().get("RawLineEdit", False) and not view.settings().get('RawLineEditPopup', False):
            file_name = view.file_name()
            if file_name is not None:
                view.settings().set("RawLineEditFilename", file_name)
            if view.settings().set("RawLineBuffer", None) is not None:
                view.settings().erase("RawLineBuffer")
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
        """Handle raw line mode shortcuts."""

        settings = view.settings()
        return (
            settings.get("RawLineEdit", False) and key.startswith("raw_line_edit") and
            not settings.get('RawLineEditPopup', False)
        )
