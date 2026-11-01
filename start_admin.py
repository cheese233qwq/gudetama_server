"""Start the loopback admin against the same configured save as the game server."""
import argparse
import sys
from pathlib import Path
from server.connection import read_server_config, SERVER_CONFIG


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=SERVER_CONFIG)
    parser.add_argument('--port', type=int, default=8081)
    args = parser.parse_args()
    selected = read_server_config(args.config)
    from server.admin import main as serve
    sys.argv = [sys.argv[0], '--state', selected['state'], '--port', str(args.port)]
    serve()


if __name__ == '__main__':
    main()
