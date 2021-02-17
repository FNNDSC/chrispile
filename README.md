# ![Logo](https://raw.githubusercontent.com/FNNDSC/chrispile/master/docs/chrispile_logo.png) ChRISPile

[![PyPI](https://img.shields.io/pypi/v/chrispile)](https://pypi.org/project/chrispile/)
[![License - MIT](https://img.shields.io/pypi/l/chrispile)](https://github.com/FNNDSC/chrispile/blob/master/LICENSE)
[![test](https://github.com/FNNDSC/chrispile/workflows/test/badge.svg)](https://github.com/FNNDSC/chrispile/actions)

Syntactical sugar for running ChRIS plugins locally.

## Abstract

`chrispile` generates wrapper scripts around `docker run` (or `podman run`).
These scripts automatically locate mount points for the position arguments
`/incoming` and `/outgoing` for
[ChRIS plugin apps](https://github.com/FNNDSC/cookiecutter-chrisapp/wiki/About-Plugins#plugin-definition).
Additionally, the wrapper sets sane defaults for running the container.

### Background

Traditionally, `docker run` is a very verbose command with user-unfriendly defaults.
Of course there are good reasons for this design (security isolation)
but it is tedious and confusing to work with.

- the default user is `root` so you will need `sudo` to remove `outputdir`.
- container timezone is UTC
- stopped containers occupy disk space
- GPU is invisible
- user needs to specify image name and command
- folders containing data need to be typed out

`chrispile` aims to hide this complexity from users.

WARNING: it is not a good idea to use `chrispile` unless you understand why it is helpful. You gotta learn the basics: [what is docker?](https://github.com/FNNDSC/cookiecutter-chrisapp/wiki/Introduction-to-Docker)

### Example

```bash
mkdir data output
cp scan.nii.gz data

chrispile run -- fnndsc/pl-fetal-brain-mask:1.0.0 --inputPathFilter scan.nii.gz data output
```

The command above is translated to:

```bash
docker run
    # clean up the stopped container after it exists
    --rm
    # run as yourself so that the output is readable+writable by you
    --user $(id -u):$(id -g)
    # if plugin meta specifies min_gpu_limit, GPU is enabled
    # GPU support is detected as --runtime=nvidia (legacy) or --gpus all (native)
    --gpus all
    # set the timezone in case your plugin logs timestamps
    -v /etc/localtime:/etc/localtime:ro
    # resolve input and output paths
    # SELinux label flag ':z' is appended to volume options if necessary
    -v /home/jenni/data:/incoming:ro -v /home/jenni/output:rw
    # container image name and command
    fnndsc/pl-fetal-brain-mask:1.0.0 fetal_brain_mask
    # user specified options
    --inputPathFilter scan.nii.gz
    # volume mountpoints
    /incoming /outgoing
```

## Installation

```bash
pip install chrispile
```

## Usage

```
$ chrispile --help
usage: chrispile [-h] [-V] {run,api,install,list,uninstall} ...

Generate wrapper scripts around docker or podman run to easily run ChRIS plugins

optional arguments:
  -h, --help            show this help message and exit

info:
  -V, --version         show program's version number and exit

subcommands:
  {run,api,install,list,uninstall}
    run                 run a ChRIS plugin
    api                 query the system for information
    install             install a ChRIS plugin as an executable
    list                list installed ChRIS plugins
    uninstall           uninstall a ChRIS plugin
```

### Run Plugin

```
$ chrispile run --help
usage: chrispile run [--dry-run] [--reload-from] -- dock_image [args ...] inputdir/ outputdir/

positional arguments:
  dock_image            container image of the ChRIS plugin
  args                  arguments to pass to the ChRIS plugin

optional arguments:
  -h, --help            show this help message and exit
  -d, --dry-run         print command to run withour running it
  -e src, --reload-from src
                        mount given host directory as source folder for rapid development
```

#### Run Example

```
docker pull fnndsc/pl-simpledsapp:2.0.0

# setup test data
mkdir input output
touch input/{a,b,c}
```

##### Dry Run

```
$ chrispile run --dry-run -- fnndsc/pl-simpledsapp:2.0.0 --dummyFloat 3.5 input output 

docker run --rm --user 1000:1003              \
  -v /etc/localtime:/etc/localtime:ro         \
  -v /home/chris/input:/incoming:ro           \
  -v /home/chris/output:/outgoing:rw          \
  fnndsc/pl-simpledsapp:2.0.0 simpledsapp     \
  --dummyFloat 3.5                            \
  /incoming /outgoing
```

##### Real Run

```
$ chrispile run -- fnndsc/pl-simpledsapp:2.0.0 --dummyFloat 3.5 input output

     _                 _          _                       
    (_)               | |        | |                      
 ___ _ _ __ ___  _ __ | | ___  __| |___  __ _ _ __  _ __  
/ __| | '_ ` _ \| '_ \| |/ _ \/ _` / __|/ _` | '_ \| '_ \ 
\__ \ | | | | | | |_) | |  __/ (_| \__ \ (_| | |_) | |_) |
|___/_|_| |_| |_| .__/|_|\___|\__,_|___/\__,_| .__/| .__/ 
                | |                          | |   | |    
                |_|                          |_|   |_|    

Version: 2.0.0
Sleeping for 0
Creating new file... /outgoing/b
Creating new file... /outgoing/a
Creating new file... /outgoing/c
```

###### Check Outputs

```
$ ls -lh output

total 0
-rw-r--r-- 1 chris grantlab 0 Feb 13 22:21 a
-rw-r--r-- 1 chris grantlab 0 Feb 13 22:21 b
-rw-r--r-- 1 chris grantlab 0 Feb 13 22:21 c

$ rm -rv output

removed 'output/b'
removed 'output/a'
removed 'output/c'
removed directory 'output'
```

##### Run With Live Code

Mount the source code directory into the installed library's location
within the container for a convenient developer experience.

The container will run changes you've made to the code without having
to rebuild the docker image.

```bash
 chrispile run --reload-from ~/Github/pl-simpledsapp/simpledsapp \
   -- fnndsc/pl-simpledsapp:2.0.0 --dummyFloat 3.2 input output
```

### Install Plugin

```bash
docker pull fnndsc/pl-brainmgz:2.0.3
chrispile install fnndsc/pl-brainmgz:2.0.3

docker pull fnndsc/pl-lungct:latest
chrispile install fnndsc/pl-lungct:latest
```

Now you can simply run

```bash
mkidr out
lungct out
```

### Uninstall Plugin

```
$ chrispile list
lungct
simpledsapp
med2img.py

$ chrispile uninstall lungct
```

## Planned Features

- [x] Github Actions build matrix to test docker and podman separately
- [ ] `chrispile create` as an alias for [cookiecutter-chrisapp](https://github.com/FNNDSC/cookiecutter-chrisapp)
- [ ] `chrispile run --clobber` deletes the `/outgoing` directory before start
- [ ] `chrispile install` from https://chrisstore.co and pulls for you
- [ ] `chrispile list` also shows container image tags
- [ ] `chrispile uninstall --rm` also runs `docker rmi`
