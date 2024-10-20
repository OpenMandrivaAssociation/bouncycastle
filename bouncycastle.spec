%{?_javapackages_macros:%_javapackages_macros}
%global ver 1.50
%global archivever jdk15on-%(echo %{ver}|sed 's|\\\.||')
%global classname org.bouncycastle.jce.provider.BouncyCastleProvider

Summary:          Bouncy Castle Crypto Package for Java
Name:             bouncycastle
Version:          %{ver}
Release:          5%{?dist}
License:          MIT
URL:              https://www.bouncycastle.org
# Use original sources from here on out.
Source0:          http://www.bouncycastle.org/download/bcprov-%{archivever}.tar.gz
Source1:          http://repo1.maven.org/maven2/org/bouncycastle/bcprov-jdk15on/%{ver}/bcprov-jdk15on-%{ver}.pom
BuildRequires:    javapackages-tools
Requires:         javapackages-tools
Requires(post):   javapackages-tools
Requires(postun): javapackages-tools
BuildArch:        noarch
BuildRequires:    java-devel
Requires:         java-headless
BuildRequires:    junit

Provides:         bcprov = %{version}-%{release}

%description
The Bouncy Castle Crypto package is a Java implementation of cryptographic
algorithms. The package is organized so that it contains a light-weight API
suitable for use in any environment (including the newly released J2ME) with
the additional infrastructure to conform the algorithms to the JCE framework.

%package javadoc
Summary:        Javadoc for %{name}

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
  export CLASSPATH=$(build-classpath junit)
  %javac -g -source 1.5 -target 1.5 -encoding UTF-8 $(find . -type f -name "*.java")
  jarfile="../bcprov.jar"
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
install -dm 755 $RPM_BUILD_ROOT%{_sysconfdir}/java/security/security.d
touch $RPM_BUILD_ROOT%{_sysconfdir}/java/security/security.d/2000-%{classname}

# install bouncy castle provider
install -dm 755 $RPM_BUILD_ROOT%{_javadir}
install -pm 644 bcprov.jar \
  $RPM_BUILD_ROOT%{_javadir}/

install -dm 755 $RPM_BUILD_ROOT%{_javadir}/gcj-endorsed
pushd $RPM_BUILD_ROOT%{_javadir}/gcj-endorsed
  ln -sf ../bcprov.jar bcprov.jar
popd

# javadoc
mkdir -p $RPM_BUILD_ROOT%{_javadocdir}/%{name}
cp -pr docs/* $RPM_BUILD_ROOT%{_javadocdir}/%{name}

# maven pom
install -dm 755 $RPM_BUILD_ROOT%{_mavenpomdir}
install -pm 644 %{SOURCE1} $RPM_BUILD_ROOT%{_mavenpomdir}/JPP-bcprov.pom
%add_maven_depmap -a "bouncycastle:bcprov-jdk15,org.bouncycastle:bcprov-jdk16,org.bouncycastle:bcprov-jdk15" JPP-bcprov.pom bcprov.jar

%check
pushd src
  export CLASSPATH=$PWD:$(build-classpath junit)
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

%files -f .mfiles
%doc *.html
%{_javadir}/gcj-endorsed/bcprov.jar
%{_sysconfdir}/java/security/security.d/2000-%{classname}

%files javadoc
%{_javadocdir}/%{name}/

%changelog
* Wed Oct 22 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.50-5
- Add alias for org.bouncycastle:bcprov-jdk15

* Mon Jun 09 2014 Michal Srb <msrb@redhat.com> - 1.50-4
- Migrate to .mfiles

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.50-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Wed Feb 26 2014 Michal Srb <msrb@redhat.com> - 1.50-2
- Fix java BR/R
- Build with -source/target 1.5
- s/organised/organized/

* Fri Feb 21 2014 Michal Srb <msrb@redhat.com> - 1.50-1
- Update to upstream version 1.50
- Switch to java-headless

* Mon Jan  6 2014 Mikolaj Izdebski <mizdebsk@redhat.com> - 1.46-12
- Add Maven alias for bouncycastle:bcprov-jdk15

* Tue Oct 22 2013 gil cattaneo <puntogil@libero.it> 1.46-11
- remove versioned Jars

* Thu Aug 29 2013 gil cattaneo <puntogil@libero.it> 1.46-10
- remove update_maven_depmap

* Mon Aug 05 2013 gil cattaneo <puntogil@libero.it> 1.46-9
- rebuilt rhbz#992026

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.46-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Wed Feb 13 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.46-7
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Wed Jul 18 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.46-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Tue May 08 2012 Tom Callaway <spot@fedoraproject.org> - 1.46-5
- use original sources from here on out

* Sat Feb 18 2012 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.46-4
- Build with -source 1.6 -target 1.6 

* Thu Jan 12 2012 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.46-3
- Update javac target version to 1.7 to build with new java

* Thu Jan 12 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.46-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Tue Mar 01 2011 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.46-1
- Import Bouncy Castle 1.46.

* Mon Feb 07 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.45-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Thu Dec 30 2010 Alexander Kurtakov <akurtako@redhat.com> 1.45-2
- Drop gcj.
- Adapt to current guidelines.

* Thu Feb 11 2010 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.45-1
- Import Bouncy Castle 1.45.

* Sat Nov 14 2009 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.44-1
- Import Bouncy Castle 1.44.

* Sun Sep  6 2009 Ville Skyttä <ville.skytta@iki.fi> - 1.43-6
- Include improvements from #521475:
- Include missing properties files in jar.
- Build with javac -encoding UTF-8.
- Use %%javac and %%jar macros.
- Run test suite during build (ignoring failures for now).
- Follow upstream in excluding various test suite classes from jar; drop
  dependency on junit4.

* Wed Aug 26 2009 Andrew Overholt <overholt@redhat.com> 1.43-5
- Add maven POM

* Fri Jul 24 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.43-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Sat Jul 11 2009 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.43-3
- Raise java requirement to >= 1.7 once again.

* Fri Jul 10 2009 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.43-2
- Re-enable AOT bits thanks to Andrew Haley.

* Mon Apr 20 2009 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.43-1
- Import Bouncy Castle 1.43.

* Sat Apr 18 2009 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.42-3
- Don't build AOT bits. The package needs java1.6

* Thu Apr 09 2009 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.42-2
- Add missing Requires: junit4

* Tue Mar 17 2009 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.42-1
- Import Bouncy Castle 1.42.
- Update description.
- Add javadoc subpackage.

* Mon Feb 23 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.41-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Wed Nov 11 2008 Orcan Ogetbil <oget [DOT] fedora [AT] gmail [DOT] com> - 1.41-2
- Fixed license tag (BSD -> MIT).
- Minor improvements in the SPEC file for better compatibility with the 
  Fedora Java Packaging Guidelines.
- Added "Provides: bcprov == %%{version}-%%{release}".

* Thu Oct  2 2008 Lillian Angel <langel@redhat.com> - 1.41-1
- Import Bouncy Castle 1.41.
- Resolves: rhbz#465203

* Thu May 15 2008 Thomas Fitzsimmons <fitzsim@redhat.com> - 1.39-1
- Import Bouncy Castle 1.39.
- Set target to 1.5.

* Mon Feb 18 2008 Fedora Release Engineering <rel-eng@fedoraproject.org> - 1.38-2
- Autorebuild for GCC 4.3

* Thu Nov 29 2007 Thomas Fitzsimmons <fitzsim@redhat.com> - 1.38-1
- Import Bouncy Castle 1.38.
- Require junit4 for build.
- Require java-1.7.0-icedtea-devel for build.
- Wrap lines at 80 columns.
- Inline rebuild-security-providers in post and postun sections.
- Related: rhbz#260161

* Sat Mar 31 2007 Thomas Fitzsimmons <fitzsim@redhat.com> - 1.34-3
- Require java-1.5.0-gcj.

* Tue Dec 12 2006 Thomas Fitzsimmons <fitzsim@redhat.com> - 1.34-2
- Install bcprov jar and unversioned symlink in %%{_javadir}.
- Install bcprov symlink in %%{_javadir}/gcj-endorsed.
- Change release numbering format to X.fc7.
- Include new bcprov files in files list.
- Import Bouncy Castle 1.34.
- Related: rhbz#218794

* Tue Jul 25 2006 Thomas Fitzsimmons <fitzsim@redhat.com> - 1.33-3
- Bump release number.

* Mon Jul 10 2006 Thomas Fitzsimmons <fitzsim@redhat.com> - 1.33-2
- Fix problems pointed out by reviewer.

* Fri Jul  7 2006 Thomas Fitzsimmons <fitzsim@redhat.com> - 1.33-1
- First release.

