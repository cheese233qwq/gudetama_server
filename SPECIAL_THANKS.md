# Special Thanks

Special thanks to **[OpenGude](https://github.com/OpenGude)** for the projects
that made this restoration possible:

- **[libgude](https://github.com/OpenGude/libgude)** — the protocol data types
  and binary serialization library used by this server, specifically:
  - `cdio_base.Object` reads and writes binary objects with their type IDs;
    primitive wrappers, arrays and integer-keyed maps preserve wire types.
  - `cdio.Packet` represents game requests; response models such as `UserData`,
    `KitchenwareData`, `GachaResult`, `CupGachaResult` and `SystemMailData`
    provide the original field order and object definitions.
  - `cdio.GameDef` and related definitions decode the archived game settings,
    including recipes, characters, shops, rewards and events.
  - These same serializers encode player-save blobs, reward receipts and
    configuration responses used by the Python server.
- **[cdn-archive](https://github.com/OpenGude/cdn-archive)** — the archived
  game configuration and resources. Download these separately and place the
  archive contents under `resources/`.
- **OpenGude's decompiled client and protocol documentation projects** —
  essential references for this project's client analysis, request/response
  reconstruction, gameplay behavior research, and compatibility fixes.

The server was written by Codex. Its restoration work and analysis build on
OpenGude's protocol library, archived resources and client research.

libgude is copyright © 2022 OpenGude and distributed under the MIT License;
its full license is included at `libgude/LICENSE`.
That license applies to libgude, not to all files in this package or the game
assets. Gudetama and the original game's assets belong to their respective
rights holders. This is an unofficial community compatibility project.
