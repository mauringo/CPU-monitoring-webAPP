# Source-built nvtop and Qualcomm NPU support

Snap version 2.0.3 builds these upstream revisions in dependency order:

| Component | Source | Revision |
| --- | --- | --- |
| FastRPC | https://github.com/qualcomm/fastrpc | `d247519650fe5cb16de6c78edaa95bcc4be25073` |
| libqcnpuperf | https://github.com/qualcomm/libqcnpuperf | `34261de1e689d0e718205e4ba8aae82108fd7881` |
| nvtop | https://github.com/Syllo/nvtop | `55896ac28e40f033af70b7bfbd8bf79b31522d8d` |

The Qualcomm userspace libraries are built for ARM64. Other architectures build
nvtop without the Qualcomm NPU library. NVIDIA, AMD, Intel and MSM/Adreno GPU
backends are enabled. Device discovery uses the bundled libudev consistently. Backend availability still depends on host hardware.
The ARM64 build fails if pkg-config cannot find libqcnpuperf or nvtop's generated
build rules omit `extract_npuinfo_qualcomm.c`.

FastRPC is built with autotools. libqcnpuperf is built with CMake and its optional
sample CLI disabled. Its pkg-config paths are corrected for staged installation.
nvtop is compiled last, against those staged headers and libraries. The distro
nvtop package is no longer staged. Upstream license notices ship under
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
