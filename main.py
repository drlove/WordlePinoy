import flet as ft
import random
import tempfile
import os

WORD_LENGTH = 5
MAX_GUESSES = 6
WORDS_FILE = "words.txt"


def load_words():
    """Load words from words.txt that match WORD_LENGTH. Return list and set."""
    if not os.path.exists(WORDS_FILE):
        return [], set()
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        lines = [ln.strip().lower() for ln in f]
    words = [w for w in lines if len(w) == WORD_LENGTH and w.isalpha()]
    return words, set(words)


def remove_word_from_file(word):
    """Remove the given word (case-insensitive) from words.txt safely."""
    word_lower = word.lower().strip()
    if not os.path.exists(WORDS_FILE):
        return
    # atomic write using tempfile
    dirpath = os.path.dirname(os.path.abspath(WORDS_FILE)) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)
    with os.fdopen(fd, "w", encoding="utf-8") as tmp:
        with open(WORDS_FILE, "r", encoding="utf-8") as orig:
            for ln in orig:
                if ln.strip().lower() != word_lower:
                    tmp.write(ln)
    os.replace(tmp_path, WORDS_FILE)


def main(page: ft.Page):
    page.title = "Wordle-like (Flet)"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20

    words_list, words_set = load_words()
    if not words_list:
        page.add(ft.Text("words.txt missing or no valid words found for length " + str(WORD_LENGTH)))
        return

    target = random.choice(words_list).lower()
    # Uncomment next line for debugging to see target
    # print("TARGET WORD:", target)

    # Board tiles: list of rows, each row is list of Containers
    board_tiles = []
    for r in range(MAX_GUESSES):
        row = []
        for c in range(WORD_LENGTH):
            tile = ft.Container(
                ft.Text("", size=24, weight=ft.FontWeight.W_700),
                width=56,
                height=56,
                alignment=ft.alignment.center,
                bgcolor=ft.colors.WHITE,
                border=ft.border.all(1, ft.colors.GREY),
                border_radius=6,
                margin=ft.margin.only(right=6),
            )
            row.append(tile)
        board_tiles.append(row)

    # Wrap rows in Columns for display
    board_rows = [ft.Row(tiles, alignment=ft.MainAxisAlignment.CENTER) for tiles in board_tiles]

    input_field = ft.TextField(label="Enter guess", width=320, text_align=ft.TextAlign.CENTER)
    submit_btn = ft.ElevatedButton("Submit", width=120)

    status_text = ft.Text("", color=ft.colors.BLACK)

    guess_index = {"value": 0}  # mutable counter in closure
    keyboard_colors = {}  # letter -> color priority (green>yellow>grey)

    def color_for_priority(existing, new):
        """Priority: green > yellow > grey. Colors are strings from ft.colors."""
        priority = {ft.colors.GREEN: 3, ft.colors.AMBER: 2, ft.colors.GREY_500: 1}
        if existing is None:
            return new
        if priority.get(new, 0) > priority.get(existing, 0):
            return new
        return existing

    def update_tile(row, col, letter, bg):
        cont = board_tiles[row][col]
        cont.content = ft.Text(letter.upper(), size=24, weight=ft.FontWeight.W_700, color=ft.colors.WHITE)
        cont.bgcolor = bg
        cont.border = None
        cont.update()

    def submit_guess(e):
        guess = input_field.value.strip().lower()
        if len(guess) != WORD_LENGTH:
            page.snack_bar = ft.SnackBar(ft.Text(f"Guess must be {WORD_LENGTH} letters"))
            page.snack_bar.open = True
            page.update()
            return
        if not guess.isalpha():
            page.snack_bar = ft.SnackBar(ft.Text("Guess must contain only letters"))
            page.snack_bar.open = True
            page.update()
            return
        if guess not in words_set:
            page.snack_bar = ft.SnackBar(ft.Text("Word not in allowed list"))
            page.snack_bar.open = True
            page.update()
            return

        row = guess_index["value"]
        if row >= MAX_GUESSES:
            return  # no more attempts

        # Determine colors: first mark greens, then yellows
        target_chars = list(target)
        guess_chars = list(guess)

        result_colors = [ft.colors.GREY_500] * WORD_LENGTH

        # First pass: greens
        for i in range(WORD_LENGTH):
            if guess_chars[i] == target_chars[i]:
                result_colors[i] = ft.colors.GREEN
                target_chars[i] = None  # consume

        # Second pass: yellows for present letters
        for i in range(WORD_LENGTH):
            if result_colors[i] == ft.colors.GREEN:
                continue
            if guess_chars[i] in target_chars:
                result_colors[i] = ft.colors.AMBER
                # consume the first matching occurrence
                idx = target_chars.index(guess_chars[i])
                target_chars[idx] = None

        # Update board UI and keyboard color map
        for i in range(WORD_LENGTH):
            update_tile(row, i, guess_chars[i], result_colors[i])
            prev = keyboard_colors.get(guess_chars[i])
            keyboard_colors[guess_chars[i]] = color_for_priority(prev, result_colors[i])

        guess_index["value"] += 1

        # Check win
        if guess == target:
            page.snack_bar = ft.SnackBar(ft.Text(f"Correct! The word was {target.upper()}"))
            page.snack_bar.open = True
            page.update()

            # Remove the word from words.txt
            try:
                remove_word_from_file(target)
                # also remove from in-memory set to prevent reusing in same session
                words_set.discard(target)
            except Exception as ex:
                # still continue but inform user
                page.snack_bar = ft.SnackBar(ft.Text(f"Couldn't remove word from file: {ex}"))
                page.snack_bar.open = True
                page.update()

            # Disable further input
            input_field.disabled = True
            submit_btn.disabled = True
            input_field.update()
            submit_btn.update()
            return

        # Not win and used up all guesses?
        if guess_index["value"] >= MAX_GUESSES:
            page.snack_bar = ft.SnackBar(ft.Text(f"Out of guesses. The word was {target.upper()}"))
            page.snack_bar.open = True
            page.update()
            input_field.disabled = True
            submit_btn.disabled = True
            input_field.update()
            submit_btn.update()
            return

        # Clear input and focus for next guess
        input_field.value = ""
        input_field.focus()
        input_field.update()

    submit_btn.on_click = submit_guess
    input_field.on_submit = submit_guess

    # Top area: board
    board_col = ft.Column(board_rows, spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    # Bottom area: input and status
    controls = ft.Row([input_field, submit_btn], alignment=ft.MainAxisAlignment.CENTER)

    page.add(board_col, ft.Container(height=12), controls, ft.Container(height=8), status_text)
    page.update()


if __name__ == "__main__":
    ft.app(target=main)
