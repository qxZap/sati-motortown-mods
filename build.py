#!/usr/bin/env python3
"""Rebuild Sati's Motor Town mods from vanilla, so they stay consistent across
game updates. Re-run after every Motor Town patch: refresh the vanilla extract
and the .usmap mappings, then `python build.py`.

No game assets live in this repo (they are the game's). The build reads the
vanilla tables from your own Motor Town install / extract and re-applies each
mod's edits, so a new game version only needs fresh inputs, not new code.

Config via env vars (defaults assume the MTLiveMap workspace on this machine):
  MT_INJECTOR  MTBPInjector.exe
  MT_REPAK     repak.exe
  MT_MAPPINGS  current .usmap
  MT_VANILLA   vanilla extract root (…/MotorTown/Content)
Outputs to ./dist/*.pak
"""
import os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "build"
DIST = ROOT / "dist"

MTL = Path(os.environ.get("MTLIVEMAP", r"D:/MTLiveMap"))
INJECTOR = Path(os.environ.get("MT_INJECTOR", MTL / "MTBPInjector/bin/Release/net8.0/MTBPInjector.exe"))
REPAK = Path(os.environ.get("MT_REPAK", MTL / "tools/repak.exe"))
MAPPINGS = Path(os.environ.get("MT_MAPPINGS", "D:/MT/MotorTown720T6.usmap"))
VANILLA = Path(os.environ.get("MT_VANILLA", MTL / "vanilla_extract/MotorTown/Content"))


def need(p: Path, what: str):
    if not p.exists():
        sys.exit(f"missing {what}: {p}\n  set its env var or fix the path (see build.py header)")


def inject(*args):
    subprocess.run([str(INJECTOR), *map(str, args)], check=True)


def pack(stage: Path, pak_name: str):
    """repak the staging tree into dist/<pak_name>.pak"""
    DIST.mkdir(exist_ok=True)
    out = DIST / f"{pak_name}.pak"
    if out.exists():
        out.unlink()
    subprocess.run([str(REPAK), "pack", str(stage), str(out)], check=True)
    print(f"  -> {out}")


# --- 3. Dump to Grain -------------------------------------------------------
# The 8 bulk cargos are CargoSpaceType::Dump only; add Grain so they also load
# into grain hoppers (Hobber Lead/Rear). Must patch BOTH Cargos and Cargos_01
# (the game loads both) -- this mirrors Sati's shipped 7.18 build.
DTG_ROWS = ["Sand", "FineSand", "Coal", "IronOre", "Limestone",
            "LimestoneRock", "CopperOre", "CopperConcentrate"]
DTG_TABLES = ["Cargos", "Cargos_01"]


def dump_to_grain():
    print("[Dump to Grain]")
    need(VANILLA, "vanilla extract (MT_VANILLA)")
    stage = WORK / "DumpToGrain_P/MotorTown/Content/DataAsset"
    if (WORK / "DumpToGrain_P").exists():
        shutil.rmtree(WORK / "DumpToGrain_P")
    stage.mkdir(parents=True)
    for tbl in DTG_TABLES:
        for ext in (".uasset", ".uexp"):
            shutil.copy(VANILLA / "DataAsset" / f"{tbl}{ext}", stage / f"{tbl}{ext}")
        for row in DTG_ROWS:
            inject("set-row-array", "--uasset", stage / f"{tbl}.uasset",
                   "--mappings", MAPPINGS, "--row", row, "--field", "CargoSpaceTypes",
                   "--kind", "enum", "--enum-type", "EMTCargoSpaceType",
                   "--values", "EMTCargoSpaceType::Dump,EMTCargoSpaceType::Grain")
    pack(WORK / "DumpToGrain_P", "satigt3_DumpToGrain_P")


# --- 1. Atlas 8x8 -----------------------------------------------------------
# The vanilla Atlas 8x4 dump truck made 8x8: all four axles driven, every
# differential lockable. vehicle-awd rewires the drivetrain (front/rear + one
# 2-wheel diff per extra axle) and --lockable sets bAllowLockableLSD on each.
# Only the modified blueprint ships -- it references the same vanilla meshes, so
# no tables and no DataTable-framework routing are needed.
#
# The verb MUST read the vanilla blueprint in place (beside its vanilla
# neighbours) or UAssetAPI parses it as RawExport and the edit silently no-ops;
# it writes the modified .uasset + .uexp into the stage.
def atlas_8x8():
    print("[Atlas 8x8]")
    need(VANILLA, "vanilla extract (MT_VANILLA)")
    rel = "Cars/Models/Atlas/Atlas_8x4_Dump"
    src = VANILLA / f"{rel}.uasset"
    need(src, "vanilla Atlas_8x4_Dump.uasset")
    stage = WORK / "Atlas8x8_P/MotorTown/Content/Cars/Models/Atlas"
    if (WORK / "Atlas8x8_P").exists():
        shutil.rmtree(WORK / "Atlas8x8_P")
    stage.mkdir(parents=True)
    inject("vehicle-awd", "--uasset", src, "--mappings", MAPPINGS,
           "--each-set-awd", "--lockable", "--output", stage / "Atlas_8x4_Dump.uasset")
    pack(WORK / "Atlas8x8_P", "satigt3_Atlas8x8_P")


# --- 2. Longhorn Rollback: lower the rear -----------------------------------
# Drop the rear of Longhorn_Rollback and its UL variant by setting a negative
# DefaultRideHeightAdjust on the rear wheels (MHWheelComponent). Negative lowers,
# positive raises. First-pass value/wheel-set -- tune in game.
# Like Atlas, the verb reads each blueprint in place (beside its vanilla
# neighbours) and writes the modified .uasset + .uexp into the stage.
LH_VEHICLES = ["Longhorn_Rollback", "Longhorn_Rollback_UL"]
LH_REAR_WHEELS = "Wheel2,Wheel3,Wheel4,Wheel5"   # the four rear wheels of the 6-wheeler
LH_ADJUST = os.environ.get("LH_ADJUST", "-5")    # cm; negative = lower


def longhorn_liftable():
    print("[Longhorn lower-rear]")
    need(VANILLA, "vanilla extract (MT_VANILLA)")
    stage = WORK / "LonghornLowered_P/MotorTown/Content/Cars/Models/Longhorn_Rollback"
    if (WORK / "LonghornLowered_P").exists():
        shutil.rmtree(WORK / "LonghornLowered_P")
    stage.mkdir(parents=True)
    for v in LH_VEHICLES:
        src = VANILLA / f"Cars/Models/Longhorn_Rollback/{v}.uasset"
        need(src, f"vanilla {v}.uasset")
        inject("vehicle-ride-height", "--uasset", src, "--mappings", MAPPINGS,
               "--wheels", LH_REAR_WHEELS, "--adjust", LH_ADJUST,
               "--output", stage / f"{v}.uasset")
    pack(WORK / "LonghornLowered_P", "satigt3_LonghornLowered_P")


MODS = {"dtg": dump_to_grain, "atlas": atlas_8x8, "longhorn": longhorn_liftable}

if __name__ == "__main__":
    need(INJECTOR, "MTBPInjector.exe (MT_INJECTOR)")
    need(REPAK, "repak.exe (MT_REPAK)")
    need(MAPPINGS, "mappings .usmap (MT_MAPPINGS)")
    which = sys.argv[1:] or list(MODS)
    for name in which:
        MODS[name]()
