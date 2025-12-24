import flet as ft
import random
import tempfile
import os

WORD_LENGTH = 5
MAX_GUESSES = 6
WORDS_FILE = "words.txt"


def load_words():
    if not os.path.exists(WORDS_FILE):
        return [], set()
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        lines = [ln.strip().lower() for ln in f]
    words = [w for w in lines if len(w) == WORD_LENGTH and w.isalpha()]
    return words, set(words)


def remove_word_from_file(word):
    word_lower = word.lower().strip()
    if not os.path.exists(WORDS_FILE):
        return
    dirpath = os.path.dirname(os.path.abspath(WORDS_FILE)) or "."
    fd, tmp_path = tempfile.mkstemp(dir=dirpath)
    with os.fdopen(fd, "w", encoding="utf-8") as tmp:
        with open(WORDS_FILE, "r", encoding="utf-8") as orig:
            for ln in orig:
                if ln.strip().lower() != word_lower:
                    tmp.write(ln)
    os.replace(tmp_path, WORDS_FILE)


def main(page: ft.Page):
    page.title = "Wordle Pinoy (Web)"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20

    words_list, words_set = load_words()
    if not words_list:
        page.add(ft.Text("words.txt missing or no valid words found"))
        return

    target = random.choice(words_list).lower()

    # Build board
    board_tiles = []
    for _ in range(MAX_GUESSES):
        row = []
        for _ in range(WORD_LENGTH):
            row.append(
                ft.Container(
                    content=ft.Text("", size=24, weight=ft.FontWeight.BOLD),
                    width=56,
                    height=56,
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY),
                    border_radius=6,
                )
            )
        board_tiles.append(row)

    board_rows = [
        ft.Row(row, alignment=ft.MainAxisAlignment.CENTER)
        for row in board_tiles
    ]

    input_field = ft.TextField(
        label="Enter guess",
        width=320,
        text_align=ft.TextAlign.CENTER,
    )

    submit_btn = ft.ElevatedButton("Submit")
    status_text = ft.Text()

    guess_index = 0

    def update_tile(row, col, letter, color):
        tile = board_tiles[row][col]
        tile.content.value = letter.upper()
        tile.content.color = ft.Colors.WHITE
        tile.bgcolor = color
        tile.border = None
        tile.update()

    def submit_guess(e):
        nonlocal guess_index

        guess = input_field.value.strip().lower()

        if len(guess) != WORD_LENGTH or not guess.isalpha():
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Enter a {WORD_LENGTH}-letter word")
            )
            page.snack_bar.open = True
            page.update()
            return

        if guess not in words_set:
            page.snack_bar = ft.SnackBar(ft.Text("Word not in list"))
            page.snack_bar.open = True
            page.update()
            return

        target_chars = list(target)
        guess_chars = list(guess)
        colors = [ft.Colors.GREY_500] * WORD_LENGTH

        # Greens
        for i in range(WORD_LENGTH):
            if guess_chars[i] == target_chars[i]:
                colors[i] = ft.Colors.GREEN
                target_chars[i] = None

        # Yellows
        for i in range(WORD_LENGTH):
            if colors[i] == ft.Colors.GREEN:
                continue
            if guess_chars[i] in target_chars:
                colors[i] = ft.Colors.AMBER
                target_chars[target_chars.index(guess_chars[i])] = None

        for i in range(WORD_LENGTH):
            update_tile(guess_index, i, guess_chars[i], colors[i])

        guess_index += 1
        input_field.value = ""

        if guess == target:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Correct! The word was {target.upper()}")
            )
            page.snack_bar.open = True
            input_field.disabled = True
            submit_btn.disabled = True
            remove_word_from_file(target)

        elif guess_index >= MAX_GUESSES:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Out of guesses. Word was {target.upper()}")
            )
            page.snack_bar.open = True
            input_field.disabled = True
            submit_btn.disabled = True

        page.update()

    submit_btn.on_click = submit_guess
    input_field.on_submit = submit_guess

    page.add(
        ft.Column(board_rows, spacing=6),
        ft.Row(
            [input_field, submit_btn],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        status_text,
    )


if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER)
