#!/usr/bin/env python3
"""
SpatialWire Settings GUI (Standalone GNOME / Libadwaita App)
Modern configuration interface for the PipeWire 7.1 Virtual Surround & Binaural HRTF Engine.
"""

import os
import sys
import subprocess
import json
import re

# ── Dynamic Typelib Environment Setup ──────────────────────────────────────────
if "GI_TYPELIB_PATH" not in os.environ:
    wrapper_path = "/run/current-system/sw/bin/balonix-settings"
    if os.path.exists(wrapper_path):
        try:
            with open(wrapper_path, "rb") as f:
                content = f.read().decode("latin1", errors="ignore")
            m_gi = re.search(r"(/nix/store/[^\x00]+libadwaita[^\x00]+girepository-1\.0)", content)
            m_mod = re.search(r"(/nix/store/[^\x00]+dconf[^\x00]+gio/modules)", content)
            m_pix = re.search(r"(/nix/store/[^\x00]+librsvg[^\x00]+loaders\.cache)", content)
            m_xdg = re.search(r"(/nix/store/[^\x00]+gsettings-desktop-schemas[^\x00]+gtk4[^\x00]+)", content)
            if m_gi:
                os.environ["GI_TYPELIB_PATH"] = m_gi.group(1)
            if m_mod:
                os.environ["GIO_EXTRA_MODULES"] = m_mod.group(1)
            if m_pix:
                os.environ["GDK_PIXBUF_MODULE_FILE"] = m_pix.group(1)
            if m_xdg:
                os.environ["XDG_DATA_DIRS"] = m_xdg.group(1) + ":" + os.environ.get("XDG_DATA_DIRS", "/usr/share")
        except Exception:
            pass

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
sys.path.insert(0, os.path.join(REPO_DIR, "src"))

import engine


class SpatialWireApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.saschlik.SpatialWire",
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = SpatialWireWindow(application=self)
        win.present()


class SpatialWireWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("SpatialWire")
        self.set_default_size(680, 740)
        self._updating = False

        self.presets = engine.list_all_presets()
        self.preset_ids = [p["id"] for p in self.presets]

        # Layout
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        # HeaderBar
        header = Adw.HeaderBar()
        title_widget = Adw.WindowTitle(
            title="SpatialWire 3D Audio",
            subtitle="PipeWire 7.1 Binaural HRTF Surround"
        )
        header.set_title_widget(title_widget)

        refresh_btn = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_btn.set_tooltip_text("Status aktualisieren")
        refresh_btn.connect("clicked", lambda b: self.refresh_ui())
        header.pack_end(refresh_btn)

        content_box.append(header)

        # Toast Overlay for feedback
        self.toast_overlay = Adw.ToastOverlay()

        # Scrolled content with Adw.Clamp
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        clamp = Adw.Clamp()
        clamp.set_maximum_size(700)
        clamp.set_margin_top(20)
        clamp.set_margin_bottom(24)
        clamp.set_margin_start(16)
        clamp.set_margin_end(16)

        page = Adw.PreferencesPage()

        # ── Group 1: Master Status & Toggle ───────────────────────────────────
        grp_status = Adw.PreferencesGroup()
        grp_status.set_title("Surround-Engine")
        grp_status.set_description("Echtzeit-Faltung (Convolver) über native PipeWire Realtime-Threads.")

        self.master_switch = Adw.SwitchRow()
        self.master_switch.set_use_markup(False)
        self.master_switch.set_title("7.1 Virtual Surround & HRTF")
        self.master_switch.set_subtitle("Binauraler 3D-Kopfhörer-Raumklang")
        self.master_switch.set_icon_name("audio-headphones-symbolic")
        self.master_switch.connect("notify::active", self.on_master_toggled)
        grp_status.add(self.master_switch)

        self.status_badge_row = Adw.ActionRow()
        self.status_badge_row.set_title("Engine-Zustand")
        self.status_badge_row.set_subtitle("Wird ermittelt...")
        self.status_indicator = Gtk.Label(label="● Inaktiv")
        self.status_indicator.add_css_class("dim-label")
        self.status_badge_row.add_suffix(self.status_indicator)
        grp_status.add(self.status_badge_row)

        self.hw_target_row = Adw.ActionRow()
        self.hw_target_row.set_title("Physische Soundkarte")
        self.hw_target_row.set_subtitle("Kein Ausgabegerät erkannt")
        self.hw_target_row.set_icon_name("audio-card-symbolic")
        grp_status.add(self.hw_target_row)

        page.add(grp_status)

        # ── Group 2: HRTF Profile Selection ──────────────────────────────────
        grp_profiles = Adw.PreferencesGroup()
        grp_profiles.set_title("HRTF Akustik-Profile")
        grp_profiles.set_description("Wähle das binaurale Impulsantwort-Modell für deine Kopfhörer.")

        self.profile_combo = Adw.ComboRow()
        self.profile_combo.set_title("Aktives Profil")
        self.profile_combo.set_icon_name("audio-speakers-symbolic")
        profile_names = [f"{p['name']} ({p['category']})" for p in self.presets]
        self.profile_combo.set_model(Gtk.StringList.new(profile_names))
        self.profile_combo.connect("notify::selected", self.on_profile_selected)
        grp_profiles.add(self.profile_combo)

        # Profile Details Row
        self.profile_desc_row = Adw.ActionRow()
        self.profile_desc_row.set_title("Klangcharakteristik")
        self.profile_desc_row.set_subtitle("Profil auswählen für Beschreibung")
        grp_profiles.add(self.profile_desc_row)

        page.add(grp_profiles)

        # ── Group 3: Testing & Import ─────────────────────────────────────────
        grp_tools = Adw.PreferencesGroup()
        grp_tools.set_title("Audio-Werkzeuge & Diagnose")
        grp_tools.set_description("Surround-Positionierung testen und eigene HeSuVi-Messungen importieren.")

        test_row = Adw.ActionRow()
        test_row.set_title("3D-Positionierungstest abspielen")
        test_row.set_subtitle("8-Kanal Testsignal (Vorne, Center, Hinten, Surround) abhören")
        test_btn = Gtk.Button(label="Testen")
        test_btn.set_icon_name("media-playback-start-symbolic")
        test_btn.set_valign(Gtk.Align.CENTER)
        test_btn.add_css_class("suggested-action")
        test_btn.connect("clicked", self.on_test_clicked)
        test_row.add_suffix(test_btn)
        test_row.set_activatable_widget(test_btn)
        grp_tools.add(test_row)

        import_row = Adw.ActionRow()
        import_row.set_title("HeSuVi WAV importieren")
        import_row.set_subtitle("7- oder 14-Kanal WAV Impulsantwort zu Presets hinzufügen")
        import_btn = Gtk.Button(label="Importieren...")
        import_btn.set_icon_name("document-open-symbolic")
        import_btn.set_valign(Gtk.Align.CENTER)
        import_btn.connect("clicked", self.on_import_clicked)
        import_row.add_suffix(import_btn)
        import_row.set_activatable_widget(import_btn)
        grp_tools.add(import_row)

        page.add(grp_tools)

        # ── Group 4: Performance & Hardware Specs ─────────────────────────────
        grp_specs = Adw.PreferencesGroup()
        grp_specs.set_title("System-Architektur")

        row_lat = Adw.ActionRow()
        row_lat.set_title("User-Space Latenz")
        row_lat.set_subtitle("0 ms (Kernel Real-Time Priority Prio 88 / Nice -11)")
        grp_specs.add(row_lat)

        row_conv = Adw.ActionRow()
        row_conv.set_title("Convolver-Matrix")
        row_conv.set_subtitle("16 parallele SPA-Convolver Nodes (FL, FR, FC, LFE, RL, RR, SL, SR)")
        grp_specs.add(row_conv)

        page.add(grp_specs)

        clamp.set_child(page)
        scrolled.set_child(clamp)
        self.toast_overlay.set_child(scrolled)
        content_box.append(self.toast_overlay)

        self.set_content(content_box)

        # Initial UI population
        self.refresh_ui()

    def show_toast(self, message):
        toast = Adw.Toast(title=message)
        self.toast_overlay.add_toast(toast)

    def refresh_ui(self):
        self._updating = True
        try:
            status = engine.get_current_status()
            is_active = status["active"]
            self.master_switch.set_active(is_active)

            if is_active:
                self.status_badge_row.set_subtitle(f"Aktiviert ({status['active_profile_name']})")
                self.status_indicator.set_label("● Aktiv")
                self.status_indicator.remove_css_class("dim-label")
                self.status_indicator.add_css_class("success")
            else:
                self.status_badge_row.set_subtitle("Inaktiv (Direkte Stereo-Soundkartenausgabe)")
                self.status_indicator.set_label("○ Inaktiv")
                self.status_indicator.remove_css_class("success")
                self.status_indicator.add_css_class("dim-label")

            hw_label = status.get("hardware_sink_label", "Default Audio Sink")
            self.hw_target_row.set_subtitle(hw_label)

            # Match active profile in combo
            active_pid = status.get("active_profile_id", "").lower()
            if active_pid in self.preset_ids:
                idx = self.preset_ids.index(active_pid)
                self.profile_combo.set_selected(idx)
                self.update_profile_description(idx)
            elif self.preset_ids:
                idx = self.profile_combo.get_selected()
                self.update_profile_description(idx)
        finally:
            self._updating = False

    def update_profile_description(self, idx):
        if 0 <= idx < len(self.presets):
            p = self.presets[idx]
            ch_info = f"{p['channels']}-Kanal HRIR"
            self.profile_desc_row.set_title(f"{p['name']} ({ch_info})")
            self.profile_desc_row.set_subtitle(p["description"])

    def on_master_toggled(self, row, param):
        if self._updating:
            return

        active = self.master_switch.get_active()
        if active:
            idx = self.profile_combo.get_selected()
            if 0 <= idx < len(self.presets):
                pid = self.presets[idx]["id"]
                res = engine.enable_profile(pid)
                if res.get("success"):
                    self.show_toast(f"Surround aktiviert: {res['profile_name']}")
                else:
                    self.show_toast(f"Fehler: {res.get('error')}")
                    self.master_switch.set_active(False)
        else:
            engine.disable_spatial()
            self.show_toast("Surround deaktiviert (Direkter Stereo-Modus)")

        self.refresh_ui()

    def on_profile_selected(self, row, param):
        idx = row.get_selected()
        self.update_profile_description(idx)

        if self._updating:
            return

        if self.master_switch.get_active() and 0 <= idx < len(self.presets):
            pid = self.presets[idx]["id"]
            res = engine.enable_profile(pid)
            if res.get("success"):
                self.show_toast(f"Profil gewechselt: {res['profile_name']}")
            else:
                self.show_toast(f"Fehler: {res.get('error')}")
            self.refresh_ui()

    def on_test_clicked(self, btn):
        res = engine.play_surround_test()
        if res.get("success"):
            self.show_toast("3D-Positionierungstest wird abgespielt...")
        else:
            self.show_toast(f"Fehler beim Abspielen: {res.get('error')}")

    def on_import_clicked(self, btn):
        dialog = Gtk.FileDialog()
        dialog.set_title("HeSuVi 7/14-Kanal WAV auswählen")

        filter_wav = Gtk.FileFilter()
        filter_wav.set_name("WAV Audio (*.wav)")
        filter_wav.add_pattern("*.wav")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_wav)
        dialog.set_filters(filters)

        def on_open_finished(dialog, result):
            try:
                gfile = dialog.open_finish(result)
                if gfile:
                    path = gfile.get_path()
                    res = engine.import_custom_wav(path)
                    if res.get("success"):
                        self.show_toast(f"Profil importiert: {res['profile_id']}")
                        # Reload presets
                        self.presets = engine.list_all_presets()
                        self.preset_ids = [p["id"] for p in self.presets]
                        profile_names = [f"{p['name']} ({p['category']})" for p in self.presets]
                        self.profile_combo.set_model(Gtk.StringList.new(profile_names))
                        # Select newly imported
                        if res["profile_id"] in self.preset_ids:
                            self.profile_combo.set_selected(self.preset_ids.index(res["profile_id"]))
                    else:
                        self.show_toast(f"Import fehlgeschlagen: {res.get('error')}")
            except Exception as e:
                self.show_toast(f"Abgebrochen oder Fehler: {e}")

        dialog.open(self, None, on_open_finished)


def main():
    app = SpatialWireApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
