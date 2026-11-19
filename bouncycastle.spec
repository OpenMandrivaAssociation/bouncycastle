Name:		bouncycastle
Version:	1.87
Release:	1
Summary:	Cryptography APIs for Java
Group:		Development/Java
License:	MIT
URL:		https://www.bouncycastle.org/
# Tag r1rv87. Vendored jars under libs/, test/libs/, config/checkstyle/lib/
# and gradle/wrapper/ are removed from the lookaside archive. module-info.java
# is not compiled: a versioned module descriptor makes jmod.deps emit
# jmod(releases:). Core classes are compiled into the provider jar, which is
# how the upstream jdk18on artifacts are built. Gradle 9.9.1 strictly pins
# bcprov-jdk18on and bcpg-jdk18on at 1.86, so Source1 is that release.
Source0:	https://github.com/bcgit/bc-java/archive/refs/tags/r1rv87.tar.gz#/bouncycastle-%{version}.tar.gz
Source1:	https://github.com/bcgit/bc-java/archive/refs/tags/r1rv86.tar.gz#/bouncycastle-1.86.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar

%description
Bouncy Castle %{version} cryptography APIs, built with javac as
bcprov-jdk18on, bcutil-jdk18on, bcpg-jdk18on and bcpkix-jdk18on.
Gradle 9.9.1 strictly pins the provider and OpenPGP jars at 1.86, so
those 1.86 jars and the util and PKIX jars they were built with are
installed beside the %{version} jars.

1.87 fixes CVE-2026-103605, CVE-2026-103606, CVE-2026-103607,
CVE-2026-103608, CVE-2026-103610, CVE-2026-103611, CVE-2026-103612,
CVE-2026-103613, CVE-2026-103614, CVE-2026-103615, CVE-2026-103616 and
CVE-2026-103617. Those cover unbounded legacy PBE iteration counts,
MD5 time-stamp imprints, OpenPGP revocation merging, quadratic X.500
and MIME parsing, and ML-KEM / NTRU rejection secrets. The deprecated
XMSS and LMS implementations under the old package names are removed.
The provider jar still carries the Java 11, 15, 17 and 25 overlays.
The Java 17 overlay is compiled with -source 17 -target 17 so it can
implement javax.crypto.KEMSpi.

%prep
%autosetup -n bouncycastle-%{version}
%setup -q -T -D -a 1 -n bouncycastle-%{version}
find . -name '*.jar' -delete
find . -name '*.class' -delete

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH

compile_tree() {
	rel="$1"
	dest="$2"
	cp="$3"
	shift 3
	mkdir -p "$dest"
	find "$@" -name '*.java' ! -name module-info.java > "$dest.sources"
	if [ ! -s "$dest.sources" ]; then
		echo "no sources for $dest" >&2
		exit 1
	fi
	if [ -n "$cp" ]; then
		javac --release "$rel" -encoding UTF-8 -Xlint:none \
			-cp "$cp" -d "$dest" @"$dest.sources"
	else
		javac --release "$rel" -encoding UTF-8 -Xlint:none \
			-d "$dest" @"$dest.sources"
	fi
}

compile_bc() {
	root="$1"
	ver="$2"
	(
		cd "$root"
		set -eo pipefail
		compile_tree 8 out/classes/prov "" core/src/main/java prov/src/main/java
		compile_tree 8 out/classes/util out/classes/prov util/src/main/java
		compile_tree 8 out/classes/pg "out/classes/prov:out/classes/util" pg/src/main/java
		compile_tree 8 out/classes/pkix "out/classes/prov:out/classes/util" pkix/src/main/java
		compile_tree 11 out/classes/prov11 out/classes/prov prov/src/main/jdk1.11
		compile_tree 15 out/classes/prov15 "out/classes/prov:out/classes/prov11" prov/src/main/jdk1.15

		mkdir -p out/classes/prov17
		find prov/src/main/jdk17 -name '*.java' ! -name module-info.java > out/classes/prov17.sources
		# Not --release 17: KEMSpi arrived in Java 21 and this overlay implements it.
		javac -source 17 -target 17 -encoding UTF-8 -Xlint:none \
			-cp "out/classes/prov:out/classes/prov11:out/classes/prov15" \
			-d out/classes/prov17 @out/classes/prov17.sources

		compile_tree 25 out/classes/prov25 "out/classes/prov:out/classes/prov11:out/classes/prov15:out/classes/prov17" prov/src/main/jdk25

		/bin/cp -a prov/src/main/resources/. out/classes/prov/
		/bin/cp -a pkix/src/main/resources/. out/classes/pkix/
		mkdir -p out/classes/prov/META-INF/versions/11
		mkdir -p out/classes/prov/META-INF/versions/15
		mkdir -p out/classes/prov/META-INF/versions/17
		mkdir -p out/classes/prov/META-INF/versions/25
		/bin/cp -a out/classes/prov11/. out/classes/prov/META-INF/versions/11/
		/bin/cp -a out/classes/prov15/. out/classes/prov/META-INF/versions/15/
		/bin/cp -a out/classes/prov17/. out/classes/prov/META-INF/versions/17/
		/bin/cp -a out/classes/prov25/. out/classes/prov/META-INF/versions/25/

		printf 'Manifest-Version: 1.0\nMulti-Release: true\n' > out/manifest-mr.txt
		printf 'Manifest-Version: 1.0\n' > out/manifest.txt
		jar cfm out/bcprov-jdk18on.jar out/manifest-mr.txt -C out/classes/prov .
		jar cfm out/bcutil-jdk18on.jar out/manifest.txt -C out/classes/util .
		jar cfm out/bcpg-jdk18on.jar out/manifest.txt -C out/classes/pg .
		jar cfm out/bcpkix-jdk18on.jar out/manifest.txt -C out/classes/pkix .

		write_pom() {
			art="$1"
			desc="$2"
			deps="$3"
			cat > "out/$art.pom" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.bouncycastle</groupId>
  <artifactId>$art</artifactId>
  <version>$ver</version>
  <name>$art</name>
  <description>$desc</description>
  <url>https://www.bouncycastle.org/</url>
  <licenses>
    <license>
      <name>MIT</name>
      <url>https://www.bouncycastle.org/licence.html</url>
    </license>
  </licenses>
  <dependencies>
$deps
  </dependencies>
</project>
EOF
		}

		dep_xml() {
			printf '    <dependency>\n      <groupId>org.bouncycastle</groupId>\n      <artifactId>%%s</artifactId>\n      <version>%%s</version>\n    </dependency>\n' "$1" "$ver"
		}

		util_deps="$(dep_xml bcprov-jdk18on)"
		pg_deps="$(dep_xml bcprov-jdk18on)
$(dep_xml bcutil-jdk18on)"
		pkix_deps="$pg_deps"
		write_pom bcprov-jdk18on "Bouncy Castle provider" ""
		write_pom bcutil-jdk18on "Bouncy Castle ASN.1 utilities" "$util_deps"
		write_pom bcpg-jdk18on "Bouncy Castle OpenPGP API" "$pg_deps"
		write_pom bcpkix-jdk18on "Bouncy Castle PKIX and CMS API" "$pkix_deps"
		grep -F -q "<version>$ver</version>" out/bcprov-jdk18on.pom
		grep -F -q "<version>$ver</version>" out/bcpg-jdk18on.pom
	)
}

compile_bc . %{version}
compile_bc bouncycastle-1.86 1.86

%install
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
install_one() {
	sysjar install --buildroot %{buildroot} \
		--artifact "$1":"$2" \
		--file-name "$3" \
		--filelist "$4"
}
pin_old() {
	art="$1"
	install_one "bouncycastle-1.86/out/${art}.pom" "bouncycastle-1.86/out/${art}.jar" "${art}-1.86" ".mfiles-${art}-186"
	/bin/mv "%{buildroot}/usr/share/sysjar/index/org.bouncycastle/${art}.sysjar" \
		"%{buildroot}/usr/share/sysjar/index/org.bouncycastle/${art}-1.86.sysjar"
	sed -i "s|/usr/share/sysjar/index/org.bouncycastle/${art}\\.sysjar|/usr/share/sysjar/index/org.bouncycastle/${art}-1.86.sysjar|" ".mfiles-${art}-186"
}
pin_old bcprov-jdk18on
pin_old bcutil-jdk18on
pin_old bcpg-jdk18on
pin_old bcpkix-jdk18on
install_one out/bcprov-jdk18on.pom out/bcprov-jdk18on.jar bcprov-jdk18on .mfiles-bcprov
install_one out/bcutil-jdk18on.pom out/bcutil-jdk18on.jar bcutil-jdk18on .mfiles-bcutil
install_one out/bcpg-jdk18on.pom out/bcpg-jdk18on.jar bcpg-jdk18on .mfiles-bcpg
install_one out/bcpkix-jdk18on.pom out/bcpkix-jdk18on.jar bcpkix-jdk18on .mfiles-bcpkix
awk '!seen[$0]++' .mfiles-bcprov-jdk18on-186 .mfiles-bcutil-jdk18on-186 .mfiles-bcpg-jdk18on-186 .mfiles-bcpkix-jdk18on-186 .mfiles-bcprov .mfiles-bcutil .mfiles-bcpg .mfiles-bcpkix > .mfiles

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
check_mr() {
	prov="$1"
	test -s "$prov"
	unzip -p "$prov" META-INF/MANIFEST.MF | grep -F 'Multi-Release: true'
	jar tf "$prov" | grep -F 'META-INF/versions/17/org/bouncycastle/pqc/jcajce/provider/ntru/NTRUKEMSpi.class'
	jar tf "$prov" | grep -F 'META-INF/versions/25/org/bouncycastle/jcajce/provider/kdf/hkdf/HKDFSpi.class'
}
check_mr %{buildroot}%{_javadir}/bcprov-jdk18on.jar
check_mr %{buildroot}%{_javadir}/bcprov-jdk18on-1.86.jar
for jarfile in \
	%{buildroot}%{_javadir}/bcprov-jdk18on.jar \
	%{buildroot}%{_javadir}/bcutil-jdk18on.jar \
	%{buildroot}%{_javadir}/bcpg-jdk18on.jar \
	%{buildroot}%{_javadir}/bcpkix-jdk18on.jar \
	%{buildroot}%{_javadir}/bcprov-jdk18on-1.86.jar \
	%{buildroot}%{_javadir}/bcutil-jdk18on-1.86.jar \
	%{buildroot}%{_javadir}/bcpg-jdk18on-1.86.jar \
	%{buildroot}%{_javadir}/bcpkix-jdk18on-1.86.jar
do
	test -s "$jarfile"
	if jar tf "$jarfile" | grep -q module-info; then
		echo "module-info leaked into $jarfile" >&2
		exit 1
	fi
done
smoke_one() {
	label="$1"
	prov="$2"
	util="$3"
	pg="$4"
	pkix="$5"
	mkdir -p "check-$label"
	cat > "check-$label/Smoke.java" << 'END'
import java.security.Security;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.bouncycastle.openpgp.operator.bc.BcKeyFingerprintCalculator;

public class Smoke {
	public static void main(String[] args) throws Exception {
		Security.addProvider(new BouncyCastleProvider());
		if (Security.getProvider("BC") == null) {
			throw new AssertionError("no BC");
		}
		new BcKeyFingerprintCalculator();
		Class.forName("org.bouncycastle.bcpg.ArmoredOutputStream");
		Class.forName("org.bouncycastle.cert.X509CertificateHolder");
		System.out.println(args[0] + " " + Security.getProvider("BC").getName());
	}
}
END
	javac --release 8 -encoding UTF-8 -Xlint:-options \
		-cp "$prov:$util:$pg:$pkix" -d "check-$label" "check-$label/Smoke.java"
	java -cp "check-$label:$prov:$util:$pg:$pkix" Smoke "$label" > "check-$label/out.txt"
	cat "check-$label/out.txt"
	grep -F -q "$label BC" "check-$label/out.txt"
}
smoke_one bc187_ok \
	%{buildroot}%{_javadir}/bcprov-jdk18on.jar \
	%{buildroot}%{_javadir}/bcutil-jdk18on.jar \
	%{buildroot}%{_javadir}/bcpg-jdk18on.jar \
	%{buildroot}%{_javadir}/bcpkix-jdk18on.jar
smoke_one bc186_ok \
	%{buildroot}%{_javadir}/bcprov-jdk18on-1.86.jar \
	%{buildroot}%{_javadir}/bcutil-jdk18on-1.86.jar \
	%{buildroot}%{_javadir}/bcpg-jdk18on-1.86.jar \
	%{buildroot}%{_javadir}/bcpkix-jdk18on-1.86.jar

%files -f .mfiles
%license LICENSE.md LICENSE.html
%doc README.md SECURITY.md
