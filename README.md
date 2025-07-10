Weii
====

Weii (pronounced "weigh") is a small script that connects to a Wii Balance Board, reads a weight measurement, and disconnects.
Weii is the new, redesigned spiritual successor to [gr8w8upd8m8](https://github.com/skorokithakis/gr8w8upd8m8).

Forked from https://github.com/skorokithakis/weii.

Installation
------------

Install required packages
```bash
# Arch
pacman -S python-pyqt6
```

```bash
# Pip
pip install PyQt6
```
Download Weii-gui
```bash
git clone https://github.com/Goldstriker208/weii-gui/
```


Usage
-----

Weii currently is only tested on Linux.
Before you use Weii, you need to pair your balance board via Bluetooth.
You can do that by pressing the red button in the battery compartment and then going through the normal Bluetooth pairing process.
I don't remember the pairing code, try 0000 or 1234, and please let me know which one is right.

To weigh yourself open the weii_gui.py and from there you select either kg or lbs. Then click start weighing.

License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
