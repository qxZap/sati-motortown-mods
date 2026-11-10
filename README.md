# Sati's Motor Town mods

Source and automated builds for three Motor Town mods by **Sati** (satigt3).
Each game update, the mods are rebuilt from vanilla by a script rather than by
hand, so they stay correct across patches.

Maintained by **qxZap** for now; Sati joins as a contributor later.

## The mods

| Mod | What it does | Status |
|-----|--------------|--------|
| **Dump to Grain** | The 8 bulk cargos (Sand, Fine Sand, Coal, Iron Ore, Limestone, Limestone Rock, Copper Ore, Copper Concentrate) gain the `Grain` cargo-space type, so they load into grain hoppers (Hobber Lead / Rear) as well as dump trailers. | **built** (0.7.20), pending in-game load test |
| **Atlas 8x8** | All four axles powered (two extra differentials), every axle a lockable diff, and four drive-mode stages — RWD-Open, AWD-Open, RWD-Locked, AWD-Locked — with 3.19 gearing when locked. | in progress |
| **Longhorn Rollback liftable axles** | Lower the rear of the Longhorn Rollback and its UL version. | in progress |

## Building

No game assets are stored here — they belong to the game. The build reads the
vanilla tables from a local Motor Town extract and re-applies each mod's edits,
so a new game version only needs fresh inputs, not new code.

```
python build.py          # build everything that's ready
python build.py dtg      # just Dump to Grain
```

After a Motor Town update: refresh the vanilla extract and the `.usmap`
mappings, then run `build.py` again. Paths are configured by env vars at the top
of `build.py` (they default to the MTLiveMap workspace on the author's machine).

Built paks land in `dist/`.

## Installing (for players)

1. Steam → right-click **Motor Town** → Manage → Browse Local Files.
2. Open `MotorTown/Content/Paks`.
3. Drop the `.pak` into that folder.
4. Launch the game.

> Do not file game bug reports while mods are installed — report mod issues on
> the mod's own page.
