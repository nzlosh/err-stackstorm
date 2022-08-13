Name:       err-stackstorm
Version:    {{ _common.version }}
Release:    {{ _common.pkg_version }}
Summary:    Bringing StackStorm ChatOps to errbot.
License:    GPL3, MIT and Apache 2.0
Packager:   {{ _common.maintainer.name }} <{{ _common.maintainer.email }}>
BuildRoot:  {{ _runtime.buildroot }}

#URL
Source0: {{ _common.archive.filename }}
BuildArch: x86_64

#BuildRequires:
#Requires:



%description
A python virtual environment with the following software installed:
  - errbot                      GPL3

  - err-backend-discord         GPL3
  - err-backend-slackv3         GPL3
  - err-backend-botframework    MIT Licence
  - err-backend-mattermost      GPL3

  - err-stackstorm              Apache 2.0

%prep
echo No prep

%build
echo Creating archive extraction directory
mkdir -p %{buildroot}

%install
echo Extract archive into rpm buildroot.
tar xvf /root/rpmbuild/SOURCES/{{ _common.archive.filename }} --directory %{buildroot}

%files
/opt/errbot

%changelog
* {{ _runtime.dyslexic_datetime }} {{ _common.maintainer.name }} <{{ _common.maintainer.email }}>
- Virtual environment of errbot and err-stackstorm.
