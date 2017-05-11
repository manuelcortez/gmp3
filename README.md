# gmp3
Google Music Player (GMP) written inPython 3 with loads of new features.

---

If you are looking for the Jukebox version, you need to head to [this page](http://github.com/chrisnorman7/jukebox).

---

## Installation
It is worth noting that there are some problems using GMP on Linux, and I still haven't tracked down the exact causes.

The enter key does not play tracks, and [sound_lib](http://hg.q-continum.net/sound_lib) does not work.

I have tried with both [Ubuntu Mate](http://www.ubuntu-mate.org) and [Raspbian](https://www.raspbian.org/).

### Python
GMP works with Python 3, and was written and is tested using Python 3.5.2. It may work with Python 2.7 as well, but I haven't tested it.

### Git
If using Windows, you must download git for windows from [here](https://git-scm.com/download/win).

If using Linux, use your package manager to install.

On Mac OS X use [Homebrew](http://brew.sh).

### Cloning
Once you have installed git, clone with a command like:

`git clone https://github.com/chrisnorman7/gmp3.git`

### Installing Dependancies
In the resulting folder there is a file called requirements.txt. You can install almost all the dependancies with the usual Pythonic method:

`pip install -Ur requirements.txt`

If you open up the file, the first line contains the command which I use for installing the latest version of [wxPython Phoenix](https://wxpython.org/Phoenix/docs/html/).

If you aren't using windows, you might wish to use the instructions provided at [this link](https://wiki.wxpython.org/How%20to%20install%20wxPython).

#### Note
It is worth noting that you will need to install Mercurial for your opperating system to clone some of the dependancies from requirements.txt. If you are on windows you can use [Mercurial SCM](https://www.mercurial-scm.org/). If you aren't, use your prefered package manager.

---

## Running GMP
Now you have installed everything you need, you can type

`python main.py`

To find out what arguments GMP takes, use either `python main.py -h` or `python main.py --help`.

---

## Creating Shortcuts

On windows it is possible to create a desktop shortcut which makes the program look and feel like it has been installed. To do this:

* Create a desktop icon and point it at your pythonw executable.
* Give it a meaningful name.
* Edit it's properties and put `main.py` at the end after a space, so your full line should look something like:
`c:\python35\pythonw.exe main.py`
* Set the `Start In` box to the location of your GMP source code.

Now you can just click the icon to launch GMP, or pin it to your taskbar and switch to it with your windows key and one of the numbers along the top row of your keyboard.

## License
For in depth details please see the License file in the distribution. In short though, it boils down to me not taking any responsibility for your use of GMP. I use it and it works for me.

If you like it and would like to tell me so, feel free with an issue or by email.

If you don't like it and would like to tell me so the same applies.

If you have found a bug in GMP please submit it through the [Issue](https://github.com/chrisnorman7/gmp3/issues) tracker.

