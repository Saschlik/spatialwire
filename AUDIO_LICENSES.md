# 🎧 SpatialWire — Audio Assets & Licensing

All bundled Head-Related Impulse Responses (HRIR) and testing assets included in **SpatialWire** are open acoustic datasets or open-source (LGPL-2.0+ / permissive academic attribution) measurements formatted as 7-channel or 14-channel HeSuVi impulse responses.

---

## 1. Summary Table

| Asset File | Preset Name | Measurement / Source | Upstream License | Attribution / Author |
|---|---|---|---|---|
| `presets/hear.wav` | MIT KEMAR Reference | MIT Media Lab KEMAR Dummy-Head HRTF (`MIT_KEMAR_normal_pinna.sofa`, Diffuse-Field Equalized 7-channel 48 kHz HeSuVi format) | **Free Use with Attribution** (MIT Media Lab) | Bill Gardner & Keith Martin (MIT Media Lab, 1994) |
| `presets/oal_dflt.wav` | OpenAL Soft Standard | OpenAL Soft Default HRIR (7-channel HeSuVi format) | **LGPL-2.0+** | Chris Robinson & OpenAL Soft Contributors |
| `presets/oal+.wav` | OpenAL Soft Wide | OpenAL Soft Extended Cross-Talk HRIR (14-channel) | **LGPL-2.0+** | Chris Robinson & OpenAL Soft Contributors |
| `presets/oal++.wav` | OpenAL Soft Extra Wide | OpenAL Soft High-Separation HRIR (14-channel) | **LGPL-2.0+** | Chris Robinson & OpenAL Soft Contributors |
| `presets/oal+++.wav` | OpenAL Soft Maximum | OpenAL Soft Diffuse-Field HRIR (14-channel) | **LGPL-2.0+** | Chris Robinson & OpenAL Soft Contributors |
| `presets/oal_cia0.wav` | OpenAL Soft CIA 0 | CIAIR / OpenAL Soft HRIR Preset 0 (7-channel) | **LGPL-2.0+ / Open Academic Dataset** | OpenAL Soft Project / Nagoya University CIAIR Database |
| `presets/oal_cia1.wav` | OpenAL Soft CIA 1 | CIAIR / OpenAL Soft HRIR Preset 1 (7-channel) | **LGPL-2.0+ / Open Academic Dataset** | OpenAL Soft Project / Nagoya University CIAIR Database |
| `assets/test_surround.wav` | 3D Spatial Audio Test | 8-channel (7.1) directional speaker verification audio assembled from `alsa-utils` (`share/sounds/alsa/*.wav`) | **GPL-2.0-or-later** | The ALSA Project (Jaroslav Kysela & Contributors) |

---

## 2. Upstream Project Attributions

### MIT Media Lab KEMAR HRTF Dataset
* **Project:** HRTF Measurements of a KEMAR Dummy-Head Microphone (`MIT_KEMAR_normal_pinna.sofa`)
* **Authors:** Bill Gardner and Keith Martin (`MIT Media Lab Perceptual Computing Technical Report #280`, May 1994)
* **License Terms:** Provided free for any use (commercial or non-commercial) provided credit is given to MIT Media Lab, Bill Gardner, and Keith Martin.

### OpenAL Soft & HeSuVi HRIR Conversion
* **Repository:** https://github.com/kcat/openal-soft
* **HeSuVi HRIR Format Specification:** https://sourceforge.net/projects/hesuvi/
* **Authors:** Chris Robinson and OpenAL Soft Contributors
* **License:** GNU Lesser General Public License 2.0 or later (LGPL-2.0+)

### CIAIR HRTF Dataset
* **Institution:** Center for Integrated Acoustic Information Research (CIAIR), Nagoya University
* **Description:** Acoustic head-related impulse response measurements converted via OpenAL Soft `makemhr`.

### ALSA Project Speaker-Test Voice Samples (`assets/test_surround.wav`)
* **Project:** Advanced Linux Sound Architecture (`alsa-utils` — `speaker-test/samples/`)
* **Repository:** https://github.com/alsa-project/alsa-utils
* **License:** GNU General Public License v2.0 or later (GPL-2.0-or-later)

