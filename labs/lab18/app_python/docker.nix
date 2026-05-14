{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";
  created = "1970-01-01T00:00:01Z";

  contents = [ app ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    Env = [
      "HOST=0.0.0.0"
      "PORT=8080"
      "DEBUG=False"
      "VERSION=1.0.0"
      "VISITS_FILE=/data/visits"
    ];
    ExposedPorts = {
      "8080/tcp" = {};
    };
    WorkingDir = "/";
  };
}