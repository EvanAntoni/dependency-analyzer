#!/usr/bin/env python

import subprocess, sys, argparse
import re


def parse_args(arguments):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-p', '--package',
        help='package name for checking'
    )

    if len(arguments) == 1:
        parser.print_help()
        exit(1)

    return parser.parse_args(arguments[1:])


def colored_text(text, color):
    """Transform text color in the terminal

    :param text: text to transform
    :type text: str
    :param color: text color
    :type color: str
    :return: colored text
    :rtype: str

    Function gets a text and a color code which must be present in the dictionary with color codes.
    Color code inserts at the start of the text and must be reset at the end on the default color
    for the terminal.
    """

    colors = {
        'blue': '\033[94m',
        'green': '\033[92m',
        'red': '\033[91m',
        'clear': '\033[0m'
    }

    text_with_color = colors[color] + text + colors['clear']

    return text_with_color


def get_command_output(command):
    """Execute command and return its output.

    :param command: command (exec format)
    :type command: list
    :return: command output
    :rtype: str

    Execute command and return its output. If the return code is not 0, command
    and its output with the return code will be printed.
    """

    try:
        output = subprocess.check_output(command, universal_newlines=True)
        return output
    except subprocess.CalledProcessError as cpe:
        print(command)
        print(cpe.output)
        print('Command error code: {}'.format(cpe.returncode))
        exit(1)


def get_resource_packages(output):
    """Get packages which provide dependency.

    :param output: output provided by yum provides package_name
    :type output: str
    :return: list of packages which provide dependency
    :rtype: list

    Parse `yum provides package_name` command output and extract names of packages
    in the correct format (e.g. bash-4.2.46-33.el7.x86_64).
    """

    # find lines with package info (e.g. bash-4.2.46-33.el7.x86_64 : The GNU Bourne Again shell)
    line_with_package_info = re.findall('.*-.*-.* : .*', output)

    # extract full packages names from the line and remove duplicates if exist
    resource_packages_list = list(dict.fromkeys([line.split(' : ')[0] for line in line_with_package_info]))

    # remove inaccuracies from package name (e.g. 2:shadow-utils-4.6-5.el7.x86_64 to shadow-utils-4.6-5.el7.x86_64)
    for index, package_ver in enumerate(resource_packages_list):
        if re.match('^[0-9]+:', package_ver) is not None:
            resource_packages_list[index] = re.split('^[0-9]+:', package_ver)[1]
    return resource_packages_list


def extract_package_name(full_package_name):
    """Extract package name from the full package name.

    :param full_package_name: full package name (with version, build number, and architecture)
    :type full_package_name: str
    :return: package name
    :rtype: str

    Take the full package name (e.g. shadow-utils-4.6-5.el7.x86_64)
    and extract the package name from it (shadow-utils)
    """

    return full_package_name.rsplit('-', 2)[0]


def get_installed_packages(package_name):
    """Get packages names which installed in the system by a short package name.

    :param package_name: short package name (jenkins)
    :type package_name: str
    :return: list of full package names (with version, build number, and architecture)
    :rtype: list

    Get full package names installed in the system by the short package name.
    It uses for comparing a version of the package which dependency requires.
    """

    command_exec = ["rpm", "-qv", package_name]
    full_package_names = get_command_output(command_exec).rstrip().splitlines()
    return full_package_names


def get_rpm_resources_list(package_name):
    """Get a list of dependencies required for the package.

    :param package_name: name of the package
    :type package_name: str
    :return: list with package dependencies
    :rtype: list

    Run `rpm -qR package_name` command and process its output to get a dependency list.
    """
    command_exec = ["rpm", "-qR", package_name]
    resources_list_output = get_command_output(command_exec)

    # create a list of package resources and remove duplicates from this list
    resources_list = list(dict.fromkeys(resources_list_output.splitlines()))
    return resources_list


def process_rpm_resources_list(resources_list):
    """Process package dependency list.

    :param resources_list: list with package dependencies
    :type resources_list: list

    This is the main function of dependency processing. It gets dependency
    check which package provides this dependency and compares the version
    of this package with the package version installed in the system.
    After this, it prints information about dependency its package and
    highlight package name if there are differences between the required
    dependency package version and version of the package installed in the system.
    """

    for resource in resources_list:
        # skip rpm resources
        if 'rpmlib' in resource:
            continue

        command_exec = ["yum", "provides", "{}".format(resource)]
        dependency_packages_output = get_command_output(command_exec)

        # skip dependency if information about it doesn't present in the yum repos
        if 'No matches found' in dependency_packages_output:
            print(command_exec)
            print('Resource "{}" | No matches found in repositories\n'.format(resource))
            continue

        # get resource packages names from the yum output (e.g.
        # ['procps-ng-3.3.10-26.el7.i686', 'procps-ng-3.3.10-26.el7.x86_64', 'procps-ng-3.3.10-26.el7_7.1.i686'])
        resource_packages = get_resource_packages(dependency_packages_output)

        # get short package name (e.g. openssl or procps-ng)
        pack_name = extract_package_name(resource_packages[0])

        # get full installed package name (e.g. bash-4.2.46-33.el7.x86_64)
        installed_packages = get_installed_packages(pack_name)
        print('Dependency: ' + resource)
        print('Dependency packages: ', end='')
        for package in resource_packages:
             if package in installed_packages:
                 print('"{}"'.format(colored_text(package, 'green')), end=' ')
             else:
                 print('"{}"'.format(package), end=' ')

        print('\nInstalled packages: ', end='')
        inst_in_res = [pack for pack in installed_packages if pack in resource_packages]
        for installed_package in installed_packages:
            if installed_package in inst_in_res:
                print('"{}"'.format(colored_text(installed_package, 'green')), end=' ')
            else:
                if pack_name in resource_packages[0]:
                    print('"{}"'.format(colored_text(installed_package, 'red')), end=' ')
                else:
                    print('"{}"'.format(installed_package), end=' ')
        print('\n', end='\n')


if __name__ == "__main__":
    argv = sys.argv
    args = parse_args(argv)
    package_to_check = args.package

    rpm_resources_list = get_rpm_resources_list(package_to_check)

    process_rpm_resources_list(rpm_resources_list)
