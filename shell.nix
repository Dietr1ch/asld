let
  pkgs = import (fetchTarball https://github.com/NixOS/nixpkgs/archive/18.03.tar.gz) {};
in with pkgs; {

  asldEnv = stdenv.mkDerivation {
    name = "asld";

    buildInputs = [
      bash

      libnotify
      xdg_utils

      # Python
      (python36.buildEnv.override {
        extraLibs = with python36Packages; [
          # Tools
          ipython

          # Dependencies
          rdflib
          SPARQLWrapper
          numpy
          matplotlib
          jsonpickle
          psutil
        ];
      })
    ];
  };
}
