# HEDTools
HED (Hierarchical Event Descriptors) is a framework for systematically describing both laboratory and real-world events. HED tags are comma-separated path strings. The goal of HED is to describe precisely the nature of the events of interest occurring in an experiment using a common language. HED, itself, is platform-independent and data-neutral. Most people will simply annotate their events by creating a spreadsheet that associates HED tags with event codes or the events themselves. If you have such a spreadsheet, you can use the HED Online Validator (http://visual.cs.utsa.edu/hed/) to validate your spreadsheet without downloading any tools.

Once an experiment is annotated using HED, this HEDTools repository provides a suite of powerful tools for MATLAB and python to extract, search, and combine events based on these annotations. The user manual can be found online at: http://vislab.github.io/HEDTools/. 

### Installation

You can run HEDTools as a standalone toolbox or as a plugin for EEGLAB. In both cases, you should install EEGLAB unless you plan to use HEDTools only to validate tags from spreadsheets.

#### Running as a standalone application

If your data files are .mat files, you can simply unzip the EEGLABPlugin/HEDToolsx.x.x.zip anywhere you choose. Execute the *setup* script to set the paths each time you run MATLAB. Alternatively, you can add the code contained in *setup* to your startup script.

#### Running with .set data file types

If you wish to use EEGLAB, you should follow the directions above also.

#### Running as a plugin to EEGLAB

To install HEDTools unzip the HEDToolsx.x.x.zip file inside the EEGLAB plugin directory. If you don’t install HEDTools via the EEGLAB menu, you can find this file at:

https://github.com/VisLab/HEDTools/tree/master/EEGLABPlugin

When you start EEGLAB again, HEDTools should be ready to use. Note: EEGLAB requires that each EEGLAB plugin be in its own subdirectory in the plugins directory of EEGLAB. Thus, if you have unzipped HEDTools correctly, you should see …/eeglab/plugins/HEDToolsx.x.x/eegplugin_hedtools.m.

### Notes

**Note:** For convenience, EEGLABPlugin directory contains the latest released version of the
HEDTools that can be unzipped into your EEGLAB plugins directory. 

**Note:** The HEDTools will be slow to load if you have a large amount of data in your workspace when you start EEGLAB. This is because the MATLAB function to add to the Java class path clears all workspace variables. The EEGLAB startup saves all workspace variables temporarily before setting up the path and then restores the variables. 

### Citing HEDTools
HEDTools is freely available under the GUN General Public License. Please cite the following publications if using:

N. Bigdely-Shamlo, J. Cockfield, S. Makeig, T. Rognon, C. LaValle, M. Miyakoshi, and K. Robbins (2016). Hierarchical Event Descriptors (HED): Semi-structured tagging for real-world events in large-scale EEG, Frontiers in Neuroinformatics doi: 10.3389/fninf.2016.00042.

N. Bigdely-Shamlo, S. Makeig, and K. Robbins (2016). Preparing laboratory and real-world EEG data for large-scale analysis: A containerized approach, Frontiers in Neuroinformatics 1 08 March 2016 | http://dx.doi.org/10.3389/fninf.2016.00007. PMID: 27014048, PMCID: PMC4782059.

### Releases
Version 2.4.0 Released 5/31/2018
* Tag epoch search bar only works with comma delimiters.
* Added Attribute/Participant indication as an exclusive tag.

Version 2.3.0 Released 5/14/2018
* HEDTools is distributed with HED schema 7.0.1.
* HEDTools validation checks for duplicate tags and comma errors.
* Refactored validation code. 

Version 2.2.0 Released 1/18/2018
* HEDTools validation functions accept time unit class tags.
* Tags with parentheses no longer report a missing comma error.
* findhedevents function search ignores slashes at the beginning and end of tags. 

Version 2.1.0 Released 1/4/2018
* HEDTools validation functions report missing commas and unequal number of tag group parentheses.

Version 2.0.5 Released 11/10/2017
* HEDTools is compatible with jsonlab version 1.5

Version 2.0.4 Released 11/9/2017
* HED tag validation messages for groups only print out the tag that raised an issue
* Renamed validatestr function to validatehedstr  

Version 2.0.3 Released 10/31/2017
* Fixed tsvhed2map prefix issue 

Version 2.0.2 Released 9/11/2017
* HEDTools is distributed with HED schema 6.0.4
* findhedevents function is more robust

Version 2.0.1 Released 7/22/2017
* HEDTools is distributed with HED schema 6.0.3

Version 2.0.0 Released 7/16/2017
* epochhed and findhedtags search functionality has been re-implemented. Added exclusive tags feature and removed boolean search functionality. 
* implemented validateworksheethedtags function for validating the HED tags in an Excel spreadsheet.

Version 1.0.4 Released 4/17/2017 

* Nested groups are validated 
* Added pop_updatehed function
* Added validatestr function 
* Restructured top-level directory

Version 1.0.3 Released 2/22/2017

* Changed NOT operator to AND NOT operator in epochhed function.
* Group tilde count is correctly checked during validation.
* Fixed preserve prefix option when set to true.
* Multi-lined fieldMap descriptions parse correctly.

Version 1.0.2 Released 12/21/2016

* Refactored so that all pop functions comply with EEGLAB standards.
* Fixed tag epoching search bar and several minor bugs. 
* Added menu for saving multiple datasets.
