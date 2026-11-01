<div align="center">

# 🍳 Gudetama Server

**A server for Gudetama Tap 3**

</div>

---

## 📖 About

This server was written by Codex, building on [OpenGude](https://github.com/OpenGude) projects.

> [!WARNING]
> Bugs may remain, and some features have not yet been restored.
> The AR camera may crash on some Android/iOS devices.

## 📋 Requirements

- Python **3.10+**
- The full [OpenGude resource archive](https://github.com/OpenGude/cdn-archive)

## 🚀 Quick Start

### 1️⃣ Prepare resources

Download the full [OpenGude resource archive](https://github.com/OpenGude/cdn-archive) and put its **contents** in `resources/` beside this README:

```text
resources/
└── static/
    ├── setting/
    │   ├── setting.dat.6045.34
    │   ├── setting.dat.en.6045.34
    │   ├── setting.dat.cn.6045.34
    │   ├── setting.dat.ko.6045.34
    │   └── setting.dat.tw.6045.34
    └── rsrc/
        └── ... # The complete resource tree
```

> [!IMPORTANT]
> Download real files, **not Git LFS pointers**. All five settings files are required.

> [!WARNING]
> The bundled `resources/static/` folder contains only selected essential files extracted from the APK.
> **You must download the complete OpenGude resource archive separately.**
> When merging folders, keep the bundled files that are absent from the downloaded archive.

### 2️⃣ Configure the address

In `server_config.json`, change the existing `public_origin` field to your PC’s LAN address. For example:

```json
"public_origin": "http://192.168.1.100:8080"
```

Keep the other configuration fields unchanged.

> [!NOTE]
> Clients must already use the same address.
> Changing this file does **not** patch installed clients.

### 3️⃣ Install and start

From the extracted release folder, run:

```sh
python -m pip install -r server/requirements.txt
python setup_server.py
python start_server.py
```

Run `setup_server.py` during initial setup. It preserves existing saves.

### 4️⃣ Start the admin page

In another terminal, run:

```sh
python start_admin.py
```

Then open <http://127.0.0.1:8081> and paste the token printed in that terminal.

- 🖥️ Open the admin page **on the server PC**.
- ⏹️ Press `Ctrl+C` in each terminal to stop its service.

## 📁 Data & Files

| Item | Location |
| --- | --- |
| Saves | `save/accounts.sqlite3` |
| Logs | `log/server.log` |

Both paths are relative to the release root, unless changed in your configuration. Setup preserves existing saves.

## ⬆️ Upgrading

1. **Stop both services** before upgrading or backing up.
2. Back up your save directory and configuration.
3. Preserve the `save/` and `log/` folders and your configuration when replacing server files.
4. When upgrading an older release, retain its configured save path or move its save directory into `save/` after stopping both services. Update the configuration if the path changes.

> [!IMPORTANT]
> If SQLite `-wal` or `-shm` files remain beside the database, keep them with the database when backing up or moving the save directory.

## 🙏 Credits

See [Special Thanks](SPECIAL_THANKS.md) for OpenGude credits and the included [`libgude/LICENSE`](libgude/LICENSE).