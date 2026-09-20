# Monitoring code review

Scope: first-party Flask collectors, dashboard JavaScript, device discovery and
deployment files. Bundled games and third-party libraries were not audited.

## Findings addressed

- **High — Unauthenticated process termination.** `POST /processes/<pid>/terminate`
  accepted arbitrary PIDs while the service listened on all interfaces. Any
  reachable client could terminate processes allowed by the service account.
  It now defaults to disabled and requires a configured bearer token.
- **High — Hardware strings interpreted as HTML.** Network and disk rendering
  interpolated names, mountpoints and filesystem metadata into `innerHTML`.
  These values now receive HTML escaping. Accelerator cards use `textContent`.
- **Medium — RAM display was virtual address space.** Process rankings used VMS,
  which can vastly exceed resident RAM. They now use RSS and show MiB.
- **Medium — Unbounded device commands.** The inventory subprocess wrapper had
  no timeout or exit-code validation. It now checks success and times out after
  three seconds per command.

## Remaining issues and limits

- Read-only endpoints expose system/process information to reachable clients.
  Use trusted networks or an authenticated reverse proxy for deployment.
- Overview polling still invokes `lsblk` and `ifconfig` per request. Slow commands
  can outlast the client polling interval and tie up workers. The new accelerator
  collector shares samples, but the existing overview needs similar caching.
- Importing `app.py` changes the working directory, checks Snap permissions and
  starts a sampler thread. An application factory would remove these lifecycle
  side effects; tests isolate them.
- `Dockerfile` uses an old Python 3.9.1 image and legacy `python-pip`/`python-dev`
  packages. The container build needs a separate refresh and build verification.
- The existing `discover_npus()` inventory labels generic Linux accelerator
  devices as NPUs. The new visualization distinguishes unknown accelerators.
- NPU utilization requires vendor-specific telemetry. Discovery is not evidence
  of utilization support, and an unavailable sensor is not reported as zero.

This is a targeted review, not a full security audit or hardware certification.
