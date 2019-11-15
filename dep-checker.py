#!/usr/bin/env python

"""
1. Get package dependencies (rpm -qR jenkins) and transform it into the list
2. Remove duplicates from the list
3. Find a package that provides each resource in the list in the repositories (yum provides "resource_name")
4. Figure out installed version of the package (rpm -qv jenkins)
5. Compare version of the package that provide a resource and installed version of the package
"""

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


def get_resource_packages(output):
    # find lines with package info (e.g. bash-4.2.46-33.el7.x86_64 : The GNU Bourne Again shell)
    line_with_package_info = re.findall('.*-.*-.* : .*', output)

    # extract full packages names from the line and remove duplicates if exist
    resource_packages_list = list(dict.fromkeys([line.split(' : ')[0] for line in line_with_package_info]))

    # remove inaccuracies from package name (e.g. 2:shadow-utils-4.6-5.el7.x86_64 to shadow-utils-4.6-5.el7.x86_64)
    for index, package_ver in enumerate(resource_packages_list):
        if re.match('^[0-9]+:', package_ver) is not None:
            resource_packages_list[index] = re.split('^[0-9]+:', package_ver)[1]
    return resource_packages_list


def extract_package_name(full_name):
    return full_name.rsplit('-', 2)[0]


def get_installed_package(pac_name):
    full_package_name = subprocess.check_output(["rpm", "-qv", pac_name], universal_newlines=True).rstrip()
    return full_package_name

if __name__ == "__main__":
    argv = sys.argv
    args = parse_args(argv)
    package_to_check = args.package

    # TODO: add error handling when package not found
    command = subprocess.check_output(["rpm", "-qR", package_to_check], universal_newlines=True)

    # create a list of package resources and remove duplicates from this list
    rpm_resources_list = list(dict.fromkeys(command.splitlines()))

    for resource in rpm_resources_list:
        # skip rpm resources
        if 'rpmlib' in resource:
            continue
        # TODO: add error handling when information about dependency not found
        command = subprocess.check_output(["yum", "provides", "{}".format(resource)], universal_newlines=True)

        # get resource packages names from the yum output (e.g.
        # ['procps-ng-3.3.10-26.el7.i686', 'procps-ng-3.3.10-26.el7.x86_64', 'procps-ng-3.3.10-26.el7_7.1.i686'])
        resource_packages = get_resource_packages(command)

        # get short package name (e.g. openssl or procps-ng)
        pack_name = extract_package_name(resource_packages[0])

        # get full installed package name (e.g. bash-4.2.46-33.el7.x86_64)
        installed_package = get_installed_package(pack_name)
        print('Dependency: ' + resource)
        print('Dependency packages: ', resource_packages)
        if installed_package in resource_packages:
            print('Installed package: ' + installed_package)
        else:
            # print if packages version not equal
            if pack_name in resource_packages[0]:
                print('Installed package: ' + installed_package + '!!!')
        print()
