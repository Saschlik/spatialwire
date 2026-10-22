import timeit
import json
import os

STATE_FILE = "test_state.json"
with open(STATE_FILE, "w") as f:
    json.dump({"hardware_sink": "alsa_output.usb-dac"}, f)

def get_hardware_sink_old(nodes):
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

def get_hardware_sink_new4(nodes):
    hw_candidates = []

    for s in nodes:
        if s.get("section") == "sinks":
            name = s.get("node_name", "")
            if "virtual-surround" not in name and "effect_" not in name and "mono_" not in name:
                label = s.get("label", "")
                if "Virtual Surround" not in label:
                    if s.get("default"):
                        return s
                    hw_candidates.append(s)

    if not hw_candidates:
        return None

    # 2. Saved hardware_sink from state.json
    saved_hw = ""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                saved_hw = json.load(f).get("hardware_sink", "")
        except Exception:
            pass

    best_fallback = None

    # Process remaining checks in a single loop
    for s in hw_candidates:
        name = s.get("node_name", "")
        label = s.get("label", "")

        if saved_hw and (name == saved_hw or label == saved_hw):
            return s

        if best_fallback is None:
            name_l = name.lower()
            if "hdmi" not in name_l and "displayport" not in name_l:
                best_fallback = s

    if best_fallback:
        return best_fallback

    return hw_candidates[0]

# Nodes with NO default, so it checks fallback/state
nodes = [
    {"section": "sources", "node_name": "mic"},
    {"section": "sinks", "node_name": "effect_virtual-surround", "label": "Virtual Surround"},
    {"section": "sinks", "node_name": "alsa_output.hdmi-1", "label": "HDMI 1"},
    {"section": "sinks", "node_name": "alsa_output.hdmi-2", "label": "HDMI 2"},
    {"section": "sinks", "node_name": "alsa_output.usb-dac", "label": "USB DAC"},
    {"section": "sinks", "node_name": "alsa_output.pci-analog", "label": "Built-in Analog"},
] * 10

print("Without default:")
print("Old:", get_hardware_sink_old(nodes).get("node_name"))
print("New:", get_hardware_sink_new4(nodes).get("node_name"))

old_time = timeit.timeit(lambda: get_hardware_sink_old(nodes), number=10000)
new_time = timeit.timeit(lambda: get_hardware_sink_new4(nodes), number=10000)

print(f"Old: {old_time:.4f} s")
print(f"New: {new_time:.4f} s")
print(f"Improvement: {((old_time - new_time) / old_time) * 100:.2f}%\n")

# Nodes WITH default
nodes_with_default = [
    {"section": "sources", "node_name": "mic"},
    {"section": "sinks", "node_name": "effect_virtual-surround", "label": "Virtual Surround"},
    {"section": "sinks", "node_name": "alsa_output.hdmi-1", "label": "HDMI 1"},
    {"section": "sinks", "node_name": "alsa_output.hdmi-2", "label": "HDMI 2", "default": True},
    {"section": "sinks", "node_name": "alsa_output.usb-dac", "label": "USB DAC"},
    {"section": "sinks", "node_name": "alsa_output.pci-analog", "label": "Built-in Analog"},
] * 10

print("With default:")
print("Old:", get_hardware_sink_old(nodes_with_default).get("node_name"))
print("New:", get_hardware_sink_new4(nodes_with_default).get("node_name"))

old_time_def = timeit.timeit(lambda: get_hardware_sink_old(nodes_with_default), number=10000)
new_time_def = timeit.timeit(lambda: get_hardware_sink_new4(nodes_with_default), number=10000)

print(f"Old (def): {old_time_def:.4f} s")
print(f"New (def): {new_time_def:.4f} s")
print(f"Improvement (def): {((old_time_def - new_time_def) / old_time_def) * 100:.2f}%")

os.remove(STATE_FILE)
