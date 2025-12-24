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

    # ---------- GAME STATE ----------
    words_list, words_set = load_words()
    if not words_list:
        page.add(ft.Text("words.txt missing or no valid words found"))
        return

    target = {"value": random.choice(words_list).lower()}
    guess_index = {"value": 0}

    # ---------- UI BUILDERS ----------
    board_tiles = []

    def build_board():
        board_tiles.clear()
        rows = []
        for _ in range(MAX_GUESSES):
            row = []
            for _ in range(WORD_LENGTH):
                tile = ft.Container(
                    content=ft.Text("", size=24, weight=ft.FontWeight.BOLD),
                    width=56,
                    height=56,
                    alignment=ft.alignment.center,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY),
                    border_radius=6,
                )
                row.append(tile)
            board_tiles.append(row)
            rows.append(ft.Row(row, alignment=ft.MainAxisAlignment.CENTER))
        return rows

    board_rows = build_board()
    board_column = ft.Column(board_rows, spacing=6)

    input_field = ft.TextField(
        label="Enter guess",
        width=320,
        text_align=ft.TextAlign.CENTER,
    )

    submit_btn = ft.ElevatedButton("Submit")
    restart_btn = ft.OutlinedButton("Restart / New Game")

    status_text = ft.Text()

    # ---------- HELPERS ----------
    def update_tile(row, col, letter, color):
        tile = board_tiles[row][col]
        tile.content.value = letter.upper()
        tile.content.color = ft.Colors.WHITE
        tile.bgcolor = color
        tile.border = None
        tile.update()

    def disable_input():
        input_field.disabled = True
        submit_btn.disabled = True
        input_field.update()
        submit_btn.update()

    def enable_input():
        input_field.disabled = False
        submit_btn.disabled = False
        input_field.value = ""
        input_field.focus()
        input_field.update()
        submit_btn.update()

    # ---------- GAME LOGIC ----------
    def submit_guess(e):
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

        row = guess_index["value"]
        if row >= MAX_GUESSES:
            return

        target_chars = list(target["value"])
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
            update_tile(row, i, guess_chars[i], colors[i])

        guess_index["value"] += 1
        input_field.value = ""
        input_field.update()

        if guess == target["value"]:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Correct! The word was {target['value'].upper()}")
            )
            page.snack_bar.open = True
            remove_word_from_file(target["value"])
            disable_input()
            page.update()
            return

        if guess_index["value"] >= MAX_GUESSES:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Out of guesses. Word was {target['value'].upper()}")
            )
            page.snack_bar.open = True
            disable_input()
            page.update()
            return

    def restart_game(e):
        target["value"] = random.choice(words_list).lower()
        guess_index["value"] = 0

        # Reset board
        for row in board_tiles:
            for tile in row:
                tile.content.value = ""
                tile.bgcolor = ft.Colors.WHITE
                tile.border = ft.border.all(1, ft.Colors.GREY)
                tile.update()

        enable_input()
        page.update()

    # ---------- EVENTS ----------
    submit_btn.on_click = submit_guess
    input_field.on_submit = submit_guess
    restart_btn.on_click = restart_game

    # ---------- LAYOUT ----------
    page.add(
        board_column,
        ft.Container(height=12),
        ft.Row(
            [input_field, submit_btn],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        ft.Container(height=8),
        restart_btn,
        status_text,
    )


if __name__ == "__main__":
    ft.app(target=main, view=ft.WEB_BROWSER)
