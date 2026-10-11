"""
SpatialWire Core Audio Engine
PipeWire Native 7.1 Virtual Surround & Binaural HRTF Convolver System.
"""

import os
import sys
import signal
import subprocess
import time
import re
import struct
import shutil
import json
from pathlib import Path

HOME = os.path.expanduser("~")
SPATIALWIRE_CONFIG_DIR = os.path.join(HOME, ".config/spatialwire")
USER_PRESETS_DIR = os.path.join(SPATIALWIRE_CONFIG_DIR, "presets")
STATE_FILE = os.path.join(SPATIALWIRE_CONFIG_DIR, "state.json")

PIPEWIRE_CONFIG_DIR = os.path.join(HOME, ".config/pipewire")
FILTER_CHAIN_CONF = os.path.join(PIPEWIRE_CONFIG_DIR, "filter-chain.conf")
FILTER_CHAIN_BACKUP = os.path.join(PIPEWIRE_CONFIG_DIR, "filter-chain.conf.user.bak")
SPATIALWIRE_HEADER = "# SpatialWire — PipeWire Virtual Surround"

SYSTEMD_USER_DIR = os.path.join(HOME, ".config/systemd/user")
FILTER_CHAIN_SERVICE = "pipewire-filter-chain.service"

# Repo & System presets search paths
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BUNDLED_PRESETS_DIR = os.path.join(REPO_DIR, "presets")
SHARE_PRESETS_DIR = os.path.join(REPO_DIR, "share/spatialwire/presets")
SYSTEM_LOCAL_PRESETS_DIR = "/usr/local/share/spatialwire/presets"
SYSTEM_PRESETS_DIR = "/usr/share/spatialwire/presets"

VIRTUAL_SINK_NAME = "effect_input.virtual-surround-7.1-hesuvi"
VIRTUAL_PLAYBACK_NAME = "effect_output.virtual-surround-7.1-hesuvi"

FOSS_PRESET_METADATA = {
    "hear": {
        "name": "MIT KEMAR Reference (1994)",
        "description": "Diffuse-field equalized MIT Media Lab KEMAR HATS reference with natural torso/shoulder warmth.",
        "category": "Studio Reference"
    },
    "sadie_kemar": {
        "name": "SADIE II KEMAR HATS (2018)",
        "description": "University of York KEMAR Head & Torso Simulator (48 kHz Genelec 8010, Apache-2.0) with full torso & shoulder reflections.",
        "category": "HATS Torso Reference"
    },
    "sadie_kemar_room": {
        "name": "SADIE II KEMAR Studio Room",
        "description": "University of York KEMAR HATS + Acoustically Treated Listening Room BRIR (85 ms Genelec 8030/40, Apache-2.0) — ideal for IEMs.",
        "category": "Studio Room & IEM"
    },
    "sadie_ku100": {
        "name": "SADIE II Neumann KU 100",
        "description": "University of York Neumann KU 100 binaural studio microphone head (Apache-2.0) with torso-warmth and pinna-smoothing compensation.",
        "category": "Binaural Studio Mic"
    },
    "oal_dflt": {
        "name": "OpenAL Soft Standard",
        "description": "Natural gaming soundstage with balanced cross-talk and pinpoint HRTF positioning.",
        "category": "Gaming & Multimedia"
    },
    "oal+": {
        "name": "OpenAL Soft Wide",
        "description": "Expanded horizontal stereo separation and 150 ms studio room reflections (-27.4 dB).",
        "category": "Wide Soundstage"
    },
    "oal++": {
        "name": "OpenAL Soft Extra Wide",
        "description": "Pronounced spatial separation for competitive gaming and open-world immersion (150 ms, -26.9 dB).",
        "category": "Competitive Gaming"
    },
    "oal+++": {
        "name": "OpenAL Soft Maximum",
        "description": "Maximum cinema soundstage with 250 ms room decay (-24.5 dB) and deep rear channel expanse.",
        "category": "Cinematic Surround"
    },
    "oal_cia0": {
        "name": "OpenAL Soft CIA 0",
        "description": "Close-field anechoic binaural HRIR profile from the CIAIR / OpenAL Soft acoustic dataset.",
        "category": "Studio Close"
    },
    "oal_cia1": {
        "name": "OpenAL Soft CIA 1",
        "description": "Diffused binaural HRIR field from the CIAIR / OpenAL Soft acoustic dataset.",
        "category": "Open-Back Audiophile"
    }
}

TRANSDUCER_MODES = {
    "over-ear": {
        "name": "Over-Ear Headphones",
        "short": "Over-Ear",
        "description": "Direct diffuse-field target for open and closed over-ear headphones (natural outer ear & open ear canal)."
    },
    "iem": {
        "name": "In-Ear Monitors (IEM)",
        "short": "IEM",
        "description": "Compensates IEM 2.85 kHz ear-canal gain (-3.2 dB), restores HATS torso warmth (+1.8 dB @ 250 Hz), and smooths >9.5 kHz pinna notches."
    }
}


def run_cmd(cmd, check=False):
    """Executes a command and returns stripped stdout."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check, timeout=5)
        return res.stdout.strip()
    except Exception:
        return ""


def ensure_dirs():
    """Ensures configuration and presets directories exist."""
    os.makedirs(SPATIALWIRE_CONFIG_DIR, exist_ok=True)
    os.makedirs(USER_PRESETS_DIR, exist_ok=True)
    os.makedirs(PIPEWIRE_CONFIG_DIR, exist_ok=True)


def ensure_filter_chain_service():
    """
    Ensures a user systemd unit `pipewire-filter-chain.service` exists.
    On standalone Linux distributions where the unit is not pre-installed,
    creates `~/.config/systemd/user/pipewire-filter-chain.service` automatically.
    """
    cat_out = run_cmd(["systemctl", "--user", "cat", FILTER_CHAIN_SERVICE])
    if cat_out:
        return True

    pw_bin = shutil.which("pipewire") or "/usr/bin/pipewire"
    os.makedirs(SYSTEMD_USER_DIR, exist_ok=True)
    unit_path = os.path.join(SYSTEMD_USER_DIR, FILTER_CHAIN_SERVICE)
    unit_content = f"""[Unit]
Description=PipeWire Filter Chain Service (Managed by SpatialWire)
After=pipewire.service
BindsTo=pipewire.service

[Service]
Type=simple
ExecStart={pw_bin} -c filter-chain.conf
Restart=on-failure

[Install]
WantedBy=default.target
"""
    try:
        with open(unit_path, "w", encoding="utf-8") as f:
            f.write(unit_content)
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


def notify_clickclick_reconnect():
    """Signals ClickClick daemon (if running) to re-anchor its audio stream."""
    pid_file = os.path.join(HOME, ".config/clickclick/daemon.pid")
    if os.path.isfile(pid_file):
        try:
            with open(pid_file, "r") as f:
                pid_str = f.read().strip()
            if pid_str.isdigit():
                os.kill(int(pid_str), signal.SIGUSR1)
        except Exception:
            pass
    run_cmd(["pkill", "-USR1", "-f", r"(^|/)((\.)?clickclickd(-wrapped)?|clickclick_rs)( |$)"])


def get_wav_channels(wav_path):
    """Reads WAV fmt chunk to determine whether it has 7 or 14 channels."""
    try:
        with open(wav_path, "rb") as f:
            data = f.read(128)
            idx = data.find(b"fmt ")
            if idx != -1:
                fmt_tag, nchan = struct.unpack("<HH", data[idx+8:idx+12])
                return nchan
    except Exception:
        pass
    return 14


def _get_default_sink_node_name():
    """Queries wpctl for the current default audio sink's node.name."""
    info = run_cmd(["wpctl", "inspect", "@DEFAULT_AUDIO_SINK@"])
    if info:
        m = re.search(r'node\.name\s*=\s*"([^"]+)"', info)
        if m:
            return m.group(1)
    return ""


def get_all_sinks_and_filters():
    """
    Extracts active sink & filter nodes with their IDs.
    Uses fast JSON `pw-dump Node` primary path with `wpctl status` fallback.
    """
    default_node_name = _get_default_sink_node_name()
    pw_raw = run_cmd(["pw-dump", "Node"])
    if pw_raw:
        try:
            data = json.loads(pw_raw)
            nodes = []
            for item in data:
                info = item.get("info") or {}
                props = info.get("props") or {}
                media_class = props.get("media.class", "")
                if media_class in ("Audio/Sink", "Audio/Duplex"):
                    nid = item.get("id")
                    node_name = props.get("node.name", "")
                    label = (
                        props.get("node.description")
                        or props.get("node.nick")
                        or props.get("media.name")
                        or node_name
                    )
                    is_virtual = (
                        VIRTUAL_SINK_NAME in node_name
                        or "virtual-surround" in node_name
                        or "effect_" in node_name
                        or "Virtual Surround" in label
                    )
                    nodes.append({
                        "id": int(nid),
                        "label": label,
                        "node_name": node_name,
                        "default": bool(default_node_name and node_name == default_node_name),
                        "section": "filters" if is_virtual else "sinks",
                    })
            if nodes:
                return nodes
        except Exception:
            pass

    # Fallback: parse wpctl status
    out = run_cmd(["wpctl", "status"])
    lines = out.splitlines()
    nodes = []
    current_section = None

    for line in lines:
        if "Sinks:" in line:
            current_section = "sinks"
            continue
        elif "Filters:" in line:
            current_section = "filters"
            continue
        elif any(k in line for k in ["Sources:", "Streams:", "Devices:", "Settings", "Video"]):
            current_section = None
            continue

        if current_section in ("sinks", "filters"):
            m = re.search(r"(\*?)\s*(\d+)\.\s+(.*)", line)
            if m:
                is_def = bool(m.group(1))
                nid = int(m.group(2))
                raw_label = m.group(3).strip()
                clean_label = re.sub(r"\s*\[vol:.*\]", "", raw_label).strip()
                nodes.append({
                    "id": nid,
                    "label": clean_label,
                    "default": is_def,
                    "section": current_section
                })

    for s in nodes:
        info = run_cmd(["wpctl", "inspect", str(s["id"])])
        m_name = re.search(r'node\.name\s*=\s*"([^"]+)"', info)
        s["node_name"] = m_name.group(1) if m_name else ""

    return nodes


def get_hardware_sink(nodes=None):
    """
    Finds physical DAC/soundcard audio sink (excluding virtual/filters).
    Prioritizes:
    1. Currently active default physical sink
    2. Previously saved hardware_sink in STATE_FILE
    3. USB / Headphone / Analog sinks over HDMI/DisplayPort
    4. First available physical sink
    """
    if nodes is None:
        nodes = get_all_sinks_and_filters()

    hw_candidates = []
    for s in nodes:
        name = s.get("node_name", "")
        label = s.get("label", "")
        if s.get("section") == "sinks":
            if "virtual-surround" not in name and "effect_" not in name and "mono_" not in name:
                if "Virtual Surround" not in label:
                    hw_candidates.append(s)

    if not hw_candidates:
        return None

    # 1. Default physical sink
    for s in hw_candidates:
        if s.get("default"):
            return s

    # 2. Saved hardware_sink from state.json
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                saved_hw = json.load(f).get("hardware_sink", "")
            if saved_hw:
                for s in hw_candidates:
                    if s.get("node_name") == saved_hw or s.get("label") == saved_hw:
                        return s
        except Exception:
            pass

    # 3. Prefer non-HDMI (USB/Analog/Headphone) sinks
    for s in hw_candidates:
        name_l = s.get("node_name", "").lower()
        if "hdmi" not in name_l and "displayport" not in name_l:
            return s

    return hw_candidates[0]


def get_virtual_surround_sink(nodes=None):
    """Finds active virtual surround filter input sink node."""
    if nodes is None:
        nodes = get_all_sinks_and_filters()

    for s in nodes:
        name = s.get("node_name", "")
        label = s.get("label", "")
        if (VIRTUAL_SINK_NAME in name or "Virtual Surround" in label) and "Output" not in label:
            return s
    return None


def list_all_presets():
    """Discovers all available HRIR presets across user, repo, Nix store, and system directories."""
    ensure_dirs()
    presets = []
    seen_ids = set()

    search_dirs = [
        USER_PRESETS_DIR,
        BUNDLED_PRESETS_DIR,
        SHARE_PRESETS_DIR,
        SYSTEM_LOCAL_PRESETS_DIR,
        SYSTEM_PRESETS_DIR,
    ]

    for sdir in search_dirs:
        if not os.path.isdir(sdir):
            continue
        for fname in sorted(os.listdir(sdir)):
            if not fname.endswith(".wav"):
                continue
            pid = fname[:-4]
            if pid in seen_ids:
                continue

            full_path = os.path.join(sdir, fname)
            channels = get_wav_channels(full_path)
            meta = FOSS_PRESET_METADATA.get(pid, {
                "name": pid.replace("_", " ").title(),
                "description": f"Custom {channels}-channel HRIR impulse response measurement.",
                "category": "User Preset" if sdir == USER_PRESETS_DIR else "Imported Profile"
            })

            presets.append({
                "id": pid,
                "name": meta["name"],
                "description": meta["description"],
                "category": meta["category"],
                "channels": channels,
                "path": full_path,
                "is_custom": sdir == USER_PRESETS_DIR
            })
            seen_ids.add(pid)

    return presets


def resolve_preset_path(preset_id_or_path):
    """Resolves a preset identifier or explicit file path to a verified WAV file."""
    if os.path.isfile(preset_id_or_path) and preset_id_or_path.lower().endswith(".wav"):
        return os.path.abspath(preset_id_or_path)

    pid = preset_id_or_path[:-4] if preset_id_or_path.lower().endswith(".wav") else preset_id_or_path
    for p in list_all_presets():
        if p["id"].lower() == pid.lower():
            return p["path"]

    return None


def get_transducer_mode():
    """Returns the configured transducer mode ('over-ear' or 'iem')."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                mode = json.load(f).get("transducer_mode", "over-ear")
                if mode in TRANSDUCER_MODES:
                    return mode
        except Exception:
            pass
    return "over-ear"


def generate_filter_chain_conf(wav_path, profile_name, hw_sink_name, transducer_mode=None):
    """Builds PipeWire filter-chain configuration with 16 acoustic convolvers and optional IEM target compensation."""
    nchan = get_wav_channels(wav_path)
    t_mode = transducer_mode if transducer_mode in TRANSDUCER_MODES else get_transducer_mode()

    if nchan == 7:
        convolvers = f"""
                    # 16 Convolvers (7-Channel Symmetrical HeSuVi HRIR)
                    # Front Left
                    {{ type = builtin label = convolver name = convFL_L  config = {{ filename = "{wav_path}" channel = 0 }} }}
                    {{ type = builtin label = convolver name = convFL_R  config = {{ filename = "{wav_path}" channel = 1 }} }}
                    # Front Right (Mirrored from FL: Left Ear=1, Right Ear=0)
                    {{ type = builtin label = convolver name = convFR_L  config = {{ filename = "{wav_path}" channel = 1 }} }}
                    {{ type = builtin label = convolver name = convFR_R  config = {{ filename = "{wav_path}" channel = 0 }} }}
                    # Front Center (Symmetrical: Left Ear=6, Right Ear=6)
                    {{ type = builtin label = convolver name = convFC_L  config = {{ filename = "{wav_path}" channel = 6 }} }}
                    {{ type = builtin label = convolver name = convFC_R  config = {{ filename = "{wav_path}" channel = 6 }} }}
                    # LFE / Subwoofer (Treated as FC)
                    {{ type = builtin label = convolver name = convLFE_L config = {{ filename = "{wav_path}" channel = 6 }} }}
                    {{ type = builtin label = convolver name = convLFE_R config = {{ filename = "{wav_path}" channel = 6 }} }}
                    # Rear Left
                    {{ type = builtin label = convolver name = convRL_L  config = {{ filename = "{wav_path}" channel = 4 }} }}
                    {{ type = builtin label = convolver name = convRL_R  config = {{ filename = "{wav_path}" channel = 5 }} }}
                    # Rear Right (Mirrored from RL: Left Ear=5, Right Ear=4)
                    {{ type = builtin label = convolver name = convRR_L  config = {{ filename = "{wav_path}" channel = 5 }} }}
                    {{ type = builtin label = convolver name = convRR_R  config = {{ filename = "{wav_path}" channel = 4 }} }}
                    # Side Left
                    {{ type = builtin label = convolver name = convSL_L  config = {{ filename = "{wav_path}" channel = 2 }} }}
                    {{ type = builtin label = convolver name = convSL_R  config = {{ filename = "{wav_path}" channel = 3 }} }}
                    # Side Right (Mirrored from SL: Left Ear=3, Right Ear=2)
                    {{ type = builtin label = convolver name = convSR_L  config = {{ filename = "{wav_path}" channel = 3 }} }}
                    {{ type = builtin label = convolver name = convSR_R  config = {{ filename = "{wav_path}" channel = 2 }} }}
        """
    else:
        convolvers = f"""
                    # 16 Convolvers (14-Channel Full HeSuVi HRIR)
                    # Front Left
                    {{ type = builtin label = convolver name = convFL_L  config = {{ filename = "{wav_path}" channel = 0 }} }}
                    {{ type = builtin label = convolver name = convFL_R  config = {{ filename = "{wav_path}" channel = 1 }} }}
                    # Front Right
                    {{ type = builtin label = convolver name = convFR_L  config = {{ filename = "{wav_path}" channel = 8 }} }}
                    {{ type = builtin label = convolver name = convFR_R  config = {{ filename = "{wav_path}" channel = 7 }} }}
                    # Front Center
                    {{ type = builtin label = convolver name = convFC_L  config = {{ filename = "{wav_path}" channel = 6 }} }}
                    {{ type = builtin label = convolver name = convFC_R  config = {{ filename = "{wav_path}" channel = 13 }} }}
                    # LFE / Subwoofer (Treated as FC)
                    {{ type = builtin label = convolver name = convLFE_L config = {{ filename = "{wav_path}" channel = 6 }} }}
                    {{ type = builtin label = convolver name = convLFE_R config = {{ filename = "{wav_path}" channel = 13 }} }}
                    # Rear Left
                    {{ type = builtin label = convolver name = convRL_L  config = {{ filename = "{wav_path}" channel = 4 }} }}
                    {{ type = builtin label = convolver name = convRL_R  config = {{ filename = "{wav_path}" channel = 5 }} }}
                    # Rear Right
                    {{ type = builtin label = convolver name = convRR_L  config = {{ filename = "{wav_path}" channel = 12 }} }}
                    {{ type = builtin label = convolver name = convRR_R  config = {{ filename = "{wav_path}" channel = 11 }} }}
                    # Side Left
                    {{ type = builtin label = convolver name = convSL_L  config = {{ filename = "{wav_path}" channel = 2 }} }}
                    {{ type = builtin label = convolver name = convSL_R  config = {{ filename = "{wav_path}" channel = 3 }} }}
                    # Side Right
                    {{ type = builtin label = convolver name = convSR_L  config = {{ filename = "{wav_path}" channel = 10 }} }}
                    {{ type = builtin label = convolver name = convSR_R  config = {{ filename = "{wav_path}" channel = 9 }} }}
        """

    if t_mode == "iem":
        iem_nodes = """
                    # IEM Target Compensation Stage (Torso Warmth + Ear-Canal Pinna De-Harsh + Treble Smoothing)
                    { type = builtin label = bq_peaking   name = iemBodyL   control = { "Freq" = 250.0  "Q" = 0.8 "Gain" = 1.8  } }
                    { type = builtin label = bq_peaking   name = iemPinnaL  control = { "Freq" = 2850.0 "Q" = 1.4 "Gain" = -3.2 } }
                    { type = builtin label = bq_highshelf name = iemSmoothL control = { "Freq" = 9500.0 "Q" = 0.7 "Gain" = -2.0 } }
                    { type = builtin label = bq_peaking   name = iemBodyR   control = { "Freq" = 250.0  "Q" = 0.8 "Gain" = 1.8  } }
                    { type = builtin label = bq_peaking   name = iemPinnaR  control = { "Freq" = 2850.0 "Q" = 1.4 "Gain" = -3.2 } }
                    { type = builtin label = bq_highshelf name = iemSmoothR control = { "Freq" = 9500.0 "Q" = 0.7 "Gain" = -2.0 } }"""
        iem_links = """
                    # IEM Post-Mixer Biquad Chain
                    { output = "mixL:Out"       input = "iemBodyL:In"   }
                    { output = "iemBodyL:Out"   input = "iemPinnaL:In"  }
                    { output = "iemPinnaL:Out"  input = "iemSmoothL:In" }
                    { output = "mixR:Out"       input = "iemBodyR:In"   }
                    { output = "iemBodyR:Out"   input = "iemPinnaR:In"  }
                    { output = "iemPinnaR:Out"  input = "iemSmoothR:In" }"""
        graph_outputs = '[ "iemSmoothL:Out" "iemSmoothR:Out" ]'
    else:
        iem_nodes = ""
        iem_links = ""
        graph_outputs = '[ "mixL:Out" "mixR:Out" ]'

    return f"""{SPATIALWIRE_HEADER} (7.1 HRTF Filter-Chain)
# Profile: {profile_name} ({nchan}-Channel HRIR)
# Transducer Mode: {t_mode}
# Hardware Target: {hw_sink_name}

context.properties = {{
    core.daemon = false
    log.level   = 0
}}

context.spa-libs = {{
    audio.convert.* = audioconvert/libspa-audioconvert
    support.*       = support/libspa-support
}}

context.modules = [
    {{ name = libpipewire-module-rt
        flags = [ ifexists nofail ]
        args = {{
            nice.level   = -11
            rt.prio      = 88
            rt.time.soft = 2000000
            rt.time.hard = 2000000
        }}
    }}
    {{ name = libpipewire-module-protocol-native }}
    {{ name = libpipewire-module-client-node }}
    {{ name = libpipewire-module-adapter }}
    {{ name = libpipewire-module-filter-chain
        flags = [ nofail ]
        args = {{
            node.description = "Virtual Surround 7.1 ({profile_name})"
            media.name       = "Virtual Surround 7.1 ({profile_name})"
            filter.graph = {{
                nodes = [
                    # Duplicate inputs for binaural splitting (each channel feeds Left AND Right ear convolvers)
                    {{ type = builtin label = copy name = copyFL  }}
                    {{ type = builtin label = copy name = copyFR  }}
                    {{ type = builtin label = copy name = copyFC  }}
                    {{ type = builtin label = copy name = copyLFE }}
                    {{ type = builtin label = copy name = copyRL  }}
                    {{ type = builtin label = copy name = copyRR  }}
                    {{ type = builtin label = copy name = copySL  }}
                    {{ type = builtin label = copy name = copySR  }}

{convolvers}
                    # Stereo Ear Output Mixers
                    {{ type = builtin label = mixer name = mixL }}
                    {{ type = builtin label = mixer name = mixR }}{iem_nodes}
                ]
                links = [
                    # Input Distribution: Each channel copies to BOTH Left and Right ear convolvers
                    {{ output = "copyFL:Out"  input = "convFL_L:In"  }}
                    {{ output = "copyFL:Out"  input = "convFL_R:In"  }}
                    {{ output = "copyFR:Out"  input = "convFR_L:In"  }}
                    {{ output = "copyFR:Out"  input = "convFR_R:In"  }}
                    {{ output = "copyFC:Out"  input = "convFC_L:In"  }}
                    {{ output = "copyFC:Out"  input = "convFC_R:In"  }}
                    {{ output = "copyLFE:Out" input = "convLFE_L:In" }}
                    {{ output = "copyLFE:Out" input = "convLFE_R:In" }}
                    {{ output = "copyRL:Out"  input = "convRL_L:In"  }}
                    {{ output = "copyRL:Out"  input = "convRL_R:In"  }}
                    {{ output = "copyRR:Out"  input = "convRR_L:In"  }}
                    {{ output = "copyRR:Out"  input = "convRR_R:In"  }}
                    {{ output = "copySL:Out"  input = "convSL_L:In"  }}
                    {{ output = "copySL:Out"  input = "convSL_R:In"  }}
                    {{ output = "copySR:Out"  input = "convSR_L:In"  }}
                    {{ output = "copySR:Out"  input = "convSR_R:In"  }}

                    # Left Ear Summation (mixL)
                    {{ output = "convFL_L:Out"  input = "mixL:In 1" }}
                    {{ output = "convFR_L:Out"  input = "mixL:In 2" }}
                    {{ output = "convFC_L:Out"  input = "mixL:In 3" }}
                    {{ output = "convLFE_L:Out" input = "mixL:In 4" }}
                    {{ output = "convRL_L:Out"  input = "mixL:In 5" }}
                    {{ output = "convRR_L:Out"  input = "mixL:In 6" }}
                    {{ output = "convSL_L:Out"  input = "mixL:In 7" }}
                    {{ output = "convSR_L:Out"  input = "mixL:In 8" }}

                    # Right Ear Summation (mixR)
                    {{ output = "convFL_R:Out"  input = "mixR:In 1" }}
                    {{ output = "convFR_R:Out"  input = "mixR:In 2" }}
                    {{ output = "convFC_R:Out"  input = "mixR:In 3" }}
                    {{ output = "convLFE_R:Out" input = "mixR:In 4" }}
                    {{ output = "convRL_R:Out"  input = "mixR:In 5" }}
                    {{ output = "convRR_R:Out"  input = "mixR:In 6" }}
                    {{ output = "convSL_R:Out"  input = "mixR:In 7" }}
                    {{ output = "convSR_R:Out"  input = "mixR:In 8" }}{iem_links}
                ]
                inputs  = [
                    "copyFL:In" "copyFR:In" "copyFC:In" "copyLFE:In"
                    "copyRL:In" "copyRR:In" "copySL:In" "copySR:In"
                ]
                outputs = {graph_outputs}
            }}
            capture.props = {{
                node.name        = "{VIRTUAL_SINK_NAME}"
                media.class      = "Audio/Sink"
                audio.channels   = 8
                audio.position   = [ FL FR FC LFE RL RR SL SR ]
                priority.driver  = 1009
                priority.session = 1009
            }}
            playback.props = {{
                node.name        = "{VIRTUAL_PLAYBACK_NAME}"
                node.passive     = true
                audio.channels   = 2
                audio.position   = [ FL FR ]
                target.object    = "{hw_sink_name}"
            }}
        }}
    }}
]
"""


def cleanup_duplicate_links(hw_sink_name):
    """Disconnects any erroneous loopback links between virtual playback and virtual capture."""
    try:
        out = run_cmd(["pw-link", "-l"])
        curr_src = None
        for line in out.splitlines():
            if not line.startswith(" ") and ":" in line:
                curr_src = line.strip()
            elif "|->" in line and curr_src:
                dest = line.split("|->")[1].strip()
                if VIRTUAL_PLAYBACK_NAME in curr_src and VIRTUAL_SINK_NAME in dest:
                    run_cmd(["pw-link", "-d", curr_src, dest])
    except Exception:
        pass


def get_current_status():
    """Returns comprehensive JSON-serializable status of SpatialWire."""
    nodes = get_all_sinks_and_filters()
    vsink = get_virtual_surround_sink(nodes)
    hw_sink = get_hardware_sink(nodes)
    t_mode = get_transducer_mode()

    is_active = vsink is not None
    active_profile_id = ""
    active_profile_name = ""

    if is_active:
        lbl = vsink.get("label", "")
        m = re.search(r"Virtual Surround 7\.1 \(([^)]+)\)", lbl)
        if m:
            active_profile_id = m.group(1)

    if not active_profile_id and os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                data = json.load(f)
                active_profile_id = data.get("active_profile_id", "")
        except Exception:
            pass

    if active_profile_id:
        meta = FOSS_PRESET_METADATA.get(active_profile_id)
        if meta:
            active_profile_name = meta["name"]
        else:
            active_profile_name = active_profile_id

    return {
        "active": is_active,
        "active_profile_id": active_profile_id,
        "active_profile_name": active_profile_name or "None",
        "transducer_mode": t_mode,
        "transducer_mode_name": TRANSDUCER_MODES[t_mode]["name"],
        "virtual_sink_id": vsink["id"] if vsink else None,
        "virtual_sink_name": vsink["node_name"] if vsink else None,
        "hardware_sink_id": hw_sink["id"] if hw_sink else None,
        "hardware_sink_name": hw_sink.get("node_name", "") if hw_sink else "",
        "hardware_sink_label": hw_sink.get("label", "Default Output") if hw_sink else "None",
        "presets_count": len(list_all_presets()),
        "latency_mode": "Quantum-Synced (RT Priority 88, ~1.3 ms)"
    }


def enable_profile(preset_id_or_path, display_name=None, transducer_mode=None):
    """Enables and routes virtual 7.1 HRTF surround sound."""
    ensure_dirs()
    ensure_filter_chain_service()

    wav_path = resolve_preset_path(preset_id_or_path)
    if not wav_path or not os.path.isfile(wav_path):
        return {"success": False, "error": f"HRIR file not found for: {preset_id_or_path}"}

    pid = Path(wav_path).stem
    disp = display_name or FOSS_PRESET_METADATA.get(pid, {}).get("name", pid)
    t_mode = transducer_mode if transducer_mode in TRANSDUCER_MODES else get_transducer_mode()

    hw_sink = get_hardware_sink()
    if not hw_sink:
        return {"success": False, "error": "No physical audio output device detected"}

    hw_sink_name = hw_sink.get("node_name") or hw_sink.get("label")

    # Non-destructive backup if user had a custom non-SpatialWire filter-chain.conf
    if os.path.isfile(FILTER_CHAIN_CONF):
        try:
            with open(FILTER_CHAIN_CONF, "r", encoding="utf-8", errors="ignore") as f:
                first_line = f.readline()
            if not first_line.startswith(SPATIALWIRE_HEADER):
                shutil.copy2(FILTER_CHAIN_CONF, FILTER_CHAIN_BACKUP)
        except Exception:
            pass

    conf_content = generate_filter_chain_conf(wav_path, pid, hw_sink_name, transducer_mode=t_mode)
    with open(FILTER_CHAIN_CONF, "w", encoding="utf-8") as f:
        f.write(conf_content)

    # Restart pipewire-filter-chain service
    subprocess.run(["systemctl", "--user", "restart", FILTER_CHAIN_SERVICE], capture_output=True, timeout=5)

    # Wait for sink to settle
    vsink = None
    for _ in range(25):
        time.sleep(0.1)
        vsink = get_virtual_surround_sink()
        if vsink:
            break

    if not vsink:
        return {"success": False, "error": "Filter-chain sink failed to register in PipeWire"}

    vsink_id = vsink["id"]
    run_cmd(["wpctl", "set-default", str(vsink_id)])
    time.sleep(0.15)

    # Explicit link to hardware playback
    run_cmd(["pw-link", f"{VIRTUAL_PLAYBACK_NAME}:output_FL", f"{hw_sink_name}:playback_FL"])
    run_cmd(["pw-link", f"{VIRTUAL_PLAYBACK_NAME}:output_FR", f"{hw_sink_name}:playback_FR"])
    cleanup_duplicate_links(hw_sink_name)

    # Hot-reload ClickClick if running so keystroke sounds anchor smoothly
    notify_clickclick_reconnect()

    # Save state
    state = {
        "active": True,
        "active_profile_id": pid,
        "active_profile_name": disp,
        "transducer_mode": t_mode,
        "wav_path": wav_path,
        "hardware_sink": hw_sink_name,
        "updated_at": time.time()
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    t_short = TRANSDUCER_MODES[t_mode]["short"]
    run_cmd(["notify-send", "-i", "audio-headphones", "SpatialWire 3D Audio", f"Active: {disp} [{t_short}]"])
    return {
        "success": True,
        "profile_id": pid,
        "profile_name": disp,
        "transducer_mode": t_mode,
        "transducer_mode_name": TRANSDUCER_MODES[t_mode]["name"],
        "virtual_sink_id": vsink_id,
        "hardware_sink": hw_sink_name
    }


def set_transducer_mode(mode):
    """Sets the transducer target mode ('over-ear' or 'iem') and hot-reloads if active."""
    ensure_dirs()
    norm = mode.strip().lower()
    if norm in ("iem", "iems", "in-ear", "inear"):
        norm = "iem"
    elif norm in ("over-ear", "overear", "headphones", "headphone"):
        norm = "over-ear"
    else:
        return {"success": False, "error": f"Unknown transducer mode '{mode}'. Choose 'over-ear' or 'iem'."}

    saved = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except Exception:
            saved = {}

    saved["transducer_mode"] = norm
    saved["updated_at"] = time.time()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(saved, f, indent=2)

    status = get_current_status()
    if status["active"]:
        pid = status.get("active_profile_id") or saved.get("active_profile_id") or "hear"
        return enable_profile(pid, transducer_mode=norm)

    return {
        "success": True,
        "transducer_mode": norm,
        "transducer_mode_name": TRANSDUCER_MODES[norm]["name"],
        "reloaded": False
    }


def disable_spatial():
    """Disables virtual surround and restores direct DAC stereo output (and any user filter-chain backup)."""
    subprocess.run(["systemctl", "--user", "stop", FILTER_CHAIN_SERVICE], capture_output=True, timeout=5)
    subprocess.run(["pkill", "-f", "pipewire -c filter-chain.conf"], capture_output=True, timeout=3)

    if os.path.isfile(FILTER_CHAIN_BACKUP):
        try:
            shutil.move(FILTER_CHAIN_BACKUP, FILTER_CHAIN_CONF)
        except Exception:
            pass
    elif os.path.isfile(FILTER_CHAIN_CONF):
        try:
            with open(FILTER_CHAIN_CONF, "r", encoding="utf-8", errors="ignore") as f:
                first_line = f.readline()
            if first_line.startswith(SPATIALWIRE_HEADER):
                os.remove(FILTER_CHAIN_CONF)
        except Exception:
            pass

    for _ in range(15):
        if get_virtual_surround_sink() is None:
            break
        time.sleep(0.1)

    hw_sink = get_hardware_sink()
    if hw_sink:
        run_cmd(["wpctl", "set-default", str(hw_sink["id"])])

    notify_clickclick_reconnect()

    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            saved["active"] = False
            saved["updated_at"] = time.time()
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(saved, f, indent=2)
        except Exception:
            pass

    run_cmd(["notify-send", "-i", "audio-headphones", "SpatialWire 3D Audio", "Spatial Surround Disabled → Stereo Direct"])
    return {"success": True, "restored_sink": hw_sink.get("label") if hw_sink else None}


def play_surround_test():
    """Plays an 8-channel directional test audio to verify spatial perception."""
    test_file = None
    for cand in [
        os.path.join(REPO_DIR, "assets/test_surround.wav"),
        os.path.join(REPO_DIR, "share/spatialwire/assets/test_surround.wav"),
        os.path.join(SCRIPT_DIR, "../assets/test_surround.wav"),
        os.path.join(SCRIPT_DIR, "../share/spatialwire/assets/test_surround.wav"),
        "/usr/share/spatialwire/assets/test_surround.wav",
        "/usr/local/share/spatialwire/assets/test_surround.wav",
    ]:
        if os.path.isfile(cand):
            test_file = cand
            break

    if not test_file or not os.path.isfile(test_file):
        return {"success": False, "error": "Test audio asset not found"}

    if shutil.which("pw-play"):
        subprocess.Popen(["pw-play", test_file])
        return {"success": True, "player": "pw-play", "file": test_file}
    elif shutil.which("mpv"):
        subprocess.Popen(["mpv", "--no-video", test_file])
        return {"success": True, "player": "mpv", "file": test_file}

    return {"success": False, "error": "Neither pw-play nor mpv found"}


def import_custom_wav(src_path):
    """Imports an external HeSuVi WAV into user's presets."""
    ensure_dirs()
    if not os.path.isfile(src_path) or not src_path.lower().endswith(".wav"):
        return {"success": False, "error": "File must be an existing .wav audio file"}

    channels = get_wav_channels(src_path)
    if channels not in (7, 14):
        return {"success": False, "error": f"WAV has {channels} channels. Must be 7 or 14-channel HeSuVi HRIR."}

    dest_filename = os.path.basename(src_path)
    dest_path = os.path.join(USER_PRESETS_DIR, dest_filename)
    shutil.copy2(src_path, dest_path)

    pid = Path(dest_filename).stem
    return {
        "success": True,
        "profile_id": pid,
        "channels": channels,
        "path": dest_path
    }
