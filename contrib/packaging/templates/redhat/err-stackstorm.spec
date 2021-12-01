Name:       err-stackstorm
Version:    2.2.0
Release:    1
Summary:    Bringing StackStorm ChatOps to errbot.
License:    GPL3, MIT and Apache 2.0

#URL
Source0: /opt/err-stackstorm_2.2.0_centos_8_x86_64.tar.gz
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
echo "Extract tar.gz here?"
tree

%build
cat > hello-world.sh <<EOF
#!/usr/bin/bash
echo Hello world
EOF

%install
mkdir -p %{buildroot}/usr/bin/
install -m 755 hello-world.sh %{buildroot}/usr/bin/hello-world.sh

%files
/usr/bin/hello-world.sh

%changelog
