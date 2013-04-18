RawLineEdit
===========
<img src="https://dl.dropboxusercontent.com/u/342698/RawLineEdit/Example.png" border="0"/>

View and edit line endings in Sublime Text.  RawLineEdit displays line endings very clearly and allows changing the line endings per line (something sublime text doesn't allow out of the box).

# Usage
Toggle current view to a "RawLineEdit" view via the command palette command ```Raw Line Edit: Toggle``` (you can setup your own keybinding or add it to your context menu if you choose).   File must exist on disk.

Using ```Enter``` key you can change Windows style line endings to Unix or use ```Shift+Enter``` to do the opposite.  Select multiple lines to change more than one line.

# Settings
```javascript
    // Use a glyph for a visual representation
    // for newlines
    "use_newline_glyph": true,

    // Use the raw line edit theme to allow
    // a view that highlights only new lines
    // and carriage returns for easy visualization.
    // (Colors customizable via your color scheme file)
    "use_raw_line_edit_theme": true
```

# Colorize Line Endings
```XML
        <dict>
            <key>name</key>
            <string>Raw New Line: Carriage Rerturn</string>
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
# License

Raw Line Edit is released under the MIT license.

Copyright (c) 2013 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
