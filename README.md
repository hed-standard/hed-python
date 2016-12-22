# HEDTools
Tools to support event annotation using hierarchical event descriptor (HED) tags. The user manual can be found online at:  [http://vislab.github.io/HEDTools/](http://vislab.github.io/HEDTools/).

**Note:** For convenience, EEGLABPlugin directory contains the latest released version of the
HEDTools that can be unzipped into your EEGLAB plugins directory. 

**Note:** The HEDTools will be slow to load if you have a large amount of data in your workspace when you start EEGLAB. This is because the MATLAB function to add to the Java class path clears all workspace variables. The EEGLAB startup saves all workspace variables temporarily before setting up the path and then restores the variables. 

### Citing HEDTools
HEDTools is freely available under the GUN General Public License. Please cite the following publications if using:

N. Bigdely-Shamlo, J. Cockfield, S. Makeig, T. Rognon, C. LaValle, M. Miyakoshi, and K. Robbins (2016). Hierarchical Event Descriptors (HED): Semi-structured tagging for real-world events in large-scale EEG, Frontiers in Neuroinformatics doi: 10.3389/fninf.2016.00042.

N. Bigdely-Shamlo, S. Makeig, and K. Robbins (2016). Preparing laboratory and real-world EEG data for large-scale analysis: A containerized approach, Frontiers in Neuroinformatics 1 08 March 2016 | http://dx.doi.org/10.3389/fninf.2016.00007. PMID: 27014048, PMCID: PMC4782059.

### Releases

Version 1.0.2 Released 12/21/2016

* Refactored so that all pop functions comply with EEGLAB standards.
* Fixed tag epoching search bar and several minor bugs. 
* Added menu for saving multiple datasets.




