# Music Background generator
Generate an image to use as the background for a static image music video.
A logo, title, and cover image can be added.

This tool is CLI based. There is no GUI.

It is known to work on linux/macOS, and WSL2. Probably works in pure windows,
but haven't tried it.

# Install
```shell
# Get the code
git clone https://github.com/mhhollomon/muThings.git
cd muThings

# build a python virtual env
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Usage

## Help

You can get a complete list of the options in the help message.

```
./mupic --help
```

# Concepts

The documentation relys on several concepts used by the software. Please
see the [mupic concepts document](mupic-concepts.md) for details.

# Configuration file

See documentation in the [example configuration file](example_config.mupic)

The `.mupic` extension on configuration files is by convention and is not
required.
