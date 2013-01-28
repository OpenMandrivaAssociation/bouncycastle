%global ver  1.46
%global archivever  jdk16-%(echo %{ver}|sed 's|\\\.||')
%global classname   org.bouncycastle.jce.provider.BouncyCastleProvider

Summary:          Bouncy Castle Crypto Package for Java
Name:             bouncycastle
Version:          %{ver}
Release:          7
Group:            Development/Java
License:          MIT
URL:              http://www.%{name}.org/
# Use original sources from here on out.
Source0:          http://www.bouncycastle.org/download/bcprov-%{archivever}.tar.gz
Source1:          http://repo2.maven.org/maven2/org/bouncycastle/bcprov-jdk16/%{version}/bcprov-jdk16-%{version}.pom
BuildRequires:    jpackage-utils >= 1.5
Requires:         jpackage-utils >= 1.5
Requires(post):   jpackage-utils >= 1.7
Requires(postun): jpackage-utils >= 1.7
BuildArch:        noarch
BuildRequires:    java-devel >= 1.7
Requires:         java >= 1.7
BuildRequires:    junit4
BuildRequires:    java-rpmbuild

Provides:         bcprov = %{version}-%{release}

%description
The Bouncy Castle Crypto package is a Java implementation of cryptographic
algorithms. The package is organised so that it contains a light-weight API
suitable for use in any environment (including the newly released J2ME) with
the additional infrastructure to conform the algorithms to the JCE framework.

%package javadoc
Summary:        Javadoc for %{name}
Group:          Development/Java
BuildArch:      noarch
Requires:       %{name} = %{version}-%{release}
Requires:       jpackage-utils

%description javadoc
API documentation for the %{name} package.

%prep
%setup -q -n bcprov-%{archivever}

# Remove provided binaries
find . -type f -name "*.class" -exec rm -f {} \;
find . -type f -name "*.jar" -exec rm -f {} \;

mkdir src
unzip -qq src.zip -d src/

%build
pushd src
  export CLASSPATH=$(build-classpath junit4)
  %javac -g -source 1.6 -target 1.6 -encoding UTF-8 $(find . -type f -name "*.java")
  jarfile="../bcprov-%{version}.jar"
  # Exclude all */test/* files except org.bouncycastle.util.test, cf. upstream
  files="$(find . -type f \( -name '*.class' -o -name '*.properties' \) -not -path '*/test/*')"
  files="$files $(find . -type f -path '*/org/bouncycastle/util/test/*.class')"
  files="$files $(find . -type f -path '*/org/bouncycastle/jce/provider/test/*.class')"
  files="$files $(find . -type f -path '*/org/bouncycastle/ocsp/test/*.class')"
  test ! -d classes && mf="" \
    || mf="`find classes/ -type f -name "*.mf" 2>/dev/null`"
  test -n "$mf" && jar cvfm $jarfile $mf $files \
    || %jar cvf $jarfile $files
popd

%install
install -dm 755 %{buildroot}%{_sysconfdir}/java/security/security.d
touch %{buildroot}%{_sysconfdir}/java/security/security.d/2000-%{classname}

# install bouncy castle provider
install -dm 755 %{buildroot}%{_javadir}
install -pm 644 bcprov-%{version}.jar \
  %{buildroot}%{_javadir}/bcprov-%{version}.jar
pushd %{buildroot}%{_javadir}
  ln -sf bcprov-%{version}.jar bcprov.jar
popd
  install -dm 755 %{buildroot}%{_javadir}/gcj-endorsed
  pushd %{buildroot}%{_javadir}/gcj-endorsed
    ln -sf ../bcprov-%{version}.jar bcprov-%{version}.jar
  popd

# javadoc
mkdir -p %{buildroot}%{_javadocdir}/%{name}
cp -pr docs/* %{buildroot}%{_javadocdir}/%{name}

# maven pom
install -dm 755 %{buildroot}%{_mavenpomdir}
install -pm 644 %{SOURCE1} %{buildroot}%{_mavenpomdir}/JPP-bcprov.pom
%add_to_maven_depmap org.bouncycastle bcprov-jdk16 %{version} JPP bcprov

%check
pushd src
  export CLASSPATH=$PWD:$(build-classpath junit4)
  for test in $(find . -name AllTests.class) ; do
    test=${test#./} ; test=${test%.class} ; test=${test//\//.}
    # TODO: failures; get them fixed and remove || :
    %java org.junit.runner.JUnitCore $test || :
  done
popd


%post
{
  # Rebuild the list of security providers in classpath.security
  suffix=security/classpath.security
  secfiles="/usr/lib/$suffix /usr/lib64/$suffix"

  for secfile in $secfiles
  do
    # check if this classpath.security file exists
    [ -f "$secfile" ] || continue

    sed -i '/^security\.provider\./d' "$secfile"

    count=0
    for provider in $(ls /etc/java/security/security.d)
    do
      count=$((count + 1))
      echo "security.provider.${count}=${provider#*-}" >> "$secfile"
    done
  done
} || :

%update_maven_depmap

%postun
if [ $1 -eq 0 ] ; then

  {
    # Rebuild the list of security providers in classpath.security
    suffix=security/classpath.security
    secfiles="/usr/lib/$suffix /usr/lib64/$suffix"

    for secfile in $secfiles
    do
      # check if this classpath.security file exists
      [ -f "$secfile" ] || continue

      sed -i '/^security\.provider\./d' "$secfile"

      count=0
      for provider in $(ls /etc/java/security/security.d)
      do
        count=$((count + 1))
        echo "security.provider.${count}=${provider#*-}" >> "$secfile"
      done
    done
  } || :

fi
%update_maven_depmap

%files
%doc *.html
%{_javadir}/bcprov.jar
%{_javadir}/bcprov-%{version}.jar
  %{_javadir}/gcj-endorsed/bcprov-%{version}.jar
%{_sysconfdir}/java/security/security.d/2000-%{classname}
%{_mavenpomdir}/JPP-bcprov.pom
%{_mavendepmapfragdir}/%{name}

%files javadoc
%{_javadocdir}/%{name}/
