# 🎧 SpatialWire — Audio Assets & Licensing

All bundled Head-Related Impulse Responses (HRIR) and testing assets included in **SpatialWire** are open acoustic datasets or open-source (**Apache-2.0**, **LGPL-2.0+**, or permissive **MIT Media Lab** academic attribution) measurements formatted as 7-channel or 14-channel HeSuVi impulse responses.

> **Strict Permissive Licensing Policy (No `CC BY-SA`):**  
> SpatialWire deliberately excludes copyleft ShareAlike datasets (such as the TH Köln AudioGroup KU 100 `CC BY-SA 3.0` compilation) so that all bundled HRIR impulse responses remain 100% redistributable under permissive open-source licenses (`Apache-2.0`, `MIT`, `LGPL-2.0+`).

---

## 1. Summary Table

| Asset File | Preset Name | Measurement / Source | Upstream License | Attribution / Author |
|---|---|---|---|---|
| `presets/hear.wav` | MIT KEMAR Reference (1994) | MIT Media Lab KEMAR HATS (`MIT_KEMAR_normal_pinna.sofa`, Diffuse-Field Equalized 7-channel 48 kHz HeSuVi format) | **Free Use with Attribution** (MIT Media Lab) | Bill Gardner & Keith Martin (MIT Media Lab, 1994) |
| `presets/sadie_kemar.wav` | SADIE II KEMAR HATS (2018) | SADIE II Subject `D2` KEMAR Head & Torso Simulator (`D2_48K_24bit_256tap_FIR_SOFA.sofa`, 14-channel 48 kHz HeSuVi format) | **Apache-2.0** | Cal Armstrong, Lewis Thresh, Gavin Kearney — AudioLab, University of York (2018) |
| `presets/sadie_kemar_room.wav` | SADIE II KEMAR Studio Room | SADIE II Subject `D2` KEMAR HATS (`D2_HRIR_SOFA` + `D2_BRIR_SOFA` Acoustically Treated Studio Room, 14-channel 48 kHz) | **Apache-2.0** | Cal Armstrong, Lewis Thresh, Gavin Kearney — AudioLab, University of York (2018) |
| `presets/sadie_ku100.wav` | SADIE II Neumann KU 100 | SADIE II Subject `D1` Neumann KU 100 Dummy Head (`D1_48K_24bit_256tap_FIR_SOFA.sofa`, torso-warmth & pinna-smoothed 14-channel 48 kHz) | **Apache-2.0** | Cal Armstrong, Lewis Thresh, Gavin Kearney — AudioLab, University of York (2018) |
| `presets/oal_dflt.wav` | OpenAL Soft Standard | OpenAL Soft Default HRIR (7-channel HeSuVi format) | **LGPL-2.0+** | Chris Robinson & OpenAL Soft Contributors |
| `presets/oal+.wav` | OpenAL Soft Wide | OpenAL Soft Extended Cross-Talk HRIR (14-channel, 150 ms room tail) | **LGPL-2.0+** | Chris Robinson & OpenAL Soft Contributors |
| `presets/oal++.wav` | OpenAL Soft Extra Wide | OpenAL Soft High-Separation HRIR (14-channel, 150 ms room tail) | **LGPL-2.0+** | Chris Robinson & OpenAL Soft Contributors |
| `presets/oal+++.wav` | OpenAL Soft Maximum | OpenAL Soft Cinema HRIR (14-channel, 250 ms room tail) | **LGPL-2.0+** | Chris Robinson & OpenAL Soft Contributors |
| `presets/oal_cia0.wav` | OpenAL Soft CIA 0 | CIAIR / OpenAL Soft HRIR Preset 0 (7-channel) | **LGPL-2.0+ / Open Academic Dataset** | OpenAL Soft Project / Nagoya University CIAIR Database |
| `presets/oal_cia1.wav` | OpenAL Soft CIA 1 | CIAIR / OpenAL Soft HRIR Preset 1 (7-channel) | **LGPL-2.0+ / Open Academic Dataset** | OpenAL Soft Project / Nagoya University CIAIR Database |
| `assets/test_surround.wav` | 3D Spatial Audio Test | 8-channel (7.1) directional speaker verification audio assembled from `alsa-utils` (`share/sounds/alsa/*.wav`) | **GPL-2.0-or-later** | The ALSA Project (Jaroslav Kysela & Contributors) |

---

## 2. Upstream Project Attributions

### SADIE II Database (University of York — `sadie_kemar.wav`, `sadie_kemar_room.wav`, `sadie_ku100.wav`)
* **Project:** SADIE II Database (Spatial Audio for Domestic Interactive Entertainment)
* **Authors:** Cal Armstrong, Lewis Thresh, and Gavin Kearney (The Audio Lab, Department of Electronic Engineering, University of York, UK)
* **Reference:** *A Perceptual Evaluation of Individual and Non-Individual HRTFs: A Case Study of the SADIE II Database*, Applied Sciences 8(11), 2029 (2018). DOI: `https://doi.org/10.3390/app8112029`
* **Copyright & License:** Copyright © 2018, University of York. Licensed under the **Apache License, Version 2.0** (`http://www.apache.org/licenses/LICENSE-2.0`).

### MIT Media Lab KEMAR HRTF Dataset (`hear.wav`)
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


