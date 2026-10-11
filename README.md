# SpatialWire 🎧🌌

> **PipeWire native 7.1 Virtual Surround & Binaural HRTF Convolver for Linux (Wayland & X11).**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%28Wayland%20%26%20X11%29-blue.svg)](https://kernel.org)
[![Audio](https://img.shields.io/badge/Audio-PipeWire%20Native%20RT-green.svg)](https://pipewire.org)
[![HRTF](https://img.shields.io/badge/HRTF-7.1%20HeSuVi%20%26%20OpenAL-orange.svg)](https://airvs.github.io/HeSuVi)
[![UI](https://img.shields.io/badge/UI-Libadwaita%20%2F%20GTK4-purple.svg)](https://gnome.pages.gitlab.gnome.org/libadwaita/)

![SpatialWire Libadwaita Interface](assets/spatialwire-ui.png)

**SpatialWire** brings authentic, zero-overhead 7.1 binaural surround sound and Head-Related Transfer Function (HRTF) spatialization to any Linux desktop. Powered directly by PipeWire's real-time filter-chain module, it eliminates the 50–100 ms audio latency and CPU drag of traditional user-space DSP hosts.

---

## ✨ Key Features

* **⚡ Quantum-Synced Real-Time DSP:** Convolves audio directly inside PipeWire's native real-time audio threads (`rt.prio = 88`, `nice = -11`). No heavy external JACK/Carla host process and minimal CPU overhead (`~1.3 ms` at 64/48000 quantum).
* **🌐 True 7.1 Spatial Surround:** Creates a virtual 8-channel sink (`effect_input.virtual-surround-7.1-hesuvi`) automatically recognized by games (Steam, Proton, Wine), media players (MPV, VLC), and browsers (Firefox, Chromium) as native 7.1 surround sound.
* **👂 16-Convolver Binaural Matrix:** Accurately routes Front Left, Front Right, Center, LFE Subwoofer, Rear Left, Rear Right, Side Left, and Side Right through individual acoustic impulse responses to your ears.
* **📁 HeSuVi & OpenAL HRIR Compatible:** Reads both 7-channel and 14-channel HeSuVi impulse response WAV files with automatic channel layout detection.
* **🎛️ Non-Destructive & Portable:** Automatically provisions its user systemd service (`pipewire-filter-chain.service`) on any Linux distribution and backs up any pre-existing `filter-chain.conf` before activation.
* **🎛️ Over-Ear Headphone & In-Ear Monitor (IEM) Target Modes:** Built-in PipeWire real-time biquad target compensation (`spatialwire mode iem` / `over-ear`) that eliminates the 2.85 kHz double ear-canal peak on IEMs, restores HATS torso/shoulder warmth (250 Hz), and smooths >9.5 kHz pinna comb-filtering.
* **⌨️ ClickClick Co-Existence:** Dispatches zero-downtime Unix signals (`SIGUSR1`) to `clickclickd` to keep mechanical switch acoustics synchronized across sink switches.
* **🎨 Modern Libadwaita Interface:** Asynchronous GTK4 settings panel featuring live engine status, Headphone vs. IEM selector, interactive preset switcher, one-click 3D directional positioning audio test, and a custom WAV file importer.
* **📦 100% Permissive FOSS Licensing:** Bundled exclusively with permissive **Apache-2.0** (University of York SADIE II), **MIT Media Lab** (KEMAR), and **LGPL-2.0+** (OpenAL Soft / CIAIR) acoustic measurements (strictly excluding copyleft `CC BY-SA` datasets).

---

## 📊 Comparison: SpatialWire vs. Other Solutions

| Feature | SpatialWire | EasyEffects / JamesDSP | Windows HeSuVi (EqualizerAPO) |
|---|---|---|---|
| **Processing Engine** | **PipeWire Native C Filter-Chain** | User-space PipeWire client | Windows Kernel Filter Driver |
| **Buffer Latency** | **Single PipeWire Quantum (~1.3–10.6 ms)** | 40 ms – 120 ms buffer delay | 5 ms – 15 ms |
| **CPU Overhead** | **< 0.5% (Realtime SPA Node)** | 4% – 12% (Full DSP suite) | < 1% |
| **Headphone vs. IEM Target** | **Native RT Biquad Stage (`over-ear` / `iem`)** | Manual parametric EQ setup | Manual Peace EQ setup |
| **Auto Sink Re-routing** | **Yes (pw-dump + wpctl + pw-link)** | Often breaks on Bluetooth/DAC disconnect | Requires manual default switch |
| **HeSuVi WAV Support** | **7-channel & 14-channel native** | Requires manual SOFA / mono splits | Native |
| **Modern Wayland UI** | **Libadwaita / GTK4** | GTK4 (Heavy suites) | Win32 (Legacy) |

---

## 🎛️ Bundled FOSS HRTF Profiles

SpatialWire includes curated, license-verified impulse response profiles out of the box:

| Profile ID | Ch | Acoustic Profile | Soundstage Characteristics | Upstream License |
|---|---|---|---|---|
| `hear` | 7ch | **MIT KEMAR Reference (1994)** | Diffuse-field equalized HATS reference with natural torso/shoulder warmth | **Free Use with Attribution** (MIT Media Lab) |
| `sadie_kemar` | 14ch | **SADIE II KEMAR HATS (2018)** | Modern 48 kHz Genelec 8010 HATS measurement with full torso & shoulders | **Apache-2.0** (University of York) |
| `sadie_kemar_room` | 14ch | **SADIE II KEMAR Studio Room** | KEMAR HATS + Acoustically Treated Studio Room BRIR (85 ms) — ideal for IEMs | **Apache-2.0** (University of York) |
| `sadie_ku100` | 14ch | **SADIE II Neumann KU 100** | Neumann KU 100 binaural studio head with torso-warmth & pinna smoothing | **Apache-2.0** (University of York) |
| `oal_dflt` | 7ch | **OpenAL Soft Standard** | Balanced cross-talk and pinpoint HRTF positioning | **LGPL-2.0+** |
| `oal+` | 14ch | **OpenAL Soft Wide** | Expanded horizontal separation with 150 ms studio room tail (`-27.4 dB`) | **LGPL-2.0+** |
| `oal++` | 14ch | **OpenAL Soft Extra Wide** | High-separation stage for competitive gaming (`150 ms`, `-26.9 dB`) | **LGPL-2.0+** |
| `oal+++` | 14ch | **OpenAL Soft Maximum** | Cinema soundstage with 250 ms room decay (`-24.5 dB`) | **LGPL-2.0+** |
| `oal_cia0` | 7ch | **OpenAL Soft CIA 0** | Close-field anechoic stage from CIAIR / OpenAL Soft dataset | **LGPL-2.0+ / Academic** |
| `oal_cia1` | 7ch | **OpenAL Soft CIA 1** | Diffuse field from CIAIR / OpenAL Soft dataset | **LGPL-2.0+ / Academic** |

*(For full licensing and attributions, see [AUDIO_LICENSES.md](AUDIO_LICENSES.md).)*

---

## 🚀 Installation

### 1. Prerequisites (PipeWire)
SpatialWire requires PipeWire with the filter-chain module enabled (standard on modern Linux distributions like NixOS, Fedora, Arch, Ubuntu 24.04+):

* `pipewire` (1.0+)
* `wireplumber` or `pipewire-media-session`
* `systemd` user service support

---

### 2. Nix / NixOS (Flakes)

Run directly without installing:
```bash
nix run github:saschlik/spatialwire
```

Or add it to your system flake:
```nix
inputs = {
  spatialwire.url = "github:saschlik/spatialwire";
};
```

---

### 3. Arch Linux, Fedora, Ubuntu & Other Distributions

#### Dependencies
* **Core:** `python3`, `pipewire`, `wireplumber`
* **UI:** `gtk4`, `libadwaita`, `python3-gobject`

#### Build & Install
```bash
git clone https://github.com/saschlik/spatialwire.git
cd spatialwire

# Install CLI tool, settings GUI, and bundled presets
sudo make install
```

---

## 🖥️ Usage

### Graphical Interface
Launch the modern control panel from your application launcher (search **SpatialWire**) or via terminal:
```bash
spatialwire gui
# or directly:
spatialwire-settings
```

### Command Line Interface
```bash
# Check current surround status & active soundcard
spatialwire status

# List all available HRTF profiles & channel configurations
spatialwire list

# Activate a profile (e.g. MIT KEMAR Reference or SADIE II KEMAR Studio Room)
spatialwire set hear
spatialwire set sadie_kemar_room

# Switch between Over-Ear Headphones and In-Ear Monitors (IEM) target compensation
spatialwire mode iem
spatialwire mode over-ear

# Activate OpenAL Soft Wide
spatialwire set oal+

# Disable surround and return to direct DAC stereo mode
spatialwire off

# Play 8-channel 3D spatial directional test
spatialwire test

# Import any custom HeSuVi 7/14-channel WAV impulse file
spatialwire import /path/to/custom_hrtf.wav
```

---

## 🏗️ Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                    Audio Application                         │
│           (Game / Steam Proton / MPV / Spotify)              │
└──────────────────────────────┬───────────────────────────────┘
                               │ Native 7.1 Surround (8 Channels)
                               ▼
┌──────────────────────────────────────────────────────────────┐
│               PipeWire Virtual Surround Sink                 │
│         (effect_input.virtual-surround-7.1-hesuvi)           │
└──────────────────────────────┬───────────────────────────────┘
                               │ 16-Convolver Real-Time Graph
                               ▼
┌──────────────────────────────────────────────────────────────┐
│             libpipewire-module-filter-chain                  │
│   FL  FR  FC  LFE  RL  RR  SL  SR  (SPA Realtime Convolver)  │
│   │   │   │    │   │   │   │   │                             │
│   └───┴───┴────┴───┴───┴───┴───┴───────► Stereo Mix (L / R)  │
│                                              │               │
│                  Optional IEM Biquad Stage ◄─┘               │
└──────────────────────────────┬───────────────────────────────┘
                               │ Low-latency PipeWire Stream
                               ▼
┌──────────────────────────────────────────────────────────────┐
│             Physical Hardware DAC / Soundcard                │
│             (USB-C DAC / PCIe / Analog / ALSA)               │
└──────────────────────────────────────────────────────────────┘
```

---

## 📜 License

* **Code:** Licensed under the [MIT License](LICENSE). Copyright © 2026 Sascha (Saschlik).
* **Audio Assets:** Licensed under Apache-2.0 (SADIE II / University of York) / LGPL-2.0+ (OpenAL Soft) / GPL-2.0+ (ALSA test voice) / MIT Media Lab Attribution. Copyleft `CC BY-SA` datasets (e.g. TH Köln) are strictly excluded. See [AUDIO_LICENSES.md](AUDIO_LICENSES.md) for details.

