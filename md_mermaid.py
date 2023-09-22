"""
Mermaid Extension for Python-Markdown
========================================

Adds mermaid parser (like github-markdown) to standard Python-Markdown code blocks.

Original code Copyright 2018-2020 [Olivier Ruelle].

License: GNU GPLv3

"""

from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor

import re
import string

def strip_notprintable(myStr):
    return ''.join(filter(lambda x: x in string.printable, myStr))

MermaidRegex = re.compile(r"^(?P<mermaid_sign>[\~\`]){3}[\ \t]*[Mm]ermaid[\ \t]*$")


# ------------------ The Markdown Extension -------------------------------

class MermaidPreprocessor(Preprocessor):
    def __init__(self, md, config):
        super().__init__(md)
        self.config = config
        if config['mermaid_js_url'] is None:
            self.mermaid_js_url = None
        elif config['mermaid_js_url']:
            self.mermaid_url = config['mermaid_js_url']
        elif config['mermaid_version'] == 'latest' or not config['mermaid_version']:
            self.mermaid_js_url = 'https://unpkg.com/mermaid/dist/mermaid.min.js'
        else:
            self.mermaid_js_url = f'https://unpkg.com/mermaid@{config["mermaid_version"]}/dist/mermaid.min.js'

    def run(self, lines):
        old_line = ""
        new_lines = []
        mermaid_sign = ""
        m_start = None
        m_end = None
        in_mermaid_code = False
        is_mermaid = False
        for line in lines:
            # Wait for starting line with MermaidRegex (~~~ or ``` following by [mM]ermaid )
            if not in_mermaid_code:
                m_start = MermaidRegex.match(line)
            else:
                m_end = re.match(r"^["+mermaid_sign+"]{3}[\ \t]*$", line)
                if m_end:
                    in_mermaid_code = False

            if m_start:
                in_mermaid_code = True
                mermaid_sign = m_start.group("mermaid_sign")
                if not re.match(r"^[\ \t]*$", old_line):
                    new_lines.append("")
                if not is_mermaid:
                    is_mermaid = True
                    #new_lines.append('<style type="text/css"> @import url("https://cdn.rawgit.com/knsv/mermaid/0.5.8/dist/mermaid.css"); </style>')
                new_lines.append('<div class="mermaid">')
                m_start = None
            elif m_end:
                new_lines.append('</div>')
                new_lines.append("")
                m_end = None
            elif in_mermaid_code:
                # new_lines.append(strip_notprintable(line).strip())
                new_lines.append(line.rstrip())
            else:
                new_lines.append(line)

            old_line = line

        if is_mermaid:
            new_lines.append('')
            # This will initialize mermaid renderer. It's done only when the HTML document is ready,
            # to ensure the loading of mermaid.js file is finished.
            if self.mermaid_js_url:
                new_lines.append(f'<script src="{self.mermaid_js_url}"></script>')
                new_lines.append('<script>mermaid.initialize({startOnLoad:true});</script>')
            else:
                new_lines.append('''<script>
                        function initializeMermaid() {
                            mermaid.initialize({startOnLoad:true})
                        }

                        if (document.readyState === "complete" || document.readyState === "interactive") {
                            setTimeout(initializeMermaid, 1);
                        } else {
                            document.addEventListener("DOMContentLoaded", initializeMermaid);
                        }
                </script>''')

        return new_lines


class MermaidExtension(Extension):
    """ Add source code hilighting to markdown codeblocks. """
    config = {
        'mermaid_version' : ['latest',
                             'Version of mermaid to use, e.g. 9.0 - '
                             'Defaults to latest',],
        'mermaid_js_url' : ['',
                            'Mermaid src to include - Defaults to unpkg.com/mermaid '
                            'based on version variable; '
                            'use None to omit src (e.g. specify a local script); '
                            'omitting src will also trigger a delayed mermaid initialization'
                           ],
        }

    def extendMarkdown(self, md):
        """ Add HilitePostprocessor to Markdown instance. """
        # Insert a preprocessor before ReferencePreprocessor
        md.preprocessors.register(MermaidPreprocessor(md, self.getConfigs()), 'mermaid', 35)
        md.registerExtension(self)

def makeExtension(**kwargs):  # pragma: no cover
    return MermaidExtension(**kwargs)
