# User Guide {: .doctitle}
Configuration and usage of RawLineEdit.
{: .doctitle-info}

---

## General Usage
Toggle current view to a "RawLineEdit" view via the command palette command `Raw Line Edit: Toggle` (you can setup your own keybinding or add it to your context menu if you choose).   File must exist on disk.

Using `Enter` key you can change Windows style line endings to Unix or use `Shift+Enter` to do the opposite.  Select multiple lines to change more than one line.

## Settings

```javascript
    // Use subnotify if available
    "use_sub_notify": true,

    // Use a glyph for a visual representation
    // for newlines
    "use_newline_glyph": true,

    // Use the raw line edit theme to allow
    // a view that highlights only new lines
    // and carriage returns for easy visualization.
    // (Colors customizable via your color scheme file)
    "use_raw_line_edit_theme": true,

    // View only mode: pops up a output panel showing line endings.
    // No editing possible.
    "view_only": false,

    // Operate on sublime unsaved view buffer
    // Instead of reading the file from disk,
    // The file will be read directly from the buffer
    // In these cases the line endings will be normalized,
    // but you can edit them and save them back to disk.
    // Not sure how useful this is.
    "operate_on_unsaved_buffers": false
```

## Colorize Line Endings

```xml
        <dict>
            <key>name</key>
            <string>Raw New Line: Carriage Return</string>
            <key>scope</key>
            <string>glyph.carriage-return</string>
            <key>settings</key>
            <dict>
                <key>foreground</key>
                <string>#66CCCC</string>
            </dict>
        </dict>
        <dict>
            <key>name</key>
            <string>Raw New Line: New Line Glyph</string>
            <key>scope</key>
            <string>glyph.new-line</string>
            <key>settings</key>
            <dict>
                <key>foreground</key>
                <string>#F2777A</string>
            </dict>
        </dict>
```
