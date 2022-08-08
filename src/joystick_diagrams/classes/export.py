from os import path
import os
from pathlib import Path
import re
import html
import subprocess
import logging
from PyQt5 import QtWidgets
from joystick_diagrams import config
from joystick_diagrams.functions import helper

_logger = logging.getLogger(__name__)

IMAGIK_PROGRAM="C:\\Program Files\\ImageMagick-7.1.0-Q16-HDRI\\magick.exe"

class Export:
    def __init__(self, joystick_listing, parser_id="UNKNOWN", 
                 export_to_png=False, 
                 output_directory=None,
                 mode_export=True):  # pylint disable=too-many-instance-attributes
        self.export_directory = "./diagrams/"
        self.templates_directory = "./templates/"
        self.file_name_divider = "_"
        self.joystick_listing = joystick_listing
        self.export_progress = None
        self.no_bind_text = config.noBindText
        self.executor = parser_id
        self.export_to_png = export_to_png
        self.output_directory = output_directory
        self.mode_export=mode_export
        self.error_bucket = []

    def export_config(self, progress_bar=None) -> list:
        """
        Manipulates stored templates, and replaces strings with actual values.

        Returns a list of errors.
        """
        joystick_count = len(self.joystick_listing)

        _logger.debug(f"Export Started with {joystick_count} joysticks")
        _logger.debug(f"Export Data: {self.joystick_listing}")

        if isinstance(progress_bar, QtWidgets.QProgressBar):
            progress_bar.setValue(0)
            progress_increment = int(100 / joystick_count)
            print(progress_increment)

        for joystick in self.joystick_listing:
            base_template = self.get_template(joystick)
            if base_template:
                progress_increment_modes = len(self.joystick_listing[joystick])
                for mode in self.joystick_listing[joystick]:
                    write_template = base_template
                    print("Replacing Strings")
                    completed_template = self.replace_template_strings(joystick, mode, write_template)
                    print("Replacing Unused String")
                    completed_template = self.replace_unused_strings(completed_template)
                    print("Branding")
                    completed_template = self.brand_template(mode, completed_template)
                    print(f"Saving: {joystick}")
                    self.save_template(joystick, mode, completed_template)
                    if isinstance(progress_bar, QtWidgets.QProgressBar):
                        progress_bar.setValue(progress_bar.value() + (progress_increment / progress_increment_modes))
            else:
                self.error_bucket.append(f"No Template file found for: {joystick}")

            if isinstance(progress_bar, QtWidgets.QProgressBar):
                progress_bar.setValue(progress_bar.value() + progress_increment)

        if isinstance(progress_bar, QtWidgets.QProgressBar):
            progress_bar.setValue(100)
        return self.error_bucket

    def get_template(self, joystick):
        joystick = joystick.strip()
        if path.exists(self.templates_directory + joystick + ".svg"):
            data = Path(os.path.join(self.templates_directory, joystick + ".svg")).read_text(encoding="utf-8")
            return data
        return False

    def save_template(self, joystick, mode, template):
        output_path = self.export_directory + self.executor + "_" + joystick.strip() + "_" + mode + ".svg"
        
        # create the output png
        png_output_directory = self.export_directory
        if self.output_directory:
            png_output_directory = self.output_directory
        if self.mode_export:
            png_output_directory += mode + "/"
            
        output_png = png_output_directory + self.executor + "_" + mode + "_" + joystick.strip()  + ".png"
        helper.create_directory(self.export_directory)

        try:
            print("Exporting svg to {}".format(output_path))
            outputfile = open(output_path, "w", encoding="UTF-8")
            outputfile.write(template)
            outputfile.close()
            # convert to png
            if (output_png):
                helper.create_directory(png_output_directory)
                print("Exporting png to {}".format(output_png))
                subprocess.run([IMAGIK_PROGRAM, output_path, output_png])
                # drawing = svg2rlg(output_path)
                # renderPM.drawToFile(drawing, output_png, fmt='PNG')
                # svg2png(bytestring=template,write_to=output_png)
            
        except PermissionError as e:
            _logger.error(e)
            raise
        
        print("Done")

    def replace_unused_strings(self, template):
        regex_search = "\\bButton_\\d+\\b|\\bPOV_\\d+_\\w+\\b"
        matches = re.findall(regex_search, template, flags=re.IGNORECASE)
        matches = list(dict.fromkeys(matches))
        if matches:
            for i in matches:
                search = "\\b" + i + "\\b"
                template = re.sub(
                    search,
                    html.escape(self.no_bind_text),
                    template,
                    flags=re.IGNORECASE,
                )
        return template

    def replace_template_strings(self, device, mode, template):
        for button, value in self.joystick_listing[device][mode]["Buttons"].items():
            if value == "NO BIND":
                value = self.no_bind_text
            regex_search = "\\b" + button + "\\b"
            template = re.sub(regex_search, html.escape(value), template, flags=re.IGNORECASE)
        return template

    def brand_template(self, title, template):
        template = re.sub("\\bTEMPLATE_NAME\\b", title, template)
        return template
