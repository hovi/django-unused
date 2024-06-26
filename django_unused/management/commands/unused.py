from argparse import ArgumentParser
from typing import Any

from django.core.management.base import BaseCommand

from ._templates import find_unused_templates, TemplateFilterOptions


class Command(BaseCommand):
    help = "Lists all unused template files."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "unused_type",
            type=str,
            nargs="?",
            default="templates",
            choices=["templates"],
            help="What to find: templates (default), views, media",
        )
        parser.add_argument(
            "--excluded-apps",
            type=str,
            nargs="*",
            help="List of apps to exclude from the search",
        )
        parser.add_argument(
            "--excluded-template-dirs",
            type=str,
            nargs="*",
            help="List of template directories to exclude from the search",
        )

    def handle(self, *args: Any, **options: dict[str, Any]):
        unused_type = options["unused_type"]
        excluded_apps = options.get("excluded_apps")
        excluded_template_dirs = options.get("excluded_template_dirs")

        filter_options = TemplateFilterOptions(
            excluded_apps=excluded_apps, excluded_template_dirs=excluded_template_dirs
        )

        if unused_type == "templates":
            unused_templates = find_unused_templates(filter_options)
            if unused_templates:
                exit(1)
        else:
            self.stderr.write(
                self.style.ERROR(
                    f"{unused_type} is not a valid parameter. Valid parameters are templates, views, and media."
                )
            )
            exit(1)
