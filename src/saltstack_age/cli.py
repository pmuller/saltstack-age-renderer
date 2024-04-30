import logging
import sys
from argparse import ArgumentParser, ArgumentTypeError, Namespace
from getpass import getpass
from pathlib import Path
from typing import Sequence

from saltstack_age.secure_value import IdentitySecureValue, parse_secure_value

LOGGER = logging.getLogger(__name__)


def normalize_identity(identity: str) -> Path:
    path = Path(identity)

    if path.is_file():
        return path

    raise ArgumentTypeError(f"Identity file does not exist: {identity}")


def parse_cli_arguments(args: Sequence[str] | None = None) -> Namespace:
    parser = ArgumentParser(
        description="Encrypt or decrypt secrets for use with saltstack-age renderer.",
        epilog="When no passphrase or identity is provided, the tool defaults to "
        "passphrase-based encryption and attempts to retrieve the passphrase from "
        "the AGE_PASSPHRASE environment variable.",
    )

    type_parameters = parser.add_mutually_exclusive_group()
    _ = type_parameters.add_argument(
        "-i",
        "--identity",
        type=normalize_identity,
        dest="identities",
        action="append",
        help="The identity file to use. "
        "Can be repeated to encrypt the data for multiple identities or "
        "to try to decrypt it with multiple identities.",
    )
    _ = type_parameters.add_argument(
        "-p",
        "--passphrase-from-stdin",
        action="store_true",
        help="Read passphrase from the standard input",
    )
    _ = type_parameters.add_argument(
        "-P",
        "--passphrase",
        metavar="PASSPHRASE",
        help="Pass passphrase as a CLI argument. ",
    )

    _ = parser.add_argument(
        "-D", "--debug", action="store_true", help="Enable debug logging"
    )

    _ = parser.add_argument(
        "mode",
        choices=("encrypt", "decrypt", "enc", "dec"),
        help="Run the tool in encryption or decryption mode",
    )
    _ = parser.add_argument(
        "value",
        nargs="?",
        help="The value that needs to be encrypted or decrypted. "
        "Will be read from the standard input if not provided.",
    )

    return parser.parse_args(args)


def configure_logging(*, debug: bool):
    level = logging.DEBUG if debug else logging.INFO
    format = "%(levelname)s:%(name)s:%(message)s" if debug else "%(message)s"
    logging.basicConfig(level=level, format=format, style="%")


def get_passphrase(arguments: Namespace) -> str | None:
    passphrase: str | None = None

    if arguments.passphrase_from_stdin:
        passphrase = getpass("Passphrase: ")
    elif arguments.passphrase:
        passphrase = arguments.passphrase

    return passphrase


def main(cli_args: Sequence[str] | None = None) -> None:
    arguments = parse_cli_arguments(cli_args)
    configure_logging(debug=arguments.debug)
    LOGGER.debug("CLI arguments: %r", arguments)
    value = arguments.value or sys.stdin.read()

    if arguments.mode.startswith("enc"):
        # TODO: implement encryption
        raise NotImplementedError
    else:
        secure_value = parse_secure_value(value)
        # TODO: implement support for multiple identities
        decrypted_value = (
            secure_value.decrypt(arguments.identities[0])
            if isinstance(secure_value, IdentitySecureValue)
            else secure_value.decrypt(get_passphrase(arguments))
        )
        LOGGER.info("%s", decrypted_value)
