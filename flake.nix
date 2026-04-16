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
          libCacheSim
        ];
        shellHook = ''
          export LD_LIBRARY_PATH=${pkgs.glib.out}/lib:$LD_LIBRARY_PATH
        '';
      };
    };
}
