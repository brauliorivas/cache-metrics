{
  description = "A very basic flake";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=25.11";
  };

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};

      libCacheSim = pkgs.stdenv.mkDerivation rec {
        pname = "libCacheSim";
        version = "0.3.2";
        src = pkgs.fetchFromGitHub {
          owner = "1a1a11a";
          repo = "libCacheSim";
          rev = "v${version}";
          hash = "sha256-wN1r2e/Wmu7weBCTgGJYRiAEfstUP7KWSQiPir/MsPM=";
        };
        buildInputs = [
          pkgs.glib
        ];
        nativeBuildInputs = [
          pkgs.pkg-config
          pkgs.ninja
          pkgs.cmake
          pkgs.zstd
        ];
      };
      stackDistance = pkgs.stdenv.mkDerivation {
        pname = "stack-distance";
        version = "v1.0.0";
        src = pkgs.fetchFromGitHub {
          owner = "jcipar";
          repo = "stack-distance";
          rev = "master";
          hash = "sha256-tD3l8eczpSId0EtLPzmeDQ3K5+6VK2ZG8gQCiRy1/r0=";
        };
        nativeBuildInputs = [ pkgs.clang ];
        installPhase = ''
          mkdir -p $out/bin
          cp stack-distance $out/bin
        '';
      };
    in
    {
      devShells.${system}.default = pkgs.stdenv.mkDerivation {
        pname = "dev-env";
        version = "v1.0.0";
        buildInputs = [
          pkgs.pkg-config
          pkgs.bear
          pkgs.llvmPackages_20.clang-tools
          pkgs.llvmPackages_20.clang
          pkgs.zstd
          pkgs.glib
          pkgs.python313
          libCacheSim
          stackDistance
        ];
        shellHook = ''
          export LD_LIBRARY_PATH=${pkgs.glib.out}/lib:${pkgs.stdenv.cc.cc.lib}/lib:$LD_LIBRARY_PATH
        '';
      };
    };
}
