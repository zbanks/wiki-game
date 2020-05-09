# wiki-game
Guess the Wikipedia article from just the Table of Contents.

[**Available to play here!**](https://zbanks.github.io/wiki-game/)

Credit to [xer0a](https://zyxyvy.wordpress.com/2019/11/03/fun-wikipedia-activity/) for the original idea.

## Contributing 

These are the steps for contributing a puzzle through a pull request, which allows zbanks or others to add the puzzle without being spoiled.

You can also reach out to zbanks directly with a Wikipedia title, and he can add it to the list and give you credit.

### Adding a Puzzle

Use `wiki_game.py` to append a new puzzle to `puzzles.txt` using a Wikipedia URL. You can optionally name yourself as a contributor for credit.

```
$ ./wiki_game.py add --contributor zbanks "https://en.wikipedia.org/wiki/Test"
```

### Rebuilding the Webpage

Once you've added your puzzles, you can rebuild the webpage that contains all the puzzles, `docs/index.html`:

```
$ ./wiki_game.py generate
```

After doing this you can commit, push, and [submit a pull request](https://github.com/zbanks/wiki-game/compare) to merge your changes in.

