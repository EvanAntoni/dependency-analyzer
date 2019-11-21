# Dependency Analyzer

This script check dependencies for the package which provided as an argument. It works as an add-on 
to yum and rpm based on their output. Script gets package dependencies, checks what packages provide 
these dependencies and compare their version with the package version installed in the system.

## Installation

Script works with the standard python library. No additional installations required.

## Usage

```bash
./dep-checker.py -p package_name
```

Example:
```bash
./dep-checker.py -p jenkins
```

Output:
```bash
Dependency: /bin/sh
Dependency packages: "bash-4.2.46-33.el7.x86_64"
Installed package: bash-4.2.46-33.el7.x86_64

Dependency: /usr/sbin/groupadd
Dependency packages: "shadow-utils-4.6-5.el7.x86_64"
Installed package: shadow-utils-4.6-5.el7.x86_64

Dependency: /usr/sbin/useradd
Dependency packages: "shadow-utils-4.6-5.el7.x86_64"
Installed package: shadow-utils-4.6-5.el7.x86_64

Dependency: config(jenkins) = 2.190.1-1.1
Dependency packages: "jenkins-2.190.1-1.1.noarch"
Installed package: jenkins-2.190.1-1.1.noarch

Dependency: procps
Dependency packages: "procps-ng-3.3.10-26.el7.i686" "procps-ng-3.3.10-26.el7.x86_64" "procps-ng-3.3.10-26.el7_7.1.i686" "procps-ng-3.3.10-26.el7_7.1.x86_64"
Installed package: procps-ng-3.3.10-26.el7.x86_64
```

## Tested on

Python 3.6

CentOS 7.7