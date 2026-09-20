# Source-built nvtop and Qualcomm NPU support

The ARM64 Snap builds these upstream revisions in dependency order:

| Component | Source | Revision |
| --- | --- | --- |
| FastRPC | https://github.com/qualcomm/fastrpc | `d247519650fe5cb16de6c78edaa95bcc4be25073` |
| libqcnpuperf | https://github.com/qualcomm/libqcnpuperf | `34261de1e689d0e718205e4ba8aae82108fd7881` |
| nvtop | https://github.com/Syllo/nvtop | `55896ac28e40f033af70b7bfbd8bf79b31522d8d` |

The Qualcomm userspace libraries and custom nvtop are built only for ARM64.
Other architectures use the distribution nvtop package. The custom ARM64 build
enables NVIDIA, AMD, Intel and MSM/Adreno GPU backends. Device discovery uses the bundled libudev consistently. Backend availability still depends on host hardware.
The ARM64 build fails if pkg-config cannot find libqcnpuperf or nvtop's generated
build rules omit `extract_npuinfo_qualcomm.c`.

FastRPC is built with autotools. libqcnpuperf is built with CMake and its optional
sample CLI disabled. Its pkg-config paths are corrected for staged installation.
nvtop is compiled last, against those staged headers and libraries. The distro
nvtop package is staged only on non-ARM64 architectures. Upstream license notices ship under
`usr/share/licenses` in the Snap.

Build in an isolated Ubuntu 26.04 environment:

```sh
snapcraft pack --use-lxd --platform arm64
```

The launcher puts the bundled nvtop first on PATH and makes the bundled
Qualcomm libraries and ncurses terminfo available to the embedded terminal.

## Host requirements and confinement

These are userspace components, not replacement kernel modules or DSP firmware.
The host must already provide its Qualcomm FastRPC kernel driver, accessible
`/dev/fastrpc-*` device nodes, and working DSP firmware. The Snap does not install
host udev rules or start FastRPC host daemons.

The `opengl` plug grants GPU device access; connect it alongside the hardware
observation interfaces when needed:

```sh
sudo snap connect cpu-monitoring-webapp:opengl
sudo snap connect cpu-monitoring-webapp:hardware-observe
sudo snap connect cpu-monitoring-webapp:system-observe
```

These interfaces do not automatically grant FastRPC device access. Strict
confinement on a Qualcomm board needs a device policy (for example a suitable
custom-device slot supplied by its gadget) that permits the board's FastRPC
nodes and any required firmware/configuration paths. Compiling the libraries
alone does not bypass this requirement. Missing permissions may leave the NPU
absent while GPU monitoring continues. The recipe retains strict confinement.

## Qualcomm NPU missing in strict mode

On the tested host, all declared GPU/hardware interfaces were already connected.
The kernel audit log recorded FastRPC accesses to `/dev/fastrpc-cdsp` (read/write)
and `/dev/fastrpc-cdsp-secure` (read) as policy violations allowed only because
the app was running in devmode. The host exposed no suitable custom-device or
DSP slot to connect. Adding another ordinary GPU observation permission would
not grant those device accesses. A board-specific device policy is needed for
strict-mode support; no host AppArmor profiles or device modes were modified.

If the NPU is visible in devmode but absent in strict mode, installing the local
package with devmode is a workaround on affected systems:

```sh
sudo snap install --dangerous --devmode ./cpu-monitoring-webapp_2.0.3_arm64.snap
```

Use the actual filename of your package. **Devmode disables Snap confinement**;
use it only for a trusted app when you accept the broader system access. It
does not supply missing firmware or kernel drivers. The GPU/NPU page includes
this notice next to the terminal. Rebuild/reinstall the Snap to include the
updated page, then reload it or reconnect the terminal.
