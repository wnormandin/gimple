# pokey_appmap
A web application scanner which can compare websites against a local or remote software template.
```
usage: pokey_appmap.py [-h] -t [TARGET [TARGET ...]] [-l LOCAL] [-r REMOTE]
                       [--ignore [IGNORE [IGNORE ...]]]
                       [--only [ONLY [ONLY ...]]] [--map-images] [-o OUTFILE]
                       [-v] [-C] [-m MAX_THREADS] [--save] [--showall]
                       [--dryrun]

optional arguments:
  -h, --help            show this help message and exit
  -t [TARGET [TARGET ...]], --target [TARGET [TARGET ...]]
                        Specify target domain(s)
  -l LOCAL, --local LOCAL
                        Specify a local directory to compare
  -r REMOTE, --remote REMOTE
                        Specify a URL to software for comparison
  --ignore [IGNORE [IGNORE ...]]
                        Specify file extensions to ignore (default = .jpg,
                        .css, .png, .gif)
  --only [ONLY [ONLY ...]]
                        Specify file extensions to grab (overrides --ignore)
  --map-images          Disable default image filtering
  -o OUTFILE, --outfile OUTFILE
                        Path to output file (default = <epoch timestamp>.json)
  -v, --verbose         Enable verbose output
  -C, --nocolor         Suppress colors in output
  -m MAX_THREADS, --max-threads MAX_THREADS
                        Specify the max number of worker threads
  --save                Keep downloaded software (in ./.path_templates)
  --showall             Show failed paths
  --dryrun              Performs preparatory steps only, no targets hit

```
Either --local OR --remote is required.
Use --local to reference a locally installed software template (e.g. /home/.../wordpress)
```
# python pokey_appmap.py --local /home/user/src/wordpress4.6.1 --target https://testurl.com
[*] Preparing local template
200 [==>] https://testurl.com/wp-content/themes/twentysixteen/readme.txt
...
200 [==>] http://testurl.com/wp-includes/ID3/license.txt
[*] Collecting results...
[*] Wrote results to: 2017-07-15_20_43_21.json

```
Use --remote to specify remote URLs for software to compare (e.g. https://wordpress.org/latest.zip)
```
# python pokey_appmap.py -r "https://wordpress.org/latest.zip" -t https://test.us --only .txt -v
[*] Argument Summary
 -  Target(s)      : https://pokeybill.us, https://pokeybill.com
 -  Source         : None
 -  Remote         : https://wordpress.org/latest.zip
 -  Outfile        : 2017-07-15_21_04_11.json
 -  Max Threads    : 2
 -  Verbose        : True
 -  Save           : False
 -  Show All       : False
 -  Include Images : False
 -  No Color       : False
 -  Dry Run        : False
 -  Find Only      : ['.txt']
[*] Preparing local template
 -  Pulling source from https://wordpress.org/latest.zip
 -  Writing to /tmp/tmpbatj_25o/latest.zip
 -  Extracting /tmp/tmpbatj_25o/latest.zip to /tmp/tmpbatj_25o
[*] Processing paths for target https://test.us
 -  Walking local path: /tmp/tmpbatj_25o/wordpress
 -  Added 1974 paths to work queue
 -  Starting thread 1
 -  Starting thread 2
200 [==>] https://test.us/license.txt
200 [==>] https://test.us/wp-includes/ID3/license.txt
...
503 [_X_] https://test.com/wp-content/themes/twentyseventeen/README.txt
[*] Collecting results...
 -  Gathered 68 results
[*] Wrote results to: 2017-07-15_20_51_26.json
```
Use --only to check files of a specific extension.
```
# python pokey_appmap.py --local /home/user/src/wordpress4.6.1 --target https://testurl.com http://testurl.net --only .txt .js
[*] Preparing local template
200 [==>] https://testurl.com/wp-content/themes/twentysixteen/readme.txt
...
200 [==>] http://testurl.net/wp-includes/ID3/license.txt
[*] Collecting results...
[*] Wrote results to: 2017-07-15_20_43_21.json

```
Conversely, using --ignore allows one to specify file extensions to ignore in the operation.
```
# python pokey_appmap.py --local /home/wnrmndn/scripts.public/private/.path_templates/wordpress -t https://test.us --ignore .php .html .js .scss
[*] Preparing local template
200 [==>] https://test.us/wp-content/themes/twentysixteen/readme.txt
...
200 [==>] https://test.us/wp-includes/ID3/license.txt
[*] Collecting results...
[*] Wrote results to: 2017-07-15_20_45_42.json

```
Various image/static extensions are excluded by default with --ignore (.jpg, .css, .png, .gif).  These can be included with the --map-images.
```
# python pokey_appmap.py --local /home/wnrmndn/scripts.public/private/.path_templates/wordpress -t https://test.us --i
gnore .php .html .js .scss --map-images
[*] Preparing local template
200 [==>] https://test.us/license.txt
200 [==>] https://test.us/wp-content/themes/twentysixteen/style.css
200 [==>] https://test.us/wp-content/themes/twentysixteen/rtl.css
200 [==>] https://pokeybill.us/wp-includes/js/tinymce/skins/wordpress/images/embedded.png
...
200 [==>] https://test.us/wp-includes/ID3/license.txt
[*] Collecting results...
[*] Wrote results to: 2017-07-15_20_46_45.json
```
