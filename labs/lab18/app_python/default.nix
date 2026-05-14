{ pkgs ? import <nixpkgs> {} }:

let
  pythonEnv = pkgs.python3.withPackages (ps: [
    ps.flask
    ps.gunicorn
    ps."python-json-logger"
    ps."prometheus-client"
  ]);
in
pkgs.stdenvNoCC.mkDerivation rec {
  pname = "devops-info-service";
  version = "1.0.0";

  src = ./.;
  nativeBuildInputs = [ pkgs.makeWrapper ];
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    mkdir -p $out/app $out/bin
    cp app.py $out/app/app.py

    makeWrapper ${pythonEnv}/bin/gunicorn $out/bin/devops-info-service \
      --add-flags "--chdir $out/app" \
      --add-flags "--bind ''${HOST:-0.0.0.0}:''${PORT:-8080}" \
      --add-flags "app:app" \
      --set-default DEBUG "False" \
      --set-default VERSION "${version}" \
      --set-default VISITS_FILE "/tmp/devops-info-service/visits"

    runHook postInstall
  '';

  meta = with pkgs.lib; {
    description = "Reproducible build for the DevOps Info Service";
    mainProgram = "devops-info-service";
    license = licenses.mit;
    platforms = platforms.unix;
  };
}