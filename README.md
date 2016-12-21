# HEDTools
Tools to support event annotation using hierarchical event descriptor (HED) tags. The user manual can be found online at:  [http://vislab.github.io/HEDTools/](http://vislab.github.io/HEDTools/).

**Note:** For convenience, EEGLABPlugin directory contains the latest released version of the
HEDTools that can be unzipped into your EEGLAB plugins directory. 

**Note:** The HEDTools will be slow to load if you have a large amount of data in your workspace when you start EEGLAB. This is because the MATLAB function to add to the Java class path clears all workspace variables. The EEGLAB startup saves all workspace variables temporarily before setting up the path and then restores the variables. 




