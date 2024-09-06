# kona-download

simple script to download photos from https://konachan.com/

- leaving tags and characters option blank will download most recent images from https://konachan.com/post?tags=
- to download single pages enter as "1 3 5 7 etc" or 1-4 which will download all pages from 1-4 / leaving blank downloads the first page
- leaving the folder name option emtpy will create and store the files in a folder called images/ in the current working directory

# dependencies

```
pip install requests beautifulsoup4
```
## For Arch Linux
```
sudo pacman -S figlet 
```
## For Ubuntu/Debian
```
sudo apt-get install figlet
```
