# krakenctl

`krakenctl` is a command-line tool for viewing and manipulating running kraken instances.

# Running

`krakenctl` is Python3 based.  It requires Python >= 3.7.

1) Verify python version (must be >= 3.7):
   ```bash
   $ python3 --version
   Python 3.9.2
   ```
3) Install dependencies:
   ```bash
   $ pip3 install pyyaml requests rich
   ...
   ```
5) Run
   ```bash
   ./krakenctl.py -h
   usage: krakenctl.py [-h] [-v] [-d] [-i IP_ADDRESS] action ...
   
   positional arguments:
     action                Desired action to perform
       node                Get node details and manipulate node config
       sme                 Control the kraken SME
       runtime             Change kraken runtime settings
   
   optional arguments:
     -h, --help            show this help message and exit
     -v, --verbose         Provides more details (default: False)
     -d, --debug           Provides details of what krakenctl is doing (default: False)
     -i IP_ADDRESS, --ip IP_ADDRESS
                           IP address of Kraken instance (default: 127.0.0.1:3141)
   ```

# Running with podman (or docker)

Note: instructions are for `podman`, but should work for `docker` as well.

1) Make sure `podman` is installed and functional.
2) `podman pull docker.io/krakenhpc/krakenctl:latest`
3) `alias krakenctl="podman run --rm -it --network=host krakenctl -i 127.0.0.1:3141"`
   
   Replace `127.0.0.1:3141` with the IP/port for your kraken restapi if it's not running on localhost.
5) Now run it!
   ```bash
      $ krakenctl -h
   usage: krakenctl.py [-h] [-v] [-d] [-i IP_ADDRESS] action ...

   positional arguments:
     action                Desired action to perform
       node                Get node details and manipulate node config
       sme                 Control the kraken SME
       runtime             Change kraken runtime settings

   optional arguments:
     -h, --help            show this help message and exit
     -v, --verbose         Provides more details (default: False)
     -d, --debug           Provides details of what krakenctl is doing (default: False)
     -i IP_ADDRESS, --ip IP_ADDRESS
                           IP address of Kraken instance (default: 127.0.0.1:3141)
   ```
