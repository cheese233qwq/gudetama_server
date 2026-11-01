"""Start the game server using server_config.json (no client patching)."""
import argparse
import sys
from pathlib import Path
from server.connection import read_server_config, SERVER_CONFIG


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=SERVER_CONFIG)
    args = parser.parse_args()
    selected = read_server_config(args.config)
    from server.app import main as serve
    sys.argv = [sys.argv[0], '--host', selected['bind'], '--port', str(selected['port']),
                '--public-origin', selected['origin'], '--state', selected['state'],
                '--log', selected['log']]
    serve()


if __name__ == '__main__':
    main()
