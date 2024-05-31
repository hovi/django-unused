import fileinput
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Iterable

from colorama import init, Fore

from ...unused.find_templates import (
    find_py_files,
    find_app_templates,
    find_global_templates,
    TemplateInfo,
)


@dataclass
class TemplateFilterOptions:
    excluded_apps: Optional[Iterable[str]] = None
    excluded_template_dirs: Optional[Iterable[str]] = None


@dataclass
class Reference:
    template_info: TemplateInfo
    line_number: int
    line: str
    reference_type: str


@dataclass
class UsedTemplateInfo:
    template_info: TemplateInfo
    references: List[Reference]


@dataclass
class TemplateSearchResult:
    unused_templates: List[TemplateInfo]
    used_templates: List[UsedTemplateInfo]


def fetch_templates() -> List[TemplateInfo]:
    print(f"{Fore.CYAN}Fetching global templates...")
    global_templates = find_global_templates()
    print(f"{Fore.GREEN}{len(global_templates)} global templates found.\n")

    print(f"{Fore.CYAN}Fetching app templates...")
    app_templates = find_app_templates()
    print(f"{Fore.GREEN}{len(app_templates)} app templates found.\n")

    return global_templates + app_templates


def filter_templates(
    templates: List[TemplateInfo], filter_options: Optional[TemplateFilterOptions]
) -> List[TemplateInfo]:
    initial_app_template_count = len([t for t in templates if t.app_config])

    # Filter out templates from excluded apps
    if filter_options and filter_options.excluded_apps:
        excluded_apps_set = set(filter_options.excluded_apps)
        templates = [
            t
            for t in templates
            if not (t.app_config and t.app_config.name in excluded_apps_set)
        ]
        filtered_app_template_count = initial_app_template_count - len(
            [t for t in templates if t.app_config]
        )
        print(
            f"{Fore.YELLOW}{filtered_app_template_count} templates excluded by app filter.\n"
        )

    initial_template_count = len(templates)

    # Filter out templates from excluded directories
    if filter_options and filter_options.excluded_template_dirs:
        excluded_dirs_set = set(filter_options.excluded_template_dirs)
        templates = [
            t
            for t in templates
            if not any(t.template_path.startswith(d) for d in excluded_dirs_set)
        ]
        filtered_dir_template_count = initial_template_count - len(templates)
        print(
            f"{Fore.YELLOW}{filtered_dir_template_count} templates excluded by directory filter.\n"
        )

    print(f"{Fore.GREEN}{len(templates)} app templates found after filtering.\n")
    return templates


def determine_reference_type(line: str) -> str:
    line = line.strip()
    if "{% include" in line and "%}" in line:
        return "include"
    elif "{% extends" in line and "%}" in line:
        return "extend"
    else:
        return "unknown"


def search_unused_templates(templates: List[TemplateInfo]) -> TemplateSearchResult:
    print(f"{Fore.CYAN}Fetching Python files...")
    py_files, _ = find_py_files()
    print(f"{Fore.GREEN}{len(py_files)} Python files found.\n")

    all_files = py_files + [t.file_path for t in templates]
    unused_templates = []
    used_templates = []

    print(f"{Fore.CYAN}Searching for unused templates...", end="", flush=True)
    current_file = None
    line_number = 0
    for line in fileinput.input(all_files, openhook=fileinput.hook_encoded("utf-8")):
        if fileinput.filename() != current_file:
            current_file = fileinput.filename()
            line_number = 0
        line_number += 1
        for template in templates:
            if (
                template.template_path in line
                or template.template_path.split("/")[-1] in line
            ):
                referencing_template = next(
                    (t for t in templates if t.file_path == current_file), None
                )
                if referencing_template:
                    reference_type = determine_reference_type(
                        line
                    )
                    reference = Reference(
                        template_info=referencing_template,
                        line_number=line_number,
                        line=line.strip(),
                        reference_type=reference_type,
                    )
                    used_template_info = next(
                        (
                            uti
                            for uti in used_templates
                            if uti.template_info == template
                        ),
                        None,
                    )
                    if used_template_info:
                        used_template_info.references.append(reference)
                    else:
                        used_templates.append(
                            UsedTemplateInfo(
                                template_info=template, references=[reference]
                            )
                        )

    fileinput.close()

    for template in templates:
        if not any(uti.template_info == template for uti in used_templates):
            unused_templates.append(template)

    return TemplateSearchResult(
        unused_templates=unused_templates, used_templates=used_templates
    )


def print_unused_templates(result: TemplateSearchResult):
    print(f"\n{Fore.GREEN}Search complete.\n")
    if result.unused_templates:
        print(f"{Fore.RED}Unused templates found:")
        unused_templates_by_app: Dict[str, List[TemplateInfo]] = {}
        for template in result.unused_templates:
            app_name = template.app_config.name if template.app_config else "global"
            if app_name not in unused_templates_by_app:
                unused_templates_by_app[app_name] = []
            unused_templates_by_app[app_name].append(template)

        for app_name, templates in unused_templates_by_app.items():
            print(f"\n{Fore.YELLOW}App: {app_name}")
            for template in templates:
                print(f"{Fore.RED}- {template.template_path}")
    else:
        print(f"{Fore.GREEN}No unused templates found.")


def print_used_templates(result: TemplateSearchResult):
    if result.used_templates:
        print(f"\n{Fore.CYAN}Used templates found:")
        used_templates_by_app: Dict[str, List[UsedTemplateInfo]] = {}
        for used_template in result.used_templates:
            app_name = (
                used_template.template_info.app_config.name
                if used_template.template_info.app_config
                else "global"
            )
            if app_name not in used_templates_by_app:
                used_templates_by_app[app_name] = []
            used_templates_by_app[app_name].append(used_template)

        for app_name, used_templates in used_templates_by_app.items():
            print(f"\n{Fore.YELLOW}App: {app_name}")
            for used_template in used_templates:
                print(f"{Fore.CYAN}- {used_template.template_info.template_path}")
                for reference in used_template.references:
                    if reference.reference_type == "include":
                        print(
                            f"{Fore.BLUE}  Included in: {Fore.MAGENTA}{reference.template_info.template_path} {Fore.BLUE}at line {Fore.MAGENTA}{reference.line_number}"
                        )
                    elif reference.reference_type == "extend":
                        print(
                            f"{Fore.BLUE}  Extended by: {Fore.MAGENTA}{reference.template_info.template_path} {Fore.BLUE}at line {Fore.MAGENTA}{reference.line_number}"
                        )
                    else:
                        print(
                            f"{Fore.BLUE}  Referenced by ({reference.reference_type}): {Fore.MAGENTA}{reference.template_info.template_path} {Fore.BLUE}at line {Fore.MAGENTA}{reference.line_number}"
                        )
                print()
    else:
        print(f"{Fore.GREEN}No used templates found.")


def find_unused_templates(
    filter_options: Optional[TemplateFilterOptions] = None,
) -> TemplateSearchResult:
    init(autoreset=True)

    start = time.perf_counter()
    print(f"{Fore.CYAN}Starting search for unused templates...\n")

    templates = fetch_templates()
    templates = filter_templates(templates, filter_options)
    result = search_unused_templates(templates)
    print_unused_templates(result)
    print_used_templates(result)

    end = time.perf_counter()
    print(f"\n{Fore.CYAN}Finished in {end - start:.2f} seconds.")
    return result
