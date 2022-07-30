# TAS_Keypresses
A Python script for replaying TAS files created in libTAS

This script was created to enable recording an overlay with programs like Nohboard and Livesplit so that the keypresses from the libTAS file are pressed in time with the TAS itself. The intent of this script is not necessarily to enable TASing of Windows-only games, although this could be possible in some circumstances.

Included with the script is the file mapping.txt, which allows for a user-customizable mapping between the keys in the libTAS file and the keys that are pressed by the TAS Keypresses script. These keys don't necessarily need to be the same between the two. Currently, this mapping file contains most keys normally found on a standard keyboard.

To use the script, copy the .ltm file created from libTAS into the same directory as the script, run the script, and enter the name of the .ltm file. There is a 10 second countdown before the input replay starts and then the entire file is played from start to finish. Currently there's no built-in way to stop the script in the middle of input playback.

Debug output can be enabled by creating a file called debug.txt in the same directory as the script. The contents of this file don't matter.
