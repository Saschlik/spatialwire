"""
SpatialWire Core Audio Engine
PipeWire Native 7.1 Virtual Surround & Binaural HRTF Convolver System.
"""

import os
import sys
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

# Repo & System presets search paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
BUNDLED_PRESETS_DIR = os.path.join(REPO_DIR, "presets")
SYSTEM_PRESETS_DIR = "/usr/share/spatialwire/presets"
LEGACY_PIPEWIRE_HRIR = os.path.join(PIPEWIRE_CONFIG_DIR, "hrir")
LEGACY_PIPEWIRE_HRIR_REPO = os.path.join(PIPEWIRE_CONFIG_DIR, "hrir-repo/hrir")

VIRTUAL_SINK_NAME = "effect_input.virtual-surround-7.1-hesuvi"
VIRTUAL_PLAYBACK_NAME = "effect_output.virtual-surround-7.1-hesuvi"

FOSS_PRESET_METADATA = {
    "hear": {
        "name": "MIT KEMAR Reference",
        "description": "Acoustically neutral binaural reference measurement (MIT Media Lab / Public Domain).",
        "category": "Studio Reference"
    },
    "oal_dflt": {
        "name": "OpenAL Soft Standard",
        "description": "Natural gaming soundstage with balanced cross-talk and pinpoint HRTF positioning.",
        "category": "Gaming & Multimedia"
    },
    "oal+": {
        "name": "OpenAL Soft Wide",
        "description": "Expanded horizontal stereo separation and heightened side channel awareness.",
        "category": "Wide Soundstage"
    },
    "oal++": {
        "name": "OpenAL Soft Extra Wide",
        "description": "Pronounced spatial separation for competitive gaming and open-world immersion.",
        "category": "Competitive Gaming"
    },
    "oal+++": {
        "name": "OpenAL Soft Maximum",
        "description": "Maximum spatial field expanse with accentuated rear and surround channel depth.",
        "category": "Cinematic Surround"
    },
    "oal_cia0": {
        "name": "OpenAL Soft CIA 0",
        "description": "Close-mic intimate profile optimized for closed-back studio headphones.",
        "category": "Studio Close"
    },
    "oal_cia1": {
        "name": "OpenAL Soft CIA 1",
        "description": "Diffused binaural field tailored for open-back dynamic and planar magnetic drivers.",
        "category": "Open-Back Audiophile"
    }
}


def run_cmd(cmd, check=False):
    """Executes a command and returns stripped stdout."""
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        return res.stdout.strip()
    except Exception:
        return ""


def ensure_dirs():
    """Ensures configuration and presets directories exist."""
    os.makedirs(SPATIALWIRE_CONFIG_DIR, exist_ok=True)
    os.makedirs(USER_PRESETS_DIR, exist_ok=True)
    os.makedirs(PIPEWIRE_CONFIG_DIR, exist_ok=True)


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


def get_all_sinks_and_filters():
    """Extracts active sink & filter nodes with their IDs from wpctl status."""
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
    """Finds physical DAC/soundcard audio sink (excluding virtual/filters)."""
    if nodes is None:
        nodes = get_all_sinks_and_filters()

    for s in nodes:
        name = s.get("node_name", "")
        label = s.get("label", "")
        if s.get("section") == "sinks":
            if "virtual-surround" not in name and "effect_" not in name and "mono_" not in name:
                if "Virtual Surround" not in label:
                    return s
    return None


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
    """Discovers all available HRIR presets across system, repo, and user directories."""
    ensure_dirs()
    presets = []
    seen_ids = set()

    search_dirs = [
        USER_PRESETS_DIR,
        BUNDLED_PRESETS_DIR,
        SYSTEM_PRESETS_DIR,
        LEGACY_PIPEWIRE_HRIR,
        LEGACY_PIPEWIRE_HRIR_REPO,
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
    if os.path.isfile(preset_id_or_path) and preset_id_or_path.endswith(".wav"):
        return os.path.abspath(preset_id_or_path)

    pid = preset_id_or_path.rstrip(".wav")
    for p in list_all_presets():
        if p["id"].lower() == pid.lower():
            return p["path"]

    return None


def generate_filter_chain_conf(wav_path, profile_name, hw_sink_name):
    """Builds PipeWire filter-chain configuration with 16 acoustic convolvers and duplicate input splitters."""
    nchan = get_wav_channels(wav_path)

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

    return f"""# SpatialWire — PipeWire Virtual Surround (7.1 HRTF Filter-Chain)
# Profile: {profile_name} ({nchan}-Channel HRIR)
# Hardware Target: {hw_sink_name}

context.properties = {{ log.level = 0 }}

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
                    {{ type = builtin label = mixer name = mixR }}
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
                    {{ output = "convSR_R:Out"  input = "mixR:In 8" }}
                ]
                inputs  = [
                    "copyFL:In" "copyFR:In" "copyFC:In" "copyLFE:In"
                    "copyRL:In" "copyRR:In" "copySL:In" "copySR:In"
                ]
                outputs = [ "mixL:Out" "mixR:Out" ]
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

    is_active = vsink is not None
    active_profile_id = ""
    active_profile_name = ""

    if is_active:
        # Determine active profile name from label
        lbl = vsink.get("label", "")
        m = re.search(r"Virtual Surround 7\.1 \(([^)]+)\)", lbl)
        if m:
            active_profile_id = m.group(1)
        else:
            # Check state file
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE) as f:
                        data = json.load(f)
                        active_profile_id = data.get("active_profile_id", "")
                except Exception:
                    pass

        # Match to human name
        meta = FOSS_PRESET_METADATA.get(active_profile_id)
        if meta:
            active_profile_name = meta["name"]
        else:
            active_profile_name = active_profile_id or "Custom HRIR"

    return {
        "active": is_active,
        "active_profile_id": active_profile_id,
        "active_profile_name": active_profile_name,
        "virtual_sink_id": vsink["id"] if vsink else None,
        "virtual_sink_name": vsink["node_name"] if vsink else None,
        "hardware_sink_id": hw_sink["id"] if hw_sink else None,
        "hardware_sink_name": hw_sink.get("node_name", "") if hw_sink else "",
        "hardware_sink_label": hw_sink.get("label", "Default Output") if hw_sink else "None",
        "presets_count": len(list_all_presets()),
        "latency_mode": "0 ms (Kernel RT Priority)"
    }


def enable_profile(preset_id_or_path, display_name=None):
    """Enables and routes virtual 7.1 HRTF surround sound."""
    ensure_dirs()
    wav_path = resolve_preset_path(preset_id_or_path)
    if not wav_path or not os.path.isfile(wav_path):
        return {"success": False, "error": f"HRIR file not found for: {preset_id_or_path}"}

    pid = Path(wav_path).stem
    disp = display_name or FOSS_PRESET_METADATA.get(pid, {}).get("name", pid)

    hw_sink = get_hardware_sink()
    if not hw_sink:
        return {"success": False, "error": "No physical audio output device detected"}

    hw_sink_name = hw_sink.get("node_name") or hw_sink.get("label")

    conf_content = generate_filter_chain_conf(wav_path, pid, hw_sink_name)
    with open(FILTER_CHAIN_CONF, "w") as f:
        f.write(conf_content)

    # Restart pipewire-filter-chain service
    subprocess.run(["systemctl", "--user", "restart", "pipewire-filter-chain.service"], capture_output=True)

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
    time.sleep(0.2)

    # Explicit link to hardware playback
    run_cmd(["pw-link", f"{VIRTUAL_PLAYBACK_NAME}:output_FL", f"{hw_sink_name}:playback_FL"])
    run_cmd(["pw-link", f"{VIRTUAL_PLAYBACK_NAME}:output_FR", f"{hw_sink_name}:playback_FR"])
    cleanup_duplicate_links(hw_sink_name)

    # Hot-reload ClickClick if running so keystroke sounds anchor smoothly
    run_cmd(["pkill", "-USR1", "-x", "clickclick_rs"])

    # Save state
    state = {
        "active_profile_id": pid,
        "active_profile_name": disp,
        "wav_path": wav_path,
        "hardware_sink": hw_sink_name,
        "updated_at": time.time()
    }
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

    run_cmd(["notify-send", "-i", "audio-headphones", "SpatialWire 3D Audio", f"Active Profile: {disp}"])
    return {
        "success": True,
        "profile_id": pid,
        "profile_name": disp,
        "virtual_sink_id": vsink_id,
        "hardware_sink": hw_sink_name
    }


def disable_spatial():
    """Disables virtual surround and restores direct DAC stereo output."""
    subprocess.run(["systemctl", "--user", "stop", "pipewire-filter-chain.service"], capture_output=True)

    if os.path.exists(FILTER_CHAIN_CONF):
        try:
            os.remove(FILTER_CHAIN_CONF)
        except Exception:
            pass

    hw_sink = get_hardware_sink()
    if hw_sink:
        run_cmd(["wpctl", "set-default", str(hw_sink["id"])])

    run_cmd(["pkill", "-USR1", "-x", "clickclick_rs"])

    if os.path.exists(STATE_FILE):
        try:
            os.remove(STATE_FILE)
        except Exception:
            pass

    run_cmd(["notify-send", "-i", "audio-headphones", "SpatialWire 3D Audio", "Spatial Surround Disabled → Stereo Direct"])
    return {"success": True, "restored_sink": hw_sink.get("label") if hw_sink else None}


def play_surround_test():
    """Plays an 8-channel directional test audio to verify spatial perception."""
    test_file = os.path.join(REPO_DIR, "assets/test_surround.ogg")
    if not os.path.isfile(test_file):
        test_file = os.path.join(HOME, ".config/pipewire/hrir-repo/test_surround.ogg")

    if not os.path.isfile(test_file):
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
    if not os.path.isfile(src_path) or not src_path.endswith(".wav"):
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
