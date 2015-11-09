Setup:
======

Open Virtual Box (if you don't have it download it [here](https://www.virtualbox.org/wiki/Downloads)). 
Create a new virtual machine using the provided vdi image.

Open the VM Settings and go to Shared Folders.

![Step 1](img/step1.png)

![Step 2](img/step2.png)

Click on the button to edit the existing shared folder.

![Step 3](img/step3.png)
 
Browse for the folder you want to work on. Make sure Name the shared folder "share", and automount is on.

![Step 4](img/step4.png)

Once you start the virtual machine the files should be available in the `share` folder on the desktop.
If the automount doesn't work open a terminal (`Ctrl+alt+T`) and run:

`sudo mount -t vboxsf -o rw,uid=1000,gid=1000 share ~/Desktop/share`

(Replace `~/Desktop/share/` with another folder if needed)

Running:
========

The password for the virtual machine is `sumup`

On the desktop you will find a folder named `share`, if the setup worked the folder should contain your files.

Open a terminal using `ctrl+alt+T`.

Run the command: `dump_json.py ~/Desktop/share/`

(Replace `~/Desktop/share/` with another folder if needed)

If everything worked correctly this should create a file named `output.json` in your current directory (usually the home directory). This file can then be passed to Anser Indicus for analysis.


Issues:
-------

For any problem, contact alessandro.preziosi@sumupanalytics.com
