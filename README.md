# Sati's Motor Town mods

Source and automated builds for three Motor Town mods by **Sati** (satigt3).
Each game update, the mods are rebuilt from vanilla by a script rather than by
hand, so they stay correct across patches.

Repo: https://github.com/qxZap/sati-motortown-mods

Maintained by **qxZap** for now; Sati joins as a contributor later.

## The mods

| Mod | What it does | Status |
|-----|--------------|--------|
| **Dump to Grain** | The 8 bulk cargos (Sand, Fine Sand, Coal, Iron Ore, Limestone, Limestone Rock, Copper Ore, Copper Concentrate) gain the `Grain` cargo-space type, so they load into grain hoppers (Hobber Lead / Rear) as well as dump trailers. | **working** on 0.7.20 (tested by Sati) |
| **Atlas 8x8** | The vanilla Atlas 8x4 dump truck made 8x8: the two front axles are driven too (own differentials), all four differentials lockable (listed as Front LSD 1–2, Rear LSD 1–2), and a drive-mode switch on `T`: **RWD-Open**, **AWD-Open**, **RWD-Lock** and **AWD-Lock** (the Lock modes use the 3.19 low range, like Jemusi/Brutus). | **working** on 0.7.20 (tested by Sati) |
| **Longhorn Rollback lowering** | Pressing `-` lowers the rear: both rear axles move up 15 cm into the body (the same axle-lift system as the Atlas tanker). The underlift variant inherits it. | **working** on 0.7.20 (tested by Sati) |

## Building

No game assets are stored here — they belong to the game. The build reads the
vanilla tables from a local Motor Town extract and re-applies each mod's edits,
so a new game version only needs fresh inputs, not new code.

```
python build.py          # build everything that's ready
python build.py dtg      # just Dump to Grain (also: atlas, longhorn)
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
