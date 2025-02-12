import os
import requests
from bs4 import BeautifulSoup
import random
import time
import sys
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text

console = Console()


def slowprint(text, delay=1.0 / 400):
    text_obj = Text(text)
    for char in text:
        console.print(char, end="")
        time.sleep(delay)
    console.print()


def download_image(url, folder, progress):
    response = requests.get(url)
    if response.status_code == 200:
        filename = os.path.join(folder, url.split("/")[-1])
        with open(filename, "wb") as f:
            f.write(response.content)


def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name


def rename_images(folder):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        files = [f for f in os.listdir(folder) if f.endswith((".jpg", ".png", ".jpeg"))]
        rename_task = progress.add_task("[cyan]Renaming files...", total=len(files))

        for filename in files:
            new_name = f"{random.randint(1000000, 9999999)}.jpg"
            os.rename(os.path.join(folder, filename), os.path.join(folder, new_name))
            progress.advance(rename_task)


def parse_pages(pages_input):
    pages = set()
    for part in pages_input.split():
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))
    return sorted(pages)


def get_images(tag, character, pages, folder_name, nsfw):
    base_url = (
        "https://konachan.com/post?tags=" if nsfw else "https://konachan.net/post?tags="
    )
    folder = create_folder(folder_name)

    total_images = 0
    for page in pages:
        params = {"page": page}
        if tag or character:
            params["tags"] = (tag + " " + character).strip()

        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            images = soup.find_all("a", class_="directlink largeimg")
            total_images += len(images)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        download_task = progress.add_task(
            "[magenta]Downloading images...", total=total_images
        )

        for page in pages:
            params = {"page": page}
            if tag or character:
                params["tags"] = (tag + " " + character).strip()

            response = requests.get(base_url, params=params)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                images = soup.find_all("a", class_="directlink largeimg")

                if images:
                    for img in images:
                        download_image(img["href"], folder, progress)
                        progress.advance(download_task)
                else:
                    console.print(f"[yellow]No images found on page {page}[/yellow]")
            else:
                console.print(f"[red]Failed to retrieve page {page}[/red]")

    rename_images(folder)
    console.print()
    console.print(Panel.fit("[cyan]Cleaning up...[/cyan]", border_style="cyan"))
    file_count = len(
        [f for f in os.listdir(folder) if f.endswith((".jpg", ".png", ".jpeg"))]
    )
    console.print(
        Panel.fit(
            f"[green]Successfully downloaded {file_count} images![/green]",
            title="Success",
            border_style="green",
        )
    )
    console.print()
    console.print("=" * 46, style="cyan bold")
    sys.exit()


def main():
    try:
        console.print(
            Panel.fit("[cyan]Konachan downloader...[/cyan]", border_style="cyan")
        )
        console.print("=" * 46, style="cyan bold")
        console.print()

        console.print("[dim]Examples: long_hair, skirt, original, touhou[/dim]")
        tag = Prompt.ask(
            "[cyan]Enter tags[/cyan]", default="", show_default=False
        ).strip()

        console.print("[dim]Examples: hatsune_miku, kagamine_rin, yakumo_yukari[/dim]")
        character = Prompt.ask(
            "[cyan]Enter characters[/cyan]", default="", show_default=False
        ).strip()

        console.print("[dim]Examples: 1 3 5 or 1-5[/dim]")
        pages_input = Prompt.ask(
            "[cyan]Enter pages[/cyan]", default="1", show_default=False
        ).strip()

        if not pages_input:
            pages = [1]
        else:
            pages = parse_pages(pages_input)

        folder_name = Prompt.ask(
            "[cyan]Enter folder name[/cyan]", default="images"
        ).strip()

        if not folder_name:
            folder_name = "images"

        while True:
            nsfw_input = Prompt.ask(
                "[cyan]Do you want NSFW images?[/cyan]",
                default="yes",
                choices=["yes", "no"],
                show_default=True,
            ).lower()

            if nsfw_input in ["yes", "no", ""]:
                nsfw = nsfw_input in ["yes", ""]
                break
            else:
                console.print(
                    "[red]Invalid input! Please enter 'yes', 'no', or leave blank for NSFW.[/red]"
                )

        print(" ")
        console.print("=" * 46, style="cyan bold")

        folder_name = os.path.join(os.getcwd(), folder_name)

        get_images(tag, character, pages, folder_name, nsfw)

    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
