import fileinput
import time
from dataclasses import dataclass
from typing import List, Optional, Dict

from colorama import init, Fore

from ...unused.find_templates import find_py_files, find_app_templates, find_global_templates, TemplateInfo


@dataclass
class TemplateFilterOptions:
    excluded_apps: Optional[List[str]] = None
    excluded_template_dirs: Optional[List[str]] = None


def find_unused_templates(filter_options: Optional[TemplateFilterOptions] = None) -> List[TemplateInfo]:
    init(autoreset=True)

    start = time.perf_counter()

    print(f"{Fore.CYAN}Starting search for unused templates...\n")

    print(f"{Fore.CYAN}Fetching global templates...")
    global_templates = find_global_templates()
    print(f"{Fore.GREEN}{len(global_templates)} global templates found.\n")

    print(f"{Fore.CYAN}Fetching app templates...")
    app_templates = find_app_templates()
    initial_app_template_count = len(app_templates)

    # Filter out templates from excluded apps
    if filter_options and filter_options.excluded_apps:
        excluded_apps_set = set(filter_options.excluded_apps)
        app_templates = [t for t in app_templates if t.app_config and t.app_config.name not in excluded_apps_set]
        filtered_app_template_count = initial_app_template_count - len(app_templates)
        print(f"{Fore.YELLOW}{filtered_app_template_count} templates excluded by app filter.\n")

    templates = global_templates + app_templates

    initial_template_count = len(templates)

    # Filter out templates from excluded directories
    if filter_options and filter_options.excluded_template_dirs:
        excluded_dirs_set = set(filter_options.excluded_template_dirs)
        templates = [t for t in templates if not any(t.template_path.startswith(d) for d in excluded_dirs_set)]
        filtered_dir_template_count = initial_template_count - len(templates)
        print(f"{Fore.YELLOW}{filtered_dir_template_count} templates excluded by directory filter.\n")

    print(f"{Fore.GREEN}{len(app_templates)} app templates found after filtering.\n")

    print(f"{Fore.CYAN}Fetching Python files...")
    py_files, _ = find_py_files()
    print(f"{Fore.GREEN}{len(py_files)} Python files found.\n")

    all_files = py_files + [t.file_path for t in templates]
    unused_templates = []

    print(f"{Fore.CYAN}Searching for unused templates...", end="", flush=True)
    for template in templates:
        print(f"{Fore.CYAN}.", end="", flush=True)
        template_found = False
        with fileinput.input(all_files, openhook=fileinput.hook_encoded("utf-8")) as lines:
            for line in lines:
                if template.template_path in line or template.template_path.split('/')[-1] in line:
                    template_found = True
                    break

        if not template_found:
            unused_templates.append(template)
    fileinput.close()

    print(f"\n{Fore.GREEN}Search complete.\n")
    if unused_templates:
        print(f"{Fore.RED}Unused templates found:")
        unused_templates_by_app: Dict[str, List[TemplateInfo]] = {}
        for template in unused_templates:
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

    end = time.perf_counter()
    print(f"\n{Fore.CYAN}Finished in {end - start:.2f} seconds.")
    return unused_templates
