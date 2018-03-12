# -*- coding: utf-8 -*-
# author:mtimer
# https://github.com/MTimer/SublimeText-Google-Translate-Plugin

import sublime
import sublime_plugin
import json
import re
import time
import mdpopups
from pprint import pprint
if sublime.version() < '3':
    from core.translate import *
else:
    from .core.translate import *

settings = sublime.load_settings("goTranslate.sublime-settings")

class GoTranslateCommand(sublime_plugin.TextCommand):

    def run(self, edit, proxy_enable = settings.get("proxy_enable"), proxy_type = settings.get("proxy_type"), proxy_host = settings.get("proxy_host"), proxy_port = settings.get("proxy_port"), source_language = settings.get("source_language"), target_language = settings.get("target_language")):

        if not source_language:
            source_language = settings.get("source_language")
        if not target_language:
            target_language = settings.get("target_language")
        if not proxy_enable:
            proxy_enable = settings.get("proxy_enable")
        if not proxy_type:
            proxy_type = settings.get("proxy_type")
        if not proxy_host:
            proxy_host = settings.get("proxy_host")
        if not proxy_port:
            proxy_port = settings.get("proxy_port")
        target_type = settings.get("target_type")
        effectuate_keep_moving = settings.get("keep_moving_down")

        v = self.view
        window = v.window()

        # Get the current cursor position in the file
        caret = v.sel()[0].begin()

        # Get the new current line number
        cur_line = self.line_at(caret)

        # Get the count of lines in the buffer so we know when to stop
        last_line = self.line_at(v.size())

        keep_moving = True
        # RE: https://stackoverflow.com/questions/44578315/making-a-sublime-text-3-macro-to-evaluate-a-line-and-then-move-the-cursor-to-the
        # A regex that matches a line that's blank or contains a comment.
        # Adjust as needed
        _r_blank = re.compile("^\s*(#.*)?$")

        while keep_moving:

            for region in v.sel():

                whole_line = False
                if not region.empty():
                    selection = v.substr(region)
                    coordinates = v.sel()
                    keep_moving = False
                else:
                    selection = v.substr(v.line(v.sel()[0]))
                    coordinates = v.line(v.sel()[0])
                    whole_line = True

                if selection:
                    largo = len(selection)
                    print('line(' + str(cur_line + 1) + ') length(' + str(largo) + ') selection(' + selection + ')' )

                    if largo > 256:
                        print('')
                        message = 'ERR:' + str(cur_line + 1) + ' line too long to translate and it will fail, consider spliting it, shorting it, making two or more.'
                        print(message)
                        print('')
                        sublime.status_message(u'ERR:' + str(cur_line + 1 ) + ' line too Long (' + selection + ')')
                        self.initialize_ProgressBar( v, "Translate", "Error", message + " \n line(" + str(cur_line + 1) + ') length(' + str(largo) + ') selection(' + selection + ')')
                        keep_moving = False
                        return

                    selection = selection.encode('utf-8')

                    translate = GoogleTranslate(proxy_enable, proxy_type, proxy_host, proxy_port, source_language, target_language)

                    if not target_language:
                        v.run_command("go_translate_to")
                        keep_moving = False
                        return
                    else:
                        try:
                            result = translate.translate(selection, target_type)
                            time.sleep(0.15)
                        except:
                            # REF: https://github.com/Enteleform/-SCRIPTS-/blob/master/SublimeText/%5BMisc%5D/%5BProof%20Of%20Concept%5D%20Progress%20Bar/ProgressBarDemo/ProgressBarDemo.py
                            print('')
                            message = 'ERR:' + str(cur_line + 1) + ' translation service failed.'
                            print(message)
                            print('')
                            sublime.status_message(u'' + message)
                            self.initialize_ProgressBar( v, "Translate", "Error", message)
                            keep_moving = False
                            return
                    # DEBUG print('edit')
                    # DEBUG pprint(edit)

                    # DEBUG print('coordinates')
                    # DEBUG pprint(coordinates)

                    # DEBUG print('result')
                    # DEBUG pprint(result)

                    if not whole_line:
                        v.replace(edit, region, result)
                    else:
                        v.replace(edit, coordinates, result)

                    window.focus_view(v)
                    if not source_language:
                        detected = 'Auto'
                    else:
                        detected = source_language
                    sublime.status_message(u'Done! (translate '+detected+' --> '+target_language+')')
                else:
                    sublime.status_message(u'Nothing to translate!')
                    print('Nothing to translate!')
                    # DEBUG print('selection(' + selection + ')' )

            if effectuate_keep_moving == 'no':
                keep_moving = False

            if keep_moving:
                # Move to the next line
                v.run_command("move", {"by": "lines", "forward": True})
                time.sleep(0.15)
                sublime.status_message(u'moved down.')
                print('moved down.')


                # Get the current cursor position in the file
                caret = v.sel()[0].begin()

                # Get the new current line number
                cur_line = self.line_at(caret)

                percent = (cur_line * 100) / last_line
                sublime.status_message('%03.2f %%' % percent)

                # Get the contents of the current line
                # content = v.substr(v.line(caret))
                # selection = v.substr(v.line(v.sel()[0]))
                # largo = len(selection.strip())

                # If the current line is the last line, or the contents of
                # the current line does not match the regex, break out now.
                if cur_line == last_line: #or largo == 0:  # not _r_blank.match(selection):
                    print('cur_line(' + str(cur_line) + ') == last_line(' + str(last_line) + ')' )
                    #print('selection.len(' + str(largo) + ')')
                    print('exiting here.')
                    keep_moving = False


    def is_visible(self):
        for region in self.view.sel():
            if not region.empty():
                return True
        return False

    # Convert a 0 based offset into the file into a 0 based line in
    # the file.
    def line_at(self, point):
        return self.view.rowcol(point)[0]

    def initialize_ProgressBar( self, view , title = "PROGRESS:", label = "COMPLETE!", content = ""):
        # REF: https://github.com/Enteleform/-SCRIPTS-/blob/master/SublimeText/%5BMisc%5D/%5BProof%20Of%20Concept%5D%20Progress%20Bar/ProgressBarDemo/ProgressBarDemo.py
        #▒▒▒  Text  ▒▒▒#
        self.popUp_Label_InProgress = title
        self.popUp_Label_Complete   = label

        #▒▒▒  Progress Tracking  ▒▒▒#
        self.maxPercent      = 100
        self.updateFrequency = 50 # In Milliseconds

        #▒▒▒  Dimensions  ▒▒▒#
        self.popupWidth         = 500
        self.popupMaxHeight     = 500
        self.progressBar_Height = 21

        #▒▒▒  Colors  ▒▒▒#
        self.progressBar_Incomplete_Color = "#0B121A"
        self.progressBar_Complete_Color   = "#57BB80"
        self.progressBar_Progress_Color   = "#5A91BC"
        self.progressBar_BorderColor      = "#000000"

        self.popupCSS = sublime.load_resource( sublime.find_resources( "ProgressBarDemo_ProgressBar.css" )[ 0 ] )
        self.progressBar_Width = int( float( self.popupWidth * 0.8 ) )
        self.progressPercent   = 100

        mdpopups.show_popup(
            view,               # view
            content,            # content
            True,               # markdown
            self.popupCSS,      # css
            0,                  # flags
            -1,                 # location
            self.popupWidth,    # width
            self.popupMaxHeight # height
        )


class GoTranslateInfoCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        settings = sublime.load_settings("goTranslate.sublime-settings")
        source_language = settings.get("source_language")
        target_language = settings.get("target_language")
        proxy_enable = settings.get("proxy_enable")
        proxy_type = settings.get("proxy_type")
        proxy_host = settings.get("proxy_host")
        proxy_port = settings.get("proxy_port")

        v = self.view
        selection = v.substr(v.sel()[0])

        translate = GoogleTranslate(proxy_enable, proxy_type, proxy_host, proxy_port, source_language, target_language)

        text = (json.dumps(translate.langs, ensure_ascii = False, indent = 2))

        v.replace(edit, v.sel()[0], text)

class GoTranslateToCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        settings = sublime.load_settings("goTranslate.sublime-settings")
        source_language = settings.get("source_language")
        target_language = settings.get("target_language")
        proxy_enable = settings.get("proxy_enable")
        proxy_type = settings.get("proxy_type")
        proxy_host = settings.get("proxy_host")
        proxy_port = settings.get("proxy_port")

        v = self.view
        selection = v.substr(v.sel()[0])

        translate = GoogleTranslate(proxy_enable, proxy_type, proxy_host, proxy_port, source_language, target_language)

        text = (json.dumps(translate.langs['langs'], ensure_ascii = False))
        continents = json.loads(text)
        lkey = []
        ltrasl = []

        for (slug, title) in continents.items():
            lkey.append(slug)
            ltrasl.append(title+' ['+slug+']')

        def on_done(index):
            if index >= 0:
                self.view.run_command("go_translate", {"target_language": lkey[index]})

        self.view.window().show_quick_panel(ltrasl, on_done)

    def is_visible(self):
        for region in self.view.sel():
            if not region.empty():
                return True
        return False


def plugin_loaded():
    global settings
    settings = sublime.load_settings("goTranslate.sublime-settings")
