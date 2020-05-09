#!/usr/bin/env python3

from base64 import b64encode, b64decode
from pathlib import Path
import argparse
import html
import json
import random
import re

from bs4 import BeautifulSoup
import requests

from typing import Any, Optional, Iterable, Tuple, List

Puzzle = Any

BASE_PATH = Path(__file__).absolute().parent
DEFAULT_OUTPUT_PATH = BASE_PATH / "docs/index.html"
DEFAULT_PUZZLE_PATH = BASE_PATH / "puzzles.txt"

ENCODE_KEYS = {"title", "url", "censor"}
CENSOR_TEXT = "█" * 8


def puzzle_encode(obj: Puzzle, encode_keys: Optional[Iterable[str]] = None) -> bytes:
    if encode_keys is None:
        encode_keys = ENCODE_KEYS
    encoded_obj = obj.copy()
    # Add a version key
    encoded_obj["v"] = 1
    for key in encode_keys:
        if key in encoded_obj:
            plaintext = encoded_obj.pop(key).encode("utf-8")
            # The salt helps prevent similar titles from containing similar substrings
            salt = random.randint(0, 255)
            ciphertext = bytes([salt] + [salt ^ b for b in plaintext])
            encoded_obj["#" + key] = b64encode(ciphertext).decode("utf-8")
    return json.dumps(encoded_obj, sort_keys=True).encode("utf-8")


def puzzle_decode(obj_str: bytes) -> Puzzle:
    obj = json.loads(obj_str.decode("utf-8"))
    assert obj["v"] == 1, "Only 'v1'-encoded puzzles are supported"
    encoded_keys = [k for k in obj.keys() if k[0] == "#"]
    for key in encoded_keys:
        ciphertext = b64decode(obj.pop(key))
        salt = ciphertext[0]
        plaintext = bytes([salt ^ b for b in ciphertext[1:]]).decode("utf-8")
        obj[key[1:]] = plaintext
    return obj


def get_puzzles(path: Path = DEFAULT_PUZZLE_PATH) -> Iterable[Puzzle]:
    with path.open("rb") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith(b"#"):
                continue
            yield puzzle_decode(line)


def append_puzzle(puzzle: Puzzle, path: Path = DEFAULT_PUZZLE_PATH):
    with path.open("ab") as f:
        f.write(puzzle_encode(puzzle) + b"\n")


def parse_url(url: str) -> Tuple[str, List[Tuple[str, str]]]:
    page_text = requests.get(url).text
    soup = BeautifulSoup(page_text, "lxml")
    title = soup.find("h1").get_text()
    contents = soup.find("div", class_="toc")
    links = []
    for a in contents.find_all("a"):
        number = a.find("span", class_="tocnumber").get_text()
        text = a.find("span", class_="toctext").get_text()
        links.append((number, text))
    return title, links


def apply_censor(text: str, censor: Optional[str]) -> str:
    if censor is None:
        return text
    return re.sub(censor, CENSOR_TEXT, text, flags=re.IGNORECASE)


def generate(puzzle_path: Path, output_path: Path, verbose: bool = False):
    used_titles = set()
    with output_path.open("w") as f:
        f.write(
            """<!doctype html>
        <html>
        <head>
            <style>
                body {
                    font-family: sans-serif;
                }
                .container {
                    display: flex;
                    flex-wrap: wrap;
                }
                .puzzle {
                    background-color: #f8f9fa;
                    border: 1px solid #a2a9b1;
                    padding: 12px;
                    display: inline-table;
                    line-height: 1.6;
                    margin: 1em;
                }
                .header {
                    text-align: center;
                }
                h2 {
                    display: inline;
                    border: 0;
                    padding: 0;
                    font-size: 100%;
                    font-weight: bold;
                }
                ul {
                    list-style-image: none;
                    list-style-type: none;
                    margin: 0.3em 0;
                    padding: 0;
                }
                li {
                    margin-bottom: 0.1em;
                }
                .toctext, a, a:visited {
                    color: #0645ad;
                    text-decoration: none;
                }
                .toctext:hover, a:hover {
                    text-decoration: underline;
                }
                .depth-0 { margin-left: 0em; }
                .depth-1 { margin-left: 2em; }
                .depth-2 { margin-left: 4em; }
                .depth-3 { margin-left: 6em; }
                .depth-4 { margin-left: 8em; }
                .depth-5 { margin-left: 10em; }
            </style>
        </head>
        <body>
        <div class="container">
        """
        )
        for i, puzzle in enumerate(get_puzzles(puzzle_path)):
            index = i + 1
            title, contents = parse_url(puzzle["url"])
            if verbose:
                print("Generating puzzle #{} '{}'".format(index, title))
            else:
                print("Generating puzzle #{}".format(index))
            if title in used_titles:
                print("Duplicate puzzle #{}".format(index))
            used_titles.add(title)

            censor = puzzle.get("censor")
            contributor = puzzle.get("contributor")
            byline = ", by {}".format(contributor) if contributor is not None else ""

            f.write(
                "<div class='puzzle' title='#{}{}'>".format(index, html.escape(byline))
            )
            f.write(
                " <div class='header'><h2>Contents</h2> [<span class='toctext'>hide</span>]</div>\n"
            )
            f.write(" <ul>\n")
            for number, text in contents:
                depth = number.count(".")
                text = apply_censor(text, censor)
                f.write("<li>")
                f.write(
                    " <span class='tocnumber depth-{}'>{}</span>".format(
                        depth, html.escape(number)
                    )
                )
                f.write(" <span class='toctext'>{}</span>".format(html.escape(text)))
                f.write("</li>\n")
            f.write(" </ul>\n")
            f.write("</div>\n")
        f.write("</div>\n")
        f.write("<div class='puzzle'>\n")
        f.write(
            " <a href='https://github.com/zbanks/wiki-game'>Fork me on Github</a>\n"
        )
        f.write("</div>\n")
        f.write("</body></html>\n")


def add(
    puzzle_path: Path,
    url: str,
    contributor: Optional[str] = None,
    censor: Optional[str] = None,
):
    title, _contents = parse_url(url)
    print("Adding puzzle '{}' to {}".format(title, puzzle_path))
    puzzle = {
        "url": url,
        "title": title,
    }
    if contributor is not None:
        puzzle["contributor"] = contributor
    if censor is not None:
        puzzle["censor"] = censor
    append_puzzle(puzzle, path=puzzle_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Include log messages that may have spoilers",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_PUZZLE_PATH,
        help="Path to input puzzles.txt file to read or modify",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="(required)")

    generate_parser = subparsers.add_parser("generate", help="Generate HTML")
    generate_parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to write generated HTML file",
    )

    add_parser = subparsers.add_parser(
        "add", help="Add a new puzzle to the puzzles.txt file"
    )
    add_parser.add_argument(
        "-C", "--contributor", required=False, help="How you want to be acknowledged"
    )
    add_parser.add_argument(
        "-X",
        "--censor",
        help="Censor a word or phrase from the table of contents, if it gives too much information",
    )
    add_parser.add_argument("url", help="URL to the Wikipedia page to add")

    args = parser.parse_args()
    if args.subcommand == "generate":
        generate(puzzle_path=args.input, output_path=args.output, verbose=args.verbose)
    elif args.subcommand == "add":
        add(
            puzzle_path=args.input,
            url=args.url,
            contributor=args.contributor,
            censor=args.censor,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
