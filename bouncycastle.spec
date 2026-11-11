Name:		bouncycastle
Version:	1.86
Release:	1
Summary:	Cryptography APIs for Java
Group:		Development/Java
License:	MIT
URL:		https://www.bouncycastle.org/
# Tag r1rv86. Vendored jars under libs/, test/libs/, config/checkstyle/lib/
# and gradle/wrapper/ are removed from the lookaside archive. module-info.java
# is not compiled: a versioned module descriptor makes jmod.deps emit
# jmod(releases:). Core classes are compiled into the provider jar, which is
# how the upstream jdk18on artifacts are built.
Source0:	https://github.com/bcgit/bc-java/archive/refs/tags/r1rv86.tar.gz#/bouncycastle-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar

%description
Bouncy Castle 1.86 is the cryptography library Gradle 9.9.1 pins for
bcprov-jdk18on and bcpg-jdk18on. This package also builds bcutil-jdk18on
and bcpkix-jdk18on with javac. The provider jar carries the Java 11, 15,
17 and 25 overlays under META-INF/versions. The Java 17 overlay is
compiled with -source 17 -target 17 so it can implement javax.crypto.KEMSpi
from the build JDK while staying in the versions/17 tree.

%prep
%autosetup -n bouncycastle-%{version}
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

compile_tree 8 classes/prov "" core/src/main/java prov/src/main/java
compile_tree 8 classes/util classes/prov util/src/main/java
compile_tree 8 classes/pg "classes/prov:classes/util" pg/src/main/java
compile_tree 8 classes/pkix "classes/prov:classes/util" pkix/src/main/java
compile_tree 11 classes/prov11 classes/prov prov/src/main/jdk1.11
compile_tree 15 classes/prov15 "classes/prov:classes/prov11" prov/src/main/jdk1.15

mkdir -p classes/prov17
find prov/src/main/jdk17 -name '*.java' ! -name module-info.java > classes/prov17.sources
# Not --release 17: KEMSpi arrived in Java 21 and this overlay implements it.
javac -source 17 -target 17 -encoding UTF-8 -Xlint:none \
	-cp "classes/prov:classes/prov11:classes/prov15" \
	-d classes/prov17 @classes/prov17.sources

compile_tree 25 classes/prov25 "classes/prov:classes/prov11:classes/prov15:classes/prov17" prov/src/main/jdk25

/bin/cp -a prov/src/main/resources/. classes/prov/
/bin/cp -a pkix/src/main/resources/. classes/pkix/
mkdir -p classes/prov/META-INF/versions/11
mkdir -p classes/prov/META-INF/versions/15
mkdir -p classes/prov/META-INF/versions/17
mkdir -p classes/prov/META-INF/versions/25
/bin/cp -a classes/prov11/. classes/prov/META-INF/versions/11/
/bin/cp -a classes/prov15/. classes/prov/META-INF/versions/15/
/bin/cp -a classes/prov17/. classes/prov/META-INF/versions/17/
/bin/cp -a classes/prov25/. classes/prov/META-INF/versions/25/

printf 'Manifest-Version: 1.0\nMulti-Release: true\n' > manifest-mr.txt
printf 'Manifest-Version: 1.0\n' > manifest.txt
jar cfm bcprov-jdk18on.jar manifest-mr.txt -C classes/prov .
jar cfm bcutil-jdk18on.jar manifest.txt -C classes/util .
jar cfm bcpg-jdk18on.jar manifest.txt -C classes/pg .
jar cfm bcpkix-jdk18on.jar manifest.txt -C classes/pkix .

write_pom() {
	art="$1"
	desc="$2"
	deps="$3"
	cat > "$art.pom" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.bouncycastle</groupId>
  <artifactId>$art</artifactId>
  <version>%{version}</version>
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
	printf '    <dependency>\n      <groupId>org.bouncycastle</groupId>\n      <artifactId>%%s</artifactId>\n      <version>%%s</version>\n    </dependency>\n' "$1" "%{version}"
}

util_deps="$(dep_xml bcprov-jdk18on)"
pg_deps="$(dep_xml bcprov-jdk18on)
$(dep_xml bcutil-jdk18on)"
pkix_deps="$pg_deps"
write_pom bcprov-jdk18on "Bouncy Castle provider" ""
write_pom bcutil-jdk18on "Bouncy Castle ASN.1 utilities" "$util_deps"
write_pom bcpg-jdk18on "Bouncy Castle OpenPGP API" "$pg_deps"
write_pom bcpkix-jdk18on "Bouncy Castle PKIX and CMS API" "$pkix_deps"

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
install_one bcprov-jdk18on.pom bcprov-jdk18on.jar bcprov-jdk18on .mfiles.prov
install_one bcutil-jdk18on.pom bcutil-jdk18on.jar bcutil-jdk18on .mfiles.util
install_one bcpg-jdk18on.pom bcpg-jdk18on.jar bcpg-jdk18on .mfiles.pg
install_one bcpkix-jdk18on.pom bcpkix-jdk18on.jar bcpkix-jdk18on .mfiles.pkix
awk '!seen[$0]++' .mfiles.prov .mfiles.util .mfiles.pg .mfiles.pkix > .mfiles

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
PROV=%{buildroot}%{_javadir}/bcprov-jdk18on.jar
UTIL=%{buildroot}%{_javadir}/bcutil-jdk18on.jar
PG=%{buildroot}%{_javadir}/bcpg-jdk18on.jar
PKIX=%{buildroot}%{_javadir}/bcpkix-jdk18on.jar
test -f "$PROV"
test -f "$UTIL"
test -f "$PG"
test -f "$PKIX"
unzip -p "$PROV" META-INF/MANIFEST.MF | grep -F 'Multi-Release: true'
jar tf "$PROV" | grep -F 'META-INF/versions/17/org/bouncycastle/pqc/jcajce/provider/ntru/NTRUKEMSpi.class'
jar tf "$PROV" | grep -F 'META-INF/versions/25/org/bouncycastle/jcajce/provider/kdf/hkdf/HKDFSpi.class'
for jarfile in "$PROV" "$UTIL" "$PG" "$PKIX"; do
	if jar tf "$jarfile" | grep -q module-info; then
		echo "module-info leaked into $jarfile" >&2
		exit 1
	fi
done
mkdir -p check
cat > check/Smoke.java <<'END'
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
		System.out.println("bc_ok " + Security.getProvider("BC").getName());
	}
}
END
javac --release 8 -encoding UTF-8 -Xlint:-options \
	-cp "$PROV:$UTIL:$PG:$PKIX" -d check check/Smoke.java
java -cp "check:$PROV:$UTIL:$PG:$PKIX" Smoke > check/out.txt
cat check/out.txt
grep -F -q 'bc_ok BC' check/out.txt

%files -f .mfiles
%license LICENSE.md LICENSE.html
%doc README.md SECURITY.md
