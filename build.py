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
# The vanilla Atlas 8x4 dump truck made 8x8: drive its two UN-driven front
# axles too, and make every differential lockable.
#
# Vanilla has Differential1 (W4,5) and Differential2 (W6,7) -- the driven rear
# axles -- while the front wheels W0-3 name no differential. So: clone the two
# vanilla diffs into Differential3/Differential4 (each carries the vanilla
# TransmissionComponentName, which is what actually feeds it power), give them
# unique LSDSlotIndex 2/3 (the lock UI keys on the slot -- a collision is why a
# naive clone shows no "lockable" interaction), point the front axles at them,
# and set LinkGearRatio=-1 on each axle's inner wheel (W5/W7 already have it).
# Result: 4 diffs, 4 driven axles, 4 lockable LSDs -- the structure of Sati's
# working 7.18 build. (`vehicle-awd` produced the Biceps-class bug: all axles on
# one wheel pair, an orphan 5th diff, and no transmission link.)
#
# No neighbours needed -- the injector round-trips this blueprint as NormalExport
# from a bare path, so the chain reads/writes the stage file in place.
def _ic(inj_asset, out, *args):
    inject(*args, "--uasset", inj_asset, "--mappings", MAPPINGS, "--output", out)


def atlas_8x8():
    print("[Atlas 8x8]")
    need(VANILLA, "vanilla extract (MT_VANILLA)")
    src = VANILLA / "Cars/Models/Atlas/Atlas_8x4_Dump.uasset"
    need(src, "vanilla Atlas_8x4_Dump.uasset")
    stage = WORK / "Atlas8x8_P/MotorTown/Content/Cars/Models/Atlas"
    if (WORK / "Atlas8x8_P").exists():
        shutil.rmtree(WORK / "Atlas8x8_P")
    stage.mkdir(parents=True)
    a = stage / "Atlas_8x4_Dump.uasset"
    # clone the two front-axle diffs (step 1 reads vanilla, the rest read the stage)
    _ic(src, a, "vehicle-clone-component", "--from", "Differential1_GEN_VARIABLE",
        "--name", "Differential3", "--int", "LSDSlotIndex=2", "--bool", "bAllowLockableLSD=1")
    _ic(a, a, "vehicle-clone-component", "--from", "Differential2_GEN_VARIABLE",
        "--name", "Differential4", "--int", "LSDSlotIndex=3", "--bool", "bAllowLockableLSD=1")
    # the two vanilla diffs become lockable too
    _ic(a, a, "set-component-props", "--export", "Differential1_GEN_VARIABLE", "--bool", "bAllowLockableLSD=1")
    _ic(a, a, "set-component-props", "--export", "Differential2_GEN_VARIABLE", "--bool", "bAllowLockableLSD=1")
    # drive the front axles; inner wheel of each gets LinkGearRatio=-1
    _ic(a, a, "set-component-props", "--export", "Wheel0", "--fname", "DifferentialComponentName=Differential3")
    _ic(a, a, "set-component-props", "--export", "Wheel1", "--fname", "DifferentialComponentName=Differential3", "--float", "LinkGearRatio=-1")
    _ic(a, a, "set-component-props", "--export", "Wheel2", "--fname", "DifferentialComponentName=Differential4")
    _ic(a, a, "set-component-props", "--export", "Wheel3", "--fname", "DifferentialComponentName=Differential4", "--float", "LinkGearRatio=-1")
    # T-key drive modes (Sati, 11 Nov): Jemusi's DiffLockings as the struct template,
    # rear = Diff1/2, front = Diff3/4, low range 3.19 with brake-TCS off like Jemusi's 4L
    rear_open, rear_lock = "Differential1=Open,Differential2=Open", "Differential1=Locked,Differential2=Locked"
    modes = ";".join([
        f"RWD-Open|1|0|{rear_open},Differential3=Disconnect,Differential4=Disconnect",
        f"AWD-Open|1|0|{rear_open},Differential3=Open,Differential4=Open",
        f"RWD-Lock|3.19|1|{rear_lock},Differential3=Disconnect,Differential4=Disconnect",
        f"AWD-Lock|3.19|1|{rear_lock},Differential3=Locked,Differential4=Locked",
    ])
    _ic(a, a, "set-diff-lockings", "--donor", VANILLA / "Cars/Models/Jemusi/Jemusi.uasset", "--modes", modes)
    pack(WORK / "Atlas8x8_P", "satigt3_Atlas8x8_P")


# --- 2. Longhorn Rollback: lowering OPTION on "-" ----------------------------
# The "-" key is the vehicle's LiftAxles list (Atlas_6x2_Tanker: "Axle 3" lifts
# W4/5 by 20). Lowering = both rear axles (W2/3, W4/5) moved up into the body by
# the same amount, so the rear squats for loading. Longhorn_Rollback_UL is a child
# blueprint of Longhorn_Rollback and inherits the list, so only the base ships.
LH_LOWER = os.environ.get("LH_LOWER", "15")   # cm; wheel SpringStroke is 20


def longhorn_liftable():
    print("[Longhorn lowering]")
    need(VANILLA, "vanilla extract (MT_VANILLA)")
    src = VANILLA / "Cars/Models/Longhorn_Rollback/Longhorn_Rollback.uasset"
    need(src, "vanilla Longhorn_Rollback.uasset")
    root = WORK / "LonghornLowering_P"
    if root.exists():
        shutil.rmtree(root)
    stage = root / "MotorTown/Content/Cars/Models/Longhorn_Rollback"
    stage.mkdir(parents=True)
    h = LH_LOWER
    _ic(src, stage / "Longhorn_Rollback.uasset", "set-lift-axles",
        "--donor", VANILLA / "Cars/Models/Atlas/Atlas_6x2_Tanker.uasset",
        "--axles", f"Lower Rear|2={h},3={h},4={h},5={h}")
    pack(root, "satigt3_LonghornLowering_P")


MODS = {"dtg": dump_to_grain, "atlas": atlas_8x8, "longhorn": longhorn_liftable}

if __name__ == "__main__":
    need(INJECTOR, "MTBPInjector.exe (MT_INJECTOR)")
    need(REPAK, "repak.exe (MT_REPAK)")
    need(MAPPINGS, "mappings .usmap (MT_MAPPINGS)")
    which = sys.argv[1:] or list(MODS)
    for name in which:
        MODS[name]()
