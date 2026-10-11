{
  description = "Native PipeWire 7.1 Virtual Surround & Binaural HRTF Convolver System";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          pygobject3
        ]);

        spatialwire = pkgs.stdenv.mkDerivation {
          pname = "spatialwire";
          version = "1.0.0";
          src = ./.;

          nativeBuildInputs = with pkgs; [
            wrapGAppsHook4
            gobject-introspection
          ];

          buildInputs = with pkgs; [
            gtk4
            libadwaita
            pipewire
            pythonEnv
          ];

          installPhase = ''
            mkdir -p $out/bin
            mkdir -p $out/share/spatialwire/presets
            mkdir -p $out/share/spatialwire/assets
            mkdir -p $out/share/spatialwire/src
            mkdir -p $out/share/applications

            cp -r presets/* $out/share/spatialwire/presets/
            cp -r assets/* $out/share/spatialwire/assets/
            cp -r src/* $out/share/spatialwire/src/

            cp ui/com.github.saschlik.SpatialWire.desktop $out/share/applications/

            cp bin/spatialwire $out/bin/spatialwire
            cp ui/spatialwire_gui.py $out/bin/spatialwire-settings

            chmod +x $out/bin/spatialwire $out/bin/spatialwire-settings
          '';

          meta = with pkgs.lib; {
            description = "High-performance PipeWire 7.1 Virtual Surround and Binaural HRTF Convolver";
            homepage = "https://github.com/saschlik/spatialwire";
            license = licenses.mit;
            platforms = platforms.linux;
            mainProgram = "spatialwire";
          };
        };
      in
      {
        packages.default = spatialwire;
        packages.spatialwire = spatialwire;

        apps.default = flake-utils.lib.mkApp {
          drv = spatialwire;
        };

        devShells.default = pkgs.mkShell {
          nativeBuildInputs = with pkgs; [
            wrapGAppsHook4
            gobject-introspection
          ];
          buildInputs = with pkgs; [
            gtk4
            libadwaita
            pipewire
            pythonEnv
          ];
        };
      }
    );
}
