ExclusiveArch: x86_64 aarch64

%define GITDATE        20180508
%define GITCOMMIT      ee3198e672e2

%global debug_package %{nil}

Name:       ovmf
Version:    %{GITDATE}
Release:    3.git%{GITCOMMIT}%{?dist}
Summary:    UEFI firmware for 64-bit virtual machines
Group:      Applications/Emulators
License:    BSD and OpenSSL and MIT
URL:        http://www.tianocore.org

# The source tarball is created using following commands:
# COMMIT=%{GITCOMMIT}
# git archive --format=tar --prefix=ovmf-$COMMIT/ $COMMIT \
# | xz -9ev >/tmp/ovmf-$COMMIT.tar.xz
Source0: http://batcave.lab.eng.brq.redhat.com/www/ovmf-%{GITCOMMIT}.tar.xz
Source1: ovmf-whitepaper-c770f8c.txt
Source2: openssl-fedora-264133c642cdb6fc916f1d9bba9db4cb4cd4a17c.tar.xz
Source3: ovmf-vars-generator
Source4: LICENSE.qosb

Patch0003: 0003-advertise-OpenSSL-on-TianoCore-splash-screen-boot-lo.patch
Patch0004: 0004-OvmfPkg-increase-max-debug-message-length-to-512-RHE.patch
Patch0005: 0005-OvmfPkg-QemuVideoDxe-enable-debug-messages-in-VbeShi.patch
Patch0006: 0006-MdeModulePkg-TerminalDxe-add-other-text-resolutions-.patch
Patch0007: 0007-MdeModulePkg-TerminalDxe-set-xterm-resolution-on-mod.patch
Patch0008: 0008-OvmfPkg-take-PcdResizeXterm-from-the-QEMU-command-li.patch
Patch0009: 0009-ArmVirtPkg-QemuFwCfgLib-allow-UEFI_DRIVER-client-mod.patch
Patch0010: 0010-ArmVirtPkg-take-PcdResizeXterm-from-the-QEMU-command.patch
Patch0011: 0011-OvmfPkg-allow-exclusion-of-the-shell-from-the-firmwa.patch
Patch0012: 0012-OvmfPkg-EnrollDefaultKeys-application-for-enrolling-.patch
Patch0013: 0013-ArmPlatformPkg-introduce-fixed-PCD-for-early-hello-m.patch
Patch0014: 0014-ArmPlatformPkg-PrePeiCore-write-early-hello-message-.patch
Patch0015: 0015-ArmVirtPkg-set-early-hello-message-RH-only.patch
Patch0017: 0017-OvmfPkg-enable-DEBUG_VERBOSE-RHEL-only.patch
Patch0018: 0018-OvmfPkg-silence-EFI_D_VERBOSE-0x00400000-in-QemuVide.patch
Patch0019: 0019-OvmfPkg-silence-EFI_D_VERBOSE-0x00400000-in-NvmExpre.patch
Patch20: ovmf-OvmfPkg-PlatformBootManagerLib-connect-consoles-unco.patch
Patch21: ovmf-ArmVirtPkg-PlatformBootManagerLib-connect-Virtio-RNG.patch
Patch22: ovmf-OvmfPkg-PlatformBootManagerLib-connect-Virtio-RNG-de.patch


# python2-devel and libuuid-devel are required for building tools
BuildRequires:  python2-devel
BuildRequires:  libuuid-devel
BuildRequires:  /usr/bin/iasl
BuildRequires:  binutils gcc git

%ifarch x86_64
%global subpkgname OVMF

# Only OVMF includes 80x86 assembly files (*.nasm*).
BuildRequires:  nasm

# Only OVMF includes the Secure Boot feature, for which we need to separate out
# the UEFI shell.
BuildRequires:  dosfstools
BuildRequires:  mtools
BuildRequires:  genisoimage

# For generating the variable store template with the default certificates
# enrolled, we need qemu-kvm (from base RHEL7) such that it includes basic OVMF
# support (split pflash) -- see RHBZ#1032346.
BuildRequires:  qemu-kvm >= 1.5.3-44

# For verifying SB enablement in the above variable store template, we need a
# trusted guest kernel that prints "Secure boot enabled". See RHBZ#903815.
BuildRequires: kernel >= 3.10.0-52
BuildRequires: rpmdevtools

%package -n OVMF
Summary:    UEFI firmware for x86_64 virtual machines
BuildArch:  noarch

# OVMF includes the Secure Boot feature; it has a builtin OpenSSL library.
Provides:   bundled(openssl) = 1.1.0h
License:    BSD and OpenSSL

# URL taken from the Maintainers.txt file.
URL:        http://www.tianocore.org/ovmf/

%description -n OVMF
OVMF (Open Virtual Machine Firmware) is a project to enable UEFI support for
Virtual Machines. This package contains a sample 64-bit UEFI firmware for QEMU
and KVM.

%else
%global subpkgname AAVMF

%package -n AAVMF
Summary:    UEFI firmware for aarch64 virtual machines
BuildArch:  noarch

# No Secure Boot for AAVMF yet -- no builtin OpenSSL library.
License:    BSD

# URL taken from the Maintainers.txt file.
URL:        https://github.com/tianocore/tianocore.github.io/wiki/ArmVirtPkg

%description -n AAVMF
AAVMF (ARM Architecture Virtual Machine Firmware) is an EFI Development Kit II
platform that enables UEFI support for QEMU/KVM ARM Virtual Machines. This
package contains a 64-bit build.
%endif

%description
EDK II is a modern, feature-rich, cross-platform firmware development
environment for the UEFI and PI specifications. This package contains sample
64-bit UEFI firmware builds for QEMU and KVM.

%prep
%setup -q -n ovmf-%{GITCOMMIT}

# Ensure old shell and binary packages are not used
rm -rf EdkShellBinPkg
rm -rf EdkShellPkg
rm -rf FatBinPkg
rm -rf ShellBinPkg

%{lua:
    tmp = os.tmpname();
    f = io.open(tmp, "w+");
    count = 0;
    for i, p in ipairs(patches) do
        f:write(p.."\n");
        count = count + 1;
    end;
    f:close();
    print("PATCHCOUNT="..count.."\n")
    print("PATCHLIST="..tmp.."\n")
}

git init -q
git config user.name rpm-build
git config user.email rpm-build
git config core.whitespace cr-at-eol
git config am.keepcr true
git add -A .
git commit -q -a --author 'rpm-build <rpm-build>' \
           -m '%{name}-%{GITCOMMIT} base'

COUNT=$(grep '\.patch$' $PATCHLIST | wc -l)
if [ $COUNT -ne $PATCHCOUNT ]; then
    echo "Found $COUNT patches in $PATCHLIST, expected $PATCHCOUNT"
    exit 1
fi
if [ $COUNT -gt 0 ]; then
    for pf in `cat $PATCHLIST`; do
      git am $pf
    done
fi
echo "Applied $COUNT patches"
rm -f $PATCHLIST

cp -a -- %{SOURCE1} %{SOURCE3} .
tar -C CryptoPkg/Library/OpensslLib -a -f %{SOURCE2} -x

# Done by %setup, but we do not use it for the auxiliary tarballs
chmod -Rf a+rX,u+w,g-w,o-w .

%build
source ./edksetup.sh
make -C "$EDK_TOOLS_PATH"

SMP_MFLAGS="%{?_smp_mflags}"
if [[ x"$SMP_MFLAGS" = x-j* ]]; then
        CC_FLAGS="$CC_FLAGS -n ${SMP_MFLAGS#-j}"
elif [ -n "%{?jobs}" ]; then
        CC_FLAGS="$CC_FLAGS -n %{?jobs}"
fi

CC_FLAGS="$CC_FLAGS --cmd-len=65536 -t GCC48 -b DEBUG --hash"

%ifarch x86_64
# Build with SB but without SMM; include UEFI shell.
build ${CC_FLAGS} -D FD_SIZE_4MB -a X64 -p OvmfPkg/OvmfPkgX64.dsc \
  -D SECURE_BOOT_ENABLE

# Build with SB and SMM; exclude UEFI shell.
build -D SECURE_BOOT_ENABLE -D EXCLUDE_SHELL_FROM_FD ${CC_FLAGS} \
  -a IA32 -a X64 -p OvmfPkg/OvmfPkgIa32X64.dsc -D SMM_REQUIRE \
  -D FD_SIZE_4MB

# Sanity check: the varstore templates must be identical.
cmp Build/OvmfX64/DEBUG_GCC4?/FV/OVMF_VARS.fd \
  Build/Ovmf3264/DEBUG_GCC4?/FV/OVMF_VARS.fd

# Prepare an ISO image that boots the UEFI shell.
(
  UEFI_SHELL_BINARY=Build/Ovmf3264/DEBUG_GCC48/X64/Shell.efi
  ENROLLER_BINARY=Build/Ovmf3264/DEBUG_GCC48/X64/EnrollDefaultKeys.efi
  UEFI_SHELL_IMAGE=uefi_shell.img
  ISO_IMAGE=UefiShell.iso

  UEFI_SHELL_BINARY_BNAME=$(basename -- "$UEFI_SHELL_BINARY")
  UEFI_SHELL_SIZE=$(stat --format=%s -- "$UEFI_SHELL_BINARY")
  ENROLLER_SIZE=$(stat --format=%s -- "$ENROLLER_BINARY")

  # add 1MB then 10% for metadata
  UEFI_SHELL_IMAGE_KB=$((
    (UEFI_SHELL_SIZE + ENROLLER_SIZE + 1 * 1024 * 1024) * 11 / 10 / 1024
  ))

  # create non-partitioned FAT image
  rm -f -- "$UEFI_SHELL_IMAGE"
  mkdosfs -C "$UEFI_SHELL_IMAGE" -n UEFI_SHELL -- "$UEFI_SHELL_IMAGE_KB"

  # copy the shell binary into the FAT image
  export MTOOLS_SKIP_CHECK=1
  mmd   -i "$UEFI_SHELL_IMAGE"                       ::efi
  mmd   -i "$UEFI_SHELL_IMAGE"                       ::efi/boot
  mcopy -i "$UEFI_SHELL_IMAGE"  "$UEFI_SHELL_BINARY" ::efi/boot/bootx64.efi
  mcopy -i "$UEFI_SHELL_IMAGE"  "$ENROLLER_BINARY"   ::
  mdir  -i "$UEFI_SHELL_IMAGE"  -/                   ::

  # build ISO with FAT image file as El Torito EFI boot image
  genisoimage -input-charset ASCII -J -rational-rock \
    -efi-boot "$UEFI_SHELL_IMAGE" -no-emul-boot \
    -o "$ISO_IMAGE" -- "$UEFI_SHELL_IMAGE"
)

# Enroll the default certificates in a separate variable store template. Base
# RHEL7 qemu-kvm does not emulate SMM, but we don't need SMM for the enrollment
# here.
./ovmf-vars-generator --verbose --verbose \
  --qemu-binary        /usr/libexec/qemu-kvm \
  --ovmf-binary        Build/OvmfX64/DEBUG_GCC4?/FV/OVMF_CODE.fd \
  --ovmf-template-vars Build/OvmfX64/DEBUG_GCC4?/FV/OVMF_VARS.fd \
  --uefi-shell-iso     UefiShell.iso \
  --skip-testing \
  --disable-smm \
  OVMF_VARS.secboot.fd

%else
# Build with a verbose debug mask first, and stash the binary.
build ${CC_FLAGS} -a AARCH64 \
  -p ArmVirtPkg/ArmVirtQemu.dsc \
  -D DEBUG_PRINT_ERROR_LEVEL=0x8040004F
cp -a Build/ArmVirtQemu-AARCH64/DEBUG_GCC48/FV/QEMU_EFI.fd \
  QEMU_EFI.verbose.fd

# Rebuild with a silent (errors only) debug mask.
build ${CC_FLAGS} -a AARCH64 \
  -p ArmVirtPkg/ArmVirtQemu.dsc \
  -D DEBUG_PRINT_ERROR_LEVEL=0x80000000
%endif

%install

copy_license() {
    install -m 0644 $1 $RPM_BUILD_ROOT%{_docdir}/%{subpkgname}/Licenses/$2-License.txt
}

mkdir -p $RPM_BUILD_ROOT%{_docdir}/%{subpkgname}/Licenses
copy_license License.txt edk2
copy_license OvmfPkg/License.txt OvmfPkg

%ifarch x86_64
mkdir -p $RPM_BUILD_ROOT%{_datadir}/OVMF

# We don't ship the SB-ful, SMM-less binary.
%if 0
install -m 0644 Build/OvmfX64/DEBUG_GCC4?/FV/OVMF_CODE.fd  $RPM_BUILD_ROOT%{_datadir}/OVMF/OVMF_CODE.fd
%endif
install -m 0644 Build/Ovmf3264/DEBUG_GCC4?/FV/OVMF_CODE.fd $RPM_BUILD_ROOT%{_datadir}/OVMF/OVMF_CODE.secboot.fd

install -m 0644 Build/OvmfX64/DEBUG_GCC4?/FV/OVMF_VARS.fd $RPM_BUILD_ROOT%{_datadir}/OVMF/OVMF_VARS.fd
install -m 0644 OVMF_VARS.secboot.fd                      $RPM_BUILD_ROOT%{_datadir}/OVMF/OVMF_VARS.secboot.fd
install -m 0644 UefiShell.iso                             $RPM_BUILD_ROOT%{_datadir}/OVMF/UefiShell.iso
install -m 0644 OvmfPkg/README                            $RPM_BUILD_ROOT%{_docdir}/%{subpkgname}/README
install -m 0644 ovmf-whitepaper-c770f8c.txt               $RPM_BUILD_ROOT%{_docdir}/%{subpkgname}/ovmf-whitepaper-c770f8c.txt

copy_license CryptoPkg/Library/OpensslLib/openssl/LICENSE OpensslLib

%else
mkdir -p $RPM_BUILD_ROOT%{_datadir}/AAVMF

# Pad and install the verbose binary.
cat QEMU_EFI.verbose.fd \
  /dev/zero \
| head -c 64m \
  > $RPM_BUILD_ROOT%{_datadir}/AAVMF/AAVMF_CODE.verbose.fd

# Pad and install the silent (default) binary.
cat Build/ArmVirtQemu-AARCH64/DEBUG_GCC48/FV/QEMU_EFI.fd \
  /dev/zero \
| head -c 64m \
  > $RPM_BUILD_ROOT%{_datadir}/AAVMF/AAVMF_CODE.fd

# Create varstore template.
cat Build/ArmVirtQemu-AARCH64/DEBUG_GCC48/FV/QEMU_VARS.fd \
  /dev/zero \
| head -c 64m \
  > $RPM_BUILD_ROOT%{_datadir}/AAVMF/AAVMF_VARS.fd

chmod 0644 -- $RPM_BUILD_ROOT%{_datadir}/AAVMF/AAVMF_*.fd
%endif

%ifarch x86_64
%files -n OVMF
%else
%files -n AAVMF
%endif

%defattr(-,root,root,-)
%dir %{_docdir}/%{subpkgname}/Licenses
%doc %{_docdir}/%{subpkgname}/Licenses/edk2-License.txt
%doc %{_docdir}/%{subpkgname}/Licenses/OvmfPkg-License.txt

%ifarch x86_64
%doc %{_docdir}/%{subpkgname}/Licenses/OpensslLib-License.txt
%doc %{_docdir}/%{subpkgname}/README
%doc %{_docdir}/%{subpkgname}/ovmf-whitepaper-c770f8c.txt
%dir %{_datadir}/OVMF/
%if 0
%{_datadir}/OVMF/OVMF_CODE.fd
%endif
%{_datadir}/OVMF/OVMF_CODE.secboot.fd
%{_datadir}/OVMF/OVMF_VARS.fd
%{_datadir}/OVMF/OVMF_VARS.secboot.fd
%{_datadir}/OVMF/UefiShell.iso

%else
%dir %{_datadir}/AAVMF/
%{_datadir}/AAVMF/AAVMF_CODE.verbose.fd
%{_datadir}/AAVMF/AAVMF_CODE.fd
%{_datadir}/AAVMF/AAVMF_VARS.fd
%endif

%check

%ifarch x86_64
# Of the installed host kernels, boot the one with the highest Version-Release
# under OVMF, and check if it prints "Secure boot enabled".
KERNEL_PKG=$(rpm -q kernel | rpmdev-sort | tail -n 1)
KERNEL_IMG=$(rpm -q -l $KERNEL_PKG | grep '^/boot/vmlinuz-')

./ovmf-vars-generator --verbose --verbose \
  --qemu-binary        /usr/libexec/qemu-kvm \
  --ovmf-binary        Build/OvmfX64/DEBUG_GCC4?/FV/OVMF_CODE.fd \
  --ovmf-template-vars Build/OvmfX64/DEBUG_GCC4?/FV/OVMF_VARS.fd \
  --uefi-shell-iso     UefiShell.iso \
  --kernel-path        $KERNEL_IMG \
  --skip-enrollment \
  --no-download \
  --disable-smm \
  OVMF_VARS.secboot.fd

%else
true

%endif

%changelog
* Fri Jul 27 2018 Miroslav Rezanina <mrezanin@redhat.com> - 20180508-3.gitee3198e672e2.el7
- ovmf-redhat-provide-virtual-bundled-OpenSSL-in-OVMF.patch [bz#1607792]
- Resolves: bz#1607792
  (add 'Provides: bundled(openssl) = 1.1.0h' to the spec file)

* Fri Jun 08 2018 Miroslav Rezanina <mrezanin@redhat.com> - 20180508-2.gitee3198e672e2
- OvmfPkg/PlatformBootManagerLib: connect consoles unconditionally [bz#1577546]
- build OVMF varstore template with SB enabled / certs enrolled [bz#1561128]
- connect Virtio RNG devices again [bz#1579518]
- Resolves: bz#1577546
  (no input consoles connected under certain circumstances)
- Resolves: bz#1561128
  (OVMF Secure boot enablement (enrollment of default keys))
- Resolves: bz#1579518
  (EFI_RNG_PROTOCOL no longer produced for virtio-rng)

* Thu May 10 2018 Miroslav Rezanina <mrezanin@redhat.com> - 20180508-1.gitee3198e672e2
- Rebase to [bz#1559542]
- Resolves: bz#1559542
  (Rebase OVMF for RHEL-7.6)

* Wed Dec 06 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20171011-4.git92d07e48907f.el7
- ovmf-MdeModulePkg-Core-Dxe-log-informative-memprotect-msg.patch [bz#1520485]
- ovmf-MdeModulePkg-BdsDxe-fall-back-to-a-Boot-Manager-Menu.patch [bz#1515418]
- Resolves: bz#1515418
  (RFE: Provide diagnostics for failed boot)
- Resolves: bz#1520485
  (AAVMF: two new messages with silent build)

* Fri Dec 01 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20171011-3.git92d07e48907f.el7
- ovmf-UefiCpuPkg-CpuDxe-Fix-multiple-entries-of-RT_CODE-in.patch [bz#1518308]
- ovmf-MdeModulePkg-DxeCore-Filter-out-all-paging-capabilit.patch [bz#1518308]
- ovmf-MdeModulePkg-Core-Merge-memory-map-after-filtering-p.patch [bz#1518308]
- Resolves: bz#1518308
  (UEFI memory map regression (runtime code entry splitting) introduced by c1cab54ce57c)

* Mon Nov 27 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20171011-2.git92d07e48907f.el7
- ovmf-MdeModulePkg-Bds-Remove-assertion-in-BmCharToUint.patch [bz#1513632]
- ovmf-MdeModulePkg-Bds-Check-variable-name-even-if-OptionN.patch [bz#1513632]
- ovmf-MdeModulePkg-PciBus-Fix-bug-that-PCI-BUS-claims-too-.patch [bz#1514105]
- ovmf-OvmfPkg-make-it-a-proper-BASE-library.patch [bz#1488247]
- ovmf-OvmfPkg-create-a-separate-PlatformDebugLibIoPort-ins.patch [bz#1488247]
- ovmf-OvmfPkg-save-on-I-O-port-accesses-when-the-debug-por.patch [bz#1488247]
- ovmf-OvmfPkg-enable-DEBUG_VERBOSE-RHEL-only.patch [bz#1488247]
- ovmf-OvmfPkg-silence-EFI_D_VERBOSE-0x00400000-in-QemuVide.patch [bz#1488247]
- ovmf-OvmfPkg-silence-EFI_D_VERBOSE-0x00400000-in-NvmExpre.patch [bz#1488247]
- ovmf-Revert-redhat-introduce-separate-silent-and-verbose-.patch [bz#1488247]
- Resolves: bz#1488247
  (make debug logging no-op unless a debug console is active)
- Resolves: bz#1513632
  ([RHEL-ALT 7.5] AAVMF fails to boot after setting BootNext)
- Resolves: bz#1514105
  (backport edk2 commit 6e3287442774 so that PciBusDxe not over-claim resources)

* Wed Oct 18 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20171011-1.git92d07e48907f.el7
- Rebase to 92d07e48907f [bz#1469787]
- Resolves: bz#1469787
  ((ovmf-rebase-rhel-7.5) Rebase OVMF for RHEL-7.5)
- Resolves: bz#1434740
  (OvmfPkg/PciHotPlugInitDxe: don't reserve IO space when IO support is disabled)
- Resolves: bz#1434747
  ([Q35] code12 error when hotplug x710 device in win2016)
- Resolves: bz#1447027
  (Guest cannot boot with 240 or above vcpus when using ovmf)
- Resolves: bz#1458192
  ([Q35] recognize "usb-storage" devices in XHCI ports)
- Resolves: bz#1468526
  (>1TB RAM support)
- Resolves: bz#1488247
  (provide "OVMF_CODE.secboot.verbose.fd" for log capturing; silence "OVMF_CODE.secboot.fd")
- Resolves: bz#1496170
  (Inconsistent MOR control variables exposed by OVMF, breaks Windows Device Guard)

* Fri May 12 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20170228-5.gitc325e41585e3.el7
- ovmf-OvmfPkg-EnrollDefaultKeys-update-SignatureOwner-GUID.patch [bz#1443351]
- ovmf-OvmfPkg-EnrollDefaultKeys-expose-CertType-parameter-.patch [bz#1443351]
- ovmf-OvmfPkg-EnrollDefaultKeys-blacklist-empty-file-in-db.patch [bz#1443351]
- ovmf-OvmfPkg-introduce-the-FD_SIZE_IN_KB-macro-build-flag.patch [bz#1443351]
- ovmf-OvmfPkg-OvmfPkg.fdf.inc-extract-VARS_LIVE_SIZE-and-V.patch [bz#1443351]
- ovmf-OvmfPkg-introduce-4MB-flash-image-mainly-for-Windows.patch [bz#1443351]
- ovmf-OvmfPkg-raise-max-variable-size-auth-non-auth-to-33K.patch [bz#1443351]
- ovmf-OvmfPkg-PlatformPei-handle-non-power-of-two-spare-si.patch [bz#1443351]
- ovmf-redhat-update-local-build-instructions-with-D-FD_SIZ.patch [bz#1443351]
- ovmf-redhat-update-OVMF-build-commands-with-D-FD_SIZE_4MB.patch [bz#1443351]
- Resolves: bz#1443351
  ([svvp][ovmf] job "Secure Boot Logo Test" failed  with q35&ovmf)

* Fri Apr 28 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20170228-4.gitc325e41585e3.el7
- ovmf-ShellPkg-Shell-clean-up-bogus-member-types-in-SPLIT_.patch [bz#1442908]
- ovmf-ShellPkg-Shell-eliminate-double-free-in-RunSplitComm.patch [bz#1442908]
- Resolves: bz#1442908
  (Guest hang when running a wrong command in Uefishell)

* Tue Apr 04 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20170228-3.gitc325e41585e3.el7
- ovmf-ArmVirtPkg-FdtClientDxe-supplement-missing-EFIAPI-ca.patch [bz#1430262]
- ovmf-ArmVirtPkg-ArmVirtPL031FdtClientLib-unconditionally-.patch [bz#1430262]
- ovmf-MdeModulePkg-RamDiskDxe-fix-C-string-literal-catenat.patch [bz#1430262]
- ovmf-EmbeddedPkg-introduce-EDKII-Platform-Has-ACPI-GUID.patch [bz#1430262]
- ovmf-EmbeddedPkg-introduce-PlatformHasAcpiLib.patch [bz#1430262]
- ovmf-EmbeddedPkg-introduce-EDKII-Platform-Has-Device-Tree.patch [bz#1430262]
- ovmf-ArmVirtPkg-add-PlatformHasAcpiDtDxe.patch [bz#1430262]
- ovmf-ArmVirtPkg-enable-AcpiTableDxe-and-EFI_ACPI_TABLE_PR.patch [bz#1430262]
- ovmf-ArmVirtPkg-FdtClientDxe-install-DT-as-sysconfig-tabl.patch [bz#1430262]
- ovmf-ArmVirtPkg-PlatformHasAcpiDtDxe-don-t-expose-DT-if-Q.patch [bz#1430262]
- ovmf-ArmVirtPkg-remove-PURE_ACPI_BOOT_ENABLE-and-PcdPureA.patch [bz#1430262]
- Resolves: bz#1430262
  (AAVMF: forward QEMU's DT to the guest OS only if ACPI payload is unavailable)

* Mon Mar 27 2017 Miroslav Rezanina <mrezanin@redhat.com> - 20170228-2.gitc325e41585e3.el7
- ovmf-MdeModulePkg-Core-Dxe-downgrade-CodeSegmentCount-is-.patch [bz#1433428]
- Resolves: bz#1433428
  (AAVMF: Fix error message during ARM guest VM installation)

* Wed Mar 08 2017 Laszlo Ersek <lersek@redhat.com> - ovmf-20170228-1.gitc325e41585e3.el7
- Rebase to upstream c325e41585e3 [bz#1416919]
- Resolves: bz#1373812
  (guest boot from network even set 'boot order=1' for virtio disk with OVMF)
- Resolves: bz#1380282
  (Update OVMF to openssl-1.0.2k-hobbled)
- Resolves: bz#1412313
  (select broadcast SMI if available)
- Resolves: bz#1416919
  (Rebase OVMF for RHEL-7.4)
- Resolves: bz#1426330
  (disable libssl in CryptoPkg)

* Mon Sep 12 2016 Laszlo Ersek <lersek@redhat.com> - ovmf-20160608b-1.git988715a.el7
- rework downstream-only commit dde83a75b566 "setup the tree for the secure
  boot feature (RHEL only)", excluding patent-encumbered files from the
  upstream OpenSSL 1.0.2g tarball [bz#1374710]
- rework downstream-only commit dfc3ca1ee509 "CryptoPkg/OpensslLib: Upgrade
  OpenSSL version to 1.0.2h", excluding patent-encumbered files from the
  upstream OpenSSL 1.0.2h tarball [bz#1374710]

* Thu Aug 04 2016 Miroslav Rezanina <mrezanin@redhat.com> - OVMF-20160608-3.git988715a.el7
- ovmf-MdePkg-PCI-Add-missing-PCI-PCIE-definitions.patch [bz#1332408]
- ovmf-ArmPlatformPkg-NorFlashDxe-accept-both-non-secure-an.patch [bz#1353494]
- ovmf-ArmVirtPkg-ArmVirtQemu-switch-secure-boot-build-to-N.patch [bz#1353494]
- ovmf-ArmPlatformPkg-NorFlashAuthenticatedDxe-remove-this-.patch [bz#1353494]
- ovmf-ArmVirtPkg-add-FDF-definition-for-empty-varstore.patch [bz#1353494]
- ovmf-redhat-package-the-varstore-template-produced-by-the.patch [bz#1353494]
- ovmf-ArmVirtPkg-Re-add-the-Driver-Health-Manager.patch [bz#1353494]
- ovmf-ArmVirtPkg-HighMemDxe-allow-patchable-PCD-for-PcdSys.patch [bz#1353494]
- ovmf-ArmVirtPkg-ArmVirtQemuKernel-make-ACPI-support-AARCH.patch [bz#1353494]
- ovmf-ArmVirtPkg-align-ArmVirtQemuKernel-with-ArmVirtQemu.patch [bz#1353494]
- ovmf-ArmVirtPkg-ArmVirtQemu-factor-out-shared-FV.FvMain-d.patch [bz#1353494]
- ovmf-ArmVirtPkg-factor-out-Rules-FDF-section.patch [bz#1353494]
- ovmf-ArmVirtPkg-add-name-GUIDs-to-FvMain-instances.patch [bz#1353494]
- ovmf-OvmfPkg-add-a-Name-GUID-to-each-Firmware-Volume.patch [bz#1353494]
- ovmf-OvmfPkg-PlatformBootManagerLib-remove-stale-FvFile-b.patch [bz#1353494]
- ovmf-MdePkg-IndustryStandard-introduce-EFI_PCI_CAPABILITY.patch [bz#1332408]
- ovmf-MdeModulePkg-PciBusDxe-look-for-the-right-capability.patch [bz#1332408]
- ovmf-MdeModulePkg-PciBusDxe-recognize-hotplug-capable-PCI.patch [bz#1332408]
- ovmf-OvmfPkg-add-PciHotPlugInitDxe.patch [bz#1332408]
- ovmf-ArmPkg-ArmGicLib-manage-GICv3-SPI-state-at-the-distr.patch [bz#1356655]
- ovmf-ArmVirtPkg-PlatformBootManagerLib-remove-stale-FvFil.patch [bz#1353494]
- ovmf-OvmfPkg-EnrollDefaultKeys-assign-Status-before-readi.patch [bz#1356913]
- ovmf-OvmfPkg-EnrollDefaultKeys-silence-VS2015x86-warning-.patch [bz#1356913]
- ovmf-CryptoPkg-update-openssl-to-ignore-RVCT-3079.patch [bz#1356184]
- ovmf-CryptoPkg-Fix-typos-in-comments.patch [bz#1356184]
- ovmf-CryptoPkg-BaseCryptLib-Avoid-passing-NULL-ptr-to-fun.patch [bz#1356184]
- ovmf-CryptoPkg-BaseCryptLib-Init-the-content-of-struct-Ce.patch [bz#1356184]
- ovmf-CryptoPkg-OpensslLib-Upgrade-OpenSSL-version-to-1.0..patch [bz#1356184]
- Resolves: bz#1332408
  (Q35 machine can not hot-plug scsi controller under switch)
- Resolves: bz#1353494
  ([OVMF] "EFI Internal Shell" should be removed from "Boot Manager")
- Resolves: bz#1356184
  (refresh embedded OpenSSL to 1.0.2h)
- Resolves: bz#1356655
  (AAVMF: stop accessing unmapped gicv3 registers)
- Resolves: bz#1356913
  (fix use-without-initialization in EnrollDefaultKeys.efi)

* Tue Jul 12 2016 Miroslav Rezanina <mrezanin@redhat.com> - OVMF-20160608-2.git988715a.el7
- ovmf-ArmPkg-ArmGicV3Dxe-configure-all-interrupts-as-non-s.patch [bz#1349407]
- ovmf-ArmVirtPkg-PlatformBootManagerLib-Postpone-the-shell.patch [bz#1353689]
- Resolves: bz#1349407
  (AArch64: backport fix to run over gicv3 emulation)
- Resolves: bz#1353689
  (AAVMF: Drops to shell with uninitialized NVRAM file)

* Thu Jun 9 2016 Laszlo Ersek <lersek@redhat.com> - ovmf-20160608-1.git988715a.el7
- Resolves: bz#1341733
  (prevent SMM stack overflow in OVMF while enrolling certificates in "db")
- Resolves: bz#1257882
  (FEAT: support to boot from virtio 1.0 modern devices)
- Resolves: bz#1333238
  (Q35 machine can not boot up successfully with more than 3 virtio-scsi
  storage controller under switch)
- Resolves: bz#1330955
  (VM can not be booted up from hard disk successfully when with a passthrough
  USB stick)

* Thu May 19 2016 Laszlo Ersek <lersek@redhat.com> - ovmf-20160419-2.git90bb4c5.el7
- Submit scratch builds from the exploded tree again to
  supp-rhel-7.3-candidate, despite FatPkg being OSS at this point; see
  bz#1329559.

* Wed Apr 20 2016 Laszlo Ersek <lersek@redhat.com> - ovmf-20160419-1.git90bb4c5.el7
- FatPkg is under the 2-clause BSDL now; "ovmf" has become OSS
- upgrade to openssl-1.0.2g
- Resolves: bz#1323363
  (remove "-D SECURE_BOOT_ENABLE" from AAVMF)
- Resolves: bz#1257882
  (FEAT: support to boot from virtio 1.0 modern devices)
- Resolves: bz#1308678
  (clearly separate SB-less, SMM-less OVMF binary from SB+SMM OVMF binary)

* Fri Feb 19 2016 Miroslav Rezanina <mrezanin@redhat.com> - OVMF-20160202-2.gitd7c0dfa.el7
- ovmf-restore-TianoCore-splash-logo-without-OpenSSL-advert.patch [bz#1308678]
- ovmf-OvmfPkg-ArmVirtPkg-show-OpenSSL-less-logo-without-Se.patch [bz#1308678]
- ovmf-OvmfPkg-simplify-VARIABLE_STORE_HEADER-generation.patch [bz#1308678]
- ovmf-redhat-bring-back-OVMF_CODE.fd-but-without-SB-and-wi.patch [bz#1308678]
- ovmf-redhat-rename-OVMF_CODE.smm.fd-to-OVMF_CODE.secboot..patch [bz#1308678]

* Tue Feb 2 2016 Laszlo Ersek <lersek@redhat.com> - ovmf-20160202-1.gitd7c0dfa.el7
- rebase to upstream d7c0dfa
- update OpenSSL to 1.0.2e (upstream)
- update FatPkg to SVN r97 (upstream)
- drive NVMe devices (upstream)
- resize xterm on serial console mode change, when requested with
  -fw_cfg name=opt/(ovmf|aavmf)/PcdResizeXterm,string=y
  (downstream)
- Resolves: bz#1259395
  (revert / roll back AAVMF fix for BZ 1188054)
- Resolves: bz#1202819
  (OVMF: secure boot limitations)
- Resolves: bz#1182495
  (OVMF rejects iPXE oprom when Secure Boot is enabled)

* Thu Nov 5 2015 Laszlo Ersek <lersek@redhat.com> - ovmf-20151104-1.gitb9ffeab.el7
- rebase to upstream b9ffeab
- Resolves: bz#1207554
  ([AAVMF] AArch64: populate SMBIOS)
- Resolves: bz#1270279
  (AAVMF: output improvements)

* Thu Jun 25 2015 Miroslav Rezanina <mrezanin@redhat.com> - OVMF-20150414-2.gitc9e5618.el7
- ovmf-OvmfPkg-PlatformPei-set-SMBIOS-entry-point-version-d.patch [bz#1232876]
- Resolves: bz#1232876
  (OVMF should install a version 2.8 SMBIOS entry point)

* Sat Apr 18 2015 Laszlo Ersek <lersek@redhat.com> - 20150414-1.gitc9e5618.el7
- rebase from upstream 9ece15a to c9e5618
- adapt .gitignore files
- update to openssl-0.9.8zf
- create Logo-OpenSSL.bmp rather than modifying Logo.bmp in-place
- update to FatPkg SVN r93 (git 8ff136aa)
- drop the following downstream-only patches (obviated by upstream
  counterparts):
  "tools_def.template: use forward slash with --add-gnu-debuglink (RHEL only)"
  "tools_def.template: take GCC48 prefixes from environment (RHEL only)"
  "OvmfPkg: set video resolution of text setup to 640x480 (RHEL only)"
  "OvmfPkg: resolve OrderedCollectionLib with base red-black tree instance"
  "OvmfPkg: AcpiPlatformDxe: actualize QemuLoader.h comments"
  "OvmfPkg: AcpiPlatformDxe: remove current ACPI table loader"
  "OvmfPkg: AcpiPlatformDxe: implement QEMU's full ACPI table loader interface"
  "OvmfPkg: QemuVideoDxe: fix querying of QXL's drawable buffer size"
  "OvmfPkg: disable stale fork of SecureBootConfigDxe"
  "OvmfPkg: SecureBootConfigDxe: remove stale fork"
  "Try to read key strike even when ..."
  "OvmfPkg: BDS: remove dead call to PlatformBdsEnterFrontPage()"
  "OvmfPkg: BDS: drop useless return statement"
  "OvmfPkg: BDS: don't overwrite the BDS Front Page timeout"
  "OvmfPkg: BDS: optimize second argument in PlatformBdsEnterFrontPage() call"
  'OvmfPkg: BDS: drop superfluous "connect first boot option" logic'
  "OvmfPkg: BDS: drop custom boot timeout, revert to IntelFrameworkModulePkg's"
  "Add comments to clarify mPubKeyStore buffer MemCopy. ..."
  "MdeModulePkg/SecurityPkg Variable: Add boundary check..."
  "OvmfPkg: AcpiPlatformDxe: make dependency on PCI enumeration explicit"
  "MdePkg: UefiScsiLib: do not encode LUN in CDB for READ and WRITE"
  "MdePkg: UefiScsiLib: do not encode LUN in CDB for other SCSI commands"
- merge downstream AAVMF patch "adapt packaging to Arm64", which forces us to
  rename the main package from "OVMF" to "ovmf"
- drop the following ARM BDS specific tweaks (we'll only build the Intel BDS):
  "ArmPlatformPkg/Bds: generate ESP Image boot option if user pref is unset
   (Acadia)"
  "ArmPlatformPkg/Bds: check for other defaults too if user pref is unset
   (Acadia)"
  "ArmPlatformPkg/ArmVirtualizationPkg: auto-detect boot path (Acadia)"
  "ArmPlatformPkg/Bds: initialize ConIn/ConOut/ErrOut before connecting
   terminals"
  "ArmPlatformPkg/Bds: let FindCandidate() search all filesystems"
  "ArmPlatformPkg/Bds: FindCandidateOnHandle(): log full device path"
  "ArmPlatformPkg/Bds: fall back to Boot Menu when no default option was found"
  "ArmPlatformPkg/Bds: always connect drivers before looking at boot options"
- drop patch "ArmPlatformPkg/ArmVirtualizationPkg: enable DEBUG_VERBOSE (Acadia
  only)", obsoleted by fixed bug 1197141
- tweak patch "write up build instructions (for interactive, local development)
  (RHELSA)". The defaults in "BaseTools/Conf/target.template", ie.
  ACTIVE_PLATFORM and TARGET_ARCH, are set for OVMF / X64. The AAVMF build
  instructions now spell out the necessary override options (-p and -a,
  respectively).
- extend patch "build FAT driver from source (RHELSA)" to the Xen build as well
  (only for consistency; we don't build for Xen).
- drop the following downstream-only AAVMF patches, due to the 77d5dac ->
  c9e5618 AAVMF rebase & join:
  "redhat/process-rh-specific.sh: fix check for hunk-less filtered patches"
  "redhat/process-rh-specific.sh: suppress missing files in final 'rm'"
  "ArmVirtualizationQemu: build UEFI shell from source (Acadia only)"
  "MdePkg: UefiScsiLib: do not encode LUN in CDB for READ and WRITE"
  "MdePkg: UefiScsiLib: do not encode LUN in CDB for other SCSI commands"
  "ArmVirtualizationPkg: work around cache incoherence on KVM affecting DTB"
  "Changed build target to supp-rhel-7.1-candidate"
  "ArmVirtualizationPkg: VirtFdtDxe: forward FwCfg addresses from DTB to PCDs"
  "ArmVirtualizationPkg: introduce QemuFwCfgLib instance for DXE drivers"
  "ArmVirtualizationPkg: clone PlatformIntelBdsLib from ArmPlatformPkg"
  "ArmVirtualizationPkg: PlatformIntelBdsLib: add basic policy"
  "OvmfPkg: extract QemuBootOrderLib"
  "OvmfPkg: QemuBootOrderLib: featurize PCI-like device path translation"
  "OvmfPkg: introduce VIRTIO_MMIO_TRANSPORT_GUID"
  "ArmVirtualizationPkg: VirtFdtDxe: use dedicated VIRTIO_MMIO_TRANSPORT_GUID"
  "OvmfPkg: QemuBootOrderLib: widen ParseUnitAddressHexList() to UINT64"
  "OvmfPkg: QemuBootOrderLib: OFW-to-UEFI translation for virtio-mmio"
  "ArmVirtualizationPkg: PlatformIntelBdsLib: adhere to QEMU's boot order"
  "ArmVirtualizationPkg: identify "new shell" as builtin shell for Intel BDS"
  "ArmVirtualizationPkg: Intel BDS: load EFI-stubbed Linux kernel from fw_cfg"
  'Revert "ArmVirtualizationPkg: work around cache incoherence on KVM affecting
   DTB"'
  "OvmfPkg: QemuBootOrderLib: expose QEMU's "-boot menu=on[, splash-time=N]""
  "OvmfPkg: PlatformBdsLib: get front page timeout from QEMU"
  "ArmVirtualizationPkg: PlatformIntelBdsLib: get front page timeout from QEMU"
  "ArmPkg: ArmArchTimerLib: clean up comments"
  "ArmPkg: ArmArchTimerLib: use edk2-conformant (UINT64 * UINT32) / UINT32"
  "ArmPkg: ArmArchTimerLib: conditionally rebase to actual timer frequency"
  "ArmVirtualizationQemu: ask the hardware for the timer frequency"
  "ArmPkg: DebugPeCoffExtraActionLib: debugger commands are not errors"
  "ArmPlatformPkg: PEIM startup is not an error"
  "ArmVirtualizationPkg: PlatformIntelBdsLib: lack of QEMU kernel is no error"
  "ArmVirtualizationPkg: expose debug message bitmask on build command line"
- tweak patch "rebase to upstream 77d5dac (Acadia only)": update spec changelog
  only
- tweak patch "spec: build AAVMF with the Intel BDS driver (RHELSA only)":
  apply "-D INTEL_BDS" to manual build instructions in redhat/README too
- tweak patch "spec: build and install verbose and silent (default) AAVMF
  binaries": apply DEBUG_PRINT_ERROR_LEVEL setting to interactive build
  instructions in redhat/README too
- install OVMF whitepaper as part of the OVMF build's documentation
- Resolves: bz#1211337
  (merge AAVMF into OVMF)
- Resolves: bz#1206523
  ([AAVMF] fix missing cache maintenance)

* Fri Mar 06 2015 Miroslav Rezanina <mrezanin@redhat.com> - AAVMF-20141113-5.git77d5dac.el7_1
- aavmf-ArmPkg-DebugPeCoffExtraActionLib-debugger-commands-a.patch [bz#1197141]
- aavmf-ArmPlatformPkg-PEIM-startup-is-not-an-error.patch [bz#1197141]
- aavmf-ArmVirtualizationPkg-PlatformIntelBdsLib-lack-of-QEM.patch [bz#1197141]
- aavmf-ArmVirtualizationPkg-expose-debug-message-bitmask-on.patch [bz#1197141]
- aavmf-spec-build-and-install-verbose-and-silent-default-AA.patch [bz#1197141]
- Resolves: bz#1197141
  (create silent & verbose builds)

* Tue Feb 10 2015 Miroslav Rezanina <mrezanin@redhat.com> - AAVMF-20141113-4.git77d5dac.el7
- aavmf-ArmPkg-ArmArchTimerLib-clean-up-comments.patch [bz#1188247]
- aavmf-ArmPkg-ArmArchTimerLib-use-edk2-conformant-UINT64-UI.patch [bz#1188247]
- aavmf-ArmPkg-ArmArchTimerLib-conditionally-rebase-to-actua.patch [bz#1188247]
- aavmf-ArmVirtualizationQemu-ask-the-hardware-for-the-timer.patch [bz#1188247]
- aavmf-ArmPkg-TimerDxe-smack-down-spurious-timer-interrupt-.patch [bz#1188054]
- Resolves: bz#1188054
  (guest reboot (asked from within AAVMF) regressed in 3.19.0-0.rc5.58.aa7a host kernel)
- Resolves: bz#1188247
  (backport "fix gBS->Stall()" series)

* Mon Jan 19 2015 Miroslav Rezanina <mrezanin@redhat.com> - AAVMF-20141113-3.git77d5dac.el7
- aavmf-OvmfPkg-QemuBootOrderLib-expose-QEMU-s-boot-menu-on-.patch [bz#1172756]
- aavmf-OvmfPkg-PlatformBdsLib-get-front-page-timeout-from-Q.patch [bz#1172756]
- aavmf-ArmVirtualizationPkg-PlatformIntelBdsLib-get-front-p.patch [bz#1172756]
- Resolves: bz#1172756
  ([RFE]Expose boot-menu shortcut to domain via AAVMF)

* Wed Jan 14 2015 Miroslav Rezanina <mrezanin@redhat.com> - AAVMF-20141113-2.git77d5dac.el7
- aavmf-ArmVirtualizationPkg-VirtFdtDxe-forward-FwCfg-addres.patch [bz#1172749]
- aavmf-ArmVirtualizationPkg-introduce-QemuFwCfgLib-instance.patch [bz#1172749]
- aavmf-ArmVirtualizationPkg-clone-PlatformIntelBdsLib-from-.patch [bz#1172749]
- aavmf-ArmVirtualizationPkg-PlatformIntelBdsLib-add-basic-p.patch [bz#1172749]
- aavmf-OvmfPkg-extract-QemuBootOrderLib.patch [bz#1172749]
- aavmf-OvmfPkg-QemuBootOrderLib-featurize-PCI-like-device-p.patch [bz#1172749]
- aavmf-OvmfPkg-introduce-VIRTIO_MMIO_TRANSPORT_GUID.patch [bz#1172749]
- aavmf-ArmVirtualizationPkg-VirtFdtDxe-use-dedicated-VIRTIO.patch [bz#1172749]
- aavmf-OvmfPkg-QemuBootOrderLib-widen-ParseUnitAddressHexLi.patch [bz#1172749]
- aavmf-OvmfPkg-QemuBootOrderLib-OFW-to-UEFI-translation-for.patch [bz#1172749]
- aavmf-ArmVirtualizationPkg-PlatformIntelBdsLib-adhere-to-Q.patch [bz#1172749]
- aavmf-ArmVirtualizationPkg-identify-new-shell-as-builtin-s.patch [bz#1172749]
- aavmf-ArmVirtualizationPkg-Intel-BDS-load-EFI-stubbed-Linu.patch [bz#1172749]
- aavmf-spec-build-AAVMF-with-the-Intel-BDS-driver-RHELSA-on.patch [bz#1172749]
- aavmf-Revert-ArmVirtualizationPkg-work-around-cache-incohe.patch [bz#1172910]
- Resolves: bz#1172749
  (implement fw_cfg, boot order handling, and -kernel booting in ArmVirtualizationQemu)
- Resolves: bz#1172910
  (revert Acadia-only workaround (commit df7bca4e) once Acadia host kernel (KVM) is fixed)

* Fri Dec 05 2014 Miroslav Rezanina <mrezanin@redhat.com> - OVMF-20140822-7.git9ece15a.el7
- ovmf-MdePkg-UefiScsiLib-do-not-encode-LUN-in-CDB-for-READ.patch [bz#1166971]
- ovmf-MdePkg-UefiScsiLib-do-not-encode-LUN-in-CDB-for-othe.patch [bz#1166971]
- Resolves: bz#1166971
  (virtio-scsi disks and cd-roms with nonzero LUN are rejected with errors)

* Tue Nov 25 2014 Miroslav Rezanina <mrezanin@redhat.com> - OVMF-20140822-6.git9ece15a.el7
- ovmf-OvmfPkg-AcpiPlatformDxe-make-dependency-on-PCI-enume.patch [bz#1166027]
- Resolves: bz#1166027
  (backport "OvmfPkg: AcpiPlatformDxe: make dependency on PCI enumeration explicit")

* Tue Nov 18 2014 Miroslav Rezanina <mrezanin@redhat.com> - OVMF-20140822-4.git9ece15a.el7
- ovmf-Add-comments-to-clarify-mPubKeyStore-buffer-MemCopy.patch [bz#1162314]
- ovmf-MdeModulePkg-SecurityPkg-Variable-Add-boundary-check.patch [bz#1162314]
- Resolves: bz#1162314
 (EMBARGOED OVMF: uefi: INTEL-TA-201410-001 && INTEL-TA-201410-002 [rhel-7.1])

* Thu Nov 13 2014 Laszlo Ersek <lersek@redhat.com> - AAVMF-20141113-1.git77d5dac
- rebased to upstream 77d5dac
  <https://bugzilla.redhat.com/show_bug.cgi?id=1162314#c1>
- patch "ArmVirtualizationPkg: FdtPL011SerialPortLib: support UEFI_APPLICATION"
  is now upstream (SVN r16219, git edb5073)

* Thu Nov 13 2014 Miroslav Rezanina <mrezanin@redhat.com> - OVMF-20140822-3.git9ece15a.el7
- ovmf-Revert-OvmfPkg-set-video-resolution-of-text-setup-to.patch [bz#1153927]
- ovmf-Try-to-read-key-strike-even-when-the-TimeOuts-value-.patch [bz#1153927]
- ovmf-OvmfPkg-BDS-remove-dead-call-to-PlatformBdsEnterFron.patch [bz#1153927]
- ovmf-OvmfPkg-BDS-drop-useless-return-statement.patch [bz#1153927]
- ovmf-OvmfPkg-BDS-don-t-overwrite-the-BDS-Front-Page-timeo.patch [bz#1153927]
- ovmf-OvmfPkg-BDS-optimize-second-argument-in-PlatformBdsE.patch [bz#1153927]
- ovmf-OvmfPkg-BDS-drop-superfluous-connect-first-boot-opti.patch [bz#1153927]
- ovmf-OvmfPkg-BDS-drop-custom-boot-timeout-revert-to-Intel.patch [bz#1153927]
- ovmf-OvmfPkg-set-video-resolution-of-text-setup-to-640x48.patch [bz#1153927]
- Resolves: bz#1153927
  (set NEXTBOOT to uefi setting failed from Windows Recovery console)

* Tue Nov 11 2014 Miroslav Rezanina <mrezanin@redhat.com> - OVMF-20140822-2.git9ece15a
- ovmf-redhat-process-rh-specific.sh-suppress-missing-files.patch [bz#1145784]
- ovmf-Revert-RH-only-OvmfPkg-QemuVideoDxe-fix-querying-of-.patch [bz#1145784]
- ovmf-Revert-RH-only-OvmfPkg-AcpiPlatformDxe-implement-QEM.patch [bz#1145784]
- ovmf-Revert-RH-only-OvmfPkg-AcpiPlatformDxe-remove-curren.patch [bz#1145784]
- ovmf-Revert-RH-only-OvmfPkg-AcpiPlatformDxe-actualize-Qem.patch [bz#1145784]
- ovmf-Revert-RH-only-OvmfPkg-resolve-OrderedCollectionLib-.patch [bz#1145784]
- ovmf-OvmfPkg-QemuVideoDxe-work-around-misreported-QXL-fra.patch [bz#1145784]
- ovmf-OvmfPkg-resolve-OrderedCollectionLib-with-base-red-b.patch [bz#1145784]
- ovmf-OvmfPkg-AcpiPlatformDxe-actualize-QemuLoader.h-comme.patch [bz#1145784]
- ovmf-OvmfPkg-AcpiPlatformDxe-remove-current-ACPI-table-lo.patch [bz#1145784]
- ovmf-OvmfPkg-AcpiPlatformDxe-implement-QEMU-s-full-ACPI-t.patch [bz#1145784]
- ovmf-spec-build-small-bootable-ISO-with-standalone-UEFI-s.patch [bz#1147592]
- ovmf-OvmfPkg-allow-exclusion-of-the-shell-from-the-firmwa.patch [bz#1147592]
- ovmf-spec-exclude-the-UEFI-shell-from-the-SecureBoot-enab.patch [bz#1147592]
- ovmf-OvmfPkg-EnrollDefaultKeys-application-for-enrolling-.patch [bz#1148296]
- ovmf-spec-package-EnrollDefaultKeys.efi-on-UefiShell.iso-.patch [bz#1148296]
- ovmf-OvmfPkg-disable-stale-fork-of-SecureBootConfigDxe.patch [bz#1148294]
- ovmf-OvmfPkg-SecureBootConfigDxe-remove-stale-fork.patch [bz#1148294]
- Resolves: bz#1145784
  (OVMF sync with QXL and ACPI patches up to edk2 7a9612ce)
- Resolves: bz#1147592
  (the binary RPM should include a small ISO file with a directly bootable UEFI shell binary)
- Resolves: bz#1148294
  (drop OvmfPkg's stale fork of SecureBootConfigDxe)
- Resolves: bz#1148296
  (provide a non-interactive way to auto-enroll important SecureBoot certificates)

* Wed Oct 15 2014 Laszlo Ersek <lersek@redhat.com> - AAVMF-20141015-1.gitc373687
- ported packaging to aarch64 / AAVMF

* Fri Aug 22 2014 Laszlo Ersek <lersek@redhat.com> - 20140822-1.git9ece15a.el7
- rebase from upstream 3facc08 to 9ece15a
- update to openssl-0.9.8zb
- update to FatPkg SVN r86 (git 2355ea2c)
- the following patches of Paolo Bonzini have been merged in upstream; drop the
  downstream-only copies:
  7bc1421 edksetup.sh: Look for BuildEnv under EDK_TOOLS_PATH
  d549344 edksetup.sh: Ensure that WORKSPACE points to the top of an edk2
          checkout
  1c023eb BuildEnv: remove useless check before setting $WORKSPACE
- include the following patches that have been pending review on the upstream
  list for a long time:
  [PATCH 0/4] OvmfPkg: complete client for QEMU's ACPI loader interface
  http://thread.gmane.org/gmane.comp.bios.tianocore.devel/8369
  [PATCH] OvmfPkg: QemuVideoDxe: fix querying of QXL's drawable buffer size
  http://thread.gmane.org/gmane.comp.bios.tianocore.devel/8515
- nasm is a build-time dependency now because upstream BuildTools has started
  to call it directly

* Wed Jul 23 2014 Laszlo Ersek <lersek@redhat.com> - 20140723-1.git3facc08.el7
- rebase from upstream a618eaa to 3facc08
- update to openssl-0.9.8za
- drop downstream-only split varstore patch, rely on upstream's

* Tue Jun 24 2014 Miroslav Rezanina <mrezanin@redhat.com> - 20140619-1.gita618eaa.el7
- Initial version
